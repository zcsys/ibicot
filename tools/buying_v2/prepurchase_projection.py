"""Native-resource bridge from raw captures to the experimental phase ledger.

No sales forecast or terminal value is invented. Unsupported records fail
explicitly; never round held goods or credit deferred receipts at buyer entry.
"""
from dataclasses import dataclass
import math
from economy.core import model as M
from .industry_oracle import Line, Offer
from .phase_ledger import Company, State, Book, Purchase, SettleBook, validate_state


class ProjectionUnsupported(ValueError):
    pass


def whole(value, label):
    if isinstance(value,bool) or not math.isfinite(value) or value<0 or value!=int(value):
        raise ProjectionUnsupported(f'{label} is not a nonnegative whole quantity')
    return int(value)



def quantity(value,label):
    if isinstance(value,bool) or not math.isfinite(value) or value<0:
        raise ProjectionUnsupported(f'{label} is not a finite nonnegative quantity')
    return int(value) if value==int(value) else value


def keyed(mapping,key):
    return mapping[key] if key in mapping else mapping[str(key)]


@dataclass(frozen=True)
class Projection:
    company: Company
    state: State
    purchase: Purchase
    committed_sales: tuple
    remaining_book_stock: tuple
    pending_fee_income: float
    material_ids: tuple
    line_ids: tuple

    def settlement(self, additional_sales, additional_fee_income=0.):
        """Explicit future deliveries, not a demand forecast or optimization.

        Already committed sales are always included once. Further sales can only
        use remaining opening-book stock, never this phase's new production.
        """
        if len(additional_sales)!=len(self.line_ids):raise ValueError('sales dimensions differ')
        additional=tuple(whole(q,'additional sales') for q in additional_sales)
        if any(q>s for q,s in zip(additional,self.remaining_book_stock)):
            raise ValueError('future sales exceed remaining phase book')
        if not math.isfinite(additional_fee_income) or additional_fee_income<0:
            raise ValueError('invalid additional fee income')
        return SettleBook(self.state.book.label,
                          tuple(a+b for a,b in zip(self.committed_sales,additional)),
                          self.pending_fee_income+additional_fee_income)


def project(record):
    if record.get('schema')!=1 or record.get('boundary')!='before-company-phase-purchases':
        raise ValueError('unsupported capture schema/boundary')
    cfg=record['config'];phase=record['phase'];tick=record['tick']
    materials=record['materials'];rows=record['lines']
    mids=tuple(x['material'] for x in materials);lids=tuple(x['line'] for x in rows)
    if mids!=tuple(range(M.NI)) or lids!=tuple(record['installedLines']) or len(set(lids))!=len(lids):
        raise ValueError('capture identity/order mismatch')
    if not rows:raise ValueError('capture has no installed lines')
    if any(x['space']!=M.T2_INPUT_PRODUCTS[m]['complexity'] for m,x in enumerate(materials)):
        raise ValueError('capture material catalog mismatch')
    for row in rows:
        product=M.T2_PRODUCTS[row['product']]
        if (row['complexity']!=product['complexity'] or row['outputQty']!=product['outputQty']
                or tuple(map(tuple,row['ingredients']))!=tuple(map(tuple,product['ingredients']))):
            raise ValueError('capture recipe catalog mismatch')
    if tuple(record['activeLines'])!=tuple(x['line'] for x in rows if x['complexity']==phase):
        raise ValueError('capture phase membership mismatch')
    index={line:i for i,line in enumerate(lids)}
    active=tuple(index[i] for i in record['productionOrder'])
    if tuple(record['activeLines'])!=tuple(record['productionOrder']):raise ValueError('active order mismatch')
    lines=[];caps=[]
    for row in rows:
        recipe=[0]*len(materials)
        for m,q in row['ingredients']:recipe[m]+=whole(q,'recipe')
        output=whole(row['outputQty'],'output yield')
        if output==0:raise ValueError('zero output yield')
        capacity=whole(keyed(cfg['t2Capacity'],row['complexity']),'capacity')//output
        lines.append(Line(tuple(recipe),capacity,M.conversion_cost(row['complexity'],cfg),
            row['quote'],record['phaseEntryOverheadPerLine'],(0.,)*(capacity*output+1),row['complexity'],output))
        caps.append(math.floor(record['outputSlotSpace']/row['complexity']))
    company=Company(tuple(x['space'] for x in materials),tuple(quantity(x['slot'],'input slot') for x in materials),
        record['goodsSpace'],tuple(lines),tuple(caps),record['equipmentBook']+cfg['t2License'],cfg['productionMarginBand'])
    opening=tuple(quantity(x['sellerBook']['opening']['fin'],'opening stock') for x in rows)
    remaining=tuple(quantity(x['sellerBook']['current']['fin'],'remaining stock') for x in rows)
    committed=tuple(whole(a-b,'committed stock movement') for a,b in zip(opening,remaining))
    if any(q<0 for q in committed):raise ValueError('phase book stock increased')
    book=Book(f'tick-{tick}-C{phase}-sales',opening,
              tuple(x['sellerBook']['opening']['basis'] for x in rows),
              tuple(x['sellerBook']['opening']['price'] for x in rows))
    pending=record['pendingSwitchingIncome']
    revenue=sum(q*p for q,p in zip(committed,book.quote))
    if pending<0 or not math.isclose(record['pendingSellerCash'],revenue+pending,rel_tol=1e-12,abs_tol=1e-8):
        raise ValueError('pending receipts do not reconcile to committed sales/fees')
    state=State(record['cash'],tuple(quantity(x['held'],'held input') for x in materials),
        tuple(x['basis'] for x in materials),tuple(quantity(x['finished'],'finished stock') for x in rows),
        tuple(x['basis'] for x in rows),tuple(x['quote'] for x in rows),tuple(x['incumbent'] for x in materials),
        arrears=record['rentArrears'],switching_net_ema=record['switchingNetEMA'],
        tick_fee_income=record['switchingIncome'],tick_fee_expense=record['switchingExpense'],book=book,
        completed_phases=tuple(f'tick-{tick}-C{cx}-purchase' for cx in sorted({x['complexity'] for x in rows if x['complexity']<phase})))
    validate_state(company,state)
    offers=[];reliability=[]
    for material in record['offers']:
        for supplier in material['suppliers']:
            current=supplier['current']
            offers.append(Offer(material['material'],supplier['supplier'],current['price'],math.floor(quantity(current['fin'],'offer stock'))))
            reliability.append(current['rel'])
    native=rows[0]['complexity']-3
    event=Purchase(f'tick-{tick}-C{phase}-purchase',tuple(offers),(),tuple(reliability),
        M.material_switching_reference(cfg),record['loyaltyMultiples'][native],active,
        cfg['storage']*cfg['storageRentPerUnitYear']/M.TIME['ticksPerYear'],
        frozen_overhead=record['phaseEntryOverheadPerLine'])
    return Projection(company,state,event,committed,remaining,pending,mids,lids)
