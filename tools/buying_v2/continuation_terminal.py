"""Compiled terminal capture directly from arena rows into result buffers."""
import numpy as np
from .jit import njit
from .continuation_arena import _check
from .continuation_arena_information import _view
from .continuation_results import terminal_value,ResultLimit
from .continuation_leaf_rows import LeafRows


@njit
def _capture(pool,live,generations,metadata,branches,cash,arrears,width,offsets,terminal,modes,knots,probabilities,
             ids,values,control,leaves,weighted):
    for i in range(len(branches)):
        scenario,row,generation,policy=branches[i]
        _check(live,generations,row,generation)
        if scenario<0 or scenario>=len(probabilities):raise ValueError('invalid terminal scenario')
        value=terminal_value(_view(pool,row),cash,arrears,scenario,width,offsets,terminal,modes,knots)
        if policy<0 or metadata[row,0]<0 or metadata[row,2]<0 or not np.isfinite(value):raise ValueError('invalid terminal result')
        at=control[0]
        if at==len(values):return False
        ids[at,0]=scenario;ids[at,1]=policy;ids[at,2]=metadata[row,0];ids[at,3]=metadata[row,2]
        values[at]=value;leaves[i]=at;weighted[i]=probabilities[scenario]*value
        control[0]+=1
    return True


def capture(branches,initial,results):
    from .continuation_branches import BranchRows
    if not isinstance(branches,BranchRows):raise ValueError('arena branches required')
    arena=branches.arena;p=arena.template.program
    leaves=LeafRows(len(branches));weighted=np.empty(len(branches),np.float64)
    control=np.array([results.count],np.int64)
    try:
        ok=_capture(arena.pool,arena.live,arena.generations,arena.search_metadata,branches.rows[:len(branches)],
            initial.cash,initial.arrears,p.inputs+p.lines,p.terminal_offsets,p.terminal_values,p.terminal_modes,p.terminal_quantities,p.probabilities,
            results.ids,results.values,control,leaves.rows,weighted)
    finally:results.count=int(control[0])
    if not ok:raise ResultLimit(dict(**results.diagnostics(),requiredRecords=results.count+1))
    leaves.count=len(branches)
    return leaves,weighted
