"""Author-only isolated browser driver. No real accounts, hosting or credential logs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from wsgiref.simple_server import make_server
from services.tideglass_service.api import Application
from services.tideglass_service.web_deletion import DeletionWebApplication
from services.tideglass_service.__main__ import ThreadedServer, QuietHandler

parser=argparse.ArgumentParser()
parser.add_argument('--node',required=True);parser.add_argument('--node-modules',required=True);parser.add_argument('--output',required=True)
args=parser.parse_args();output=Path(args.output).resolve();output.mkdir()
with tempfile.TemporaryDirectory(prefix='tideglass-web-delete-synthetic-') as temporary:
    app=Application(Path(temporary)/'synthetic.sqlite3')
    server=make_server('127.0.0.1',0,app,server_class=ThreadedServer,handler_class=QuietHandler)
    origin=f'http://127.0.0.1:{server.server_port}'
    server.set_app(DeletionWebApplication(app,origin=origin,allow_loopback_http=True))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        env=dict(os.environ,NODE_PATH=args.node_modules)
        command=[args.node,'tests/services/web_deletion_browser.cjs',origin,str(output)]
        with (output/'browser.log').open('w') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        (output/'runner.json').write_text(json.dumps({'command':command,'exit_code':result.returncode,'synthetic':True,'server':'loopback disposable SQLite, request logging disabled','temporary_database_removed_on_exit':True},indent=2)+'\n')
    finally:
        server.shutdown();server.server_close();thread.join()
raise SystemExit(result.returncode)
