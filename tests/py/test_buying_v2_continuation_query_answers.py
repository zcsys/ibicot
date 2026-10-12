import unittest
from tools.buying_v2.continuation_query_answers import QueryAnswers
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.benchmark_phase_search import case


class QueryAnswerTests(unittest.TestCase):
    def test_reuse_ordered_keys_and_values(self):
        q=QueryAnswers(2,2);row,ready=q.request(0,(0,1));self.assertFalse(ready)
        with self.assertRaises(ValueError):q.answer(0)
        q.store(row,(2,1),.3,-.2);same,ready=q.request(1,(0,1))
        self.assertEqual(row,same);self.assertTrue(ready);self.assertEqual(q.answer(0),q.answer(1))
        other,ready=q.request(2,(1,));self.assertFalse(ready);q.store(other,(1,0),0.,2.)
        self.assertNotEqual(q.answer(0),q.answer(2));self.assertEqual(q.buffer_bytes,q.bytes_required(2,2))
        out=q.answer(0);out['goods']=99.;self.assertEqual(q.answer(0)['goods'],.3)
        with self.assertRaises(ValueError):q.request(0,())
        with self.assertRaises(ValueError):q.store(row,(1,1),1.,1.)

    def test_empty_offers_and_invalid_values(self):
        q=QueryAnswers(0,1);row,_=q.request(0,());q.store(row,(0,),0.,0.)
        self.assertEqual(q.answer(0)['quantities'],(0,));self.assertEqual(q.buffer_bytes,q.bytes_required(0,1))
        q=QueryAnswers(2,1)
        for key in (None,1,1.5,'x'):
            with self.assertRaises(ValueError):q.request(0,key)
        row,_=q.request(0,(0,))
        with self.assertRaises(ValueError):q.request(0,(1,))
        for values in (((-1,),0.,0.),((1,),-1.,0.),((1,),0.,float('nan'))):
            with self.assertRaises(ValueError):q.store(row,*values)

    def test_search_scratch_limit_and_exact_peak_replay(self):
        c,s,paths=case(1,1,2,1)
        with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,funding='continuation',max_query_bytes=0)
        self.assertEqual(cm.exception.diagnostics['queryScratchBytes'],0)
        result=solve(c,s,paths,funding='continuation',storage='arena');peak=result['diagnostics']['peakQueryScratchBytes']
        self.assertEqual(result['diagnostics']['queryScratchBytes'],0)
        exact=solve(c,s,paths,funding='continuation',storage='arena',max_query_bytes=peak)
        self.assertEqual(result['expectedValue'],exact['expectedValue']);self.assertEqual([x['funding'] for x in result['leaves']],[x['funding'] for x in exact['leaves']])
        with self.assertRaises(SearchLimit):solve(c,s,paths,funding='continuation',max_query_bytes=peak-1)


if __name__=='__main__':unittest.main()
