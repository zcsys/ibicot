"""Bounded numeric records of completed continuation-v2 funding decisions."""
import numpy as np
from .continuation_program import _array
from .continuation_history import _intern


class FundingRecordLimit(ValueError):
    def __init__(self,diagnostics):super().__init__('funding record arena capacity exhausted');self.diagnostics=diagnostics


class FundingRecords:
    def __init__(self,*,max_nodes=65536,max_integers=262144,max_floats=262144):
        if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (max_nodes,max_integers,max_floats)):raise ValueError('positive funding record capacities required')
        self.parents=np.zeros(max_nodes,np.int64);self.io=np.zeros(max_nodes+1,np.int64);self.fo=np.zeros(max_nodes+1,np.int64)
        self.integers=np.empty(max_integers,np.int64);self.floats=np.empty(max_floats,np.float64)
        self.count=1;self.integer_count=0;self.float_count=0

    def diagnostics(self):
        return dict(nodes=self.count,integerValues=self.integer_count,floatValues=self.float_count,
            capacityNodes=len(self.parents),capacityIntegers=len(self.integers),capacityFloats=len(self.floats),
            bufferBytes=sum(a.nbytes for a in (self.parents,self.io,self.fo,self.integers,self.floats)))

    def _check(self,node):
        if not isinstance(node,int) or isinstance(node,bool) or not 0<=node<self.count:raise ValueError('invalid funding record node')

    def append(self,parent,event,detail):
        self._check(parent)
        if not isinstance(event,int) or isinstance(event,bool) or not 0<=event<2**63 or (parent and event<=self.integers[self.io[parent]]):raise ValueError('funding events must increase')
        iv,fv=encode_detail(event,detail)
        from numba.typed import List
        records=List();records.append((iv,fv))
        node,count,ic,fc,processed,ok,rn,ri,rf=_intern(parent,records,self.parents,self.io,self.fo,self.integers,self.floats,self.count,self.integer_count,self.float_count)
        if not ok:raise FundingRecordLimit(dict(**self.diagnostics(),requiredNodes=int(rn),requiredIntegers=int(ri),requiredFloats=int(rf)))
        self.count=int(count);self.integer_count=int(ic);self.float_count=int(fc)
        return int(node)

    def export(self,node):
        self._check(node);entries=[]
        while node:
            iv=self.integers[self.io[node]:self.io[node+1]];fv=self.floats[self.fo[node]:self.fo[node+1]]
            event,n,count=(int(x) for x in iv[:3]);cursor=3
            refs=tuple(int(x) for x in iv[cursor:cursor+n]);cursor+=n
            demands=tuple(int(x) for x in iv[cursor:cursor+n]);cursor+=n
            joint=tuple(int(x) for x in iv[cursor:cursor+n]);cursor+=n
            queries=[]
            for j in range(count):
                queries.append(dict(material=int(iv[cursor]),supplier=int(iv[cursor+1]),quantities=tuple(int(x) for x in iv[cursor+2:cursor+2+n]),goods=float(fv[1+2*j]),conditionalValue=float(fv[2+2*j])))
                cursor+=2+n
            entries.append((event,dict(rule='continuation-v2',referenceSuppliers=refs,referenceDemands=demands,jointQuantities=joint,jointGoods=float(fv[0]),quoteVectors=tuple(queries))))
            node=int(self.parents[node])
        return dict(reversed(entries))


def encode_detail(event,detail):
    if not isinstance(event,int) or isinstance(event,bool) or not 0<=event<2**63:raise ValueError('invalid funding event')
    if detail['rule']!='continuation-v2':raise ValueError('unsupported funding record rule')
    refs=detail['referenceSuppliers'];demands=detail['referenceDemands'];joint=detail['jointQuantities'];queries=detail['quoteVectors'];n=len(refs)
    if not n or len(demands)!=n or len(joint)!=n:raise ValueError('invalid funding record dimensions')
    integers=[event,n,len(queries),*refs,*demands,*joint];floats=[detail['jointGoods']]
    if any(x < -1 for x in refs) or any(x<0 for x in (*demands,*joint)):raise ValueError('invalid funding record quantity')
    for q in queries:
        if len(q['quantities'])!=n or not 0<=q['material']<n or q['supplier']<0 or any(x<0 for x in q['quantities']):raise ValueError('invalid funding query record')
        integers.extend((q['material'],q['supplier'],*q['quantities']));floats.extend((q['goods'],q['conditionalValue']))
    if any(floats[i]<0 for i in (0,*range(1,len(floats),2))):raise ValueError('negative funding goods cost')
    iv=_array(integers,'<i8').copy();fv=_array(floats,'<f8').copy()
    return iv,fv
