"""Independent read-only review of these actual four native captures and metadata adoption."""
from array import array
from pathlib import Path
import hashlib,json,struct,sys,zlib,subprocess
ROOT=Path('/Users/csys/Desktop/ibicot/idle'); OUT=Path(__file__).resolve().parent
RAW=ROOT/'release/native-proof/integration-ios-phone-20261023T045334.631912Z'
MEDIA=ROOT/'release/store/media-3b00-phone-clean-20261023T045548.384747Z'
CAND=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
ADOPT=ROOT/'release/qa/lead-s04-acceptance-20261023T045632.781258Z'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p): return json.loads(p.read_text())
def save(n,d): (OUT/n).write_text(json.dumps(d,indent=2)+'\n')
pins={str(p.relative_to(ROOT)):sha(p) for folder in [RAW,MEDIA,ADOPT] for p in folder.rglob('*') if p.is_file()}
for p in ['implementation/program.json','implementation/scope_requirements.json','v1_backlog.json','TIDEGLASS_DESIGN.md','V1_ROADMAP.md','game/mobile/integration_test/platform_smoke_test.dart','tool/verify_native.py','release/store/tools/export_screenshots.py','release/store/tools/export_preview.swift','release/store/tools/inspect_preview.swift']:
 pins[p]=sha(ROOT/p)
save('input-pins-before.json',pins)
before=js(ADOPT/'scope-before.json'); after=js(ROOT/'implementation/scope_requirements.json')
assert before.keys()==after.keys()
assert before['source_of_truth']==after['source_of_truth']
changes=[]
for old,new in zip(before['requirements'],after['requirements'],strict=True):
 fields=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)]
 if fields: changes.append({'id':old['id'],'fields':sorted(fields),'before':{k:old.get(k) for k in fields},'after':{k:new.get(k) for k in fields}})
assert len(changes)==1 and changes[0]['id']=='S04'
assert changes[0]['fields']==['delivery_status','evidence','verification_note']
assert (ADOPT/'program-before.json').read_bytes()==(ROOT/'implementation/program.json').read_bytes()
program=js(ROOT/'implementation/program.json'); backlog=js(ROOT/'v1_backlog.json')
assert len(before['requirements'])==len(after['requirements'])==44 and len(backlog['items'])==65
orig={x['id']:x for x in backlog['items']}; items={x['id']:x for x in program['items']}
for k,item in orig.items():
 assert items[k]['source_acceptance']==item['acceptance'],k
 assert items[k]['source_acceptance_dependencies']==item['dependencies'],k
ad=js(ADOPT/'adoption.json')
assert ad['scope_before_sha256']==sha(ADOPT/'scope-before.json') and ad['scope_after_sha256']==sha(ROOT/'implementation/scope_requirements.json')
assert ad['program_unchanged_sha256']==sha(ROOT/'implementation/program.json')
result=subprocess.run([sys.executable,str(ROOT/'implementation/tools/validate_program.py')],cwd=ROOT,text=True,capture_output=True)
(OUT/'program-validation.log').write_text(result.stdout+result.stderr); assert result.returncode==0
save('metadata-diff.json',{'changes':changes,'program_unchanged':True,'original_packages':65,'requirements':44,'validator_exit_code':result.returncode,'adoption_sha256':sha(ADOPT/'adoption.json')})
v=js(RAW/'verification.json'); manifest=js(CAND/'manifest.json'); export=js(MEDIA/'screenshots/export-manifest.json')
assert v['passed'] and v['source_snapshot_unchanged'] and v['production_inputs_match_snapshot'] and not v['verification_errors']
for name,digest in v['evidence_sha256'].items(): assert sha(RAW/name)==digest,name
for name,digest in export['source_sha256'].items(): assert sha(RAW/name)==digest,name
assert export['native_verification_sha256']==sha(RAW/'verification.json')
assert v['candidate_fingerprint']==export['candidate_fingerprint']==manifest['source_fingerprint']
assert v['harness_sha256']['harness.dart']==sha(ROOT/'game/mobile/integration_test/platform_smoke_test.dart')
for name,digest in manifest['source_sha256'].items(): assert sha(CAND/'source'/name)==digest,name
sys.path.insert(0,str(ROOT/'tool')); import verify_native
prod=verify_native.production_inputs(manifest['source_sha256'])
for name,digest in prod.items():
 assert sha(CAND/'workspace'/name)==digest,('workspace',name)
 assert sha(ROOT/name)==digest,('live',name)
save('native-provenance.json',{'candidate':manifest['source_fingerprint'],'native_verification_sha256':sha(RAW/'verification.json'),'raw_evidence_files_rehashed':len(v['evidence_sha256']),'frozen_source_files_rehashed':len(manifest['source_sha256']),'live_and_workspace_production_files_rehashed':len(prod),'harness_sha256':sha(RAW/'harness.dart'),'result':js(RAW/'result.json')})
def decode(p):
 data=p.read_bytes(); assert data[:8]==b'\x89PNG\r\n\x1a\n'; cur=8; chunks=[]
 while cur<len(data):
  n=struct.unpack('>I',data[cur:cur+4])[0]; tag=data[cur+4:cur+8]; payload=data[cur+8:cur+8+n]; crc=struct.unpack('>I',data[cur+8+n:cur+12+n])[0]
  assert zlib.crc32(tag+payload)&0xffffffff==crc
  chunks.append((tag,payload));cur+=n+12
 assert cur==len(data) and chunks[-1][0]==b'IEND'
 w,h,depth,ct,comp,filt,interlace=struct.unpack('>IIBBBBB',chunks[0][1]);assert comp==filt==interlace==0
 assert (depth,ct) in [(16,6),(8,2)]
 bpp=(4 if ct==6 else 3)*(depth//8);stride=w*bpp
 stream=zlib.decompress(b''.join(v for t,v in chunks if t==b'IDAT'));assert len(stream)==h*(stride+1)
 assert all(stream[i*(stride+1)]==0 for i in range(h)),'actual captures should use filter0'
 pixels=b''.join(stream[i*(stride+1)+1:(i+1)*(stride+1)] for i in range(h))
 return {'width':w,'height':h,'depth':depth,'type':ct,'chunks':chunks,'pixels':pixels}
rows=[]
for e in export['exports']:
 name=e['file'];s=decode(RAW/name);o=decode(MEDIA/'screenshots'/name)
 assert sha(MEDIA/'screenshots'/name)==e['sha256']
 assert (s['width'],s['height'])==(o['width'],o['height'])==(1206,2622)
 assert s['depth']==16 and s['type']==6 and o['depth']==8 and o['type']==2
 assert all(t not in [b'tRNS',b'acTL',b'fcTL',b'fdAT'] for t,_ in o['chunks'])
 vals=array('H');vals.frombytes(s['pixels']);
 if sys.byteorder=='little': vals.byteswap()
 assert min(vals[3::4])==max(vals[3::4])==65535
 rgb=array('H');changed=0;maxerror=0
 expected=bytearray(len(o['pixels']));at=0
 for pos,vv in enumerate(vals):
  if pos%4==3:continue
  mapped=round(vv/257);expected[at]=mapped;at+=1
  err=abs(vv-mapped*257); changed+=err!=0;maxerror=max(maxerror,err)
 assert expected==o['pixels']
 assert changed==e['rgb_samples_not_exactly_representable'] and maxerror==e['maximum_native_sample_error']==128
 color={b'iCCP',b'cICP',b'sRGB',b'gAMA',b'cHRM',b'mDCv',b'cLLi'}
 sc=[(t,p) for t,p in s['chunks'] if t in color]; oc=[(t,p) for t,p in o['chunks'] if t in color]; assert sc==oc
 from PIL import Image
 with Image.open(MEDIA/'screenshots'/name) as im: assert im.mode=='RGB' and im.tobytes()==expected and im.size==(1206,2622)
 rows.append({'file':name,'input_sha256':sha(RAW/name),'output_sha256':sha(MEDIA/'screenshots'/name),'size':[1206,2622],'source_format':'RGBA16','native_alpha_range':[65535,65535],'output_format':'RGB8 PNG type2','mapping':'independent round(sample/257) matches every output RGB sample','nonrepresentable_samples':changed,'maximum_native_sample_error':maxerror,'color_chunks_unchanged':{t.decode():hashlib.sha256(p).hexdigest() for t,p in sc},'no_crop_resize_composite':True})
save('actual-png-analysis.json',rows)
afterpins={p:sha(ROOT/p) for p in pins};assert pins==afterpins
save('input-pins-after.json',afterpins)
print(json.dumps({'metadata':'only S04 three allowed fields changed','png_rows':len(rows),'raw_evidence_rehashed':len(v['evidence_sha256']),'frozen_source_count':len(manifest['source_sha256']),'production_count':len(prod),'preserved_input_files':len(pins),'passed':True}))
