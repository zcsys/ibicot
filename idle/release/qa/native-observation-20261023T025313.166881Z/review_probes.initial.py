"""Independent, disposable-fixture counterexamples. No device or Flutter use."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = ROOT / 'release/native-privacy/runtime-observation-staged'
spec = importlib.util.spec_from_file_location('author_fixture', STAGE / 'test_runtime_observation.py')
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
o = author.o


class ReviewProbes(unittest.TestCase):
    def test_existing_success_control(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = author.FinalizationTests().prepare(Path(directory))
            self.assertEqual(o.finalize(output, ROOT)['status'], 'finalized-sampled-observation')

    def test_preserved_collector_must_match_claimed_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = author.FinalizationTests().prepare(Path(directory))
            (output / 'collector.py').write_text('CHANGED COLLECTOR EVIDENCE\n')
            with self.assertRaisesRegex(ValueError, 'collector|Collector'):
                o.finalize(output, ROOT)

    def test_missing_collector_must_not_finalize(self):
        with tempfile.TemporaryDirectory() as directory:
            _, output, _ = author.FinalizationTests().prepare(Path(directory))
            self.assertFalse((output / 'collector.py').exists())
            with self.assertRaises((ValueError, OSError)):
                o.finalize(output, ROOT)

    def test_fixture_leaf_swapped_to_symlink_before_open_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'fixture'
            (base / 'support').mkdir(parents=True)
            target = base / 'support/tideglass-study.json'
            target.write_text('SYNTHETIC ALLOWED BYTES')
            outside = Path(directory) / 'outside-synthetic-sentinel'
            outside.write_text('DISPOSABLE OUTSIDE SENTINEL')
            original_open = Path.open
            swapped = False

            def racing_open(path, *args, **kwargs):
                nonlocal swapped
                if path == target and not swapped:
                    swapped = True
                    path.unlink()
                    path.symlink_to(outside)
                return original_open(path, *args, **kwargs)

            with patch.object(Path, 'open', racing_open):
                try:
                    result = o.local_storage(base)
                except (ValueError, OSError):
                    return
            (HERE / 'accepted-outside-fixture-read.json').write_text(json.dumps({
                'synthetic_only': True,
                'result': result,
                'outside_sentinel_sha256': o.sha(outside.read_bytes()),
                'outside_bytes_read': result['support/tideglass-study.json']['sha256'] == o.sha(outside.read_bytes()),
            }, indent=2) + '\n')
            self.fail('Fixture leaf changed after lstat; collector read/hash came from outside its fixed fixture')

    def test_fixture_root_swapped_after_validation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'fixture'
            base.mkdir()
            outside = Path(directory) / 'outside'
            (outside / 'support').mkdir(parents=True)
            (outside / 'support/tideglass-study.json').write_text('DISPOSABLE OUTSIDE SENTINEL')
            host = object.__new__(o.Host)
            host.platform, host.base = 'ios', base
            # Reproduces the post-Host.__init__, pre-Host.storage boundary.
            base.rmdir()
            base.symlink_to(outside, target_is_directory=True)
            with self.assertRaises((ValueError, OSError)):
                host.storage()

    def test_leaf_replaced_with_fifo_cannot_exceed_host_budget(self):
        script = r'''
import importlib.util, os
from pathlib import Path
from unittest.mock import patch
import sys, tempfile
spec=importlib.util.spec_from_file_location('o',sys.argv[1]);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
with tempfile.TemporaryDirectory() as directory:
 base=Path(directory);(base/'support').mkdir();target=base/'support/tideglass-study.json';target.write_text('fixture')
 original=Path.open
 def racing_open(path,*args,**kwargs):
  if path==target:
   path.unlink();os.mkfifo(path)
  return original(path,*args,**kwargs)
 with patch.object(Path,'open',racing_open):
  try:o.local_storage(base)
  except (ValueError,OSError):pass
'''
        try:
            subprocess.run([sys.executable, '-c', script, str(STAGE / 'runtime_observation.py')], capture_output=True, timeout=1, check=True)
        except subprocess.TimeoutExpired:
            self.fail('Local FIFO open blocks outside Host.command deadline; disposable child was terminated by reviewer timeout')

    def test_socket_wrong_package_uid_and_missing_table_remain_rejected(self):
        rows = b'FD|123\nTABLE|tcp\nSOCKET|tcp|10123|123|0100007F:0010|00000000:0000|0A\nTABLE|tcp6\nTABLE|udp\nTABLE|udp6\n'
        self.assertEqual(len(o.parse_android_sockets(rows, 10123)), 1)
        for wrong in [rows.replace(b'FD|123', b'FD|124'), rows.replace(b'|10123|', b'|10124|'), rows.replace(b'TABLE|udp6\n', b'')]:
            with self.assertRaises(ValueError): o.parse_android_sockets(wrong, 10123)

    def test_protected_device_rejected_before_input_read(self):
        with patch.object(o, 'context_for', side_effect=AssertionError('input accessed')):
            with self.assertRaisesRegex(ValueError, 'Protected'):
                o.collect(Path('/missing'), Path('/missing'), Path('/missing'), o.PROTECTED, Path('/missing'))

    def test_hook_changes_are_exact_and_no_default_define(self):
        before = (STAGE / 'baseline/tool/verify_current_runtime.py').read_text()
        after = (STAGE / 'source/tool/verify_current_runtime.py').read_text()
        self.assertNotIn('TIDEGLASS_PRIVACY_OBSERVATION', before)
        self.assertIn("if observe_privacy:\n            command.append('--dart-define=TIDEGLASS_PRIVACY_OBSERVATION=true')", after)
        self.assertIn("require(not observe_privacy or args.scenario in ('runtime-study-default', 'runtime-study-enroll')", after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
