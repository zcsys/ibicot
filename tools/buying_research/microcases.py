"""Reproducible worked examples and structural counterexamples (not calibration)."""
import argparse
import itertools
import json
import math
from pathlib import Path
import numpy as np
from .solvers import industry,canonical_industry,retail
from .oracle import industry_oracle,retail_oracle,multi_route_oracle


def retail_case(values,prices,stock,pref,bid,fee,cash=1e9):
    args=(np.array(values,float),np.array(prices,float),np.array(stock,float),pref,bid,float(fee),float(cash))
    a=retail(*args);b=retail_oracle(*args)
    np.testing.assert_array_equal(a[0],b[0]);np.testing.assert_allclose(a[1:4],b[1:4],rtol=1e-12,atol=1e-9)
    return dict(values=values,prices=prices,stock=stock,incumbent=pref,canonicalBid=bid,payableFee=fee,cash=cash,
        allocation=a[0].tolist(),objective=a[1],goods=a[2],fee=a[3],newPreference=int(a[4]))


def industrial_case(held,ratios,lots,spaces,slots,room,prices,stocks,prefs,fees,bound,finished,price,mean,conversion,cash):
    arrays=[np.array(x,float) for x in (held,ratios,lots,spaces,slots,prices,stocks)]
    h,r,l,s,sl,p,st=arrays;counts=np.full(len(h),p.shape[1],dtype=np.int64);pf=np.array(prefs,dtype=np.int64);f=np.array(fees,float)
    canonical=np.array([p[k,pf[k]] if pf[k]>=0 else np.median(p[k]) for k in range(len(h))])
    bids,y=canonical_industry(h,r,l,s,sl,room,canonical,bound,finished,price,mean,conversion)
    args=(h,r,l,s,sl,float(room),p,st,counts,pf,f,bids,bound,float(finished),float(price),float(mean),float(conversion),float(cash),float(conversion))
    a=industry(*args);b=industry_oracle(*args)
    np.testing.assert_array_equal(a[0],b[0]);np.testing.assert_array_equal(a[1],b[1])
    np.testing.assert_allclose(a[4],b[4],rtol=1e-12,atol=1e-9)
    return dict(held=held,ratios=ratios,lots=lots,spaces=spaces,slots=slots,room=room,prices=prices,stocks=stocks,
        incumbent=prefs,fees=fees,bound=bound,finished=finished,outputPrice=price,horizonMean=mean,conversion=conversion,cash=cash,
        canonicalBid=bids.tolist(),canonicalOutput=y,supplier=a[0].tolist(),quantity=a[1].tolist(),chargedFees=a[2].tolist(),
        plannedOutput=a[3],objective=a[4],goodsAndFees=a[5],conversionReserved=a[3]*conversion)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    examples={}
    for full,available in itertools.product((False,True),repeat=2):
        examples[f'fee_full_{full}_inc_available_{available}']=retail_case([20,15],[11,1],[2 if available else 1,2 if full else 1],0,2,2)
    examples['expensive_fallback']=retail_case([12,8,4],[1,10],[1,5],-1,3,0)
    examples['fee_exceeds_savings']=retail_case([10],[8,7],[1,1],0,1,3)
    examples['cash_covers_goods_not_fee']=retail_case([10],[8,7],[1,1],0,1,3,7)
    examples['refinery_wholesale']=industrial_case([100],[1],[1000],[1],[6100],6000,[[1.25,1.1]],[[6000,6000]],[0],[50],6000,0,3,6000,.25,20000)
    examples['manufacturer_complements_partial']=industrial_case([10,0],[1,1],[1,1],[1,2],[30,30],90,
        [[1.5,1.],[2.,2.]],[[100,2],[100,100]],[0,0],[.2,0],24,0,8,20,.5,60)
    examples['manufacturer_repeated_input']=industrial_case([3],[2],[1],[2],[60],120,[[2.,3.]],[[100,100]],[0],[0],72,5,12,30,1,50)
    examples['multiple_routes']=dict(result=multi_route_oracle([0,0],[[1,1],[2,0]],[2,2],[[0,8,12],[0,7,9]],
        [[(1,3,0,0)],[(2,2,0,1)]],[1,1],[1,1],[3,2],5,8,[1,1]),
        explanation='Outputs (1,1) share ingredient 0; independent full-output decisions violate its three-unit availability.')
    # An independent two-period finite problem: a useful buffer cannot be
    # represented by a complete-kit-only current supplier-stock action space.
    choices=[]
    for a_now,b_later in itertools.product((0,1),repeat=2):
        sale=min(a_now,b_later);profit=10*sale-a_now-b_later
        choices.append(dict(aNow=a_now,bLater=b_later,output=sale,profit=profit))
    examples['unmatched_buffer_counterexample']=dict(period1={'A':dict(price=1,stock=1),'B':dict(price=1,stock=0)},
        period2={'A':dict(price=1,stock=0),'B':dict(price=1,stock=1)},recipe='A+B',salePrice=10,
        exhaustiveChoices=choices,optimum=max(choices,key=lambda x:x['profit']),completeKitPolicyProfit=0,
        interpretation='With known complementary arrival, holding unmatched A is worth eight dollars. R1 intentionally excludes this action and loses that option value.')
    examples['identification']=dict(observation=dict(price=10,quantity=5,eta=2),
        compatibleCurves=[dict(L=L,halfPrice=10/math.sqrt(L/5-1)) for L in (10,20,40)],
        interpretation='One observed point fits infinitely many bounded demand curves even with fixed elasticity.')
    examples['share_assumptions']=dict(capacities=[1,3],productRequested=40,equalForecasts=[20,20],capacityForecasts=[10,30],
        interpretation='Neither forecast allocates customers. They coincide only with identical capacity per installed product line, as in the current single-route world.')
    examples['bid_inflation_discontinuity']=dict(stock=2,fee=4,
        bid2=retail_case([20,15],[11,1],[2,1],0,2,4),bid3=retail_case([20,15],[11,1],[2,1],0,3,4),
        interpretation='Changing only canonical bid from two to three waives the fee. R1 prevents arbitrary buyer submissions but is not strategy-proof against genuine changes to valuation/canonical quotes.')
    with a.output.open('x') as f:json.dump(examples,f,indent=2)
    print(json.dumps({k:v for k,v in examples.items() if k.startswith(('refinery','manufacturer'))},indent=2))


if __name__=='__main__':main()
