"""One bounded local health-and-delivery cycle; installs no scheduler."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

from .alert_transport import deliver, envelope
from .operating_config import decode


def run(database, *, lock_file, backup=None, alert_config=None, health_seconds=15):
    if type(health_seconds) is not int or not 1 <= health_seconds <= 15:
        raise ValueError('Health deadline outside bound.')
    lock = Path(lock_file)
    if not lock.is_absolute() or not lock.parent.is_dir():
        raise ValueError('Private absolute lock directory required.')
    directory = lock.parent.stat()
    if directory.st_uid != os.getuid() or directory.st_mode & 0o077:
        raise ValueError('Private lock directory required.')
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Private regular lock required.')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'already_running', 'exit_code': 5, 'release_gate_verified': False}
        command = [sys.executable, '-m', 'services.tideglass_service.ops', '--database', str(database), 'health']
        if backup is not None:
            command += ['--backup', str(backup)]
        fault = None
        try:
            child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   timeout=health_seconds, check=False)
            report = decode(child.stdout) if len(child.stdout) <= 65536 else None
            if (not isinstance(report, dict) or child.returncode not in range(4)
                    or report.get('exit_code') != child.returncode
                    or type(report.get('exit_code')) is not int
                    or report.get('status') not in {'ok', 'warning', 'critical', 'unknown'}
                    or report.get('exit_code') != {'ok': 0, 'warning': 1, 'critical': 2, 'unknown': 3}.get(report.get('status'))):
                fault = 'health_command_failed'
            else:
                envelope(report, 'operator-validation')
        except subprocess.TimeoutExpired:
            fault = 'health_deadline_exceeded'
        except (ValueError, UnicodeError, TypeError):
            fault = 'health_command_failed'
        if fault:
            report = {'format': 'tideglass-local-health-v1', 'generated_at': int(time.time()),
                      'status': 'critical', 'exit_code': 2,
                      'signals': [{'check': 'operator', 'status': 'critical', 'code': fault}]}
        delivery = deliver(report, alert_config)
        code = 4 if delivery['status'] == 'delivery_incomplete' else report['exit_code']
        return {'status': 'completed', 'health_status': report['status'],
                'health_failure_code': fault, 'delivery': delivery, 'exit_code': code,
                'release_gate_verified': False}
    finally:
        # Keep inode in place: unlinking a lock allows concurrent distinct locks.
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--lock-file', required=True)
    parser.add_argument('--backup')
    parser.add_argument('--alert-config')
    args = parser.parse_args()
    try:
        result = run(args.database, lock_file=args.lock_file, backup=args.backup,
                     alert_config=args.alert_config)
    except Exception:
        result = {'status': 'operator_configuration_or_execution_failed', 'exit_code': 6,
                  'release_gate_verified': False}
    print(json.dumps(result, sort_keys=True))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
