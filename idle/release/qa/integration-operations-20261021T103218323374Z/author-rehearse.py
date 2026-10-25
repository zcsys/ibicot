
import hashlib,json,os,subprocess,sys,tempfile,time,uuid
from pathlib import Path
from services.tideglass_service.api import Application
from services.tideglass_service.storage import Database
with tempfile.TemporaryDirectory(prefix='tideglass-ops-author-') as folder:
 p=Path(folder); live=p/'service.sqlite3'; backup=p/'backup.sqlite3'
 database=Database(live); app=Application(database)
 account=app.dispatch('POST','/v1/accounts',{'consent_cloud':True})[1]
 database.backup(backup)
 before=hashlib.sha256(backup.read_bytes()).hexdigest()
 records=[]
 for label,path,tail,expected in [('healthy_structure_no_samples',live,['health','--backup',str(backup)],3),('missing_path',p/'absent',['health'],2),('isolated_restore',backup,['restore-drill'],0)]:
  r=subprocess.run([sys.executable,'-m','services.tideglass_service.ops','--database',str(path),*tail],capture_output=True,text=True)
  assert r.returncode==expected,(label,r.returncode)
  records.append({'scenario':label,'exit_code':r.returncode,'output':json.loads(r.stdout)})
 with database.transaction() as db:
  db.execute('INSERT INTO purchases VALUES(?,?,?,?,?,?,?,?,?,?)',('google',str(uuid.uuid4()),account['account_id'],'dev.tideglass.cosmetic.01','purchased',1,'synthetic_operator_rehearsal',str(uuid.uuid4()),0,int(time.time())-601))
 r=subprocess.run([sys.executable,'-m','services.tideglass_service.ops','--database',str(live),'health','--backup',str(backup)],capture_output=True,text=True)
 assert r.returncode==2
 records.append({'scenario':'old_pending_acknowledgement','exit_code':r.returncode,'output':json.loads(r.stdout)})
 assert before==hashlib.sha256(backup.read_bytes()).hexdigest()
 assert not (p/'absent').exists()
 output=json.dumps({'synthetic_local_data_only':True,'unchanged_backup_sha256':before,'records':records},indent=2)
 assert account['account_id'] not in output and account['session_token'] not in output and account['recovery_code'] not in output
 print(output)
