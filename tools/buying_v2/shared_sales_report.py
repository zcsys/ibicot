"""Preserve explicit multi-line shared-demand counterexamples and source."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from .industry_oracle import Line, Offer
from .phase_ledger import Company, State, Purchase, OpenBook, SettleBook, SharedSettleBook
from .phase_oracle import Scenario, solve


def examples():
    lines=tuple(Line(recipe,1,.25,3.,0.,(0.,0.),1.) for recipe in ((1,0),(0,1)))
    company=Company((1.,1.),(1,1),8.,lines,(2,2),0.)
    initial=State(10.,(0,0),(0.,0.),(0,0),(0.,0.),(3.,3.),(-1,-1))
    buy=Purchase('buy',(Offer(0,10,1.,1),Offer(1,11,1.,1)),(),(0.,0.),1.,0.,(0,1),0.)
    rows=[]
    for name,state,sale in (
        ('independent-opportunities',initial,SettleBook('sales',(1,1))),
        ('one-shared-opportunity',initial,SharedSettleBook('sales',(1,1),groups=((0,1),))),
        ('shared-with-old-stock',replace(initial,finished=(1,0),finished_basis=(.5,0.)),
         SharedSettleBook('sales',(1,1),groups=((0,1),)))):
        scenario=Scenario(1.,(buy,OpenBook('sales'),sale),((0.,0.),(0.,0.)),((0.,)*3,(0.,)*3))
        result=solve(company,state,(scenario,),funding='continuation')
        rows.append(dict(name=name,company=asdict(company),initial=asdict(state),
                         scenario={**asdict(scenario),'eventTypes':[type(e).__name__ for e in scenario.events]},
                         result=result))
    return dict(scope='Explicit small scenarios only. Shared residual-demand allocation is an assumption, not a calibrated world market or production adoption.',examples=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    package=args.output/'source'/'tools'/'buying_v2';package.mkdir(parents=True)
    (package/'__init__.py').write_text('');(package.parent/'__init__.py').write_text('')
    hashes={}
    for name in ('shared_sales_report.py','phase_ledger.py','phase_oracle.py','industry_oracle.py'):
        data=Path(__file__).with_name(name).read_bytes();(package/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    (args.output/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    result=examples()
    text=json.dumps(result,default=lambda x:asdict(x),indent=2)+'\n'
    (args.output/'results.json').write_text(text)
    print(json.dumps({x['name']:x['result']['expectedValue'] for x in result['examples']}))


if __name__=='__main__':main()
