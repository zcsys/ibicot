"""Bounded immutable action-prefix records for continuation search."""
import numpy as np
from .jit import njit
from .continuation_program import _array


@njit
def _append(parent,event,allocation,parents,events,offsets,values,count,used):
    for node in range(1,count):
        if parents[node]!=parent or events[node]!=event or offsets[node+1]-offsets[node]!=len(allocation):continue
        same=True
        for j in range(len(allocation)):
            if values[offsets[node]+j]!=allocation[j]:same=False;break
        if same:return node,count,used,True
    if count>=len(parents) or used+len(allocation)>len(values):return -1,count,used,False
    parents[count]=parent;events[count]=event;offsets[count]=used
    for j in range(len(allocation)):values[used+j]=allocation[j]
    used+=len(allocation);offsets[count+1]=used
    return count,count+1,used,True


class PolicyLimit(ValueError):
    def __init__(self,diagnostics):super().__init__('policy arena capacity exhausted');self.diagnostics=diagnostics


class PolicyArena:
    def __init__(self,*,max_nodes=65536,max_values=262144):
        if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (max_nodes,max_values)):raise ValueError('positive policy capacities required')
        self.parents=np.zeros(max_nodes,np.int64);self.events=np.full(max_nodes,-1,np.int64)
        self.offsets=np.zeros(max_nodes+1,np.int64);self.values=np.empty(max_values,np.int64)
        self.count=1;self.used=0

    def diagnostics(self):
        return dict(nodes=self.count,allocationValues=self.used,capacityNodes=len(self.parents),capacityValues=len(self.values),
            bufferBytes=sum(a.nbytes for a in (self.parents,self.events,self.offsets,self.values)))

    def _check(self,node):
        if not isinstance(node,int) or isinstance(node,bool) or not 0<=node<self.count:raise ValueError('invalid policy node')

    def append(self,parent,event,allocation):
        self._check(parent)
        if not isinstance(event,int) or isinstance(event,bool) or not 0<=event<2**63 or event<=self.events[parent]:raise ValueError('policy events must increase')
        if any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('invalid policy allocation')
        a=_array(allocation,'<i8')
        node,count,used,ok=_append(parent,event,a,self.parents,self.events,self.offsets,self.values,self.count,self.used)
        if not ok:raise PolicyLimit(dict(**self.diagnostics(),requiredNodes=self.count+1,requiredValues=self.used+len(a)))
        self.count=int(count);self.used=int(used)
        return int(node)

    def export(self,node):
        self._check(node);entries=[]
        while node:
            entries.append((int(self.events[node]),tuple(int(q) for q in self.values[self.offsets[node]:self.offsets[node+1]])))
            node=int(self.parents[node])
        return dict(reversed(entries))
