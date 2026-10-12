"""Native-unit production primitive for the pending fractional-state planner.

No quantity rescaling or fixed fractional remainder: float64 holdings retain the
same operation order as the real T2 phase. This primitive is not yet wired into
the integer continuation state or its terminal-value tables.
"""
import math
import numpy as np
from .jit import njit


@njit
def produce(held, basis, materials, ratios, cash, finished, finished_basis,
            output_qty, capacity, finished_slot, conversion, quote, overhead, margin_band):
    inventory=held.copy()
    possible=math.floor(min(capacity,max(0.,finished_slot-finished))/output_qty)
    input_cost=0.
    for j in range(len(materials)):
        m=materials[j];q=ratios[j]
        possible=min(possible,math.floor(inventory[m]/q))
        input_cost+=q*basis[m]
    possible=min(possible,math.floor(cash/(conversion*output_qty)))
    unit=input_cost/output_qty+conversion
    batches=0
    if possible>0 and unit<=quote+1e-9:
        margin=(quote-unit-overhead/(possible*output_qty))/max(quote,1e-9)
        factor=min(1.,max(0.,margin/margin_band))
        candidate=math.floor(possible*factor+.5)
        if candidate>0 and (quote-unit)*candidate*output_qty-overhead>=-1e-9:
            batches=candidate
    units=batches*output_qty
    if batches>0:
        for j in range(len(materials)):inventory[materials[j]]-=batches*ratios[j]
        cash-=units*conversion
        finished_basis=(finished*finished_basis+unit*units)/(finished+units)
        finished+=units
    return inventory,cash,finished,finished_basis,units,unit


def checked_produce(held,basis,materials,ratios,*,cash,finished,finished_basis,
                    output_qty,capacity,finished_slot,conversion,quote,overhead,margin_band):
    held=np.asarray(held,dtype=np.float64);basis=np.asarray(basis,dtype=np.float64)
    if held.ndim!=1 or basis.shape!=held.shape or not np.isfinite(held).all() or not np.isfinite(basis).all() or np.any(held<0) or np.any(basis<0):
        raise ValueError('invalid native input holdings/basis')
    if len(materials)!=len(ratios) or len(materials)==0:raise ValueError('invalid recipe dimensions')
    if any(isinstance(m,bool) or int(m)!=m or not 0<=m<len(held) for m in materials):raise ValueError('invalid material')
    if any(isinstance(q,bool) or not math.isfinite(q) or q<=0 or int(q)!=q for q in ratios):raise ValueError('invalid recipe quantity')
    values=(cash,finished,finished_basis,output_qty,capacity,finished_slot,conversion,quote,overhead,margin_band)
    if not all(math.isfinite(v) for v in values) or min(cash,finished,finished_basis,capacity,finished_slot)<0 or min(conversion,quote,margin_band,output_qty)<=0 or int(output_qty)!=output_qty:
        raise ValueError('invalid production parameters')
    return produce(held,basis,np.asarray(materials,dtype=np.int64),np.asarray(ratios,dtype=np.int64),
                   cash,finished,finished_basis,int(output_qty),capacity,finished_slot,conversion,quote,overhead,margin_band)
