"""Explicit terminal valuation in native quantity units; no extrapolation."""
from dataclasses import dataclass
from bisect import bisect_right
import math


@dataclass(frozen=True)
class LinearQuantityValue:
    """Caller-declared piecewise-linear values, never an inferred forecast."""
    quantities: tuple
    values: tuple

    def __post_init__(self):
        object.__setattr__(self,'quantities',tuple(self.quantities))
        object.__setattr__(self,'values',tuple(self.values))
        if (len(self.quantities)!=len(self.values) or len(self.quantities)<2
                or any(not math.isfinite(x) for x in (*self.quantities,*self.values))
                or self.quantities[0]<0 or any(b<=a for a,b in zip(self.quantities,self.quantities[1:]))):
            raise ValueError('invalid native quantity valuation')

    def at(self,quantity):
        if not math.isfinite(quantity) or not self.quantities[0]<=quantity<=self.quantities[-1]:
            raise ValueError('quantity outside declared terminal value domain')
        i=bisect_right(self.quantities,quantity)-1
        if quantity==self.quantities[i]:return self.values[i]
        a,b=self.quantities[i:i+2];x,y=self.values[i:i+2]
        return x+(y-x)*((quantity-a)/(b-a))


def value_at(table,quantity):
    if isinstance(table,LinearQuantityValue):return table.at(quantity)
    if not math.isfinite(quantity) or quantity<0 or quantity!=int(quantity):
        raise ValueError('fractional quantity requires explicit native terminal valuation')
    if len(table)<=quantity or any(not math.isfinite(v) for v in table):
        raise ValueError('missing or invalid terminal value table')
    return table[int(quantity)]
