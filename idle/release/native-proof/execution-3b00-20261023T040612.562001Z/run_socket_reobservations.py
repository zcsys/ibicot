import hashlib,json
from execute_cells import ROOT,EVIDENCE,cell
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert pin(ROOT/'release/native-privacy/runtime_observation.py')=='f6ae5e4a715b5ffc37999daa2919999e9a463f8ebd3ad238017be193ec47a438'
assert pin(ROOT/'game/mobile/integration_test/current_runtime_test.dart')=='102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5'
assert pin(ROOT/'tool/verify_current_runtime.py')=='d1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847'
paths={}
for scenario in ['default','enroll']:
 path=cell('android','runtime-study-'+scenario,'v3b00-android-socket-fixed-'+scenario,observe=True)
 paths[scenario]=str(path)
(EVIDENCE/'socket-reobservation-pair.json').write_text(json.dumps(paths,indent=2)+'\n')
