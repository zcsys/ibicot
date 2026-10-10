"""Full-population, one-year regression audit. Run with ./run.sh's PYTHONPATH.

Writes monthly summaries and a machine-readable final report under stats/.
This is deliberately separate from the small default test suite.
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from economy.core import model as M
from economy.core.state import reset_world, T0P
from economy.kernel.tick import tick
from economy.server.runtime import stats_row


def run(output):
    cfg, w = reset_world({})
    n, lc = cfg['t2FirmCount'], int(w.t2LineCount)
    products = w.t2LineProduct[:lc].astype(int)
    complexities = np.array([p['complexity'] for p in M.T2_PRODUCTS])[products]
    t1_footprints = np.array([cfg['footprint'][M.complexity(p)] for p in M.PRODUCTS])
    t2_footprints = np.array([cfg['footprint'][int(c)] for c in complexities])
    line_firms = w.t2LineFirm[:lc].astype(int)

    def cash():
        return float(w.t0Cash.sum() + w.t1Cash.sum() + w.t2Cash[:n].sum())

    def equity():
        e0 = (w.t0Cash + cfg['t0License'] + cfg['t0Reserve']
              + np.array([len(p['elements']) * cfg['t0Machinery'] for p in T0P])
              + (w.t0Inv * w.t0InvBasis).reshape(M.N0, M.NE).sum(1))
        e1 = (w.t1Cash + w.t1EqBook + cfg['t1License']
              + (w.raw * w.rawBasis).reshape(M.N1, M.NE).sum(1)
              + (w.t1Fin * w.t1FinBasis).reshape(M.N1, M.NP).sum(1))
        e2 = (w.t2Cash[:n] + w.t2EqBook[:n] + cfg['t2License']
              + (w.t2Raw * w.t2RawBasis).reshape(M.N2_FIRMS, M.NE)[:n].sum(1)
              + (w.t2T1Raw * w.t2T1Basis).reshape(M.N2_FIRMS, M.NP)[:n].sum(1)
              + np.bincount(line_firms, weights=w.t2Fin[:lc] * w.t2FinBasis[:lc], minlength=n))
        return [e0, e1] + [e2[complexities == c] for c in (3, 4, 5)]

    initial = equity()
    start = time.monotonic()
    max_cash_error = 0.
    max_occupancy = {'T1': 0., 'T2': 0.}
    totals = {'orders': 0, 'filledOrders': 0, 'activeQuantity': 0., 'fulfilledQuantity': 0.}
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'monthly.jsonl').open('w') as log:
        for t in range(1, 361):
            before = cash()
            state = tick(w, cfg, t)
            residual = abs(cash() - before - state['distributorPayments'] + state['costSinks'] + state['equipmentSinks'])
            max_cash_error = max(max_cash_error, residual)
            assert residual < .001, (t, 'cash conservation', residual)
            for name in ('t0Inv', 'raw', 't1Fin', 't2Raw', 't2T1Raw', 't2Fin',
                         't0Cash', 't1Cash', 't2Cash'):
                a = getattr(w, name)
                assert np.isfinite(a).all() and (a >= -1e-8).all(), (t, name)
                if 'Cash' not in name and name != 't0Inv':
                    assert np.equal(a, np.floor(a)).all(), (t, 'fractional goods', name)
            assert (w.t0Sold % cfg['minWholesaleLot'] == 0).all()
            for prices in (w.t0Price[np.isfinite(w.t0Price)],
                           w.t1Price[w.t1Operates != 0], w.t2Price[:lc]):
                assert np.isfinite(prices).all() and (prices >= .01).all() and (prices <= M.MAX_UNIT_PRICE).all()
            for name in ('t0Rel', 't1Rel', 't2Rel'):
                a = getattr(w, name)
                assert np.isfinite(a).all() and (a >= 0).all() and (a <= 1).all(), (t, name)
            space1 = (w.raw.reshape(M.N1, M.NE).sum(1) + w.t1Fin.reshape(M.N1, M.NP).sum(1)
                      + w.t1Operates.reshape(M.N1, M.NP) @ t1_footprints)
            space2 = (w.t2Raw.reshape(M.N2_FIRMS, M.NE)[:n].sum(1)
                      + w.t2T1Raw.reshape(M.N2_FIRMS, M.NP)[:n].sum(1)
                      + np.bincount(line_firms, weights=w.t2Fin[:lc] + t2_footprints, minlength=n))
            for tier, space in (('T1', space1), ('T2', space2)):
                max_occupancy[tier] = max(max_occupancy[tier], float(space.max()))
                assert (space <= cfg['storage']).all(), (t, tier, 'storage', space.max())
            np.testing.assert_array_equal(w.marketPotential, w.marketActive + w.marketPriceLost)
            np.testing.assert_array_equal(w.marketActive, w.marketFulfilled + w.marketStockUnmet)
            q, f = w.distributorLastQ, w.distributorLastFulfilled
            assert (f <= q).all()
            assert state['fulfilledOrders'] == int(((q > 0) & (f == q)).sum())
            assert state['activeOrders'] == int((q > 0).sum())
            totals['orders'] += state['activeOrders']
            totals['filledOrders'] += state['fulfilledOrders']
            totals['activeQuantity'] += float(w.marketActive.sum())
            totals['fulfilledQuantity'] += float(w.marketFulfilled.sum())
            if t % 30 == 0:
                row = stats_row(w, cfg, t, t // 30)
                row['maxCashResidual'] = max_cash_error
                log.write(json.dumps(row) + '\n')
                log.flush()
                print(f'tick {t}/360, {time.monotonic() - start:.1f}s, cash residual ${max_cash_error:.8f}', flush=True)
    groups = {}
    for name, final, baseline in zip(('T0', 'T1', 'C3', 'C4', 'C5'), equity(), initial):
        groups[name] = {'firms': len(final), 'equityROI_pct': float((final.sum() / baseline.sum() - 1) * 100),
                        'individualROI_percentiles': np.percentile((final / baseline - 1) * 100, [0, 10, 50, 90, 100]).tolist()}
    report = {'ticks': 360, 'seed': cfg['seed'], 'config': cfg, 'seconds': time.monotonic() - start,
              'maxCashResidual': max_cash_error, 'maxStorageOccupancy': max_occupancy,
              'groups': groups, 'totals': totals,
              'fullOrderRate': totals['filledOrders'] / totals['orders'],
              'quantityFillRate': totals['fulfilledQuantity'] / totals['activeQuantity'],
              'finalPrices': {'T0': float(np.nanmean(w.t0Price)), 'T1': float(np.nanmean(w.t1Price)),
                              **{f'C{c}': float(w.t2Price[:lc][complexities == c].mean()) for c in (3, 4, 5)}},
              'manufacturersWithNoSales': int((w.t2LastSaleTick[:n] == 0).sum()),
              'invariants': 'passed every tick'}
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('stats/review-fixes-2026-10-10'))
    run(parser.parse_args().output)
