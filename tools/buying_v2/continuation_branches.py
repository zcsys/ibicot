"""Bounded numeric branch sequences for arena-backed search."""
import numpy as np
from .continuation_arena import ArenaResident


class BranchRows:
    def __init__(self,arena,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<0:raise ValueError('invalid branch sequence capacity')
        self.arena=arena;self.rows=np.empty((capacity,4),np.int64);self.count=0

    def __len__(self):return self.count

    def append(self,branch):
        scenario,resident,policy=branch
        for value in (scenario,policy):
            if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<2**63:raise ValueError('invalid branch identifier')
        if scenario>=len(self.arena.template.program.probabilities):raise ValueError('invalid branch scenario')
        if not isinstance(resident,ArenaResident) or resident.arena is not self.arena:raise ValueError('incompatible branch arena')
        self.arena._check(resident.handle)
        if resident.observations or resident.observation_positions:raise ValueError('branch observations must be interned before retention')
        if self.count==len(self.rows):raise ValueError('branch sequence capacity exhausted')
        self.rows[self.count]=(scenario,*resident.handle,policy);self.count+=1

    def __getitem__(self,index):
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<self.count:raise IndexError('invalid branch sequence index')
        scenario,row,generation,policy=(int(x) for x in self.rows[index])
        handle=(row,generation);self.arena._check(handle)
        return scenario,ArenaResident(self.arena,handle),policy

    def __iter__(self):
        for index in range(self.count):yield self[index]
