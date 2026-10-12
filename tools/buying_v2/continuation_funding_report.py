"""Reproducible joint-funding examples and explicit unsuccessful candidates."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from .industry_oracle import Line, Offer
from .phase_ledger import Company, State, Purchase, OpenBook, SettleBook
from .phase_oracle import Scenario, solve


def base(slots,cash,quote,conversion,batches):
    n=len(slots)
    line=Line((1,)*n,batches,conversion,quote,0.,(0.,)*(batches+1),1.)
    c=Company((1.,)*n,slots,float(sum(slots)+batches),(line,),(batches,),0.)
    s=State(cash,(0,)*n,(0.,)*n,(0,),(0.,),(quote,),(-1,)*n)
    return c,s


def make_path(c,events):
    return Scenario(1.,tuple(events),tuple((0.,)*(cap+1) for cap in c.slots),
                    tuple((0.,)*(cap+1) for cap in c.finished_caps))


def cases():
    c,s=base((4,2),4.,5.,.5,2)
    b=Purchase('buy',(Offer(0,1,1.,4),Offer(1,2,2.,2)),(),(.5,.5),1.,0.,(0,),0.)
    yield 'joint-complements',c,s,make_path(c,(b,OpenBook('sales'),SettleBook('sales',(2,)))),('continuation',)
    c,s=base((2,2),5.,5.,.5,2);s=replace(s,incumbents=(1,2))
    b=replace(b,offers=(Offer(0,1,1.,2),Offer(1,2,2.,2),Offer(1,3,1.,2)),reliability=(.5,.5,.5))
    yield 'flexible-other-quotes',c,s,make_path(c,(b,OpenBook('sales'),SettleBook('sales',(2,)))),('continuation-reference-v1','continuation')
    c,s=base((3,1),7.,10.,.25,1);s=replace(s,incumbents=(-1,7))
    now=replace(b,label='A-now',offers=(Offer(0,1,1.,3),),reliability=(0.,))
    later=replace(now,label='B-later',offers=(Offer(1,7,5.,1),Offer(1,2,1.,1)),reliability=(0.,0.),fee_multiple=3.)
    for name,fee in (('cash-truncation-fee-incentive',3.),('no-fee-control',0.)):
        event=replace(later,fee_multiple=fee)
        yield name,c,s,make_path(c,(now,event,OpenBook('sales'),SettleBook('sales',(1,)))),('continuation',)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    source=a.output/'source'/'tools'/'buying_v2';source.mkdir(parents=True)
    (source/'__init__.py').write_text('')
    hashes={}
    for name in ('continuation_funding_report.py','phase_oracle.py','phase_ledger.py','industry_oracle.py'):
        data=Path(__file__).with_name(name).read_bytes()
        (source/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    manifest=dict(status='running',sourceHashes=hashes)
    manifest_path=a.output/'manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    try:
        results=[]
        for name,c,s,path,modes in cases():
            results.append(dict(name=name,company=c,initial=s,scenario=path,
                                outcomes={mode:solve(c,s,(path,),funding=mode) for mode in modes}))
        (a.output/'result.json').write_text(json.dumps(dict(cases=results,
            scope='Small exact examples, not calibrated forecasts, full-world outcomes or an adoption recommendation.'),
            default=asdict,indent=2)+'\n')
        manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
