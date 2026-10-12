"""Bounded selected-result IDs; one terminal row per scenario branch."""
import numpy as np


class LeafRows:
    def __init__(self,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<0:
            raise ValueError('invalid leaf row capacity')
        self.rows=np.empty(capacity,dtype=np.int64)
        self.count=0

    def __len__(self):return self.count

    def __iter__(self):
        for i in range(self.count):yield int(self.rows[i])

    def append(self,row):
        if not isinstance(row,(int,np.integer)) or isinstance(row,(bool,np.bool_)) or not 0<=row<2**63:
            raise ValueError('invalid leaf row identifier')
        if self.count==len(self.rows):raise ValueError('leaf row capacity exhausted')
        self.rows[self.count]=row;self.count+=1

    def extend(self,other):
        if not isinstance(other,LeafRows):raise TypeError('leaf rows required')
        count=other.count
        if self.count+count>len(self.rows):raise ValueError('leaf row capacity exhausted')
        self.rows[self.count:self.count+count]=other.rows[:count]
        self.count+=count
