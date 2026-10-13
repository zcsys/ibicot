import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.server.aggregates import project_complexity_balances
from economy.kernel.tick import storage_rent_equity


class ComplexityBalanceTests(unittest.TestCase):
    def test_actual_balances_reconcile_with_tiers(self):
        cfg,w=reset_world({'t2FirmCount':100,'distributorCount':10})
        w.t1Bought[:]=np.arange(M.N1)
        w.t2Bought[:100]=np.arange(100)
        w.raw[:]=3;w.t1Fin[:]=2
        w.t2Raw[:100*M.NE]=5;w.t2T1Raw[:100*M.NI]=7;w.t2Fin[:int(w.t2LineCount)]=11
        rows=project_complexity_balances(w,cfg)
        for tier,cs,n in [('t1',(1,2),M.N1),('t2',(3,4),100)]:
            for field,array in [('cash',getattr(w,tier+'Cash')[:n]),
                                ('bought',getattr(w,tier+'Bought')[:n]),
                                ('equity',storage_rent_equity(w,cfg,tier))]:
                self.assertAlmostEqual(sum(rows[c][field] for c in cs),array.sum(),places=5)
        self.assertEqual(rows[1]['bought'],w.t1Bought[:M.T1_FIRM_OFFSETS[4]].sum())
        self.assertEqual(rows[2]['bought'],w.t1Bought[M.T1_FIRM_OFFSETS[4]:].sum())
        self.assertEqual(sum(rows[c]['inventory'] for c in (1,2)),w.raw.sum()+(w.t1Fin*w.t1Operates).sum())
        self.assertEqual(sum(rows[c]['inventory'] for c in (3,4)),w.t2Raw.sum()+w.t2T1Raw.sum()+w.t2Fin.sum())

    def test_shared_company_is_not_double_counted(self):
        cfg,w=reset_world({'t2FirmCount':2,'distributorCount':1})
        # Give one refinery a second line in the other complexity.
        w.t1Operates[4]=1
        w.t1Cash[:]=0;w.t1Cash[0]=100
        w.t1Bought[:]=0;w.t1Bought[0]=20
        rows=project_complexity_balances(w,cfg)
        self.assertEqual((rows[1]['cash'],rows[2]['cash']),(50,50))
        self.assertEqual((rows[1]['bought'],rows[2]['bought']),(10,10))
