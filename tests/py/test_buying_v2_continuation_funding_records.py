import unittest
from tools.buying_v2.continuation_funding_records import FundingRecords,FundingRecordLimit
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case


def detail():return dict(rule='continuation-v2',referenceSuppliers=(2**53+1,-1),referenceDemands=(2,0),jointQuantities=(2,1),jointGoods=.3,
    quoteVectors=(dict(material=0,supplier=2**53+1,quantities=(2,1),goods=.3,conditionalValue=-.2),))


class FundingRecordTests(unittest.TestCase):
    def test_roundtrip_prefix_reuse_and_export_isolation(self):
        p=FundingRecords();d=detail();a=p.append(0,1,d);b=p.append(a,3,d);before=p.diagnostics()
        self.assertEqual(p.append(a,3,d),b);self.assertEqual(p.diagnostics(),before)
        self.assertEqual(p.export(b),{1:d,3:d});self.assertEqual(p.export(0),{})
        out=p.export(b);out[1]['quoteVectors'][0]['goods']=999.
        self.assertEqual(p.export(a),{1:d})

    def test_capacity_and_validation_leave_records_unchanged(self):
        for kwargs in ({'max_nodes':1},{'max_integers':1},{'max_floats':1}):
            p=FundingRecords(**kwargs);before=p.diagnostics()
            with self.assertRaises(FundingRecordLimit):p.append(0,0,detail())
            self.assertEqual(p.diagnostics(),before)
        p=FundingRecords();a=p.append(0,1,detail())
        with self.assertRaises(ValueError):p.append(a,1,detail())
        with self.assertRaises(ValueError):p.append(0,0,{**detail(),'jointGoods':float('nan')})
        with self.assertRaises(ValueError):p.export(True)

    def test_search_limits_and_exact_capacity(self):
        c,s,paths=case(1,1,2,1)
        for kwargs in ({'funding_nodes':1},{'funding_integers':1},{'funding_floats':1}):
            with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',storage='arena',**kwargs)
            self.assertIn('fundingRecords',cm.exception.diagnostics);self.assertNotIn('leaves',cm.exception.diagnostics)
        result=solve(c,s,paths,funding='continuation',storage='arena');d=result['diagnostics']['fundingRecords']
        exact=solve(c,s,paths,funding='continuation',storage='arena',funding_nodes=d['nodes'],funding_integers=d['integerValues'],funding_floats=d['floatValues'])
        self.assertEqual(result['expectedValue'],exact['expectedValue'])
        self.assertEqual([l['funding'] for l in result['leaves']],[l['funding'] for l in exact['leaves']])


if __name__=='__main__':unittest.main()
