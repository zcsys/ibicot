"""Player money, isolation, persistence and acquisition integration checks."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from economy.core import model as M
from economy.server.runtime import KernelRuntime
from economy.server.onboarding import create_router, new_profile, work, bonus
from economy.server import players


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'ECONOMY_PLAYERS_DB': str(Path(self.temp.name) / 'players.sqlite3')})
        self.env.start()
        with patch('economy.server.runtime._STATS_DIR', Path(self.temp.name)):
            self.rt = KernelRuntime({'t2FirmCount': 2, 'distributorCount': 3})
        app = FastAPI()
        app.include_router(create_router(lambda: self.rt))
        self.app = app
        self.client = TestClient(app)
        self.state = self.client.get('/play-api/state').json()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def action(self, kind, amount=0, **kwargs):
        response = self.client.post('/play-api/action', json={'kind': kind, 'amount': amount, 'revision': self.state['revision'], **kwargs})
        if response.status_code == 200:
            self.state = response.json()
        return response

    def test_progression_wallet_and_isolation(self):
        cash = self.rt.world.t1Cash.copy()
        quotes = self.rt.world.t1Price.copy()
        controls = self.rt.world.t1Controller.copy()
        self.assertEqual(self.action('bonus', 10).status_code, 400)
        self.action('name', name='Ada')
        for _ in range(4):
            self.assertEqual(self.action('work', self.state['price']).status_code, 200)
        cash_before = self.state['cash']
        wallet_before = self.state['wallet']
        self.assertEqual(self.action('bonus', 1234.56).status_code, 200)
        self.assertAlmostEqual(cash_before - self.state['cash'], 1234.56)
        self.assertAlmostEqual(self.state['wallet'] - wallet_before, 1234.56)
        self.assertEqual(self.action('bonus', self.state['cash'] + 1).status_code, 400)
        np.testing.assert_array_equal(self.rt.world.t1Cash, cash)
        np.testing.assert_array_equal(self.rt.world.t1Price, quotes)
        np.testing.assert_array_equal(self.rt.world.t1Controller, controls)
        self.assertEqual(self.rt.tick, 0)
        refreshed = self.client.get('/play-api/state').json()
        self.assertEqual(refreshed['person']['name'], 'Ada')
        self.assertEqual(refreshed['wallet'], self.state['wallet'])
        with players.transaction() as db:
            total = db.execute('SELECT SUM(amount_cents) FROM ledger').fetchone()[0]
            self.assertEqual(total, round(self.state['wallet'] * 100))

    def test_stale_retries_and_separate_people(self):
        revision = self.state['revision']
        self.action('work', self.state['price'])
        duplicate = self.client.post('/play-api/action', json={'kind':'work','amount':10,'revision':revision})
        self.assertEqual(duplicate.status_code, 409)
        other = TestClient(self.app).get('/play-api/state').json()
        self.assertNotEqual(other['person']['id'], self.state['person']['id'])
        self.assertEqual(other['wallet'], 0)

    def test_acquisition_and_restart(self):
        self.assertEqual(self.action('buy').status_code, 400)
        for _ in range(4):
            self.action('work', self.state['price'])
        # Real progression earns purchase funds, no wallet injection.
        for _ in range(200):
            if self.state['cash'] > 0:
                self.action('bonus', self.state['cash'])
            if self.state['wallet'] >= self.state['offer']['price']:
                break
            self.action('work', self.state['price'])
        self.assertGreaterEqual(self.state['wallet'], self.state['offer']['price'])
        cid = self.state['offer']['id']
        treasury = float(self.rt.world.t1Cash[cid])
        wallet = self.state['wallet']
        self.assertEqual(self.action('buy').status_code, 200)
        self.assertEqual(self.state['wallet'], round(wallet - 200000, 2))
        self.assertEqual(self.rt.world.t1Cash[cid], treasury)
        self.assertEqual(self.rt.world.t1Controller[cid], 1)
        self.assertEqual(self.action('buy').status_code, 400)
        self.assertEqual(self.action('bonus', 1).status_code, 400)
        self.assertEqual(self.action('work', 1).status_code, 400)
        self.assertEqual(self.action('price', 12.34).status_code, 200)
        self.assertEqual(self.rt.world.playerPrice[cid * M.NP], 12.34)
        self.rt.world.t1Controller[cid] = 0
        players.sync_ownership(self.rt)
        self.assertEqual(self.rt.world.t1Controller[cid], 1)
        client = TestClient(self.app)
        client.cookies.update(self.client.cookies)
        restarted = client.get('/play-api/state').json()
        self.assertEqual(restarted['owned'], cid)
        self.assertEqual(restarted['wallet'], self.state['wallet'])
        with players.transaction() as db:
            rows = db.execute("SELECT * FROM ledger WHERE kind='company_purchase'").fetchall()
            self.assertEqual(len(rows), 1)

    def test_two_players_cannot_buy_same_company(self):
        other = TestClient(self.app)
        second = other.get('/play-api/state').json()
        for client, profile in [(self.client, self.state), (other, second)]:
            for _ in range(4):
                profile = client.post('/play-api/action', json={'kind':'work', 'amount':profile['price'], 'revision':profile['revision']}).json()
            profile = client.post('/play-api/action', json={'kind':'bonus', 'amount':200000, 'revision':profile['revision']}).json()
            if client is self.client:
                self.state = profile
            else:
                second = profile
        cid = self.state['offer']['id']
        self.assertEqual(second['offer']['id'], cid)
        self.assertEqual(self.action('buy').status_code, 200)
        rejected = other.post('/play-api/action', json={'kind':'buy','revision':second['revision']})
        self.assertEqual(rejected.status_code, 400)
        refreshed = other.get('/play-api/state').json()
        self.assertEqual(refreshed['wallet'], second['wallet'])
        self.assertNotEqual(refreshed['offer']['id'], cid)
        self.assertGreater(refreshed['revision'], second['revision'])

    def test_t1_recipe_space_cost_and_loss_gate(self):
        reference = {'price': 3, 'rawPrice': 1, 'conversion': .25,
                     'storage': 50000, 'machinery': 1000, 'capacity': 6000}
        p = new_profile(reference)
        work(p, 3)
        self.assertEqual(p['raw'], p['last']['bought'] - p['last']['made'])
        self.assertEqual(p['stock'], 12000 + p['last']['made'] - p['last']['sold'])
        self.assertLessEqual(p['raw'] + p['stock'] + 1000, 50000)
        self.assertLessEqual(p['last']['made'], 6000)
        self.assertEqual(p['unitCost'], 1.25)
        p['reference']['rawPrice'] = 2
        work(p, 3)
        self.assertGreater(p['unitCost'], 1.25)
        self.assertLess(p['unitCost'], 2.25)  # Existing raw stock retains its basis.
        work(p, .5)
        self.assertEqual(p['last']['made'], 0)
        self.assertGreaterEqual(p['cash'], 0)

    def test_demo_reset_preserves_person_and_reconciles_wallet(self):
        pid = self.state['person']['id']
        for _ in range(4):
            self.action('work', self.state['price'])
        self.action('bonus', 100)
        revision = self.state['revision']
        world_cash = self.rt.world.t1Cash.copy()
        self.assertEqual(self.action('reset').status_code, 200)
        self.assertEqual(self.state['person']['id'], pid)
        self.assertEqual(self.state['cash'], 240000)
        self.assertEqual(self.state['wallet'], 0)
        self.assertEqual(self.state['stock'], 12000)
        self.assertEqual(self.state['period'], 0)
        self.assertEqual(self.state['history'], [])
        self.assertEqual(self.state['revision'], revision + 1)
        np.testing.assert_array_equal(self.rt.world.t1Cash, world_cash)
        with players.transaction() as db:
            self.assertEqual(db.execute('SELECT SUM(amount_cents) FROM ledger WHERE player_id=?', (pid,)).fetchone()[0], 0)
        self.assertEqual(self.client.get('/play-api/state').json()['period'], 0)

    def test_production_target(self):
        self.assertEqual(self.action('work', 3, production=1234).status_code, 200)
        self.assertEqual(self.state['last']['made'], 1234)
        self.assertEqual(self.client.get('/play-api/state').json()['productionTarget'], 1234)
        self.assertEqual(self.action('work', 3, production=0).status_code, 200)
        self.assertEqual(self.state['last']['made'], 0)
        self.assertEqual(self.action('work', 3, production=999999).status_code, 400)
        self.assertEqual(self.action('work', 3, production=1.5).status_code, 422)
        self.action('reset')
        self.assertNotIn('productionTarget', self.state)

    def test_demo_fluctuates_without_a_world(self):
        def forbidden_world():
            raise AssertionError('Demo must not access a shared world')
        app = FastAPI()
        app.include_router(create_router(forbidden_world))
        client = TestClient(app)
        state = client.get('/play-api/state').json()
        quotes, costs = [], []
        for _ in range(12):
            response = client.post('/play-api/action', json={'kind':'work', 'amount':3, 'production':3000, 'revision':state['revision']})
            self.assertEqual(response.status_code, 200)
            state = response.json()
            quotes.append(state['reference']['rawPrice'])
            costs.append(state['unitCost'])
        self.assertGreater(len(set(quotes)), 5)
        self.assertGreater(len(set(costs)), 2)
        before = state['reference']
        self.assertEqual(client.get('/play-api/state').json()['reference'], before)

    def test_demand_and_accounting(self):
        reference = {'price':10,'tick':0,'product':'Test'}
        low, high = new_profile(reference), new_profile(reference)
        work(low, 8)
        work(high, 15)
        self.assertGreater(low['last']['sold'], high['last']['sold'])
        p = new_profile(reference)
        opening = p['cash'] + p['stock'] * p['unitCost']
        work(p, 10)
        closing = p['cash'] + p['stock'] * p['stockBasis'] + p['raw'] * p['rawBasis']
        self.assertAlmostEqual(closing - opening, p['last']['profit'])
        p['period'] = 4
        bonus(p, p['cash'])
        work(p, 10)
        self.assertGreaterEqual(p['cash'], 0)
        self.assertGreaterEqual(p['stock'], 0)
        for value in [-1, float('inf'), float('nan')]:
            with self.assertRaises(ValueError): work(p, value)


if __name__ == '__main__':
    unittest.main()
