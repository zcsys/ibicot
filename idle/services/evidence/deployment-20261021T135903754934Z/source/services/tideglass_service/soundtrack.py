"""Fixed configured asset only; bearer credentials stay in request headers."""
import hashlib
import os
from pathlib import Path
import stat
from .verification import VerificationUnavailable

MAX_ARCHIVE = 64 * 1024 * 1024
CHUNK = 64 * 1024

class Download:
    def __init__(self, opener, size, digest):
        self.opener, self.source = opener, None
        self.remaining, self.size, self.digest = size, size, digest
    def prepare(self):
        if self.source is None: self.source = self.opener()
    def __iter__(self):
        self.prepare()
        try:
            while self.remaining:
                chunk = self.source.read(min(CHUNK, self.remaining))
                if not chunk: raise OSError('Soundtrack asset changed during delivery.')
                self.remaining -= len(chunk)
                yield chunk
        finally: self.close()
    def close(self):
        if self.source is not None: self.source.close()
    @property
    def headers(self):
        return [('Content-Type','application/zip'),('Content-Length',str(self.size)),
                ('Content-Disposition','attachment; filename="tideglass-original-soundtrack.zip"'),
                ('Cache-Control','private, no-store'),('X-Content-Type-Options','nosniff'),
                ('X-Content-SHA256',self.digest),('Accept-Ranges','none')]

class SoundtrackAsset:
    def __init__(self, path, sha256):
        self.path = Path(path)
        self.sha256 = sha256
        with self._open() as source:
            info = os.fstat(source.fileno())
            self.identity = self._identity(info)
            self.size = info.st_size
            actual = hashlib.file_digest(source,'sha256').hexdigest()
        if actual != sha256: raise ValueError('Configured soundtrack checksum mismatch.')
    @staticmethod
    def _identity(info): return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
    def _open(self):
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_ARCHIVE or info.st_mode & 0o022:
            os.close(fd); raise ValueError('Soundtrack must be a bounded regular file without shared write access.')
        return os.fdopen(fd, 'rb')
    def manifest(self):
        return {'asset_id':'soundtrack.01','filename':'tideglass-original-soundtrack.zip','content_type':'application/zip',
                'bytes':self.size,'sha256':self.sha256,'download_path':'/v1/soundtrack/download'}
    def _checked_open(self):
        try:
            source = self._open()
            if self._identity(os.fstat(source.fileno())) != self.identity:
                source.close(); raise ValueError()
            return source
        except (ValueError, OSError): raise VerificationUnavailable('Configured soundtrack is unavailable.') from None

    def download(self):
        return Download(self._checked_open,self.size,self.sha256)
