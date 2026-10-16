import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from fastapi.testclient import TestClient
from economy.server import service
from economy.server.runtime import KernelRuntime


class DashboardSaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.old = service._runtime
        self.patches = [patch.object(service, 'DASHBOARD_SAVE_DIR', root/'saves'),
                        patch.object(service, '_STATS_DIR', root/'stats'),
                        patch('economy.server.runtime._STATS_DIR', root/'stats'),
                        patch.object(service, 'sync_ownership')]
        for p in self.patches: p.start()
        self.rt = KernelRuntime({'t2FirmCount': 1, 'distributorCount': 2})
        self.rt.statsPath = root/'stats'/'ticks.jsonl'
        service._runtime = self.rt
        self.client = TestClient(service.app)

    def tearDown(self):
        service._runtime = self.old
        for p in reversed(self.patches): p.stop()
        self.temp.cleanup()

    def test_save_load_restores_arrays_and_pauses_without_overwrite(self):
        self.rt.step()
        before = {k: getattr(self.rt.world,k).copy() for k in self.rt.world.array_names}
        self.rt.run('max')
        saved = self.client.post('/dashboard-saves', json={'name':'Colony trial'})
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(self.rt.running)
        second = self.client.post('/dashboard-saves', json={'name':'Colony trial'}).json()
        self.assertNotEqual(saved.json()['id'],second['id'])
        self.assertEqual(len(self.client.get('/dashboard-saves').json()),2)
        self.rt.step()
        loaded = self.client.post('/dashboard-saves/'+saved.json()['id']+'/load')
        self.assertEqual(loaded.status_code,200,loaded.text)
        self.assertIs(service._runtime,self.rt)
        self.assertEqual(self.rt.tick,1)
        self.assertFalse(self.rt.running)
        trends = self.rt.publish()['complexityTrends']
        self.assertEqual(len(trends), 1)
        self.assertEqual(trends[0]['ticks'], 1)
        self.assertEqual(trends[0]['tick'], 1)
        for key,value in before.items():
            np.testing.assert_array_equal(getattr(self.rt.world,key),value,err_msg=key)

    def test_invalid_save_and_missing_load_leave_world_alone(self):
        self.assertEqual(self.client.post('/dashboard-saves',json={'name':'  '}).status_code,400)
        self.rt.run('max')
        self.assertEqual(self.client.post('/dashboard-saves/not-a-save/load').status_code,404)
        self.assertTrue(self.rt.running)
        self.assertEqual(self.rt.tick,0)
