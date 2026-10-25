"""Explicit bounded Gunicorn entrypoint. No listener starts on import."""
import argparse
import importlib.metadata
import ipaddress
import json
import os
from pathlib import Path
import resource
import ssl
import sys

from .operating_config import decode, fields, integer, private_bytes

VERSIONS = {'gunicorn': '26.2.0', 'packaging': '26.3'}


def read_config(path):
    value = decode(private_bytes(path))
    fields(value, {'version', 'mode', 'host', 'port', 'database', 'workers',
                   'timeout_seconds', 'backlog', 'max_requests'},
           {'service_config', 'certificate_file', 'private_key_file'})
    integer(value['version'], 1, 1)
    if not isinstance(value['host'], str):
        raise ValueError('Explicit IPv4 string required.')
    host = ipaddress.ip_address(value['host'])
    if host.version != 4:
        raise ValueError('This deployment profile supports explicit IPv4 binds only.')
    if value['mode'] not in {'loopback_http', 'tls'}:
        raise ValueError('Explicit TLS or local loopback mode required.')
    if value['mode'] == 'loopback_http':
        if str(host) != '127.0.0.1' or {'certificate_file', 'private_key_file'} & value.keys():
            raise ValueError('Unencrypted mode requires literal loopback.')
    else:
        if not {'certificate_file', 'private_key_file'} <= value.keys():
            raise ValueError('TLS material required.')
        private_bytes(value['certificate_file'], 65536)
        private_bytes(value['private_key_file'], 16384)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(value['certificate_file'], value['private_key_file'])
    integer(value['port'], 1024, 65535)
    integer(value['workers'], 1, 4)
    integer(value['timeout_seconds'], 2, 30)
    integer(value['backlog'], 1, 128)
    integer(value['max_requests'], 10, 1000)
    database = Path(value['database'])
    if not database.is_absolute() or not database.parent.is_dir():
        raise ValueError('Existing absolute database directory required.')
    directory = database.parent.stat()
    if directory.st_uid != os.getuid() or directory.st_mode & 0o077:
        raise ValueError('Private database directory required.')
    if database.exists() or database.is_symlink():
        info = database.lstat()
        import stat
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Private regular database required.')
    if 'service_config' in value:
        private_bytes(value['service_config'])
    return value


def tls_context(config, default_factory):
    context = default_factory()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def settings(value):
    """Fixed sync class; no CLI/env override changes the qualified profile."""
    result = {
        'bind': f"{value['host']}:{value['port']}", 'workers': value['workers'],
        'worker_class': 'sync', 'threads': 1, 'backlog': value['backlog'],
        'timeout': value['timeout_seconds'], 'graceful_timeout': 10,
        'max_requests': value['max_requests'], 'max_requests_jitter': 10,
        'keepalive': 0, 'limit_request_line': 2048, 'limit_request_fields': 32,
        'limit_request_field_size': 4096, 'forwarded_allow_ips': '',
        'secure_scheme_headers': {}, 'forwarder_headers': '', 'proxy_protocol': False,
        'accesslog': None, 'errorlog': '-', 'capture_output': False,
        'preload_app': False, 'reload': False, 'umask': 0o077,
        'control_socket_disable': True, 'http_protocols': 'h1',
    }
    if value['mode'] == 'tls':
        result.update(certfile=value['certificate_file'], keyfile=value['private_key_file'], ssl_context=tls_context)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--check', action='store_true', help='Validate without binding or initializing the database.')
    args = parser.parse_args()
    try:
        value = read_config(args.config)
        for name, expected in VERSIONS.items():
            if importlib.metadata.version(name) != expected:
                raise ValueError('Pinned deployment dependency differs.')
        if os.geteuid() == 0:
            raise ValueError('Dedicated unprivileged user required.')
        if args.check:
            print(json.dumps({'valid': True, 'mode': value['mode'], 'workers': value['workers'],
                              'timeout_seconds': value['timeout_seconds'], 'release_gate_verified': False}))
            return
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        _, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        limit = min(512, hard) if hard != resource.RLIM_INFINITY else 512
        resource.setrlimit(resource.RLIMIT_NOFILE, (limit, limit))
        from gunicorn.app.base import BaseApplication
        from gunicorn.glogging import Logger
        from .factory import create_runtime

        class RedactedLogger(Logger):
            # Gunicorn parsing errors can otherwise interpolate request bytes.
            # Only a fixed event classification and OS pid reach the operator.
            def _safe(self, level, msg):
                event = ('worker_timeout' if isinstance(msg, str) and msg.startswith('WORKER TIMEOUT')
                         else 'server_'+level)
                sys.stderr.write(json.dumps({'event': event, 'pid': os.getpid()})+'\n')
                sys.stderr.flush()
            def critical(self, msg, *a, **kw): self._safe('critical', msg)
            def error(self, msg, *a, **kw): self._safe('error', msg)
            def warning(self, msg, *a, **kw): self._safe('warning', msg)
            def info(self, msg, *a, **kw): self._safe('info', msg)
            def debug(self, msg, *a, **kw): pass
            def exception(self, msg, *a, **kw): self._safe('exception', msg)
            def access(self, resp, req, environ, request_time): pass

        class Server(BaseApplication):
            def load_config(self):
                for name, setting in settings(value).items():
                    self.cfg.set(name, setting)
                self.cfg.set('logger_class', RedactedLogger)
            def load(self):
                return create_runtime(value['database'], value.get('service_config')).wsgi

        # BaseApplication otherwise inspects this entrypoint's --config as a
        # Python Gunicorn config, and ambient GUNICORN_CMD_ARGS is unqualified.
        sys.argv = [sys.argv[0]]
        os.environ.pop('GUNICORN_CMD_ARGS', None)
        Server().run()
    except Exception:
        parser.exit(2, 'Deployment configuration or startup failed; inspect private inputs and pinned runtime.\n')


if __name__ == '__main__':
    main()
