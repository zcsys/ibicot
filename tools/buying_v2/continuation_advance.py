"""Compiled non-purchase advancement with immediate numeric history interning."""
import numpy as np
from .jit import njit
from .continuation_arena import _check,_step
from .continuation_history import _intern,HistoryLimit


@njit
def _advance(pool,live,generations,metadata,branches,company,kinds,labels,io,fo,floats,offsets,persistent,
             parents,hio,hfo,hints,hfloats,control,stop):
    # control: history counts (nodes/ints/floats), completed transitions, event index.
    empty=np.empty(0,np.int64)
    for branch in branches:
        scenario,row,generation,_=branch
        _check(live,generations,row,generation)
        if scenario<0 or scenario+1>=len(offsets):raise ValueError('invalid branch scenario')
        if stop>offsets[scenario+1]-offsets[scenario]:raise ValueError('invalid advance boundary')
        if metadata[row,1]!=control[4] or metadata[row,0]<0 or metadata[row,0]>=control[0]:raise ValueError('incomplete advance history')
    while control[4]<stop:
        index=control[4]
        if kinds[offsets[branches[0,0]]+index]==0:break
        for branch in branches:
            scenario,row,generation,_=branch;event=offsets[scenario]+index
            if kinds[event]==0:raise ValueError('inconsistent purchase positions')
            records=_step(pool,row,company,kinds,labels,io,fo,floats,event,empty,True,persistent,offsets[scenario+1])
            for iv,fv in records:
                if not np.isfinite(fv).all():raise ValueError('invalid observation arrays')
            end,count,ic,fc,processed,ok,rn,ri,rf=_intern(metadata[row,0],records,parents,hio,hfo,hints,hfloats,control[0],control[1],control[2])
            if not ok:return False,rn,ri,rf
            control[0]=count;control[1]=ic;control[2]=fc
            metadata[row,0]=end;metadata[row,1]+=processed;control[3]+=1
        control[4]+=1
    return True,control[0],control[1],control[2]


def advance(branches,index,stop,history,stats):
    from .continuation_branches import BranchRows
    if not isinstance(branches,BranchRows) or not len(branches):raise ValueError('arena branches required')
    if any(not isinstance(v,int) or isinstance(v,bool) for v in (index,stop)) or not 0<=index<=stop:raise ValueError('invalid advance range')
    arena=branches.arena;p=arena.template.program
    if history.program is not p:raise ValueError('incompatible history program')
    control=np.array([history.count,history.integer_count,history.float_count,0,index],np.int64)
    try:
        ok,rn,ri,rf=_advance(arena.pool,arena.live,arena.generations,arena.search_metadata,branches.rows[:len(branches)],
            arena.template.company_data,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,p.floats,p.scenario_offsets,
            arena.template.supply=='persistent-arrivals',history.parents,history.io,history.fo,history.integers,history.floats,control,stop)
    finally:
        history.count=int(control[0]);history.integer_count=int(control[1]);history.float_count=int(control[2])
        stats['transitions']+=int(control[3])
    if not ok:raise HistoryLimit(dict(**history.diagnostics(),processedRecords=0,requiredNodes=int(rn),requiredIntegers=int(ri),requiredFloats=int(rf)))
    return int(control[4])
