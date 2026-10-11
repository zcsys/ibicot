"""Explicit tier-specific sell-side anchor ablation; other pricing rules remain."""
import argparse
import json
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K,numba as N
from . import run as R


if __name__=='__main__':
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--options',default='{}');a,_=p.parse_known_args()
    tiers=json.loads(a.options).get('disableAnchorTiers',['t0','t1','t2'])
    if any(t not in ('t0','t1','t2') for t in tiers):raise ValueError('Unknown anchor tier')
    original=K._market_going_rate
    def going_rate(prices,sales,markets,count):
        tier='t0' if count==M.NE else 't1' if count==M.NP else 't2'
        return np.zeros(count) if tier in tiers else original(prices,sales,markets,count)
    K._market_going_rate=going_rate;N._market_going_rate=going_rate
    R.main()
