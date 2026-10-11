"""Falsify seller neutrality of the frozen stable-ID tie rule in equal-quote markets."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from .solvers import sample_distinct
from .jit import njit


@njit
def sample_counts(n,k,draws,seed):
    ids=np.arange(n);selected=np.zeros(n,dtype=np.int64);included=np.zeros(n,dtype=np.int64)
    for buyer in range(draws):
        offers=sample_distinct(ids,-1,seed,1,buyer,0,k)
        selected[offers[0]]+=1
        for seller in offers:included[seller]+=1
    return selected,included


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    n=100;k=5;draws=100000;denom=math.comb(n,k)
    exact=np.array([math.comb(n-j-1,k-1)/denom if n-j-1>=k-1 else 0. for j in range(n)])
    result=dict(fixture=dict(sellers=n,alternatives=k,incumbent=None,quotes='equal',stock='unlimited',
        quantity=1,fees=0,drawsPerSeed=draws),formula='Pr(lowest sampled seller ID = j) = C(N-j-1,k-1)/C(N,k)',
        exactFirstRequestShares=exact.tolist(),exactShareBottom20Percent=float(exact[:20].sum()),
        exactShareTop20Percent=float(exact[-20:].sum()),expectedInclusionPerSeller=k/n,seeds=[])
    for seed in (137,271,811):
        selected,included=sample_counts(n,k,draws,seed)
        result['seeds'].append(dict(seed=seed,chosen=selected.tolist(),included=included.tolist(),
            shareBottom20Percent=float(selected[:20].sum()/draws),shareTop20Percent=float(selected[-20:].sum()/draws),
            minInclusion=float(included.min()/draws),maxInclusion=float(included.max()/draws),
            maxAbsoluteChoiceProbabilityError=float(np.max(np.abs(selected/draws-exact)))))
    assert abs(exact.sum()-1)<1e-12
    assert all(sum(x['chosen'])==draws and sum(x['included'])==draws*k for x in result['seeds'])
    result['interpretation']='Uniform offer inclusion does not make deterministic lowest-ID equal-quote selection neutral. This is a counterexample to seller neutrality, not a measured attribution of full-world outcomes. Incumbency and finite stocks change realized shares; the first-request ledger can retain this bias even when fallback sales go elsewhere.'
    result['candidateRepairNotImplemented']='Use a stable role-specific buyer/tick/seller hash to rank exact ties, with permutation and checkpoint tests. Changing tie priority is a behavior treatment and must not be silently substituted into the frozen experiment.'
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ('seeds','exactFirstRequestShares')}))


if __name__=='__main__':main()
