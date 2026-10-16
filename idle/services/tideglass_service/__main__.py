"""Local-only runner. Public serving needs a configured TLS application server."""
import argparse
from wsgiref.simple_server import make_server, WSGIRequestHandler
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer
from .api import Application

class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass

class ThreadedServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='services/local/tideglass.sqlite3')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    app = Application(args.database)
    with make_server('127.0.0.1', args.port, app, server_class=ThreadedServer, handler_class=QuietHandler) as server:
        print(f'Tideglass local service: http://127.0.0.1:{server.server_port}; store and ad verification unavailable.', flush=True)
        server.serve_forever()

if __name__ == '__main__':
    main()
