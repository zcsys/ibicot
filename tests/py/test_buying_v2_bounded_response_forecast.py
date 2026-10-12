import unittest
from dataclasses import replace
import numpy as np
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.forecast import PublishedChannel,ForecastParameters
from tools.buying_v2.competitive_forecast import forecast as peer
from tools.buying_v2.bounded_response_forecast import forecast

P=ForecastParameters(1.,1.,0.,.25,1.,1.,0.,.5)


def history(quotes=(5.,10.,15.),sales=(8000.,6000.,4800.),constrained=False):
    h=SellerHistory(len(quotes))
    for tick,(quote,sold) in enumerate(zip(quotes,sales),1):
        closing=np.array([20000.-sold,20000.,20000.]);short=np.array([int(constrained),0,0])
        h.record('retail',tick,np.zeros(3,dtype=int),np.arange(3),np.ones(3),np.full(3,20000.),closing,
                 np.array([quote,30.,40.]),np.array([sold,0.,0.]),np.array([np.ones(3),np.ones(3),short]))
    return h


def predict(h,quote,**changes):
    pub=PublishedChannel(h,'retail',len(h.view('retail')['ticks'])+1)
    local=pub.forecast('local',seller=0,product=0,quote=quote,payoff_cap=20000,market_size=3,parameters=P)
    fallback=peer(pub,seller=0,product=0,quote=quote,payoff_cap=20000,decay=1.,elasticity=1.,max_log_quote_distance=2.,fallback=local)
    kw=dict(seller=0,product=0,quote=quote,payoff_cap=20000,decay=1.,max_log_extrapolation=2.,fallback=fallback)
    kw.update(changes)
    return forecast(pub,**kw)


class BoundedResponseTests(unittest.TestCase):
    def test_recovers_supplied_saturating_curve_and_bounded_extrapolation(self):
        h=history()
        for quote in (1.,5.,7.,10.,15.,20.):
            f=predict(h,quote)
            self.assertFalse(f.diagnostics['fallbackUsed'])
            self.assertAlmostEqual(f.mean,12000./(1.+quote/10.),places=7)
            self.assertAlmostEqual(f.diagnostics['fit']['zeroPriceMean'],12000.)
        self.assertTrue(predict(h,.001,max_log_extrapolation=0.).diagnostics['fallbackUsed'])
        self.assertFalse(predict(h,7.,max_log_extrapolation=0.).diagnostics['fallbackUsed'])

    def test_insufficient_support_constraints_and_wrong_slope_use_explicit_fallback(self):
        for h,reason in ((history((10.,),(6000.,)),'insufficient-quote-variation'),
                         (history(constrained=True),'no-eligible-observations'),
                         (history(sales=(100.,200.,300.)),'inadmissible-fitted-response')):
            f=predict(h,8.);self.assertTrue(f.diagnostics['fallbackUsed']);self.assertEqual(f.diagnostics['fallbackReason'],reason)
        self.assertTrue(predict(history(),50.).diagnostics['fallbackUsed'])
        self.assertEqual(predict(history(),50.).mean,0.)

    def test_quote_scale_frozen_publication_and_bad_fallback(self):
        h=history();pub=PublishedChannel(h,'retail',4)
        base=predict(h,7.)
        fallback=replace(base,diagnostics={**base.diagnostics,'seller':99})
        with self.assertRaises(ValueError):forecast(pub,seller=0,product=0,quote=7.,payoff_cap=20000,decay=1.,max_log_extrapolation=2.,fallback=fallback)
        kw=dict(seller=0,product=0,quote=7.,payoff_cap=20000,decay=1.,max_log_extrapolation=2.,fallback=base)
        frozen=forecast(pub,**kw)
        h.channels['retail']['sold'].fill(1.)
        h.channels['retail']['quote'].fill(1.)
        self.assertEqual(frozen,forecast(pub,**kw))
        for scale in (1e-8,1e8):
            scaled=history(tuple(q*scale for q in (5.,10.,15.)))
            # Rival quotes must scale as well to preserve the observed rank.
            scaled.channels['retail']['quote'][:,1:]*=scale
            f=predict(scaled,7.*scale)
            self.assertAlmostEqual(f.mean,base.mean,places=7)


if __name__=='__main__':unittest.main()
