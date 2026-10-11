"""Check completed campaign archives, exact recording coverage and core provenance."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();jobs=json.loads(a.plan.read_text());rows=[];errors=[]
    reference=json.loads((a.root/'20261011-baseline-137-two-generations'/'manifest.json').read_text())['sourceHashes']
    for job in jobs:
        path=a.root/job['id'];manifest=json.loads((path/'manifest.json').read_text());issues=[]
        if manifest['status']!='complete':issues.append('run is not complete')
        spec=manifest['specification']
        start,end=spec.get('window',[1,job['ticks']])
        if end-start+1!=job['ticks']:issues.append('manifest/plan window length mismatch')
        hashes=manifest['sourceHashes'];computed=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
        if computed!=manifest['sourceIdentity']:issues.append('source identity does not match manifest hashes')
        if hashlib.sha256((path/'starting.patch').read_bytes()).hexdigest()!=manifest['patchSHA256']:
            issues.append('starting patch hash mismatch')
        with tarfile.open(path/'source.tar.gz') as archive:
            members=[m for m in archive.getmembers() if m.isfile()]
            if len({m.name for m in members})!=len(members):issues.append('duplicate archived source paths')
            if {m.name for m in members}!=set(hashes):issues.append('archive/manifest path mismatch')
            for member in members:
                if hashlib.sha256(archive.extractfile(member).read()).hexdigest()!=hashes.get(member.name):
                    issues.append('archive hash mismatch: '+member.name)
        ticks=[]
        for file in sorted(path.glob('products-*.npz')):
            with np.load(file,allow_pickle=False) as z:ticks.extend(z['ticks'].tolist())
        if ticks!=list(range(start,end+1)):issues.append('product tick coverage mismatch')
        with (path/'ticks.jsonl').open() as f:
            history_ticks=[json.loads(line)['tick'] for line in f if line.strip()]
        if history_ticks!=ticks:issues.append('tick history coverage mismatch')
        company_ticks=[]
        for file in sorted(path.glob('companies-*.npz')):
            with np.load(file,allow_pickle=False) as z:company_ticks.extend(range(int(z['startTick']),int(z['endTick'])+1))
        if company_ticks!=ticks:issues.append('company interval coverage mismatch')
        config=json.loads((path/'config.json').read_text())
        if config['seed']!=job.get('seed',spec['seed']):issues.append('seed mismatch')
        if config['t2FirmCount']!=57960 or config['distributorCount']!=1000000:issues.append('not the declared full population')
        changes=[key for key,value in hashes.items() if (key.startswith('economy/') or key.startswith('catalogs/')) and reference.get(key)!=value]
        missing=sorted(set(reference)-set(hashes))
        runtime_catalogs={'catalogs/midbridge-4259-recursive/'+name for name in ('catalog.json','naming.json','starting-selection.json','consumption-calibration.json')}
        missing_runtime=[key for key in missing if key.startswith('economy/') or key in runtime_catalogs]
        if missing_runtime:issues.append('missing runtime source: '+','.join(missing_runtime))
        expanded='workspace' in job
        if changes and not expanded:issues.append('unexplained production/catalog source change: '+','.join(changes))
        allowed_expansion={'economy/core/midbridge.py','catalogs/midbridge-4259-recursive/starting-selection.json'}
        if expanded and any(key not in allowed_expansion for key in changes):
            issues.append('expanded run changed more than its adapter and starting selection')
        for tick in sorted({end}|({7200} if start==1 and end>=7200 else set())):
            for extension in ('.json','.npz'):
                if not (path/f'checkpoint-{tick:06}{extension}').exists():issues.append(f'missing checkpoint {tick}{extension}')
            if job['treatment']!='baseline' and not (path/f'research-{tick:06}.npz').exists():issues.append(f'missing information sidecar {tick}')
        row=dict(id=job['id'],sourceIdentity=manifest['sourceIdentity'],archivedFiles=len(hashes),
            recordedWindow=[start,end],recordedTicks=len(ticks),companyRecordedTicks=len(company_ticks),invariantGate=manifest.get('invariantGate'),
            intentionalExpandedCatalog=expanded,productionSourceDifferences=changes,issues=issues)
        if spec.get('benchmarkOnly',False):
            for source,expected_hash in spec['sourceHashes'].items():
                with Path(source).open('rb') as f:
                    h=hashlib.file_digest(f,'sha256').hexdigest()
                if h!=expected_hash:issues.append('benchmark source checkpoint hash mismatch: '+source)
        row['omittedOldAuxiliarySources']=[key for key in missing if key.startswith('catalogs/') and key not in runtime_catalogs]
        rows.append(row)
        if issues:errors.append(dict(id=job['id'],issues=issues))
    result=dict(status='pass' if not errors else 'fail',runs=len(rows),archivedFilesChecked=sum(x['archivedFiles'] for x in rows),
        productTickWindowsChecked=sum(x['recordedTicks'] for x in rows),results=rows,errors=errors,
        caveat='Archive/coverage audit is separate from economic, numerical and performance gates. Expanded-catalog adapter/selection changes are explicitly listed, not treated as the original catalog.')
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('results',)}))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
