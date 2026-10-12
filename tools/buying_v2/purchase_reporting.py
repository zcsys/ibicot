"""Project recorded purchasing evidence with explicit units and denominators."""
import json
from pathlib import Path
import numpy as np
from .observations import schema as retail_schema
from .industrial_observations import schema as industrial_schema


def schema(coverage):
    return dict(version=2,retail=retail_schema(),industrial=industrial_schema(),
                industrialCoverage=list(coverage),
                notes='Industrial observations are diagnostic only. Discovery stock checks are not incoming orders; quoted remainders are not unique market demand.')


def ratio(numerator,denominator):
    return float(numerator/denominator) if denominator else None


def project(totals,definition,coverage,start,end):
    fields=definition['fields']
    if totals.shape!=(len(definition['markets']),len(fields)):
        raise ValueError('industrial metric shape does not match recorded schema')
    rows=[]
    for market,values in zip(definition['markets'],totals):
        measured=market['buyerTier'] in coverage
        row=dict(market,measured=measured)
        row.update({name:float(value) if measured else None for name,value in zip(fields,values)})
        if measured:
            purchasing=row['decisions']-row['noPurchaseDecisions']
            row.update(observedStockAvailability=ratio(row['sufficientStockChecks'],row['fundedOfferChecks']),
                       purchaseDecisionRate=ratio(purchasing,row['decisions']),
                       meanSuppliersPerPurchase=ratio(row['positiveLegs'],purchasing),
                       feeIncidence=ratio(row['feesPaid'],purchasing),
                       referenceShortfallRate=ratio(row['referenceShortfall'],row['referenceFundedQuantity']))
        else:
            row.update({name:None for name in ('observedStockAvailability','purchaseDecisionRate','meanSuppliersPerPurchase','feeIncidence','referenceShortfallRate')})
        rows.append(row)
    return dict(version=1,startTick=int(start),endTick=int(end),rows=rows,
        units='Quantities are items; money is dollars. Checks and legs are event counts, not distinct companies.',
        denominators=dict(observedStockAvailability='fundedOfferChecks',purchaseDecisionRate='decisions',
                          meanSuppliersPerPurchase='decisions minus noPurchaseDecisions',
                          feeIncidence='decisions minus noPurchaseDecisions',referenceShortfallRate='referenceFundedQuantity'),
        caveat='No unique-demand or causal stock-loss estimate. Ratios use summed period numerators and denominators; zero denominators and uninstrumented tiers are null.')


def report(directory):
    """Read schema with stable archived IDs; reject gaps, overlaps or old data."""
    directory=Path(directory)
    definition=json.loads((directory/'purchase-schema.json').read_text())
    if definition.get('version')!=2:
        raise ValueError('recording has no version-2 industrial purchasing observations')
    totals=np.zeros((len(definition['industrial']['markets']),len(definition['industrial']['fields'])))
    ticks=[]
    for file in sorted(directory.glob('purchase-*.npz')):
        with np.load(file,allow_pickle=False) as data:
            if 'industrialObservations' not in data:
                raise ValueError('missing industrial observation array')
            block=data['industrialObservations']
            if block.shape!=(len(data['ticks']),*totals.shape) or not np.all(np.isfinite(block)) or np.any(block<0):
                raise ValueError('invalid industrial observation block')
            ticks.extend(data['ticks'].tolist())
            totals+=block.sum(axis=0)
    if not ticks or ticks!=list(range(ticks[0],ticks[-1]+1)):
        raise ValueError('missing, gapped or overlapping purchase history')
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('status')!='complete' or [ticks[0],ticks[-1]]!=manifest['specification']['window']:
        raise ValueError('purchase history does not cover a completed run')
    return project(totals,definition['industrial'],definition['industrialCoverage'],ticks[0],ticks[-1])


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=report(args.directory)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
