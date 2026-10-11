"""Expose a prospective-return/retained-production-gate incompatibility."""
import argparse
import json
from pathlib import Path
from economy.kernel.numba import _production_batches
from .microcases import industrial_case


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    case=industrial_case([1,0],[1,1],[1,1],[1,2],[100,100],100,
        [[100.],[1.]],[[100],[100]],[0,0],[0,0],96,0,10,30,.75,20)
    assert case['quantity']==[0,1] and case['plannedOutput']==1 and case['objective']>0
    historical_a=100.;new_b=1.;conversion=.75
    accounting_unit_cost=historical_a+new_b+conversion
    produced=int(_production_batches(1,1,accounting_unit_cost,10.,0.,.05))
    assert produced==0
    result=dict(status='counterexample verified',basket=case,ownedInputHistoricalUnitCost=historical_a,
        productionAccountingUnitCost=accounting_unit_cost,outputQuote=10,gateMarginBand=.05,
        physicallyAndCashFeasibleOutput=1,compiledProductionGateOutput=produced,
        consequence='The objective chooses the one-dollar missing complement for positive modeled incremental return, but the unchanged historical-cost production gate permits no output. The purchased input remains an asset; no operating loss or realized eight-dollar profit is posted merely by acquiring it.',
        interpretation='Ignoring sunk input basis can be a reasonable incremental economic objective, but it is not sufficient when an independently retained book-margin gate constrains execution. R1 does not model this gate inside its future-plan feasibility. This is a conceptual mismatch, not a solver/oracle disagreement.',
        scope='Fixed quotes and costs, one complete recipe, no fees or rent; no claim about frequency or eventual price changes in the adaptive full world.',
        remainingAction='A replacement objective must respect the retained production gate or propose a separately authorized change to it. Do not silently change the gate to conceal this counterexample.')
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
