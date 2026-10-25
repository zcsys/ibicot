"""Strict bounded private operator inputs, independent of provider dependencies."""
import json
import os
from pathlib import Path
import stat


def private_bytes(path, maximum=16384):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Absolute private path required.')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or not 0 < info.st_size <= maximum):
            raise ValueError('Owner-only bounded regular file required.')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(maximum+1)
        if len(data) > maximum:
            raise ValueError('File grew beyond its bound.')
        return data
    finally:
        os.close(fd)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate key.')
        result[key] = value
    return result


def decode(data):
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite number.')))


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Integer outside operating bound.')
    return value


def fields(value, required, optional=()):
    if (not isinstance(value, dict) or not set(required) <= value.keys()
            or value.keys()-set(required)-set(optional)):
        raise ValueError('Invalid configuration fields.')
