"""Static event contracts checked before optional continuation pruning.

State-dependent accounting/feasibility still belongs to the ordinary ledger.
Funding caps are generated endogenously and are checked when each order executes.
"""
import math
from .quantity_value import LinearQuantityValue
from .phase_ledger import Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,Rent,EndTick,_integer


def validate_calendar(company,initial,scenario):
    n=len(initial.held);nl=len(company.lines)
    quotes=initial.quotes
    book=None if initial.book is None else (initial.book.label,initial.book.quote)
    phases=set(initial.completed_phases);rented=initial.rent_settled
    if len(scenario.input_values)!=n or len(scenario.finished_values)!=nl:
        raise ValueError('invalid horizon boundary')
    if any(not isinstance(table,LinearQuantityValue) and (not table or any(not math.isfinite(v) for v in table)) for table in (*scenario.input_values,*scenario.finished_values)):
        raise ValueError('missing or invalid terminal value table')
    for event in scenario.events:
        if not isinstance(event.label,str) or not event.label:raise ValueError('event requires a label')
        if rented and isinstance(event,(Purchase,OpenBook,SettleBook,SetQuotes)):
            raise ValueError('trading after rent requires a new tick')
        if type(event) is Purchase:
            if event.label in phases:raise ValueError('company purchasing phase already completed this tick')
            phases.add(event.label)
            if (event.overhead_timing not in ('before','after') or len(event.offers)!=len(event.reliability)
                    or len(set(event.active_lines))!=len(event.active_lines)
                    or any(not _integer(i) or i>=nl for i in event.active_lines)):
                raise ValueError('invalid purchase event dimensions/timing')
            if any(not math.isfinite(x) or x<0 for x in (event.rent_bill,event.rent_threshold,event.fee_unit_cost,event.fee_multiple)):
                raise ValueError('invalid purchase fee/rent parameters')
            if any(not math.isfinite(x) for x in event.reliability):raise ValueError('nonfinite supplier reliability')
            if event.frozen_overhead is not None and (event.overhead_timing != 'before' or isinstance(event.frozen_overhead,bool) or not math.isfinite(event.frozen_overhead)):
                raise ValueError('invalid frozen phase overhead')
            seen=set()
            for offer in event.offers:
                if (not _integer(offer.material) or offer.material>=n or not _integer(offer.supplier)
                        or not _integer(offer.stock) or not _integer(offer.lot,1)
                        or not math.isfinite(offer.price) or offer.price<=0):raise ValueError('invalid offer')
                key=(offer.material,offer.supplier)
                if key in seen:raise ValueError('duplicate supplier stock for one input')
                seen.add(key)
        elif type(event) is OpenBook:
            if book is not None:raise ValueError('overlapping sales book')
            book=(event.label,quotes)
        elif isinstance(event,SettleBook):
            if book is None or book[0]!=event.label or len(event.demand)!=nl:raise ValueError('missing/mismatched sales book')
            if any(not _integer(q) for q in event.demand) or not math.isfinite(event.fee_income) or event.fee_income<0:
                raise ValueError('invalid sale demand or fee income')
            if isinstance(event,SharedSettleBook):
                flat=tuple(i for group in event.groups for i in group)
                if not event.groups or any(not g for g in event.groups) or any(not _integer(i) for i in flat) or sorted(flat)!=list(range(nl)):
                    raise ValueError('shared sales groups must partition installed lines')
                for group in event.groups:
                    order=sorted(group,key=lambda i:(book[1][i],i))
                    for left,right in zip(order,order[1:]):
                        if event.demand[left]<event.demand[right] or (book[1][left]==book[1][right] and event.demand[left]!=event.demand[right]):
                            raise ValueError('shared demand must be consistent with frozen quotes')
            book=None
        elif type(event) is SetQuotes:
            if len(event.quotes)!=nl or any(not math.isfinite(p) or p<=0 for p in event.quotes):raise ValueError('invalid new quotes')
            quotes=event.quotes
        elif type(event) is Rent:
            if rented or book is not None:raise ValueError('duplicate rent or unsettled sales book at billing')
            if any(not math.isfinite(x) or x<0 for x in (event.bill,event.threshold)):raise ValueError('invalid rent terms')
            rented=True
        elif type(event) is EndTick:
            if book is not None:raise ValueError('unsettled phase book at tick end')
            if not math.isfinite(event.alpha) or not 0<=event.alpha<=1:raise ValueError('invalid transfer EMA alpha')
            phases=set();rented=False
        else:raise ValueError('unsupported phase event')
    if book is not None:raise ValueError('unsettled sales book at horizon boundary')
