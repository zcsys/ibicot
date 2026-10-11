"""Verify preserved replay coverage and reconcile its product accounts to baseline."""
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('legacy',type=Path);p.add_argument('baseline',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    latest=Path((a.legacy/'served-recovery-path.txt').read_text().strip())
    paths=sorted(q.resolve() for q in a.legacy.glob('served-recovery-*') if q.is_dir() and (q/'generation_run.jsonl').exists())
    assert latest in paths
    schema=json.loads((a.baseline/'measurement-schema.json').read_text());fields=schema['fields']
    chunks=[np.load(f)['data'] for f in sorted(a.baseline.glob('products-*.npz'))]
    data=np.concatenate(chunks)[:7200]
    data[:,:,fields.index('net')]=sum(sign*data[:,:,fields.index(name)] for sign,name in
        ((1,'revenue'),(-1,'cogs'),(1,'switchIncome'),(-1,'switchExpense'),(-1,'rent')))
    names=('revenue','cogs','sold','switchIncome','switchExpense','rent','net')
    legacy_names=('revenue','cogs','sold','switchingIncome','switchingExpense','rent','netEarnings')
    ids={(p['tier'],p['id']):i for i,p in enumerate(schema['products'])}
    ticks=[];maxabs={x:0. for x in names};failures={x:0 for x in names};coverage=[]
    for path in paths:
        count=0;first=None;last=None
        with (path/'generation_run.jsonl').open() as f:
            for line in f:
                row=json.loads(line);t=row['tick'];ticks.append(t);first=t if first is None else first;last=t;count+=1
                for product in row['productProfitability']:
                    i=ids[(product['tier'],product['product'])]
                    for new,old in zip(names,legacy_names):
                        x=float(product[old]);y=float(data[t-1,i,fields.index(new)]);d=abs(x-y)
                        maxabs[new]=max(maxabs[new],d)
                        if d>1e-8+1e-12*max(abs(x),abs(y)):failures[new]+=1
        coverage.append(dict(path=str(path.resolve()),start=first,end=last,rows=count))
    assert ticks==list(range(1,7201)),'replay gaps/overlap'
    original=[json.loads(x)['tick'] for x in (a.legacy/'generation_run.jsonl').read_text().splitlines()]
    assert original==ticks
    result=dict(coverage=coverage,originalCoverage=[original[0],original[-1]],productTicks=len(ids)*len(ticks),
        maxAbsoluteDifference=maxabs,failedComparisons=failures,
        result='pass' if not any(failures.values()) else 'mismatch',
        notes='Compare account fields only; no historical sampler/unique-intention detail is inferred from snapshots.')
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
