import unittest
import numpy as np
from economy.server.runtime import KernelRuntime
from tools.buying_v2.engine import IndustrialReferenceEngine
from tools.buying_v2.prepurchase_run import CaptureEngine


class CaptureRunTests(unittest.TestCase):
    def test_full_ticks_equal_without_capture(self):
        runtimes=[KernelRuntime(dict(t2FirmCount=30,distributorCount=100,seed=137)) for _ in range(2)]
        rows=[]
        engines=[IndustrialReferenceEngine(runtimes[0]),CaptureEngine(runtimes[1],30,rows.append)]
        for tick in range(1,3):
            for engine in engines: engine.step(tick)
            a,b=[rt.world for rt in runtimes]
            for name in a.array_names:
                np.testing.assert_array_equal(getattr(a,name),getattr(b,name),err_msg=name)
            self.assertEqual(runtimes[0].state,runtimes[1].state)
            np.testing.assert_array_equal(engines[0].industrial_observations,engines[1].industrial_observations)
        self.assertEqual(len(rows),4)
        for row in rows:
            self.assertTrue(row['reconciled'])
            self.assertEqual(len(row['records'])+len(row['missing']),30)
            self.assertEqual({r['firm'] for r in row['records']},{r['firm'] for r in row['settlement']})

        import json, tempfile
        from pathlib import Path
        from tools.buying_v2.prepurchase_audit import audit
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rows.jsonl'
            path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            self.assertEqual(audit(path)['phases'],4)
            next(r for r in rows if r['settlement'])['settlement'][0]['cashAfter']+=1
            path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            with self.assertRaisesRegex(ValueError,'cash'): audit(path)
