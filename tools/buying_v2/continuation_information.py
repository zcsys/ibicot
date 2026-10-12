"""Exact observed-history interning and compiled resident decision grouping.

Trace encoding is a verification boundary; resident trace production remains to
be connected. Future demand, terminal values and probabilities are not keys.
"""
import numpy as np
from .jit import njit
from .continuation_program import _array

FIELDS=('cash','equity','postedEarnings','sold','sales','cogs','feeIncome',
        'openingStock','openingBasis','openingQuote','quotes','eligible',
        'charge','paid','arrears','netTransfers','nextTransferEMA',
        'allocation','observedPurchase','fundedDemands','preferences',
        'fees','goods','outputs','conversion')


class History:
    """Collision-free trie of exact observed records, in one grouping scope."""
    def __init__(self):
        self.nodes={};self.count=1

    def append(self,parent,detail):
        if not isinstance(parent,int) or isinstance(parent,bool) or not 0<=parent<self.count:raise ValueError('unknown history parent')
        key=(parent,detail['event'],detail['label'],tuple((name,detail[name]) for name in FIELDS if name in detail))
        if key not in self.nodes:
            self.nodes[key]=self.count;self.count+=1
        return self.nodes[key]

    def trace(self,trace):
        parent=0
        for detail in trace:parent=self.append(parent,detail)
        return parent


@njit
def _same_state(a,b):
    # Complete live state, including accounts. Ignore unused buffer tails.
    for i in range(len(a[0])):
        if a[0][i]!=b[0][i]:return False
    for i in range(len(a[1])):
        if a[1][i]!=b[1][i] or a[2][i]!=b[2][i] or a[6][i]!=b[6][i]:return False
    for i in range(len(a[3])):
        if a[3][i]!=b[3][i] or a[4][i]!=b[4][i] or a[5][i]!=b[5][i]:return False
    if a[7]!=b[7] or a[11]!=b[11] or a[13]!=b[13]:return False
    if a[7]>=0:
        for i in range(len(a[8])):
            if a[8][i]!=b[8][i] or a[9][i]!=b[9][i] or a[10][i]!=b[10][i]:return False
    for i in range(a[13]):
        if a[12][i]!=b[12][i]:return False
    return True


@njit
def _same_offer_event(left,right,labels,io,fo,integers,other_integers,floats,neutral):
    if labels[left]!=labels[right]:return False
    a=integers[io[left]:io[left+1]];b=other_integers[io[right]:io[right+1]]
    x=floats[fo[left]:fo[left+1]];y=floats[fo[right]:fo[right+1]]
    if a[0]!=b[0] or a[2]!=b[2] or a[3]!=b[3]:return False
    for i in range(4):
        if i==1 and neutral:continue
        if x[i]!=y[i]:return False
    if a[3]==2 and x[-1]!=y[-1]:return False
    for j in range(a[2]):
        if a[4+4*a[0]+a[1]+j]!=b[4+4*b[0]+b[1]+j]:return False
    # Offers are a set keyed by validated unique (material,supplier), not order.
    for i in range(a[0]):
        found=False
        for j in range(b[0]):
            if a[4+4*i]==b[4+4*j] and a[5+4*i]==b[5+4*j]:
                if a[6+4*i]!=b[6+4*j] or a[7+4*i]!=b[7+4*j] or x[4+i]!=y[4+j] or x[4+a[0]+i]!=y[4+b[0]+j]:return False
                found=True;break
        if not found:return False
    return True


@njit
def _groups(states,histories,events,labels,io,fo,integers,floats,neutral):
    groups=np.empty(len(states),np.int64);count=0
    for i in range(len(states)):
        match=-1
        for j in range(i):
            if histories[i]==histories[j] and _same_state(states[i],states[j]) and _same_offer_event(events[i],events[j],labels,io,fo,integers[i],integers[j],floats,neutral):
                match=groups[j];break
        if match<0:match=count;count+=1
        groups[i]=match
    return groups


def group_decisions(residents,scenarios,index,histories,history,*,neutral=False):
    """Stable group IDs for branches at one purchase index of one program."""
    if not residents or len(residents)!=len(scenarios) or len(residents)!=len(histories):raise ValueError('invalid branch dimensions')
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid decision index')
    if not isinstance(neutral,bool):raise ValueError('invalid neutral mode')
    p=residents[0].program;events=[]
    for r,scenario,h in zip(residents,scenarios,histories):
        if r.program is not p or r.company!=residents[0].company or r.labels!=residents[0].labels or r.supply!=residents[0].supply:raise ValueError('incompatible grouping scope')
        if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid scenario')
        event=int(p.scenario_offsets[scenario])+index
        if event>=p.scenario_offsets[scenario+1] or p.event_kinds[event]!=0:raise ValueError('grouping requires a purchase event')
        if not isinstance(h,int) or isinstance(h,bool) or not 0<=h<history.count:raise ValueError('unknown history')
        events.append(event)
    from numba.typed import List
    states=List();integers=List()
    for r in residents:
        states.append(r.data);integers.append(r.integers)
    result=_groups(states,_array(histories,'<i8'),_array(events,'<i8'),p.event_labels,p.integer_offsets,p.float_offsets,integers,p.floats,neutral)
    return tuple(int(x) for x in result)
