"""Explicit local-information alternative: floor own first requests by own sales.

R1 counts one first submitted request and records retries separately. A firm can
receive fallback sales without that first request. This treatment uses both
observations, preventing a zero forecast for a firm that actually sold goods.
It does not sum them (which would double-count first requests that were filled),
change market intelligence, post extra demand or alter the sell-side learner.
Forecast-error telemetry retains the same first-request target as the control;
it is not an estimate of total unobserved demand.
"""
import json
import numpy as np
from . import engine as E
from . import run as R

OriginalEngine=E.ResearchEngine


class LocalSalesFloor(OriginalEngine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.treatment not in ('local','hybrid'):raise ValueError('sales-floor alternative is local or hybrid')
        self.options['salesFloor']=True
        p=self.path/'research-config.json';data=json.loads(p.read_text());data['options']=self.options
        data['learningSignal']='max(own first submitted requests, own actual units sold); one-tick lag'
        p.write_text(json.dumps(data,indent=2)+'\n')

    def step(self,tick,state):
        super().step(tick,state)
        alpha=2/(self.options['window']+1)
        self.local1+=alpha*np.maximum(0.,self.w.t1Sold-self.local_requests1)
        self.local2+=alpha*np.maximum(0.,self.w.t2Sold[:self.lc]-self.local_requests2)


if __name__=='__main__':
    E.ResearchEngine=LocalSalesFloor
    R.main()
