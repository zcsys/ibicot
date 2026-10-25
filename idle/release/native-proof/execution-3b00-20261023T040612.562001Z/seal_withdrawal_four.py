import datetime,hashlib,json,pathlib
from execute_cells import ROOT,EVIDENCE
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[json.loads(x) for x in (EVIDENCE/'cells.jsonl').read_text().splitlines()]
selected=[x for x in rows if x['run_id'] in ['v3b00-ios-phone-withdraw-barrier','v3b00-android-withdraw-barrier']]
assert len(selected)==4 and all(x['status']=='passed' for x in selected)
for row in selected:
 path=pathlib.Path(row['verification']);assert pin(path)==row['verification_sha256'];report=json.loads(path.read_text());assert report['harness_sha256']=='997e7510aaef0dcebfa6505fc0dcde7d136a25e8a76abea78ede8602b0a4fef9'
 row['evidence_sha256']=report['evidence_sha256']
 for name,digest in row['evidence_sha256'].items():assert pin(path.parent/name)==digest
 if row['scenario']=='runtime-study-withdraw-reopen':
  original=[x for x in selected if x['label']==row['label'] and x['scenario']=='runtime-study-storage-withdraw'];assert len(original)==1 and row['predecessor']==original[0]['verification']
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=EVIDENCE/('sealed-withdrawal-four-'+stamp);out.mkdir()
value={'candidate_fingerprint':'3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59','created_utc':stamp,'rows':selected,'author_review':str(ROOT/'release/qa/native-withdraw-barrier-staged-20261023T044951.387640Z'),'independent_review':str(ROOT/'release/qa/lead-withdraw-barrier-20261023T045309.713695Z/REVIEW.md'),'old_phone_failed_report':str(ROOT/'release/native-proof/current-runtime-ios-phone-20261023T044453553593Z/verification.json'),'old_phone_failed_sha256':pin(ROOT/'release/native-proof/current-runtime-ios-phone-20261023T044453553593Z/verification.json'),'release_acceptance':False,'scope':'Fresh exact reviewed test-only barrier, both native withdrawal/refusal and exact-predecessor new-process reopen. Every terminal source/result/checkpoint/raw/save hash re-read. Old failure retained.'}
(out/'checkpoint.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'path':str(out/'checkpoint.json'),'sha256':pin(out/'checkpoint.json')}))
