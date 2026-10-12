"""Compiled cloning and funding assignment for an observed scenario group."""
import numpy as np
from .jit import njit
from .continuation_arena import _check,_claim,_load,_store,BranchLimit
from .continuation_branches import BranchRows
from .continuation_groups import GroupView
from .continuation_history import _intern
from .continuation_funding_records import encode_detail,FundingRecordLimit
from .continuation_program import _array


@njit
def _resolve(pool,live,generations,metadata,branches,index,demands,offsets,kinds,io,
             parents,hio,hfo,hints,hfloats,iv,fv,control,output):
    # control: active/peak/allocations; record node/int/float counts.
    records=[(iv,fv)]
    for i in range(len(branches)):
        scenario,source,generation,policy=branches[i]
        _check(live,generations,source,generation)
        if scenario<0 or scenario+1>=len(offsets):raise ValueError('invalid funding scenario')
        event=offsets[scenario]+index
        if event>=offsets[scenario+1] or kinds[event]!=0:raise ValueError('funding requires purchase')
        start=io[event];n=pool[12][source,start]
        if pool[12][source,start+1]!=n:raise ValueError('funding payload was not preallocated')
        if len(demands)!=n:raise ValueError('invalid resolved funded demands')
        for j in range(n):
            if demands[j]<0 or demands[j]%pool[12][source,start+7+4*j]:raise ValueError('invalid resolved funded demands')
        row=_claim(live,generations)
        if row<0:return 1,0,0,0
        control[0]+=1;control[1]=max(control[1],control[0]);control[2]+=1
        _store(pool,row,_load(pool,source),pool[12][source]);metadata[row]=metadata[source]
        for j in range(n):pool[12][row,start+4+4*n+j]=demands[j]
        parent=metadata[source,2]
        if parent<0 or parent>=control[3]:raise ValueError('invalid funding record node')
        if parent and index<=hints[hio[parent]]:raise ValueError('funding events must increase')
        node,count,ic,fc,processed,ok,rn,ri,rf=_intern(parent,records,parents,hio,hfo,hints,hfloats,control[3],control[4],control[5])
        if not ok:return 2,rn,ri,rf
        control[3]=count;control[4]=ic;control[5]=fc;metadata[row,2]=node
        output[i,0]=scenario;output[i,1]=row;output[i,2]=generations[row];output[i,3]=policy
    return 0,0,0,0


def _resolve_prepared(group,index,demands,iv,fv,records):
    if isinstance(group,BranchRows):arena=group.arena;rows=group.rows[:len(group)]
    elif isinstance(group,GroupView) and isinstance(group.groups.branches,BranchRows):
        arena=group.groups.branches.arena
        rows=group.groups.branches.rows[group.groups.members[group.start:group.stop]]
    else:raise ValueError('numeric arena group required')
    p=arena.template.program
    output=BranchRows(arena,len(group));control=np.array([arena.active,arena.peak,arena.allocations,records.count,records.integer_count,records.float_count],np.int64)
    try:
        status,rn,ri,rf=_resolve(arena.pool,arena.live,arena.generations,arena.search_metadata,rows,index,demands,p.scenario_offsets,p.event_kinds,p.integer_offsets,
            records.parents,records.io,records.fo,records.integers,records.floats,iv,fv,control,output.rows)
    finally:
        arena.active=int(control[0]);arena.peak=int(control[1]);arena.allocations=int(control[2])
        records.count=int(control[3]);records.integer_count=int(control[4]);records.float_count=int(control[5])
    if status==1:raise BranchLimit(arena.diagnostics())
    if status==2:raise FundingRecordLimit(dict(**records.diagnostics(),requiredNodes=int(rn),requiredIntegers=int(ri),requiredFloats=int(rf)))
    output.count=len(group)
    return output


def resolve(group,index,demands,detail,records):
    if any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in demands):raise ValueError('invalid resolved funded demands')
    iv,fv=encode_detail(index,detail)
    return _resolve_prepared(group,index,_array(demands,'<i8'),iv,fv,records)


def resolve_answers(group,index,scratch,records):
    from .continuation_funding_encoding import encode_answers
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid funding event')
    scenario,resident,_=group[0];arena=resident.arena;p=arena.template.program
    row=arena._check(resident.handle);event=int(p.scenario_offsets[scenario])+index
    if event>=p.scenario_offsets[scenario+1] or p.event_kinds[event]!=0:raise ValueError('funding requires purchase')
    iv=arena.pool[12][row,p.integer_offsets[event]:p.integer_offsets[event+1]]
    fv=p.floats[p.float_offsets[event]:p.float_offsets[event+1]]
    demands,record_iv,record_fv=encode_answers(index,iv,fv,arena.pool[6][row],scratch.requests,scratch.ready,scratch.quantities,scratch.values)
    return _resolve_prepared(group,index,demands,record_iv,record_fv,records)
