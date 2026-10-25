#!/usr/bin/env python3
"""Append an exact terminal reminder report without changing its verdict."""
import pathlib,sys,json,hashlib,datetime
from execute_cells import ROOT,EVIDENCE
p=pathlib.Path(sys.argv[1]).resolve();assert p.name=='verification.json' and p.parent.parent==ROOT/'release/native-notifications';v=json.loads(p.read_text());pin=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for name,h in v.get('evidence_sha256',{}).items():assert pin(p.parent/name)==h,name
record={'verification':str(p),'verification_sha256':pin(p),'scenario':v['scenario'],'label':v['device_label'] if 'device_label' in v else v['label'],'run_id':v['run_id'],'passed':v['passed'],'verification_errors':v.get('errors',[]),'native_evidence_sha256':v.get('evidence_sha256',{}),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
index=EVIDENCE/'reminder-cells.jsonl'
if index.exists():assert not any(json.loads(line)['verification']==str(p) for line in index.read_text().splitlines() if line.strip())
with index.open('a') as out:out.write(json.dumps(record)+'\n')
print(json.dumps(record))
