from pathlib import Path
from contextlib import closing
import tempfile,sqlite3,json
from services.tideglass_service.storage import Database
from services.tideglass_service.health import require_existing_database
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'probe.sqlite3';Database(p)
 with closing(sqlite3.connect(p)) as db:
  db.execute('CREATE TRIGGER sqliteXdestructive AFTER INSERT ON accounts BEGIN DELETE FROM accounts; END');db.commit()
 try: require_existing_database(p)
 except Exception as e: print(json.dumps({'rejected':True,'code':str(e)}))
 else: print(json.dumps({'rejected':False,'unexpected_trigger':'sqliteXdestructive'}));raise SystemExit(1)
