"""Compiled observed-information grouping directly over live arena rows."""
import numpy as np
from .jit import njit
from .continuation_arena import _check
from .continuation_information import _same_state,_same_offer_event


@njit
def _view(pool,row):
    m=pool[11][row]
    return (pool[0][row],pool[1][row],pool[2][row],pool[3][row],pool[4][row],pool[5][row],pool[6][row],
        m[0],pool[7][row],pool[8][row],pool[9][row],bool(m[1]),pool[10][row],m[2])


@njit
def _groups(pool,live,generations,metadata,branches,index,history_count,scenario_offsets,kinds,labels,io,fo,floats,neutral):
    groups=np.empty(len(branches),np.int64);events=np.empty(len(branches),np.int64);count=0
    # Validate all indices before comparisons; no invalid array access or partial grouping.
    for i in range(len(branches)):
        scenario,row,generation,_=branches[i]
        _check(live,generations,row,generation)
        if scenario<0 or scenario+1>=len(scenario_offsets):raise ValueError('invalid branch scenario')
        event=scenario_offsets[scenario]+index
        if event>=scenario_offsets[scenario+1] or kinds[event]!=0:raise ValueError('grouping requires a purchase event')
        if metadata[row,0]<0 or metadata[row,0]>=history_count:raise ValueError('unknown history')
        events[i]=event
    for i in range(len(branches)):
        row=branches[i,1];match=-1
        for j in range(i):
            other=branches[j,1]
            if metadata[row,0]==metadata[other,0] and _same_state(_view(pool,row),_view(pool,other)) and _same_offer_event(events[i],events[j],labels,io,fo,pool[12][row],pool[12][other],floats,neutral):
                match=groups[j];break
        if match<0:match=count;count+=1
        groups[i]=match
    return groups


def group_arena_decisions(branches,index,history,*,neutral=False):
    from .continuation_branches import BranchRows
    if not isinstance(branches,BranchRows) or not len(branches):raise ValueError('arena branches required')
    if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid decision index')
    if not isinstance(neutral,bool):raise ValueError('invalid neutral mode')
    arena=branches.arena;p=arena.template.program
    return _groups(arena.pool,arena.live,arena.generations,arena.search_metadata,branches.rows[:len(branches)],index,history.count,
        p.scenario_offsets,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,p.floats,neutral)
