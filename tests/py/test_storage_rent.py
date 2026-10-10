"""Per-tick rent, equity exemptions, vectorized allocations and checkpoint compatibility."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from economy.core.config import normalize_config
from economy.core.state import reset_world, add_tier2_line
from economy.core import model as M
from economy.server.aggregates import project_storage_rent
from economy.kernel.tick import settle_storage_rent, storage_rent_equity, tick
from economy.kernel import numba as accelerated
from economy.kernel import tick as reference
from economy.server.persistence import save_checkpoint, load_checkpoint
from economy.server.runtime import KernelRuntime, stats_row

# Keep legacy-rate scenarios explicit; the default-rate test below uses the current rate.
SMALL = {'t2FirmCount': 12, 'distributorCount': 30, 'storageRentPerUnitYear': 20.16}


class StorageRentTests(unittest.TestCase):
    def setUp(self):
        # Runtime construction resets its stats log; isolate every test from live runs.
        self.stats_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.stats_dir.cleanup)
        self.stats_patch = patch('economy.server.runtime._STATS_DIR', Path(self.stats_dir.name))
        self.stats_patch.start()
        self.addCleanup(self.stats_patch.stop)

    def test_per_tick_full_pool_and_t0_exemption(self):
        cfg, w = reset_world({k:v for k,v in SMALL.items() if k != 'storageRentPerUnitYear'})
        w.t1Cash += 1000000
        w.t2Cash[:12] += 1000000
        start0, start1, start2 = w.t0Cash.copy(), w.t1Cash.copy(), w.t2Cash.copy()
        self.assertEqual(settle_storage_rent(w, cfg, 0)['t2RentPayment'], 0)
        for t in range(1, 361):
            result = settle_storage_rent(w, cfg, t)
            self.assertAlmostEqual(result['t2RentExpense'], 56 * 12)
        np.testing.assert_array_equal(w.t0Cash, start0)
        np.testing.assert_allclose(w.t1Cash, start1 - 20160)
        np.testing.assert_allclose(w.t2Cash[:12], start2[:12] - 20160)
        np.testing.assert_array_equal(w.t2Cash[12:], start2[12:])
        self.assertAlmostEqual(w.costSinks, 20160 * 1012, places=6)
        self.assertAlmostEqual(w.t2RentPaid[0], 20160)

    def test_unpaid_rent_is_collected_next_tick(self):
        cfg, w = reset_world(SMALL)
        w.t2EqBook[0] = 2000000
        w.t2Cash[0] = 10
        settle_storage_rent(w, cfg, 1)
        self.assertEqual(w.t2Cash[0], 0)
        self.assertAlmostEqual(w.t2RentArrears[0], 1120-10)
        cfg['storageRentPerUnitYear'] = 0
        w.t2Cash[0] = 2000
        settle_storage_rent(w, cfg, 2)
        self.assertAlmostEqual(w.t2Cash[0], 2010-1120)
        self.assertEqual(w.t2RentArrears[0], 0)
        self.assertAlmostEqual(w.t2RentPaid[0], 1120)

    def test_equity_threshold_inventory_and_existing_debt(self):
        cfg, w = reset_world(SMALL)
        # Put both tiers below, exactly at, and above the $2M boundary.
        for tier in ('t1', 't2'):
            eq = storage_rent_equity(w, cfg, tier)
            getattr(w, tier + 'Cash')[:3] += np.array([1999999., 2000000., 2000001.]) - eq[:3]
        w.t2RentArrears[0] = 100
        settle_storage_rent(w, cfg, 1)
        for tier in ('t1', 't2'):
            np.testing.assert_array_equal(getattr(w, tier + 'RentCharge')[:3], [0,1120,1120])
        self.assertEqual(w.t2RentArrears[0], 100)  # Frozen, not forgiven.
        settle_storage_rent(w, cfg, 2)
        for tier in ('t1', 't2'):
            np.testing.assert_array_equal(getattr(w, tier + 'RentCharge')[:3], [0,0,0])
        # Inventory at cost participates in book equity eligibility.
        w.t2Raw[0] = 2000
        w.t2RawBasis[0] = 1
        settle_storage_rent(w, cfg, 3)
        self.assertEqual(w.t2RentCharge[0],1120)
        self.assertEqual(w.t2RentArrears[0],0)

    def test_vectorized_allocations_match_company_line_reference(self):
        cfg, w = reset_world(SMALL)
        installed = w.t2LineProduct[w.t2FirmLines[0]]
        extra = [p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0] and p['id'] != installed][:2]
        for product in extra:
            add_tier2_line(w, cfg, 0, product, paid=False)
        w.t1Operates[1] = 1  # One refinery now serves two products.
        rng = np.random.default_rng(822)
        w.t1RentCharge[:] = rng.choice([0., 1120.], M.N1)
        w.t2RentCharge[:12] = rng.choice([0., 1120.], 12)
        w.t2RentCharge[0] = 1120
        actual = project_storage_rent(w, cfg)
        expected = {k: np.zeros_like(v) for k,v in actual.items()}
        for firm in range(M.N1):
            charge = w.t1RentCharge[firm]
            expected['cohorts1'][firm // 100] += charge
            products = np.flatnonzero(w.t1Operates.reshape(M.N1, M.NP)[firm])
            for product in products:
                expected['complexity'][M.PRODUCTS[product]['complexity']] += charge / len(products)
        for firm in range(12):
            charge = w.t2RentCharge[firm]
            expected['cohorts2'][w.t2Sector[firm]] += charge
            lines = np.flatnonzero(w.t2LineFirm[:int(w.t2LineCount)] == firm)
            for line in lines:
                product = M.T2_PRODUCTS[w.t2LineProduct[line]]
                portion = charge / len(lines)
                expected['products'][product['id']] += portion
                expected['industries'][M.T2_SECTORS.index(product['sector'])] += portion
                expected['complexity'][product['complexity']] += portion
        for key in expected:
            np.testing.assert_allclose(actual[key], expected[key], rtol=1e-14, atol=1e-9)
        self.assertAlmostEqual(actual['products'].sum(), w.t2RentCharge[:12].sum())

    def test_equity_projections_include_debt(self):
        rt = KernelRuntime(SMALL)
        before = rt.publish()
        rt.world.t1RentArrears[0] = 4321
        rt.world.t2RentArrears[0] = 1234
        after = rt.publish()
        self.assertAlmostEqual(before['tiers']['t1']['equity'] - after['tiers']['t1']['equity'], 4321)
        self.assertAlmostEqual(before['tiers']['t2']['equity'] - after['tiers']['t2']['equity'], 1234)
        self.assertAlmostEqual(before['cohorts'][0]['equity'] - after['cohorts'][0]['equity'], 4321)
        self.assertAlmostEqual(before['tier2Cohorts'][0]['equity'] - after['tier2Cohorts'][0]['equity'], 1234)
        detail = rt._company_detail('T1', 0)
        self.assertEqual(detail['equity'], after['companies'][0]['equity'])
        detail2 = rt._tier2_company(0, False)
        self.assertEqual(detail2['equity'], rt._tier2_sort_values(np.array([0]), 'equity')[0])
        self.assertEqual(detail2['storageRentArrears'], 1234)
        self.assertAlmostEqual(stats_row(rt.world, rt.cfg, 0, 0)['t2Equity'], after['tiers']['t2']['equity'])

    def test_checkpoint_preserves_debt_and_legacy_load_disables_new_rent(self):
        cfg, w = reset_world(SMALL)
        w.t1RentArrears[0] = 17
        w.t2RentPaid[0] = 35
        with tempfile.TemporaryDirectory() as d:
            p = str(Path(d) / 'rent')
            save_checkpoint(p, cfg, 360, w)
            cfg2, t, w2, _ = load_checkpoint(p)
            self.assertEqual(cfg2['storageRentPerUnitYear'], 20.16)
            self.assertEqual(t, 360)
            self.assertEqual(w2.t1RentArrears[0], 17)
            self.assertEqual(w2.t2RentPaid[0], 35)
            meta = json.loads(Path(p + '.json').read_text())
            meta['version'] = 2
            del meta['cfg']['storageRentPerUnitYear']
            Path(p + '.json').write_text(json.dumps(meta))
            np.savez(p + '.npz', **{k: getattr(w, k) for k in w.array_names if 'Rent' not in k})
            cfg3, _, w3, _ = load_checkpoint(p)
            self.assertEqual(cfg3['storageRentPerUnitYear'], 0)
            self.assertEqual(w3.t1RentArrears.sum() + w3.t2RentPaid.sum(), 0)

    def test_year_end_tick_cash_conservation_in_both_engines(self):
        for fast in (False, True):
            if fast and not accelerated._HAVE_NUMBA:
                continue
            cfg, w = reset_world(SMALL)
            def cash():
                return w.t0Cash.sum() + w.t1Cash.sum() + w.t2Cash[:12].sum()
            w.t1Cash += 1000000
            w.t2Cash[:12] += 1000000
            before = cash()
            with patch.object(accelerated, '_HAVE_NUMBA', fast):
                state = tick(w, cfg, 360)
            self.assertAlmostEqual(cash() - before, state['distributorPayments'] - state['costSinks'] - state['equipmentSinks'], delta=1e-5)
            self.assertAlmostEqual(state['t2RentExpense'], 1120 * 12)
            self.assertTrue((w.t2Cash >= 0).all())

    def test_normalization_and_zero_rate(self):
        self.assertEqual(normalize_config({'storageRentPerUnitYear': -5})['storageRentPerUnitYear'], 0)
        self.assertEqual(normalize_config({'storageRentPerUnitYear': float('nan')})['storageRentPerUnitYear'], 1.008)
        cfg, w = reset_world(dict(SMALL, storageRentPerUnitYear=0))
        before = w.t1Cash.copy()
        settle_storage_rent(w, cfg, 360)
        np.testing.assert_array_equal(before, w.t1Cash)
        self.assertEqual(w.costSinks, 0)

    def test_net_margin_rent_projection_exemption_and_multiline(self):
        cfg, w = reset_world(SMALL)
        for tier in ('t1', 't2'):
            np.testing.assert_array_equal(reference.production_line_rent(w, cfg, tier), 0)
            eq = storage_rent_equity(w, cfg, tier)
            getattr(w, tier + 'Cash')[:3] += np.array([1999999., 2000000., 2000001.]) - eq[:3]
        w.t1Operates[1] = 1
        w.t1Cash[0] += 1  # Exactly eligible, two lines.
        w.t1RentCharge[1] = 9999  # Forecast must not use stale recorded expense.
        np.testing.assert_array_equal(reference.production_line_rent(w, cfg, 't1')[:3], [560,1120,1120])
        np.testing.assert_array_equal(reference.production_line_rent(w, cfg, 't2')[:3], [0,1120,1120])
        installed = w.t2LineProduct[w.t2FirmLines[1 * M.T2_MAX_PRODUCTS_PER_FIRM]]
        extra = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[1] and p['id'] != installed)
        add_tier2_line(w, cfg, 1, extra, paid=False)
        self.assertEqual(reference.production_line_rent(w, cfg, 't2')[1], 560)
        cfg['storageRentPerUnitYear'] = 0
        np.testing.assert_array_equal(reference.production_line_rent(w, cfg, 't2'), 0)

    def test_refinery_restocking_ignores_margin_in_both_engines(self):
        # $2 price and $1.50 marginal cost: 25% gross margin. A $900
        # line expense on 2,000 planned units leaves 2.5% net margin.
        for fast in (False, True):
            if fast and not accelerated._HAVE_NUMBA:
                continue
            for eligible, bill, expected in [(True,900,1000), (True,1120,0), (False,1120,2000), (True,0,2000)]:
                cfg, w = reset_world(dict(SMALL, storageRentPerUnitYear=bill * 360 / 20000))
                w.t0Price[:] = 1.25
                w.t0Inv[:] = 0  # Observe plans without actual purchasing.
                w.t1Price[:] = 2
                if eligible:
                    w.t1Cash[0] += 1000000
                cash = w.t1Cash[0]
                if fast:
                    accelerated.plan_and_buy_inputs(w, cfg, 1)
                else:
                    reference.plan_and_buy_inputs(w, cfg, M.PRODUCTS, reference.T0P, 1)
                self.assertEqual(w.t1InputNeed[:M.NE].sum(), 9500, (fast, eligible, bill))
                self.assertEqual(w.t1PurchaseReq[:M.NE].sum(), 9000)
                self.assertEqual(w.t1Cash[0], cash)  # Forecast posts no charge.

    def test_net_margin_throttles_manufacturer_in_both_engines(self):
        for fast in (False, True):
            if fast and not accelerated._HAVE_NUMBA:
                continue
            for eligible in (False, True):
                cfg, w = reset_world(SMALL)
                w.t1Fin[:] = 10000.0 * w.t1Operates
                w.t1FinBasis[:] = 1.5
                w.t1Price[:] = 1.5
                w.t2Price[:int(w.t2LineCount)] = 10
                if eligible:
                    w.t2Cash[:12] += 1000000
                if fast:
                    accelerated.operate_tier2(w, cfg, 1)
                else:
                    reference.operate_tier2(w, cfg, M.PRODUCTS, reference.T0P, M.T2_PRODUCTS, 1)
                if eligible:
                    self.assertEqual(w.t2Made.sum(), 0)
                else:
                    self.assertGreater(w.t2Made.sum(), 0)

    def test_stocked_inputs_cannot_bypass_production_rent_gate(self):
        for fast in (False, True):
            if fast and not accelerated._HAVE_NUMBA:
                continue
            for eligible in (False, True):
                cfg, w = reset_world(dict(SMALL, storageRentPerUnitYear=1.008))
                # Reproduce a refinery replacing eight daily sales from existing raw stock.
                firm = 906
                product = M.PRODUCTS[9]
                index = firm * M.NP + 9
                w.t1Fin[index] = reference.tier1_stock_target(w, cfg, product, index) - 8
                w.t1Price[index] = 7.88
                for e in product['inputs']:
                    ri = firm * M.NE + M.ELEMENTS.index(e)
                    w.raw[ri] = 648
                    w.rawBasis[ri] = 2.54
                if eligible:
                    w.t1Cash[firm] += 1000000
                before = w.t1Fin[index]
                if fast:
                    accelerated.operate_tier1(w, cfg)
                else:
                    reference.operate_tier1(w, cfg, M.PRODUCTS)
                self.assertEqual(w.t1Fin[index] - before, 0 if eligible else 8)
                # Manufacturers also have sufficient existing inputs and no stocked suppliers.
                cfg, w = reset_world(SMALL)  # Legacy high rent makes the loss unambiguous.
                w.t1Fin[:] = 0
                w.t2Raw[:] = 100
                w.t2RawBasis[:] = 1.5
                w.t2T1Raw[:] = 100
                w.t2T1Basis[:] = 1.5
                w.t2Price[:int(w.t2LineCount)] = 10
                if eligible:
                    w.t2Cash[:12] += 1000000
                if fast:
                    accelerated.operate_tier2(w, cfg, 1)
                else:
                    reference.operate_tier2(w, cfg, M.PRODUCTS, reference.T0P, M.T2_PRODUCTS, 1)
                self.assertEqual(w.t2Bought.sum(), 0)
                self.assertEqual(w.t2Made.sum() == 0, eligible)

    def test_production_ramp_rechecks_fixed_cost_after_rounding(self):
        for fn in ([M.production_batches, accelerated._production_batches]
                   if accelerated._HAVE_NUMBA else [M.production_batches]):
            # 2.5% net margin becomes a half-volume plan that still covers its bill.
            self.assertEqual(fn(100, 1, .97, 1, .5, .05), 50)
            # The same initial margin with a larger fixed bill loses money after halving.
            self.assertEqual(fn(100, 1, .5, 1, 47.5, .05), 0)
            self.assertEqual(fn(8, 1, 2.79, 7.88, 56, .05), 0)
            self.assertEqual(fn(8, 1, 2.79, 7.88, 0, .05), 8)

    @unittest.skipUnless(accelerated._HAVE_NUMBA, 'Numba unavailable')
    def test_net_margin_all_complexities_match_engines(self):
        worlds = []
        for _ in range(2):
            cfg, w = reset_world(dict(SMALL, t2FirmCount=200, distributorCount=400,
                                      storageRentPerUnitYear=.072))  # $4/firm/tick.
            for i, p in enumerate(M.T2_PRODUCTS):
                w.t2LineProduct[i] = i
                w.t2Sector[i] = p['sectorIndex']
                w.t2UnitCost[i] = M.unit_cost(p['complexity'], cfg)
                w.t2Price[i] = round(w.t2UnitCost[i] * 1.25, 2)
            w.t1Cash[::2] += 1000000
            w.t2Cash[:200:2] += 1000000
            extra = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0] and p['complexity'] == 4)
            add_tier2_line(w, cfg, 0, extra)
            w.t1Operates[1] = 1
            worlds.append(w)
        for t in range(1, 9):
            with patch.object(accelerated, '_HAVE_NUMBA', False):
                a = tick(worlds[0], cfg, t)
            with patch.object(accelerated, '_HAVE_NUMBA', True):
                b = tick(worlds[1], cfg, t)
            for name in worlds[0].array_names:
                np.testing.assert_array_equal(getattr(worlds[0], name), getattr(worlds[1], name), err_msg=f'{t}: {name}')
            for key in a:
                self.assertAlmostEqual(a[key], b[key], delta=1e-6, msg=key)


if __name__ == '__main__':
    unittest.main()
