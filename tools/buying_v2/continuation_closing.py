"""Opt-in bridge to existing certified closing search; unsupported suffixes fall back."""
from dataclasses import replace
import numpy as np
import pickle
from .industry_oracle import Offer
from .continuation_query import prepare as query_payload
from .closing_allocation import prepare
from .closing_certificate import solve as closing_solve


class SelectedAllocation:
    def __init__(self,allocation):self.allocation=tuple(allocation);self.control=np.zeros(5,np.int64)
    def next(self,*,max_prefixes):
        if self.control[1]:return None
        self.control[1]=1;self.control[3]=1
        return self.allocation


def purchase_event(paths,group,index,query,offer):
    scenario,r,_=group[0];p=r.program;position=int(p.scenario_offsets[scenario])+index
    iv=r.integers[p.integer_offsets[position]:p.integer_offsets[position+1]]
    fv=p.floats[p.float_offsets[position]:p.float_offsets[position+1]]
    if query:iv,fv,_=query_payload(r,scenario,index,offer)
    n=int(iv[0]);event=replace(paths[scenario].events[index],
        offers=tuple(Offer(int(iv[4+4*i]),int(iv[5+4*i]),float(fv[4+i]),int(iv[6+4*i]),int(iv[7+4*i])) for i in range(n)),
        funded_demands=tuple(int(x) for x in iv[4+4*n:4+4*n+int(iv[1])]),
        reliability=tuple(float(x) for x in fv[4+n:4+2*n]),fee_multiple=float(fv[1]))
    return event


def select(company,initial,paths,group,index,query,offer,max_allocations,max_work,memo=None,proposal_memo=None,joint_memo=None,cash_relaxed=False,joint_fallback=False):
    scenario,r,_=group[0];event=purchase_event(paths,group,index,query,offer)
    state=r.snapshot();posterior=tuple((paths[s].probability,replace(paths[s],events=paths[s].events[index+1:])) for s,_,_ in group)
    if prepare(company,initial,state,event,posterior) is None:return None
    key=None
    if memo is not None:
        key=pickle.dumps((state,event,posterior,query),protocol=5)
        cached=memo.get(key)
        if cached is not None:
            if max_allocations<1:raise ValueError('closing allocation limit; no approximate result returned')
            return dict(allocation=cached[0],payment=cached[1],value=cached[2],enumeratedAllocations=1,boxes=0,proposalStates=0,certificates=0,jointBoundWork=0)
    if max_allocations<1 or max_work<1:raise ValueError('closing work limit; no approximate result returned')
    result=closing_solve(company,initial,state,event,posterior,max_allocations=max_allocations,max_boxes=max_work,joint_proposals=True,proposal_memo=proposal_memo,joint_memo=joint_memo,cash_relaxed_joint_bound=cash_relaxed,joint_fallback=joint_fallback)
    if memo is not None:memo.put(key,(result['allocation'],result['payment'],result['value']))
    return result
