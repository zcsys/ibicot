"""Show that canonical-bid qualification differs from filling a cheap-quote plan."""
import argparse
import json
from pathlib import Path
import numpy as np
from .solvers import demand_quantity,marginal_values,retail
from .oracle import retail_oracle


def example():
    latent,half,eta,u=20.,10.,2.,.5
    prices=np.array([30.,1.]);stock=np.array([20.,3.]);pref=0;fee=2.
    bid=demand_quantity(latent,half,eta,prices[pref],u)
    values=marginal_values(latent,half,eta,u)
    intended=retail(values,prices,np.full(2,1e15),pref,bid,fee,1e100)
    actual=retail(values,prices,stock,pref,bid,fee,1e100)
    reference=retail_oracle(values,prices,stock,pref,bid,fee,1e100)
    np.testing.assert_array_equal(actual[0],reference[0])
    np.testing.assert_allclose(actual[1:4],reference[1:4],atol=1e-9,rtol=1e-12)
    assert actual[4]==reference[4]==1
    assert bid==2 and int(intended[0].sum())==20 and actual[0].tolist()==[0,3]
    return dict(status='verified',latent=latent,halfPrice=half,elasticity=eta,roundingDraw=u,
        quotes=prices.tolist(),openingStocks=stock.tolist(),incumbent=pref,fixedFee=fee,
        canonicalBid=int(bid),unlimitedStockIntention=int(intended[0].sum()),
        actualAllocation=actual[0].tolist(),feePaid=float(actual[3]),newPreference=int(actual[4]),
        intendedQuantityFulfillment=float(actual[0].sum()/intended[0].sum()),
        interpretation='The challenger fills the frozen canonical bid and therefore replaces the incumbent, despite filling only 15% of the quote-stage intended quantity. R1 defines whole bid using the former. This exposes a substantive contract choice, not oracle disagreement. Requiring full cheap-quote intention would be a different protocol.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=example()
    with a.output.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
    print(json.dumps(data))


if __name__=='__main__':main()
