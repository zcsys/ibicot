"""Bounded exact numeric observation trie; no trace decoding or hashed equality."""
import numpy as np
from .jit import njit


@njit
def _intern(parent,records,parents,io,fo,ints,floats,count,ic,fc):
    processed=0
    for iv,fv in records:
        found=-1
        for node in range(1,count):
            if parents[node]!=parent or io[node+1]-io[node]!=len(iv) or fo[node+1]-fo[node]!=len(fv):continue
            same=True
            for j in range(len(iv)):
                if ints[io[node]+j]!=iv[j]:same=False;break
            if same:
                for j in range(len(fv)):
                    if floats[fo[node]+j]!=fv[j]:same=False;break
            if same:found=node;break
        if found<0:
            if count>=len(parents) or ic+len(iv)>len(ints) or fc+len(fv)>len(floats):
                return parent,count,ic,fc,processed,False,count+1,ic+len(iv),fc+len(fv)
            found=count;parents[count]=parent;io[count]=ic;fo[count]=fc
            for j in range(len(iv)):ints[ic+j]=iv[j]
            for j in range(len(fv)):floats[fc+j]=fv[j]
            ic+=len(iv);fc+=len(fv);count+=1;io[count]=ic;fo[count]=fc
        parent=found;processed+=1
    return parent,count,ic,fc,processed,True,count,ic,fc


@njit
def _intern_one(parent,iv,fv,parents,io,fo,ints,floats,count,ic,fc):
    return _intern(parent,[(iv,fv)],parents,io,fo,ints,floats,count,ic,fc)


class HistoryLimit(ValueError):
    def __init__(self,diagnostics):
        super().__init__('numeric history arena exhausted');self.diagnostics=diagnostics


class NumericHistory:
    def __init__(self,program,*,max_nodes=4096,max_integers=262144,max_floats=262144):
        if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (max_nodes,max_integers,max_floats)):raise ValueError('positive history capacities required')
        self.program=program;self.count=1;self.integer_count=0;self.float_count=0
        self.parents=np.zeros(max_nodes,np.int64);self.io=np.zeros(max_nodes+1,np.int64);self.fo=np.zeros(max_nodes+1,np.int64)
        self.integers=np.empty(max_integers,np.int64);self.floats=np.empty(max_floats,np.float64)

    def diagnostics(self):
        return dict(nodes=self.count,integerValues=self.integer_count,floatValues=self.float_count,
            capacityNodes=len(self.parents),capacityIntegers=len(self.integers),capacityFloats=len(self.floats),
            allocatedBytes=sum(a.nbytes for a in (self.parents,self.io,self.fo,self.integers,self.floats)))

    def extend(self,parent,records):
        if not isinstance(parent,int) or isinstance(parent,bool) or not 0<=parent<self.count:raise ValueError('unknown numeric history parent')
        if not records:return parent
        validated=[]
        for iv,fv in records:
            if iv.dtype!=np.dtype('int64') or fv.dtype!=np.dtype('float64') or iv.ndim!=1 or fv.ndim!=1 or not np.isfinite(fv).all():raise ValueError('invalid observation arrays')
            if len(iv)<3 or len(fv)<3 or iv[0] not in (1,2,3) or not 0<=iv[1]<=6 or not 0<=iv[2]<len(self.program.labels):raise ValueError('invalid observation header')
            kind=int(iv[1])
            if kind==0:
                if len(iv)<8 or np.any(iv[3:7]<0) or iv[7] not in (0,1,2):raise ValueError('invalid purchase observation')
                count,n,nl,active=(int(x) for x in iv[3:7]);ni=8+6*count+active+n+nl;nf=9+2*count+n+int(iv[7]==2)
                if (iv[0]==2)!=(iv[7]==2):raise ValueError('invalid purchase observation schema')
            elif iv[0]==3 and kind==1:
                if len(iv)!=4 or iv[3]<0:raise ValueError('invalid native opening observation')
                ni=4;nf=3+3*int(iv[3])
            elif iv[0]!=1:raise ValueError('invalid observation schema')
            elif kind in (1,2,3,4):
                if len(iv)<4 or iv[3]<0:raise ValueError('invalid vector observation')
                n=int(iv[3]);ni=4+n if kind!=4 else 4
                nf=3+2*n if kind==1 else (3+n if kind==4 else 6)
            elif kind==5:
                ni=4;nf=6
                if len(iv)!=4 or iv[3] not in (0,1):raise ValueError('invalid rent observation')
            else:ni=3;nf=5
            if len(iv)!=ni or len(fv)!=nf:raise ValueError('invalid observation payload length')
            validated.append((iv.copy(),fv.copy()))
        if len(validated)==1:
            iv,fv=validated[0]
            result=_intern_one(parent,iv,fv,self.parents,self.io,self.fo,self.integers,self.floats,self.count,self.integer_count,self.float_count)
        else:
            from numba.typed import List
            typed=List()
            for record in validated:typed.append(record)
            result=_intern(parent,typed,self.parents,self.io,self.fo,self.integers,self.floats,self.count,self.integer_count,self.float_count)
        end,count,ic,fc,processed,ok,rn,ri,rf=result
        if not ok:
            raise HistoryLimit(dict(**self.diagnostics(),processedRecords=int(processed),requiredNodes=int(rn),requiredIntegers=int(ri),requiredFloats=int(rf)))
        self.count=int(count);self.integer_count=int(ic);self.float_count=int(fc)
        return int(end)

    def trace(self,records):return self.extend(0,records)

    def export(self,node):
        if not isinstance(node,int) or isinstance(node,bool) or not 0<=node<self.count:raise ValueError('unknown numeric history node')
        records=[]
        while node:
            records.append((self.integers[self.io[node]:self.io[node+1]].copy(),self.floats[self.fo[node]:self.fo[node+1]].copy()))
            node=int(self.parents[node])
        return tuple(reversed(records))


def group_observed(residents,scenarios,index,history,*,neutral=False):
    from .continuation_information import group_decisions
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid decision index')
    if not residents or any(r.program is not history.program for r in residents):raise ValueError('incompatible history program')
    if any(r.observation_positions!=tuple(range(index)) for r in residents):raise ValueError('complete observed prefix required')
    ids=[history.trace(r.observations) for r in residents]
    return group_decisions(residents,scenarios,index,ids,history,neutral=neutral)
