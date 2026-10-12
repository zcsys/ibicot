from dataclasses import replace
import unittest
from test_buying_v2_phase_ledger import company,state,buy
from tools.buying_v2.phase_ledger import apply,OpenBook,SettleBook,horizon_value
from tools.buying_v2.quantity_value import LinearQuantityValue,value_at
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.phase_oracle import Scenario


class NativeLedgerTests(unittest.TestCase):
    def test_fractional_slots_and_holdings_keep_whole_purchases(self):
        c=replace(company(),slots=(1.5,));s=state(held=(.5,),basis=(2.,))
        e=buy(offers=(Offer(0,1,3.,2),),demands=(2,),active=())
        end,d=apply(c,s,e,(1,))
        self.assertEqual(end.held,(1.5,));self.assertEqual(end.basis,(4/1.5,))
        self.assertEqual(end.cash,7.)
        with self.assertRaisesRegex(ValueError,'infeasible'):apply(c,s,e,(2,))

    def test_native_subtraction_basis_and_whole_sales_preserve_residue(self):
        c=company();s=state(cash=10.,held=(3.1,),basis=(.2,),finished=(.5,),finished_basis=(1.,))
        end,d=apply(c,s,buy(offers=(),demands=()),())
        self.assertEqual(d['outputs'],(3,));self.assertEqual(end.held,(3.1-3,))
        opened,_=apply(c,end,OpenBook('sales'))
        sold,d=apply(c,opened,SettleBook('sales',(10,)))
        self.assertEqual(d['sold'],(3,));self.assertEqual(sold.finished,(.5,))
        native=LinearQuantityValue((0.,1.),(0.,2.))
        self.assertEqual(value_at(native,.5),1.)
        value=horizon_value(s,sold,(native,),(native,))
        self.assertAlmostEqual(value,sold.cash-s.cash+2*(sold.held[0]+sold.finished[0]))
        with self.assertRaisesRegex(ValueError,'fractional'):horizon_value(s,sold,((0.,0.),),((0.,0.),))

    def test_declared_value_domain_has_no_extrapolation(self):
        table=LinearQuantityValue((0.,.5,2.),(0.,3.,4.))
        self.assertEqual(table.at(.5),3.)
        with self.assertRaises(ValueError):table.at(2.1)
        with self.assertRaises(ValueError):LinearQuantityValue((1.,1.),(0.,2.))

    def test_compiler_preserves_fractional_state_before_terminal_lookup(self):
        c=company();s=state(held=(.5,))
        path=Scenario(1.,(),((0.,)*21,),((0.,)*11,))
        self.assertEqual(compile_calendar(c,s,(path,)).version,4)
        from tools.buying_v2.continuation_search import solve
        with self.assertRaises(ValueError):solve(c,s,(path,),funding='continuation')

    def test_native_ledger_matches_verified_native_production_primitive(self):
        from tools.buying_v2.native_inventory import checked_produce
        for fraction in (.1,.5,.999999999):
            c=company();s=state(cash=20.,held=(3+fraction,),basis=(.17,),finished=(fraction,),finished_basis=(.23,))
            end,d=apply(c,s,buy(offers=(),demands=()),())
            expected=checked_produce(s.held,s.basis,[0],[1],cash=s.cash,finished=s.finished[0],
                finished_basis=s.finished_basis[0],output_qty=1,capacity=5,finished_slot=10,
                conversion=.5,quote=3.,overhead=0.,margin_band=.05)
            self.assertEqual(end.held,tuple(expected[0]))
            self.assertEqual(end.cash,expected[1]);self.assertEqual(end.finished,(expected[2],))
            self.assertEqual(end.finished_basis,(expected[3],));self.assertEqual(d['outputs'],(expected[4],))
            self.assertEqual(end.basis,s.basis)

    def test_integer_only_optimizations_cannot_drop_fractional_resources(self):
        import math
        from tools.buying_v2.continuation_bound import upper_value
        from tools.buying_v2.closing_allocation import prepare
        c=company();s=state(held=(.5,));e=buy()
        self.assertEqual(upper_value(c,s,s,(),((0.,)*21,),((0.,)*11,)),math.inf)
        self.assertIsNone(prepare(c,s,s,e,()))
