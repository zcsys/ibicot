"""Industrial decision evidence. Candidate checks are never incoming orders.

This reducer cannot affect decisions, reliability, pricing, or accounting. Each
row aggregates one buyer tier/input market; order identity is tick/phase/buyer/input.
"""
import numpy as np
from economy.core import model as M
from .jit import njit

VERSION=1
FIELDS=(
    'decisions','offersObserved','fundedOfferChecks','sufficientStockChecks','belowLotStockChecks',
    'storageTargetQuantity','referenceFundedQuantity','purchasedQuantity','positiveLegs',
    'quotedRemainingQuantity','stockLimitedLegs','otherLimitedLegs','feesPaid','feeAmount',
    'firstAssignments','preferenceChanges','noOfferDecisions','noFundedOfferDecisions',
    'noPurchaseDecisions','referenceShortfall','incumbentAvailabilityChecks','incumbentAvailableChecks',
    'goodsSpend','feeWaivedUnavailableOrders',
)


def empty_totals():
    return np.zeros((M.NE+M.NI,len(FIELDS)),dtype=np.float64)


@njit
def record(totals,offset,materials,targets,lot,om,suppliers,prices,stocks,demands,incumbents,bids,allocation,requests,preferences,charges):
    for j in range(len(materials)):
        row=offset+materials[j]
        observed=checks=sufficient=empty=bought=legs=stock_limited=other_limited=0
        quoted=goods=0.
        reference=-1;inc=-1;outside=False
        for i in range(len(om)):
            if om[i]!=j:
                continue
            observed+=1
            if reference<0 or prices[i]<prices[reference] or (prices[i]==prices[reference] and suppliers[i]<suppliers[reference]):
                reference=i
            if suppliers[i]==incumbents[j]:
                inc=i
            if demands[i]>0:
                checks+=1
                sufficient+=int(stocks[i]//lot*lot>=demands[i])
                empty+=int(stocks[i]<lot)
            q=allocation[i]
            bought+=q;goods+=q*prices[i]
            if q:
                outside|=suppliers[i]!=incumbents[j]
                legs+=1;quoted+=requests[i]
                stock_limited+=int(q<requests[i] and stocks[i]//lot*lot<requests[i])
                other_limited+=int(q<min(requests[i],stocks[i]//lot*lot))
        if inc>=0:
            reference=inc
        intended=demands[reference] if reference>=0 else 0
        inc_checked=inc>=0 and bids[j]>0
        inc_available=inc_checked and stocks[inc]//lot*lot>=bids[j]
        totals[row,0]+=1;totals[row,1]+=observed;totals[row,2]+=checks
        totals[row,3]+=sufficient;totals[row,4]+=empty
        totals[row,5]+=targets[j]//lot*lot;totals[row,6]+=intended
        totals[row,7]+=bought;totals[row,8]+=legs;totals[row,9]+=quoted
        totals[row,10]+=stock_limited;totals[row,11]+=other_limited
        totals[row,12]+=int(charges[j]>0);totals[row,13]+=charges[j]
        totals[row,14]+=int(incumbents[j]<0 and preferences[j]>=0)
        totals[row,15]+=int(incumbents[j]>=0 and preferences[j]>=0 and incumbents[j]!=preferences[j])
        totals[row,16]+=int(observed==0);totals[row,17]+=int(checks==0)
        totals[row,18]+=int(bought==0);totals[row,19]+=max(0,intended-bought)
        totals[row,20]+=int(inc_checked);totals[row,21]+=int(inc_available)
        totals[row,22]+=goods
        totals[row,23]+=int(outside and inc_checked and not inc_available)


def record_problem(totals,offset,materials,p,allocation,requests,preferences,charges,demands=None,lot=None):
    """Reference adapter: read-only inputs, no inference from ending stock."""
    if totals is None:
        return
    if lot is None:
        lot=p.offers[0].lot if p.offers else 1
    record(totals,offset,np.asarray(materials,dtype=np.int64),np.array(p.slots)-p.held,lot,
           np.array([o.material for o in p.offers],dtype=np.int64),np.array([o.supplier for o in p.offers],dtype=np.int64),
           np.array([o.price for o in p.offers]),np.array([o.stock for o in p.offers],dtype=np.int64),
           np.asarray(p.funded_demands if demands is None else demands,dtype=np.int64),np.array(p.incumbents),np.array(p.bids),
           np.asarray(allocation,dtype=np.int64),np.array(requests),np.array(preferences),np.array(charges))


def schema():
    return dict(version=VERSION,fields=list(FIELDS),orderIdentity=['tick','phase','buyer','input'],
        markets=[dict(row=i,buyerTier='t1',product=e,complexity=0) for i,e in enumerate(M.ELEMENTS)]
            +[dict(row=M.NE+i,buyerTier='t2',product=p['catalogId'],complexity=p['complexity']) for i,p in enumerate(M.T2_INPUT_PRODUCTS)],
        notes=dict(
            decisions='One evaluated input per company/phase, including zero targets and missing offers.',
            fundedOfferChecks='Hypothetical stock-unconstrained joint quantity at each discovered quote is positive. These are not incoming orders.',
            sufficientStockChecks='Opening live whole-lot stock can cover that quote-funded quantity. Denominator: fundedOfferChecks.',
            belowLotStockChecks='Positive funded quote, but opening stock contains less than one purchase lot.',
            referenceFundedQuantity='Coupled goods-only quantity at incumbent quote, else cheapest discovered quote; ignores supplier stock and switching fees.',
            quotedRemainingQuantity='Sum of quote-funded remainders on positive delivery legs, matching legacy demand counters. May exceed affordable placed units and unique intention; not unique market demand.',
            purchasedQuantity='Actually placed and atomically delivered units; these coincide in this stock-aware basket protocol.',
            referenceShortfall='Positive part of reference-funded quantity minus bought per decision. May reflect prices, fees, stock or shared resources; not attributed stock loss.',
            stockLimitedLegs='Positive leg delivers less than its quote remainder and opening whole-lot stock is insufficient for that remainder; not a causal loss estimate.',
            otherLimitedLegs='Positive leg delivers less than both stock and quote remainder; cause not classified.',
            reliability='Diagnostic candidate checks do not modify existing reliability. Legacy positive-leg checks remain separately posted.',
            noHistory='A ratio with zero denominator is unavailable (null), never zero.',
            quantities='Items, not storage spaces. T1 quantities respect configured wholesale lots.',
            fees='Actual posted fees; fee incidence and incumbent changes are independent.'))
