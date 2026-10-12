import unittest
import numpy as np
from tools.buying_v2.continuation_query_answers import QueryAnswers
from tools.buying_v2.continuation_funding_encoding import encode_answers
from tools.buying_v2.continuation_funding_records import encode_detail


class EncodingTests(unittest.TestCase):
    def fixture(self):
        scratch=QueryAnswers(3,3)
        for ordinal,selected,q,cost,value in [(0,(0,1,2),(2,3,0),11.,-2.),(1,(0,2),(1,3,0),11.,-3.),(2,(1,2),(4,3,0),13.,4.),(3,(0,1,2),None,0.,0.)]:
            row,ready=scratch.request(ordinal,selected)
            if not ready:scratch.store(row,q,cost,value)
        iv=np.array([3,3,0,0,0,7,5,1,0,9,5,1,1,11,5,1,0,0,0],np.int64)
        fv=np.array([1.,0.,0.,0.,2.,1.,3.,0.,0.,0.])
        return scratch,iv,fv

    def test_exact_encoding_including_incumbent_missing_input_and_reused_query(self):
        s,iv,fv=self.fixture()
        demands,a,b=encode_answers(4,iv,fv,np.array([7,-1,-1]),s.requests,s.ready,s.quantities,s.values)
        d=dict(rule='continuation-v2',referenceSuppliers=(7,11,-1),referenceDemands=(1,3,0),jointQuantities=(2,3,0),jointGoods=11.,
            quoteVectors=tuple(dict(material=m,supplier=supplier,quantities=q,goods=goods,conditionalValue=value) for m,supplier,q,goods,value in
                [(0,7,(1,3,0),11.,-3.),(0,9,(4,3,0),13.,4.),(1,11,(2,3,0),11.,-2.)]))
        expected=encode_detail(4,d)
        np.testing.assert_array_equal(demands,[1,4,3]);np.testing.assert_array_equal(a,expected[0]);np.testing.assert_array_equal(b,expected[1])

    def test_empty_offer_book_retains_joint_result_and_missing_references(self):
        s=QueryAnswers(0,2);row,_=s.request(0,());s.store(row,(0,0),0.,-1.)
        demands,iv,fv=encode_answers(0,np.array([0,0,0,0]),np.zeros(4),np.array([-1,-1]),s.requests,s.ready,s.quantities,s.values)
        np.testing.assert_array_equal(demands,[])
        np.testing.assert_array_equal(iv,[0,2,0,-1,-1,0,0,0,0])
        np.testing.assert_array_equal(fv,[0.])

    def test_ties_use_supplier_id_and_incomplete_answers_fail(self):
        s,iv,fv=self.fixture();fv[4]=fv[5]
        _,a,_=encode_answers(0,iv,fv,np.array([-1,-1,-1]),s.requests,s.ready,s.quantities,s.values)
        self.assertEqual(a[3],7)
        s.ready[0]=False
        with self.assertRaisesRegex(ValueError,'not completed'):encode_answers(0,iv,fv,np.array([-1,-1,-1]),s.requests,s.ready,s.quantities,s.values)


if __name__=='__main__':unittest.main()
