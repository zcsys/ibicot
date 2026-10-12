from dataclasses import replace
import unittest
import test_buying_v2_prepurchase_projection as fixtures
from economy.core import model as M
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from tools.buying_v2.prepurchase_state import capture_t2
from tools.buying_v2.prepurchase_projection import project
from tools.buying_v2.phase_ledger import apply
from tools.buying_v2.phase_oracle import Scenario
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident


class NativeProjectionTests(unittest.TestCase):
    def test_fractional_inputs_slots_and_production_match_actual_phase(self):
        for fraction in (.1,.5,.999999999):
            cfg,w,phase=fixtures.ProjectionTests().fixture()
            product=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
            for m,q in product['ingredients']:
                (w.t2Raw if m<M.NE else w.t2T1Raw)[m]=q*2+fraction
                (w.t2RawBasis if m<M.NE else w.t2T1Basis)[m]=.17
            w.t2Fin[0]=fraction;w.t2FinBasis[0]=.23;w.t2Price[0]=100
            overhead=K.production_line_overhead(w,cfg,'t2');results=[]
            def capture(w,c,t,f,p,b):
                if f!=0:return
                raw=capture_t2(w,c,t,f,p,b,overhead);x=project(raw)
                self.assertEqual(x.company.slots,tuple(m['slot'] for m in raw['materials']))
                event=replace(x.purchase,funded_demands=(0,)*len(x.purchase.offers))
                expected,_=apply(x.company,x.state,event,(0,)*len(event.offers))
                path=Scenario(1.,(event,x.settlement((0,))),tuple((0.,) for _ in x.state.held),((0.,),))
                r=Resident(x.company,x.state,compile_calendar(x.company,x.state,(path,)))
                r.run(0,{0:(0,)*len(event.offers)},stop=1)
                self.assertEqual(r.snapshot(),expected);results.append(expected)
            K._operate_tier2_phase(w,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=capture)
            self.assertEqual(len(results),1);result=results[0]
            self.assertEqual(result.finished,(w.t2Fin[0],));self.assertEqual(result.finished_basis,(w.t2FinBasis[0],))
            self.assertEqual(result.cash,w.t2Cash[0])
            for m,q in enumerate(result.held):self.assertEqual(q,(w.t2Raw if m<M.NE else w.t2T1Raw)[m])

    def test_fractional_opening_and_pending_settlement_match_actual_book(self):
        for fraction in (.1,.5,.999999999):
            for sold in (0,2):
                cfg,w,phase=fixtures.ProjectionTests().fixture()
                w.t2Fin[0]=2+fraction;w.t2FinBasis[0]=.23;w.t2Price[0]=7
                book=InputMarket(w,1);seller=book.n1;owner=M.N1
                book.fin[seller]-=sold;book.sold[seller]+=sold
                book.revenue[seller]+=sold*7;book.cogs[seller]+=sold*.23;book.cash[owner]+=sold*7
                x=project(capture_t2(w,cfg,1,0,phase,book,K.production_line_overhead(w,cfg,'t2')))
                self.assertEqual(x.state.book.quantity,(2+fraction,))
                event=x.settlement((0,));expected,_=apply(x.company,x.state,event)
                path=Scenario(1.,(event,),tuple((0.,) for _ in x.state.held),((0.,),))
                r=Resident(x.company,x.state,compile_calendar(x.company,x.state,(path,)));r.run(0,{})
                self.assertEqual(r.snapshot(),expected)
                book.settle()
                self.assertEqual(expected.cash,w.t2Cash[0])
                self.assertEqual(expected.finished,(w.t2Fin[0],))
                self.assertEqual(expected.finished_basis,(w.t2FinBasis[0],))

    def test_fractional_slots_and_offer_residue_remain_explicit(self):
        cfg,w,phase=fixtures.ProjectionTests().fixture()
        cfg['storage']+=.5
        w.t1Fin[:]=1.5
        raw=capture_t2(w,cfg,1,0,phase,InputMarket(w,1),K.production_line_overhead(w,cfg,'t2'))
        x=project(raw)
        self.assertEqual(x.company.slots,tuple(m['slot'] for m in raw['materials']))
        self.assertTrue(any(q!=int(q) for q in x.company.slots))
        self.assertTrue(x.purchase.offers)
        for offer in x.purchase.offers:
            source=next(s for m in raw['offers'] if m['material']==offer.material for s in m['suppliers'] if s['supplier']==offer.supplier)
            self.assertEqual(offer.stock,int(source['current']['fin']))
            self.assertEqual(source['current']['fin'],1.5)
