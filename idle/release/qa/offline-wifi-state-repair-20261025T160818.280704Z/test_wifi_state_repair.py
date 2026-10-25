"""Pure parser and protocol regressions; no network, device or child process."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

import offline_support as subject
from test_offline_protocol import fixture

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
ACTUAL = ROOT / 'release/native-proof/integration-android-offline-20261025T160235.910710Z'


def snapshots_with_three(args):
    for row in args[3]['snapshots']:
        if row['marker']['phase'].startswith('offline-'):
            row['commands']['wifi']['stdout'] = '3'
    return args


class WifiStateRepairTests(unittest.TestCase):
    def test_exact_actual_rows_keep_raw_three(self):
        rows = json.loads((ACTUAL / 'os-snapshots.json').read_text())['snapshots']
        self.assertEqual([subject.parse_os(r) for r in rows], [
            {'airplane': '0', 'wifi': '1', 'data': '1', 'default': '102'},
            {'airplane': '1', 'wifi': '3', 'data': '1', 'default': 'none'},
            {'airplane': '1', 'wifi': '3', 'data': '1', 'default': 'none'},
        ])

    def test_before_parser_reproduces_original_rejection(self):
        spec = importlib.util.spec_from_file_location('original_offline_support', STAGE / 'before/offline_support.py')
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        row = json.loads((ACTUAL / 'os-snapshots.json').read_text())['snapshots'][1]
        with self.assertRaisesRegex(ValueError, 'Unknown actual radio settings'):
            old.parse_os(row)

    def test_three_synthetic_start_and_reload_preserve_raw_output(self):
        start = snapshots_with_three(fixture())
        result = subject.qualify(*start)
        self.assertEqual(result['states']['offline-ready']['wifi'], '3')
        reload = snapshots_with_three(fixture('natural-reload', start[0]))
        result = subject.qualify(*reload, predecessor=start[0])
        self.assertEqual(result['states']['after-restored']['wifi'], '1')

    def test_three_without_airplane_is_rejected(self):
        row = deepcopy(fixture()[3]['snapshots'][1])
        row['commands']['airplane']['stdout'] = '0'
        row['commands']['wifi']['stdout'] = '3'
        with self.assertRaisesRegex(ValueError, 'without airplane mode'):
            subject.parse_os(row)

    def test_three_cannot_be_before_or_restored_state(self):
        for scenario in ('natural-start', 'natural-reload'):
            prior = fixture()[0] if scenario == 'natural-reload' else None
            args = snapshots_with_three(fixture(scenario, prior))
            row = args[3]['snapshots'][0 if prior is None else -1]
            row['commands']['airplane']['stdout'] = '1'
            row['commands']['wifi']['stdout'] = '3'
            with self.subTest(scenario=scenario), self.assertRaisesRegex(ValueError, 'Before/restored OS network not active'):
                subject.qualify(*args, predecessor=prior)

    def test_enabled_override_and_unknown_values_never_qualify_offline(self):
        for value in ('1', '2', '-1', '4', 'true', 'null', ''):
            args = snapshots_with_three(fixture())
            args[3]['snapshots'][1]['commands']['wifi']['stdout'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                subject.qualify(*args)

    def test_three_with_actual_default_network_is_rejected(self):
        args = snapshots_with_three(fixture())
        args[3]['snapshots'][1]['commands']['connectivity']['stdout'] = 'Active default network: 102'
        with self.assertRaisesRegex(ValueError, 'actual default network/wifi still available'):
            subject.qualify(*args)

    def test_three_with_reachable_app_endpoint_is_rejected(self):
        args = snapshots_with_three(fixture())
        next(row for row in args[0]['offline_network']['samples'] if row['phase'] == 'bootstrap')['reachable'] = True
        with self.assertRaisesRegex(ValueError, 'App endpoint remained reachable'):
            subject.qualify(*args)

    def test_three_without_independent_listener_health_is_rejected(self):
        args = snapshots_with_three(fixture())
        args[2].clear()
        with self.assertRaisesRegex(ValueError, 'Incomplete listener journal'):
            subject.qualify(*args)

    def test_three_with_listener_failure_is_rejected(self):
        args = snapshots_with_three(fixture())
        from test_offline_protocol import iso
        next(row for row in args[2] if row['type'] == 'health' and row['host_utc'] == iso(22))['ok'] = False
        with self.assertRaisesRegex(ValueError, 'Listener failure overlaps'):
            subject.qualify(*args)

    def test_three_without_successful_reconnection_is_rejected(self):
        start = snapshots_with_three(fixture())
        args = snapshots_with_three(fixture('natural-reload', start[0]))
        for row in args[0]['offline_network']['samples']:
            if row['phase'] == 'after-restored':
                row.update(reachable=False, error_type='SocketException')
        with self.assertRaisesRegex(ValueError, 'Missing three actual reconnection probes'):
            subject.qualify(*args, predecessor=start[0])

    def test_unchanged_helpers_bind_raw_restoration_and_failed_predecessor(self):
        import ast
        new = ast.parse((STAGE / 'offline_support.py').read_text())
        old = ast.parse((STAGE / 'before/offline_support.py').read_text())
        for name in ('finish', 'load_predecessor', 'snapshot_os', 'run_command', 'challenge', 'validate_profile'):
            select = lambda tree: next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            self.assertEqual(ast.dump(select(new)), ast.dump(select(old)), name)
        # In particular, do not normalize 3 to 0 and thereby hide restoration drift.
        self.assertIn("any(before[k] != after[k] for k in ('airplane', 'wifi', 'data'))", (STAGE / 'offline_support.py').read_text())

    def test_all_pins_and_runtime_harness_unchanged(self):
        for path, expected in json.loads((STAGE / 'source-before.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)
        for name in ('verify_offline_native.py', 'platform_smoke_offline_test.dart', 'test_offline_protocol.py'):
            self.assertEqual((STAGE / name).read_bytes(), (STAGE / 'before' / name).read_bytes(), name)
        report = json.loads((ACTUAL / 'verification.json').read_text())
        self.assertFalse(report['passed'])
        self.assertEqual(report['verification_errors'], ['Offline qualification: Unknown actual radio settings'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
