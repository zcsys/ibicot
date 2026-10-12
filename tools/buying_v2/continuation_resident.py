"""Resident typed calendar replay. Supplied allocations/funding, no policy search."""
from dataclasses import replace
import numpy as np
from .jit import njit
from .continuation_program import decode_calendar,_array
from .continuation_executor import _step,_dot,ACCOUNT_NAMES
from .continuation_purchase import purchase
from .continuation_observation import emit
from .phase_ledger import Accounts,Book,validate_state


@njit
def _replay(state,company,kinds,labels,io,fo,integers,floats,start,stop,ao,allocations,observe,persistent,scenario_stop,query_index,query_iv,query_fv):
    money,held,basis,stock,stock_basis,quotes,incumbents,book_label,bq,bb,bp,rented,phases,phase_count=state
    money=money.copy();held=held.copy();basis=basis.copy();stock=stock.copy();stock_basis=stock_basis.copy()
    quotes=quotes.copy();incumbents=incumbents.copy();bq=bq.copy();bb=bb.copy();bp=bp.copy();phases=phases.copy()
    slots,spaces,storage,fixed,recipe,limits,yields,conversion,output_space,caps,band=company
    if persistent:integers=integers.copy()
    observations=[]
    for index in range(start,stop):
        kind=kinds[index];label=labels[index]
        physical=integers[io[index]:io[index+1]]
        iv=physical;fv=floats[fo[index]:fo[index+1]]
        hypothetical=index==query_index
        if hypothetical:iv=query_iv;fv=query_fv
        old=money.copy()
        allocation=np.empty(0,np.int64);fees=np.empty(0,np.float64);outputs=np.empty(0,np.int64)
        sold=np.empty(0,np.int64);details=np.zeros(5);goods=paid=0.
        before=money[0]+fixed-money[1]+_dot(held,basis)+_dot(stock,stock_basis)
        if kind==0:
            if rented:raise ValueError('trading after rent requires a new tick')
            for j in range(phase_count):
                if phases[j]==label:raise ValueError('company purchasing phase already completed this tick')
            allocation=allocations[ao[index-start]:ao[index-start+1]]
            old_incumbents=incumbents.copy()
            result=purchase(iv,fv,allocation,money[0],held,basis,stock,stock_basis,quotes,incumbents,
                slots,spaces,storage,fixed,money[1],money[2],recipe,limits,yields,conversion,output_space,caps,band)
            cash,held,basis,stock,stock_basis,incumbents,goods,fees,outputs,paid,overhead,gate,purchased_cash=result
            if hypothetical:incumbents=old_incumbents
            fee=_dot(np.ones(len(fees)),fees)
            money[0]=cash;money[4]+=fee;money[5]+=goods;money[6]+=paid;money[10]+=fee
            phases[phase_count]=label;phase_count+=1
            if persistent:
                for future in range(index+1,scenario_stop):
                    if kinds[future]!=0:continue
                    offset=io[future]
                    for j in range(integers[offset]):
                        for k in range(iv[0]):
                            if integers[offset+4+4*j]==iv[4+4*k] and integers[offset+5+4*j]==iv[5+4*k]:
                                consumed=allocation[k]
                                if hypothetical:
                                    for physical_index in range(physical[0]):
                                        if physical[4+4*physical_index]==iv[4+4*k] and physical[5+4*physical_index]==iv[5+4*k]:
                                            consumed=min(consumed,physical[6+4*physical_index]);break
                                integers[offset+6+4*j]-=consumed
                                if integers[offset+6+4*j]<0:raise ValueError('persistent supply became negative')
                                break
        else:
            result=_step(kind,label,iv,fv,money,held,basis,stock,stock_basis,quotes,book_label,bq,bb,bp,rented,fixed)
            money,stock,stock_basis,quotes,book_label,bq,bb,bp,rented,clear,sold,details=result
            if clear:phase_count=0
        after=money[0]+fixed-money[1]+_dot(held,basis)+_dot(stock,stock_basis)
        earnings=(money[7]-money[8]+money[9]-money[10]-money[11])-(old[7]-old[8]+old[9]-old[10]-old[11])
        tolerance=1e-6+1e-12*max(abs(before),abs(after))
        if abs(after-before-earnings)>tolerance:raise AssertionError('resident equity does not reconcile')
        expected=old[0]+(money[7]-old[7])+(money[9]-old[9])-(money[5]-old[5])-(money[6]-old[6])-(money[10]-old[10])-(money[12]-old[12])
        if abs(money[0]-expected)>tolerance:raise AssertionError('resident cash does not reconcile')
        if not np.isfinite(money).all() or not np.isfinite(basis).all() or not np.isfinite(stock_basis).all():
            raise ValueError('nonfinite resident state')
        if money[0]<0 or money[1]<0 or np.any(held<0) or np.any(stock<0):raise ValueError('invalid resident resources')
        if storage-_dot(held,spaces)-_dot(stock,output_space)<-1e-8:raise ValueError('resident inventory exceeds storage')
        if observe:
            observations.append(emit(kind,label,iv,fv,money,after,earnings,stock,stock_basis,quotes,sold,details,allocation,incumbents,fees,outputs,goods,paid))
    return (money,held,basis,stock,stock_basis,quotes,incumbents,book_label,bq,bb,bp,rented,phases,phase_count),observations,integers


class Resident:
    """Own typed state across compiled calendar segments; fork without ledger objects."""
    def __init__(self,company,initial,program,*,supply='independent-snapshots'):
        self.company=company;self.initial=initial;self.program=program;self.observations=();self.observation_positions=()
        if supply not in ('independent-snapshots','persistent-arrivals'):raise ValueError('unknown supply mode')
        self.supply=supply;self.integers=program.integers.copy()
        scenarios=decode_calendar(program,company,initial)
        if supply=='persistent-arrivals':
            from .phase_ledger import Purchase
            for path in scenarios:
                previous={}
                for event in path.events:
                    if not isinstance(event,Purchase):continue
                    for offer in event.offers:
                        key=(offer.material,offer.supplier)
                        if offer.stock<previous.get(key,0):raise ValueError('persistent supply requires nondecreasing stock totals')
                        previous[key]=offer.stock
        self.events=tuple(e for path in scenarios for e in path.events)
        self.labels=list(program.labels)
        for label in (*initial.completed_phases,*(() if initial.book is None else (initial.book.label,))):
            if label not in self.labels:self.labels.append(label)
        ints=lambda x:_array(x,'<i8').copy()
        floats=lambda x:_array(x,'<f8').copy()
        c=company;s=initial;n=len(s.finished)
        quantities=floats if program.version==4 else ints
        self.native=program.version==4
        self.company_data=(quantities(c.slots),floats(c.spaces),c.storage,c.fixed_assets,
            ints(tuple(q for line in c.lines for q in line.recipe)).reshape(n,len(s.held)),
            ints(tuple(line.max_batches for line in c.lines)),ints(tuple(line.output_qty for line in c.lines)),
            floats(tuple(line.conversion for line in c.lines)),floats(tuple(line.output_space for line in c.lines)),ints(c.finished_caps),c.margin_band)
        book=s.book
        phases=np.full(len(self.events)+len(s.completed_phases),-1,dtype=np.int64)
        for j,label in enumerate(s.completed_phases):phases[j]=self.labels.index(label)
        self.data=(floats((s.cash,s.arrears,s.switching_net_ema,s.tick_fee_income,s.tick_fee_expense,
                   *(getattr(s.accounts,name) for name in ACCOUNT_NAMES))),quantities(s.held),floats(s.basis),quantities(s.finished),
                   floats(s.finished_basis),floats(s.quotes),ints(s.incumbents),self.labels.index(book.label) if book else -1,
                   quantities(book.quantity if book else (0,)*n),floats(book.basis if book else (0.,)*n),
                   floats(book.quote if book else (0.,)*n),s.rent_settled,phases,len(s.completed_phases))

    def fork(self):
        other=object.__new__(type(self));other.__dict__=self.__dict__.copy()
        other.data=tuple(x.copy() if isinstance(x,np.ndarray) else x for x in self.data)
        other.integers=self.integers.copy()
        other.observations=tuple((i.copy(),f.copy()) for i,f in self.observations)
        return other

    def snapshot(self):
        money,held,basis,stock,stock_basis,quotes,incumbents,label,bq,bb,bp,rented,phases,count=self.data
        ti=lambda x:tuple(int(v) for v in x)
        tf=lambda x:tuple(float(v) for v in x)
        tq=tf if self.native else ti
        book=None if label<0 else Book(self.labels[label],tq(bq),tf(bb),tf(bp))
        result=replace(self.initial,cash=float(money[0]),arrears=float(money[1]),switching_net_ema=float(money[2]),
            tick_fee_income=float(money[3]),tick_fee_expense=float(money[4]),accounts=Accounts(*tf(money[5:])),
            held=tq(held),basis=tf(basis),finished=tq(stock),finished_basis=tf(stock_basis),quotes=tf(quotes),
            incumbents=ti(incumbents),book=book,rent_settled=bool(rented),completed_phases=tuple(self.labels[i] for i in phases[:count]))
        validate_state(self.company,result)
        return result

    def run(self,scenario,allocations,*,start=0,stop=None,observe=False):
        """Atomically run a scenario segment. Allocation keys are local event indices."""
        if not isinstance(observe,bool):raise ValueError('invalid observation mode')
        p=self.program
        if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid scenario index')
        base=int(p.scenario_offsets[scenario]);length=int(p.scenario_offsets[scenario+1])-base
        stop=length if stop is None else stop
        if any(not isinstance(x,int) or isinstance(x,bool) for x in (start,stop)) or not 0<=start<=stop<=length:raise ValueError('invalid event range')
        if any(not isinstance(i,int) or isinstance(i,bool) for i in allocations):raise ValueError('invalid allocation index')
        required={i for i in range(start,stop) if p.event_kinds[base+i]==0}
        if set(allocations)!=required:raise ValueError('missing or extra purchase allocation indices')
        offsets=[0];values=[]
        for i in range(start,stop):
            if i in required:
                event=self.events[base+i];allocation=allocations[i]
                if len(event.funded_demands)!=len(event.offers):raise ValueError('purchase requires resolved funded demands')
                if any(q<0 or q%o.lot for q,o in zip(event.funded_demands,event.offers)):raise ValueError('invalid funded whole-lot quantity')
                if len(allocation)!=len(event.offers) or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('invalid purchase allocation')
                values.extend(allocation)
            offsets.append(len(values))
        # All state arrays are copied inside the kernel. Failure cannot commit a partial segment.
        data,records,integers=_replay(self.data,self.company_data,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,
            self.integers,p.floats,base+start,base+stop,_array(offsets,'<i8'),_array(values,'<i8'),observe,self.supply=='persistent-arrivals',int(p.scenario_offsets[scenario+1]),-1,_array((),'<i8'),_array((),'<f8'))
        self.data=data;self.integers=integers
        self.observations+=tuple(records)
        if observe:self.observation_positions+=tuple(range(start,stop))

    def funding_purchase(self,scenario,index,allocation,*,offer=None,observe=True):
        """Execute one continuation-v2 hypothetical purchase on this branch.

        Current fees are removed and incumbents held; future fees remain real.
        Caller forks before counterfactual execution. This does not derive bids.
        """
        from .continuation_query import prepare
        iv,fv,selected=prepare(self,scenario,index,offer)
        if not isinstance(observe,bool):raise ValueError('invalid observation mode')
        if len(allocation)!=len(selected) or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('invalid query allocation')
        p=self.program;event=int(p.scenario_offsets[scenario])+index
        data,records,integers=_replay(self.data,self.company_data,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,
            self.integers,p.floats,event,event+1,_array((0,len(allocation)),'<i8'),_array(allocation,'<i8'),observe,
            self.supply=='persistent-arrivals',int(p.scenario_offsets[scenario+1]),event,iv,fv)
        self.data=data;self.integers=integers;self.observations+=tuple(records)
        if observe:self.observation_positions+=(index,)
        return tuple(int(i) for i in selected)

    def set_funded_demands(self,scenario,index,demands):
        """Set a resolved actual bid vector in the preallocated event payload."""
        from .continuation_query import prepare
        prepare(self,scenario,index)  # Validate the scenario/event boundary.
        p=self.program;event=int(p.scenario_offsets[scenario])+index
        start=int(p.integer_offsets[event]);count=int(self.integers[start])
        if self.integers[start+1]!=count:raise ValueError('funding payload was not preallocated')
        if len(demands)!=count or any(not isinstance(q,int) or isinstance(q,bool) or q<0 or q%int(self.integers[start+7+4*i]) for i,q in enumerate(demands)):raise ValueError('invalid resolved funded demands')
        values=_array(demands,'<i8')
        self.integers[start+4+4*count:start+4+5*count]=values
