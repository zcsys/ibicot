"""Joint first production shared across future scenarios; optimistic recourse.

First-period material requirements are summed across installed lines. Future
lines independently reuse residual inputs, a relaxation rather than execution.
This standalone bound neither changes actions nor selects a production vector.
"""
import math
from .quantity_value import LinearQuantityValue
from fractions import Fraction
from .continuation_bound import line_envelope
from .phase_ledger import Purchase,OpenBook,SettleBook,EndTick,validate_state


from .shared_first_bound import BoundMemo
from itertools import product

def bound(company,initial,state,event,prefix,posterior,*,max_first_states,neutral=False,memo=None,recourse_memo=None):
    validate_state(company,initial);validate_state(company,state)
    if memo is not None and not isinstance(memo,BoundMemo):raise ValueError('shared-bound memo type required')
    if recourse_memo is not None and not isinstance(recourse_memo,BoundMemo):raise ValueError('recourse memo type required')
    if not isinstance(max_first_states,int) or isinstance(max_first_states,bool) or max_first_states<1:
        raise ValueError('explicit positive joint first-state work limit required')
    unavailable=dict(value=math.inf,firstBatchStates=0,scenarioEvaluations=0)
    if any(isinstance(t,LinearQuantityValue) for _,p in posterior for t in p.input_values+p.finished_values):return unavailable
    if any(q!=int(q) for q in (*state.held,*state.finished,*company.slots)):return unavailable
    if (len(company.lines)<2 or state.book is not None or not isinstance(event,Purchase)
            or event.active_lines!=tuple(range(len(company.lines))) or len(prefix)>len(event.offers) or not posterior):return unavailable
    lines=company.lines
    count=math.prod(line.max_batches+1 for line in lines)
    if count>max_first_states:return unavailable
    mass=math.fsum(w for w,_ in posterior)
    if not math.isfinite(mass) or mass<=0 or any(not math.isfinite(w) or w<=0 for w,_ in posterior):
        raise ValueError('positive posterior mass required')
    held=list(state.held);paid=Fraction(0)
    for offer,q in zip(event.offers,prefix):
        if (not isinstance(q,int) or isinstance(q,bool) or q<0 or q>offer.stock or offer.lot<1
                or q%offer.lot or not 0<=offer.material<len(held) or not math.isfinite(offer.price) or offer.price<=0):
            raise ValueError('invalid allocation prefix')
        held[offer.material]+=q;paid+=q*Fraction(offer.price)
    current=[math.inf]*len(held)
    def add_prices(prices,offers):
        for offer in offers:
            if not 0<=offer.material<len(prices) or not math.isfinite(offer.price) or offer.price<=0:return False
            prices[offer.material]=min(prices[offer.material],offer.price)
        return True
    if not add_prices(current,event.offers[len(prefix):]):return unavailable
    # A fully fixed ingredient has no remaining quote: only the purchased and
    # opening stock can support first output. Skip impossible batch ranges.
    first_limits=tuple(min([line.max_batches]+[held[m]//q for m,q in enumerate(line.recipe)
                      if q and not math.isfinite(current[m])]) for line in lines)
    paths=[]
    for weight,scenario in posterior:
        events=scenario.events
        # Exact supported structure: first book, optional tick boundary, second
        # purchase, second book. No shared-book allocation or quote changes.
        if len(events)==6 and type(events[2]) is EndTick:events=events[:2]+events[3:]
        if (len(events)!=5 or tuple(type(e) for e in events)!=(OpenBook,SettleBook,Purchase,OpenBook,SettleBook)
                or events[0].label!=events[1].label or events[3].label!=events[4].label
                or events[2].active_lines!=tuple(range(len(lines)))) :return unavailable
        a,b=events[1],events[4]
        if (len(a.demand)!=len(lines) or len(b.demand)!=len(lines) or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in (*a.demand,*b.demand))
                or any(not math.isfinite(x) or x<0 for x in (a.fee_income,b.fee_income))):return unavailable
        future=current.copy()
        if not add_prices(future,events[2].offers):return unavailable
        limits=tuple(max(h,s) for h,s in zip(held,company.slots))+tuple(max(q,h) for q,h in zip(company.finished_caps,state.finished))
        tables=scenario.input_values+scenario.finished_values
        if len(tables)!=len(limits) or any(len(t)<=n or any(not math.isfinite(v) for v in t) for t,n in zip(tables,limits)):return unavailable
        terminal=sum((Fraction(max(t[:n+1])) for t,n in zip(tables,limits)),Fraction(0))
        fees=Fraction(0) if neutral else Fraction(a.fee_income)+Fraction(b.fee_income)
        paths.append((Fraction(weight),a.demand,b.demand,future,terminal+fees))
    # Cash, arrears and compulsory prefix spend are an additive constant.
    # Cache exact relaxed profit before that offset and the caller's numerical
    # cushion, so different sunk costs never inherit another caller's value.
    key=(lines,tuple(held),tuple(current),state.finished,state.quotes,
         tuple((w,d1,d2,tuple(prices),terminal) for w,d1,d2,prices,terminal in paths))
    offset=Fraction(state.cash)-Fraction(initial.cash)+Fraction(initial.arrears)-Fraction(state.arrears)-paid
    def finish(profit,states,evaluations):
        try:
            value=float(profit+offset)
            scale=max(1.,abs(state.cash),abs(initial.cash),abs(value),float(abs(paid)))
        except OverflowError:return unavailable
        if not math.isfinite(value):return unavailable
        value=math.nextafter(value+(1e-9+1e-12*scale)*(len(event.offers)+len(held)+20)*(len(lines)+1),math.inf)
        return dict(value=value,firstBatchStates=states,scenarioEvaluations=evaluations)
    if memo is not None:
        cached=memo.get(key)
        if cached is not None:return finish(cached,0,0)
    best=None;states=0;evaluations=0
    for batches in product(*(range(limit+1) for limit in first_limits)):
        states+=1
        units=tuple(b*line.output_qty for b,line in zip(batches,lines))
        cost=sum((Fraction(q)*Fraction(line.conversion) for q,line in zip(units,lines)),Fraction(0))
        required=tuple(sum(line.recipe[m]*b for line,b in zip(lines,batches)) for m in range(len(held)))
        left=[];feasible=True
        for needed,h,price in zip(required,held,current):
            missing=max(0,needed-h)
            if missing and not math.isfinite(price):feasible=False;break
            if missing:cost+=missing*Fraction(price)
            left.append(max(0,h-needed))
        if not feasible:continue
        values=[]
        for weight,d1,d2,prices,terminal in paths:
            evaluations+=1
            value=-cost+terminal
            for r,line in enumerate(lines):
                evaluations+=1
                sold=min(state.finished[r]+units[r],d1[r])
                remaining=state.finished[r]+units[r]-sold
                # Each later line gets independent access to residual inputs.
                # This deliberately relaxes shared inputs in recourse only.
                # Exact immutable inputs to line_envelope; caller offsets,
                # posterior weighting and shared first costs remain outside.
                recourse_key=(line,remaining,tuple(left),tuple(prices),line.max_batches*line.output_qty,((d2[r],state.quotes[r]),))
                later=recourse_memo.get(recourse_key) if recourse_memo is not None else None
                if later is None:
                    later=line_envelope(line,remaining,left,prices,line.max_batches*line.output_qty,[(d2[r],state.quotes[r])])
                    if recourse_memo is not None and math.isfinite(later):recourse_memo.put(recourse_key,later)
                # Retain the existing evaluation charge even for a cache hit.

                if not math.isfinite(later):return unavailable
                value+=sold*Fraction(state.quotes[r])+Fraction(later)
            values.append(weight*value)
        value=sum(values,Fraction(0))/sum((p[0] for p in paths),Fraction(0))
        best=value if best is None else max(best,value)
    if best is None:return unavailable
    result=finish(best,states,evaluations)
    if memo is not None and math.isfinite(result['value']):memo.put(key,best)
    return result
