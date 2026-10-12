"""Versioned purchase observations, independent of selection and fee policy.

The kernel caller invokes record_order exactly once per buyer/product/phase.
Arrays contain only quotes actually requested (including a terminal zero
remainder), never every quote evaluated during discovery. No aggregate here is
labelled latent demand or causal stock loss. No world state is mutated.
"""
import numpy as np
from .jit import njit

SCHEMA_VERSION = 1
FIELDS = (
    'orders', 'offersObserved', 'requestLegs', 'initialQuoteQuantity',
    'terminalQuoteQuantity', 'remainingRequests', 'unitsBought',
    'terminalShortfall', 'feeOrders', 'feeAmount', 'firstAssignments',
    'preferenceChanges',
)


@njit
def record_order(totals, market, observed, demands, delivered, leg_count,
                 old_incumbent, new_incumbent, fee):
    """Reduce one validated trace into a caller-owned [market, field] array.

    Demand quantities are funded price-dependent totals before supplier stock
    caps. Existing purchases are subtracted only for each remaining request.
    terminalShortfall is max(terminal quote quantity - purchased, 0), without
    claiming that stock rather than cash, fees or selection caused the gap.
    Zero-leg orders have no observed request quantity; their order count remains.
    No-history ratios are computed as unavailable by consumers, never zero.
    """
    bought = 0
    requested = 0
    for i in range(leg_count):
        requested += max(0, demands[i] - bought)
        bought += delivered[i]
    totals[market, 0] += 1
    totals[market, 1] += observed
    totals[market, 2] += leg_count
    if leg_count:
        totals[market, 3] += demands[0]
        totals[market, 4] += demands[leg_count - 1]
        totals[market, 7] += max(0, demands[leg_count - 1] - bought)
    totals[market, 5] += requested
    totals[market, 6] += bought
    totals[market, 8] += int(fee > 0)
    totals[market, 9] += fee
    totals[market, 10] += int(old_incumbent < 0 and new_incumbent >= 0)
    totals[market, 11] += int(old_incumbent >= 0 and new_incumbent >= 0
                            and old_incumbent != new_incumbent)


def empty_totals(markets):
    return np.zeros((markets, len(FIELDS)), dtype=np.float64)


def schema():
    return dict(version=SCHEMA_VERSION, fields=list(FIELDS),
                orderIdentity=['tick', 'phase', 'buyer', 'product'],
                notes={
                    'initialQuoteQuantity': 'Funded total at the first actual request quote; includes no inferred retries.',
                    'terminalQuoteQuantity': 'Funded total at the last visited request quote, including zero remaining request.',
                    'remainingRequests': 'Sum of attempted remaining quantities; may exceed unique intention.',
                    'terminalShortfall': 'Terminal quote quantity minus bought, floored at zero; cause unclassified.',
                    'offersObserved': 'Discovery count, distinct from requests and reliability attempts.',
                    'preferenceChanges': 'Existing incumbent replaced; excludes first assignments.',
                    'availability': 'Not instrumented by this reducer; measured at actual checks by the eventual caller.',
                })
