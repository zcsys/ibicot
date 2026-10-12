from dataclasses import replace
import unittest
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.phase_ledger import OpenBook,SettleBook,SharedSettleBook,apply
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_information import History,group_decisions


class InformationTests(unittest.TestCase):
    def groups(self,c,s,paths,index):
        p=compile_calendar(c,s,paths);history=History();residents=[];ids=[]
        for j,path in enumerate(paths):
            r=Resident(c,s,p);r.run(j,{},stop=index);residents.append(r)
            state=s;trace=[]
            for event in path.events[:index]:
                state,detail=apply(c,state,event);trace.append(detail)
            self.assertEqual(r.snapshot(),state)
            ids.append(history.trace(trace))
        return group_decisions(residents,list(range(len(paths))),index,ids,history)

    def test_timing_signal_survives_converged_balances(self):
        c,s,b=fixture()
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(early,)),
            OpenBook('later'),SettleBook('later',(1-early,)),b)) for early in (0,1))
        self.assertEqual(self.groups(c,s,paths,4),(0,1))

    def test_hidden_unmet_demand_not_an_observation(self):
        c,s,b=fixture();s=replace(s,finished=(0,),finished_basis=(0.,))
        for shared in (False,True):
            paths=tuple(scenario((OpenBook('empty'),
                SharedSettleBook('empty',(d,),groups=((0,),)) if shared else SettleBook('empty',(d,)),b)) for d in (0,8))
            self.assertEqual(self.groups(c,s,paths,2),(0,0))

    def test_offer_order_funding_hidden_future_and_neutral_fee(self):
        from tools.buying_v2.industry_oracle import Offer
        c,s,b=fixture();b=replace(b,offers=(Offer(0,1,1.,1),Offer(0,2,2.,1)),reliability=(.1,.2))
        alternate=replace(b,offers=b.offers[::-1],reliability=b.reliability[::-1],funded_demands=(1,1))
        paths=(scenario((b,)),replace(scenario((alternate,)),finished_values=((0.,99.,500.),)))
        p=compile_calendar(c,s,paths);h=History();r=[Resident(c,s,p) for _ in paths]
        self.assertEqual(group_decisions(r,[0,1],0,[0,0],h),(0,0))
        changed=replace(paths[1],events=(replace(alternate,fee_multiple=3.),))
        p=compile_calendar(c,s,(paths[0],changed));r=[Resident(c,s,p) for _ in paths]
        self.assertEqual(group_decisions(r,[0,1],0,[0,0],h),(0,1))
        self.assertEqual(group_decisions(r,[0,1],0,[0,0],h,neutral=True),(0,0))

    def test_history_filters_unobserved_fields_but_remembers_inspection(self):
        h=History();a=dict(event='SharedSettleBook',label='book',cash=10.,sold=(0,),quoteDemands=(1,))
        self.assertEqual(h.trace((a,)),h.trace(({**a,'quoteDemands':(100,)},)))
        b=dict(event='Purchase',label='buy',cash=10.,observedPurchase=((1,2.,0),),allocation=(0,))
        self.assertNotEqual(h.trace((b,)),h.trace(({**b,'observedPurchase':((1,3.,0),)},)))
        self.assertNotEqual(h.trace((a,b)),h.trace((b,a)))

    def test_complete_state_and_live_buffer_semantics(self):
        c,s,b=fixture();p=compile_calendar(c,s,(scenario((b,)),scenario((b,))))
        a=Resident(c,s,p);other=a.fork();h=History()
        other.data[8][:]=123;other.data[12][:]=123
        self.assertEqual(group_decisions([a,other],[0,1],0,[0,0],h),(0,0))
        other.data[0][5]=1.
        self.assertEqual(group_decisions([a,other],[0,1],0,[0,0],h),(0,1))
        with self.assertRaises(ValueError):group_decisions([a],[0],0,[1],h)
        with self.assertRaises(ValueError):group_decisions([a],[0],1,[0],h)
        with self.assertRaises(ValueError):h.append(123,dict(event='x',label='x'))


if __name__=='__main__':unittest.main()
