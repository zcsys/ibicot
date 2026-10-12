"""Standalone cash-translation relaxation for repeated joint closing proofs.

Normalize both opening and initial cash to enough money for every box basket.
The resulting bound includes every production vector even when actual cash is
scarce. Translate its value with an explicit allowance for actual ledger and
posterior floating-point operations. This is a bound, never a funded decision.
"""
from dataclasses import replace
from fractions import Fraction
import math
from collections import OrderedDict
from .closing_joint_bound import bounder as joint_bounder


def _ceil(value):
    x=float(value)
    if not math.isfinite(x):raise OverflowError('nonfinite rounding scale')
    return math.nextafter(x,math.inf) if Fraction(x)<value else x



class ProfitMemo:
    """Bounded normalized upper values; caller cash and rounding are never cached."""
    def __init__(self,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:
            raise ValueError('positive normalized-profit memo capacity required')
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


def bounder(problem,initial,state,posterior,*,neutral=False,max_states=4096,memo=None,compiled=False):
    if not isinstance(max_states,int) or isinstance(max_states,bool) or max_states<1:
        raise ValueError('positive cash-relaxed batch budget required')
    if memo is not None and not isinstance(memo,ProfitMemo):raise ValueError('normalized-profit memo type required')
    if not isinstance(compiled,bool):raise ValueError('compiled bound flag must be boolean')
    engine=joint_bounder
    if compiled:
        from .closing_joint_compiled import bounder as engine
    key=(compiled,problem.slots,state.held,tuple((o.material,o.price) for o in problem.offers),
         tuple((line.recipe,line.max_batches,line.output_qty,line.conversion) for line in problem.lines),
         state.finished,state.quotes,
         tuple((w,s.events[1].demand,0. if neutral else s.events[1].fee_income,s.input_values,s.finished_values) for w,s in posterior))
    weights=tuple(Fraction(w) for w,_ in posterior)
    mass=Fraction(math.fsum(w for w,_ in posterior))
    if mass<=0 or any(w<=0 for w in weights):raise ValueError('positive posterior weights required')
    ratio=sum(weights,Fraction(0))/mass
    offset=Fraction(state.cash)-Fraction(initial.cash)-Fraction(state.arrears)+Fraction(initial.arrears)
    conversion=sum((Fraction(line.max_batches*line.output_qty)*Fraction(line.conversion) for line in problem.lines),Fraction(0))
    sales=sum((Fraction(old+line.max_batches*line.output_qty)*Fraction(quote) for old,line,quote in zip(state.finished,problem.lines,state.quotes)),Fraction(0))
    terminal=max(sum((max(abs(Fraction(v)) for v in table) for table in s.input_values+s.finished_values),Fraction(0)) for _,s in posterior)
    fees=max(Fraction(0) if neutral else Fraction(s.events[1].fee_income) for _,s in posterior)
    unavailable=dict(upperValue=math.inf,batchStates=0)
    def bound(lo,hi,*,work_budget=None):
        if work_budget is not None and (not isinstance(work_budget,int) or isinstance(work_budget,bool) or work_budget<1):
            raise ValueError('positive cash-relaxed work budget required')
        available=max_states if work_budget is None else min(max_states,(work_budget-1)//(1+len(posterior)))
        goods=sum((q*Fraction(o.price) for q,o in zip(hi,problem.offers)),Fraction(0))
        spent=0
        try:
            cash=_ceil(goods+conversion+1)
            normalized_initial=replace(initial,cash=cash,arrears=0.)
            normalized_state=replace(state,cash=cash,arrears=0.)
            box_key=(key,tuple(lo),tuple(hi))
            cached=memo.get(box_key) if memo is not None else None
            if cached is None:
                if available<1:return unavailable
                result=engine(problem,normalized_initial,normalized_state,posterior,
                              neutral=neutral,max_states=available)(lo,hi)
                if not math.isfinite(result['upperValue']):return result
                if memo is not None:memo.put(box_key,result['upperValue'])
            else:
                result=dict(upperValue=cached,batchStates=0)
            spent=result['batchStates']
            # M bounds the absolute sum of all value-relevant cash terms.
            # Twice M leaves room for accumulated rounding. The deliberately
            # generous operation count covers compensated sales summation too.
            magnitude=max(Fraction(1),abs(Fraction(state.cash))+abs(Fraction(initial.cash))+
                          abs(Fraction(state.arrears))+abs(Fraction(initial.arrears))+
                          goods+conversion+sales+terminal+fees+Fraction(cash))
            scale=_ceil(2*magnitude)
            operations=64+32*len(problem.lines)+4*len(state.held)+2*len(problem.offers)
            leaf_error=operations*Fraction(math.ulp(scale))
            if leaf_error>=magnitude:return dict(upperValue=math.inf,batchStates=spent)
            product_error=sum((Fraction(math.ulp(_ceil(w*2*magnitude))) for w in weights),Fraction(0))
            weighted_scale=_ceil(sum(weights,Fraction(0))*2*magnitude)
            reduction_error=2*Fraction(math.ulp(weighted_scale))
            quotient_scale=_ceil(sum(weights,Fraction(0))*2*magnitude/mass)
            error=leaf_error*ratio+(product_error+reduction_error)/mass+2*Fraction(math.ulp(quotient_scale))
            value=Fraction(result['upperValue'])+offset*ratio+error
            return dict(upperValue=math.nextafter(_ceil(value),math.inf),batchStates=result['batchStates'])
        except (OverflowError,ValueError):
            return dict(upperValue=math.inf,batchStates=spent)
    return bound
