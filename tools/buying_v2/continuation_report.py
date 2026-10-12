"""Preserve two-period buffer counterexamples with explicit supply beliefs."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from .policy_comparison import cases
from .industry_oracle import Offer
from .continuation_oracle import continuation,optimize,optimize_uncertain


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    initial=cases()['useful_future_buffer_assumption']
    future=replace(initial,offers=(Offer(1,1,4.,2),),terminal_values=((0.,)*5,(0.,)*5))
    empty=replace(future,offers=())
    result=dict(scope='Exhaustive delayed-receipt scenario benchmark; no loyalty fees or rent, not a calibrated world forecast.',
        initial=asdict(initial),future=asdict(future),finishedCaps=[8],closingDemand=[4],
        fixedActions=[dict(quantity=q,result=continuation(initial,future,(8,),(4,),(q,))) for q in range(5)],
        knownArrival=optimize(initial,future,(8,),(4,)),
        noArrival=optimize(initial,empty,(8,),(4,)),
        uncertainArrival={str(p):optimize_uncertain(initial,((p,future,((1.,(4,)),)),(1-p,empty,((1.,(4,)),))),(8,)) for p in (.5,.75)},
        information='First action is shared across supply states. Second action observes supply/quotes, but not the closing demand realization. Sales cash arrives only at closing.')
    payload=json.dumps(result,indent=2)+'\n'
    with args.output.open('x') as stream:
        stream.write(payload)
    print(json.dumps(dict(knownArrival=result['knownArrival']['first']['allocation'],
                         noArrival=result['noArrival']['first']['allocation'],
                         uncertain={p:r['firstAllocation'] for p,r in result['uncertainArrival'].items()})))


if __name__=='__main__':
    main()
