import datetime,hashlib,json,shutil
from execute_cells import ROOT,EVIDENCE

def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=ROOT/'release/qa/lead-recorder-headroom-20261023T085031.238934Z/verification.json';assert pin(review)=='061ddbc6976854e5568457331abbf85586efa506c4ed817ef47a11e275265299'
live=ROOT/'tool/native_recording.py';stage=ROOT/'release/store/android-recorder-headroom-20261023T084849.796490Z/staged/native_recording.py';before='77ddd47079b1373e8dc4b99b239b03f1ac8cd8200d125b777c4d0adaa3fe5d18';after='b1cbf7d75e58bba41db1fe43d7b3cfd4bb59b888fadda36d8ed1ed68f58ad2c3';assert pin(live)==before and pin(stage)==after
assert pin(ROOT/'game/mobile/integration_test/platform_smoke_test.dart')=='1c8ed846dff6c007edb867d801d6f592a1cbd8b297e75de21e690603081afb31';assert pin(ROOT/'tool/native_integration_driver.dart')=='ec880d16153b1ac577a221a46f81e7c309dd5417fbba8aae4ce68f7acbcfb668'
out=EVIDENCE/('recorder-headroom-adoption-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir();shutil.copyfile(live,out/'before.py');shutil.copyfile(stage,out/'after.py');shutil.copyfile(stage,live);assert pin(live)==after
v={'review':str(review),'review_sha256':pin(review),'source_before':before,'source_after':after,'exact_promotion':True,'scope':'Two exact Android safety-timeout launch/argv-identity literals27→29; owned-PID actual-DONE stop, strict raw15–30, all receipts/gameplay unchanged. Prior failures retained. No frozen or production source edits.'};(out/'adoption.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'path':str(out/'adoption.json'),'sha256':pin(out/'adoption.json')}))
