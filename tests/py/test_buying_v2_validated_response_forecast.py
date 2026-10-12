import unittest
import numpy as np
from tools.buying_v2.forecast import PublishedChannel
from tools.buying_v2.validated_response_forecast import forecast
from test_buying_v2_bounded_response_forecast import history,P


def predict(h,quote=7.,**changes):
    pub=PublishedChannel(h,'retail',len(h.view('retail')['ticks'])+1)
    cap=changes.get('payoff_cap',20000)
    fallback=pub.forecast('local',seller=0,product=0,quote=quote,payoff_cap=cap,market_size=3,parameters=P)
    args=dict(seller=0,product=0,quote=quote,payoff_cap=20000,decay=1.,peer_elasticity=1.,
              peer_max_log_quote_distance=2.,max_log_extrapolation=2.,max_quote_folds=16,fallback=fallback)
    args.update(changes)
    before=pub.local_informed.copy();result=forecast(pub,**args)
    np.testing.assert_array_equal(pub.local_informed,before)
    return result


class ValidatedResponseTests(unittest.TestCase):
    def test_observed_curve_selects_bounded_without_target_data(self):
        h=history();result=predict(h)
        v=result.diagnostics['validation']
        self.assertEqual(v['selected'],'bounded')
        self.assertAlmostEqual(result.mean,12000./1.7,places=7)
        self.assertLess(v['losses']['bounded'],v['losses']['peer'])
        self.assertEqual([f['withheldTicks'] for f in v['folds']],[[1],[2],[3]])

    def test_steeper_curve_retains_peer_and_duplicate_quotes_share_fold(self):
        quotes=(4.,8.,11.)*2
        sales=tuple(10000./(1+(q/10.)**2) for q in quotes)
        result=predict(history(quotes,sales),payoff_cap=10000)
        v=result.diagnostics['validation']
        self.assertEqual(v['selected'],'peer')
        self.assertEqual([f['withheldTicks'] for f in v['folds']],[[1,4],[2,5],[3,6]])
        self.assertGreater(v['losses']['bounded'],v['losses']['peer'])
        # Validation is conditional on the fixed payoff cap, not a universal
        # private buyer-shape classifier. Removing this cap changes the score.
        uncapped=predict(history(quotes,sales),payoff_cap=20000)
        self.assertEqual(uncapped.diagnostics['validation']['selected'],'bounded')

    def test_incomplete_validation_and_unsupported_data_preserve_peer(self):
        for h,changes,reason in ((history((5.,10.),(8000.,6000.)),{},'insufficient-quotes-for-validation'),
                                 (history(),dict(max_log_extrapolation=0.),'incomplete-validation'),
                                 (history(),dict(max_quote_folds=2),'validation-fold-limit'),
                                 (history(constrained=True),{},'bounded-unsupported:no-eligible-observations')):
            result=predict(h,**changes)
            self.assertEqual(result.diagnostics['validation']['selected'],'peer')
            self.assertEqual(result.diagnostics['validation']['reason'],reason)

    def test_invalid_work_budget(self):
        for cap in (0,-1,True,1.5):
            with self.assertRaises(ValueError):predict(history(),max_quote_folds=cap)


if __name__=='__main__':unittest.main()
