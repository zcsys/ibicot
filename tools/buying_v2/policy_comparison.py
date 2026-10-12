"""Independent small-company comparison of procurement objectives.

Batch-first means actual output items under the retained ordered production
and accounting gate, then input-target units, then lower cash payment. It does
not mean profit maximization. Fixture revenue tables are explicit assumptions.
"""
import argparse
from dataclasses import asdict, replace
from itertools import product
import json
import math
from pathlib import Path
from .industry_oracle import Problem,Offer,Line,evaluate,solve,validate
from .funding import replenishment_plan


def batch_first(p,max_allocations=1000000):
    validate(p)
    ranges=[range(0,min(o.stock,p.slots[o.material]-p.held[o.material])+1,o.lot) for o in p.offers]
    count=math.prod(len(r) for r in ranges)
    if count>max_allocations:
        raise ValueError('batch-first exhaustive allocation limit')
    best=None;best_key=None
    for q in product(*ranges):
        result=evaluate(p,q)
        if result is None:
            continue
        key=(-sum(result['outputs']),-sum(q),result['goods']+sum(result['fees']),q)
        if best_key is None or key<best_key:
            best,best_key=result,key
    if best is None:
        raise ValueError('no feasible batch-first plan')
    return best


def fund_policy(p,solver):
    """Each objective funds its own joint hypothetical plan. Reusing the unit-
    first bid can suppress complements before a batch-first solver sees them.
    """
    n=len(p.held);refs=[]
    for m in range(n):
        offers=[o for o in p.offers if o.material==m]
        refs.append(next((o for o in offers if o.supplier==p.incumbents[m]),
                         min(offers,key=lambda o:(o.price,o.supplier),default=None)))
    def hypothetical(material=-1,replacement=None):
        chosen=[replacement if m==material else o for m,o in enumerate(refs)]
        offers=tuple(Offer(m,o.supplier,o.price,p.slots[m]-p.held[m],o.lot) for m,o in enumerate(chosen) if o is not None)
        problem=replace(p,offers=offers,fees=(0.,)*n,bids=(0,)*n,funded_demands=None)
        result=solver(problem)
        return result['quantities']
    reference=hypothetical()
    bids=tuple(reference[m] if o is not None and o.supplier==p.incumbents[m] else 0 for m,o in enumerate(refs))
    demands=tuple(hypothetical(o.material,o)[o.material] for o in p.offers)
    funded=replace(p,bids=bids,funded_demands=demands)
    return funded,solver(funded)


def cases():
    # Output quantity and space preserve input/output embodied-space accounting.
    return {
        'complementary_inputs_scarce_cash':Problem((0,0),(0.,0.),(1.,1.),(4,4),8.,4.,
            (Offer(0,0,1.,4),Offer(1,1,2.,4)),(-1,-1),(0,0),(0.,0.),
            (Line((1,1),4,.25,3.,0.,tuple(3.*q for q in range(9)),1.,2),),((0.,)*5,(0.,)*5)),
        'conversion_cash_reservation':Problem((0,),(0.,),(1.,),(10,),10.,10.,
            (Offer(0,0,1.,10),),(-1,),(0,),(0.,),
            (Line((1,),10,1.,4.,0.,tuple(4.*q for q in range(11)),1.),),((0.,)*11,)),
        'weak_realizable_sales':Problem((0,),(0.,),(1.,),(8,),8.,20.,
            (Offer(0,0,1.,8),),(-1,),(0,),(0.,),
            (Line((1,),8,.25,4.,0.,tuple(4.*min(q,1) for q in range(9)),1.),),((0.,)*9,)),
        'owned_input_history_gate':Problem((1,0),(100.,0.),(1.,1.),(2,2),4.,20.,
            (Offer(1,1,1.,2),),(-1,1),(0,0),(0.,0.),
            (Line((1,1),1,.25,3.,0.,(0.,3.,6.),1.,2),),((0.,)*3,(0.,)*3)),
        'useful_future_buffer_assumption':Problem((0,0),(0.,0.),(1.,1.),(4,4),8.,11.,
            (Offer(0,0,1.,4),),(-1,-1),(0,0),(0.,0.),
            (Line((1,1),4,.25,3.,0.,tuple(3.*q for q in range(9)),1.,2),),
            ((0.,1.5,3.,3.,3.),(0.,)*5)),
    }


def compare(p):
    funded,allocation=replenishment_plan(p)
    refill=evaluate(funded,tuple(int(q) for q in allocation[0]))
    bp,batch=fund_policy(p,batch_first)
    vp,value=fund_policy(p,solve)
    answer={}
    for name,problem,result in [('storage_units',funded,refill),('batch_first',bp,batch),('scenario_return',vp,value)]:
        answer[name]=dict(result,fundedBids=problem.bids,quoteQuantities=problem.funded_demands)
    return answer


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    result=dict(scope='Small exhaustive mechanism counterexamples. Fixture sales/terminal tables are assumptions, not forecasts or economic validation.',
                objectives=dict(storage_units='Most purchased input units, then least payment.',
                    batch_first='Most actual produced output items, then most input units, then least goods/fee payment.',
                    scenario_return='Explicit scenario output/terminal values minus goods, fees and actual conversion.'),
                cases={name:dict(problem=asdict(p),policies=compare(p)) for name,p in cases().items()})
    payload=json.dumps(result,indent=2)+'\n'
    with a.output.open('x') as stream:
        stream.write(payload)
    for name,row in result['cases'].items():
        print(name,{policy:dict(purchases=v['quantities'],outputs=v['outputs'],value=v['value']) for policy,v in row['policies'].items()})


if __name__=='__main__':
    main()
