"""Typed scalar control frames with explicit remaining object-reference slots.

The Python mapping view is transitional; it preserves search dispatch while
integer/float frame storage can be consumed by a later compiled driver.
"""
import math
import numpy as np

KINDS=('walk','choose','fund')
STAGES=('enter','groups','group-return','next','child-return','next-query','query-return','actual-return')
VALID_STAGES={'walk':('enter','groups','group-return'),'choose':('next','child-return'),'fund':('next-query','query-return','actual-return')}
INT_FIELDS=('kind','stage','index','next_group','cursor','query','offer','active_offer','active_slot','ownsBranches')
FLOAT_FIELDS=('mass','payment')
REF_FIELDS=('branches','groups','totals','leaves','frame','scratch','best','allocation','rangeProof')
ALL_FIELDS=INT_FIELDS+FLOAT_FIELDS+REF_FIELDS


class ControlStack:
    def __init__(self,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:raise ValueError('positive frame capacity required')
        self.capacity=capacity;self.depth=0;self.peak=0
        self.integers=np.zeros((capacity,len(INT_FIELDS)),np.int64);self.floats=np.zeros((capacity,len(FLOAT_FIELDS)))
        self.present=np.zeros((capacity,len(ALL_FIELDS)),np.bool_);self.generations=np.zeros(capacity,np.int64)
        self.refs=[[None]*len(REF_FIELDS) for _ in range(capacity)]

    def __len__(self):return self.depth

    def __getitem__(self,index):
        if index!=-1 or not self.depth:raise IndexError('only the active control frame can be selected')
        row=self.depth-1
        return Frame(self,row,int(self.generations[row]))

    def append(self,values):
        if self.depth==self.capacity:raise ValueError('control frame capacity exhausted')
        if any(k not in values for k in ('kind','stage','index')):raise ValueError('incomplete control frame')
        # Validate before any storage mutation.
        encoded={k:_encode(k,v,values['kind']) for k,v in values.items()}
        row=self.depth
        if self.generations[row]==2**63-1:raise ValueError('control generation exhausted')
        self.integers[row].fill(0);self.floats[row].fill(0);self.present[row].fill(False);self.refs[row]=[None]*len(REF_FIELDS)
        self.generations[row]+=1;self.depth+=1;self.peak=max(self.peak,self.depth)
        frame=self[-1]
        for key,value in encoded.items():frame._store(key,value)

    def pop(self):
        if not self.depth:raise IndexError('empty control stack')
        row=self.depth-1;self.refs[row]=[None]*len(REF_FIELDS);self.present[row].fill(False);self.depth-=1

    def diagnostics(self):
        return dict(capacity=self.capacity,activeFrames=self.depth,peakFrames=self.peak,
            scalarBufferBytes=self.integers.nbytes+self.floats.nbytes+self.present.nbytes+self.generations.nbytes,
            objectReferenceSlots=self.capacity*len(REF_FIELDS))


def _encode(key,value,kind):
    if key not in ALL_FIELDS:raise KeyError(key)
    if key=='kind':
        if value not in KINDS:raise ValueError('invalid frame kind')
        return KINDS.index(value)
    if key=='stage':
        if kind not in VALID_STAGES or value not in VALID_STAGES[kind]:raise ValueError('invalid frame stage')
        return STAGES.index(value)
    if key in ('query','ownsBranches'):
        if not isinstance(value,bool):raise ValueError('invalid frame flag')
        return int(value)
    if key in ('offer','active_offer') and value is None:return -1
    if key in INT_FIELDS:
        if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<2**63:raise ValueError('invalid frame integer')
    if key in FLOAT_FIELDS:
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):raise ValueError('invalid frame number')
        if float(value)!=value:raise ValueError('lossy frame number')
        return float(value)
    return value


class Frame:
    def __init__(self,stack,row,generation):self.stack=stack;self.row=row;self.generation=generation

    def _check(self):
        if self.row>=self.stack.depth or self.stack.generations[self.row]!=self.generation:raise ValueError('stale control frame')

    def _store(self,key,value):
        self._check();s=self.stack;r=self.row
        if key in INT_FIELDS:s.integers[r,INT_FIELDS.index(key)]=value
        elif key in FLOAT_FIELDS:s.floats[r,FLOAT_FIELDS.index(key)]=value
        else:s.refs[r][REF_FIELDS.index(key)]=value
        s.present[r,ALL_FIELDS.index(key)]=True

    def __getitem__(self,key):
        self._check();s=self.stack;r=self.row
        if key not in ALL_FIELDS or not s.present[r,ALL_FIELDS.index(key)]:raise KeyError(key)
        if key in INT_FIELDS:
            value=int(s.integers[r,INT_FIELDS.index(key)])
            if key=='kind':return KINDS[value]
            if key=='stage':return STAGES[value]
            if key in ('query','ownsBranches'):return bool(value)
            return None if key in ('offer','active_offer') and value==-1 else value
        if key in FLOAT_FIELDS:return float(s.floats[r,FLOAT_FIELDS.index(key)])
        return s.refs[r][REF_FIELDS.index(key)]

    def __setitem__(self,key,value):
        if key=='kind':raise ValueError('frame kind is immutable')
        self._store(key,_encode(key,value,self['kind']))

    def update(self,**values):
        encoded={k:_encode(k,v,self['kind']) for k,v in values.items()}
        if 'kind' in values:raise ValueError('frame kind is immutable')
        for key,value in encoded.items():self._store(key,value)

    def get(self,key,default=None):
        try:return self[key]
        except KeyError:return default
