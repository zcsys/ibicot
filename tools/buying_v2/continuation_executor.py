"""Compiled event transitions for typed continuation programs.

This verification adapter decodes/validates once and packs a state per step.
A persistent compiled state arena remains explicit work. Transitions do not
delegate execution to the reference ledger.
"""
from dataclasses import replace
import numpy as np
import math
from .jit import njit
from .float_sum import add,finish
from .continuation_program import decode_calendar,_array
from .phase_ledger import Accounts,Book,validate_state,equity

ACCOUNT_NAMES=('goods_paid','conversion_paid','sales','cogs','fee_income','fee_expense','rent_charge','rent_paid')


@njit
def _dot(q,p):
    total=correction=0.
    for i in range(len(q)):total,correction=add(total,correction,q[i]*p[i])
    return finish(total,correction)


@njit
def _step(kind,label,iv,fv,scalars,held,basis,stock,stock_basis,quotes,book_label,book_stock,book_basis,book_quotes,rented,fixed_assets):
    if kind==0:raise ValueError('compiled purchase transition not implemented')
    if rented and kind in (1,2,3,4):raise ValueError('trading after rent requires a new tick')
    scalars=scalars.copy();stock=stock.copy();stock_basis=stock_basis.copy();quotes=quotes.copy()
    book_stock=book_stock.copy();book_basis=book_basis.copy();book_quotes=book_quotes.copy()
    sold=np.zeros(len(stock),dtype=np.int64);details=np.zeros(5,dtype=np.float64)
    clear_phases=False
    if kind==1:
        if book_label!=-1:raise ValueError('sales books cannot overlap')
        book_label=label;book_stock=stock.copy();book_basis=stock_basis.copy();book_quotes=quotes.copy()
    elif kind==2 or kind==3:
        if book_label!=label:raise ValueError('missing/mismatched sales book')
        if kind==2:
            for i in range(len(stock)):sold[i]=min(iv[1+i],math.floor(book_stock[i]))
        else:
            cursor=1+iv[0];groups=iv[cursor];cursor+=1
            for _ in range(groups):
                size=iv[cursor];cursor+=1;order=iv[cursor:cursor+size].copy();cursor+=size
                for j in range(1,size):
                    i=order[j];k=j-1
                    while k>=0 and (book_quotes[i]<book_quotes[order[k]] or (book_quotes[i]==book_quotes[order[k]] and i<order[k])):
                        order[k+1]=order[k];k-=1
                    order[k+1]=i
                cumulative=0
                for j in range(size):
                    i=order[j]
                    if j:
                        previous=order[j-1]
                        if iv[1+previous]<iv[1+i] or (book_quotes[previous]==book_quotes[i] and iv[1+previous]!=iv[1+i]):
                            raise ValueError('shared demand must be consistent with frozen quotes')
                    sold[i]=min(math.floor(book_stock[i]),max(0,iv[1+i]-cumulative));cumulative+=sold[i]
        for i in range(len(stock)):
            if sold[i]>stock[i]:raise ValueError('book stock was consumed outside settlement')
            remaining=stock[i]-sold[i]
            value=(remaining+sold[i])*stock_basis[i]-sold[i]*book_basis[i]
            if value < -1e-8:raise ValueError('book sale exceeds inventory book value')
            stock[i]=remaining
            if sold[i]>0:stock_basis[i]=max(0.,value)/remaining if remaining else 0.
        sales=_dot(sold,book_quotes);cogs=_dot(sold,book_basis);fee=fv[0]
        scalars[0]=scalars[0]+sales+fee;scalars[3]+=fee
        scalars[7]+=sales;scalars[8]+=cogs;scalars[9]+=fee
        details[0]=sales;details[1]=cogs;details[2]=fee
        book_label=-1
    elif kind==4:
        quotes=fv.copy()
    elif kind==5:
        if rented or book_label!=-1:raise ValueError('duplicate rent or unsettled sales book at billing')
        before=scalars[0]+fixed_assets-scalars[1]+_dot(held,basis)+_dot(stock,stock_basis)
        eligible=before>=fv[1];charge=fv[0] if eligible else 0.
        paid=min(scalars[0],scalars[1]+charge) if eligible else 0.
        scalars[0]-=paid;scalars[1]=scalars[1]+charge-paid;scalars[11]+=charge;scalars[12]+=paid
        rented=True;details[0]=1. if eligible else 0.;details[1]=before;details[2]=charge;details[3]=paid
    elif kind==6:
        if book_label!=-1:raise ValueError('unsettled phase book at tick end')
        net=scalars[3]-scalars[4]
        scalars[2]=scalars[2]+fv[0]*(net-scalars[2]);scalars[3]=0.;scalars[4]=0.
        rented=False;clear_phases=True;details[0]=net
    else:raise ValueError('unsupported compiled event kind')
    return scalars,stock,stock_basis,quotes,book_label,book_stock,book_basis,book_quotes,rented,clear_phases,sold,details


class Executor:
    """Validation/trace adapter around the compiled event kernel, not a planner."""
    def __init__(self,company,initial,program):
        if program.version==4:raise ValueError('native state requires Resident execution')
        self.company=company;self.program=program
        scenarios=decode_calendar(program,company,initial)
        self.events=tuple(e for scenario in scenarios for e in scenario.events)
        self.labels=list(program.labels)
        if initial.book is not None and initial.book.label not in self.labels:self.labels.append(initial.book.label)

    def apply(self,state,index,allocation=None):
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<len(self.events):raise ValueError('invalid compiled event index')
        validate_state(self.company,state)
        program=self.program;event=self.events[index];kind=int(program.event_kinds[index])
        if kind==0:
            after,detail=self._purchase(state,index,allocation)
            return self._reconcile(state,after,event,detail)
        if allocation is not None:raise ValueError('allocation supplied for a non-purchase event')
        if state.book is not None and state.book.label not in self.labels:raise ValueError('unknown compiled book label')
        n=len(state.finished)
        scalar=_array([state.cash,state.arrears,state.switching_net_ema,state.tick_fee_income,state.tick_fee_expense,
                       *(getattr(state.accounts,name) for name in ACCOUNT_NAMES)],'<f8')
        book=state.book
        arrays=(_array(state.held,'<i8'),_array(state.basis,'<f8'),_array(state.finished,'<i8'),
                _array(state.finished_basis,'<f8'),_array(state.quotes,'<f8'))
        bq=_array(book.quantity if book else (0,)*n,'<i8')
        bb=_array(book.basis if book else (0.,)*n,'<f8');bp=_array(book.quote if book else (0.,)*n,'<f8')
        iv=program.integers[program.integer_offsets[index]:program.integer_offsets[index+1]]
        fv=program.floats[program.float_offsets[index]:program.float_offsets[index+1]]
        result=_step(kind,int(program.event_labels[index]),iv,fv,scalar,*arrays,
                     self.labels.index(book.label) if book else -1,bq,bb,bp,state.rent_settled,self.company.fixed_assets)
        money,stock,basis,quotes,label,bq,bb,bp,rented,clear,sold,details=result
        asints=lambda a:tuple(int(x) for x in a)
        asfloats=lambda a:tuple(float(x) for x in a)
        next_book=None if label<0 else Book(self.labels[label],asints(bq),asfloats(bb),asfloats(bp))
        after=replace(state,cash=float(money[0]),arrears=float(money[1]),switching_net_ema=float(money[2]),
            tick_fee_income=float(money[3]),tick_fee_expense=float(money[4]),accounts=Accounts(*asfloats(money[5:])),
            finished=asints(stock),finished_basis=asfloats(basis),quotes=asfloats(quotes),book=next_book,
            rent_settled=bool(rented),completed_phases=() if clear else state.completed_phases)
        if kind==1:detail=dict(openingStock=state.finished,openingBasis=state.finished_basis,openingQuote=state.quotes)
        elif kind in (2,3):
            detail=dict(sold=asints(sold),sales=float(details[0]),cogs=float(details[1]),feeIncome=float(details[2]))
            if kind==3:detail.update(sharedGroups=event.groups,quoteDemands=event.demand,groupSales=tuple(sum(int(sold[i]) for i in group) for group in event.groups))
        elif kind==4:detail=dict(quotes=after.quotes)
        elif kind==5:detail=dict(eligible=bool(details[0]),equityBeforeBilling=float(details[1]),charge=float(details[2]),paid=float(details[3]),arrears=after.arrears)
        else:detail=dict(netTransfers=float(details[0]),nextTransferEMA=after.switching_net_ema)
        return self._reconcile(state,after,event,detail)

    def _reconcile(self,state,after,event,detail):
        validate_state(self.company,after)
        earnings=after.accounts.earnings-state.accounts.earnings
        residual=equity(self.company,after)-equity(self.company,state)-earnings
        tolerance=1e-6+1e-12*max(abs(equity(self.company,state)),abs(equity(self.company,after)))
        if abs(residual)>tolerance:raise AssertionError('compiled event equity does not reconcile')
        a,b=state.accounts,after.accounts
        cash_expected=state.cash+(b.sales-a.sales)+(b.fee_income-a.fee_income)-(b.goods_paid-a.goods_paid)-(b.conversion_paid-a.conversion_paid)-(b.fee_expense-a.fee_expense)-(b.rent_paid-a.rent_paid)
        if abs(after.cash-cash_expected)>tolerance:raise AssertionError('compiled event cash does not reconcile')
        detail.update(event=type(event).__name__,label=event.label,cash=after.cash,equity=equity(self.company,after),postedEarnings=earnings,equityResidual=residual)
        return after,detail

    def _purchase(self,state,index,allocation):
        from .continuation_purchase import purchase
        event=self.events[index];c=self.company;p=self.program
        if state.rent_settled:raise ValueError('trading after rent requires a new tick')
        if event.label in state.completed_phases:raise ValueError('company purchasing phase already completed this tick')
        if allocation is None:raise ValueError('purchase allocation required')
        if len(event.funded_demands)!=len(event.offers):raise ValueError('purchase requires resolved funded demands')
        if any(q<0 or q%o.lot for q,o in zip(event.funded_demands,event.offers)):raise ValueError('invalid funded whole-lot quantity')
        if len(allocation)!=len(event.offers):raise ValueError('allocation length differs from offers')
        if any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('allocation must contain nonnegative integers')
        iv=p.integers[p.integer_offsets[index]:p.integer_offsets[index+1]]
        fv=p.floats[p.float_offsets[index]:p.float_offsets[index+1]]
        ints=lambda x:_array(x,'<i8')
        floats=lambda x:_array(x,'<f8')
        recipes=ints(tuple(q for line in c.lines for q in line.recipe)).reshape(len(c.lines),len(state.held))
        result=purchase(iv,fv,ints(allocation),state.cash,ints(state.held),floats(state.basis),
            ints(state.finished),floats(state.finished_basis),floats(state.quotes),ints(state.incumbents),
            ints(c.slots),floats(c.spaces),c.storage,c.fixed_assets,state.arrears,state.switching_net_ema,
            recipes,ints(tuple(line.max_batches for line in c.lines)),ints(tuple(line.output_qty for line in c.lines)),
            floats(tuple(line.conversion for line in c.lines)),floats(tuple(line.output_space for line in c.lines)),
            ints(c.finished_caps),c.margin_band)
        cash,held,basis,stock,stock_basis,preferences,goods,fees,outputs,conversion,overhead,gate,purchased_cash=result
        ti=lambda a:tuple(int(x) for x in a)
        tf=lambda a:tuple(float(x) for x in a)
        fee=sum(tf(fees))
        accounts=replace(state.accounts,goods_paid=state.accounts.goods_paid+goods,
            fee_expense=state.accounts.fee_expense+fee,conversion_paid=state.accounts.conversion_paid+conversion)
        after=replace(state,cash=float(cash),held=ti(held),basis=tf(basis),finished=ti(stock),
            finished_basis=tf(stock_basis),incumbents=ti(preferences),accounts=accounts,
            tick_fee_expense=state.tick_fee_expense+fee,completed_phases=state.completed_phases+(event.label,))
        return after,dict(goods=float(goods),fees=tf(fees),preferences=ti(preferences),outputs=ti(outputs),
            conversion=float(conversion),gateOverhead=float(overhead),gateEquity=float(gate),
            cashAfterProcurement=float(purchased_cash),feeRecipients=tuple(state.incumbents[i] if q else -1 for i,q in enumerate(fees)))
