import unittest
from dataclasses import asdict
import numpy as np
from tools.buying_v2.forecast import ForecastParameters
from tools.buying_v2.forecast_probe import world
from tools.buying_v2.forecast_response_stress import evaluate,install_profile,expected_focal_sales


class ResponseStressTests(unittest.TestCase):
    def spec(self):
        return dict(buyers=8,latentQuantity=20.,halfPrice=10.,elasticity=1.,sellerStorage=50000,ampleStock=200,
                    seeds=[137],trainingQuotes=[4.,8.,11.],rivalQuotes=[20.,24.],targetQuotes=[3.,9.,18.,26.],decay=1.,
                    maxLogExtrapolation=2.,peerElasticity=1.,peerMaxLogQuoteDistance=2.,
                    fallbackParameters=asdict(ForecastParameters(1.,1.,0.,.25,1.,1.,0.,.5)),
                    buyerProfiles=dict(control=[dict(count=8,quantity=20.,halfPrice=10.,elasticity=1.)],
                        mixed=[dict(count=4,quantity=5.,halfPrice=5.,elasticity=1.),dict(count=4,quantity=35.,halfPrice=20.,elasticity=1.)],
                        steep=[dict(count=8,quantity=20.,halfPrice=10.,elasticity=2.)]))

    def test_reference_compiled_and_analytical_profiles_match(self):
        spec=self.spec();a=evaluate(spec,compiled=False);b=evaluate(spec,compiled=True)
        self.assertEqual(a,b)
        self.assertEqual(len(a['rows']),12)
        for row in a['rows']:
            self.assertEqual(row['actualSales'][0],row['analyticalFocalSales'])
            self.assertEqual(row['diagnostics']['latestPublishedTick'],3)
            self.assertEqual(row['diagnostics']['decisionTick'],4)
            self.assertNotIn('buyerProfiles',row['diagnostics'])

    def test_profile_population_validation_and_active_arrays(self):
        spec=self.spec();cfg,w=world(spec,137)
        before=w.distributorQMax[8:].copy()
        install_profile(w,cfg,spec['buyerProfiles']['mixed'])
        np.testing.assert_array_equal(w.distributorQMax[:8],[5.]*4+[35.]*4)
        np.testing.assert_array_equal(w.distributorQMax[8:],before)
        for groups in ([],[dict(count=7,quantity=20.,halfPrice=10.,elasticity=1.)],
                       [dict(count=8,quantity=20.,halfPrice=10.,elasticity=0.)]):
            with self.assertRaises(ValueError):install_profile(w,cfg,groups)
        with self.assertRaises(ValueError):expected_focal_sales(spec['buyerProfiles']['mixed'],137,1,20.,[20.,24.])
        spec['ampleStock']=1
        with self.assertRaises(ValueError):evaluate(spec)


if __name__=='__main__':unittest.main()
