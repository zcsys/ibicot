"""Seeded independent-oracle coverage of the connected continuation search."""
from dataclasses import replace
import random
import unittest
import test_buying_v2_continuation_search as verification
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_ledger import Purchase,Rent,EndTick


def cases():
    rng=random.Random(84371)
    for number in range(24):
        lines=1+number%2;c,s,paths=case(1,2,2,2,lines=lines)
        c=replace(c,spaces=(.5,1.5),fixed_assets=rng.choice((0.,5.)),
            lines=tuple(replace(line,conversion=rng.choice((0.,.1,.5)),output_space=1.5) for line in c.lines))
        s=replace(s,cash=rng.choice((0.,.7,3.,20.)),held=(rng.randrange(2),rng.randrange(2)),
            basis=(rng.choice((.1,.3,2.)),rng.choice((.2,1.))),
            quotes=tuple(rng.choice((1.,3.,10.)) for _ in range(lines)),
            incumbents=(rng.choice((-1,0,1)),rng.choice((-1,0,1))),
            arrears=rng.choice((0.,.3)),switching_net_ema=rng.choice((-.2,0.,.5)))
        price=tuple(rng.choice((.1,.3,1.,4.)) for _ in range(4))
        lots=tuple(rng.choice((1,2)) for _ in range(4))
        opening=tuple(rng.randrange(3) for _ in range(4))
        multiple=rng.choice((0.,.5,2.));bill=rng.choice((0.,.3,2.));threshold=rng.choice((0.,5.,100.))
        edited=[]
        for outcome,path in enumerate(paths):
            events=[];period=0
            for event in path.events:
                if isinstance(event,Purchase):
                    offers=tuple(replace(o,price=price[i],lot=lots[i],stock=opening[i]+period*outcome) for i,o in enumerate(event.offers))
                    event=replace(event,offers=offers,reliability=(0.,.3,1.,-.2),fee_unit_cost=.2,fee_multiple=multiple,
                        rent_bill=bill,rent_threshold=threshold,overhead_timing='before' if number%2 else 'after')
                    period+=1
                events.append(event)
            events.extend((Rent('billing',bill,threshold),EndTick('closing',.15)))
            edited.append(replace(path,probability=(.25,.75)[outcome],events=tuple(events),
                input_values=tuple(tuple(q*.1 for q in range(len(table))) for table in path.input_values),
                finished_values=tuple(tuple(q*.2 for q in range(len(table))) for table in path.finished_values)))
        yield number,c,s,tuple(edited),'persistent-arrivals' if number%3 else 'independent-snapshots'


class DifferentialTests(unittest.TestCase):
    def test_seeded_complete_policies_funding_observations_and_accounts(self):
        for number,c,s,paths,supply in cases():
            with self.subTest(case=number,supply=supply):
                verification.SearchTests().compare(c,s,paths,supply=supply,funding='continuation')


if __name__=='__main__':unittest.main()
