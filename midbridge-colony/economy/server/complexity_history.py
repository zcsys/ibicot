"""Full-run annual complexity trends, accumulated from every simulation tick."""
import numpy as np
from ..core import model as M


def company_counts(world):
    operates = world.t1Operates.reshape(-1, M.NP)
    c1 = np.array([p['complexity'] for p in M.PRODUCTS])
    lc = int(world.t2LineCount)
    c2 = np.array([p['complexity'] for p in M.T2_PRODUCTS])[world.t2LineProduct[:lc]]
    return {**{c: int(np.any(operates[:, c1 == c], axis=1).sum()) for c in (1, 2)},
            **{c: int(np.unique(world.t2LineFirm[:lc][c2 == c]).size) for c in (3, 4)}}


def accumulate(history, tick, rows, counts, year_ticks):
    """Ratios of period totals; company-ticks handle changing installed populations."""
    year = (tick - 1) // year_ticks
    if not history or history[-1]['year'] != year:
        history.append({'year': year, 'startTick': tick, 'tick': tick, 'ticks': 0,
                        'bands': {str(c): dict(net=0., revenue=0., sold=0., companyTicks=0, available=True)
                                  for c in (1, 2, 3, 4)}})
    point = history[-1]
    if point['ticks'] and tick <= point['tick']:
        return
    point['tick'] = tick
    point['ticks'] += 1
    for c, band in point['bands'].items():
        band['companyTicks'] += counts[int(c)]
    for row in rows:
        band = point['bands'].get(str(row['complexity']))
        if band is None:
            continue
        band['revenue'] += row['revenue']
        band['sold'] += row['sold']
        if row['netEarnings'] is None:
            band['available'] = False
        else:
            band['net'] += row['netEarnings']


def project(history):
    return [dict(tick=p['tick'], startTick=p['startTick'], ticks=p['ticks'],
                 bands={c: {'netPerCompany': b['net']/b['companyTicks']
                           if b['companyTicks'] and b['available'] else None,
                           'price': b['revenue']/b['sold'] if b['sold'] else None}
                        for c, b in p['bands'].items()}) for p in history]
