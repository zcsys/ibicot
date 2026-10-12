"""Build a standalone, read-only inspection page from a completed recorded run."""
import argparse
import hashlib
import json
from pathlib import Path
from .purchase_reporting import report
from .decision_traces import verify_export as verify_industrial
from .retail_traces import verify_export as verify_retail

ROOT=Path(__file__).resolve().parents[2]


def build(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('status')!='complete' or not manifest.get('invariantGate'):
        raise ValueError('inspection requires a completed run with passing accounting invariants')
    aggregate=report(directory)
    first,last=manifest['specification']['window']
    paths=sorted(directory.glob('decision-traces-*.json'))
    expected=[f'decision-traces-{tick:06}.json' for tick in range(first,last+1)]
    if [p.name for p in paths]!=expected:
        raise ValueError('trace files are missing, overlapping or outside the recorded window')
    documents=[];proofs=[];hashes={};phase_keys=None
    for tick,path in zip(range(first,last+1),paths):
        batch=json.loads(path.read_text())
        keys=[]
        for doc in batch:
            if doc['tick']!=tick or doc['seed']!=manifest['specification']['seed']:
                raise ValueError('trace tick/seed differs from its run')
            retail=doc.get('kind')=='distributor-decision'
            key=(3,0) if retail else (doc['tier'],doc['phase'])
            if key in keys:
                raise ValueError('duplicate trace phase')
            keys.append(key)
            proofs.append(dict(tick=tick,tier=key[0],phase=key[1],
                               **(verify_retail(doc) if retail else verify_industrial(doc))))
        if not keys or (phase_keys is not None and set(keys)!=phase_keys):
            raise ValueError('trace phase coverage changes inside the run')
        phase_keys=set(keys)
        documents.extend(batch)
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(version=1,run=directory.name,policy=manifest['specification']['treatment'],
                seed=manifest['specification']['seed'],window=[first,last],
                sourceIdentity=manifest['sourceIdentity'],aggregate=aggregate,traces=documents,
                verification=dict(status='passed',scope='Recorded accounting gate plus replay of every captured decision. This is not policy adoption or long-run validation.',
                                  results=proofs,traceHashes=hashes,
                                  verifierHashes={name:hashlib.sha256((ROOT/'tools/buying_v2'/name).read_bytes()).hexdigest()
                                                  for name in ('decision_traces.py','retail_traces.py','inspection_report.py')}))


def write(directory,output):
    data=build(directory)
    payload=json.dumps(data,allow_nan=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(ROOT/'web/buying-inspector.html').read_text()
    script=(ROOT/'web/buying-inspector.js').read_text()
    html=template.replace('/*__INSPECTOR_SCRIPT__*/',script).replace('/*__INSPECTOR_DATA__*/',payload)
    with Path(output).open('x') as stream:
        stream.write(html)
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=write(args.directory,args.output)
    print(json.dumps(dict(output=str(args.output.resolve()),documents=len(data['traces']),verification=data['verification']['status'])))
