"""Regression tests for OBS-001/002. Only owned disposable fixtures/processes."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('repaired_author', HERE / 'test_runtime_observation.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
o = author.o


class StorageRepairTests(unittest.TestCase):
    def fixture(self, directory):
        base = Path(directory).resolve() / 'fixture'
        (base / 'support').mkdir(parents=True)
        target = base / 'support/tideglass-study.json'
        target.write_bytes(b'ALLOWED SYNTHETIC BYTES')
        outside = base.parent / 'outside-sentinel'
        outside.write_bytes(b'OUTSIDE SYNTHETIC BYTES MUST NOT BE READ')
        return base, target, outside

    def test_leaf_replacement_at_descriptor_open_rejected_without_read(self):
        for replacement in ('symlink', 'fifo', 'regular'):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                base, target, outside = self.fixture(directory)
                original_open, original_read = os.open, os.read
                swapped, reads = [], []

                def racing_open(path, *args, **kwargs):
                    if path == target.name and not swapped:
                        swapped.append(True)
                        target.unlink()
                        if replacement == 'symlink': target.symlink_to(outside)
                        elif replacement == 'fifo': os.mkfifo(target)
                        else: target.write_bytes(b'REPLACEMENT SYNTHETIC FILE')
                    return original_open(path, *args, **kwargs)

                def monitored_read(*args):
                    reads.append(True)
                    return original_read(*args)

                start = time.monotonic()
                with patch.object(os, 'open', racing_open), patch.object(os, 'read', monitored_read):
                    with self.assertRaises((ValueError, OSError)):
                        o.local_storage(base)
                self.assertTrue(swapped, 'Injection must execute')
                self.assertFalse(reads, 'Rejected replacement bytes must not be read')
                self.assertLess(time.monotonic() - start, .5)

    def test_component_replacement_at_open_rejects_symlink_and_directory(self):
        for kind in ('symlink', 'directory'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base, _, _ = self.fixture(directory)
                original = os.open
                swapped = []

                def racing_open(path, *args, **kwargs):
                    if path == 'support' and not swapped:
                        swapped.append(True)
                        (base / 'support').rename(base / 'original-support')
                        if kind == 'symlink': (base / 'support').symlink_to(base / 'original-support')
                        else: (base / 'support').mkdir()
                    return original(path, *args, **kwargs)

                with patch.object(os, 'open', racing_open):
                    with self.assertRaises((ValueError, OSError)):
                        o.local_storage(base)
                self.assertTrue(swapped)

    def test_root_identity_pinned_between_host_and_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            base, _, _ = self.fixture(directory)
            expected = o.storage_root_identity(base)
            base.rename(base.parent / 'old-fixture')
            base.mkdir()
            with self.assertRaisesRegex(ValueError, 'root replaced'):
                o.local_storage(base, expected_root=expected)

    def test_missing_host_anchor_rejected_before_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            base, _, _ = self.fixture(directory)
            host = object.__new__(o.Host)
            host.platform, host.base = 'ios', base
            host.command = lambda *_: self.fail('command invoked for unsafe root')
            base.rename(base.parent / 'old-fixture')
            base.symlink_to(base.parent / 'old-fixture')
            with self.assertRaises((ValueError, OSError)):
                host.storage()

    def test_native_worker_rejects_root_replacement_after_host_validation(self):
        for kind in ('symlink', 'directory'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base, _, _ = self.fixture(directory)
                host = object.__new__(o.Host)
                host.platform, host.base = 'ios', base
                host.storage_root_identity = o.storage_root_identity(base)
                host.commands, host.runner = [], subprocess.run
                host.deadline = time.monotonic() + 2
                base.rename(base.parent / 'old-fixture')
                if kind == 'symlink': base.symlink_to(base.parent / 'old-fixture')
                else: base.mkdir()
                with self.assertRaisesRegex(ValueError, 'command unavailable'):
                    host.storage()
                self.assertEqual(len(host.commands), 1)

    def test_root_component_and_leaf_swapped_after_open_are_detected(self):
        for kind in ('root', 'component', 'leaf'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base, target, _ = self.fixture(directory)
                original_read = os.read
                swapped = []

                def racing_read(fd, count):
                    block = original_read(fd, count)
                    if not swapped:
                        swapped.append(True)
                        path = {'root': base, 'component': base / 'support', 'leaf': target}[kind]
                        path.rename(path.with_name(path.name + '-old'))
                        if kind == 'leaf': path.write_bytes(b'NEW LEAF')
                        else: path.mkdir()
                    return block

                with patch.object(os, 'read', racing_read):
                    with self.assertRaises((ValueError, OSError)):
                        o.local_storage(base)
                self.assertTrue(swapped)

    def test_same_inode_mutation_and_hardlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base, target, _ = self.fixture(directory)
            original_read = os.read
            mutated = []

            def racing_read(fd, count):
                block = original_read(fd, count)
                if not mutated:
                    mutated.append(True)
                    target.write_bytes(b'X' * len(block))
                return block

            with patch.object(os, 'read', racing_read):
                with self.assertRaisesRegex(ValueError, 'mutated'):
                    o.local_storage(base)
            os.link(target, base.parent / 'outside-hardlink')
            with self.assertRaisesRegex(ValueError, 'hard link'):
                o.local_storage(base)

    def test_bounded_read_reports_same_descriptor_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            base, target, _ = self.fixture(directory)
            info = target.stat()
            row = o.local_storage(base)['support/tideglass-study.json']
            self.assertEqual(row['inode'], info.st_ino)
            self.assertEqual(row['device'], info.st_dev)
            self.assertEqual(row['size'], info.st_size)
            self.assertEqual(row['sha256'], o.sha(target.read_bytes()))
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.local_storage(base, deadline=time.monotonic() - 1)

    def test_native_caller_enforces_actual_worker_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            base, _, _ = self.fixture(directory)
            worker = base.parent / 'blocked-worker.py'
            worker.write_text('import time\ntime.sleep(60)\n')
            host = object.__new__(o.Host)
            host.platform, host.base = 'ios', base
            host.storage_root_identity = o.storage_root_identity(base)
            host.commands, host.runner = [], subprocess.run
            host.deadline = time.monotonic() + .2
            start = time.monotonic()
            with patch.object(o, 'COLLECTOR_PATH', worker):
                with self.assertRaises(subprocess.TimeoutExpired): host.storage()
            self.assertLess(time.monotonic() - start, 1)

    def test_real_storage_worker_is_bounded_and_source_identified(self):
        with tempfile.TemporaryDirectory() as directory:
            base, target, _ = self.fixture(directory)
            host = object.__new__(o.Host)
            host.platform, host.base = 'ios', base
            host.storage_root_identity = o.storage_root_identity(base)
            host.commands, host.runner = [], subprocess.run
            host.deadline = time.monotonic() + 2
            self.assertEqual(host.storage()['support/tideglass-study.json']['sha256'], o.sha(target.read_bytes()))
            self.assertEqual(len(host.commands), 1)

    def test_android_storage_is_unavailable_without_shell_or_command(self):
        host = object.__new__(o.Host)
        host.platform = 'android'
        host.command = lambda *_: self.fail('Android shell storage must never run')
        with self.assertRaisesRegex(ValueError, 'Android storage unavailable'):
            host.storage()


class SourceRepairTests(unittest.TestCase):
    def fixture(self, directory):
        return author.FinalizationTests().prepare(Path(directory).resolve())

    def test_only_open_log_read_allows_same_inode_append(self):
        for allowed in (False, True):
            with self.subTest(allowed=allowed), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'active-run.log'
                path.write_bytes(b'INITIAL\n')
                original_read = os.read
                appended = []

                def racing_read(fd, count):
                    block = original_read(fd, count)
                    if not appended:
                        appended.append(True)
                        with path.open('ab') as stream: stream.write(b'APPENDED\n')
                    return block

                with patch.object(os, 'read', racing_read):
                    if allowed:
                        self.assertEqual(o.read_bounded(path, allow_append=True), b'INITIAL\nAPPENDED\n')
                    else:
                        with self.assertRaisesRegex(ValueError, 'changed during read'):
                            o.read_bounded(path)

    def test_each_preserved_source_archive_is_required_and_exact(self):
        for name in ('collector.py', 'completion-verifier.py', 'native-runner.py', 'candidate-manifest.json'):
            for defect in ('missing', 'changed'):
                with self.subTest(name=name, defect=defect), tempfile.TemporaryDirectory() as directory:
                    _, output, _ = self.fixture(directory)
                    path = output / name
                    if defect == 'missing': path.unlink()
                    else: path.write_bytes(b'CHANGED SYNTHETIC ARCHIVE')
                    with self.assertRaises((ValueError, OSError)): o.finalize(output, Path('/unused'))
                    self.assertFalse((output / 'finalization.json').exists())

    def test_runner_and_candidate_verifier_binding_must_match(self):
        for target in ('verify_native.py', 'runner.py', 'candidate-verifier', 'manifest', 'runner-pin'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                evidence, output, verification = self.fixture(directory)
                report = json.loads((output / 'observation.json').read_text())
                candidate = Path(report['candidate'])
                if target == 'candidate-verifier':
                    path = candidate / 'source/tool/verify_native.py'
                elif target == 'manifest': path = candidate / 'manifest.json'
                elif target == 'runner-pin':
                    verification['source_pins']['verify_native.py'] = '0' * 64
                    (evidence / 'verification.json').write_text(json.dumps(verification))
                    path = None
                else: path = evidence / target
                if path: path.write_bytes(path.read_bytes() + b'\n# CHANGED\n')
                with self.assertRaises((ValueError, OSError)): o.finalize(output, Path('/unused'))

    def test_collector_changed_after_module_load_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = self.fixture(directory)
            changed = Path(directory) / 'changed-collector.py'
            changed.write_bytes(o.COLLECTOR_BYTES + b'\n# CHANGED\n')
            with patch.object(o, 'COLLECTOR_PATH', changed):
                with self.assertRaisesRegex(ValueError, 'Collector source changed'):
                    o.finalize(output, Path('/unused'))

    def test_preserved_collector_special_replacement_cannot_block(self):
        for kind in ('fifo', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                _, output, _ = self.fixture(directory)
                target = output / 'collector.py'
                target.unlink()
                if kind == 'fifo': os.mkfifo(target)
                else: target.symlink_to(HERE / 'runtime_observation.py')
                start = time.monotonic()
                with self.assertRaises((ValueError, OSError)):
                    o.finalize(output, Path('/unused'))
                self.assertLess(time.monotonic() - start, .5)

    def test_sys_modules_and_arbitrary_root_cannot_replace_completion_check(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, output, verification = self.fixture(directory)
            text = (evidence / 'run.log').read_text().replace('+1:', '+0:')
            (evidence / 'run.log').write_text(text)
            verification['evidence_sha256']['run.log'] = o.sha(text.encode())
            (evidence / 'verification.json').write_text(json.dumps(verification))
            root = Path(directory) / 'untrusted-root'
            (root / 'tool').mkdir(parents=True)
            sentinel = root / 'executed'
            (root / 'tool/verify_native.py').write_text(f'from pathlib import Path\nPath({str(sentinel)!r}).touch()\ndef native_log_errors(value): return []\n')
            fake = types.SimpleNamespace(native_log_errors=lambda _: [])
            before = list(sys.path)
            with patch.dict(sys.modules, {'verify_native': fake}):
                with self.assertRaisesRegex(ValueError, 'completion failed'):
                    o.finalize(output, root)
            self.assertFalse(sentinel.exists())
            self.assertEqual(before, sys.path)

    def test_source_replacement_during_finalization_cannot_publish(self):
        for name in ('collector.py', 'completion-verifier.py'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                _, output, _ = self.fixture(directory)
                original = o.archived_completion_errors

                def replacing_verifier(source, log):
                    result = original(source, log)
                    (output / name).write_bytes(b'CHANGED DURING FINALIZATION')
                    return result

                with patch.object(o, 'archived_completion_errors', replacing_verifier):
                    with self.assertRaises(ValueError): o.finalize(output, Path('/unused'))
                self.assertFalse((output / 'finalization.json').exists())

    def test_unavailable_storage_retains_partial_status(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = self.fixture(directory)
            path = output / 'observation.json'
            report = json.loads(path.read_text())
            report['samples'][0]['storage'] = {'status': 'unavailable', 'reason': 'Android reader unqualified'}
            path.write_text(json.dumps(report))
            result = o.finalize(output, Path('/unused'))
            self.assertEqual(result['status'], 'finalized-partial-observation')
            self.assertEqual(result['paired_socket_storage_samples'], 0)
            self.assertFalse(result['release_acceptance'])

    def test_collection_rechecks_collector_before_pending_status(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, old_output, _ = self.fixture(directory)
            old = json.loads((old_output / 'observation.json').read_text())
            (evidence / 'run.log').write_bytes((old_output / 'open-prefix.log').read_bytes())
            output = Path(directory).resolve() / 'new-observation'
            copy = output.parent / 'collector-copy.py'
            copy.write_bytes(o.COLLECTOR_BYTES)

            class FakeHost:
                def __init__(self, *_): self.commands = []
                def identity(self): return {'pid': 123}
                def sockets(self): return []
                def storage(self):
                    copy.write_bytes(o.COLLECTOR_BYTES + b'\n# changed during collection\n')
                    return {}

            with patch.object(o, 'Host', FakeHost), patch.object(o, 'COLLECTOR_PATH', copy):
                result = o.collect(Path('/unused'), Path(old['candidate']), evidence, old['device'], output)
            self.assertEqual(result['status'], 'failed')
            self.assertIn('Collector source changed', str(result['errors']))
            self.assertFalse((output / 'finalization.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
