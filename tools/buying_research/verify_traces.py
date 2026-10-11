"""Replay recorded decision snapshots without accessing the final world state."""
import argparse
import json
from pathlib import Path
import numpy as np
from .solvers import industry,retail,marginal_values


def verify(path):
    counts=dict(t1=0,t2=0,t3=0)
    for file in sorted(Path(path).glob('requests-*.npz')):
        with np.load(file,allow_pickle=False) as z:
            for key in z.files:
                if key.startswith(('t1_','t2_')):
                    for rows in z[key]:
                        if not np.isfinite(rows[0,0]):continue
                        nm=int(rows[0,34]);r=rows[:nm];n=int(max(r[:,30]));prices=np.zeros((nm,n));stocks=np.zeros((nm,n))
                        for m,row in enumerate(r):
                            for s in range(int(row[30])):prices[m,s]=row[41+3*s];stocks[m,s]=row[42+3*s]
                        a=industry(r[:,16],r[:,17],r[:,18],r[:,19],r[:,20],r[0,21],prices,stocks,
                            r[:,30].astype(np.int64),r[:,28].astype(np.int64),r[:,29],r[:,4].astype(np.int64),
                            int(r[0,27]),r[0,23],r[0,24],r[0,12],r[0,25],r[0,22],r[0,26])
                        np.testing.assert_array_equal(a[1],r[:,6])
                        np.testing.assert_allclose(a[2],r[:,8],rtol=0,atol=1e-9)
                        np.testing.assert_allclose(a[4],r[0,11],rtol=1e-12,atol=1e-9)
                        for m,s in enumerate(a[0]):
                            if a[1][m]:assert r[m,40+3*s]==r[m,3]
                            old=int(r[m,2]);quantity=int(r[m,6]);bid=int(r[m,4])
                            seller=int(r[m,3]);expected=old
                            if quantity>0 and bid>0 and quantity>=bid:
                                expected=seller//4 if key.startswith('t1_') else seller
                            assert int(r[m,9])==expected,'industry preference reconstruction mismatch'
                            pref=int(r[m,28])
                            if pref<0 or bid<=0 or stocks[m,pref]<bid:
                                assert r[m,29]==0 and r[m,8]==0,'unavailable incumbent received a fee'
                        counts[key[:2]]+=1
                elif key.startswith('t3_'):
                    for r in z[key]:
                        if not np.isfinite(r[0]):continue
                        n=int(r[18]);p=r[21:20+4*n:4];s=r[22:20+4*n:4]
                        v=marginal_values(r[12],r[13],r[14],r[15])
                        a=retail(v,p,s,int(r[16]),int(r[4]),r[17],1e100)
                        np.testing.assert_array_equal(a[0],r[23:20+4*n:4])
                        np.testing.assert_allclose(a[1:4],[r[11],r[7],r[8]],rtol=1e-12,atol=1e-9)
                        expected=int(r[20+4*a[4]]) if a[4]>=0 else int(r[2])
                        assert int(r[9])==expected,'retail preference reconstruction mismatch'
                        pref=int(r[16]);bid=int(r[4])
                        if pref<0 or bid<=0 or s[pref]<bid:
                            assert r[17]==0 and r[8]==0,'unavailable incumbent received a fee'
                        counts['t3']+=1
    if not all(counts.values()):raise ValueError('missing buyer-class traces')
    return counts


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');a=p.parse_args()
    result=dict(run=str(Path(a.run).resolve()),replayed=verify(a.run),status='pass')
    with open(Path(a.run)/'trace-verification.json','x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
