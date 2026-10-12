from dataclasses import replace
import unittest
from test_buying_v2_phase_ledger import company,state,buy
from tools.buying_v2.phase_ledger import apply,OpenBook,SettleBook
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.continuation_bound import upper_value
from tools.buying_v2.closing_allocation import candidate
import test_buying_v2_continuation_search as verification


class OvercapFinishedTests(unittest.TestCase):
    def fixture(self):
        c=replace(company(),finished_caps=(2,))
        s=state(cash=20.,held=(5,),basis=(.1,),finished=(4,),finished_basis=(1.,))
        e=buy(offers=(),demands=())
        return c,s,e

    def test_stock_is_preserved_and_production_resumes_only_below_cap(self):
        c,s,e=self.fixture()
        end,detail=apply(c,s,e,())
        self.assertEqual(end.finished,(4,));self.assertEqual(detail['outputs'],(0,))
        opened,_=apply(c,end,OpenBook('sales'))
        sold,_=apply(c,opened,SettleBook('sales',(3,)))
        resumed,detail=apply(c,sold,replace(e,label='next'),())
        self.assertEqual(detail['outputs'],(1,));self.assertEqual(resumed.finished,(2,))
        self.assertEqual(c.finished_caps,(2,))

    def test_terminal_spike_above_cap_is_not_lost_by_bound_or_closing(self):
        c,s,e=self.fixture()
        paths=(Scenario(1.,(e,OpenBook('sales'),SettleBook('sales',(0,))),((0.,)*21,),((0.,0.,0.,0.,100.),)),)
        actual=verification.SearchTests().compare(c,s,paths,storage='arena')
        self.assertEqual(actual['expectedValue'],100.)
        self.assertGreaterEqual(upper_value(c,s,s,paths[0].events,paths[0].input_values,paths[0].finished_values),100.)
        closing=candidate(c,s,s,e,((1.,replace(paths[0],events=paths[0].events[1:])),))
        self.assertEqual(closing['expectedValue'],actual['expectedValue'])

    def test_multiphase_compiled_and_oracle_preserve_stock_and_limits(self):
        c,s,e=self.fixture()
        events=(e,OpenBook('early'),SettleBook('early',(3,)),replace(e,label='next'),OpenBook('late'),SettleBook('late',(2,)))
        paths=(Scenario(1.,events,((0.,)*21,),((0.,)*5,)),)
        for storage in ('resident','arena'):
            verification.SearchTests().compare(c,s,paths,storage=storage,funding='continuation')

    def test_shared_bounds_include_value_above_cap(self):
        from tools.buying_v2.shared_first_bound import bound as single
        from tools.buying_v2.shared_joint_first_bound import bound as joint
        for count in (1,2):
            c,s,e=self.fixture()
            if count==2:
                c=replace(c,lines=c.lines*2,finished_caps=(2,2),storage=80.)
                s=replace(s,finished=(4,4),finished_basis=(1.,1.),quotes=(3.,3.))
                e=replace(e,active_lines=(0,1))
            suffix=(OpenBook('a'),SettleBook('a',(0,)*count),replace(e,label='next'),OpenBook('b'),SettleBook('b',(0,)*count))
            path=Scenario(1.,suffix,((0.,)*21,),((0.,0.,0.,0.,100.),)*count)
            result=(single(c,s,s,e,(),((1.,path),),max_first_batches=10) if count==1 else joint(c,s,s,e,(),((1.,path),),max_first_states=100))
            self.assertGreaterEqual(result['value'],100.*count)

    def test_actual_phase_preserves_overallocated_finished_goods(self):
        from economy.core import model as M
        from economy.core.state import reset_world
        from economy.kernel import tick as K
        from tools.buying_v2.prepurchase_state import capture_t2
        from tools.buying_v2.prepurchase_projection import project
        cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
        product=M.T2_PRODUCTS[int(w.t2LineProduct[0])];phase=product['complexity']
        _,slot,_=K.tier2_storage_layout(w,cfg,0)
        w.t2Fin[0]=int(slot/phase)+1;w.t2FinBasis[0]=1.;w.t2Price[0]=100.
        for m,q in product['ingredients']:
            (w.t2Raw if m<M.NE else w.t2T1Raw)[m]+=q*2
            (w.t2RawBasis if m<M.NE else w.t2T1Basis)[m]=.1
        initial=float(w.t2Fin[0]);snapshot=K.production_line_overhead(w,cfg,'t2');expected=[]
        def no_purchase(w,c,t,f,p,b):
            if f==0:
                projected=project(capture_t2(w,c,t,f,p,b,snapshot))
                event=replace(projected.purchase,funded_demands=(0,)*len(projected.purchase.offers))
                expected.append(apply(projected.company,projected.state,event,(0,)*len(event.offers))[0])
        K._operate_tier2_phase(w,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=no_purchase)
        self.assertEqual(w.t2Fin[0],initial)
        self.assertEqual(expected[0].finished[0],w.t2Fin[0])
        self.assertEqual(expected[0].cash,w.t2Cash[0])
        self.assertEqual(expected[0].finished_basis[0],w.t2FinBasis[0])
