"""Typed continuation-v2 own-quote query payloads; no funding optimization."""
import numpy as np
from .jit import njit


@njit
def native_cap(held,slot,lot):
    # Search the actual monotone native-addition predicate. Reserve the frame's
    # next-quantity sentinel; never silently clip a larger representable range.
    top=(9223372036854775807-lot)//lot
    limit=max(held,slot)
    if held+top*lot<=limit:
        raise ValueError('native query range exceeds signed int64 frame')
    low=0;high=top
    while low<high:
        middle=low+(high-low+1)//2
        if held+middle*lot<=limit:low=middle
        else:high=middle-1
    return low*lot


@njit
def payload(iv,fv,held,slots,offer,native=False):
    n=iv[0]
    material=iv[4+4*offer] if offer>=0 else -1
    selected=np.empty(n,np.int64);count=0
    for i in range(n):
        if material<0 or iv[4+4*i]!=material or i==offer:selected[count]=i;count+=1
    selected=selected[:count].copy()
    integers=np.empty(4+5*count+iv[2],np.int64);floats=np.empty(4+2*count+int(iv[3]==2))
    integers[0]=count;integers[1]=count;integers[2]=iv[2];integers[3]=iv[3]
    for j in range(4):floats[j]=fv[j]
    floats[1]=0.
    if iv[3]==2:floats[-1]=fv[-1]
    for j in range(count):
        i=selected[j];m=iv[4+4*i];lot=iv[7+4*i]
        cap=native_cap(held[m],slots[m],lot) if native else int(max(0,slots[m]-held[m])//lot*lot)
        for k in range(4):integers[4+4*j+k]=iv[4+4*i+k]
        integers[6+4*j]=cap;integers[4+4*count+j]=cap
        floats[4+j]=fv[4+i];floats[4+count+j]=fv[4+n+i]
    for j in range(iv[2]):integers[4+5*count+j]=iv[4+4*n+iv[1]+j]
    return integers,floats,selected


def prepare(resident,scenario,index,offer=None):
    p=resident.program
    if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid query scenario')
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid query index')
    event=int(p.scenario_offsets[scenario])+index
    if event>=p.scenario_offsets[scenario+1] or p.event_kinds[event]!=0:raise ValueError('query requires purchase event')
    iv=resident.integers[p.integer_offsets[event]:p.integer_offsets[event+1]]
    fv=p.floats[p.float_offsets[event]:p.float_offsets[event+1]]
    if offer is not None and (not isinstance(offer,int) or isinstance(offer,bool) or not 0<=offer<iv[0]):raise ValueError('invalid queried offer')
    return payload(iv,fv,resident.data[1],resident.company_data[0],-1 if offer is None else offer,resident.native)
