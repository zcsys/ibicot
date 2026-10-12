"""Opt-in exact prefix-proof bridge; unsupported or unbudgeted proofs cannot prune."""
from dataclasses import replace
import math
from .continuation_closing import purchase_event
from .prefix_continuation_bound import upper_value


def check(company,initial,paths,group,index,query,offer,prefix,prior,budget,shared_states,stats,memo=None,recourse_memo=None):
    event=purchase_event(paths,group,index,query,offer)
    state=group[0][1].snapshot();mass=math.fsum(paths[s].probability for s,_,_ in group)
    work=0
    def inferior(value):
        return math.isfinite(value) and value<prior-(1e-9+1e-12*max(abs(value),abs(prior)))
    if shared_states:
        count=math.prod(line.max_batches+1 for line in company.lines)
        per_scenario=1 if len(company.lines)==1 else len(company.lines)+1
        reservation=1+count*(1+len(group)*per_scenario)
        if count<=shared_states and reservation<=budget:
            posterior=tuple((paths[s].probability,replace(paths[s],events=paths[s].events[index+1:])) for s,_,_ in group)
            if len(company.lines)==1:
                from .shared_first_bound import bound
                result=bound(company,initial,state,event,prefix,posterior,max_first_batches=shared_states-1,memo=memo)
            else:
                from .shared_joint_first_bound import bound
                result=bound(company,initial,state,event,prefix,posterior,max_first_states=shared_states,memo=memo,recourse_memo=recourse_memo)
            work=1+result['firstBatchStates']+result['scenarioEvaluations']
            if work>reservation:raise AssertionError('shared prefix bound exceeded reservation')
            stats['sharedPrefixCalls']+=1;stats['prefixBoundWork']+=work
            if inferior(result['value']):
                stats['prefixBoundPruned']+=1;return True,work
        else:stats['sharedPrefixSkipped']+=1
    if len(group)<=budget-work:
        values=[]
        for scenario,_,_ in group:
            path=paths[scenario];value=upper_value(company,initial,state,event,prefix,path.events[index+1:],path.input_values,path.finished_values)
            work+=1;stats['prefixBoundWork']+=1
            if not math.isfinite(value):return False,work
            values.append(path.probability*value)
        if inferior(math.fsum(values)/mass):
            stats['prefixBoundPruned']+=1;return True,work
    return False,work
