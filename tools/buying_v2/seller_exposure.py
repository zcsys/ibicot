"""Read-only buyer snapshot counters, indexed by stable seller columns."""
from .jit import njit


@njit
def record_exposure(exposure, suppliers, stocks, demands, lot):
    for i in range(len(suppliers)):
        seller = suppliers[i]
        exposure[0, seller] += 1
        if demands[i] > 0:
            exposure[1, seller] += 1
            exposure[2, seller] += int(stocks[i] // lot * lot < demands[i])
