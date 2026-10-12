import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.forecast import ForecastParameters, PublishedChannel


PARAMETERS = ForecastParameters(decay=1., elasticity=1., censored_tail_weight=.5,
    cold_start_positive_weight=.25, cold_start_quantity=4., cold_start_quote=2.,
    prior_weight=0., hybrid_local_weight=.25)


class ForecastTests(unittest.TestCase):
    def sample(self, history, tick, sales=(2, 6), closing=(10, 10), discovery=(1, 1),
               funded=(1, 1), short=(0, 0), quotes=(2., 2.), offered=(1, 1)):
        sold=np.array(sales,dtype=float)
        history.record('retail',tick,np.array([3,3]),np.array([0,1]),np.array(offered),
                       sold+closing,np.array(closing,dtype=float),np.array(quotes),sold,
                       np.array([discovery,funded,short]))

    def forecast(self, h, regime='local', tick=2, seller=0, feedback='inquiries', **changes):
        args=dict(seller=seller,product=3,quote=2.,payoff_cap=10,market_size=2,parameters=PARAMETERS)
        args.update(changes)
        return PublishedChannel(h,'retail',tick,feedback=feedback).forecast(regime,**args)

    def test_local_market_hybrid_have_independent_expected_values(self):
        h=SellerHistory(3);self.sample(h,1)
        self.assertAlmostEqual(self.forecast(h).mean,2.)
        self.assertAlmostEqual(self.forecast(h,'market').mean,4.)
        # Mixture of distributions, not demand summed across information sources.
        hybrid=self.forecast(h,'hybrid')
        self.assertAlmostEqual(hybrid.mean,.25*2+.75*4)
        self.assertEqual(hybrid.quantities,(2,4))
        np.testing.assert_allclose(hybrid.probabilities,(.25,.75))
        # Product totals are divided among current eligible sellers exactly once.
        self.assertAlmostEqual(sum(self.forecast(h,'market',seller=i).mean for i in range(2)),8.)
        self.assertAlmostEqual(self.forecast(h,'market',market_size=4).mean,2.)

    def test_no_exposure_is_missing_and_zero_funded_interest_is_observed_zero(self):
        h=SellerHistory(3)
        self.sample(h,1,sales=(0,0),closing=(0,10),discovery=(0,1),funded=(0,0))
        missing=self.forecast(h)
        self.assertEqual(missing.diagnostics['observedRows'],0)
        self.assertAlmostEqual(missing.mean,1.)
        measured=self.forecast(h,seller=1)
        self.assertEqual(measured.mean,0.)
        self.assertEqual(measured.diagnostics['observedRows'],1)
        # Empty stock cannot imply censoring when every sampled bid was zero.
        h2=SellerHistory(2)
        self.sample(h2,1,sales=(0,0),closing=(0,0),funded=(0,0))
        self.assertEqual(self.forecast(h2).mean,0.)
        self.assertEqual(self.forecast(h2).diagnostics['constrainedRows'],0)

    def test_stock_constraints_use_explicit_tail_mixture(self):
        h=SellerHistory(2)
        self.sample(h,1,sales=(2,0),closing=(0,10),funded=(1,0))
        prediction=self.forecast(h)
        self.assertEqual(prediction.quantities,(2,10))
        self.assertEqual(prediction.probabilities,(.5,.5))
        self.assertEqual(prediction.mean,6.)
        for weight,mean in ((0,2),(1,10)):
            self.assertEqual(self.forecast(h,parameters=replace(PARAMETERS,censored_tail_weight=weight)).mean,mean)
        # Short checks preserve an earlier shortage even if residual stock > 0.
        h2=SellerHistory(2)
        self.sample(h2,1,sales=(2,0),closing=(1,10),funded=(1,0),short=(1,0))
        self.assertEqual(self.forecast(h2).mean,6.)

    def test_price_adjustment_is_explicit_and_integer_mixture_preserves_mean(self):
        h=SellerHistory(2);self.sample(h,1,sales=(3,6))
        f=self.forecast(h,quote=4.)
        self.assertEqual(f.quantities,(1,2))
        self.assertAlmostEqual(f.mean,1.5)
        flat=self.forecast(h,quote=4.,parameters=replace(PARAMETERS,elasticity=0.))
        self.assertAlmostEqual(flat.mean,3.)
        self.assertEqual(self.forecast(h,quote=1e-300).mean,10.)
        self.assertLess(self.forecast(h,quote=1e300).mean,1e-290)

    def test_cold_start_is_explicit_quote_anchored_and_can_be_zero(self):
        h=SellerHistory(2)
        self.assertAlmostEqual(self.forecast(h).mean,1.)
        self.assertAlmostEqual(self.forecast(h,quote=4.).mean,.5)
        self.assertEqual(self.forecast(h,parameters=replace(PARAMETERS,cold_start_positive_weight=0.)).mean,0.)
        # Prior quantity does not grow when the planner offers a larger cap.
        self.assertEqual(self.forecast(h,payoff_cap=100).mean,1.)

    def test_completed_tick_lag_and_detached_publication(self):
        h=SellerHistory(4);self.sample(h,1)
        published=PublishedChannel(h,'retail',2)
        self.sample(h,2,sales=(50,50),closing=(0,0))
        self.sample(h,3,sales=(99,99),closing=(0,0))
        self.assertAlmostEqual(self.forecast(h,tick=2).mean,2.)
        self.assertAlmostEqual(self.forecast(h,tick=1).mean,1.)
        f=published.forecast('local',seller=0,product=3,quote=2.,payoff_cap=10,market_size=2,parameters=PARAMETERS)
        self.assertAlmostEqual(f.mean,2.)
        self.assertEqual(f.diagnostics['latestPublishedTick'],1)

    def test_decay_and_prior_weight_have_declared_denominators(self):
        h=SellerHistory(4);self.sample(h,1,sales=(2,2));self.sample(h,2,sales=(6,6))
        p=replace(PARAMETERS,decay=.5,prior_weight=1.)
        f=self.forecast(h,tick=3,parameters=p)
        # Weights: 0.5 for tick 1, 1 for tick 2, 1 for prior whose mean is 1.
        self.assertAlmostEqual(f.mean,(.5*2+6+1)/2.5)
        self.assertAlmostEqual(f.diagnostics['priorProbability'],1/2.5)

    def test_existing_finished_stock_consumes_sales_before_new_output(self):
        h=SellerHistory(2);self.sample(h,1,sales=(3,6))
        f=self.forecast(h)
        np.testing.assert_allclose(f.incremental_values(existing=2,max_new=4,quote=2.),[0,2,2,2,2])
        self.assertEqual(f.incremental_values(existing=5,max_new=1,quote=2.),(0.,0.))
        with self.assertRaisesRegex(ValueError,'contemplated quote'):
            f.incremental_values(existing=0,max_new=1,quote=4.)
        with self.assertRaisesRegex(ValueError,'fixed payoff cap'):
            f.incremental_values(existing=9,max_new=2,quote=2.)

    def test_shutdown_and_market_reentry_without_permanent_local_floor(self):
        h=SellerHistory(2)
        self.sample(h,1,sales=(0,6),funded=(0,1))
        self.assertEqual(self.forecast(h).mean,0.)
        self.assertAlmostEqual(self.forecast(h,'market').mean,3.)
        self.assertAlmostEqual(self.forecast(h,'hybrid').mean,2.25)
        self.sample(h,2,sales=(0,0),funded=(0,0))
        self.sample(h,3,sales=(0,0),funded=(0,0))
        for regime in ('local','market','hybrid'):
            self.assertEqual(self.forecast(h,regime,tick=4).mean,0.)

    def test_other_products_cannot_inflate_this_market_forecast(self):
        h=SellerHistory(2)
        h.record('retail',1,np.array([3,8]),np.array([0,1]),np.ones(2),
                 np.array([12.,1000010.]),np.array([10.,10.]),np.array([2.,900.]),
                 np.array([2.,1000000.]),np.array([[1,1],[1,1],[0,0]]))
        self.assertAlmostEqual(self.forecast(h,'market',market_size=1).mean,2.)

    def test_forecast_after_history_reload_is_identical(self):
        h=SellerHistory(2)
        for tick in range(1,5):
            self.sample(h,tick,sales=(tick,6),short=(int(tick==4),0))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'history.npz';h.save(path)
            restored=SellerHistory.load(path,expected_tick=4)
            for regime in ('local','market','hybrid'):
                self.assertEqual(self.forecast(h,regime,tick=5),self.forecast(restored,regime,tick=5))

    def test_transaction_feedback_distinguishes_stocked_zero_from_empty_missing(self):
        h=SellerHistory(2)
        self.sample(h,1,sales=(0,0),closing=(0,10),discovery=(0,0),funded=(0,0))
        empty=self.forecast(h,feedback='transactions')
        stocked=self.forecast(h,seller=1,feedback='transactions')
        self.assertEqual(empty.mean,1.)  # Explicit cold-start prior, not zero demand.
        self.assertEqual(empty.diagnostics['observedRows'],0)
        self.assertEqual(stocked.mean,0.)
        self.assertEqual(stocked.diagnostics['observedRows'],1)
        self.assertEqual(stocked.diagnostics['feedback'],'transactions')
        self.assertEqual(self.forecast(h,seller=1).mean,1.)

    def test_transaction_forecast_cannot_read_inquiries(self):
        h=SellerHistory(2);self.sample(h,1,sales=(2,0),closing=(1,10),short=(1,0))
        class TransactionView:
            channels=h.channels;catalog=h.catalog;window=h.window
            def view(self,channel):
                return {k:v for k,v in h.view(channel).items()
                        if k not in ('discoveries','fundedChecks','shortChecks')}
        for regime in ('local','market','hybrid'):
            self.assertEqual(self.forecast(h,regime,feedback='transactions'),
                             self.forecast(TransactionView(),regime,feedback='transactions'))
        # A rejected large inquiry is invisible in this information regime.
        self.assertEqual(self.forecast(h).mean,6.)
        self.assertEqual(self.forecast(h,feedback='transactions').mean,2.)
        publication=PublishedChannel(h,'retail',2,feedback='transactions')
        self.assertNotIn('discoveries',publication.rows)
        self.assertNotIn('fundedChecks',publication.rows)
        self.assertNotIn('shortChecks',publication.rows)

    def test_transaction_depletion_and_wholesale_lots(self):
        h=SellerHistory(2)
        h.record('retail',1,np.array([3,3]),np.array([0,1]),np.ones(2),
                 np.array([6.,1.]),np.array([0.,1.]),np.full(2,2.),np.array([6.,0.]),
                 np.array([[1,0],[1,0],[0,0]]),lot=2)
        f=self.forecast(h,feedback='transactions')
        self.assertEqual(f.quantities,(6,10))
        self.assertEqual(f.probabilities,(.5,.5))
        self.assertEqual(f.diagnostics['constrainedRows'],1)
        # One residual item cannot support a wholesale lot; it is not evidence
        # of an unconstrained zero-sales opportunity.
        self.assertEqual(self.forecast(h,seller=1,feedback='transactions').diagnostics['observedRows'],0)

    def test_transaction_publication_reload_lag_and_invalid_mode(self):
        h=SellerHistory(3);self.sample(h,1)
        before=self.forecast(h,feedback='transactions')
        self.sample(h,2,sales=(50,50),closing=(0,0))
        self.assertEqual(before,self.forecast(h,feedback='transactions'))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'history.npz';h.save(path)
            restored=SellerHistory.load(path,expected_tick=2)
            for regime in ('local','market','hybrid'):
                self.assertEqual(self.forecast(h,regime,tick=3,feedback='transactions'),
                                 self.forecast(restored,regime,tick=3,feedback='transactions'))
        with self.assertRaisesRegex(ValueError,'feedback mode'):
            PublishedChannel(h,'retail',3,feedback='hidden-inquiries')

    def test_validation_and_zero_payoff_cap(self):
        h=SellerHistory(2);self.sample(h,1)
        self.assertEqual(self.forecast(h,payoff_cap=0).quantities,(0,))
        for change in (dict(decay=0),dict(elasticity=-1),dict(cold_start_quote=0),
                       dict(cold_start_quantity=-1),dict(prior_weight=float('nan')),dict(hybrid_local_weight=2)):
            with self.assertRaises(ValueError):
                replace(PARAMETERS,**change)
        with self.assertRaisesRegex(ValueError,'completed phase'):
            self.forecast(h,tick=4)
        for change in (dict(product=8),dict(seller=-1),dict(quote=0),dict(payoff_cap=1.5),dict(market_size=0)):
            with self.assertRaises(ValueError):
                self.forecast(h,**change)


if __name__=='__main__':
    unittest.main()
