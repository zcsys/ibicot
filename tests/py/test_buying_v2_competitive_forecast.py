import unittest
from dataclasses import replace
import numpy as np
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.forecast import PublishedChannel, ForecastParameters
from tools.buying_v2.competitive_forecast import forecast

P=ForecastParameters(1.,1.,0.,.25,1.,1.,0.,.5)

class CompetitiveForecastTests(unittest.TestCase):
    def history(self, *, sold=(5000,0,0), closing=(5000,10000,10000), quotes=(10.,12.,14.), short=(0,0,0)):
        h=SellerHistory(3)
        sales=np.array(sold,float);close=np.array(closing,float)
        h.record('retail',1,np.zeros(3,dtype=int),np.arange(3),np.ones(3),sales+close,close,np.array(quotes),sales,
                 np.array([(1,1,1),(1,1,1),short]))
        return h

    def predict(self,h,quote,seller=0,**changes):
        pub=PublishedChannel(h,'retail',2)
        fallback=pub.forecast('local',seller=seller,product=0,quote=quote,payoff_cap=10000,market_size=3,parameters=P)
        args=dict(seller=seller,product=0,quote=quote,payoff_cap=10000,decay=1.,elasticity=1.,max_log_quote_distance=2.,fallback=fallback)
        args.update(changes)
        return forecast(pub,**args)

    def test_competitive_displacement_and_unresolved_low_quote_extrapolation(self):
        h=self.history()
        self.assertEqual(self.predict(h,20.).mean,0.)
        self.assertAlmostEqual(self.predict(h,10.).mean,5000.)
        self.assertEqual(self.predict(h,5.).mean,10000.)
        self.assertFalse(self.predict(h,20.).diagnostics['fallbackUsed'])
        self.assertEqual(self.predict(h,20.).diagnostics['selectedObservations'][0]['seller'],2)

    def test_censored_rival_excludes_whole_book_and_preserves_explicit_fallback(self):
        for h in (self.history(sold=(100,4500,0),closing=(0,5500,10000),short=(1,0,0)),
                  self.history(sold=(0,4500,0),closing=(0,5500,10000))):
            result=self.predict(h,20.)
            self.assertTrue(result.diagnostics['fallbackUsed'])
            self.assertEqual(result.diagnostics['eligibleBooks'],0)

    def test_ties_and_quote_support_do_not_silently_extrapolate(self):
        h=self.history()
        self.assertTrue(self.predict(h,12.).diagnostics['fallbackUsed'])
        self.assertTrue(self.predict(h,20.,max_log_quote_distance=.01).diagnostics['fallbackUsed'])
        self.assertFalse(self.predict(h,10.,max_log_quote_distance=0.).diagnostics['fallbackUsed'])

    def test_new_seller_changes_market_size_and_no_history_uses_fallback(self):
        self.assertTrue(self.predict(self.history(),10.,seller=3).diagnostics['fallbackUsed'])
        self.assertTrue(self.predict(SellerHistory(2),10.).diagnostics['fallbackUsed'])

    def test_identity_permutation_preserves_result(self):
        a=self.predict(self.history(),20.)
        b=self.predict(self.history(sold=(0,5000,0),closing=(10000,5000,10000),quotes=(14.,10.,12.)),20.,seller=1)
        self.assertEqual(a.quantities,b.quantities);self.assertEqual(a.probabilities,b.probabilities)

    def test_frozen_publication_and_fallback_validation(self):
        h=self.history();pub=PublishedChannel(h,'retail',2)
        fb=pub.forecast('local',seller=0,product=0,quote=20.,payoff_cap=10000,market_size=3,parameters=P)
        args=dict(seller=0,product=0,quote=20.,payoff_cap=10000,decay=1.,elasticity=1.,max_log_quote_distance=2.,fallback=fb)
        before=forecast(pub,**args)
        h.channels['retail']['sold'].fill(999)
        self.assertEqual(before,forecast(pub,**args))
        with self.assertRaises(ValueError):forecast(pub,**{**args,'fallback':replace(fb,payoff_cap=5)})
        with self.assertRaises(ValueError):forecast(pub,**{**args,'decay':0.})

if __name__=='__main__':unittest.main()
