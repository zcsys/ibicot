"""Preserve worked timing, fee and liability examples with code identities."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from .industry_oracle import Line, Offer
from .phase_ledger import Company, State, Purchase, OpenBook, SettleBook, Rent, EndTick, replay, horizon_value
from .phase_oracle import Scenario, solve


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    line=Line((1,),2,1.,3.,0.,(0.,)*3,1.)
    company=Company((1.,),(4,),10.,(line,),(4,),0.)
    initial=State(1.,(0,),(0.,),(1,),(.5,),(3.,),(-1,))
    events=(OpenBook('C3'),Purchase('C3-buy',(Offer(0,1,1.,1),),(1,),(.5,),1.,0.,(0,),0.),
            SettleBook('C3',(1,)),Purchase('C4-buy',(),(),(),1.,0.,(0,),0.))
    final,trace=replay(company,initial,events,{1:(1,),3:()})
    timing=dict(company=asdict(company),initial=asdict(initial),events=[asdict(e) for e in events],
                allocations={'1':[1],'3':[]},trace=trace,final=asdict(final))
    rent_company=Company((1.,),(1,),4.,(line,),(2,),2_000_000.)
    rent_initial=State(0.,(0,),(0.,),(1,),(0.,),(10.,),(-1,))
    rent_events=(Rent('tick1',4.),EndTick('tick1-end',.15),Rent('tick2',4.),EndTick('tick2-end',.15),
                 OpenBook('retail'),SettleBook('retail',(1,)),Rent('zero-rate-collection',0.))
    rent_final,rent_trace=replay(rent_company,rent_initial,rent_events,{})
    liabilities=dict(company=asdict(rent_company),initial=asdict(rent_initial),events=[asdict(e) for e in rent_events],
                     trace=rent_trace,final=asdict(rent_final),horizonValue=horizon_value(rent_initial,rent_final,((0.,),),((0.,),)))
    line=Line((1,),1,.25,4.,0.,(0.,0.),1.)
    c=Company((1.,),(1,),4.,(line,),(2,),0.)
    s=State(10.,(0,),(0.,),(0,),(0.,),(4.,),(-1,))
    buy=Purchase('buy',(Offer(0,1,3.,1),),(),(.5,),1.,0.,(0,),0.)
    scenarios=tuple(Scenario(.5,(buy,OpenBook('sales'),SettleBook('sales',(q,))),((0.,0.),),((0.,)*3,)) for q in (0,1))
    def funding(company,state,event):
        return tuple(min(1,company.slots[o.material]-state.held[o.material],int(state.cash//o.price)) for o in event.offers)
    result=solve(c,s,scenarios,funding=funding)
    result['leaves']=[{**leaf,'state':asdict(leaf['state'])} for leaf in result['leaves']]
    hidden=dict(company=asdict(c),initial=asdict(s),scenarios=[asdict(v) for v in scenarios],result=result,
                funding='Explicit single-material fixture: at most one item per hypothetical quote, within current cash and input slots. Not an adopted value-model funding rule.')
    sources={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
             for name in ('phase_report.py','phase_ledger.py','phase_oracle.py','industry_oracle.py')}
    output=dict(sourceHashes=sources,receiptTiming=timing,rentLiabilities=liabilities,hiddenDemand=hidden,
                status='Small-instance contract evidence; no production activation or full-world model claim.')
    serialized=json.dumps(output,indent=2)+'\n'
    with args.output.open('x') as stream:stream.write(serialized)


if __name__=='__main__':main()
