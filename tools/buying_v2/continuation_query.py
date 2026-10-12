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


def _collapse_joint(integers,floats,selected):
    """Collapse equal-(material, price, lot) offers in a continuation-v2 query.

    For offers sharing material, price and lot, the hypothetical continuation
    state (held, basis and goods cost) and its value depend only on the
    per-material aggregate quantity, while incumbents are held and current fees
    are removed inside the query. Collapsing each group to one offer removes the
    redundant per-offer composition enumeration without changing the aggregate
    answer. The original `selected` tuple is returned unchanged so that
    QueryAnswers.request keeps its offer-set dedup key distinct across queries;
    callers validate allocation length against the collapsed iv[0].
    """
    n=int(integers[0])
    order=[];members=[]
    for j in range(n):
        key=(int(integers[4+4*j]),float(floats[4+j]),int(integers[7+4*j]))
        for gi,k in enumerate(order):
            if key==k:members[gi].append(j);break
        else:order.append(key);members.append([j])
    if len(order)==n:return integers,floats,selected
    count=len(order)
    ni=np.empty(4+5*count+integers[2],np.int64);nf=np.empty(4+2*count+int(integers[3]==2))
    ni[0]=count;ni[1]=count;ni[2]=integers[2];ni[3]=integers[3]
    nf[0]=floats[0];nf[1]=floats[1];nf[2]=floats[2];nf[3]=floats[3]
    if integers[3]==2:nf[-1]=floats[-1]
    for gi,key in enumerate(order):
        rep=members[gi][0]
        ni[4+4*gi]=integers[4+4*rep]
        ni[5+4*gi]=integers[5+4*rep]
        ni[6+4*gi]=integers[6+4*rep]
        ni[7+4*gi]=integers[7+4*rep]
        ni[4+4*count+gi]=integers[6+4*rep]
        nf[4+gi]=floats[4+rep];nf[4+count+gi]=floats[4+n+rep]
    for j in range(integers[2]):ni[4+5*count+j]=integers[4+5*n+j]
    return ni,nf,selected


def prepare(resident,scenario,index,offer=None):
    p=resident.program
    if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid query scenario')
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid query index')
    event=int(p.scenario_offsets[scenario])+index
    if event>=p.scenario_offsets[scenario+1] or p.event_kinds[event]!=0:raise ValueError('query requires purchase event')
    iv=resident.integers[p.integer_offsets[event]:p.integer_offsets[event+1]]
    fv=p.floats[p.float_offsets[event]:p.float_offsets[event+1]]
    if offer is not None and (not isinstance(offer,int) or isinstance(offer,bool) or not 0<=offer<iv[0]):raise ValueError('invalid queried offer')
    result=payload(iv,fv,resident.data[1],resident.company_data[0],-1 if offer is None else offer,resident.native)
    if resident.supply!='persistent-arrivals':
        result=_collapse_joint(*result)
    return result


def query_key(integers,floats,selected,supply):
    """Supplier/order-independent dedup identity for a funding query.

    Independent-snapshot supply makes the hypothetical value depend only on each
    collapsed offer's material, price and lot; persistent arrivals keep the
    unique offer subset because a hypothetical purchase consumes a specific
    supplier's future stock.
    """
    if supply!='persistent-arrivals':
        return tuple(sorted((int(integers[4+4*j]),float(floats[4+j]),int(integers[7+4*j])) for j in range(int(integers[0]))))
    return tuple(int(x) for x in selected)
