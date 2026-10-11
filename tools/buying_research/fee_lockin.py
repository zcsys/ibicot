"""A controlled repeated split-fill counterexample, not a full-world equilibrium."""
import argparse
import json
from pathlib import Path
import numpy as np
from economy.core.rng import random_
from .solvers import retail,demand_quantity,marginal_values
from .oracle import retail_oracle


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prices=np.array([30.,1.,1.]);incumbent_stock=2;preference=0;records=[]
    for tick in range(1,11):
        u=random_(137,tick,7000000);values=marginal_values(20.,10.,2.,u)
        bid=demand_quantity(20.,10.,2.,prices[preference],u)
        stock=np.array([incumbent_stock,1,1],dtype=float)
        args=(values,prices,stock,preference,bid,2.,1e100)
        actual=retail(*args);oracle=retail_oracle(*args)
        np.testing.assert_array_equal(actual[0],oracle[0]);np.testing.assert_allclose(actual[1:4],oracle[1:4],rtol=1e-12,atol=1e-9)
        assert bid==2 and actual[4]==0 and actual[3]==2
        np.testing.assert_array_equal(actual[0],[0,1,1])
        incumbent_stock-=int(actual[0][0]);preference=int(actual[4])
        records.append(dict(tick=tick,roundingDraw=u,canonicalBid=bid,stock=stock.tolist(),
            allocation=actual[0].tolist(),goods=actual[2],fee=actual[3],preference=preference,objective=actual[1]))
    result=dict(status='counterexample verified by independent allocation oracle',seed=137,
        fixture=dict(latent=20,halfPrice=10,eta=2,quotes=prices.tolist(),fixedFee=2,initialIncumbentStock=2,
            alternativeReplenishment='Each cheaper seller offers one freshly replenished unit per order; quotes and fee held fixed.'),
        orders=records,totalIncumbentGoodsSold=sum(r['allocation'][0] for r in records),
        totalIncumbentFees=sum(r['fee'] for r in records),finalIncumbentStock=incumbent_stock,
        interpretation='Both cheaper suppliers jointly fill the whole two-unit canonical bid, but neither individually qualifies. Split fills retain the old incumbent, which earns a fee without selling goods. The same state can repeat under the stated fixed offers. This falsifies a universal no-lock-in/no-fee-farming claim for this split-order protocol; it does not establish prevalence or strategic profitability in the adaptive full world.',
        remainingDecision='Any remedy must state its change to order boundaries, split qualification, fee eligibility, or preference rules and be evaluated separately against the confirmed loyalty requirements.')
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='orders'}))


if __name__=='__main__':main()
