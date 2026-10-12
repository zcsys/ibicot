"""Stable numeric partitions with views over the original branch sequence."""
import numpy as np
from .jit import njit


@njit
def _partition(ids,count):
    offsets=np.zeros(count+1,np.int64)
    for group in ids:offsets[group+1]+=1
    for group in range(count):offsets[group+1]+=offsets[group]
    cursor=offsets[:-1].copy();members=np.empty(len(ids),np.int64)
    for index in range(len(ids)):
        group=ids[index];members[cursor[group]]=index;cursor[group]+=1
    return offsets,members


class Groups:
    def __init__(self,branches,ids):
        if len(branches)!=len(ids):raise ValueError('group dimensions differ')
        count=0
        for group in ids:
            if not isinstance(group,(int,np.integer)) or isinstance(group,(bool,np.bool_)) or not 0<=group<=count:
                raise ValueError('group IDs must follow first appearance order')
            if group==count:count+=1
        self.branches=branches
        self.offsets,self.members=_partition(np.asarray(ids,dtype=np.int64),count)

    def __len__(self):return len(self.offsets)-1

    def __getitem__(self,index):
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(self):raise IndexError('invalid group index')
        return GroupView(self,int(self.offsets[index]),int(self.offsets[index+1]))


class GroupView:
    def __init__(self,groups,start,stop):self.groups=groups;self.start=start;self.stop=stop

    def __len__(self):return self.stop-self.start

    def __getitem__(self,index):
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(self):raise IndexError('invalid branch index')
        return self.groups.branches[int(self.groups.members[self.start+index])]

    def __iter__(self):
        for position in range(self.start,self.stop):yield self.groups.branches[int(self.groups.members[position])]
