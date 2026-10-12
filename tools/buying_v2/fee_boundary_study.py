"""Small, preregistered sensitivity study of continuation funding boundaries."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from .industry_oracle import Line, Offer
from .phase_ledger import Company, State, Purchase, OpenBook, SettleBook, EndTick
from .phase_oracle import Scenario, solve

MODES=('continuation','continuation-transfer-neutral')


def fee_case(cash,fee,slot):
    line=Line((1,1),1,.25,10.,0.,(0.,0.),1.)
    c=Company((1.,1.),(slot,1),float(slot+2),(line,),(1,),0.)
    s=State(cash,(0,0),(0.,0.),(0,),(0.,),(10.,),(-1,7))
    now=Purchase('A-now',(Offer(0,1,1.,slot),),(),(0.,),1.,0.,(0,),0.)
    later=replace(now,label='B-later',offers=(Offer(1,7,5.,1),Offer(1,2,1.,1)),reliability=(0.,0.),fee_multiple=fee)
    path=Scenario(1.,(now,EndTick('tick1-end',.15),later,OpenBook('sales'),SettleBook('sales',(1,))),
                  ((0.,)*(slot+1),(0.,0.)),((0.,0.),))
    return c,s,(path,)


def income_case(probability):
    line=Line((1,1),1,.25,4.,0.,(0.,0.),1.)
    c=Company((1.,1.),(1,1),4.,(line,),(2,),0.)
    # Existing sellable stock makes the later switching receipt feasible: this
    # company can fill a one-unit order, while the outside seller wins instead.
    # That old unit is subsequently sold at closing and is valued only once.
    s=State(1.,(0,0),(0.,0.),(1,),(0.,),(4.,),(-1,7))
    now=Purchase('A-now',(Offer(0,1,1.,1),),(),(0.,),1.,0.,(0,),0.)
    later=replace(now,label='B-later',offers=(Offer(1,2,1.,1),),reliability=(0.,))
    def path(weight,income):
        return Scenario(weight,(now,EndTick('tick1-end',.15),OpenBook('fee-source'),SettleBook('fee-source',(0,),fee_income=income),
                         later,OpenBook('closing'),SettleBook('closing',(2,))),
                         ((0.,0.),(0.,0.)),((0.,0.,0.),))
    return c,s,(path(probability,2.),path(1-probability,0.))


def summarize(result):
    leaves=[]
    for leaf in result['leaves']:
        state=leaf['state']
        leaves.append(dict(probability=leaf['probability'],value=leaf['value'],
            firstAllocation=leaf['trace'][0]['allocation'],remainingInputs=state.held,
            feeExpense=state.accounts.fee_expense,feeIncome=state.accounts.fee_income,
            closingCash=state.cash,postedEarnings=state.accounts.earnings))
    return dict(expectedValue=result['expectedValue'],enumeratedNodes=result['enumeratedNodes'],leaves=leaves)


def evaluate(spec):
    rows=[]
    for cash in spec['cash']:
        for fee in spec['fees']:
            for slot in spec['inputSlots']:
                c,s,paths=fee_case(cash,fee,slot)
                outcomes={mode:summarize(solve(c,s,paths,funding=mode,max_nodes=spec['maxNodes'])) for mode in MODES}
                rows.append(dict(cash=cash,fee=fee,inputSlots=slot,outcomes=outcomes))
    controls={(r['cash'],r['inputSlots'],mode):r['outcomes'][mode]['leaves'][0]['firstAllocation'][0]
              for r in rows if r['fee']==0 for mode in MODES}
    for row in rows:
        for mode,outcome in row['outcomes'].items():
            outcome['extraInputVersusNoFee']=outcome['leaves'][0]['firstAllocation'][0]-controls[(row['cash'],row['inputSlots'],mode)]
    summary={mode:dict(cases=len(rows),feeInducedExtraInputCases=sum(r['outcomes'][mode]['extraInputVersusNoFee']>0 for r in rows),
                       totalExpectedValue=sum(r['outcomes'][mode]['expectedValue'] for r in rows)) for mode in MODES}
    incomes=[]
    for probability in spec['incomeProbabilities']:
        c,s,paths=income_case(probability)
        incomes.append(dict(probability=probability,company=c,initial=s,scenarios=paths,
            outcomes={mode:summarize(solve(c,s,paths,funding=mode,max_nodes=spec['maxNodes'])) for mode in MODES}))
    return dict(specification=spec,summary=summary,feeCases=rows,incomeCases=incomes,
        caveat='Finite small-company sensitivity, not a whole-economy campaign. The alternative suppresses all future switching transfers only inside funded-intention counterfactuals; actual payments are unchanged. Eliminating the waste incentive does not prove the alternative preserves useful funding.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();spec=json.loads(a.spec.read_text());a.output.mkdir(parents=True,exist_ok=False)
    source=a.output/'source'/'tools'/'buying_v2';source.mkdir(parents=True)
    (source/'__init__.py').write_text('')
    hashes={}
    for name in ('fee_boundary_study.py','phase_oracle.py','phase_ledger.py','industry_oracle.py'):
        data=Path(__file__).with_name(name).read_bytes();(source/name).write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    (a.output/'specification.json').write_bytes(a.spec.read_bytes())
    manifest=dict(status='running',sourceHashes=hashes,specificationSha256=hashlib.sha256(a.spec.read_bytes()).hexdigest())
    path=a.output/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
    try:
        result=evaluate(spec)
        (a.output/'result.json').write_text(json.dumps(result,default=asdict,indent=2)+'\n')
        manifest['status']='complete'
    except BaseException as exc:
        manifest.update(status='failed',error=repr(exc));raise
    finally:path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
