import unittest
from dataclasses import asdict
from tools.buying_v2.forecast_probe import world,phase,evaluate
from test_buying_v2_forecast import PARAMETERS


class ForecastProbeTests(unittest.TestCase):
    def spec(self):
        return dict(buyers=8,trainingTicks=2,seeds=[137],latentQuantity=20.,elasticity=1.,halfPrice=10.,
                    sellerStorage=50000.,ampleStock=200,trainingStocks=dict(empty=0,limited=5,ample=200),
                    trainingQuotes=[10.,12.,14.],targetQuotes=[5.,10.,20.],profiles={'fixed':asdict(PARAMETERS)})

    def test_actual_phase_integer_demand_partial_supply_and_compiled_parity(self):
        spec=self.spec();results=[]
        for compiled in (False,True):
            cfg,w=world(spec,137)
            a=phase(w,cfg,1,(200,200,200),(10.,12.,14.),compiled)
            self.assertEqual(a['sold'].tolist(),[80.,0.,0.])
            b=phase(w,cfg,1,(5,200,200),(10.,12.,14.),compiled)
            self.assertEqual(b['sold'][0],5.)
            self.assertGreater(b['sold'][1],0.)
            c=phase(w,cfg,1,(200,200,200),(20.,12.,14.),compiled)
            self.assertEqual(c['sold'][0],0.)
            results.append([x['sold'].tolist() for x in (a,b,c)])
        self.assertEqual(*results)

    def test_targets_paired_histories_lagged_and_no_rival_share_guarantee(self):
        result=evaluate(self.spec(),compiled=False)
        self.assertEqual(len(result['rows']),9)
        for quote in (5.,10.,20.):
            rows=[x for x in result['rows'] if x['targetQuotes'][0]==quote]
            self.assertTrue(all(x['actualSales']==rows[0]['actualSales'] for x in rows))
            for row in rows:
                for forecast in row['predictions']:
                    self.assertEqual(forecast['diagnostics']['latestPublishedTick'],2)
                    self.assertEqual(forecast['diagnostics']['decisionTick'],3)
        expensive=next(x for x in result['rows'] if x['training']=='ample' and x['targetQuotes'][0]==20.)
        self.assertEqual(expensive['actualSales'][0],0.)
        local=next(p for p in expensive['predictions'] if p['regime']=='local' and p['feedback']=='transactions')
        self.assertAlmostEqual(local['predicted'],40.)
        unchanged=next(x for x in result['rows'] if x['training']=='ample' and x['targetQuotes'][0]==10.)
        local=next(p for p in unchanged['predictions'] if p['regime']=='local' and p['feedback']=='transactions')
        self.assertAlmostEqual(local['predicted'],80.)
        market=next(p for p in unchanged['predictions'] if p['regime']=='market' and p['feedback']=='transactions')
        self.assertAlmostEqual(market['predicted'],(80/3)*(12/10))


if __name__=='__main__':unittest.main()
