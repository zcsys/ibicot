"""Compact bounded terminal-result records; selected states are replayed."""
import math
import numpy as np
from .jit import njit


@njit
def quantity_value(quantity,table,offsets,values,modes=None,knots=None):
    a=offsets[table];b=offsets[table+1]
    if not math.isfinite(quantity) or quantity<0:raise ValueError('invalid terminal quantity')
    if modes is None or modes[table]==0:
        if quantity!=math.floor(quantity) or quantity>=b-a:raise ValueError('missing integer terminal value')
        return values[a+int(quantity)]
    if b-a<2 or quantity<knots[a] or quantity>knots[b-1]:raise ValueError('quantity outside declared terminal value domain')
    left=a;right=b
    while left<right:
        mid=(left+right)//2
        if knots[mid]<=quantity:left=mid+1
        else:right=mid
    i=left-1
    if quantity==knots[i]:return values[i]
    return values[i]+(values[i+1]-values[i])*((quantity-knots[i])/(knots[i+1]-knots[i]))


@njit
def terminal_value(state,initial_cash,initial_arrears,scenario,width,offsets,values,modes=None,knots=None):
    if state[7]>=0:raise ValueError('unsettled sales book at horizon boundary')
    total=0.;start=scenario*width
    for m in range(len(state[1])):
        total+=quantity_value(state[1][m],start+m,offsets,values,modes,knots)
    start+=len(state[1])
    for m in range(len(state[3])):
        total+=quantity_value(state[3][m],start+m,offsets,values,modes,knots)
    return state[0][0]-initial_cash-(state[0][1]-initial_arrears)+total


class ResultLimit(ValueError):
    def __init__(self,diagnostics):super().__init__('terminal result arena capacity exhausted');self.diagnostics=diagnostics


class Results:
    def __init__(self,capacity=100000):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:raise ValueError('positive result capacity required')
        self.ids=np.empty((capacity,4),np.int64);self.values=np.empty(capacity);self.count=0

    def diagnostics(self):return dict(records=self.count,capacity=len(self.values),bufferBytes=self.ids.nbytes+self.values.nbytes)

    def append(self,scenario,policy,history,funding,value):
        fields=(scenario,policy,history,funding)
        if any(not isinstance(x,int) or isinstance(x,bool) or not 0<=x<2**63 for x in fields) or not math.isfinite(value):raise ValueError('invalid terminal result')
        if self.count==len(self.values):raise ResultLimit(dict(**self.diagnostics(),requiredRecords=self.count+1))
        row=self.count;self.ids[row]=fields;self.values[row]=value;self.count+=1
        return row

    def read(self,row):
        if not isinstance(row,int) or isinstance(row,bool) or not 0<=row<self.count:raise ValueError('invalid result row')
        return (*tuple(int(x) for x in self.ids[row]),float(self.values[row]))
