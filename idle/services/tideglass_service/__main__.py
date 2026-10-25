"""Local-only runner. Public serving needs a configured TLS application server."""
import argparse
from wsgiref.simple_server import make_server, WSGIRequestHandler
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer
from .factory import create_runtime

class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass

class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='services/local/tideglass.sqlite3')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--config', help='Owner-only configuration JSON; absent providers remain disabled.')
    parser.add_argument('--reconcile', action='store_true', help='Run one bounded provider reconciliation batch, then exit.')
    parser.add_argument('--limit',type=int,default=100)
    args = parser.parse_args()
    try:
        runtime = create_runtime(args.database,args.config)
    except Exception:
        parser.exit(2,'Service configuration unavailable or invalid; providers remain disabled. Check private file permissions, identities and keys.\n')
    if args.reconcile:
        import json
        from .reconcile import reconcile
        print(json.dumps(reconcile(runtime.application,limit=args.limit),sort_keys=True))
        return
    app = runtime.wsgi
    with make_server('127.0.0.1', args.port, app, server_class=ThreadedServer, handler_class=QuietHandler) as server:
        print(f'Tideglass local service: http://127.0.0.1:{server.server_port}; providers require explicit configuration.', flush=True)
        server.serve_forever()

if __name__ == '__main__':
    main()
