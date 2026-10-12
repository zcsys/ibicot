import unittest
from tools.buying_v2.forecast_identification_probe import evaluate


def specification():
    return dict(buyers=10, latentQuantity=20., elasticity=1., halfPrice=10., sellerStorage=10000,
        ampleStock=400, trainingStock=1, trainingQuotes=[4.,8.,11.], rivalQuotes=[20.,24.],
        targetQuotes=[3.,6.,9.,13.,18.], seeds=[137], decay=1., peerElasticity=1.,
        peerMaxLogQuoteDistance=2., maxLogExtrapolation=2., maxQuoteFolds=16,
        fallbackParameters=dict(decay=1.,elasticity=1.,censored_tail_weight=.5,
            cold_start_positive_weight=.25,cold_start_quantity=1.,cold_start_quote=1.,prior_weight=0.,hybrid_local_weight=.5),
        buyerProfiles={'lower-ceiling':[dict(count=10,quantity=20.,halfPrice=10.,elasticity=1.)],
                       'higher-ceiling':[dict(count=10,quantity=40.,halfPrice=10./3,elasticity=1.)]})


class IdentificationProbeTests(unittest.TestCase):
    def test_identical_positive_sales_histories_hide_distinct_restocked_sales(self):
        spec = specification()
        a = evaluate(spec, compiled=False)
        b = evaluate(spec, compiled=True)
        self.assertEqual(a,b)
        self.assertTrue(a['publishedHistoriesIdentical'])
        self.assertTrue(any(r['unavoidableWorstAbsoluteError'] > 0 for r in a['rows']))
        for row in a['rows']:
            gap = abs(row['actualSales'][0]-row['actualSales'][1])
            self.assertEqual(row['unavoidableWorstAbsoluteError'],gap/2)
            self.assertGreaterEqual(max(abs(row['forecast']['mean']-y) for y in row['actualSales']),gap/2)

    def test_empty_stock_and_invalid_private_profiles(self):
        spec = specification();spec['trainingStock']=0
        self.assertTrue(evaluate(spec, compiled=False)['publishedHistoriesIdentical'])
        spec['trainingStock']=True
        with self.assertRaises(ValueError):evaluate(spec, compiled=False)
        spec = specification();spec['buyerProfiles'].pop('higher-ceiling')
        with self.assertRaises(ValueError):evaluate(spec, compiled=False)


if __name__ == '__main__': unittest.main()
