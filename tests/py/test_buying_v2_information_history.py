import unittest
from dataclasses import replace
from tools.buying_v2.industry_oracle import Line,Offer
from tools.buying_v2.phase_ledger import Company,State,Purchase,OpenBook,SettleBook,SharedSettleBook
from tools.buying_v2.phase_oracle import Scenario,solve


def fixture():
    c=Company((1.,),(1,),4.,(Line((1,),1,.25,2.,0.,(0.,0.),1.),),(2,),0.)
    s=State(10.,(0,),(0.,),(1,),(.5,),(2.,),(-1,))
    b=Purchase('buy',(Offer(0,1,1.,1),),(),(0.,),1.,0.,(0,),0.)
    return c,s,b


def scenario(events):return Scenario(.5,events,((0.,0.),),((0.,)*3,))
def fixed(c,s,e):return (1,)*len(e.offers)


class InformationHistoryTests(unittest.TestCase):
    def test_remembers_observed_sales_timing_after_balances_converge(self):
        c,s,b=fixture()
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(early,)),
            OpenBook('later'),SettleBook('later',(1-early,)),b,
            OpenBook('final'),SettleBook('final',(early,)))) for early in (0,1))
        for funding in (fixed,'continuation','continuation-transfer-neutral'):
            r=solve(c,s,paths,funding=funding)
            self.assertEqual(r['expectedValue'],2.375)
            self.assertEqual([x['trace'][4]['allocation'] for x in r['leaves']],[(0,),(1,)])
            # Both paths observed exactly $2 before purchasing; the remembered
            # timing signal, not greater current wealth, supports the difference.
            self.assertEqual([x['trace'][3]['cash'] for x in r['leaves']],[12.,12.])

    def test_remembers_inspected_quote_without_a_transaction(self):
        c,s,b=fixture();s=replace(s,finished=(0,),finished_basis=(0.,))
        paths=[]
        for high in (0,1):
            earlier=replace(b,label='inspect',offers=(Offer(0,1,1.+high,0),),active_lines=())
            paths.append(scenario((earlier,b,OpenBook('final'),SettleBook('final',(high,)))))
        for funding in (fixed,'continuation'):
            r=solve(c,s,tuple(paths),funding=funding)
            self.assertEqual(r['expectedValue'],.375)
            self.assertEqual([x['trace'][1]['allocation'] for x in r['leaves']],[(0,),(1,)])

    def test_hidden_unfulfilled_demand_does_not_become_a_memory_signal(self):
        c,s,b=fixture();s=replace(s,finished=(0,),finished_basis=(0.,))
        for shared in (False,True):
            paths=[]
            for high in (0,1):
                first=(SharedSettleBook('empty',(high,),groups=((0,),)) if shared else SettleBook('empty',(high,)))
                paths.append(scenario((OpenBook('empty'),first,b,OpenBook('final'),SettleBook('final',(high,)))))
            for funding in (fixed,'continuation'):
                r=solve(c,s,tuple(paths),funding=funding)
                self.assertEqual(r['expectedValue'],0.)
                self.assertEqual([x['trace'][2]['allocation'] for x in r['leaves']],[(0,),(0,)])


if __name__=='__main__':unittest.main()
