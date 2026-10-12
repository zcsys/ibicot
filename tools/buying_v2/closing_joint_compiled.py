"""Compiled joint-output upper bound with directed rounding and bounded work."""
import math
from collections import OrderedDict
import numpy as np
from .jit import njit
from .closing_cost_compiled import _pack


@njit
def up(value):
    return np.nextafter(value, np.inf)


@njit
def down(value):
    return np.nextafter(value, -np.inf)


@njit
def _bound(args, lo, hi, max_states):
    held, slots, material, price, order, recipe, capacity, yield_qty, conversion, old, quote, opening_cash, initial_cash, liabilities, weights, mass, demand, fee_income, inputs, terminal, finished_prefix = args
    minimum = held.copy();maximum = held.copy()
    base = error = prefix = 0.
    for i in range(len(material)):
        m = material[i]
        minimum[m] += lo[i];maximum[m] += hi[i]
        base = down(base+down(lo[i]*price[i]))
        top = hi[i]*price[i]
        prefix = up(prefix+up(top))
        if not np.isfinite(prefix):
            error = np.inf
        elif np.isfinite(error):
            # For finite positive values, this equals ulp except at the
            # greatest finite float, where infinity safely weakens the bound.
            allowance = up((up(top)-top)+(up(prefix)-prefix))
            error = up(error+allowance)
    for m in range(len(held)):
        if minimum[m] > slots[m]:return -np.inf, 0
        maximum[m] = min(maximum[m], slots[m])
    limits = capacity.copy()
    finished = old.copy()
    for r in range(len(capacity)):
        for m in range(len(held)):
            if recipe[r, m]:limits[r] = min(limits[r], maximum[m]//recipe[r, m])
        finished[r] += limits[r]*yield_qty[r]
    count = 1
    for limit in limits:
        if count > max_states//(limit+1):return np.inf, 0
        count *= limit+1
    best = -np.inf
    batches = np.zeros(len(capacity),dtype=np.int64)
    required = np.zeros(len(held),dtype=np.int64)
    units = np.zeros(len(capacity),dtype=np.int64)
    for ordinal in range(count):
        remainder = ordinal
        required[:] = 0
        valid = True
        for r in range(len(capacity)-1,-1,-1):
            batches[r] = remainder % (limits[r]+1)
            remainder //= limits[r]+1
            units[r] = batches[r]*yield_qty[r]
            for m in range(len(held)):
                amount = recipe[r,m]*batches[r]
                if amount > maximum[m]-required[m]:
                    valid = False
                elif valid:
                    required[m] += amount
        if not valid:continue
        lower = base
        for m in range(len(held)):
            missing = max(0, required[m]-minimum[m])
            for rank in range(len(order)):
                if missing == 0:break
                i = order[rank]
                if material[i] != m:continue
                take = min(missing, hi[i]-lo[i])
                lower = down(lower+down(take*price[i]));missing -= take
            if missing:raise AssertionError('output cap exceeds relaxed input supply')
        goods = max(0., down(lower-error)) if np.isfinite(error) else 0.
        if goods > opening_cash:continue
        cash = up(opening_cash-goods)
        valid = True
        for r in range(len(capacity)):
            expense = units[r]*conversion[r]
            if not np.isfinite(expense):
                valid = False;break
            cash = up(cash-expense)
        if not valid:continue
        weighted = 0.
        for s in range(len(weights)):
            sales = remaining_value = 0.
            for m in range(len(held)):
                remaining_value = up(remaining_value+inputs[s, m, maximum[m]-required[m]])
            for r in range(len(capacity)):
                stock = old[r]+units[r]
                sold = min(stock, demand[s, r])
                sales = up(sales+up(sold*quote[r]))
                remaining = stock-sold
                value = terminal[s, r, remaining]
                remaining_value = up(remaining_value+value)
            closing = up(up(cash+sales)+fee_income[s])
            value = up(up(up(closing-initial_cash)-liabilities)+remaining_value)
            term = up(weights[s]*value)
            weighted = up(weighted+term)
            if not np.isfinite(term) or not np.isfinite(weighted):
                weighted = np.inf;break
        value = up(up(weighted)/mass)
        best = max(best, value)
    return best, count



class BoundMemo:
    """Per-solve exact bounds, keyed by every consumed value and box endpoint."""
    def __init__(self,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:
            raise ValueError('positive joint-bound memo capacity required')
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


def bounder(problem, initial, state, posterior, *, neutral=False, max_states=4096, memo=None):
    if not isinstance(max_states,int) or isinstance(max_states,bool) or not 1<=max_states<=2**63-1:
        raise ValueError('positive int64 joint batch-state budget required')
    if memo is not None and not isinstance(memo,BoundMemo):
        raise ValueError('joint-bound memo type required')
    args = _pack(problem,initial,state,posterior,neutral=neutral)
    # Stock and lot constraints are already encoded in box endpoints. Fees,
    # basis, gates and funded caps are relaxed by this bound, never by execution.
    key = (problem.slots,state.held,tuple((o.material,o.price) for o in problem.offers),
           tuple((line.recipe,line.max_batches,line.output_qty,line.conversion) for line in problem.lines),
           state.finished,state.quotes,state.cash,initial.cash,state.arrears-initial.arrears,
           tuple((w,s.events[1].demand,0. if neutral else s.events[1].fee_income,s.input_values,s.finished_values) for w,s in posterior)) if memo is not None else None
    def bound(lo,hi,*,work_budget=None):
        if work_budget is not None and (not isinstance(work_budget,int) or isinstance(work_budget,bool) or work_budget<1):
            raise ValueError('positive joint evaluation work budget required')
        available_states=max_states if work_budget is None else min(max_states,(work_budget-1)//(1+len(posterior)))
        box_key=(key,tuple(lo),tuple(hi))
        cached=memo.get(box_key) if memo is not None else None
        if cached is not None:
            return dict(upperValue=cached,batchStates=0)
        value,count = _bound(args,np.asarray(lo,dtype=np.int64),np.asarray(hi,dtype=np.int64),available_states)
        # Never cache unavailable work-limited bounds or numerical infinity.
        if memo is not None and math.isfinite(value):memo.put(box_key,float(value))
        return dict(upperValue=float(value),batchStates=int(count))
    return bound
