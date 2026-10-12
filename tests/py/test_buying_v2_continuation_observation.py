import unittest
from dataclasses import replace
import test_buying_v2_continuation_resident as fixtures
from test_buying_v2_information_history import fixture,scenario
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_observation import decode
from tools.buying_v2.continuation_information import FIELDS,History
from tools.buying_v2.phase_ledger import Purchase,OpenBook,SharedSettleBook,apply


class ObservationTests(unittest.TestCase):
    def test_all_event_observations_equal_independent_reference_fields(self):
        c,s,paths=fixtures.ResidentTests().fixture();p=compile_calendar(c,s,paths)
        for scenario_id,path in enumerate(paths):
            r=Resident(c,s,p);a={i:(2,0,2,0) for i,e in enumerate(path.events) if isinstance(e,Purchase)}
            r.run(scenario_id,a,observe=True);state=s;history=History();expected=[]
            for i,event in enumerate(path.events):
                state,d=apply(c,state,event,a.get(i))
                if isinstance(event,Purchase):
                    order=sorted(range(len(event.offers)),key=lambda j:(event.offers[j].material,event.offers[j].supplier))
                    d.update(allocation=a[i],fundedDemands=event.funded_demands,
                        observedPurchase=(tuple((event.offers[j].material,event.offers[j].supplier,event.offers[j].price,event.offers[j].stock,event.offers[j].lot) for j in order),
                        tuple(event.reliability[j] for j in order),event.fee_unit_cost,event.fee_multiple,event.active_lines,event.rent_bill,event.rent_threshold,event.overhead_timing))
                projection={k:v for k,v in d.items() if k in FIELDS or k in ('event','label')}
                self.assertEqual(decode(r.observations[i],r.labels),projection)
                expected.append(projection)
            self.assertEqual(history.trace(expected),history.trace(tuple(decode(x,r.labels) for x in r.observations)))
            self.assertEqual(r.snapshot(),state)
            quiet=Resident(c,s,p);quiet.run(scenario_id,a)
            self.assertEqual(quiet.observations,());self.assertEqual(quiet.snapshot(),state)

    def test_hidden_demand_is_absent_from_numeric_records(self):
        c,s,b=fixture();s=replace(s,finished=(0,),finished_basis=(0.,))
        paths=tuple(scenario((OpenBook('empty'),SharedSettleBook('empty',(q,),groups=((0,),)),b)) for q in (0,99))
        p=compile_calendar(c,s,paths);records=[]
        for j in range(2):
            r=Resident(c,s,p);r.run(j,{},stop=2,observe=True);records.append(r.observations)
        for a,b in zip(*records):
            for x,y in zip(a,b):self.assertTrue((x==y).all())

    def test_segment_fork_and_failure_observations_are_atomic(self):
        c,s,paths=fixtures.ResidentTests().fixture();p=compile_calendar(c,s,paths);r=Resident(c,s,p)
        r.run(0,{0:(2,0,2,0)},stop=2,observe=True);child=r.fork()
        before=tuple(decode(x,r.labels) for x in r.observations)
        with self.assertRaises(ValueError):r.run(0,{4:(100,0,0,0)},start=2,stop=5,observe=True)
        self.assertEqual(tuple(decode(x,r.labels) for x in r.observations),before)
        child.run(0,{},start=2,stop=3,observe=True)
        self.assertEqual(len(child.observations),3);self.assertEqual(len(r.observations),2)
        import numpy as np
        for a,b in zip(r.observations,child.observations):
            for x,y in zip(a,b):self.assertFalse(np.shares_memory(x,y))


if __name__=='__main__':unittest.main()
