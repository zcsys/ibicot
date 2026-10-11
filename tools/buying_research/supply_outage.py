"""Close the raw-water supplier market during ticks 181–360, retaining assets.

Offers are unavailable only at the wholesale settlement stage. Physical goods
are held in escrow for that call and returned immediately afterward. Extraction,
production, accounting and the rest of the tick are unchanged. This is distinct
from the production-capacity outage in scenarios.py.
"""
import inspect
import numpy as np
from economy.kernel import numba as N
from . import engine as E
from . import run as R
from .scenarios import Scenario

closed=False
original_baseline=N.plan_and_buy_inputs
original_procure=E.procure
stock_position=list(inspect.signature(original_procure.py_func).parameters).index('stock')


def unavailable_call(stock,operation):
    ids=np.arange(0,len(stock),4)
    escrow=stock[ids].copy();stock[ids]=0
    try:return operation()
    finally:stock[ids]+=escrow


def baseline(world,cfg,tick):
    if closed:return unavailable_call(world.t0Inv,lambda:original_baseline(world,cfg,tick))
    return original_baseline(world,cfg,tick)


def procure(*args):
    if closed and args[2]==1:return unavailable_call(args[stock_position],lambda:original_procure(*args))
    return original_procure(*args)


class SupplyScenario(Scenario):
    def __init__(self,name,rt,path):
        if name!='supplier-outage':raise ValueError('Use --scenario supplier-outage with this module')
        super().__init__('none',rt,path);self.name=name;self.write()

    def before(self,t,engine,recorder):
        global closed
        closed=181<=t<=360
        if t in (181,361):
            self.events.append(dict(tick=t,kind='rawWaterOffersAvailable',value=not closed,
                note='Physical inventory remains owned and recorded; only offers at wholesale settlement are withheld.'))
            self.write()


if __name__=='__main__':
    N.plan_and_buy_inputs=baseline;E.procure=procure;R.Scenario=SupplyScenario
    R.main()
