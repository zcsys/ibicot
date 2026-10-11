"""Explicit exogenous research interventions; no production defaults or files change."""
import json
import numpy as np
from economy.core import model as M


class Scenario:
    def __init__(self, name, rt, path):
        self.name=name;self.rt=rt;self.path=path;self.events=[];self.original={}
        if name not in ('none','demand-up','demand-down','raw-outage','quote-shock','small-cash','large-fees','asymmetric','reentry'):
            raise ValueError('unknown scenario '+name)
        w=rt.world
        if name in ('small-cash','asymmetric'):
            for tier in ('t0','t1','t2'):
                cash=getattr(w,tier+'Cash');active=M.N0 if tier=='t0' else M.N1 if tier=='t1' else rt.cfg['t2FirmCount']
                multiplier=np.full(active,.001) if name=='small-cash' else np.where(np.arange(active)%2==0,.01,1.99)
                cash[:active]*=multiplier
            self.events.append(dict(tick=0,kind='initialCashEndowment',description=name))
        if name=='large-fees':
            w.lm1*=10;w.lm2*=10;w.lm3*=10
            self.events.append(dict(tick=0,kind='initialLoyaltyMultiples',multiplier=10,
                                    note='Existing annual adaptation remains enabled.'))
        self.write()

    def write(self):
        (self.path/'interventions.json').write_text(json.dumps(dict(scenario=self.name,events=self.events),indent=2)+'\n')

    def before(self,t,engine,recorder):
        cfg=self.rt.cfg;w=self.rt.world;event=None
        if self.name in ('demand-up','demand-down'):
            if t==181:
                self.original['activation']=cfg['distributorActivation']
                cfg['distributorActivation']*=2 if self.name=='demand-up' else .1
                event=dict(kind='activation',value=cfg['distributorActivation'])
            elif t==361:
                cfg['distributorActivation']=self.original['activation'];event=dict(kind='activation',value=cfg['distributorActivation'])
        elif self.name=='raw-outage':
            if t==181:
                self.original['t0Capacity']=cfg['t0Capacity'];cfg['t0Capacity']=0
                event=dict(kind='t0ProductionCapacity',value=0,note='All extractors stop production; inventory remains tradable.')
            elif t==361:
                cfg['t0Capacity']=self.original['t0Capacity'];event=dict(kind='t0ProductionCapacity',value=cfg['t0Capacity'])
            if t in (181,361):recorder.structure['t0'][-1][:]=cfg['t0Capacity']
        elif self.name=='quote-shock' and t==181:
            w.t1Price[w.t1Operates.astype(bool)]*=2
            event=dict(kind='oneTimeT1QuoteMultiplier',value=2,note='Subsequent existing price learning remains active.')
        elif self.name=='reentry' and t==361 and engine is not None:
            for name in ('local1','local2','market1','market2'):getattr(engine,name).fill(0)
            event=dict(kind='forgetProcurementHistory',value=0,note='Synthetic re-entry with zero prior; physical assets unchanged.')
        if event is not None:
            self.events.append(dict(tick=t,**event));self.write()
