"""Optimistic cash-return envelope for a supplied remaining event calendar.

Research primitive only: not yet used to prune the exhaustive oracle. Production,
procurement and rent costs are relaxed; physical sales-book timing is retained.
"""
import math
from .quantity_value import LinearQuantityValue
from fractions import Fraction
from .phase_ledger import (Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,
                           Rent,EndTick,validate_state)


def line_envelope(line,finished,held,prices,production,opportunities):
    # Fractional production, unlimited cheapest input supply, and independent
    # use of all owned inputs by each line form an optimistic relaxation.
    finished=Fraction(finished);held=tuple(Fraction(h) for h in held)
    production=Fraction(production)
    tranches=sorted(((Fraction(p),Fraction(q)) for q,p in opportunities),reverse=True)
    maximum=Fraction(min(sum(q for _,q in tranches),finished+production))
    for a,h,p in zip(line.recipe,held,prices):
        if a and not math.isfinite(p):
            maximum=min(maximum,Fraction(finished)+h*Fraction(line.output_qty,a))
    points={Fraction(0),maximum}
    cumulative=0
    for _,q in tranches:
        cumulative+=q;points.add(Fraction(min(cumulative,maximum)))
    points.add(Fraction(min(finished,maximum)))
    for a,h in zip(line.recipe,held):
        if a:points.add(min(maximum,Fraction(finished)+h*Fraction(line.output_qty,a)))
    best=Fraction(0)
    for quantity in points:
        remaining=quantity;revenue=Fraction(0)
        for price,cap in tranches:
            sold=min(remaining,cap);revenue+=sold*price;remaining-=sold
        made=max(Fraction(0),quantity-finished)
        cost=made*Fraction(line.conversion)
        for a,h,p in zip(line.recipe,held,prices):
            if a and math.isfinite(p):
                cost+=max(Fraction(0),Fraction(a,line.output_qty)*made-h)*Fraction(p)
        best=max(best,revenue-cost)
    return math.nextafter(float(best),math.inf)


def upper_value(company,initial,state,events,input_values,finished_values,*,neutral=False, include_costs=False,free_inputs=False):
    if free_inputs and not include_costs:raise ValueError('free-input relaxation requires cost envelope')
    try:
        value=_upper_value(company,initial,state,events,input_values,finished_values,neutral=neutral,include_costs=include_costs,free_inputs=free_inputs)
        return value if math.isfinite(value) else math.inf
    except OverflowError:
        return math.inf


def _upper_value(company,initial,state,events,input_values,finished_values,*,neutral=False, include_costs=False,free_inputs=False):
    validate_state(company,initial);validate_state(company,state)
    native=any(q!=int(q) for q in (*state.held,*state.finished,*company.slots,*(state.book.quantity if state.book else ())))
    n=len(company.lines)
    if len(input_values)!=len(state.held) or len(finished_values)!=n:return math.inf
    limits=tuple(max(h,s) for h,s in zip(state.held,company.slots))+tuple(max(q,h) for q,h in zip(company.finished_caps,state.finished))
    tables=tuple(input_values)+tuple(finished_values)
    terminal=[]
    for table,limit in zip(tables,limits):
        if isinstance(table,LinearQuantityValue):
            if table.quantities[0]>0 or table.quantities[-1]<limit:return math.inf
            # Global knot maximum bounds every interpolation in the domain.
            terminal.append(max(table.values))
        else:
            if native or len(table)<=limit or any(not math.isfinite(x) for x in table):return math.inf
            terminal.append(max(table[:int(limit)+1]))
    # Forgetting sales decrements is optimistic, and avoids greedily selling
    # stock now at a low quote when a future quote could be more valuable.
    possible=list(state.finished);quotes=state.quotes
    book=None if state.book is None else (state.book.label,state.book.quantity,state.book.quote)
    income=[];fees=[];terms=1
    prices=[math.inf]*len(state.held);production=[0]*n;opportunities=[[] for _ in range(n)]
    for event in events:
        terms+=1
        if isinstance(event,Purchase):
            if (any(not isinstance(i,int) or isinstance(i,bool) or not 0<=i<n for i in event.active_lines)
                    or len(set(event.active_lines))!=len(event.active_lines)):
                return math.inf
            if include_costs:
                for offer in event.offers:
                    if not 0<=offer.material<len(prices) or not math.isfinite(offer.price) or offer.price<=0:return math.inf
                    prices[offer.material]=0. if free_inputs else min(prices[offer.material],offer.price)
            for i in event.active_lines:
                line=company.lines[i]
                production[i]+=line.max_batches*line.output_qty
                possible[i]=max(possible[i],min(company.finished_caps[i],possible[i]+line.max_batches*line.output_qty))
            terms+=len(event.offers)+len(event.active_lines)
        elif isinstance(event,OpenBook):
            if book is not None:return math.inf
            book=(event.label,tuple(possible),quotes)
        elif isinstance(event,SettleBook):
            if (book is None or book[0]!=event.label or len(event.demand)!=n
                    or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in event.demand)
                    or not math.isfinite(event.fee_income) or event.fee_income<0):
                return math.inf
            # Shared residual demand can only reduce each line's sales relative
            # to independent min(demand, stock); deliberately relax that coupling.
            income.extend(min(q,s)*p for q,s,p in zip(event.demand,book[1],book[2]))
            for i,(q,s,p) in enumerate(zip(event.demand,book[1],book[2])):
                opportunities[i].append((min(q,s),p))
            if not neutral:
                income.append(event.fee_income);fees.append(event.fee_income)
            book=None;terms+=n
        elif isinstance(event,SetQuotes):
            if len(event.quotes)!=n or any(not math.isfinite(p) or p<=0 for p in event.quotes):return math.inf
            quotes=event.quotes
        elif isinstance(event,Rent):
            if any(not math.isfinite(x) or x<0 for x in (event.bill,event.threshold)):return math.inf
            # Cash minus arrears cannot increase from billing or paying rent.
        elif isinstance(event,EndTick):
            if book is not None or not math.isfinite(event.alpha) or not 0<=event.alpha<=1:return math.inf
        else:return math.inf
    if book is not None:return math.inf
    components=[state.cash,-initial.cash,initial.arrears,-state.arrears,*income,*terminal]
    if any(not math.isfinite(x) for x in components):return math.inf
    value=math.fsum(components)
    if include_costs:
        profits=[line_envelope(line,f,state.held,prices,count,sales)
                 for line,f,count,sales in zip(company.lines,state.finished,production,opportunities)]
        tightened=math.fsum([state.cash,-initial.cash,initial.arrears,-state.arrears,*profits,*fees,*terminal])
        value=min(value,tightened)
    # Deliberately conservative numerical cushion; never tighten a bound on the
    # strength of floating-point cancellation. Infinite envelopes do not prune.
    scale=max(1.,abs(initial.cash),abs(state.cash),math.fsum(abs(x) for x in components))
    return value+(1e-9+1e-12*scale)*(terms+len(limits)+1)
