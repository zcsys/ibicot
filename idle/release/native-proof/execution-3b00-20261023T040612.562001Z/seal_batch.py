#!/usr/bin/env python3
"""Read-only artifact replay with a new immutable batch index."""
import argparse,collections,datetime,hashlib,json,pathlib
ROOT=pathlib.Path('/Users/csys/Desktop/ibicot/idle');E=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('label',choices=['ios-phone','android','ios-tablet']);p.add_argument('suffix');p.add_argument('--note',required=True);a=p.parse_args()
def pin(path):return hashlib.sha256(path.read_bytes()).hexdigest()
rows=[json.loads(x) for x in (E/'cells.jsonl').read_text().splitlines() if x.strip()];rows=[x for x in rows if x['label']==a.label]
assert rows
cells=[];observations=[]
for row in rows:
 path=pathlib.Path(row['verification']);assert pin(path)==row['verification_sha256'],path
 report=json.loads(path.read_text());pins=report.get('evidence_sha256',{})
 for name,h in pins.items():assert pin(path.parent/name)==h,(path,name)
 cells.append({k:row.get(k) for k in ['scenario','run_id','status','verification','verification_sha256','predecessor','errors']}|{'native_evidence_sha256':pins})
 if row.get('observer_command'):
  command=row['observer_command'];folder=pathlib.Path(command[command.index('--output')+1]);final=folder/'finalization.json'
  observations.append({'native_verification':str(path),'finalization':json.loads(final.read_text()) if final.exists() else None,'all_files_sha256':{str(x.relative_to(folder)):pin(x) for x in sorted(folder.rglob('*')) if x.is_file()}})
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=E/('sealed-'+a.label+'-'+a.suffix+'-'+stamp);out.mkdir()
value={'candidate_fingerprint':'3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59','sealed_utc':stamp,'cells':cells,'counts':dict(collections.Counter(x['status'] for x in cells)),'observations':observations,'note':a.note,'release_acceptance':False,'source':'Terminal cell ledger only; every stored native evidence digest reread and matched. Expected-interrupted rows are preparations, not passing tests.'}
(out/'checkpoint.json').write_text(json.dumps(value,indent=2)+'\n');h=pin(out/'checkpoint.json');(out/'checkpoint.sha256').write_text(h+'  checkpoint.json\n');print(json.dumps({'checkpoint':str(out/'checkpoint.json'),'sha256':h,'cells':len(cells),'counts':value['counts']}))
