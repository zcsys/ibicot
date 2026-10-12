import unittest
from dataclasses import replace
from tools.buying_v2.continuation_bound import upper_value,line_envelope
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.phase_ledger import OpenBook,SettleBook,SetQuotes
from tools.buying_v2.fee_boundary_study import fee_case,income_case

class CostEnvelopeTests(unittest.TestCase):
    def test_certain_costs_tighten_bound_to_analytical_profit(self):
        c,s,paths=case(1,1,1,1);p=paths[0]
        bound=upper_value(c,s,s,p.events,p.input_values,p.finished_values,include_costs=True)
        self.assertAlmostEqual(bound,5.5,places=6)
        self.assertLess(bound,upper_value(c,s,s,p.events,p.input_values,p.finished_values))

    def test_existing_stock_is_not_reused_and_future_best_quote_is_allowed(self):
        c,s,paths=case(1,1,1,1);s=replace(s,finished=(1,),finished_basis=(1.,),quotes=(2.,))
        events=(OpenBook('low'),SettleBook('low',(1,)),SetQuotes('raise',(10.,)),OpenBook('high'),SettleBook('high',(1,)))
        bound=upper_value(c,s,s,events,((0.,0.),)*2,((0.,)*3,),include_costs=True)
        self.assertAlmostEqual(bound,10.,places=6)  # Relaxed choice to defer the single item.

    def test_no_future_offer_limits_production_to_owned_complements(self):
        c,s,paths=case(2,1,1,1)
        self.assertAlmostEqual(line_envelope(c.lines[0],0,(1,0),(float('inf'),float('inf')),2,((2,10.),)),0.,places=6)
        self.assertAlmostEqual(line_envelope(c.lines[0],0,(1,1),(float('inf'),float('inf')),2,((2,10.),)),9.5,places=6)

    def test_shared_inputs_and_multiple_lines_against_exhaustive_policy(self):
        import random
        from tools.buying_v2.industry_oracle import Line,Offer
        from tools.buying_v2.phase_ledger import Company,State,Purchase
        from tools.buying_v2.phase_oracle import Scenario
        from tools.buying_v2.benchmark_phase_search import frozen_funding
        rng=random.Random(461823)
        for _ in range(60):
            held=tuple(rng.randrange(3) for _ in range(2))
            lines=(Line((1,1),1,.5,8.,0.,(0.,0.),2.),Line((2,0),1,.25,7.,0.,(0.,0.),2.))
            c=Company((1.,1.),(2,2),12.,lines,(2,2),0.)
            s=State(20.,held,(2.,2.),(0,0),(0.,0.),(8.,7.),(-1,-1))
            offers=tuple(Offer(m,k,float(rng.randrange(1,6)),2) for m in range(2) for k in range(2))
            buy=Purchase('buy',offers,(),(0.,)*4,1.,0.,(0,1),0.)
            path=Scenario(1.,(buy,OpenBook('sales'),SettleBook('sales',(1,1))),((0.,)*3,)*2,((0.,)*3,)*2)
            bound=upper_value(c,s,s,path.events,path.input_values,path.finished_values,include_costs=True)
            exact=solve(c,s,(path,),funding=frozen_funding)['expectedValue']
            self.assertGreaterEqual(bound,exact)

    def test_scaled_money_keeps_the_cost_bound_above_actual_return(self):
        for scale in (1e-8,1.,1e8):
            c,s,paths=case(1,1,1,1)
            c=replace(c,lines=(replace(c.lines[0],conversion=.5*scale,quote=10.*scale),))
            s=replace(s,cash=100.*scale,quotes=(10.*scale,))
            event=paths[0].events[0]
            event=replace(event,offers=tuple(replace(o,price=o.price*scale) for o in event.offers))
            path=replace(paths[0],events=(event,)+paths[0].events[1:])
            bound=upper_value(c,s,s,path.events,path.input_values,path.finished_values,include_costs=True)
            self.assertGreaterEqual(bound,solve(c,s,(path,),funding='continuation')['expectedValue'])

    def test_shadow_audit_preserves_full_results(self):
        for args in (case(1,1,2,2),case(2,2,2,2),fee_case(7.,3.,3),income_case(.5)):
            base=solve(*args,funding='continuation',allocation_search='feasible-prefix',funding_memo_size=4096,max_prefix_nodes=400000)
            audited=solve(*args,funding='continuation',allocation_search='feasible-prefix',funding_memo_size=4096,max_prefix_nodes=400000,audit_continuation_bound=True,continuation_bound_costs=True)
            stats=audited.pop('boundAudit');base.pop('boundAudit')
            self.assertEqual(base,audited);self.assertGreaterEqual(stats['minSlack'],0.)

if __name__=='__main__':unittest.main()
