"""Read-only offer-grid sizes from verified industrial traces; not solver work estimates."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def integer(value,label):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or int(value)!=value:
        raise ValueError('invalid '+label)
    return int(value)


def bounded_compositions(caps,total):
    """Exact count of 0 <= x[i] <= cap[i], sum(x) <= total, via inclusion/exclusion."""
    total=integer(total,'total')
    caps=[integer(c,'cap') for c in caps]
    caps=[min(c,total) for c in caps if c>0]
    n=len(caps)
    if n>16:raise ValueError('geometry proof limited to sixteen offers per material')
    count=0
    for mask in range(1<<n):
        left=total-sum(caps[i]+1 for i in range(n) if mask&(1<<i))
        if left>=0:count+=(-1 if mask.bit_count()%2 else 1)*math.comb(left+n,n)
    return count


def geometry(document,row):
    identity={k:document[k] for k in ('seed','tick','tier','phase')};identity['firm']=row['firm']
    if row['status']=='callback-not-observed':return dict(**identity,status=row['status'])
    if row['status']!='captured':raise ValueError('unknown trace status')
    lot=integer(row['lot'],'lot')
    if lot<1:raise ValueError('positive lot required')
    mi={n:i for i,n in enumerate(document['materialFields'])};oi={n:i for i,n in enumerate(document['offerFields'])}
    targets=[integer(r[mi['target']],'target')//lot for r in row['materials']]
    caps=[[] for _ in targets]
    for offer in row['offers']:
        material=integer(offer[oi['materialIndex']],'material index')
        if material>=len(caps):raise ValueError('material index out of range')
        caps[material].append(min(integer(offer[oi['stock']],'stock')//lot,targets[material]))
    independent=math.prod(c+1 for group in caps for c in group)
    coupled=math.prod(bounded_compositions(group,total) for group,total in zip(caps,targets))
    return dict(**identity,status='captured',materials=len(targets),offers=sum(map(len,caps)),
        positiveQuantityOffers=sum(c>0 for group in caps for c in group),maxOfferLotChoices=max((c+1 for group in caps for c in group),default=1),
        independentStockSlotGrid=str(independent),perMaterialSlotFeasibleGrid=str(coupled),
        scope='One recorded company phase. Cash, fees, shared physical space, production and future decisions are not filtered.')


def summarize(rows):
    groups=defaultdict(list)
    for row in rows:groups[f"T{row['tier']}-phase-{row['phase']}"].append(row)
    result={}
    for name,items in sorted(groups.items()):
        captured=[r for r in items if r['status']=='captured'];values=sorted(int(r['perMaterialSlotFeasibleGrid']) for r in captured)
        def quantile(q):return str(values[max(0,math.ceil(q*len(values))-1)]) if values else None
        result[name]=dict(sampled=len(items),captured=len(captured),notObserved=len(items)-len(captured),
            fixedZeroGrid=sum(v==1 for v in values),slotGridAbove4000=sum(v>4000 for v in values),
            slotGridMedianNearestRank=quantile(.5),slotGridP95NearestRank=quantile(.95),slotGridMaximum=quantile(1),
            maximumPositiveQuantityOffers=max((r['positiveQuantityOffers'] for r in captured),default=None))
    return result


def analyze(run):
    proof=json.loads((run/'trace-reconstruction-proof.json').read_text())
    if proof['status']!='pass':raise ValueError('trace reconstruction proof must pass')
    rows=[];identities=set();ticks=set();hashes={}
    for name,expected in sorted(proof['files'].items()):
        path=run/name;raw=path.read_bytes();actual=hashlib.sha256(raw).hexdigest()
        if actual!=expected:raise ValueError('trace hash mismatch: '+name)
        hashes[name]=actual
        for doc in json.loads(raw):
            if doc['schema']!=1:raise ValueError('unsupported trace schema')
            ticks.add(doc['tick'])
            for row in doc['decisions']:
                result=geometry(doc,row);key=tuple(result[k] for k in ('seed','tick','tier','phase','firm'))
                if key in identities:raise ValueError('duplicate sampled identity')
                identities.add(key);rows.append(result)
    if sorted(ticks)!=list(range(min(ticks),max(ticks)+1)):raise ValueError('trace tick gap')
    return dict(run=str(run.resolve()),sourceIdentity=proof['sourceIdentity'],tickRange=[min(ticks),max(ticks)],
        fileHashes=hashes,summary=summarize(rows),rows=rows,
        scope='Systematic startup sample under isolated D3 replenishment. Grid sizes are not actual search work, feasible profitable policy counts, population frequencies or continuation timing estimates.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=analyze(args.run)
    with args.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result['summary'],indent=2))


if __name__=='__main__':main()
