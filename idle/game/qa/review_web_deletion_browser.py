"""Isolated review driver; deletes only its own temporary synthetic database."""
from pathlib import Path
import argparse,json,os,subprocess,sys,tempfile,threading
from wsgiref.simple_server import make_server
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from services.tideglass_service.api import Application
from services.tideglass_service.web_deletion import DeletionWebApplication
from services.tideglass_service.__main__ import ThreadedServer,QuietHandler
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output).resolve();out.mkdir()
with tempfile.TemporaryDirectory(prefix='tideglass-review-browser-') as directory:
 app=Application(Path(directory)/'synthetic.sqlite3');server=make_server('127.0.0.1',0,app,server_class=ThreadedServer,handler_class=QuietHandler)
 origin=f'http://127.0.0.1:{server.server_port}';server.set_app(DeletionWebApplication(app,origin=origin,allow_loopback_http=True));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  cmd=['/Users/csys/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(ROOT/'game/qa/review_web_deletion_browser.cjs'),origin,str(out)]
  r=subprocess.run(cmd,env=dict(os.environ,NODE_PATH='/Users/csys/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
  (out/'browser.log').write_bytes(r.stdout)
 finally:server.shutdown();server.server_close();thread.join()
removed=not Path(directory).exists()
(out/'runner.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,synthetic=True,temporary_database_removed=removed,server_closed=True),indent=2)+'\n')
raise SystemExit(r.returncode)
