"""Two-book single-line upper bound with a common first production decision.

Unsupported calendars return infinity; this never restricts planner actions.
Future input costs use unlimited cheapest current-remaining/future offers, so
advance buffers, cash limits, gates, fees and inventory caps remain relaxed.
"""
import math
from .quantity_value import LinearQuantityValue
from collections import OrderedDict
from fractions import Fraction
from .continuation_bound import line_envelope
from .phase_ledger import Purchase,OpenBook,SettleBook,EndTick,validate_state


class BoundMemo:
    """Bounded per-solve cache of completed exact relaxed profits, never policies."""
    def __init__(self, capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:
            raise ValueError('positive shared-bound memo capacity required')
        self.capacity=capacity;self.data=OrderedDict()
        self.hits=self.misses=self.peak_entries=0

    def get(self,key):
        if key in self.data:
            self.hits+=1;self.data.move_to_end(key);return self.data[key]
        self.misses+=1;return None

    def put(self,key,value):
        self.data[key]=value
        if len(self.data)>self.capacity:self.data.popitem(last=False)
        self.peak_entries=max(self.peak_entries,len(self.data))


def bound(company,initial,state,event,prefix,posterior,*,max_first_batches,neutral=False,memo=None):
    validate_state(company,initial);validate_state(company,state)
    if memo is not None and not isinstance(memo,BoundMemo):raise ValueError('shared-bound memo type required')
    if not isinstance(max_first_batches,int) or isinstance(max_first_batches,bool) or max_first_batches<0:
        raise ValueError('explicit nonnegative first-batch work limit required')
    unavailable=dict(value=math.inf,firstBatchStates=0,scenarioEvaluations=0)
    if any(isinstance(t,LinearQuantityValue) for _,p in posterior for t in p.input_values+p.finished_values):return unavailable
    if any(q!=int(q) for q in (*state.held,*state.finished,*company.slots)):return unavailable
    if (len(company.lines)!=1 or state.book is not None or not isinstance(event,Purchase)
            or event.active_lines!=(0,) or len(prefix)>len(event.offers) or not posterior):return unavailable
    line=company.lines[0]
    if line.max_batches>max_first_batches:return unavailable
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
    paths=[]
    for weight,scenario in posterior:
        events=scenario.events
        # Exact supported structure: first book, optional tick boundary, second
        # purchase, second book. No shared-book allocation or quote changes.
        if len(events)==6 and type(events[2]) is EndTick:events=events[:2]+events[3:]
        if (len(events)!=5 or tuple(type(e) for e in events)!=(OpenBook,SettleBook,Purchase,OpenBook,SettleBook)
                or events[0].label!=events[1].label or events[3].label!=events[4].label
                or events[2].active_lines!=(0,)) :return unavailable
        a,b=events[1],events[4]
        if (len(a.demand)!=1 or len(b.demand)!=1 or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in (*a.demand,*b.demand))
                or any(not math.isfinite(x) or x<0 for x in (a.fee_income,b.fee_income))):return unavailable
        future=current.copy()
        if not add_prices(future,events[2].offers):return unavailable
        limits=tuple(max(h,s) for h,s in zip(held,company.slots))+tuple(max(q,h) for q,h in zip(company.finished_caps,state.finished))
        tables=scenario.input_values+scenario.finished_values
        if len(tables)!=len(limits) or any(len(t)<=n or any(not math.isfinite(v) for v in t) for t,n in zip(tables,limits)):return unavailable
        terminal=sum((Fraction(max(t[:n+1])) for t,n in zip(tables,limits)),Fraction(0))
        fees=Fraction(0) if neutral else Fraction(a.fee_income)+Fraction(b.fee_income)
        paths.append((Fraction(weight),a.demand[0],b.demand[0],future,terminal+fees))
    # Cash, arrears and compulsory prefix spend are an additive constant.
    # Cache exact relaxed profit before that offset and the caller's numerical
    # cushion, so different sunk costs never inherit another caller's value.
    key=(line,tuple(held),tuple(current),state.finished[0],state.quotes[0],
         tuple((w,d1,d2,tuple(prices),terminal) for w,d1,d2,prices,terminal in paths))
    offset=Fraction(state.cash)-Fraction(initial.cash)+Fraction(initial.arrears)-Fraction(state.arrears)-paid
    def finish(profit,states,evaluations):
        try:
            value=float(profit+offset)
            scale=max(1.,abs(state.cash),abs(initial.cash),abs(value),float(abs(paid)))
        except OverflowError:return unavailable
        if not math.isfinite(value):return unavailable
        value=math.nextafter(value+(1e-9+1e-12*scale)*(len(event.offers)+len(held)+20),math.inf)
        return dict(value=value,firstBatchStates=states,scenarioEvaluations=evaluations)
    if memo is not None:
        cached=memo.get(key)
        if cached is not None:return finish(cached,0,0)
    best=None;states=0;evaluations=0
    for batches in range(line.max_batches+1):
        states+=1;units=batches*line.output_qty
        cost=Fraction(units)*Fraction(line.conversion);left=[];feasible=True
        for required,h,price in zip(line.recipe,held,current):
            missing=max(0,required*batches-h)
            if missing and not math.isfinite(price):feasible=False;break
            if missing:cost+=missing*Fraction(price)
            left.append(max(0,h-required*batches))
        if not feasible:continue
        values=[]
        for weight,d1,d2,prices,terminal in paths:
            evaluations+=1
            sold=min(state.finished[0]+units,d1)
            remaining=state.finished[0]+units-sold
            later=line_envelope(line,remaining,left,prices,line.max_batches*line.output_qty,[(d2,state.quotes[0])])
            if not math.isfinite(later):return unavailable
            value=-cost+sold*Fraction(state.quotes[0])+Fraction(later)+terminal
            values.append(weight*value)
        value=sum(values,Fraction(0))/sum((p[0] for p in paths),Fraction(0))
        best=value if best is None else max(best,value)
    if best is None:return unavailable
    result=finish(best,states,evaluations)
    if memo is not None and math.isfinite(result['value']):memo.put(key,best)
    return result
