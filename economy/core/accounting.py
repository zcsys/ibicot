"""Posted company P&L and vectorized allocation of company-period items.

Sales/COGS remain line ledgers. Switching transfers are posted at their cash
transaction sites; rent is posted by settlement. No earnings value is inferred
from equity. Company-period items are shared equally by installed lines.
"""
import numpy as np
from . import model as M


def firm_count(cfg, tier):
    return {'t0': M.N0, 't1': M.N1, 't2': cfg['t2FirmCount']}[tier]


def line_counts(world, cfg, tier):
    if tier == 't0':
        return np.isfinite(world.t0Price.reshape(M.N0, M.NE)).sum(axis=1)
    if tier == 't1':
        return world.t1Operates.reshape(M.N1, M.NP).sum(axis=1)
    return world.t2FirmLineCount[:cfg['t2FirmCount']]


def allocate_to_lines(world, cfg, tier, amounts):
    per_line = amounts / np.maximum(line_counts(world, cfg, tier), 1)
    if tier == 't0':
        return (np.isfinite(world.t0Price.reshape(M.N0, M.NE)) * per_line[:, None]).ravel()
    if tier == 't1':
        return (world.t1Operates.reshape(M.N1, M.NP) * per_line[:, None]).ravel()
    return per_line[world.t2LineFirm[:int(world.t2LineCount)]]


def company_earnings(world, cfg, tier):
    """Independently posted income less expenses, per company, for this tick."""
    n = firm_count(cfg, tier)
    if tier == 't2':
        lc = int(world.t2LineCount)
        gross = np.bincount(world.t2LineFirm[:lc],
            weights=world.t2Revenue[:lc] - world.t2COGS[:lc], minlength=n)
    else:
        gross = (getattr(world, tier + 'Revenue') - getattr(world, tier + 'COGS')).reshape(n, -1).sum(axis=1)
    net = gross + getattr(world, tier + 'SwitchingIncome')[:n] - getattr(world, tier + 'SwitchingExpense')[:n]
    if tier != 't0':
        net -= getattr(world, tier + 'RentCharge')[:n]
    return net


def finalize_net_earnings(world, cfg):
    """Finalize posted net earnings and update production transfer forecasts.

    The EMA predicts switching net income for the NEXT tick's planning. Actual
    Price learning retains line sales minus COGS; period postings affect only
    financial reporting and the production forecast.
    """
    totals = {}
    for tier in ('t0', 't1', 't2'):
        n = firm_count(cfg, tier)
        transfers = getattr(world, tier + 'SwitchingIncome')[:n] - getattr(world, tier + 'SwitchingExpense')[:n]
        forecast = getattr(world, tier + 'SwitchingNetEMA')[:n]
        forecast += cfg['alpha'] * (transfers - forecast)
        totals[tier + 'NetEarnings'] = float(company_earnings(world, cfg, tier).sum())
    world.netEarningsAvailable = True
    return totals
