import itertools
import unittest
from tools.buying_v2.trace_search_geometry import bounded_compositions,geometry,summarize


class TraceGeometryTests(unittest.TestCase):
    def test_compositions_match_independent_enumeration(self):
        for n in range(5):
            for caps in itertools.product(range(4),repeat=n):
                for total in range(5):
                    expected=sum(sum(x)<=total for x in itertools.product(*(range(c+1) for c in caps)))
                    self.assertEqual(bounded_compositions(caps,total),expected)

    def test_lots_same_material_and_missing_callback(self):
        doc=dict(seed=137,tick=1,tier=2,phase=3,materialFields=['target'],offerFields=['materialIndex','stock'])
        row=dict(firm=4,status='captured',lot=2,materials=[[4]],offers=[[0,5],[0,4]])
        r=geometry(doc,row);self.assertEqual(r['independentStockSlotGrid'],'9');self.assertEqual(r['perMaterialSlotFeasibleGrid'],'6')
        missing=geometry(doc,dict(firm=5,status='callback-not-observed'))
        summary=summarize([r,missing])['T2-phase-3'];self.assertEqual(summary['captured'],1);self.assertEqual(summary['notObserved'],1)
        empty=geometry(doc,dict(row,offers=[]));self.assertEqual(empty['perMaterialSlotFeasibleGrid'],'1')

    def test_invalid_quantity_rejected(self):
        for caps,total in [([-1],2),([1],-1),([True],2),([1],1.5)]:
            with self.assertRaises(ValueError):bounded_compositions(caps,total)
        doc=dict(seed=137,tick=1,tier=1,phase=1,materialFields=['target'],offerFields=['materialIndex','stock'])
        with self.assertRaises(ValueError):geometry(doc,dict(firm=1,status='captured',lot=1,materials=[[1.5]],offers=[]))


if __name__=='__main__':unittest.main()
