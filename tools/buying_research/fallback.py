"""User-confirmed price-dependent fallback quantity rule, isolated from loyalty.

The caller supplies eligible offers in nondecreasing merchandise-price order.
This function does not choose which fee-bearing offer to accept or update a
preference. It plans quantities against the stock visible to this buyer.
"""
import numpy as np
from .jit import njit
from .solvers import demand_quantity


@njit
def price_fallback(latent, half, eta, rounding, prices, stock):
    """Return units per offer and remaining requests; -1 means not visited.

    The same rounding draw is used at every quote. This preserves the ordering
    of demand as price rises, rather than drawing a new quantity on each retry.
    No cash/fee restriction is imposed here; those are separate constraints.
    """
    allocation = np.zeros(len(prices), dtype=np.int64)
    requests = np.full(len(prices), -1, dtype=np.int64)
    bought = 0
    for i in range(len(prices)):
        total = demand_quantity(latent, half, eta, prices[i], rounding)
        remaining = max(0, total - bought)
        requests[i] = remaining
        if remaining == 0:
            break
        take = min(remaining, int(stock[i]))
        allocation[i] = take
        bought += take
        if bought >= total:
            break
    return allocation, requests
