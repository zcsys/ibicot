"""Exact end-state and posted-account comparison for behavior-preserving changes."""
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path)
    p.add_argument('--tick',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    stem=f'checkpoint-{a.tick:06}';failures=[]
    with np.load(a.before/(stem+'.npz')) as x,np.load(a.after/(stem+'.npz')) as y:
        assert x.files==y.files
        count=len(x.files)
        for k in x.files:
            if not np.array_equal(x[k],y[k],equal_nan=True):failures.append(k)
    for suffix in ('.json',):
        x=json.loads((a.before/(stem+suffix)).read_text());y=json.loads((a.after/(stem+suffix)).read_text())
        for k in x:
            if json.dumps(x[k],sort_keys=True)!=json.dumps(y[k],sort_keys=True):failures.append('json:'+k)
    with np.load(a.before/f'research-{a.tick:06}.npz') as x,np.load(a.after/f'research-{a.tick:06}.npz') as y:
        for k in ('local1','local2','market1','market2','lastTick'):
            if not np.array_equal(x[k],y[k],equal_nan=True):failures.append('research:'+k)
    result=dict(before=str(a.before.resolve()),after=str(a.after.resolve()),tick=a.tick,worldArrays=count,
                exactWorldJSON=True,researchInformationArrays=4,differences=failures,
                status='pass' if not failures else 'fail')
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
