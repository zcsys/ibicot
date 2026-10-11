"""Show the industrial single-supplier restriction excludes the confirmed fill rule."""
import argparse
import itertools
import json
import math
from pathlib import Path
import numpy as np
from .solvers import industry


def example():
    # One output consumes one input; no other constraints bind. Quotes put the
    # unconstrained maxima at ten and eight outputs respectively. These are
    # derived-demand quantities, not consumer utility or an assumed T1 lot.
    prices = np.array([[20 * math.exp(-1), 20 * math.exp(-.8)]])
    stocks = np.array([[2., 20.]])
    value = lambda q: 200 * (1 - math.exp(-q / 10))
    desired = [max(range(21), key=lambda q: value(q) - q*p) for p in prices[0]]
    assert desired == [10, 8]
    user_allocation = [2, 6]
    # Independently enumerate all purchase quantities, permitting split fills.
    best = max(itertools.product(range(3), range(21)),
        key=lambda x: value(sum(x)) - float(np.dot(prices[0], x)) if sum(x)<=20 else -math.inf)
    assert list(best) == user_allocation
    args = (np.zeros(1), np.ones(1), np.ones(1), np.ones(1), np.full(1, 20.),
        20., prices, stocks, np.array([2]), np.array([-1]), np.zeros(1),
        np.zeros(1, dtype=np.int64), 20, 0., 20., 10., 0., 1000., 0.)
    r1 = industry(*args)
    assert r1[0].tolist() == [1] and r1[1].tolist() == [8] and r1[3] == 8
    r1_goods = float(8 * prices[0, 1])
    split_goods = float(np.dot(prices[0], user_allocation))
    assert split_goods < r1_goods
    return dict(status='verified',desiredAtEachQuote=desired,quotes=prices[0].tolist(),
        stock=stocks[0].tolist(),userFallbackAllocation=user_allocation,
        independentSplitOracle=list(best),r1Allocation=[0,8],plannedOutput=8,
        r1GoodsCost=r1_goods,splitGoodsCost=split_goods,savings= r1_goods-split_goods,
        interpretation='The confirmed fallback rule buys two cheap units and six at the next quote. Historical R1 industry only allows one supplier per ingredient and buys all eight from B. That restriction excludes the requested split behavior and a strictly cheaper feasible basket. This one-input witness does not establish a multi-input algorithm with shared cash or fixed fees.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();data=example()
    with args.output.open('x') as f:json.dump(data,f,indent=2);f.write('\n')
    print(json.dumps(data))


if __name__=='__main__':main()
