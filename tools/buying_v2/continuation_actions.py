"""Resumable compiled lexicographic action frame for continuation search.

Prunes only monotone goods cash and aggregate input slots. Complete ledger
execution still decides fee, funded-demand, storage and production feasibility.
"""
import numpy as np
from .jit import njit
from .continuation_program import _array


@njit
def advance(material,price,lot,cap,cash,remaining,chosen,next_q,goods,control,budget,native,inventory,slots,saved,initial_remaining,max_funded,stop_prefix=False):
    # control: depth, finished, visited prefixes, yielded leaves, peak depth.
    n=len(material);work=0
    if control[1]:return 0,work
    if n==0:
        control[1]=1;control[3]+=1
        return 1,work
    depth=control[0]
    while True:
        if depth==n:
            control[3]+=1;depth-=1
            remaining[material[depth]]+=chosen[depth]
            if native:inventory[material[depth]]=saved[depth]
            control[0]=depth
            return 1,work
        m=material[depth]
        if next_q[depth]>cap[depth] or next_q[depth]>remaining[m]:
            if depth==0:
                control[0]=0;control[1]=1
                return 0,work
            depth-=1;remaining[material[depth]]+=chosen[depth]
            if native:inventory[material[depth]]=saved[depth]
            continue
        if work>=budget:
            control[0]=depth
            return 2,work
        q=next_q[depth];next_q[depth]+=lot[depth]
        control[2]+=1;work+=1
        payment=goods[depth]+q*price[depth]
        if payment>cash:
            # Positive price makes every later quantity at this prefix fail.
            next_q[depth]=cap[depth]+1
            continue
        if initial_remaining[m]-remaining[m]+q>max_funded[m]:
            # The ledger caps this material's total by its funded demand; larger
            # quantities at this prefix cannot restore feasibility.
            next_q[depth]=cap[depth]+1
            continue
        if native:
            updated=inventory[m]+q
            if updated>slots[m]:
                # Positive whole lots cannot repair an exceeded native slot.
                next_q[depth]=cap[depth]+1
                continue
            saved[depth]=inventory[m];inventory[m]=updated
        chosen[depth]=q;remaining[m]-=q;goods[depth+1]=payment
        depth+=1;control[4]=max(control[4],depth)
        if depth<n:next_q[depth]=0
        if stop_prefix:
            control[0]=depth
            return 3,work


class ActionLimit(ValueError):
    def __init__(self,diagnostics):
        super().__init__('action prefix work limit; no approximate result returned');self.diagnostics=diagnostics


class AllocationFrame:
    """One exact action traversal; suspend/resume without a Python generator."""
    def __init__(self,resident,scenario,index,*,query=False,offer=None,canonical=False):
        p=resident.program
        if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid scenario')
        if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid action index')
        event=int(p.scenario_offsets[scenario])+index
        if event>=p.scenario_offsets[scenario+1] or p.event_kinds[event]!=0:raise ValueError('action frame requires purchase')
        iv=resident.integers[p.integer_offsets[event]:p.integer_offsets[event+1]]
        fv=p.floats[p.float_offsets[event]:p.float_offsets[event+1]]
        if query:
            from .continuation_query import prepare
            iv,fv,_=prepare(resident,scenario,index,offer)
        n=int(iv[0]);held=resident.data[1];slots=resident.company_data[0]
        self.material=iv[4:4+4*n:4].copy();self.price=fv[4:4+n].copy();self.lot=iv[7:4+4*n:4].copy()
        self.remaining=np.maximum(0,slots-held);self.cash=float(resident.data[0][0])
        self.native=resident.native
        self.inventory=held.copy() if self.native else np.empty(0)
        self.slots=np.maximum(held,slots) if self.native else np.empty(0)
        self.saved=np.zeros(n) if self.native else np.empty(0)
        if resident.native:
            # Subtraction can round below a feasible whole purchase even when
            # native held + purchase fits. Prune with ordered native additions.
            caps=[int(iv[6+4*i]) for i in range(n)]
            totals=[0]*len(slots)
            for m,cap in zip(self.material,caps):totals[int(m)]+=cap
            if any(q>2**63-1 for q in totals):raise ValueError('action aggregate exceeds signed int64 frame')
            self.remaining=_array(totals,'<i8').copy()
        else:
            caps=[min(int(iv[6+4*i]),int(self.remaining[self.material[i]])) for i in range(n)]
        # next quantity and exhausted sentinel must also fit the typed frame.
        if any(c>2**63-1-int(l) for c,l in zip(caps,self.lot)):raise ValueError('action range exceeds signed int64 frame')
        # Per-material funded-demand cap: a conservative upper bound on the total
        # the ledger will accept for this material. The ledger enforces
        # q_i <= funded_i - running_total[material], so total <= funded_last <=
        # max funded over that material's offers. Bounding the frame the same way
        # avoids enumerating funded-infeasible compositions (e.g. a zero funded
        # demand admits only the empty allocation).
        self.initial_remaining=self.remaining.copy()
        funded=[(1<<63)-1]*len(slots)
        if int(iv[1])==n:
            funded=[0]*len(slots)
            for i in range(n):
                m=int(self.material[i]);f=int(iv[4+4*n+i])
                if f>funded[m]:funded[m]=f
        self.max_funded=_array(funded,'<i8')
        if canonical:
            # Symmetry break for split-invariant purchases: only the first offer
            # of each (material, price, lot) group may take quantity. The caller
            # enables this only when the per-offer split is value-irrelevant.
            seen={}
            for i in range(n):
                key=(int(self.material[i]),float(self.price[i]),int(self.lot[i]))
                if key in seen:caps[i]=0
                else:seen[key]=i
        self.cap=_array(caps,'<i8');self.chosen=np.zeros(n,np.int64);self.next_q=np.zeros(n,np.int64)
        self.goods=np.zeros(n+1);self.control=np.zeros(5,np.int64)

    def fork(self):
        other=object.__new__(type(self));other.__dict__={k:v.copy() if isinstance(v,np.ndarray) else v for k,v in self.__dict__.items()}
        return other

    def diagnostics(self):
        return dict(depth=int(self.control[0]),finished=bool(self.control[1]),visitedPrefixes=int(self.control[2]),
            yieldedAllocations=int(self.control[3]),peakDepth=int(self.control[4]),
            allocatedBytes=sum(v.nbytes for v in self.__dict__.values() if isinstance(v,np.ndarray)))

    def next(self,*,max_prefixes,prune=None):
        if not isinstance(max_prefixes,int) or isinstance(max_prefixes,bool) or not 0<=max_prefixes<2**63:raise ValueError('invalid prefix allowance')
        remaining_budget=max_prefixes;call_prefixes=0;call_bound_work=0
        while True:
            status,work=advance(self.material,self.price,self.lot,self.cap,self.cash,self.remaining,self.chosen,self.next_q,self.goods,self.control,remaining_budget,self.native,self.inventory,self.slots,self.saved,self.initial_remaining,self.max_funded,prune is not None)
            remaining_budget-=int(work);call_prefixes+=int(work)
            if status==2:raise ActionLimit(dict(**self.diagnostics(),callPrefixes=call_prefixes,callBoundWork=call_bound_work))
            if status!=3:return tuple(int(q) for q in self.chosen) if status==1 else None
            depth=int(self.control[0])
            proof=prune(tuple(int(q) for q in self.chosen[:depth]),remaining_budget)
            cut,cost=proof[:2];tail=proof[2] if len(proof)==3 else False
            if not isinstance(tail,bool) or (tail and not cut):raise ValueError('invalid range certificate')
            if not isinstance(cost,int) or isinstance(cost,bool) or not 0<=cost<=remaining_budget:raise AssertionError('prefix bound exceeded work reservation')
            remaining_budget-=cost;call_bound_work+=cost
            if cut:
                depth-=1;self.remaining[self.material[depth]]+=self.chosen[depth];self.control[0]=depth
                if self.native:self.inventory[self.material[depth]]=self.saved[depth]
                if tail:self.next_q[depth]=self.cap[depth]+1
