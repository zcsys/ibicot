"""Capture actual T2 resources as solver workloads, without executing purchases.

Output quotes are deliberately an optimistic synthetic valuation envelope for
algorithm testing, not an adopted sales forecast. Fees are disabled explicitly
until the coupled funded-bid adapter is implemented; no production claim follows.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from economy.kernel.input_market import InputMarket
from economy.server.persistence import load_checkpoint
from .discovery import sample_distinct
from .industry_oracle import Problem, Offer, Line
from .industry_search import solve
from .industry_bounds import SearchLimit


from .industrial_adapter import company_problem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-nodes', type=int, default=20000)
    a = parser.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    cfg, tick, w, state = load_checkpoint(str(a.checkpoint))
    book = InputMarket(w, tick)
    overhead = K.production_line_overhead(w, cfg, 't2')
    selected = []
    product_ids = w.t2LineProduct[:int(w.t2LineCount)]
    for route in dict.fromkeys(p['demandGroup'] for p in M.T2_PRODUCTS):
        ids = [p['id'] for p in M.T2_PRODUCTS if p['demandGroup'] == route]
        lines = np.flatnonzero(np.isin(product_ids, ids))
        if not len(lines):
            continue
        # First/middle/last stable line is a declared coverage sample, not a
        # claim of statistical representativeness across company distributions.
        for pos in sorted(set((0, len(lines)//2, len(lines)-1))):
            line = int(lines[pos])
            firm = int(w.t2LineFirm[line])
            phase = M.T2_PRODUCTS[int(product_ids[line])]['complexity']
            if (firm, phase) not in selected:
                selected.append((firm, phase))
    rows = []
    for firm, phase in selected:
        p, identity = company_problem(w, cfg, tick, firm, phase, book, overhead, workload_values=True)
        name = f'firm-{firm}-phase-{phase}.json'
        (a.output/name).write_text(json.dumps(dict(identity=identity, problem=asdict(p)), indent=2)+'\n')
        started = time.perf_counter()
        row = dict(**identity, fixture=name, held=list(p.held), bounds=[x.max_batches for x in p.lines])
        try:
            result, stats = solve(p, a.max_nodes)
            row.update(status='exact', allocation=result[0].tolist(), outputs=result[1].tolist(), objective=result[3], **stats)
        except SearchLimit as exc:
            row.update(status='limit', reason=str(exc))
        row['elapsedMs'] = (time.perf_counter()-started)*1000
        rows.append(row)
        print(json.dumps(row), flush=True)
    manifest = dict(checkpoint=str(a.checkpoint.resolve()), tick=tick, seed=cfg['seed'],
                    checkpointHashes={suffix:hashlib.sha256(Path(str(a.checkpoint)+suffix).read_bytes()).hexdigest() for suffix in ('.npz','.json')},
                    maxNodes=a.max_nodes, cases=rows,
                    scope='Actual resources/offers, synthetic quote-times-output values, zero terminal values and fees. First case includes compilation. No world mutations or economic policy comparison.')
    (a.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
