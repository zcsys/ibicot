"""Regression checks for the repository-wide economy review."""
import asyncio
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from economy.core import model as M
from economy.core.config import normalize_config
from economy.core.state import reset_world, T0P, add_tier2_line, tier1_goods_space, tier2_occupied_space
from economy.core.trading import select_offer, affordable_order
from economy.kernel import tick as reference
from economy.kernel import numba as accelerated
from economy.server import service
from economy.server.persistence import save_checkpoint, load_checkpoint
from economy.server.runtime import KernelRuntime, stats_row

SMALL = {'t2FirmCount': 12, 'distributorCount': 30}


class _FakeWS:
    def __init__(self):
        self.sent = []

    async def send_json(self, message):
        self.sent.append(message)


class ReviewFixes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_runtime = service._runtime
        self.addCleanup(setattr, service, '_runtime', self.old_runtime)

    def runtime(self):
        rt = KernelRuntime(SMALL)
        rt.statsPath = Path(self.tmp.name) / 'stats.jsonl'
        return rt

    def test_zero_refinery_quote_stays_positive_in_both_engines(self):
        for fast in (False, True):
            with self.subTest(fast=fast), patch.object(accelerated, '_HAVE_NUMBA', fast):
                rt = self.runtime()
                rt.player('T1', 0, 'W', 0, True, 'PLAYER')
                rt.step()
                self.assertEqual(rt.tick, 1)
                self.assertEqual(rt.world.t1Price[0], .01)
                self.assertTrue(np.isfinite(rt.world.t2Cash).all())
                self.assertTrue((rt.world.t2Cash >= 0).all())

    def test_fixed_loyalty_cost_and_cash_cap_in_both_engines(self):
        stock = np.array([100., 100.])
        prices = np.array([2., 1.8])
        reliability = np.array([.5, .5])
        offers = np.array([1, 0], dtype=np.int64)
        for choose, settle in ((select_offer, affordable_order),
                               (accelerated._select_offer_nb, accelerated._affordable_order_nb)):
            self.assertEqual(choose(offers, stock, prices, 0, reliability, 1, 1.5, .605, 1), 0)
            self.assertEqual(choose(offers, stock, prices, 0, reliability, 20, 1.5, .605, 1), 1)
            # A large proposed order becomes a one-unit fill when cash is scarce.
            seller, funded, bought, charge = settle(1, 0, 20, 3.2, stock, prices, reliability, 1.5, .605, 1)
            self.assertEqual((seller, bought, charge), (0, 1, 0))
            empty_incumbent = np.array([0., 100.])
            self.assertEqual(choose(offers, empty_incumbent, prices, 0, reliability, 1, 1.5, 100, 1), 1)
            self.assertEqual(settle(1, 0, 1, 100., empty_incumbent, prices, reliability, 1.5, 100, 1)[3], 0)

    def test_raw_orders_use_the_adaptive_fixed_charge(self):
        for fast in (False, True):
            cfg, w = reset_world(SMALL)
            w.t1Operates.fill(0)
            w.t1Operates[0] = 1
            w.t1Price[0] = 10
            w.t0Inv.fill(0)
            w.t0Inv[[0, 4]] = 10000
            w.t0Price[[0, 4]] = [2., 1.8]
            w.preferredWholesale[0] = 0
            w.lm1 = 500  # $750 charge exceeds $400 savings on the 2,000-unit order.
            if fast:
                accelerated.plan_and_buy_inputs(w, cfg, 1)
            else:
                reference.plan_and_buy_inputs(w, cfg, M.PRODUCTS, T0P, 1)
            self.assertEqual(w.preferredWholesale[0], 0)
            self.assertEqual(w.t0Sold[0], 2000)
            self.assertEqual(w.loyaltyPenalties[0], 0)

    def test_manufacturer_orders_compare_settlement_cost(self):
        for fast in (False, True):
            cfg, w = reset_world(dict(SMALL, t2FirmCount=1, t2Capacity={3: 3, 4: 20, 5: 10}))
            w.t1Fin[w.t1Operates != 0] = 100
            w.t1Price[[0, 10]] = [2., 1.8]
            w.t2Preferred[0] = 0
            w.t2Price[0] = 10
            if fast:
                accelerated.operate_tier2(w, cfg, 1)
            else:
                reference.operate_tier2(w, cfg, M.PRODUCTS, T0P, M.T2_PRODUCTS, 1)
            self.assertEqual(w.t2Preferred[0], 0)
            self.assertEqual(w.t1Sold[0], 1)
            self.assertEqual(w.loyaltyPenalties[1], 0)

    def test_distributor_ranking_uses_adaptive_charge_and_stockout_waiver(self):
        for fast in (False, True):
            for incumbent_stock, expected in ((100, 0), (0, 1)):
                cfg, w = reset_world(dict(SMALL, t2FirmCount=2, distributorCount=1,
                                          distributorActivation=1, distributorSearchOffers=20))
                w.distributorProduct[0] = M.NP
                w.distributorPreferredSupplier[0] = 0
                w.t2Price[:2] = [3., 2.]
                w.t2Fin[:2] = [incumbent_stock, 100]
                w.lm3 = 100
                if fast:
                    accelerated.clear_distributors(w, cfg, 1)
                else:
                    reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
                self.assertEqual(w.distributorLastSupplier[0], expected)
                self.assertEqual(w.loyaltyPenalties[2], 0)

    def test_attach_preserves_running_world_configuration_and_log(self):
        rt = self.runtime()
        rt.step()
        rt.statsPath.write_text('existing run\n')
        rt.running = True
        world = rt.world
        cash = world.t2Cash.copy()
        for _ in range(2):
            response = service._dispatch(rt, {'type': 'init', 'cfg': {'seed': 999}})
            self.assertEqual(response[0]['data']['tick'], 1)
        self.assertIs(rt.world, world)
        self.assertEqual(rt.cfg['seed'], 137)
        self.assertTrue(rt.running)
        np.testing.assert_array_equal(world.t2Cash, cash)
        self.assertEqual(rt.statsPath.read_text(), 'existing run\n')

    def test_load_updates_the_runtime_held_by_connected_clients(self):
        rt = self.runtime()
        rt.tick = 7
        stem = str(Path(self.tmp.name) / 'checkpoint')
        save_checkpoint(stem, rt.cfg, rt.tick, rt.world, rt.state)
        rt.tick = 99
        rt.running = True
        service._runtime = rt
        result = asyncio.run(service.checkpoint_load(service.CheckpointRequest(path=stem)))
        self.assertEqual(result['tick'], 7)
        self.assertIs(service.runtime(), rt)
        self.assertFalse(rt.running)
        self.assertEqual(rt.tick, 7)
        rt.statsPath = Path(self.tmp.name) / 'restored.jsonl'
        service._dispatch(rt, {'type': 'step'})
        self.assertEqual(service.runtime().tick, 8)

    def test_checkpoint_restores_controls_equipment_and_ownership(self):
        rt = self.runtime()
        rt.player('T1', 0, 'W', .02, True, 'PLAYER')
        rt.buy_equipment('T1', 0, 'W+E')
        rt.player('T0', 0, 'Water', .03, True, 'PLAYER')
        rt.player('T2', 0, M.T2_PRODUCTS[0]['code'], .04, True, 'PLAYER')
        rt.playerLicenses = {'T0', 'T1', 'T2'}
        rt.playerHouse = {'name': 'Checkpoint test'}
        rt.ownershipAccounting = {'licensesSpent': 123, 'houseSpent': 456}
        rt.world.lm1 = 321
        rt.world.loyaltyPenalties[:] = [1, 2, 3]
        before = rt.checkpoint_metadata()
        arrays = {n: getattr(rt.world, n).copy() for n in rt.world.array_names}
        service._runtime = rt
        req = service.CheckpointRequest(path=str(Path(self.tmp.name) / 'controls'))
        asyncio.run(service.checkpoint_save(req))
        asyncio.run(service.checkpoint_load(req))
        self.assertEqual(rt.checkpoint_metadata(), before)
        self.assertIn('W+E', rt.equipment[0])
        self.assertEqual(rt.controller[0], 1)
        self.assertEqual(rt.playerPrices[0]['W'], .02)
        for name, saved in arrays.items():
            np.testing.assert_array_equal(getattr(rt.world, name), saved, err_msg=name)
        with self.assertRaisesRegex(ValueError, 'new equipment'):
            rt.buy_equipment('T1', 0, 'W+E')
        # Re-saving after a resumed run must not overwrite new adaptive scalars.
        rt.world.lm1 = 654
        asyncio.run(service.checkpoint_save(req))
        _, _, w, _ = load_checkpoint(req.path)
        self.assertEqual(w.lm1, 654)
        np.testing.assert_array_equal(w.loyaltyPenalties, [1, 2, 3])

    def test_legacy_checkpoint_expands_line_capacity(self):
        rt = self.runtime()
        rt.player('T1', 0, 'W', .5, True, 'PLAYER')
        rt.buy_equipment('T1', 0, 'W+E')
        stem = str(Path(self.tmp.name) / 'legacy')
        save_checkpoint(stem, rt.cfg, 0, rt.world)
        meta = json.loads(Path(stem + '.json').read_text())
        meta['version'] = 1
        meta.pop('runtime')
        meta.pop('extras')
        Path(stem + '.json').write_text(json.dumps(meta))
        arrays = {}
        for name in rt.world.array_names:
            a = getattr(rt.world, name).copy()
            if name.startswith('t2') and len(a) == SMALL['t2FirmCount'] * M.T2_MAX_PRODUCTS_PER_FIRM:
                if name.startswith('t2Learn') or name in ('t2Demand', 't2DemandEMA'):
                    a = np.pad(a, (0, M.N2_FIRMS - len(a)))
                else:
                    a = a[:SMALL['t2FirmCount']]
            arrays[name] = a
        np.savez(stem + '.npz', **arrays)
        service._runtime = rt
        asyncio.run(service.checkpoint_load(service.CheckpointRequest(path=stem)))
        self.assertEqual(len(rt.world.t2Fin), SMALL['t2FirmCount'] * M.T2_MAX_PRODUCTS_PER_FIRM)
        self.assertEqual(rt.world.t2LineCount, SMALL['t2FirmCount'])
        self.assertIn('W+E', rt.equipment[0])
        self.assertEqual(rt.controller[0], 1)
        rt.statsPath = Path(self.tmp.name) / 'legacy-resumed.jsonl'
        rt.step()
        self.assertEqual(rt.tick, 1)

    def test_storage_config_changes_are_atomic(self):
        rt = self.runtime()
        rt.world.raw[0] = 18000
        original = dict(rt.cfg)
        with self.assertRaisesRegex(ValueError, 'Storage'):
            rt.apply_config({'storage': 5000})
        self.assertEqual(rt.cfg, original)
        with self.assertRaisesRegex(ValueError, 'Storage'):
            reset_world(dict(SMALL, storage=100))

    def test_retail_partial_challenger_must_cover_actual_switch_fee(self):
        for fast in (False, True):
            cfg, w = reset_world(dict(SMALL, t2FirmCount=2, distributorCount=1,
                                      distributorActivation=1, distributorSearchOffers=20))
            w.distributorProduct[0] = M.NP
            w.distributorPreferredSupplier[0] = 0
            w.distributorChoke[0] = 100
            w.t2Price[:2] = [3, 2]
            w.t2Fin[:2] = [100, 1]
            w.lm3 = 1  # Fee > $1 single-unit saving, even though a full order could justify it.
            if fast:
                accelerated.clear_distributors(w, cfg, 1)
            else:
                reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
            self.assertEqual(w.distributorLastSupplier[0], 0)
            self.assertEqual(w.loyaltyPenalties[2], 0)
            self.assertEqual(w.t2Sold[1], 0)
            self.assertEqual(w.t2RelAttempts[1], 0)

    def test_logged_equity_includes_all_inventory_at_book_cost(self):
        rt = self.runtime()
        w = rt.world
        before = stats_row(w, rt.cfg, 0, 0)['t2Equity']
        w.t2Raw[0], w.t2RawBasis[0] = 7, 2
        w.t2T1Raw[4], w.t2T1Basis[4] = 3, 4
        w.t2Fin[0], w.t2FinBasis[0] = 5, 6
        self.assertEqual(stats_row(w, rt.cfg, 0, 0)['t2Equity'] - before, 56)
        snapshot = rt.publish()
        self.assertEqual(snapshot['tiers']['t2']['equity'], before + 56)

    def test_json_loyalty_mappings_and_ui_anchor(self):
        from economy.core.config import normalize_config
        patch_cfg = {'loyaltyMultiple': {'1': 0, '2': {'3': 2, '4': 3, '5': 4}, '3': 5}}
        cfg = normalize_config(patch_cfg)
        self.assertEqual(cfg['loyaltyMultiple'], {1: 0, 2: {3: 2., 4: 3., 5: 4.}, 3: 5.})
        self.assertEqual(normalize_config(json.loads(json.dumps(cfg))), cfg)
        self.assertEqual(patch_cfg['loyaltyMultiple']['1'], 0)
        # Exercise the dashboard's actual readCfg function with its DOM controls.
        script = r"""
const fs = require('fs'), vm = require('vm');
const source = fs.readFileSync('web/app.js','utf8');
const params = source.match(/const PARAMS = (\[[\s\S]*?\]);/)[0];
const read = source.match(/function readCfg\(\) \{[\s\S]*?\n  \}/)[0];
const nodes = new Proxy({}, {get: (_, id) => ({value: id === 'marketAnchorBand' ? '0.123' : '1'})});
const ctx = {M: {ECONOMY_DEFAULTS: {footprint: {1:1000}}}, $: id=>nodes[id], serverCfg: null};
vm.createContext(ctx);
vm.runInContext(params + read + ';result=readCfg()', ctx);
if (ctx.result.marketAnchorBand !== .123) throw Error('anchor omitted');
"""
        subprocess.run(['node', '-e', script], check=True)

    def test_expansion_storage_and_money_accounting(self):
        rt = self.runtime()
        w = rt.world
        rt.player('T2', 0, M.T2_PRODUCTS[0]['code'], 3, True, 'PLAYER')
        product = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0]
                       and p['id'] != w.t2LineProduct[0] and p['complexity'] == 3)
        cash, book = w.t2Cash[0], w.t2EqBook[0]
        rt.buy_equipment('T2', 0, product['code'])
        self.assertEqual(w.t2FirmLineCount[0], 2)
        self.assertEqual(w.t2LineCount, SMALL['t2FirmCount'] + 1)
        self.assertEqual(w.t2Cash[0] + w.t2EqBook[0], cash + book)
        self.assertEqual(w.equipmentSinks, rt.cfg['t2Machinery'][3])
        other = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0]
                     and p['complexity'] == 4)
        w.t2Raw[0] = rt.cfg['storage'] - tier2_occupied_space(w, rt.cfg, 0)
        cash, count = w.t2Cash[0], w.t2LineCount
        # Give enough cash to isolate the space check.
        w.t2Cash[0] = 1000000
        with self.assertRaisesRegex(ValueError, 'storage'):
            rt.buy_equipment('T2', 0, other['code'])
        self.assertEqual(w.t2Cash[0], 1000000)
        self.assertEqual(w.t2LineCount, count)
        rt.player('T1', 0, 'W', 3, True, 'PLAYER')
        w.raw[0] = tier1_goods_space(w, rt.cfg, 0)
        cash = w.t1Cash[0]
        with self.assertRaisesRegex(ValueError, 'storage'):
            rt.buy_equipment('T1', 0, 'W+E')
        self.assertEqual(w.t1Cash[0], cash)

    def test_procurement_reserves_machine_footprints(self):
        for fast in (False, True):
            cfg, w = reset_world(SMALL)
            # Existing stock leaves less than one wholesale lot of goods room.
            w.raw[0] = 18500
            w.t1Price[0] = 100
            w.t0Inv.fill(100000)
            if fast:
                accelerated.plan_and_buy_inputs(w, cfg, 1)
            else:
                reference.plan_and_buy_inputs(w, cfg, M.PRODUCTS, T0P, 1)
            self.assertLessEqual(w.raw[:M.NE].sum() + w.t1Fin[:M.NP].sum(), 19000)
            w.t1Fin[w.t1Operates != 0] = 100000
            w.t2Raw[0] = 16999
            w.t2Price[0] = 100
            if fast:
                accelerated.operate_tier2(w, cfg, 1)
            else:
                reference.operate_tier2(w, cfg, M.PRODUCTS, T0P, M.T2_PRODUCTS, 1)
            self.assertLessEqual(tier2_occupied_space(w, cfg, 0), cfg['storage'])

    def test_retail_full_partial_and_split_orders(self):
        for fast in (False, True):
            for stocks, new_preferred, complete in (([0, 100, 0], 1, 1), ([1, 0, 0], 0, 0), ([1, 100, 0], 0, 1)):
                cfg, w = reset_world(dict(SMALL, t2FirmCount=3, distributorCount=1,
                                          distributorActivation=1, distributorSearchOffers=20))
                w.distributorProduct[0] = M.NP
                w.distributorPreferredSupplier[0] = 0
                w.distributorChoke[0] = 100
                w.t2Price[:3] = [1., 1.1, 1.2]
                w.t2Fin[:3] = stocks
                if fast:
                    _, filled, _, _, purchases = accelerated.clear_distributors(w, cfg, 1)
                else:
                    result = reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
                    filled, purchases = result['filledOrders'], result['purchaseOrders']
                self.assertEqual(w.distributorPreferredSupplier[0], new_preferred)
                self.assertEqual(filled, complete)
                self.assertEqual(purchases, 1)
                self.assertEqual(w.t2RelAvailable[0], 0)
                self.assertEqual(w.marketActive.sum(), w.marketFulfilled.sum() + w.marketStockUnmet.sum())

    def test_player_manufacturer_can_quote_below_cost(self):
        rt = self.runtime()
        code = M.T2_PRODUCTS[int(rt.world.t2LineProduct[0])]['code']
        rt.player('T2', 0, code, .01, True, 'PLAYER')
        rt.step()
        self.assertEqual(rt.world.t2Price[0], .01)
        self.assertEqual(rt.world.t2Made[0], 0)

    def test_all_complexities_multiline_and_live_config_match_engines(self):
        # Explicitly cover every product: ordinary small worlds use a product prefix.
        a = KernelRuntime(dict(SMALL, t2FirmCount=200, distributorCount=400))
        b = KernelRuntime(dict(SMALL, t2FirmCount=200, distributorCount=400))
        for rt in (a, b):
            w = rt.world
            for i, p in enumerate(M.T2_PRODUCTS):
                w.t2LineProduct[i] = i
                w.t2Sector[i] = p['sectorIndex']
                w.t2UnitCost[i] = M.unit_cost(p['complexity'], rt.cfg)
                w.t2Price[i] = round(w.t2UnitCost[i] * 1.25, 2)
            other = next(p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0] and p['complexity'] == 4)
            add_tier2_line(w, rt.cfg, 0, other)
            with patch.object(rt, 'publish'):
                rt.apply_config({'t2MaterialCost': 3.5, 'conversionFactor': .4})
            w.distributorPreferredSupplier[:200] = np.arange(200)
            w.distributorProduct[:200] = np.arange(200) + M.NP
        for t in range(1, 33):
            with patch.object(accelerated, '_HAVE_NUMBA', True):
                sa = reference.tick(a.world, a.cfg, t)
            with patch.object(accelerated, '_HAVE_NUMBA', False):
                sb = reference.tick(b.world, b.cfg, t)
            for key in sa:
                self.assertAlmostEqual(sa[key], sb[key], delta=1e-6, msg=key)
            for name in a.world.array_names:
                np.testing.assert_array_equal(getattr(a.world, name), getattr(b.world, name), err_msg=f'{t}: {name}')
            self.assertAlmostEqual(a.world.costSinks, b.world.costSinks, delta=1e-6)

    def test_partial_nested_config_is_total_and_atomic(self):
        cfg = normalize_config({'t2Capacity': {'3': 30}})
        self.assertEqual(sorted(cfg['t2Capacity']), [3, 4, 5])
        self.assertEqual(cfg['t2Capacity'][4], 20)
        rt = self.runtime()
        rt.apply_config({'t2Capacity': {'3': 30}})
        self.assertEqual(sorted(rt.cfg['t2Capacity']), [3, 4, 5])
        self.assertEqual(rt.cfg['t2Capacity'][3], 30)
        self.assertEqual(rt.cfg['t2Capacity'][4], 20)

    def test_loyalty_aov_bootstrap_is_five_percent(self):
        cfg, w = reset_world(SMALL)
        self.assertAlmostEqual(w.aov1, w.lm1 * w.lmUnitCost1 * 1.5 / 0.05)
        self.assertAlmostEqual(w.aov3, w.lm3 * w.lmUnitCost3 * 1.5 / 0.05)
        # Bootstrap and annual re-derivation agree: 5 % everywhere.
        self.assertAlmostEqual(0.05 * w.aov1 / (w.lmUnitCost1 * 1.5), w.lm1)
        self.assertAlmostEqual(0.05 * w.aov3 / (w.lmUnitCost3 * 1.5), w.lm3)

    def test_server_scheduler_is_singleton(self):
        service._runtime = self.runtime()
        service._scheduler_task = None

        async def exercise():
            service._ensure_scheduler()
            first = service._scheduler_task
            service._ensure_scheduler()
            self.assertIs(service._scheduler_task, first)
            first.cancel()
            try:
                await first
            except asyncio.CancelledError:
                pass
            service._scheduler_task = None

        asyncio.run(exercise())
        self.assertIsNone(service._scheduler_task)

    def test_connection_manager_broadcast(self):
        mgr = service._ConnectionManager()
        a, b = _FakeWS(), _FakeWS()

        async def exercise():
            await mgr.connect(a)
            await mgr.connect(b)
            await mgr.broadcast({'type': 'x'})
            mgr.disconnect(a)
            await mgr.broadcast({'type': 'y'})
            return a, b

        a, b = asyncio.run(exercise())
        self.assertEqual([m['type'] for m in a.sent], ['x'])
        self.assertEqual([m['type'] for m in b.sent], ['x', 'y'])


if __name__ == '__main__':
    unittest.main()
