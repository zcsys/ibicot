#!/usr/bin/env python3
"""Read-only, simulator-only, process-bound socket/storage snapshots.

Never a traffic-absence or release/privacy approval. Collection stays incomplete
until a separate finalization validates normal native and driver completion.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

BUNDLE = 'dev.tideglass.game'
PROTECTED = 'F103390E-7B7C-4F0B-9404-5E029C7131FF'
DEVICES = {'F05BE4B0-52C1-4CA1-B721-BD64AE559E3F': 'ios',
           '089884DC-AD2A-4D69-8C60-C50271AC21BF': 'ios',
           'emulator-5556': 'android'}
MODES = {'runtime-study-default': 'default-unprovisioned',
         'runtime-study-enroll': 'synthetic-consented'}
FILES = ('support/tideglass-study.json', 'support/tideglass-study-eligibility.json',
         'support/tideglass-study.json.withdrawn', 'support/tideglass/progress.0.json',
         'support/tideglass/progress.1.json', 'game/progress.0.json', 'game/progress.1.json')
HEX = re.compile(r'^[a-f0-9]{64}$')
SAFE = re.compile(r'^[A-Za-z0-9_-]+$')
MARKER = re.compile(r'^(?:flutter:|I/flutter\s*\(\s*\d+\):)\s*TIDEGLASS_PRIVACY_WINDOW_(OPEN|CLOSE) (\{[^\n]+\})\s*$', re.M)
LIMITATIONS = [
    'Point-in-time open-socket snapshots are not packets, requests, destinations contacted, or absence of traffic.',
    'Short-lived sockets between samples, earlier startup and later activity are outside coverage.',
    'Debug simulator/emulator and automation/VM-service sockets are not release or physical-device behavior.',
    'Only this PID is selected; subprocesses and OS/SDK services outside it are not observed.',
    'Host/native UTC containment is required without tolerance; clocks are not authenticated. A mismatch leaves the interval unqualified.',
    'Private storage inventory covers seven fixed synthetic fixture files, not all SDK caches, Keychain, preferences or files.',
    'Synthetic study interaction is not participant consent. No paid/provider account, human or crash-free rate evidence.',
    'Sample identity checks bracket commands; socket descriptors and files may change within a bracket. iOS host ps start time has one-second resolution.',
    'The window starts after bootstrap/consent assertions; startup activity before OPEN is outside these samples. Audio and reminders use existing harness isolation.',
    'Android storage is unavailable: no descriptor-anchored native reader has been qualified. No path-check plus shell hash fallback is used.',
    'Storage identity checks detect lasting replacement or mutation; they are not an atomic filesystem snapshot or protection against a privileged mutation-and-restore adversary.',
    'Collector and verifier source pins detect lasting changes at operation boundaries; local hashes are integrity records, not external authentication.',
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path, limit=4 * 1024 * 1024, *, allow_append=False):
    # Evidence/source files are regular files too; an absent or FIFO/symlink
    # replacement must not turn source verification into a blocking open.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit,
                'Evidence is not a bounded regular file')
        chunks, size = [], 0
        while True:
            block = os.read(fd, min(65536, limit + 1 - size))
            size += len(block)
            require(size <= limit, 'Evidence exceeds byte bound')
            if not block:
                break
            chunks.append(block)
        after = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                                 info.st_mtime_ns, info.st_ctime_ns)
        if allow_append:
            # Only the in-progress run log may grow. Its exact observed prefix
            # is archived and later checked against the completed pinned log.
            require(identity(before)[:3] == identity(after)[:3] == identity(named)[:3]
                    and before.st_size <= size <= after.st_size <= named.st_size <= limit,
                    'Growing evidence was replaced, truncated or exceeded its bound')
        else:
            require(size == before.st_size and identity(before) == identity(after) == identity(named),
                    'Evidence changed during read')
        return b''.join(chunks)
    finally:
        os.close(fd)


# Captured once when this module is loaded, then checked before/after each
# operation. The archive is written from these exact bytes, not a second read.
COLLECTOR_PATH = Path(__file__).absolute()
COLLECTOR_BYTES = read_bounded(COLLECTOR_PATH)
COLLECTOR_SHA256 = sha(COLLECTOR_BYTES)


def collector_source_unchanged():
    require(read_bounded(COLLECTOR_PATH) == COLLECTOR_BYTES,
            'Collector source changed since module load')


def device_platform(device):
    require(device.upper() != PROTECTED, 'Protected tablet refused before commands')
    require(device in DEVICES, 'Only explicitly approved dedicated test devices')
    return DEVICES[device]


def parse_ios_identity(raw, expected_pid, executable):
    # ps emits PID UID weekday month day hh:mm:ss year executable. No global ps.
    parts = raw.decode().strip().split(maxsplit=7)
    require(len(parts) == 8, 'Missing exact iOS process identity')
    require(parts[0].isdigit() and int(parts[0]) == expected_pid, 'iOS PID mismatch')
    require(parts[1].isdigit(), 'Missing host UID')
    require(parts[7] == str(executable), 'iOS executable is not selected installed app')
    require(re.fullmatch(r'\w{3} \w{3} +\d{1,2} \d{2}:\d{2}:\d{2} \d{4}', ' '.join(parts[2:7])), 'Invalid process start')
    return {'pid': expected_pid, 'uid': int(parts[1]), 'start': ' '.join(parts[2:7]),
            'executable': parts[7], 'uid_scope': 'macOS host UID, not a unique iOS application UID'}


def parse_android_identity(cmdline, proc_stat, status, expected_pid, app_uid, boot_id):
    require(cmdline.split(b'\0')[0] == BUNDLE.encode(), 'Android package cmdline mismatch')
    match = re.fullmatch(rb'(\d+) \((.*)\) (.+)\n?', proc_stat.strip(), re.S)
    require(match and int(match[1]) == expected_pid, 'Android PID/stat mismatch')
    fields = match[3].split()
    require(len(fields) >= 20 and fields[19].isdigit(), 'Missing kernel process start ticks')
    uid = re.findall(rb'^Uid:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$', status, re.M)
    require(len(uid) == 1 and all(int(x) == app_uid for x in uid[0]), 'Android process UID differs from run-as package UID')
    require(re.fullmatch(r'[a-f0-9-]{36}', boot_id), 'Missing kernel boot identity')
    return {'pid': expected_pid, 'uid': app_uid, 'start_ticks': int(fields[19]),
            'boot_id': boot_id, 'package': BUNDLE, 'uid_scope': 'package run-as UID plus exact PID cmdline'}


def parse_lsof(raw, expected_pid):
    lines = raw.decode().splitlines()
    if not lines:
        return []
    rows, row, pid = [], {}, None
    for line in lines:
        require(line and line[0] in 'pcuLfPaDtTn', 'Unrecognized process-scoped lsof field')
        kind, value = line[0], line[1:]
        if kind == 'p':
            require(value.isdigit() and int(value) == expected_pid, 'lsof returned another PID')
            pid = int(value)
        elif kind == 'f':
            if row:
                rows.append(row)
            row = {'fd': value}
        elif kind in 'PtnT':
            require(pid == expected_pid and row, 'Socket outside selected process/descriptor')
            row.setdefault(kind, []).append(value)
    if row:
        rows.append(row)
    require(pid == expected_pid, 'Missing lsof PID binding')
    return rows


def parse_android_sockets(raw, app_uid):
    rows, inodes, available = [], set(), set()
    for line in raw.decode().splitlines():
        parts = line.split('|')
        if parts[0] == 'FD':
            require(len(parts) == 2 and parts[1].isdigit(), 'Invalid socket inode')
            inodes.add(int(parts[1]))
        elif parts[0] == 'TABLE':
            require(len(parts) == 2 and parts[1] in ('tcp', 'tcp6', 'udp', 'udp6'), 'Invalid table')
            available.add(parts[1])
        elif parts[0] == 'SOCKET':
            require(len(parts) == 7 and parts[1] in available, 'Invalid selected socket row')
            require(parts[2].isdigit() and int(parts[2]) == app_uid, 'Socket belongs to another UID')
            require(parts[3].isdigit() and int(parts[3]) in inodes, 'Socket is not in selected PID FD snapshot')
            require(all(re.fullmatch(r'[A-Fa-f0-9:]+', s) for s in parts[4:]), 'Malformed socket endpoint/state')
            rows.append({'table': parts[1], 'uid': app_uid, 'inode': int(parts[3]),
                         'local_hex': parts[4], 'remote_hex': parts[5], 'state_hex': parts[6]})
        else:
            raise ValueError('Unexpected socket output')
    require(available == {'tcp', 'tcp6', 'udp', 'udp6'}, 'Socket table access incomplete; absence cannot be inferred')
    return rows


def validate_window(marker, context):
    required = {'verification_id', 'candidate_fingerprint', 'harness_sha256', 'scenario', 'run_id',
                'device_label', 'platform', 'process_id', 'fixture_directory', 'mode', 'window_id',
                'maximum_ms', 'native_elapsed_us', 'native_utc_ms'}
    require(set(marker) == required, 'Unexpected/missing window fields')
    for key in ('verification_id', 'candidate_fingerprint', 'harness_sha256', 'scenario', 'run_id', 'device_label', 'platform'):
        require(marker[key] == context[key], 'Window identity mismatch: ' + key)
    require(marker['scenario'] in MODES and marker['mode'] == MODES[marker['scenario']], 'Window mode mismatch')
    require(type(marker['process_id']) is int and marker['process_id'] > 1, 'Invalid observed PID')
    require(marker['window_id'] == context['verification_id'] + '-privacy', 'Window ID mismatch')
    require(type(marker['maximum_ms']) is int and marker['maximum_ms'] == 20000, 'Unbounded observation window')
    for key in ('native_elapsed_us', 'native_utc_ms'):
        require(type(marker[key]) is int and marker[key] >= 0, 'Invalid native time')
    return marker


def window_pair(log, context):
    values = MARKER.findall(log)
    require(len(values) == 2 and [p[0] for p in values] == ['OPEN', 'CLOSE'], 'Exactly one ordered open/close window required')
    opened, closed = [validate_window(json.loads(item), context) for _, item in values]
    for key in opened.keys() - {'native_elapsed_us', 'native_utc_ms'}:
        require(closed[key] == opened[key], 'Native window identity changed: ' + key)
    elapsed = closed['native_elapsed_us'] - opened['native_elapsed_us']
    require(0 < elapsed <= 20000000, 'Native observation exceeded20s or invalid monotonic interval')
    return opened, closed


def attributed_sample(before, after, sample, window_start_ns, window_end_ns):
    require(before == after, 'PID/package/UID/start identity changed during sample')
    require(type(sample['started_ns']) is int and type(sample['finished_ns']) is int and
            window_start_ns <= sample['started_ns'] <= sample['finished_ns'] <= window_end_ns,
            'Sample not within host-observed window')
    return dict(sample, process_identity=before)


def validate_sample_window(sample, opened, closed, observed_ns, expected_identity):
    require(sample['process_identity'] == expected_identity, 'Sample process identity mismatch')
    require(opened['native_utc_ms'] <= sample['started_utc_ms'] <= sample['finished_utc_ms'] <= closed['native_utc_ms'], 'Sample UTC interval outside native window; clock alignment unqualified')
    require(observed_ns <= sample['started_ns'] <= sample['finished_ns'] <= observed_ns + 17000000000, 'Sample monotonic interval outside host budget')


def fixture_root(marker, device, data_container):
    suffix = Path('native-current-verification') / (marker['device_label'] + '-' + marker['run_id']) / 'study'
    actual = Path(marker['fixture_directory'])
    require(actual.is_absolute() and '..' not in actual.parts, 'Unsafe fixture path')
    if device_platform(device) == 'ios':
        container = Path(data_container)
        require('/Devices/' + device + '/data/Containers/Data/Application/' in str(container), 'Unexpected device data container')
        expected = container / 'Library/Application Support' / suffix
        require(actual == expected and actual.resolve() == expected.resolve(), 'Fixture differs from exact selected app namespace')
        return expected
    expected = Path('/data/user/0') / BUNDLE / 'files' / suffix
    require(actual == expected, 'Android fixture differs from exact app support namespace')
    return actual


def inode_identity(info):
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


def file_identity(info):
    return (inode_identity(info), info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_uid, info.st_nlink)


class AnchoredDirectory:
    """Retain every directory descriptor from / to the selected fixture.

    Relative opens cannot follow a swapped ancestor, and every retained entry
    is compared with its opened descriptor before publishing a sample.
    """
    def __init__(self, base):
        base = Path(base)
        require(base.is_absolute() and '..' not in base.parts,
                'Storage root must be a canonical absolute path')
        self.fds, self.links = [], []
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        try:
            current = os.open('/', flags)
            self.fds.append(current)
            for name in base.parts[1:]:
                current = self.child(current, name)
            self.fd = current
            self.identity = inode_identity(os.fstat(current))
            self.verify()
        except BaseException:
            self.close()
            raise

    def child(self, parent, name):
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        require(stat.S_ISDIR(info.st_mode), 'Synthetic fixture directory is a symlink or special file')
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        child = os.open(name, flags, dir_fd=parent)
        self.fds.append(child)
        opened = os.fstat(child)
        require(inode_identity(opened) == inode_identity(info), 'Synthetic fixture directory replaced before open')
        self.links.append((parent, name, child, inode_identity(opened)))
        return child

    def verify(self):
        for parent, name, child, identity in self.links:
            require(inode_identity(os.fstat(child)) == identity and
                    inode_identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) == identity,
                    'Synthetic fixture root/component identity changed')

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def storage_root_identity(base):
    with AnchoredDirectory(base) as anchor:
        return anchor.identity


def local_storage(base, expected_root=None, deadline=None):
    # O_NONBLOCK prevents a replacement FIFO from waiting for a writer. Only
    # regular single-link files are read, from the exact fd whose metadata is
    # recorded. The production caller additionally runs this in a subprocess
    # with a hard <=2s timeout, covering slow regular-file/kernel operations.
    deadline = min(deadline or time.monotonic() + 2, time.monotonic() + 2)
    result = {}
    with AnchoredDirectory(base) as anchor:
        require(expected_root is None or tuple(expected_root) == anchor.identity,
                'Synthetic fixture root replaced since Host validation')
        for relative in FILES:
            require(time.monotonic() < deadline, 'Storage read budget exhausted')
            parent = anchor.fd
            parts = Path(relative).parts
            absent = None
            for part in parts[:-1]:
                try:
                    parent = anchor.child(parent, part)
                except FileNotFoundError:
                    absent = (parent, part)
                    break
            if absent is None:
                try:
                    info = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    absent = (parent, parts[-1])
            if absent is not None:
                anchor.verify()
                try:
                    os.stat(absent[1], dir_fd=absent[0], follow_symlinks=False)
                except FileNotFoundError:
                    result[relative] = {'present': False}
                    continue
                raise ValueError('Synthetic fixture absent entry changed during sample')
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                    'Synthetic fixture file is a symlink, special file or hard link')
            require(0 <= info.st_size <= 2 * 1024 * 1024, 'Synthetic fixture file exceeds bound')
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
            fd = os.open(parts[-1], flags, dir_fd=parent)
            try:
                opened = os.fstat(fd)
                require(stat.S_ISREG(opened.st_mode) and file_identity(opened) == file_identity(info),
                        'Synthetic fixture file replaced before open')
                digest = hashlib.sha256()
                count = 0
                while True:
                    require(time.monotonic() < deadline, 'Storage read budget exhausted')
                    block = os.read(fd, min(65536, 2 * 1024 * 1024 + 1 - count))
                    count += len(block)
                    require(count <= 2 * 1024 * 1024, 'Synthetic fixture grew beyond bound')
                    if not block:
                        break
                    digest.update(block)
                after = os.fstat(fd)
                require(count == opened.st_size and file_identity(after) == file_identity(opened),
                        'Synthetic fixture file mutated during read')
                anchor.verify()
                require(file_identity(os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)) == file_identity(opened),
                        'Synthetic fixture file identity changed during read')
                result[relative] = {'present': True, 'size': count, 'sha256': digest.hexdigest(),
                                    'mtime_ns': opened.st_mtime_ns, 'uid': opened.st_uid,
                                    'inode': opened.st_ino, 'device': opened.st_dev}
            finally:
                os.close(fd)
        anchor.verify()
        require(time.monotonic() < deadline, 'Storage read budget exhausted')
    return result


# Filtering runs ON DEVICE. Other UIDs/endpoints never enter host evidence.
ANDROID_SOCKETS = r'''
set -eu
p="$1"; uid="$2"; nodes=' '
for f in /proc/"$p"/fd/*; do
  link=$(readlink "$f" 2>/dev/null) || continue
  case "$link" in socket:\[*\]) n=${link#socket:[}; n=${n%]}; case "$n" in *[!0-9]*|'') exit 71;; esac; nodes="$nodes$n "; printf 'FD|%s\n' "$n";; esac
done
for t in tcp tcp6 udp udp6; do
  test -r /proc/"$p"/net/"$t" || exit 72
  printf 'TABLE|%s\n' "$t"
  while read -r line; do
    set -- $line
    test "$#" -ge 10 || continue
    test "$8" = "$uid" || continue
    shift 9; inode="$1"
    case "$nodes" in *" $inode "*) set -- $line; printf 'SOCKET|%s|%s|%s|%s|%s|%s\n' "$t" "$uid" "$inode" "$2" "$3" "$4";; esac
  done < /proc/"$p"/net/"$t"
done
'''


class Host:
    def __init__(self, root, device, marker, run=subprocess.run):
        self.platform = device_platform(device)
        self.root, self.device, self.marker, self.runner = Path(root), device, marker, run
        self.commands = []
        self.deadline = time.monotonic() + 15
        self.adb = self.root / '.tooling/android-sdk/platform-tools/adb'
        self.app_uid = None
        if self.platform == 'ios':
            self.data = self.command(['xcrun', 'simctl', 'get_app_container', device, BUNDLE, 'data']).strip().decode()
            self.app = self.command(['xcrun', 'simctl', 'get_app_container', device, BUNDLE, 'app']).strip().decode()
            require('/Devices/' + device + '/data/Containers/Bundle/Application/' in self.app and self.app.endswith('/Runner.app'), 'Unexpected installed simulator app container')
        else:
            self.data = None
            raw = self.command(self.remote('id', '-u')).strip()
            require(raw.isdigit() and int(raw) >= 10000, 'Invalid Android package UID')
            self.app_uid = int(raw)
        self.base = fixture_root(marker, device, self.data)
        if self.platform == 'ios':
            self.storage_root_identity = storage_root_identity(self.base)

    def remote(self, *args):
        return [str(self.adb), '-s', self.device, 'exec-out', 'run-as', BUNDLE, *args]

    def command(self, argv, allowed=(0,)):
        start = time.monotonic_ns()
        remaining = self.deadline - time.monotonic()
        require(remaining > 0, 'Collector command budget exhausted')
        result = self.runner(argv, capture_output=True, timeout=min(2, remaining), env=dict(os.environ, LC_ALL='C', TZ='UTC'))
        require(len(result.stdout) <= 65536 and len(result.stderr) <= 4096, 'Host command output exceeds bound')
        self.commands.append({'argv': argv, 'exit_code': result.returncode,
                              'started_ns': start, 'finished_ns': time.monotonic_ns(),
                              'stdout_sha256': sha(result.stdout), 'stdout': result.stdout.decode(errors='replace'),
                              'stderr': result.stderr.decode(errors='replace')})
        require(result.returncode in allowed, 'Read-only host command unavailable')
        return result.stdout

    def identity(self):
        pid = self.marker['process_id']
        if self.platform == 'ios':
            raw = self.command(['/bin/ps', '-p', str(pid), '-o', 'pid=,uid=,lstart=,comm='])
            return parse_ios_identity(raw, pid, Path(self.app) / 'Runner')
        cmd = self.command(self.remote('cat', f'/proc/{pid}/cmdline'))
        data = self.command(self.remote('cat', f'/proc/{pid}/stat'))
        status = self.command(self.remote('cat', f'/proc/{pid}/status'))
        # Only kernel boot identifier is read; no device-wide process/network list.
        boot = self.command(self.remote('cat', '/proc/sys/kernel/random/boot_id')).decode().strip()
        return parse_android_identity(cmd, data, status, pid, self.app_uid, boot)

    def sockets(self):
        pid = self.marker['process_id']
        if self.platform == 'ios':
            raw = self.command(['/usr/sbin/lsof', '-a', '-p', str(pid), '-i', '-nP', '-FpcufPtnT'], allowed=(0, 1))
            if self.commands[-1]['exit_code'] == 1:
                require(not raw and not self.commands[-1]['stderr'], 'lsof inspection unavailable, not empty')
            return parse_lsof(raw, pid)
        raw = self.command([str(self.adb), '-s', self.device, 'shell', 'run-as', BUNDLE, 'sh', '-c', shlex.quote(ANDROID_SOCKETS), 'observer', str(pid), str(self.app_uid)])
        return parse_android_sockets(raw, self.app_uid)

    def storage(self):
        if self.platform != 'ios':
            raise ValueError('Android storage unavailable: a descriptor-anchored native reader is not qualified')
        # Every per-sample filesystem operation runs inside the timed worker.
        # Its constructor-to-worker root identity is mandatory, so even root
        # replacement cannot silently choose a new synthetic directory.
        expected = getattr(self, 'storage_root_identity', None)
        require(expected is not None, 'Storage root lacks anchored Host validation')
        raw = self.command([sys.executable, str(COLLECTOR_PATH), 'storage-worker',
                            '--fixture-root', str(self.base),
                            '--root-identity', json.dumps(expected, separators=(',', ':'))])
        value = json.loads(raw)
        require(value.get('collector_sha256') == COLLECTOR_SHA256,
                'Storage worker collector source differs')
        require(tuple(value.get('root_identity', ())) == expected,
                'Storage worker root identity differs')
        require(set(value['files']) == set(FILES), 'Storage worker returned unexpected files')
        return value['files']


def context_for(candidate, evidence, device):
    manifest = json.loads(read_bounded(candidate / 'manifest.json', 16 * 1024 * 1024))
    require(sha(json.dumps(manifest['source_sha256'], sort_keys=True, separators=(',', ':')).encode()) == manifest['source_fingerprint'], 'Candidate fingerprint invalid')
    for relative, digest in manifest['source_sha256'].items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts, 'Unsafe candidate path')
        require(sha((candidate / 'source' / path).read_bytes()) == digest, 'Candidate source drift')
    harness = read_bounded(evidence / 'harness.dart')
    return manifest, {'verification_id': evidence.name, 'candidate_fingerprint': manifest['source_fingerprint'],
                      'harness_sha256': sha(harness), 'platform': device_platform(device)}


SOURCE_ARCHIVES = {'verify_native.py': 'tool/verify_native.py',
                   'runner.py': 'tool/verify_current_runtime.py',
                   'harness.dart': 'game/mobile/integration_test/current_runtime_test.dart'}


ANDROID_PROBE_BRIDGE = {
    'candidate_fingerprint': '3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59',
    'candidate_runner_sha256': 'd849ab8feb642eb1b988f9a6d82558491b7ebef4c63768fb4fa132f49edf3804',
    'executed_runner_sha256': 'd1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847',
}
_PROBE_BEFORE = b"self.adb_command('exec-out', 'run-as', BUNDLE, 'test', flag, str(target))"
_PROBE_AFTER = b"self.adb_command('shell', 'run-as', BUNDLE, 'test', flag, str(target))"


def source_binding(candidate, evidence, manifest, *, platform=None):
    """Bind the runner's actual archived sources to this exact candidate."""
    manifest_raw = read_bounded(candidate / 'manifest.json', 16 * 1024 * 1024)
    require(json.loads(manifest_raw) == manifest, 'Candidate manifest changed')
    sources = {}
    bridge = None
    original_runner = None
    for archive, relative in SOURCE_ARCHIVES.items():
        data = read_bounded(candidate / 'source' / relative)
        require(sha(data) == manifest['source_sha256'].get(relative),
                'Candidate omitted or changed reviewed source: ' + relative)
        executed = read_bounded(evidence / archive)
        if executed != data:
            # One reviewed Android host-probe correction. This is an explicit
            # verification-tool revision, not an arbitrary source override.
            # Completion verifier and Dart harness remain candidate-exact.
            require(archive == 'runner.py' and platform == 'android',
                    'Archived native source differs from candidate: ' + archive)
            require(manifest['source_fingerprint'] == ANDROID_PROBE_BRIDGE['candidate_fingerprint']
                    and sha(data) == ANDROID_PROBE_BRIDGE['candidate_runner_sha256']
                    and sha(executed) == ANDROID_PROBE_BRIDGE['executed_runner_sha256'],
                    'Unknown Android probe verification revision')
            require(data.count(_PROBE_BEFORE) == 1
                    and executed == data.replace(_PROBE_BEFORE, _PROBE_AFTER, 1),
                    'Android probe revision has additional changes')
            original_runner = data
            bridge = dict(ANDROID_PROBE_BRIDGE,
                          scope='Android test exit-status transport only; raw binary transfer unchanged')
        sources[archive] = executed
    binding = {'candidate_manifest_sha256': sha(manifest_raw),
               'candidate_fingerprint': manifest['source_fingerprint'],
               'native_source_sha256': {name: sha(data) for name, data in sources.items()}}
    archives = {'collector.py': COLLECTOR_BYTES,
                'completion-verifier.py': sources['verify_native.py'],
                'native-runner.py': sources['runner.py'],
                'candidate-manifest.json': manifest_raw}
    if bridge is not None:
        binding['verification_tool_bridge'] = bridge
        archives['candidate-native-runner.py'] = original_runner
    binding['observation_source_sha256'] = {name: sha(data) for name, data in archives.items()}
    return binding, archives


def validate_source_binding(report, output):
    collector_source_unchanged()
    require(report['collector_sha256'] == COLLECTOR_SHA256 and
            read_bounded(output / 'collector.py') == COLLECTOR_BYTES,
            'Preserved collector does not match the collecting/finalizing source')
    candidate, evidence = Path(report['candidate']), Path(report['native_evidence'])
    manifest, context = context_for(candidate, evidence, report['device'])
    require(all(report['context'][key] == value for key, value in context.items()),
            'Candidate/harness context changed')
    binding, archives = source_binding(candidate, evidence, manifest, platform=context['platform'])
    require(binding == report['source_binding'], 'Collector/completion source binding changed')
    for name, data in archives.items():
        require(read_bounded(output / name, 16 * 1024 * 1024) == data,
                'Preserved source archive changed: ' + name)
    return archives['completion-verifier.py']


def archived_completion_errors(source, log):
    # Execute the exact reviewed function AST from the pinned archive. Do not
    # import verify_native or its unrelated build/recording modules through a
    # mutable sys.path or sys.modules cache. Full source hash is retained.
    tree = ast.parse(source, filename='archived-completion-verifier.py')
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'native_log_errors']
    require(len(functions) == 1 and not functions[0].decorator_list,
            'Archived verifier lacks exactly one undecorated completion function')
    namespace = {'re': re, '__builtins__': __builtins__}
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 'archived-completion-verifier.py', 'exec'), namespace)
    return namespace['native_log_errors'](log)


def collect(root, candidate, evidence, device, output):
    device_platform(device)  # before any external command or input access
    collector_source_unchanged()
    require(not output.exists(), 'Evidence directory already exists')
    manifest, context = context_for(candidate, evidence, device)
    binding, archives = source_binding(candidate, evidence, manifest, platform=context['platform'])
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'status': 'incomplete', 'device': device,
              'candidate': str(candidate), 'native_evidence': str(evidence), 'samples': [],
              'limitations': LIMITATIONS, 'release_acceptance': False, 'traffic_absence_claim': False,
              'collector_sha256': COLLECTOR_SHA256, 'source_binding': binding, 'errors': []}
    for name, data in archives.items():
        (output / name).write_bytes(data)
    host = None
    try:
        deadline = time.monotonic() + 300
        while True:
            raw = read_bounded(evidence / 'run.log', allow_append=True)
            values = MARKER.findall(raw.decode(errors='replace'))
            require(not any(x[0] == 'CLOSE' for x in values), 'Observation window already ended')
            if values:
                require(len(values) == 1 and values[0][0] == 'OPEN', 'Ambiguous observation open marker')
                opened = json.loads(values[0][1])
                context.update({k: opened[k] for k in ('scenario', 'run_id', 'device_label')})
                for key in ('run_id', 'device_label'):
                    require(type(context[key]) is str and SAFE.fullmatch(context[key]), 'Unsafe window token')
                validate_window(opened, context)
                break
            require(time.monotonic() < deadline, 'No native observation window within300s')
            time.sleep(.05)
        observed = time.monotonic_ns()
        report.update(context=context, opened=opened, opened_observed_ns=observed,
                      open_prefix_bytes=len(raw), open_prefix_sha256=sha(raw))
        (output / 'open-prefix.log').write_bytes(raw)
        host = Host(root, device, opened)
        baseline = host.identity()
        report['process_identity'] = baseline
        # A maximum three samples, hard budget below the20s native hold. Each
        # command has a2s deadline. Exceeding the bracket invalidates a sample.
        for index in range(3):
            if time.monotonic_ns() - observed >= 12_000_000_000:
                break
            before = host.identity()
            require(before == baseline, 'Observed native process restarted/reused PID')
            sample = {'started_ns': time.monotonic_ns(), 'started_utc_ms': time.time_ns() // 1000000, 'index': index}
            try:
                sample['sockets'] = {'status': 'observed', 'rows': host.sockets()}
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                sample['sockets'] = {'status': 'unavailable', 'reason': str(error)}
            try:
                sample['storage'] = {'status': 'observed', 'files': host.storage()}
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                sample['storage'] = {'status': 'unavailable', 'reason': str(error)}
            after = host.identity()
            sample['finished_ns'] = time.monotonic_ns()
            sample['finished_utc_ms'] = time.time_ns() // 1000000
            # The host close observation is an upper bound, not proof that a
            # delayed/buffered open log equals native window start. Finalization
            # requires the native pair plus this conservative max17s budget.
            report['samples'].append(attributed_sample(before, after, sample, observed, observed + 17_000_000_000))
            time.sleep(.2)
        require(report['samples'], 'No fully attributed sample completed')
        validate_source_binding(report, output)
        report['status'] = 'collected-pending-native-completion'
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        report['errors'].append(type(error).__name__ + ': ' + str(error))
        report['status'] = 'failed'
    finally:
        report['commands'] = host.commands if host else []
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (output / 'observation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def finalize(output, root):
    report_path = output / 'observation.json'
    report_raw = read_bounded(report_path)
    report = json.loads(report_raw)
    require(report['status'] == 'collected-pending-native-completion' and not report['errors'], 'Collection incomplete or failed')
    completion_source = validate_source_binding(report, output)
    evidence = Path(report['native_evidence'])
    verification_raw = read_bounded(evidence / 'verification.json')
    verification = json.loads(verification_raw)
    payload_raw = read_bounded(evidence / 'result.json')
    payload = json.loads(payload_raw)
    log_raw = read_bounded(evidence / 'run.log')
    require(not archived_completion_errors(completion_source, log_raw.decode(errors='replace')),
            'Native framework/driver completion failed')
    require(verification.get('passed') is True and verification.get('status') == 'passed' and verification.get('exit_code') == 0
            and not verification.get('verification_errors'), 'Normal native verification did not pass')
    for key, expected in report['context'].items():
        report_key = 'label' if key == 'device_label' else key
        require(verification.get(report_key) == expected and payload.get(key) == expected, 'Native final identity mismatch: ' + key)
    require(verification.get('device') == report['device'], 'Native device mismatch')
    require(verification.get('native_process_id') == report['opened']['process_id'] == payload.get('process_id'), 'Final process mismatch')
    require(payload.get('completed') is True, 'Native test not complete')
    require(verification.get('source_snapshot_unchanged') is True and not verification.get('source_changes_during_run') and not verification.get('production_input_differences_after_run'), 'Native source integrity not established')
    require(verification.get('privacy_observation_enabled') is True and '--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true' in verification.get('command', []), 'Exact observation flag not archived')
    require(verification.get('candidate_path') == report['candidate'], 'Runner used another candidate path')
    for name, expected in report['source_binding']['native_source_sha256'].items():
        require(verification.get('source_pins', {}).get(name) == expected and
                verification.get('evidence_sha256', {}).get(name) == expected,
                'Runner did not pin the exact reviewed native source: ' + name)
    for name, raw in [('result.json', payload_raw), ('run.log', log_raw), ('harness.dart', read_bounded(evidence / 'harness.dart'))]:
        require(verification.get('evidence_sha256', {}).get(name) == sha(raw), 'Native evidence pin mismatch: ' + name)
    require(log_raw.startswith(read_bounded(output / 'open-prefix.log')), 'Observed log prefix changed')
    require(sha(read_bounded(output / 'open-prefix.log')) == report['open_prefix_sha256'], 'Observation prefix hash changed')
    opened, closed = window_pair(log_raw.decode(errors='replace'), report['context'])
    require(opened == report['opened'], 'Native opening checkpoint changed')
    require(payload.get('privacy_observation_window') == {'opened': opened, 'closed': closed}, 'Driver lacks same completed observation pair')
    # Independent monotonic clocks cannot be directly compared. Require UTC
    # containment as well, with no tolerance that could admit post-window data.
    # A clock mismatch fails qualification; these clocks are not authenticated.
    for sample in report['samples']:
        validate_sample_window(sample, opened, closed, report['opened_observed_ns'], report['process_identity'])
    require(sha((evidence / 'harness.dart').read_bytes()) == report['context']['harness_sha256'], 'Harness evidence changed')
    paired = sum(s['sockets']['status'] == 'observed' and s['storage']['status'] == 'observed' for s in report['samples'])
    result = {'schema_version': 1, 'status': 'finalized-sampled-observation' if paired else 'finalized-partial-observation',
              'paired_socket_storage_samples': paired,
              'observation_sha256': sha(report_raw), 'native_verification_sha256': sha(verification_raw),
              'native_payload_sha256': sha(payload_raw), 'native_log_sha256': sha(log_raw),
              'window': {'opened': opened, 'closed': closed}, 'samples': len(report['samples']),
              'socket_statuses': [s['sockets']['status'] for s in report['samples']],
              'storage_statuses': [s['storage']['status'] for s in report['samples']],
              'collector_sha256': report['collector_sha256'], 'completion_verifier_sha256': sha(completion_source),
              'completion_verifier_mode': 'exact-function-from-candidate-pinned-archive',
              'source_binding': report['source_binding'],
              'traffic_absence_claim': False, 'release_acceptance': False, 'limitations': LIMITATIONS}
    target = output / 'finalization.json'
    require(not target.exists(), 'Finalization already exists')
    # Revalidate after the decision, before publishing it. Every used input is
    # also pinned, so a replacement during finalization cannot be silently
    # reported as the bytes that were actually examined.
    require(validate_source_binding(report, output) == completion_source,
            'Completion verifier changed during finalization')
    for path, before in [(report_path, report_raw), (evidence / 'verification.json', verification_raw),
                         (evidence / 'result.json', payload_raw), (evidence / 'run.log', log_raw)]:
        require(read_bounded(path) == before, 'Finalization input changed: ' + path.name)
    collector_source_unchanged()
    target.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'storage-worker':
        worker = argparse.ArgumentParser(description='Bounded fixed synthetic storage reader')
        worker.add_argument('action', choices=['storage-worker'])
        worker.add_argument('--fixture-root', type=Path, required=True)
        worker.add_argument('--root-identity', required=True)
        arguments = worker.parse_args()
        collector_source_unchanged()
        identity = json.loads(arguments.root_identity)
        files = local_storage(arguments.fixture_root, identity)
        collector_source_unchanged()
        print(json.dumps({'collector_sha256': COLLECTOR_SHA256,
                          'root_identity': identity, 'files': files}))
        return 0
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['collect', 'finalize'])
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--evidence', type=Path)
    p.add_argument('--device')
    a = p.parse_args()
    if a.action == 'collect':
        p.error('candidate/evidence/device required') if not all((a.candidate, a.evidence, a.device)) else None
        value = collect(a.root.resolve(), a.candidate.resolve(), a.evidence.resolve(), a.device, a.output.resolve())
    else:
        value = finalize(a.output.resolve(), a.root.resolve())
    print(json.dumps({'status': value['status'], 'release_acceptance': False}))
    return 1 if value['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
