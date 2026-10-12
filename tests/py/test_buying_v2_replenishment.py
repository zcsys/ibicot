import itertools
import unittest
import numpy as np
from tools.buying_v2.industry_oracle import Offer
from tools.buying_v2.replenishment import solve


def oracle(targets,offers,incumbents,bids,fees,cash,lot,spaces=(1.,2.),room=100.,demands=None):
    best=(0,0.,tuple(0 for o in offers))
    for q in itertools.product(*(range(0,min(o.stock,targets[o.material])+1,lot) for o in offers)):
        if demands is not None:
            bought=[0]*len(targets)
            valid=True
            for i in sorted(range(len(offers)),key=lambda i:(offers[i].material,offers[i].price,offers[i].supplier)):
                m=offers[i].material
                if q[i]>max(0,demands[i]-bought[m]):
                    valid=False
                bought[m]+=q[i]
            if not valid:
                continue
        totals=[sum(x for o,x in zip(offers,q) if o.material==m) for m in range(len(targets))]
        if any(x>t for x,t in zip(totals,targets)):
            continue
        charge=0.
        for m in range(len(targets)):
            stock=next((o.stock for o in offers if o.material==m and o.supplier==incumbents[m]),0)
            outside=any(x>0 and o.material==m and o.supplier!=incumbents[m] for o,x in zip(offers,q))
            if incumbents[m]>=0 and bids[m]>0 and stock>=bids[m] and outside:
                charge+=fees[m]
        payment=sum(o.price*x for o,x in zip(offers,q))+charge
        if payment>cash or sum(x*spaces[o.material] for o,x in zip(offers,q))>room:
            continue
        key=(-sum(q),payment,q)
        if key<best:
            best=key
    return tuple(best[2]),-best[0],best[1]


class ReplenishmentTests(unittest.TestCase):
    def test_random_uniform_lot_cases_against_full_enumeration(self):
        rng=np.random.default_rng(301947)
        for _ in range(600):
            lot=int(rng.integers(1,3))
            targets=(int(rng.integers(0,5)),int(rng.integers(0,5)))
            offers=tuple(Offer(m,s,float(rng.integers(1,10)),int(rng.integers(0,5)),lot) for m in range(2) for s in range(2))
            inc=(int(rng.integers(-1,2)),int(rng.integers(-1,2)))
            bids=(int(rng.integers(0,5)),int(rng.integers(0,5)))
            fees=(float(rng.integers(0,8)),float(rng.integers(0,8)))
            cash=float(rng.integers(0,60))
            room=float(rng.integers(0,12))
            demands=tuple(min(targets[o.material], max(0,5-int(o.price)//2)) for o in offers) if rng.random()<.5 else None
            expected=oracle(targets,offers,inc,bids,fees,cash,lot,room=room,demands=demands)
            actual=solve(targets,offers,inc,bids,fees,cash,(1.,2.),room,lot,funded_demands=demands)
            self.assertEqual(tuple(actual[0]),expected[0])
            self.assertEqual(actual[1],expected[1])
            self.assertEqual(actual[2],expected[2])

    def test_arbitrary_funded_caps_against_exhaustive_allocations(self):
        rng=np.random.default_rng(98273)
        for _ in range(1000):
            offers=tuple(Offer(m,s,float(rng.integers(1,5)),int(rng.integers(0,5))) for m in range(2) for s in range(2))
            demands=tuple(int(rng.integers(0,5)) for o in offers)
            cash=float(rng.integers(0,30))
            expected=oracle((4,4),offers,(-1,-1),(0,0),(0.,0.),cash,1,room=100.,demands=demands)
            actual=solve((4,4),offers,(-1,-1),(0,0),(0.,0.),cash,(1.,2.),100.,funded_demands=demands)
            self.assertEqual(tuple(actual[0]),expected[0])
            self.assertEqual(actual[1],expected[1])
            self.assertEqual(actual[2],expected[2])

    def test_cheap_partial_does_not_lose_to_full_supplier(self):
        result=solve((8,),(Offer(0,0,10.,2),Offer(0,1,15.,20)),(-1,),(0,),(0.,),1000.,(1.,),8.)
        self.assertEqual(tuple(result[0]),(2,6))
        self.assertEqual(result[2],110.)

    def test_binding_space_uses_exact_fallback(self):
        result=solve((8,),(Offer(0,0,10.,8),),(-1,),(0,),(0.,),1000.,(2.,),8.)
        self.assertEqual(tuple(result[0]),(4,))


if __name__ == '__main__':
    unittest.main()
