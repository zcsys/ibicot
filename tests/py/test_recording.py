import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch
import numpy as np
from economy.core.state import reset_world
from economy.core.accounting import company_earnings
from economy.server.recording import profitability_rows, CompanyHistory


class RecordingTests(unittest.TestCase):
    def test_auto_pause_saves_company_history_and_reloadable_checkpoint(self):
        from economy.server.runtime import KernelRuntime
        from economy.server.persistence import load_checkpoint
        with tempfile.TemporaryDirectory() as directory, patch('economy.server.runtime._STATS_DIR',Path(directory)), patch.dict(os.environ,{'ECONOMY_MAX_TICK':'1'}):
            rt=KernelRuntime({'t2FirmCount':12,'distributorCount':30})
            rt.run();rt.step()
            self.assertFalse(rt.running)
            path=rt._companyStats.path
            self.assertEqual(len(list(path.glob('companies-*.npz'))),1)
            cfg,tick,w,state=load_checkpoint(str(path/'final-checkpoint'))
            self.assertEqual(tick,1)
            np.testing.assert_array_equal(w.t2Cash,rt.world.t2Cash)
            self.assertTrue((Path(directory)/'generation_run.jsonl').exists())

    def test_product_profit_reconciles_posted_company_earnings(self):
        cfg,w=reset_world({'t2FirmCount':12,'distributorCount':30})
        w.netEarningsAvailable=True
        for tier in ('t0','t1','t2'):
            revenue=getattr(w,tier+'Revenue'); cogs=getattr(w,tier+'COGS')
            revenue[:]=np.arange(len(revenue))%17+10
            cogs[:]=revenue*.6
            if tier=='t2':
                revenue[int(w.t2LineCount):]=0;cogs[int(w.t2LineCount):]=0
            getattr(w,tier+'SwitchingIncome')[:]=3
            getattr(w,tier+'SwitchingExpense')[:]=2
            if tier!='t0':getattr(w,tier+'RentCharge')[:]=7
        rows=profitability_rows(w,cfg)
        for tier in ('t0','t1','t2'):
            actual=sum(p['netEarnings'] for p in rows if p['tier']==tier)
            self.assertAlmostEqual(actual,company_earnings(w,cfg,tier).sum())
        self.assertEqual({p['complexity'] for p in rows},{0,1,2,3,4})
        for p in rows:
            if p['revenue']:
                self.assertAlmostEqual(p['netMargin'],p['netEarnings']/p['revenue'])

    def test_company_archive_retains_period_totals_and_partial_intervals(self):
        cfg,w=reset_world({'t2FirmCount':12,'distributorCount':30})
        w.netEarningsAvailable=True
        with tempfile.TemporaryDirectory() as directory:
            recorder=CompanyHistory(directory,cfg)
            for t in (359,360):
                w.t2Revenue[:int(w.t2LineCount)]=t
                recorder.record(w,cfg,t)
            recorder.record(w,cfg,361)
            recorder.flush(w,cfg)
            files=sorted(recorder.path.glob('companies-*.npz'))
            self.assertEqual(len(files),2)
            with np.load(files[0]) as data:
                self.assertEqual(int(data['startTick']),359)
                self.assertEqual(int(data['endTick']),360)
                self.assertAlmostEqual(data['t2_revenue'].sum(),719*int(w.t2LineCount))
                np.testing.assert_allclose(data['t0_equity'],np.full(20,cfg['t0Equity']))
                self.assertEqual(len(data['t2_equity']),12)
            with np.load(files[1]) as data:
                self.assertEqual(int(data['startTick']),361)
                self.assertAlmostEqual(data['t2_revenue'].sum(),360*int(w.t2LineCount))
