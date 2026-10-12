import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from tools.buying_v2.seller_history import SellerHistory


class SellerHistoryTests(unittest.TestCase):
    def sample(self, h, tick=1, channel='retail', **changes):
        args = dict(channel=channel, tick=tick, product=[4, 5, 6], owner=[0, 1, 1],
                    offered=[1, 1, 0], opening=[5, 0, 3], closing=[3, 0, 3],
                    quote=[2, 4, np.nan], sold=[2, 0, 0],
                    exposure=[[2, 3, 0], [1, 2, 0], [0, 2, 0]])
        args.update(changes)
        h.record(**args)

    def same(self, a, b):
        self.assertEqual(set(a.channels), set(b.channels))
        for channel in a.channels:
            x, y = a.view(channel), b.view(channel)
            self.assertEqual(set(x), set(y))
            for key in x:
                np.testing.assert_array_equal(x[key], y[key])

    def test_stock_constrained_zero_and_unobserved_are_distinct(self):
        h = SellerHistory(3)
        self.sample(h)
        v = h.view('retail')
        np.testing.assert_array_equal(v['sold'], [[2, 0, 0]])
        np.testing.assert_array_equal(v['shortChecks'], [[0, 2, 0]])
        np.testing.assert_array_equal(v['offered'], [[1, 1, 0]])
        self.assertTrue(np.isnan(v['quote'][0, 2]))
        # An offered seller with no discovery still has measured zero sales,
        # but there was no buyer observation supporting a zero-demand estimate.
        self.sample(h, 2, sold=[0, 0, 0], closing=[5, 0, 3], exposure=np.zeros((3, 3)))
        self.assertEqual(h.view('retail')['discoveries'][1, 0], 0)

    def test_same_tick_replenishment_is_separated_by_phase(self):
        h = SellerHistory(3)
        self.sample(h, channel='retail', opening=[2, 0, 3], closing=[0, 0, 3],
                    exposure=[[2, 3, 0], [2, 2, 0], [1, 2, 0]])
        self.sample(h, channel='input-C4', opening=[10, 0, 3], closing=[8, 0, 3])
        self.assertEqual(h.view('retail')['closingStock'][0, 0], 0)
        self.assertEqual(h.view('retail')['shortChecks'][0, 0], 1)
        self.assertEqual(h.view('input-C4')['closingStock'][0, 0], 8)
        self.assertEqual(h.view('input-C4')['shortChecks'][0, 0], 0)

    def test_ring_wrap_and_returned_views_do_not_alias(self):
        h = SellerHistory(2)
        for tick in range(5, 9):
            self.sample(h, tick)
        v = h.view('retail')
        np.testing.assert_array_equal(v['ticks'], [7, 8])
        v['sold'][:] = 100
        self.assertEqual(h.view('retail')['sold'][0, 0], 2)

    def test_append_only_identity_preserves_missing_historical_offer(self):
        h = SellerHistory(3)
        self.sample(h)
        self.sample(h, 2, product=[4, 5, 6, 7], owner=[0, 1, 1, 2],
                    offered=[1, 1, 0, 1], opening=[5, 0, 3, 1], closing=[3, 0, 3, 1],
                    quote=[2, 4, np.nan, 9], sold=[2, 0, 0, 0],
                    exposure=[[2, 3, 0, 0], [1, 2, 0, 0], [0, 2, 0, 0]])
        v = h.view('retail')
        self.assertTrue(np.isnan(v['quote'][0, 3]))
        np.testing.assert_array_equal(v['offered'][:, 3], [0, 1])
        for changes in (dict(product=[4, 9, 6, 7], owner=[0, 1, 1, 2]),
                        dict(product=[4, 5, 6, 7], owner=[0, 9, 1, 2])):
            state = h.channels['retail']
            with self.assertRaises(ValueError):
                self.sample(h, 3, **changes)
            self.assertEqual(state['lastTick'], 2)
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.sample(h, 3)  # shrinking the column set

    def test_invalid_record_rejected_before_mutation(self):
        h = SellerHistory(3)
        self.sample(h)
        cases = [dict(product=[4, 9, 6]), dict(owner=[0, 9, 1]), dict(tick=1), dict(tick=3), dict(tick=2.0), dict(lot=2),
                 dict(product=[4.5, 5, 6]), dict(owner=[0, -1, 1]),
                 dict(opening=[6, 0, 3]), dict(quote=[0, 4, np.nan]),
                 dict(offered=[1, 2, 0]), dict(sold=[np.nan, 0, 0]),
                 dict(exposure=[[0, 3, 0], [0, 2, 0], [0, 2, 0]]),
                 dict(exposure=[[2, 3, 1], [1, 2, 0], [0, 2, 0]]),
                 dict(exposure=[[2, 3, 0], [1, 2, 0], [2, 2, 0]]),
                 dict(exposure=[[2.5, 3, 0], [1, 2, 0], [0, 2, 0]]),
                 dict(exposure=[[2**32, 3, 0], [1, 2, 0], [0, 2, 0]])]
        before = h.view('retail')
        for changes in cases:
            args = dict(tick=2)
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.sample(h, **args)
            for key, value in before.items():
                np.testing.assert_array_equal(h.view('retail')[key], value)

    def test_checkpoint_continuation_partial_and_full_ring(self):
        for stop in (1, 2, 5):
            with self.subTest(stop=stop), tempfile.TemporaryDirectory() as directory:
                h = SellerHistory(3)
                for tick in range(1, stop + 1):
                    self.sample(h, tick)
                    self.sample(h, tick, channel='input-C4')
                path = Path(directory) / 'history.npz'
                h.save(path)
                restored = SellerHistory.load(path, expected_tick=stop, expected_channels=['retail', 'input-C4'])
                self.same(h, restored)
                for tick in range(stop + 1, stop + 5):
                    for channel in h.channels:
                        self.sample(h, tick, channel=channel)
                        self.sample(restored, tick, channel=channel)
                self.same(h, restored)
                with self.assertRaisesRegex(ValueError, 'tick mismatch'):
                    SellerHistory.load(path, expected_tick=stop + 1)
                with self.assertRaisesRegex(ValueError, 'channel coverage'):
                    SellerHistory.load(path, expected_channels=['retail'])

    def test_save_never_overwrites_and_failed_write_removes_own_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.npz'
            h = SellerHistory(3)
            self.sample(h)
            path.write_bytes(b'prior evidence')
            with self.assertRaises(FileExistsError):
                h.save(path)
            self.assertEqual(path.read_bytes(), b'prior evidence')
            partial = Path(directory) / 'partial.npz'
            with patch('tools.buying_v2.seller_history.np.savez_compressed', side_effect=OSError('write failed')):
                with self.assertRaisesRegex(OSError, 'write failed'):
                    h.save(partial)
            self.assertFalse(partial.exists())

    def test_corrupt_checkpoint_metadata_and_values_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.npz'
            h = SellerHistory(3)
            self.sample(h)
            h.save(path)
            with np.load(path) as archive:
                original = {k: archive[k].copy() for k in archive.files}
            def metadata_change(data, key, value, channel=False):
                meta = json.loads(data['metadata'].tobytes())
                (meta['channels'][0] if channel else meta)[key] = value
                data['metadata'] = np.frombuffer(json.dumps(meta).encode(), dtype=np.uint8)
            mutations = [lambda d: metadata_change(d, 'version', 99),
                         lambda d: metadata_change(d, 'catalog', 'other'),
                         lambda d: metadata_change(d, 'cursor', 2, True),
                         lambda d: metadata_change(d, 'lot', 1.5, True),
                         lambda d: metadata_change(d, 'window', True),
                         lambda d: d.update(c0_discoveries=d['c0_discoveries'].astype(float)),
                         lambda d: d['c0_offered'].__setitem__((0, 0), 2),
                         lambda d: d['c0_quote'].__setitem__((0, 2), 4),
                         lambda d: d['c0_sold'].__setitem__((0, 2), 1),
                         lambda d: d['c0_closingStock'].__setitem__((2, 0), 1),
                         lambda d: d['c0_fundedChecks'].__setitem__((0, 0), 0),
                         lambda d: d['c0_ticks'].__setitem__(2, -1),
                         lambda d: d['c0_product'].__setitem__(0, -1),
                         lambda d: d.pop('c0_shortChecks')]
            for i, mutate in enumerate(mutations):
                data = {k: v.copy() for k, v in original.items()}
                mutate(data)
                invalid = Path(directory) / f'invalid-{i}.npz'
                np.savez(invalid, **data)
                with self.subTest(i=i), self.assertRaises(ValueError):
                    SellerHistory.load(invalid)

    def test_empty_history_is_not_valid_checkpoint_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.npz'
            h = SellerHistory(3)
            h.save(path)
            self.assertEqual(SellerHistory.load(path).channels, {})
            with self.assertRaisesRegex(ValueError, 'empty seller history'):
                SellerHistory.load(path, expected_tick=1)
        for window in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                SellerHistory(window)


if __name__ == '__main__':
    unittest.main()
