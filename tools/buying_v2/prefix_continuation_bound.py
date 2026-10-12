"""Optimistic continuation value after fixing an initial offer-allocation prefix.

Diagnostic primitive: does not select allocations or change planner traversal.
Remaining current offers and all future offers retain relaxed unlimited supply;
fees, production gates and shared-input competition remain relaxed.
"""
from dataclasses import replace
import math
from .continuation_bound import upper_value as continuation_upper
from .phase_ledger import Purchase, validate_state


def upper_value(company, initial, state, event, prefix, events, input_values,
                finished_values, *, neutral=False):
    validate_state(company, initial);validate_state(company, state)
    if not isinstance(event, Purchase) or len(prefix)>len(event.offers):
        raise ValueError('purchase and initial offer-allocation prefix required')
    held=list(state.held);paid=0.
    for offer,q in zip(event.offers,prefix):
        if (not isinstance(q,int) or isinstance(q,bool) or q<0 or q>offer.stock
                or offer.lot<1 or q%offer.lot or not 0<=offer.material<len(held)
                or not math.isfinite(offer.price) or offer.price<=0):
            raise ValueError('invalid allocation prefix')
        held[offer.material]+=q
        # Downward arithmetic understates mandatory payment, never overstates
        # its deduction from the relaxed cash available to the continuation.
        product=math.nextafter(q*offer.price,-math.inf) if q else 0.
        paid=math.nextafter(paid+product,-math.inf)
    if any(h>max(old,slot) for h,old,slot in zip(held,state.held,company.slots)):
        return math.inf
    cash=math.nextafter(state.cash-paid,math.inf)
    if not math.isfinite(cash) or cash<0:return math.inf
    relaxed=replace(state,cash=cash,held=tuple(held))
    try:validate_state(company,relaxed)
    except ValueError:return math.inf
    # Fixed offers cannot be purchased again in the current decision. Later
    # books remain as supplied (persistent-supply decrements are relaxed).
    remaining=replace(event,offers=event.offers[len(prefix):],
                      reliability=event.reliability[len(prefix):],funded_demands=())
    value=continuation_upper(company,initial,relaxed,(remaining,)+tuple(events),
        input_values,finished_values,neutral=neutral,include_costs=True)
    if not math.isfinite(value):return math.inf
    # Cover changed grouping of compulsory and remaining payment reductions;
    # the existing continuation envelope covers the future ledger arithmetic.
    scale=max(1.,abs(state.cash),abs(initial.cash),abs(paid),abs(value))
    cushion=(1e-9+1e-12*scale)*(len(event.offers)+len(prefix)+1)
    return math.nextafter(value+cushion,math.inf)
