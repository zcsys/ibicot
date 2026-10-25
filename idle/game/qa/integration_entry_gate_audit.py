"""Verify only the bounded representative style/import/audio qualification delta."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:out.append((p+'/'+k,a.get(k),b.get(k)))
   else:out+=diff(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [(p,a,b)]
def main():
 out=ROOT/'release/qa'/('integration-entry-gates-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(); src=out/'source';checks=[]
 files=set(['implementation/art/production_contract.json','release/art/entry-gates/contract-before.json','source/art/style-guide.md','release/art/style-qualification.json','release/art/import-qualification.json','release/art/entry-gates/CLIENT_STYLE_REVIEW.md','release/art/entry-gates/client-style-review.json','release/audio/capability-and-rights.json','release/audio/history/capability-and-rights-before-20261021.json'])
 style=json.loads((ROOT/'release/art/style-qualification.json').read_text()); imp=json.loads((ROOT/'release/art/import-qualification.json').read_text());audio=json.loads((ROOT/'release/audio/capability-and-rights.json').read_text())
 for m in [style['source_and_evidence_sha256'],imp['source_sha256'],audio['current_component_evidence']['sha256']]:
  for p,h in m.items():assert sha(ROOT/p)==h,p;files.add(p);checks.append('hash:'+p)
 assert sha(ROOT/style['client_review'])==style['client_review_sha256'];assert sha(ROOT/'release/art/entry-gates/client-style-review.json')==style['client_review_record_sha256']
 before=json.loads((ROOT/'release/art/entry-gates/contract-before.json').read_text());after=json.loads((ROOT/'implementation/art/production_contract.json').read_text());delta=diff(before,after)
 assert {x[0] for x in delta}=={'/production_entry_gates/0/status','/production_entry_gates/1/status','/production_entry_gates/2/status','/naming_and_paths/engine_binding_status'}
 checks+=['exact-four-contract-status-deltas','no-requirements-assets-budgets-changed']
 assert style['status']=='satisfied_representative_style_direction' and style['client_review'];assert imp['release_ready']==False
 assert audio['standalone_download']['approved_host_url'] is None and audio['standalone_download']['purchase_restore_evidence'] is None and audio['reviewer'] is None
 oldaudio=json.loads((ROOT/'release/audio/history/capability-and-rights-before-20261021.json').read_text());audio_delta=diff(oldaudio,audio)
 assert audio['standalone_download']['download_sha256']==oldaudio['standalone_download']['download_sha256'];assert audio['standalone_download']['download_bytes']==oldaudio['standalone_download']['download_bytes']
 checks+=['audio-source-zip-identity-unchanged','external-host-purchase-rights-not-approved']
 guide=(ROOT/'source/art/style-guide.md').read_text();pal=(ROOT/'game/mobile/lib/palette.dart').read_text()
 for token,color in re.findall(r'static const (\w+) = Color\(0xFF([A-F0-9]+)\);',pal):assert '| '+token+' | #'+color+' |' in guide;checks.append('palette:'+token)
 pub=(ROOT/'game/mobile/pubspec.yaml').read_text();declared=[]
 in_assets=False
 for line in pub.splitlines():
  if line=='  assets:':in_assets=True;continue
  if in_assets:
   if line.startswith('    - '):declared.append(line[6:].strip())
   elif line.strip() and not line.startswith('    '):break
 assetfiles=[]
 for p in declared:
  target=ROOT/'game/mobile'/p
  assetfiles.extend([f for f in target.rglob('*') if f.is_file()] if target.is_dir() else [target])
 observation=imp['source_package_observation'];assert len(assetfiles)==observation['declared_asset_file_count'];assert sum(p.stat().st_size for p in assetfiles)==observation['declared_asset_uncompressed_bytes']
 files.update(str(p.relative_to(ROOT)) for p in assetfiles);checks+=['actual-declared-asset-count','actual-source-asset-bytes']
 hashes={}
 for p in sorted(files):
  target=src/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target);hashes[p]=sha(target)
 fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 (out/'verification.json').write_text(json.dumps({'source_sha256':hashes,'source_fingerprint':fingerprint,'checks':checks,'contract_delta':delta,'audio_delta':audio_delta,'source_drift':[p for p,h in hashes.items() if sha(ROOT/p)!=h],'new_asset_or_package_approval':False},indent=2)+'\n')
 (ROOT/'game/qa/current_entry_gate_review.json').write_text(json.dumps({'evidence':str(out)},indent=2)+'\n');print(out);print(len(hashes),len(checks),fingerprint)
if __name__=='__main__':main()
