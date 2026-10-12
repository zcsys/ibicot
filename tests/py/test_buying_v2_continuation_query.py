import unittest
from dataclasses import replace
from itertools import product
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_ledger import apply,Purchase
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.continuation_resident import Resident
from tools.buying_v2.continuation_query import prepare
from tools.buying_v2.continuation_observation import decode
from test_buying_v2_persistent_supply import fixture


class QueryTests(unittest.TestCase):
    def test_query_selection_and_execution_match_independent_construction(self):
        c,s,paths=case(1,2,1,1,lines=2);s=replace(s,incumbents=(0,0))
        e=replace(paths[0].events[0],fee_multiple=3.,reliability=(.1,.2,.3,.4))
        path=replace(paths[0],events=(e,));p=compile_calendar(c,s,(path,));r=Resident(c,s,p)
        for offer in (None,0,1,2,3):
            indices=tuple(i for i,o in enumerate(e.offers) if offer is None or o.material!=e.offers[offer].material or i==offer)
            offers=tuple(replace(e.offers[i],stock=max(0,c.slots[e.offers[i].material]-s.held[e.offers[i].material])//e.offers[i].lot*e.offers[i].lot) for i in indices)
            hypothetical=replace(e,offers=offers,reliability=tuple(e.reliability[i] for i in indices),fee_multiple=0.,funded_demands=tuple(o.stock for o in offers))
            iv,fv,selected=prepare(r,0,0,offer);self.assertEqual(tuple(selected),indices)
            self.assertEqual(tuple(iv[6:4+4*len(offers):4]),tuple(o.stock for o in offers))
            for allocation in product(*(range(o.stock+1) for o in offers)):
                child=r.fork()
                try:expected,detail=apply(c,s,hypothetical,allocation)
                except ValueError:
                    with self.assertRaises(ValueError):child.funding_purchase(0,0,allocation,offer=offer)
                    continue
                expected=replace(expected,incumbents=s.incumbents)
                child.funding_purchase(0,0,allocation,offer=offer)
                self.assertEqual(child.snapshot(),expected)
                observed=decode(child.observations[-1],child.labels)
                self.assertEqual(observed['preferences'],s.incumbents);self.assertEqual(observed['fees'],(0.,0.))
            self.assertEqual(r.snapshot(),s)

    def test_phantom_stock_does_not_consume_real_future_arrival(self):
        for opening in (0,1):
            c,s,path=fixture(1);events=list(path.events)
            events[0]=replace(events[0],offers=(replace(events[0].offers[0],stock=opening),))
            events=tuple(replace(e,funded_demands=(1,)) if isinstance(e,Purchase) else e for e in events)
            path=replace(path,events=events);p=compile_calendar(c,s,(path,));r=Resident(c,s,p,supply='persistent-arrivals')
            r.funding_purchase(0,0,(1,))
            next_offset=int(p.integer_offsets[4]);self.assertEqual(r.integers[next_offset+6],1-opening)
            self.assertEqual(r.snapshot().incumbents,(-1,))
            r.run(0,{4:(1-opening,)},start=1,observe=True)
            self.assertEqual(r.snapshot().accounts.goods_paid,2-opening)
            self.assertEqual(p.integers[next_offset+6],1)

    def test_invalid_queries_and_atomic_failure(self):
        c,s,paths=case(1,2,1,1);r=Resident(c,s,compile_calendar(c,s,paths))
        for offer in (-1,True,4):
            with self.assertRaises(ValueError):prepare(r,0,0,offer)
        with self.assertRaises(ValueError):prepare(r,0,1)
        with self.assertRaises(ValueError):r.funding_purchase(0,0,(100,)*4)
        self.assertEqual(r.snapshot(),s);self.assertEqual(r.observations,())


if __name__=='__main__':unittest.main()
