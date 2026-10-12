"""Typed per-funding-frame scratch for deduplicated query answers."""
import math
import numpy as np
from .jit import njit
from .continuation_program import _array


@njit
def _request(selected,keys,lengths,requests,ordinal,count):
    for row in range(count):
        if lengths[row]!=len(selected):continue
        same=True
        for j in range(len(selected)):
            if keys[row,j]!=selected[j]:same=False;break
        if same:requests[ordinal]=row;return row,count
    lengths[count]=len(selected)
    for j in range(len(selected)):keys[count,j]=selected[j]
    requests[ordinal]=count
    return count,count+1


class QueryAnswers:
    @staticmethod
    def bytes_required(offers,inputs):
        return (offers+1)*(8*offers+8+8+1+8*inputs+16)

    def __init__(self,offers,inputs):
        if any(not isinstance(x,int) or isinstance(x,bool) for x in (offers,inputs)) or offers<0 or inputs<1:raise ValueError('invalid query scratch dimensions')
        n=offers+1;self.offers=offers;self.inputs=inputs;self.count=0
        self.keys=np.empty((n,offers),np.int64);self.lengths=np.zeros(n,np.int64);self.requests=np.full(n,-1,np.int64)
        self.ready=np.zeros(n,np.bool_);self.quantities=np.zeros((n,inputs),np.int64);self.values=np.zeros((n,2))

    def request(self,ordinal,selected):
        if not isinstance(ordinal,int) or isinstance(ordinal,bool) or not 0<=ordinal<=self.offers or self.requests[ordinal]>=0:raise ValueError('invalid or repeated query ordinal')
        if any(not isinstance(x,(int,np.integer)) or isinstance(x,(bool,np.bool_)) for x in selected):raise ValueError('invalid selected-offer identity')
        selected=tuple(int(x) for x in selected)
        if len(selected)>self.offers or tuple(sorted(set(selected)))!=selected or any(x<0 or x>=self.offers for x in selected):raise ValueError('invalid selected-offer key')
        row,count=_request(_array(selected,'<i8'),self.keys,self.lengths,self.requests,ordinal,self.count);self.count=int(count)
        return int(row),bool(self.ready[row])

    def store(self,row,quantities,goods,value):
        if not isinstance(row,int) or isinstance(row,bool) or not 0<=row<self.count or self.ready[row]:raise ValueError('invalid query answer slot')
        if len(quantities)!=self.inputs or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in quantities):raise ValueError('invalid query quantities')
        if not math.isfinite(goods) or goods<0 or not math.isfinite(value):raise ValueError('invalid query values')
        q=_array(quantities,'<i8');v=_array((goods,value),'<f8')
        self.quantities[row]=q;self.values[row]=v;self.ready[row]=True

    def answer(self,ordinal):
        if not isinstance(ordinal,int) or isinstance(ordinal,bool) or not 0<=ordinal<=self.offers:raise ValueError('invalid query ordinal')
        row=int(self.requests[ordinal])
        if row<0 or not self.ready[row]:raise ValueError('query answer not completed')
        return dict(quantities=tuple(int(q) for q in self.quantities[row]),goods=float(self.values[row,0]),conditionalValue=float(self.values[row,1]))

    @property
    def buffer_bytes(self):return sum(a.nbytes for a in (self.keys,self.lengths,self.requests,self.ready,self.quantities,self.values))
