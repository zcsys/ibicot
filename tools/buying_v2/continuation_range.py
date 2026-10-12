"""Optional whole-prefix-tail certificate with free inputs and conversion costs."""
import math
from .continuation_closing import purchase_event
from .continuation_bound import upper_value


class RangeProof:
    def __init__(self,company,initial,paths,group,index,query,offer):
        self.company=company;self.initial=initial;self.paths=paths;self.group=group;self.index=index
        self.event=purchase_event(paths,group,index,query,offer)
        self.state=group[0][1].snapshot();self.ceiling=None

    def check(self,prefix,prior,budget,stats):
        required=(len(self.group) if self.ceiling is None else 0)+1
        if budget<required:return False,0
        work=0
        if self.ceiling is None:
            values=[];mass=math.fsum(self.paths[s].probability for s,_,_ in self.group)
            for scenario,_,_ in self.group:
                path=self.paths[scenario]
                value=upper_value(self.company,self.initial,self.state,(self.event,)+path.events[self.index+1:],path.input_values,path.finished_values,include_costs=True,free_inputs=True)
                values.append(path.probability*value);work+=1
            self.ceiling=math.fsum(values)/mass
        paid=0.
        for offer,q in zip(self.event.offers,prefix):
            # Lower bound on mandatory goods payment, also valid for every
            # larger last coordinate and every nonnegative suffix.
            term=math.nextafter(q*offer.price,-math.inf) if q else 0.
            paid=math.nextafter(paid+term,-math.inf)
        work+=1;stats['prefixBoundWork']+=work
        if not math.isfinite(self.ceiling):return False,work
        scale=max(1.,abs(self.ceiling),abs(paid),abs(self.initial.cash),abs(self.state.cash))
        cushion=(1e-9+1e-12*scale)*(len(self.event.offers)+len(prefix)+1)
        upper=math.nextafter(self.ceiling-paid+cushion,math.inf)
        cut=upper<prior-(1e-9+1e-12*max(abs(upper),abs(prior)))
        if cut:stats['prefixBoundPruned']+=1
        return cut,work
