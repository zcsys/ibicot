"""Reproducible scaling probes; synthetic cases, not a full-population benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from .industry_oracle import Problem, Offer, Line
from .industry_search import solve
from .industry_bounds import SearchLimit


def case(capacity, suppliers):
    return Problem((0, 0), (0., 0.), (1., 1.), (capacity, capacity), 2.*capacity, 100.*capacity,
        tuple(Offer(m, s, float(2+s), capacity) for m in range(2) for s in range(suppliers)),
        (-1, -1), (0, 0), (0., 0.),
        (Line((1, 1), capacity, 1., 30., 0., tuple(30.*q for q in range(capacity+1)), 2.),),
        ((0.,)*(capacity+1), (0.,)*(capacity+1)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-nodes', type=int, default=100000)
    a = parser.parse_args()
    solve(case(1, 1))
    rows = []
    for capacity, suppliers in ((4, 2), (16, 3), (64, 3), (64, 6), (256, 6)):
        p = case(capacity, suppliers)
        start = time.perf_counter()
        row = dict(capacity=capacity, suppliersPerInput=suppliers, maxNodes=a.max_nodes)
        try:
            result, stats = solve(p, a.max_nodes)
            row.update(status='exact', objective=result[3], allocation=result[0].tolist(), **stats)
        except SearchLimit as error:
            row.update(status='limit', reason=str(error))
        row['elapsedMs'] = (time.perf_counter() - start)*1000
        rows.append(row)
    root = Path(__file__).parent
    output = dict(cases=rows, sourceHashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.py'))},
                  scope='Synthetic one-line two-input warm search only; no population-level suitability claim.')
    with a.output.open('x') as stream:
        json.dump(output, stream, indent=2)
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
