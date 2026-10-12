"""Reproducible inventory carry-over examples for the small event-tree oracle."""
import argparse
from dataclasses import asdict,replace
import hashlib,json
from pathlib import Path
from .industry_oracle import Line,Offer
from .phase_ledger import Company,State,Purchase,OpenBook,SettleBook,SetQuotes
from .phase_oracle import Scenario,solve


def examples():
    c=Company((1.,),(1,),4.,(Line((1,),1,.25,3.,0.,(0.,0.),1.),),(2,),0.)
    s=State(10.,(0,),(0.,),(0,),(0.,),(3.,),(-1,))
    b=Purchase('first',(Offer(0,1,1.,1),),(),(0.,),1.,0.,(0,),0.)
    rows=[]
    for arrival in (0,1):
        later=replace(b,label='second',offers=(Offer(0,1,1.,1+arrival),))
        events=(b,OpenBook('early'),SettleBook('early',(1,)),SetQuotes('lower',(2.,)),
                later,OpenBook('late'),SettleBook('late',(1,)))
        scenario=Scenario(1.,events,((0.,0.),),((0.,)*3,))
        for mode in ('independent-snapshots','persistent-arrivals'):
            result=solve(c,s,(scenario,),funding='continuation',supply=mode)
            rows.append(dict(arrivals=arrival,supplyMode=mode,company=asdict(c),initial=asdict(s),
                scenario={**asdict(scenario),'eventTypes':[type(e).__name__ for e in events]},result=result))
    return dict(scope='Small supplied supply scenarios; no outside withdrawals, self-supply, calibrated scenario generation or population execution.',examples=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    package=a.output/'source'/'tools'/'buying_v2';package.mkdir(parents=True)
    (package/'__init__.py').write_text('');(package.parent/'__init__.py').write_text('')
    hashes={}
    for name in ('persistent_supply_report.py','phase_ledger.py','phase_oracle.py','industry_oracle.py'):
        data=Path(__file__).with_name(name).read_bytes();(package/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    (a.output/'source-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    result=examples()
    (a.output/'results.json').write_text(json.dumps(result,default=asdict,indent=2)+'\n')
    print([(x['arrivals'],x['supplyMode'],x['result']['expectedValue']) for x in result['examples']])


if __name__=='__main__':main()
