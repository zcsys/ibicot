"""Independent small-company event ledger for continuation-value verification.

Explicit frozen quote-funded demands are inputs to a purchase event, not a new
funding model. Events preserve phase-book stock/basis, receipt timing, D1/D2,
production gates and rent liabilities. No production engine is imported.
"""
from dataclasses import dataclass, replace
import math
from .industry_oracle import Problem, Line, Offer, validate, evaluate
from .quantity_value import value_at


@dataclass(frozen=True)
class Company:
    spaces: tuple
    slots: tuple
    storage: float
    lines: tuple[Line, ...]
    finished_caps: tuple
    fixed_assets: float
    margin_band: float = .05


@dataclass(frozen=True)
class Accounts:
    goods_paid: float = 0.
    conversion_paid: float = 0.
    sales: float = 0.
    cogs: float = 0.
    fee_income: float = 0.
    fee_expense: float = 0.
    rent_charge: float = 0.
    rent_paid: float = 0.

    @property
    def earnings(self):
        return self.sales-self.cogs+self.fee_income-self.fee_expense-self.rent_charge


@dataclass(frozen=True)
class Book:
    label: str
    quantity: tuple
    basis: tuple
    quote: tuple


@dataclass(frozen=True)
class State:
    cash: float
    held: tuple
    basis: tuple
    finished: tuple
    finished_basis: tuple
    quotes: tuple
    incumbents: tuple
    arrears: float = 0.
    switching_net_ema: float = 0.
    tick_fee_income: float = 0.
    tick_fee_expense: float = 0.
    accounts: Accounts = Accounts()
    book: Book | None = None
    completed_phases: tuple = ()
    rent_settled: bool = False


@dataclass(frozen=True)
class Purchase:
    label: str
    offers: tuple[Offer, ...]
    funded_demands: tuple
    reliability: tuple
    fee_unit_cost: float
    fee_multiple: float
    active_lines: tuple
    rent_bill: float
    rent_threshold: float = 2_000_000.
    # T1 takes its gate snapshot after procurement; combined T2 before it.
    overhead_timing: str = 'before'
    # T2 adapters carry the value frozen at phase entry, before other buyers.
    frozen_overhead: float | None = None


@dataclass(frozen=True)
class OpenBook:
    label: str


@dataclass(frozen=True)
class SettleBook:
    label: str
    demand: tuple
    fee_income: float = 0.


@dataclass(frozen=True)
class SharedSettleBook(SettleBook):
    """Explicit residual-demand scenario, grouped by interchangeable product.

    Demand is each line's whole quantity at its frozen quote. Within each group,
    serve ascending quotes (then line index), subtracting prior group sales.
    This scenario allocator is not the world's buyer search/loyalty mechanism.
    """
    groups: tuple = ()


@dataclass(frozen=True)
class SetQuotes:
    label: str
    quotes: tuple


@dataclass(frozen=True)
class Rent:
    label: str
    bill: float
    threshold: float = 2_000_000.


@dataclass(frozen=True)
class EndTick:
    label: str
    alpha: float


def equity(company, state):
    return (state.cash+company.fixed_assets-state.arrears
            +sum(q*b for q,b in zip(state.held,state.basis))
            +sum(q*b for q,b in zip(state.finished,state.finished_basis)))


def room(company, state):
    return company.storage-sum(q*s for q,s in zip(state.held,company.spaces))-sum(
        q*line.output_space for q,line in zip(state.finished,company.lines))


def _integer(x, minimum=0):
    return isinstance(x,(int,float)) and math.isfinite(x) and x==int(x) and x>=minimum


def validate_state(company, state):
    n=len(company.spaces);nl=len(company.lines)
    if not n or not nl or any(len(x)!=n for x in (company.slots,state.held,state.basis,state.incumbents)) or any(
            len(x)!=nl for x in (company.finished_caps,state.finished,state.finished_basis,state.quotes)):
        raise ValueError('company state dimensions differ')
    if any(not math.isfinite(x) for x in (company.storage,company.fixed_assets,company.margin_band,
            state.cash,state.arrears,state.switching_net_ema,state.tick_fee_income,state.tick_fee_expense,
            *company.spaces,*state.basis,*state.finished_basis,*state.quotes,*vars(state.accounts).values())):
        raise ValueError('nonfinite company state')
    if (company.storage<0 or company.fixed_assets<0 or company.margin_band<=0 or state.cash<0 or state.arrears<0
            or min(company.spaces)<=0 or min(state.quotes)<=0 or min((*state.basis,*state.finished_basis))<0
            or state.tick_fee_income<0 or state.tick_fee_expense<0 or any(x<0 for x in vars(state.accounts).values())):
        raise ValueError('invalid company resources')
    if (any(not math.isfinite(x) or x<0 for x in (*company.slots,*state.held,*state.finished))
            or any(not _integer(x) for x in company.finished_caps)) or any(
            not _integer(x,-1) for x in state.incumbents):
        raise ValueError('invalid inventory quantity or incumbent')
    if room(company,state)<-1e-8:
        raise ValueError('inventory exceeds physical storage')
    # Existing inputs may exceed reallocated slots; purchases cannot increase
    # them until consumption brings them below the current allocation.
    shell=Problem(state.held,state.basis,company.spaces,tuple(max(h,s) for h,s in zip(state.held,company.slots)),
        max(0.,room(company,state)),state.cash,(),state.incumbents,(0,)*n,(0.,)*n,company.lines,
        tuple((0.,)*(math.ceil(max(h,s))+1) for h,s in zip(state.held,company.slots)),company.margin_band)
    _validate_resources(shell)


def _validate_resources(problem):
    # Structural checks still use the independent integer validator. Ceilings
    # are validation-only: all execution retains the original float quantities.
    validate(replace(problem,held=tuple(math.ceil(q) for q in problem.held),
                     slots=tuple(math.ceil(q) for q in problem.slots)))


def _post(state, **amounts):
    return replace(state,accounts=replace(state.accounts,**{name:getattr(state.accounts,name)+value for name,value in amounts.items()}))


def _overhead(company,state,bill,threshold):
    return ((bill if equity(company,state)>=threshold else 0.)-state.switching_net_ema)/len(company.lines)


def _purchase(company,state,event,allocation):
    n=len(state.held);nl=len(company.lines)
    native=any(q!=int(q) for q in (*state.held,*state.finished,*company.slots))
    if event.label in state.completed_phases:
        raise ValueError('company purchasing phase already completed this tick')
    if (event.overhead_timing not in ('before','after') or len(event.offers)!=len(event.funded_demands)
            or len(event.offers)!=len(event.reliability) or len(allocation)!=len(event.offers)
            or len(set(event.active_lines))!=len(event.active_lines)
            or any(not _integer(i) or i>=nl for i in event.active_lines)):
        raise ValueError('invalid purchase event dimensions/timing')
    if any(not math.isfinite(x) or x<0 for x in (event.rent_bill,event.rent_threshold,event.fee_unit_cost,event.fee_multiple)):
        raise ValueError('invalid purchase fee/rent parameters')
    if any(not math.isfinite(x) for x in event.reliability):
        raise ValueError('nonfinite supplier reliability')
    if event.frozen_overhead is not None and (event.overhead_timing != 'before' or isinstance(event.frozen_overhead,bool) or not math.isfinite(event.frozen_overhead)):
        raise ValueError('invalid frozen phase overhead')
    bids=[0]*n;fees=[0.]*n
    for i,o in enumerate(event.offers):
        if not 0<=o.material<n or not _integer(event.funded_demands[i]) or not _integer(o.lot,1) or event.funded_demands[i]%o.lot:
            raise ValueError('invalid material or funded whole-lot quantity')
        if o.supplier==state.incumbents[o.material]:
            bids[o.material]=event.funded_demands[i]
            fees[o.material]=event.fee_multiple*event.fee_unit_cost*(1+min(1.,max(0.,event.reliability[i])))
    p=Problem(state.held,state.basis,company.spaces,tuple(max(h,s) for h,s in zip(state.held,company.slots)),
        max(0.,room(company,state)),state.cash,event.offers,state.incumbents,tuple(bids),tuple(fees),(),
        tuple((0.,)*(math.ceil(max(h,s))+1) for h,s in zip(state.held,company.slots)),company.margin_band,event.funded_demands)
    _validate_resources(p)
    if any(not _integer(q) for q in allocation):
        raise ValueError('allocation must contain nonnegative integers')
    bought=evaluate(p,allocation,terminal_lookup=lambda table,q:0.,native_resources=native)
    if bought is None:
        raise ValueError('infeasible procurement allocation')
    preferences=list(state.incumbents)
    for i in sorted(range(len(event.offers)),key=lambda i:(event.offers[i].material,event.offers[i].price,event.offers[i].supplier)):
        if allocation[i]>0 and event.funded_demands[i]>0 and allocation[i]>=event.funded_demands[i]:
            preferences[event.offers[i].material]=event.offers[i].supplier
    fee=sum(bought['fees'])
    purchased=replace(state,cash=bought['cash'],held=bought['remaining'],basis=bought['basis'],
                      incumbents=tuple(preferences),tick_fee_expense=state.tick_fee_expense+fee,
                      completed_phases=state.completed_phases+(event.label,))
    purchased=_post(purchased,goods_paid=bought['goods'],fee_expense=fee)
    snapshot=state if event.overhead_timing=='before' else purchased
    overhead=(_overhead(company,snapshot,event.rent_bill,event.rent_threshold)
              if event.frozen_overhead is None else event.frozen_overhead)
    lines=[]
    for i,line in enumerate(company.lines):
        limit=max(0,min(line.max_batches,math.floor((company.finished_caps[i]-state.finished[i])/line.output_qty))) if i in event.active_lines else 0
        lines.append(replace(line,max_batches=limit,quote=state.quotes[i],overhead=overhead,
                             output_values=(0.,)*(limit*line.output_qty+1)))
    production=replace(p,held=purchased.held,basis=purchased.basis,cash=purchased.cash,
                       free_space=max(0.,room(company,purchased)),offers=(),bids=(0,)*n,fees=(0.,)*n,
                       funded_demands=None,incumbents=purchased.incumbents,lines=tuple(lines))
    made=evaluate(production,(),terminal_lookup=lambda table,q:0.,native_resources=native)
    if made is None:
        raise ValueError('production would exceed physical storage')
    quantities=[];bases=[]
    for i,line in enumerate(lines):
        output=made['outputs'][i]
        unit_cost=line.conversion+sum(q*b for q,b in zip(line.recipe,purchased.basis))/line.output_qty
        quantity=state.finished[i]+output
        value=state.finished[i]*state.finished_basis[i]+output*unit_cost
        quantities.append(quantity);bases.append(value/quantity if quantity else 0.)
    result=replace(purchased,cash=made['cash'],held=made['remaining'],basis=made['basis'],
                   finished=tuple(quantities),finished_basis=tuple(bases))
    result=_post(result,conversion_paid=made['conversion'])
    return result,dict(goods=bought['goods'],fees=bought['fees'],preferences=tuple(preferences),
                       outputs=made['outputs'],conversion=made['conversion'],gateOverhead=overhead,
                       gateEquity=equity(company,snapshot),cashAfterProcurement=purchased.cash,
                       feeRecipients=tuple(state.incumbents[i] if q else -1 for i,q in enumerate(bought['fees'])))


def apply(company,state,event,allocation=None):
    """Pure transition; returns new state plus diagnostics, never mutates input."""
    validate_state(company,state)
    if not isinstance(event.label,str) or not event.label:
        raise ValueError('event requires a label')
    if state.rent_settled and isinstance(event,(Purchase,OpenBook,SettleBook,SetQuotes)):
        raise ValueError('trading after rent requires a new tick')
    if isinstance(event,Purchase):
        if allocation is None:
            raise ValueError('purchase allocation required')
        result,detail=_purchase(company,state,event,allocation)
    elif isinstance(event,OpenBook):
        if state.book is not None:
            raise ValueError('sales books cannot overlap')
        result=replace(state,book=Book(event.label,state.finished,state.finished_basis,state.quotes))
        detail=dict(openingStock=state.finished,openingBasis=state.finished_basis,openingQuote=state.quotes)
    elif isinstance(event,SettleBook):
        book=state.book
        if book is None or book.label!=event.label or len(event.demand)!=len(state.finished):
            raise ValueError('missing/mismatched sales book')
        if any(not _integer(q) for q in event.demand) or not math.isfinite(event.fee_income) or event.fee_income<0:
            raise ValueError('invalid sale demand or fee income')
        if isinstance(event,SharedSettleBook):
            flat=tuple(i for group in event.groups for i in group)
            if (not event.groups or any(not group for group in event.groups)
                    or any(not _integer(i) for i in flat)
                    or sorted(flat)!=list(range(len(book.quantity)))):
                raise ValueError('shared sales groups must partition installed lines')
            delivered=[0]*len(book.quantity)
            for group in event.groups:
                order=sorted(group,key=lambda i:(book.quote[i],i))
                for left,right in zip(order,order[1:]):
                    if (event.demand[left]<event.demand[right] or
                            (book.quote[left]==book.quote[right] and event.demand[left]!=event.demand[right])):
                        raise ValueError('shared demand must be consistent with frozen quotes')
                cumulative=0
                for i in order:
                    delivered[i]=min(math.floor(book.quantity[i]),max(0,event.demand[i]-cumulative))
                    cumulative+=delivered[i]
            sold=tuple(delivered)
        else:
            sold=tuple(min(want,math.floor(available)) for want,available in zip(event.demand,book.quantity))
        quantities=[];bases=[]
        for i,q in enumerate(sold):
            if q>state.finished[i]:
                raise ValueError('book stock was consumed outside settlement')
            remaining=state.finished[i]-q
            # Match InputMarket settlement: only sold lines update basis,
            # with pre-settlement units reconstructed after the stock delta.
            value=(remaining+q)*state.finished_basis[i]-q*book.basis[i]
            if value < -1e-8:
                raise ValueError('book sale exceeds inventory book value')
            quantities.append(remaining);bases.append(state.finished_basis[i] if q==0 else (max(0.,value)/remaining if remaining else 0.))
        sales=sum(q*p for q,p in zip(sold,book.quote));cogs=sum(q*b for q,b in zip(sold,book.basis))
        result=replace(state,cash=state.cash+sales+event.fee_income,finished=tuple(quantities),finished_basis=tuple(bases),
                       tick_fee_income=state.tick_fee_income+event.fee_income,book=None)
        result=_post(result,sales=sales,cogs=cogs,fee_income=event.fee_income)
        detail=dict(sold=sold,sales=sales,cogs=cogs,feeIncome=event.fee_income)
        if isinstance(event,SharedSettleBook):
            detail.update(sharedGroups=event.groups,quoteDemands=event.demand,
                          groupSales=tuple(sum(sold[i] for i in group) for group in event.groups))
    elif isinstance(event,SetQuotes):
        if len(event.quotes)!=len(state.quotes) or any(not math.isfinite(p) or p<=0 for p in event.quotes):
            raise ValueError('invalid new quotes')
        result=replace(state,quotes=event.quotes);detail=dict(quotes=event.quotes)
    elif isinstance(event,Rent):
        if state.rent_settled or state.book is not None:
            raise ValueError('duplicate rent or unsettled sales book at billing')
        if any(not math.isfinite(x) or x<0 for x in (event.bill,event.threshold)):
            raise ValueError('invalid rent terms')
        before=equity(company,state);eligible=before>=event.threshold
        charge=event.bill if eligible else 0.
        paid=min(state.cash,state.arrears+charge) if eligible else 0.
        result=replace(state,cash=state.cash-paid,arrears=state.arrears+charge-paid,rent_settled=True)
        result=_post(result,rent_charge=charge,rent_paid=paid)
        detail=dict(eligible=eligible,equityBeforeBilling=before,charge=charge,paid=paid,arrears=result.arrears)
    elif isinstance(event,EndTick):
        if state.book is not None:
            raise ValueError('unsettled phase book at tick end')
        if not math.isfinite(event.alpha) or not 0<=event.alpha<=1:
            raise ValueError('invalid transfer EMA alpha')
        net=state.tick_fee_income-state.tick_fee_expense
        result=replace(state,switching_net_ema=state.switching_net_ema+event.alpha*(net-state.switching_net_ema),
                       tick_fee_income=0.,tick_fee_expense=0.,completed_phases=(),rent_settled=False)
        detail=dict(netTransfers=net,nextTransferEMA=result.switching_net_ema)
    else:
        raise ValueError('unsupported phase event')
    validate_state(company,result)
    # Independent accounting check: posted earnings, never an equity-derived P&L.
    earnings=result.accounts.earnings-state.accounts.earnings
    residual=equity(company,result)-equity(company,state)-earnings
    tolerance=1e-6+1e-12*max(abs(equity(company,state)),abs(equity(company,result)))
    if abs(residual)>tolerance:
        raise AssertionError('phase event equity does not reconcile to posted earnings')
    a,b=state.accounts,result.accounts
    cash_expected=state.cash+(b.sales-a.sales)+(b.fee_income-a.fee_income)-(b.goods_paid-a.goods_paid)-(b.conversion_paid-a.conversion_paid)-(b.fee_expense-a.fee_expense)-(b.rent_paid-a.rent_paid)
    if abs(result.cash-cash_expected)>tolerance:
        raise AssertionError('phase event cash does not reconcile')
    detail.update(event=type(event).__name__,label=event.label,cash=result.cash,
                  equity=equity(company,result),postedEarnings=earnings,equityResidual=residual)
    return result,detail


def replay(company,initial,events,allocations):
    state=initial;trace=[];used=set()
    for index,event in enumerate(events):
        allocation=allocations.get(index)
        if isinstance(event,Purchase):used.add(index)
        elif allocation is not None:raise ValueError('allocation supplied for a non-purchase event')
        state,detail=apply(company,state,event,allocation)
        trace.append(detail)
    if set(allocations)!=used:
        raise ValueError('missing or extra purchase allocation indices')
    if state.book is not None:
        raise ValueError('unsettled sales book at horizon boundary')
    return state,trace


def horizon_value(initial,final,input_values,finished_values):
    """Incremental cash return net of newly accrued liabilities, plus explicitly
    supplied terminal values. Paying old arrears affects liquidity, not expense.
    """
    if final.book is not None or len(input_values)!=len(final.held) or len(finished_values)!=len(final.finished):
        raise ValueError('invalid horizon boundary')
    terminal=0.
    for q,table in zip((*final.held,*final.finished),(*input_values,*finished_values)):
        terminal+=value_at(table,q)
    return final.cash-initial.cash-(final.arrears-initial.arrears)+terminal
