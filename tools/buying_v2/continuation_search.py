"""Explicit-stack exact conditional search with supplied or continuation-v2 funding.

Control scalars and selected-result IDs use typed bounded buffers around Python
dispatch and compiled action, transition, and grouping kernels. No calibrated forecast or population feasibility claim.
"""
from dataclasses import replace
import math
import numpy as np
from .phase_ledger import Purchase
from .continuation_program import compile_calendar
from .continuation_resident import Resident
from .continuation_history import NumericHistory,HistoryLimit
from .continuation_information import group_decisions
from .continuation_actions import AllocationFrame,ActionLimit
from .continuation_observation import purchase_payment,decode
from .continuation_query import prepare,query_key
from .continuation_arena import BranchArena,ArenaResident,BranchLimit
from .continuation_policy import PolicyArena,PolicyLimit
from .continuation_funding_records import FundingRecords,FundingRecordLimit
from .continuation_query_answers import QueryAnswers
from .continuation_results import Results,ResultLimit,terminal_value
from .continuation_control import ControlStack
from .continuation_leaf_rows import LeafRows
from .continuation_groups import Groups
from .continuation_branches import BranchRows
from .continuation_arena_information import group_arena_decisions
from .continuation_advance import advance
from .continuation_terminal import capture
from .continuation_resolve import resolve_answers
from .continuation_query_memo import QueryMemo
from .continuation_closing import select as select_closing,SelectedAllocation


class SearchLimit(ValueError):
    def __init__(self,message,diagnostics):super().__init__(message);self.diagnostics=diagnostics


def solve(company,initial,scenarios,*,max_frames=256,max_allocations=100000,max_prefixes=100000,
          supply='independent-snapshots',funding='supplied',storage='resident',max_branches=256,history_nodes=65536,history_integers=4194304,history_floats=4194304,policy_nodes=65536,policy_values=262144,funding_nodes=65536,funding_integers=262144,funding_floats=262144,max_query_bytes=67108864,max_results=100000,control='typed',funding_memo_entries=0,funding_memo_bytes=16777216,closing=False,closing_memo_entries=0,closing_memo_bytes=16777216,prune_continuation=False,prune_prefix=False,shared_first_states=0,proof_memo_entries=0,closing_cash_relaxed=False,shared_recourse_memo_entries=0,closing_joint_fallback=False,prune_ranges=False):
    if not isinstance(prune_ranges,bool) or (prune_ranges and not prune_prefix):raise ValueError('range pruning requires prefix pruning')
    if not isinstance(closing_joint_fallback,bool) or (closing_joint_fallback and not closing):raise ValueError('joint fallback requires closing mode')
    if not isinstance(shared_recourse_memo_entries,int) or isinstance(shared_recourse_memo_entries,bool) or shared_recourse_memo_entries<0 or (shared_recourse_memo_entries and not (prune_prefix and shared_first_states)):raise ValueError('recourse memo requires shared prefix proofs and nonnegative size')
    if not isinstance(proof_memo_entries,int) or isinstance(proof_memo_entries,bool) or proof_memo_entries<0:raise ValueError('invalid proof memo size')
    if not isinstance(closing_cash_relaxed,bool) or (closing_cash_relaxed and not closing):raise ValueError('cash relaxed proof requires closing mode')
    if proof_memo_entries and not (closing or (prune_prefix and shared_first_states)):raise ValueError('proof memo requires closing or shared prefix proofs')
    if not isinstance(prune_prefix,bool):raise ValueError('invalid prefix pruning mode')
    if not isinstance(shared_first_states,int) or isinstance(shared_first_states,bool) or shared_first_states<0 or (shared_first_states and not prune_prefix):raise ValueError('shared first states requires prefix pruning and nonnegative limit')
    if not isinstance(prune_continuation,bool):raise ValueError('invalid continuation pruning mode')
    if not isinstance(closing,bool):raise ValueError('invalid closing mode')
    if not isinstance(closing_memo_entries,int) or isinstance(closing_memo_entries,bool) or closing_memo_entries<0 or (closing_memo_entries and not closing):raise ValueError('closing memo requires closing mode and nonnegative size')
    if funding not in ('supplied','continuation'):raise ValueError('unsupported funding mode')
    if storage not in ('resident','arena'):raise ValueError('unknown branch storage')
    if not isinstance(max_query_bytes,int) or isinstance(max_query_bytes,bool) or max_query_bytes<0:raise ValueError('invalid query scratch limit')
    if control not in ('typed','python'):raise ValueError('unknown control storage')
    if not isinstance(funding_memo_entries,int) or isinstance(funding_memo_entries,bool) or funding_memo_entries<0:raise ValueError('invalid funding memo size')
    endogenous=funding=='continuation'
    for x in (max_frames,max_allocations,max_prefixes):
        if not isinstance(x,int) or isinstance(x,bool) or x<1:raise ValueError('positive search limits required')
    # Match the oracle's observed-offer canonicalization before action traversal.
    paths=[]
    for path in scenarios:
        events=[]
        for event in path.events:
            if isinstance(event,Purchase):
                if endogenous:event=replace(event,funded_demands=(0,)*len(event.offers))
                if len(event.funded_demands)!=len(event.offers):raise ValueError('search requires supplied funded demands')
                order=sorted(range(len(event.offers)),key=lambda i:(event.offers[i].material,event.offers[i].supplier))
                event=replace(event,offers=tuple(event.offers[i] for i in order),reliability=tuple(event.reliability[i] for i in order),funded_demands=tuple(event.funded_demands[i] for i in order))
            events.append(event)
        paths.append(replace(path,events=tuple(events)))
    paths=tuple(paths);program=compile_calendar(company,initial,paths)
    memo=QueryMemo(program,funding_memo_entries,funding_memo_bytes) if funding_memo_entries else None
    closing_memo=QueryMemo(program,closing_memo_entries,closing_memo_bytes) if closing_memo_entries else None
    proposal_memo=joint_memo=shared_memo=None
    if proof_memo_entries:
        if closing:
            from .closing_certificate import ProposalMemo
            if closing_cash_relaxed:
                from .closing_cash_relaxed_bound import ProfitMemo as JointMemo
            else:
                from .closing_joint_compiled import BoundMemo as JointMemo
            proposal_memo=ProposalMemo(proof_memo_entries);joint_memo=JointMemo(proof_memo_entries)
        if prune_prefix and shared_first_states:
            from .shared_first_bound import BoundMemo
            shared_memo=BoundMemo(proof_memo_entries)
    recourse_memo=None
    if shared_recourse_memo_entries:
        from .shared_first_bound import BoundMemo
        recourse_memo=BoundMemo(shared_recourse_memo_entries)
    def proof_diagnostics():
        if not proof_memo_entries and not shared_recourse_memo_entries:return {}
        return dict(proofMemos={name:dict(capacity=m.capacity,hits=m.hits,misses=m.misses,peakEntries=m.peak_entries)
            for name,m in (('proposal',proposal_memo),('joint',joint_memo),('shared',shared_memo),('recourse',recourse_memo)) if m is not None})
    history=NumericHistory(program,max_nodes=history_nodes,max_integers=history_integers,max_floats=history_floats)
    arena=BranchArena(Resident(company,initial,program,supply=supply),max_branches) if storage=='arena' else None
    policies=PolicyArena(max_nodes=policy_nodes,max_values=policy_values)
    funding_records=FundingRecords(max_nodes=funding_nodes,max_integers=funding_integers,max_floats=funding_floats)
    results=Results(max_results)
    length=len(paths[0].events);stack=ControlStack(max_frames) if control=='typed' else [];returned=None
    stats=dict(allocations=0,prefixes=0,peakFrames=0,transitions=0,fundingQueries=0,fundingDecisions=0,queryScratchBytes=0,peakQueryScratchBytes=0)

    if prune_prefix:stats.update(prefixBoundWork=0,prefixBoundPruned=0,sharedPrefixCalls=0,sharedPrefixSkipped=0)
    if prune_continuation:stats.update(boundEvaluations=0,boundPruned=0,boundUnavailable=0)
    if closing:stats.update(closingWork=0,closingAllocations=0,closingSolves=0,closingUnsupported=0,closingCertificates=0)

    def fail(message,extra=None):
        raise SearchLimit(message,dict(**stats,**proof_diagnostics(),activeFrames=len(stack),control=None if control=='python' else stack.diagnostics(),history=history.diagnostics(),policies=policies.diagnostics(),fundingRecords=funding_records.diagnostics(),results=results.diagnostics(),detail=extra,
            branchArena=None if arena is None else arena.diagnostics(),scope='Completed work only; no policy or approximate value returned.',**({} if memo is None else dict(fundingMemo=memo.diagnostics())),**({} if closing_memo is None else dict(closingMemo=closing_memo.diagnostics()))))

    def push(frame):
        if len(stack)>=max_frames:fail('continuation frame limit')
        stack.append(frame);stats['peakFrames']=max(stats['peakFrames'],len(stack))

    def canonical_split_ok(scenario,index,incumbents):
        if any(int(x)>=0 for x in incumbents):return False
        if any(isinstance(e,Purchase) for e in paths[scenario].events[index+1:]):return False
        event=paths[scenario].events[index]
        if not isinstance(event,Purchase) or len(event.funded_demands)!=len(event.offers):return False
        first={};cap={}
        for i,o in enumerate(event.offers):
            m=o.material
            if m not in first:first[m]=o.stock;cap[m]=event.funded_demands[i]
            else:cap[m]=max(cap[m],event.funded_demands[i])
        return all(first[m]>=cap[m] for m in first)

    def choose(group,index,query=False,offer=None):
        scenario,r,_=group[0]
        canonical=canonical_split_ok(scenario,index,r.data[6]) if not query else False
        frame=AllocationFrame(r,scenario,index,query=query,offer=offer,canonical=canonical)
        if closing:
            allocation_budget=max_allocations-stats['allocations'];work_budget=max_prefixes-stats['prefixes']-stats['closingWork']-stats.get('boundEvaluations',0)-stats.get('prefixBoundWork',0)
            try:chosen=select_closing(company,initial,paths,group,index,query,offer,allocation_budget,work_budget,memo=closing_memo,proposal_memo=proposal_memo,joint_memo=joint_memo,cash_relaxed=closing_cash_relaxed,joint_fallback=closing_joint_fallback)
            except ValueError as exc:
                if 'limit' not in str(exc):raise
                fail(str(exc),dict(closingAllocationBudget=allocation_budget,closingWorkBudget=work_budget,
                    scope='Prior completed work only; interrupted closing work is not returned by the closing solver.'))
            if chosen is None:stats['closingUnsupported']+=1
            else:
                stats['closingSolves']+=1;stats['closingAllocations']+=chosen['enumeratedAllocations']
                stats['allocations']+=chosen['enumeratedAllocations']-1
                stats['closingWork']+=chosen.get('boxes',0)+chosen.get('proposalStates',0)+chosen.get('jointBoundWork',0)
                stats['closingCertificates']+=chosen.get('certificates',0)
                frame=SelectedAllocation(chosen['allocation'])
        return dict(kind='choose',branches=group,index=index,stage='next',frame=frame,
            mass=math.fsum(paths[s].probability for s,_,_ in group),best=None,query=query,offer=offer)


    def fork(r):
        try:return r.fork()
        except BranchLimit as exc:fail(str(exc),exc.diagnostics)

    def release(branches):
        if arena is not None:
            for _,r,_ in branches:r.release()

    def record(r):
        if r.observation_positions!=tuple(range(r.history_count,r.history_count+len(r.observations))):raise AssertionError('incomplete search observation prefix')
        try:node=history.extend(r.history_node,r.observations)
        except HistoryLimit as exc:fail(str(exc),exc.diagnostics)
        r.history_node=node;r.history_count+=len(r.observations)
        r.observations=();r.observation_positions=()

    branches=BranchRows(arena,len(paths)) if arena is not None else []
    for i,path in enumerate(paths):
        if path.probability<=0:continue
        try:r=ArenaResident(arena,arena.create()) if arena is not None else Resident(company,initial,program,supply=supply)
        except BranchLimit as exc:fail(str(exc),exc.diagnostics)
        r.history_node=0;r.history_count=0
        branches.append((i,r,0))
    push(dict(kind='walk',branches=branches,index=0,stage='enter'))
    while stack:
        f=stack[-1]
        if f['kind']=='walk':
            if f['stage']=='enter':
                index=f['index'];branches=f['branches']
                if arena is not None:
                    try:index=advance(branches,index,length,history,stats)
                    except HistoryLimit as exc:fail(str(exc),exc.diagnostics)
                else:
                    while index<length and not isinstance(paths[0].events[index],Purchase):
                        for scenario,r,policy in branches:
                            r.run(scenario,{},start=index,stop=index+1,observe=True);record(r);stats['transitions']+=1
                        index+=1
                f['index']=index
                if index==length:
                    if arena is not None:
                        try:leaves,values=capture(branches,initial,results)
                        except ResultLimit as exc:fail(str(exc),exc.diagnostics)
                    else:
                        leaves=LeafRows(len(branches));values=np.empty(len(branches),dtype=np.float64)
                        for branch_index,(scenario,r,policy) in enumerate(branches):
                            path=paths[scenario];value=float(terminal_value(r.data,initial.cash,initial.arrears,scenario,program.inputs+program.lines,program.terminal_offsets,program.terminal_values,program.terminal_modes,program.terminal_quantities))
                            try:leaf=results.append(scenario,policy,r.history_node,getattr(r,'funding_node',0),value)
                            except ResultLimit as exc:fail(str(exc),exc.diagnostics)
                            leaves.append(leaf)
                            values[branch_index]=path.probability*value
                    returned=(math.fsum(values),leaves);release(f['branches']);stack.pop();continue
                if any(r.history_count!=index for _,r,_ in branches):raise AssertionError('incomplete decision history')
                ids=group_arena_decisions(branches,index,history) if arena is not None else group_decisions([b[1] for b in branches],[b[0] for b in branches],index,[b[1].history_node for b in branches],history)
                groups=Groups(branches,ids)
                f.update(stage='groups',groups=groups,next_group=0,totals=np.empty(len(groups),dtype=np.float64),leaves=LeafRows(len(branches)))
            elif f['stage']=='group-return':
                f['totals'][f['next_group']-1]=returned[0];f['leaves'].extend(returned[1]);f['stage']='groups'
            else:
                if f['next_group']==len(f['groups']):
                    returned=(math.fsum(f['totals']),f['leaves']);release(f['branches']);stack.pop();continue
                group=f['groups'][f['next_group']];f['next_group']+=1;f['stage']='group-return'
                scenario,r,_=group[0];index=f['index']
                if endogenous:
                    stats['fundingDecisions']+=1
                    offers=len(paths[scenario].events[index].offers);required=QueryAnswers.bytes_required(offers,len(initial.held))
                    if stats['queryScratchBytes']+required>max_query_bytes:fail('query scratch byte limit',dict(requiredBytes=stats['queryScratchBytes']+required,capacityBytes=max_query_bytes))
                    scratch=QueryAnswers(offers,len(initial.held));stats['queryScratchBytes']+=scratch.buffer_bytes
                    stats['peakQueryScratchBytes']=max(stats['peakQueryScratchBytes'],stats['queryScratchBytes'])
                    push(dict(kind='fund',branches=group,index=index,stage='next-query',cursor=0,scratch=scratch))
                    continue
                demands=paths[scenario].events[index].funded_demands
                if any(paths[s].events[index].funded_demands!=demands for s,_,_ in group):raise ValueError('supplied funding reveals hidden scenario information')
                push(choose(group,index))
        elif f['kind']=='fund':
            if f['stage']=='actual-return':
                stats['queryScratchBytes']-=f['scratch'].buffer_bytes
                stack.pop();continue
            if f['stage']=='query-return':
                scenario,r,_=f['branches'][0]
                iv,fv,selected=prepare(r,scenario,f['index'],f['active_offer'])
                quantities=[0]*len(initial.held)
                for i,q in enumerate(returned[2]):quantities[int(iv[4+4*i])]+=q
                answer=(tuple(quantities),returned[3],returned[0]/math.fsum(paths[s].probability for s,_,_ in f['branches']))
                f['scratch'].store(f['active_slot'],*answer)
                if memo is not None:memo.put(f['scratch'].memo_key,answer)
                f['stage']='next-query'
                continue
            if f['cursor']<=f['scratch'].offers:
                ordinal=f['cursor'];offer=None if ordinal==0 else ordinal-1;f['cursor']+=1
                scenario,r,_=f['branches'][0];iv,fv,selected=prepare(r,scenario,f['index'],offer)
                slot,ready=f['scratch'].request(ordinal,query_key(iv,fv,selected,r.supply))
                if ready:continue
                if memo is not None:
                    key=memo.key(f['branches'],f['index'],iv,fv);answer=memo.get(key)
                    if answer is not None:
                        f['scratch'].store(slot,*answer);continue
                    f['scratch'].memo_key=key
                f.update(stage='query-return',active_slot=slot,active_offer=offer)
                stats['fundingQueries']+=1;push(choose(f['branches'],f['index'],True,offer));continue
            if arena is not None:
                try:resolved=resolve_answers(f['branches'],f['index'],f['scratch'],funding_records)
                except (BranchLimit,FundingRecordLimit) as exc:fail(str(exc),exc.diagnostics)
            else:
                scenario,r,_=f['branches'][0];event=paths[scenario].events[f['index']]
                demands=tuple(f['scratch'].answer(i+1)['quantities'][o.material] for i,o in enumerate(event.offers))
                references=[]
                for m in range(len(initial.held)):
                    candidates=[i for i,o in enumerate(event.offers) if o.material==m]
                    incumbent=next((i for i in candidates if event.offers[i].supplier==r.data[6][m]),None)
                    references.append(incumbent if incumbent is not None else min(candidates,key=lambda i:(event.offers[i].price,event.offers[i].supplier),default=None))
                joint=f['scratch'].answer(0)
                detail=dict(rule='continuation-v2',referenceSuppliers=tuple(event.offers[i].supplier if i is not None else -1 for i in references),
                    referenceDemands=tuple(demands[i] if i is not None else 0 for i in references),jointQuantities=joint['quantities'],jointGoods=joint['goods'],
                    quoteVectors=tuple(dict(material=o.material,supplier=o.supplier,**f['scratch'].answer(i+1)) for i,o in enumerate(event.offers)))
                resolved=[]
                for scenario,r,policy in f['branches']:
                    child=fork(r);child.set_funded_demands(scenario,f['index'],demands)
                    try:child.funding_node=funding_records.append(getattr(r,'funding_node',0),f['index'],detail)
                    except FundingRecordLimit as exc:fail(str(exc),exc.diagnostics)
                    resolved.append((scenario,child,policy))
            f['stage']='actual-return';actual_frame=choose(resolved,f['index']);actual_frame['ownsBranches']=True;push(actual_frame)
        else:
            if f['stage']=='child-return':
                value=returned[0]/f['mass'];payment=f['payment'];allocation=f['allocation'];best=f['best']
                better=best is None
                if best is not None:
                    old=best[0][0]/f['mass'];cost=best[1];chosen=best[2]
                    tol=1e-9+1e-12*max(abs(value),abs(old));ctol=1e-9+1e-12*max(abs(payment),abs(cost))
                    better=value>old+tol or (abs(value-old)<=tol and (payment<cost-ctol or (abs(payment-cost)<=ctol and (sum(allocation),allocation)<(sum(chosen),chosen))))
                if better:f['best']=(returned,payment,allocation)
                f['stage']='next';continue
            frame=f['frame'];before=int(frame.control[2])
            options={}
            if prune_prefix and f['best'] is not None and isinstance(frame,AllocationFrame):
                from .continuation_prefix import check as check_prefix
                prior=f['best'][0][0]/f['mass']
                options['prune']=lambda prefix,budget:check_prefix(company,initial,paths,f['branches'],f['index'],f['query'],f['offer'],prefix,prior,budget,shared_first_states,stats,memo=shared_memo,recourse_memo=recourse_memo)
                if prune_ranges:
                    from .continuation_range import RangeProof
                    if f.get('rangeProof') is None:f['rangeProof']=RangeProof(company,initial,paths,f['branches'],f['index'],f['query'],f['offer'])
                    def proof(prefix,budget):
                        cut,work=f['rangeProof'].check(prefix,prior,budget,stats)
                        if cut:return True,work,True
                        cut,extra=check_prefix(company,initial,paths,f['branches'],f['index'],f['query'],f['offer'],prefix,prior,budget-work,shared_first_states,stats,memo=shared_memo,recourse_memo=recourse_memo)
                        return cut,work+extra,False
                    options['prune']=proof
            try:allocation=frame.next(max_prefixes=max_prefixes-stats['prefixes']-stats.get('closingWork',0)-stats.get('boundEvaluations',0)-stats.get('prefixBoundWork',0),**options)
            except ActionLimit as exc:
                stats['prefixes']+=int(frame.control[2])-before;fail(str(exc),exc.diagnostics)
            stats['prefixes']+=int(frame.control[2])-before
            if allocation is None:
                if f['best'] is None:raise ValueError('no feasible action at observed decision')
                returned=(*f['best'][0][:2],f['best'][2],f['best'][1])
                if f.get('ownsBranches'):release(f['branches'])
                stack.pop();continue
            if stats['allocations']>=max_allocations:fail('continuation allocation limit')
            stats['allocations']+=1;children=BranchRows(arena,len(f['branches'])) if arena is not None else [];index=f['index'];valid=True
            for scenario,r,policy in f['branches']:
                child=fork(r)
                try:
                    if f['query']:child.funding_purchase(scenario,index,allocation,offer=f['offer'],observe=True)
                    else:child.run(scenario,{index:allocation},start=index,stop=index+1,observe=True)
                except ValueError as exc:
                    if str(exc) not in ('infeasible procurement allocation','production would exceed physical storage'):raise
                    if arena is not None:child.release()
                    valid=False;break
                stats['transitions']+=1
                if not children:payment=purchase_payment(child.observations[-1])
                record(child)
                try:policy_node=policies.append(policy,index,allocation)
                except PolicyLimit as exc:fail(str(exc),exc.diagnostics)
                children.append((scenario,child,policy_node))
            if not valid:
                release(children);continue
            if prune_continuation and f['best'] is not None:
                from .continuation_bound import upper_value
                values=[]
                for scenario,child,_ in children:
                    if stats['prefixes']+stats.get('closingWork',0)+stats['boundEvaluations']+stats.get('prefixBoundWork',0)>=max_prefixes:
                        fail('continuation bound work limit')
                    stats['boundEvaluations']+=1
                    path=paths[scenario]
                    # Future stock is relaxed by the bound. Original future offer
                    # payloads are therefore valid for persistent supply too.
                    bound=upper_value(company,initial,child.snapshot(),path.events[index+1:],path.input_values,path.finished_values)
                    if not math.isfinite(bound):
                        stats['boundUnavailable']+=1;values=None;break
                    values.append(path.probability*bound)
                if values is not None:
                    envelope=math.fsum(values)/f['mass'];prior=f['best'][0][0]/f['mass']
                    tolerance=1e-9+1e-12*max(abs(envelope),abs(prior))
                    if math.isfinite(envelope) and envelope<prior-tolerance:
                        stats['boundPruned']+=1;release(children);continue
            # Same goods/fee reduction as the ledger, not subtraction of cumulative accounts.
            f.update(stage='child-return',allocation=allocation,payment=payment)
            push(dict(kind='walk',branches=children,index=index+1,stage='enter'))
    leaves=[]
    for row in returned[1]:
        scenario,policy_node,history_node,funding_node,value=results.read(row)
        policy=policies.export(policy_node);observations=history.export(history_node)
        replay=Resident(company,initial,program,supply=supply)
        for index,event in enumerate(paths[scenario].events):
            if isinstance(event,Purchase):
                replay.set_funded_demands(scenario,index,decode(observations[index],replay.labels)['fundedDemands'])
                replay.run(scenario,{index:policy[index]},start=index,stop=index+1,observe=True)
            else:replay.run(scenario,{},start=index,stop=index+1,observe=True)
            for actual,expected in zip(replay.observations[-1],observations[index]):
                if not (actual==expected).all():raise AssertionError('selected policy observation replay differs')
        replay_value=float(terminal_value(replay.data,initial.cash,initial.arrears,scenario,program.inputs+program.lines,program.terminal_offsets,program.terminal_values,program.terminal_modes,program.terminal_quantities))
        if replay_value!=value:raise AssertionError('selected terminal value replay differs')
        leaves.append(dict(scenario=scenario,probability=paths[scenario].probability,value=value,state=replay.snapshot(),
            policy=policy,observations=observations,funding=funding_records.export(funding_node)))
    return dict(expectedValue=returned[0],leaves=leaves,diagnostics=dict(**stats,**proof_diagnostics(),control=None if control=='python' else stack.diagnostics(),history=history.diagnostics(),policies=policies.diagnostics(),fundingRecords=funding_records.diagnostics(),results=results.diagnostics(),branchArena=None if arena is None else arena.diagnostics(),**({} if memo is None else dict(fundingMemo=memo.diagnostics())),**({} if closing_memo is None else dict(closingMemo=closing_memo.diagnostics()))),
        supplyMode=supply,fundingRule=funding,scope='Exact conditional search under declared funding; Python control frames, compiled kernels.')
