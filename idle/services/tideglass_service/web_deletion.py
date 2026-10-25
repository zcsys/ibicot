"""Opt-in same-origin account-deletion UI; delegates all auth/deletion to the API.

This module has no account writes, credential store, logger, CORS grants or public
hosting side effects. An approved production operator/TLS deployment is separate.
"""
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).with_name('web_deletion_static')
PREFIX = '/account/delete'
BROWSER_HEADER = 'HTTP_X_TIDEGLASS_DELETION'
BROWSER_ROUTES = {('POST', '/v1/sessions'), ('DELETE', '/v1/account'),
                  ('POST', '/v1/sessions/revoke')}
MAX_BROWSER_BODY = 1024
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; "
       "form-action 'none'; frame-ancestors 'none'; worker-src 'none'; manifest-src 'none'")


class DeletionWebApplication:
    def __init__(self, downstream, *, origin, allow_loopback_http=False):
        if not isinstance(origin, str) or len(origin) > 300 or type(allow_loopback_http) is not bool:
            raise ValueError('Invalid deletion web configuration.')
        parsed = urlsplit(origin)
        try:
            port = parsed.port
        except ValueError:
            raise ValueError('Invalid deletion web origin.') from None
        # Exact serialized origins avoid alternate Host spellings, userinfo,
        # inherited path credentials, DNS-rebinding aliases and proxy guesses.
        local = parsed.scheme == 'http' and parsed.hostname == '127.0.0.1'
        public_host = parsed.hostname or ''
        valid_public = (parsed.scheme == 'https' and '.' in public_host and
                        re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', public_host) and
                        not re.fullmatch(r'[0-9.]+', public_host) and
                        not any(not part or len(part)>63 or part.startswith('-') or part.endswith('-')
                                for part in public_host.split('.')))
        if (parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or
            not parsed.netloc or port is not None and not 1 <= port <= 65535 or
            origin != f'{parsed.scheme}://{parsed.netloc}' or parsed.netloc != parsed.netloc.lower() or
            not (valid_public or local and allow_loopback_http)):
            raise ValueError('Deletion web origin requires HTTPS or explicit loopback development.')
        if allow_loopback_http and not local:
            raise ValueError('Loopback development must use literal 127.0.0.1 over HTTP.')
        self.downstream, self.origin = downstream, origin
        self.host, self.scheme, self.local = parsed.netloc, parsed.scheme, local
        self.assets = {
            PREFIX: (ROOT / 'index.html', 'text/html; charset=utf-8'),
            PREFIX + '/delete.js': (ROOT / 'delete.js', 'text/javascript; charset=utf-8'),
            PREFIX + '/delete.css': (ROOT / 'delete.css', 'text/css; charset=utf-8'),
        }
        # Bound/freeze the static bytes at startup; no request-derived file paths.
        self.assets = {url: (path.read_bytes(), mime) for url, (path, mime) in self.assets.items()}
        if any(len(raw) > 65536 for raw, _ in self.assets.values()):
            raise ValueError('Deletion web asset exceeds bound.')

    def headers(self):
        result = [('Cache-Control', 'no-store, max-age=0'), ('Pragma', 'no-cache'),
                  ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                  ('Content-Security-Policy', CSP), ('X-Frame-Options', 'DENY'),
                  ('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=(), usb=()'),
                  ('Cross-Origin-Resource-Policy', 'same-origin'),
                  ('Cross-Origin-Opener-Policy', 'same-origin'), ('X-Robots-Tag', 'noindex, nofollow')]
        if not self.local:
            result.append(('Strict-Transport-Security', 'max-age=31536000'))
        return result

    def response(self, start, status, text, mime='text/plain; charset=utf-8', *, head=False):
        raw = text.encode('utf-8') if isinstance(text, str) else text
        start(status, [('Content-Type', mime), ('Content-Length', str(len(raw))), *self.headers()])
        return [] if head else [raw]

    def __call__(self, environ, start_response):
        method, path = environ.get('REQUEST_METHOD', ''), environ.get('PATH_INFO', '')
        owned = path == PREFIX or path.startswith(PREFIX + '/')
        browser = BROWSER_HEADER in environ
        origin = environ.get('HTTP_ORIGIN')
        if environ.get('HTTP_HOST') != self.host or environ.get('wsgi.url_scheme') != self.scheme:
            return self.response(start_response, '403 Forbidden', 'Configured secure origin required.')
        # Browser-origin checks also protect an API caller omitting the special
        # UI marker. Native clients omit Origin and continue to the same API.
        if origin is not None and origin != self.origin:
            return self.response(start_response, '403 Forbidden', 'Origin not allowed.')
        if environ.get('HTTP_SEC_FETCH_SITE') in {'cross-site', 'same-site'}:
            return self.response(start_response, '403 Forbidden', 'Same-origin access required.')
        if owned or browser or origin is not None:
            if (environ.get('QUERY_STRING') or environ.get('HTTP_TRANSFER_ENCODING') or
                    environ.get('HTTP_COOKIE')):
                return self.response(start_response, '400 Bad Request', 'Unsupported request metadata.')
        if owned:
            if path not in self.assets:
                return self.response(start_response, '404 Not Found', 'Not found.')
            if method not in {'GET', 'HEAD'}:
                return self.response(start_response, '405 Method Not Allowed', 'Read-only page.')
            if environ.get('CONTENT_LENGTH') not in {None, '', '0'}:
                return self.response(start_response, '400 Bad Request', 'Unexpected body.')
            raw, mime = self.assets[path]
            if path == PREFIX:
                notice = ('Local development tool — not a published account-deletion service.' if self.local else
                          'Connected to this service only. Check the service address before entering your recovery code.')
                raw = raw.replace(b'<!-- deployment-notice -->', notice.encode('utf-8'))
            return self.response(start_response, '200 OK', raw, mime, head=method == 'HEAD')
        if origin is not None and (method, path) in BROWSER_ROUTES and not browser:
            return self.response(start_response, '403 Forbidden', 'Deletion UI marker required.')
        if browser:
            if environ[BROWSER_HEADER] != '1' or origin != self.origin or (method, path) not in BROWSER_ROUTES:
                return self.response(start_response, '403 Forbidden', 'Invalid deletion UI request.')
            length = environ.get('CONTENT_LENGTH', '')
            if not isinstance(length,str) or not 1 <= len(length) <= 4 or not length.isascii() or not length.isdigit() or not 0 < int(length) <= MAX_BROWSER_BODY:
                return self.response(start_response, '413 Content Too Large', 'Bounded JSON body required.')
            if environ.get('CONTENT_TYPE', '').split(';')[0].strip() != 'application/json':
                return self.response(start_response, '415 Unsupported Media Type', 'JSON required.')
            def secured_start(status, headers, exc_info=None):
                # Credentials remain in API bodies/Authorization only; never add
                # CORS, cookies, redirects or response-derived script content.
                kept = [(key, value) for key, value in headers
                        if key.lower() not in {k.lower() for k, _ in self.headers()}]
                return start_response(status, kept + self.headers(), exc_info)
            return self.downstream(environ, secured_start)
        return self.downstream(environ, start_response)
