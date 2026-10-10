"""Differential checks for optimized ranking, arithmetic and wire output."""
import asyncio
import copy
import json
import unittest
from unittest.mock import patch

import numpy as np

from economy.core import model as M
from economy.core.state import reset_world, T0P, add_tier2_line
from economy.core.trading import select_offer
from economy.kernel import numba as fast
from economy.kernel import tick as reference
from economy.server.aggregates import (project_refineries, _project, project_manufacturing,
                                      ManufacturingView, _T2_FIELDS, _manufacturing_numpy)
from economy.server.runtime import KernelRuntime
from economy.server.service import _ConnectionManager


class PerformanceTests(unittest.TestCase):
    def test_grouped_going_rates_preserve_numpy_reductions(self):
        rng = np.random.default_rng(831)
        for n in (0, 1, 7, 128, 129, 1000, 60000):
            markets = rng.integers(0, 200, n)
            prices = rng.random(n) * 1e9
            sales = rng.random(n) * 1e6
            prices[::13] = np.nan
            prices[::17] = np.inf
            sales[markets % 3 == 0] = 0
            expected = np.zeros(200)
            for m in range(200):
                p, w = prices[markets == m], sales[markets == m]
                finite = np.isfinite(p)
                p, w = p[finite], w[finite]
                if p.size:
                    expected[m] = (p * w).sum() / w.sum() if w.sum() > 0 else p.mean()
            actual = reference._market_going_rate(prices, sales, markets, 200)
            self.assertEqual(actual.tobytes(), expected.tobytes())

    @unittest.skipUnless(fast._HAVE_NUMBA, 'Numba not installed')
    def test_stock_index_matches_order_ranking_as_stock_depletes(self):
        rng = np.random.default_rng(7219)
        sizes = np.array([0, 1, 7, 16, 31, 60, 99, 100, 200, 1000])
        off = np.r_[0, np.cumsum(sizes)].astype(np.int64)
        n = int(off[-1])
        prices = rng.integers(1, 60, n).astype(float) / 7
        stocks = rng.integers(0, 200, n).astype(float) / 2
        reliability = rng.random(n) * 3 - 1
        reliability[::33] = np.nan
        offers = np.concatenate([np.arange(off[m], off[m + 1])[np.argsort(prices[off[m]:off[m + 1]], kind='stable')]
                                 for m in range(M.NP)])
        tree, positions, width = fast._stock_index(offers, off, stocks)
        for step in range(2500):
            m = step % M.NP
            preferred = int(rng.integers(-1, n))
            request = float(rng.choice([0, .5, 1, 2, 17, 100, 150]))
            unit, multiple = 1.87, .735
            expected = select_offer(offers[off[m]:off[m + 1]], stocks, prices, preferred,
                                    reliability, request, unit, multiple)
            actual = fast._indexed_supplier(tree, width, m, offers, off[m], off[m + 1],
                                            stocks, prices, preferred, reliability, request, unit, multiple)
            self.assertEqual(actual, expected, (step, m, request))
            if sizes[m]:
                supplier = int(rng.integers(off[m], off[m + 1]))
                stocks[supplier] = max(0, stocks[supplier] - rng.integers(1, 80))
                fast._update_stock_index(tree, m, positions[supplier], stocks[supplier])

    @unittest.skipUnless(fast._HAVE_NUMBA, 'Numba not installed')
    def test_refinery_production_and_research_observation_match_reference(self):
        cfg, w = reset_world({'t2FirmCount': 200, 'distributorCount': 400,
                              'storage': 70000, 't1Capacity': 17433, 'conversionFactor': .371,
                              'researchPriceMinimumOpportunities': 2})
        rng = np.random.default_rng(618)
        w.t1Operates[:] = rng.integers(0, 2, len(w.t1Operates))
        for name in ('raw', 'rawBasis', 't1Fin', 't1FinBasis', 't1Price', 't1Cash'):
            arr = getattr(w, name)
            arr[:] = rng.random(len(arr)) * (10000 if name in ('raw', 't1Fin', 't1Cash') else 5)
        w.costSinks = 12345.6789
        expected = copy.deepcopy(w)
        reference.operate_tier1(expected, cfg, M.PRODUCTS)
        fast.operate_tier1(w, cfg)
        for name in w.array_names:
            self.assertEqual(getattr(w, name).tobytes(), getattr(expected, name).tobytes(), name)
        self.assertEqual(w.costSinks, expected.costSinks)
        # All products and unequal line counts make opportunity denominators
        # sensitive to accumulation order, unlike a single-product smoke test.
        w.t2LineProduct[:200] = np.arange(200)
        other = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == 0 and p['id'] != 0)
        add_tier2_line(w, cfg, 0, other, paid=False)
        for tier in ('t0', 't1', 't2'):
            for suffix in ('Opportunities', 'Sold', 'Revenue', 'COGS', 'Demand'):
                a = getattr(w, tier + suffix)
                a[:] = rng.random(len(a)) * 123
        w.t2PotentialOrders[:] = rng.random(len(w.t2PotentialOrders)) * 40
        expected = copy.deepcopy(w)
        reference.observe_markets(expected, cfg, T0P)
        fast.observe_markets(w, cfg, T0P)
        for name in w.array_names:
            self.assertEqual(getattr(w, name).tobytes(), getattr(expected, name).tobytes(), name)

    def test_sort_columns_match_company_details_and_stable_ties(self):
        rt = KernelRuntime({'t2FirmCount': 200, 'distributorCount': 30, 'storage': 50000})
        rng = np.random.default_rng(902)
        for p in [p for p in M.T2_PRODUCTS if p['sectorIndex'] == 0 and p['id'] != 0][:3]:
            add_tier2_line(rt.world, rt.cfg, 0, p, paid=False)
        for name in ('t2Fin', 't2FinBasis', 't2Raw', 't2RawBasis', 't2T1Raw', 't2T1Basis',
                     't2Cash', 't2Made', 't2Revenue', 't2COGS', 't2Rel'):
            arr = getattr(rt.world, name)
            arr[:] = rng.random(len(arr)) * (1 if name == 't2Rel' else 117)
        ids = np.arange(200)
        rows = [rt._tier2_company(int(i), False) for i in ids]
        for key in ('name', 'sector', 'cash', 'equity', 'inventory', 'raw', 'finished',
                    'capacity', 'utilization', 'margin', 'revenue', 'grossProfit', 'reliability'):
            self.assertEqual(list(rt._tier2_sort_values(ids, key)), [r[key] for r in rows], key)
            keyfn = lambda r: (r[key].lower() if isinstance(r[key], str) else r[key], r['id'])
            for descending in (False, True):
                rt.tier2Query.update(sort=key, descending=descending, page=1)
                expected = sorted(rows, key=keyfn, reverse=descending)[50:100]
                self.assertEqual(rt._tier2_page()['rows'], expected, (key, descending))
        for search, sector, control in [('0x1', '', ''), ('', M.T2_SECTORS[0], 'BOT'),
                                       ('', '', 'PLAYER'), ('missing', '', ''), ('', 'missing', '')]:
            rt.tier2Query.update(search=search, sector=sector, controller=control, sort='id', descending=False, page=0)
            matches = [r for r in rows if (not sector or r['sector'] == sector)
                       and (not control or r['controller'] == control)
                       and (not search or search in (r['name'] + ' ' + r['sector'] + ' ' + r['controller']
                            + ''.join(' ' + p['name'] for p in r['products'])).lower())]
            page = rt._tier2_page()
            self.assertEqual(page['total'], len(matches))
            self.assertEqual(page['rows'], matches[:50])

    @unittest.skipUnless(fast._HAVE_NUMBA, 'Numba not installed')
    def test_storage_bound_large_capacity_and_multiline_plans_match_reference(self):
        cfg, w = reset_world({'t2FirmCount': 40, 'distributorCount': 1,
                              't2Capacity': {3: 45000, 4: 32000, 5: 27000}})
        w.t2LineProduct[:40] = np.arange(40)
        for p in [p for p in M.T2_PRODUCTS if p['sectorIndex'] == 0 and p['id'] != 0][:3]:
            add_tier2_line(w, cfg, 0, p, paid=False)
        rng = np.random.default_rng(313)
        w.t2Raw[:40 * M.NE] = rng.random(40 * M.NE) * 1000
        w.t2T1Raw[:40 * M.NP] = rng.random(40 * M.NP) * 1000
        w.t2RawBasis[:] = 1.17
        w.t2T1Basis[:] = 1.37
        w.t2Price[:w.t2LineCount] = 100
        w.t1Fin[w.t1Operates != 0] = 12345
        expected = copy.deepcopy(w)
        for tick in (1, 2, 17):
            reference.operate_tier2(expected, cfg, M.PRODUCTS, T0P, M.T2_PRODUCTS, tick)
            fast.operate_tier2(w, cfg, tick)
            for name in w.array_names:
                self.assertEqual(getattr(w, name).tobytes(), getattr(expected, name).tobytes(), (tick, name))
            self.assertAlmostEqual(w.costSinks, expected.costSinks, delta=1e-6)

    @unittest.skipUnless(fast._HAVE_NUMBA, 'Numba not installed')
    def test_projection_compiled_and_python_outputs_are_identical(self):
        cfg, w = reset_world({'t2FirmCount': 1, 'distributorCount': 1})
        rng = np.random.default_rng(775)
        for name in ('raw', 'rawBasis', 't1Fin', 't1FinBasis', 't1Price', 't1UnitCost',
                     't1Sold', 't1Revenue', 't1COGS', 't1Cash', 't1Rel'):
            arr = getattr(w, name)
            arr[:] = rng.random(len(arr)) * 1234567
        w.t1Operates[:] = rng.integers(0, 2, len(w.t1Operates))
        made = rng.random(len(w.t1Fin)) * 1234
        expected = project_refineries(w, made, w.t1Controller, cfg['t1License'])
        with patch('economy.server.aggregates._project', _project.py_func):
            actual = project_refineries(w, made, w.t1Controller, cfg['t1License'])
        for a, b in zip(actual, expected):
            if isinstance(a, dict):
                for key in a:
                    np.testing.assert_array_equal(a[key], b[key])
            else:
                np.testing.assert_array_equal(a, b)

    def test_broadcast_encodes_once_and_preserves_wire_text_and_disconnects(self):
        class Socket:
            def __init__(self, fail=False):
                self.fail, self.messages = fail, []
            async def send_text(self, text):
                if self.fail:
                    raise ConnectionError('closed')
                self.messages.append(text)
        async def exercise():
            manager = _ConnectionManager()
            sockets = [Socket(), Socket(), Socket(True)]
            for socket in sockets:
                await manager.connect(socket)
            message = {'type': 'snapshot', 'data': {'label': 'é —', 'price': 1.23}}
            expected = json.dumps(message, separators=(',', ':'), ensure_ascii=False)
            with patch('economy.server.service.json.dumps', wraps=json.dumps) as encode:
                await manager.broadcast(message)
                self.assertEqual(encode.call_count, 1)
            self.assertEqual(sockets[0].messages, [expected])
            self.assertEqual(sockets[1].messages, [expected])
            self.assertNotIn(sockets[2], manager._ws)
        asyncio.run(exercise())

    @unittest.skipUnless(fast._HAVE_NUMBA, 'Numba not installed')
    def test_fused_manufacturing_aggregates_match_independent_numpy_reductions(self):
        cfg, w = reset_world({})
        rng = np.random.default_rng(117)
        for name in ('t2Fin', 't2FinBasis', 't2UnitCost', 't2Price', 't2Raw', 't2RawBasis',
                     't2T1Raw', 't2T1Basis', 't2Cash', 't2Made', 't2Sold', 't2Revenue', 't2COGS', 't2Rel'):
            arr = getattr(w, name)
            arr[:] = rng.random(len(arr)) * 1234567
        w.t2FinBasis[::7] = 0
        capacity = np.array([cfg['t2Capacity'][p['complexity']] for p in M.T2_PRODUCTS])
        expected = _manufacturing_numpy(ManufacturingView(*(getattr(w, k) for k in _T2_FIELDS)),
                                        cfg['t2FirmCount'], w.t2LineCount, capacity)
        actual = project_manufacturing(w, cfg['t2FirmCount'], w.t2LineCount, capacity)
        for a, b in zip(actual, expected):
            self.assertEqual(a.tobytes(), b.tobytes())


if __name__ == '__main__':
    unittest.main()
