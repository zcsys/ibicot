"""Copy a stable host-test source snapshot without changing production files."""
from pathlib import Path
import json,hashlib,datetime,argparse,shutil
ROOT=Path(__file__).resolve().parents[2]
def inputs():
 files=[]
 for area in ['core','persistence','progression','mobile']:
  base=ROOT/'game'/area
  for path in base.rglob('*'):
   rel=path.relative_to(base)
   if not path.is_file() or any(k in rel.parts for k in ['.dart_tool','build','ios','android','macos','.idea']):continue
   if area=='mobile' and rel.parts[0] not in ['lib','test','assets'] and path.name not in ['pubspec.yaml','pubspec.lock','analysis_options.yaml']:continue
   files.append(path)
 for area in ['game/content','implementation/fixtures','implementation/contracts','implementation/tools']:
  files.extend(p for p in (ROOT/area).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 files.append(ROOT/'economy.json');return sorted(set(files))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('label');args=parser.parse_args()
 if not args.label.replace('-','').isalnum():raise SystemExit('Use an alphanumeric label.')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');dest=ROOT/'game/qa/workspaces'/(args.label+'-'+stamp)
 files=inputs();hashes={}
 for p in files:
  rel=p.relative_to(ROOT);data=p.read_bytes();out=dest/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);hashes[str(rel)]=hashlib.sha256(data).hexdigest()
 changed=[p for p,h in hashes.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
 changed+=sorted(set(str(p.relative_to(ROOT)) for p in inputs())-set(hashes))
 if changed:raise SystemExit('Source changed during snapshot; unused snapshot retained: '+str(changed))
 fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest();manifest={'utc':stamp,'source_fingerprint':fingerprint,'workspace':str(dest),'files':hashes,'changed_during_snapshot':[],'purpose':'Independent host review; not a native export'}
 report=ROOT/'release/qa'/(args.label+'-snapshot.json');report.write_text(json.dumps(manifest,indent=2)+'\n');print(report);print(fingerprint)
if __name__=='__main__':main()
