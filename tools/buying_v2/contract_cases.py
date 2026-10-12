"""Executable D1/D2 alternatives; no production policy is selected here."""
from dataclasses import dataclass
from typing import Literal

Qualification = Literal['remaining', 'whole']


@dataclass(frozen=True)
class Delivery:
    supplier: int
    demand_at_quote: int
    delivered: int


def preference_after(incumbent: int, legs: tuple[Delivery, ...],
                     rule: Qualification) -> int:
    """Compare terminal remainder qualification with whole-quantity qualification.

    Quantities are already funded and executable. A cash-truncated request must
    be represented by its funded total before calling this diagnostic function.
    No mid-order preference updates occur; the original incumbent remains the
    fee recipient throughout. This is a fixture evaluator, not a basket solver.
    """
    if rule not in ('remaining', 'whole'):
        raise ValueError('unknown qualification rule')
    bought = 0
    winner = incumbent
    complete = False
    for leg in legs:
        if complete:
            raise ValueError('delivery after a completed order')
        if leg.supplier < 0 or leg.demand_at_quote < 0 or leg.delivered < 0:
            raise ValueError('invalid delivery')
        remaining = max(0, leg.demand_at_quote - bought)
        if leg.delivered > remaining:
            raise ValueError('delivery exceeds price-sensitive remaining demand')
        bought += leg.delivered
        complete = bought >= leg.demand_at_quote
        threshold = remaining if rule == 'remaining' else leg.demand_at_quote
        if leg.delivered > 0 and leg.delivered >= threshold:
            winner = leg.supplier
    return winner


def order_fee(incumbent: int, opening_stock: int, funded_bid: int,
              fee: float, legs: tuple[Delivery, ...]) -> float:
    """D2 proposal: one fee per product order using frozen incumbent availability.

    The caller derives funded_bid at the incumbent quote from pre-order cash,
    storage and lots, BEFORE observing supplier stock, without inflating a bid
    from another supplier's cheap quote. The formula is evaluated elsewhere.
    This function tests the settlement boundary, not that bid's economic model.
    """
    if opening_stock < 0 or funded_bid < 0 or fee < 0:
        raise ValueError('negative fee input')
    if incumbent < 0 or funded_bid == 0 or opening_stock < funded_bid:
        return 0.0
    return fee if any(x.delivered > 0 and x.supplier != incumbent for x in legs) else 0.0


def decision_examples():
    cases = {
        'A2_B6': (Delivery(1, 10, 2), Delivery(2, 8, 6)),
        'A2_B1_C2': (Delivery(1, 10, 2), Delivery(2, 8, 1), Delivery(3, 5, 2)),
        'partial_only': (Delivery(1, 10, 2),),
        'full_only': (Delivery(1, 8, 8),),
        'no_purchase': (Delivery(1, 8, 0),),
    }
    return {name: {
        'deliveries': [vars(x) for x in legs],
        'remainingPreference': preference_after(0, legs, 'remaining'),
        'wholePreference': preference_after(0, legs, 'whole'),
        'feeIfIncumbentAvailable': order_fee(0, 8, 8, 2., legs),
        'feeIfIncumbentShort': order_fee(0, 7, 8, 2., legs),
    } for name, legs in cases.items()}


if __name__ == '__main__':
    import json
    print(json.dumps(decision_examples(), indent=2))
