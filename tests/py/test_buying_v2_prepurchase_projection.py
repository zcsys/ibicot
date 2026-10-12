from dataclasses import replace
import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from tools.buying_v2.prepurchase_state import capture_t2
from tools.buying_v2.prepurchase_projection import project, ProjectionUnsupported
from tools.buying_v2.phase_ledger import apply


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
        phase=M.T2_PRODUCTS[int(w.t2LineProduct[0])]['complexity']
        return cfg,w,phase

    def test_pending_sales_and_mixed_basis_match_actual_book_settlement(self):
        cfg,w,phase=self.fixture()
        w.t2Fin[0]=10;w.t2FinBasis[0]=2;w.t2Price[0]=7
        book=InputMarket(w,1);s=book.n1;owner=M.N1
        # Earlier buyers took two opening units, then two new units were made.
        book.fin[s]-=2;book.sold[s]+=2;book.revenue[s]+=14;book.cogs[s]+=4
        book.cash[owner]+=17;book.switch_income[owner]+=3
        w.t2Fin[0]=12;w.t2FinBasis[0]=3
        record=capture_t2(w,cfg,1,0,phase,book,K.production_line_overhead(w,cfg,'t2'))
        p=project(record)
        self.assertEqual(p.state.cash,w.t2Cash[0])
        self.assertEqual(p.committed_sales,(2,));self.assertEqual(p.remaining_book_stock,(8,))
        result,detail=apply(p.company,p.state,p.settlement((0,)))
        from tools.buying_v2.phase_oracle import Scenario
        from tools.buying_v2.continuation_program import compile_calendar
        from tools.buying_v2.continuation_resident import Resident
        scenario=Scenario(1.,(p.settlement((0,)),),tuple((0.,) for _ in p.state.held),((0.,),))
        resident=Resident(p.company,p.state,compile_calendar(p.company,p.state,(scenario,)))
        resident.run(0,{})
        self.assertEqual(resident.snapshot(),result)
        book.settle()
        self.assertEqual(result.cash,w.t2Cash[0])
        self.assertEqual(result.finished,(w.t2Fin[0],))
        self.assertEqual(result.finished_basis,(w.t2FinBasis[0],))
        self.assertEqual(detail['sales'],14);self.assertEqual(detail['cogs'],4)
        self.assertEqual(detail['feeIncome'],3)
        with self.assertRaises(ValueError):p.settlement((9,))

    def test_no_purchase_production_matches_real_phase(self):
        cfg,w,phase=self.fixture()
        product=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
        for m,q in product['ingredients']:
            (w.t2Raw if m<M.NE else w.t2T1Raw)[m]+=q*2
            (w.t2RawBasis if m<M.NE else w.t2T1Basis)[m]=.1
        w.t2Price[0]=100
        overhead=K.production_line_overhead(w,cfg,'t2');projected=[]
        def capture(w,c,t,f,p,b):
            if f==0:
                x=project(capture_t2(w,c,t,f,p,b,overhead))
                e=replace(x.purchase,funded_demands=(0,)*len(x.purchase.offers))
                projected.append(apply(x.company,x.state,e,(0,)*len(e.offers))[0])
        K._operate_tier2_phase(w,cfg,M.PRODUCTS,[],M.T2_PRODUCTS,1,phase,purchase_company=capture)
        self.assertEqual(len(projected),1);end=projected[0]
        self.assertGreater(end.finished[0],0)
        self.assertEqual(end.finished[0],w.t2Fin[0]);self.assertEqual(end.cash,w.t2Cash[0])
        self.assertEqual(end.finished_basis[0],w.t2FinBasis[0])
        for m,q in enumerate(end.held):self.assertEqual(q,(w.t2Raw if m<M.NE else w.t2T1Raw)[m])

    def test_fractional_and_overcap_records_are_never_rounded_or_expanded(self):
        cfg,w,phase=self.fixture();w.t2Raw[0]=.5
        record=capture_t2(w,cfg,1,0,phase,InputMarket(w,1),K.production_line_overhead(w,cfg,'t2'))
        self.assertEqual(project(record).state.held[0],.5)
        record['materials'][0]['held']=0
        record['lines'][0]['finished']=int(record['outputSlotSpace']/phase)+1
        projected=project(record)
        self.assertGreater(projected.state.finished[0],projected.company.finished_caps[0])

    def test_receipt_mismatch_rejects(self):
        cfg,w,phase=self.fixture()
        r=capture_t2(w,cfg,1,0,phase,InputMarket(w,1),K.production_line_overhead(w,cfg,'t2'))
        r['pendingSellerCash']=1
        with self.assertRaisesRegex(ValueError,'receipts'):project(r)

    def test_multiple_lines_keep_all_materials_and_actual_execution_order(self):
        from economy.core.state import add_tier2_line
        cfg,w,phase=self.fixture()
        native=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
        other=next(p for p in M.T2_PRODUCTS if p['invented'] and p['sectorIndex']==native['sectorIndex'] and p['complexity']<=phase and p['id']!=native['id'])
        add_tier2_line(w,cfg,0,other,paid=False)
        r=capture_t2(w,cfg,1,0,phase,InputMarket(w,1),K.production_line_overhead(w,cfg,'t2'))
        p=project(r)
        self.assertEqual(len(p.company.lines),2)
        self.assertEqual(len(p.state.held),M.NI)
        self.assertEqual(p.purchase.active_lines,tuple(i for i,x in enumerate(r['lines']) if x['complexity']==phase))
        self.assertEqual(p.state.completed_phases,tuple(f'tick-1-C{cx}-purchase' for cx in sorted({x['complexity'] for x in r['lines'] if x['complexity']<phase})))
