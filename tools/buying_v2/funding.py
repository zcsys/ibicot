"""Coupled hypothetical funding for an explicitly supplied industrial value model.

This does not adopt a valuation model or post requests. It removes supplier stock
limits while retaining company cash, lots, storage and actual production gates.
Each alternate quote is evaluated in a separate hypothetical joint basket.
"""
from dataclasses import replace
import math
from .industry_oracle import Offer, validate
from .industry_search import solve


def funded_intentions(problem, max_nodes=100000):
    validate(problem)
    count = len(problem.held)
    references = []
    for m in range(count):
        offers = [o for o in problem.offers if o.material == m]
        incumbent = next((o for o in offers if o.supplier == problem.incumbents[m]), None)
        references.append(incumbent if incumbent is not None else min(offers, key=lambda o:(o.price,o.supplier), default=None))

    def hypothetical(replaced_material=-1, replacement=None):
        offers = []
        for m, reference in enumerate(references):
            quote = replacement if m == replaced_material else reference
            if quote is not None:
                offers.append(Offer(m, quote.supplier, quote.price,
                                    problem.slots[m]-problem.held[m], quote.lot))
        # Loyalty fees are not charged for this incumbent-reference funding
        # question. Actual selection must reserve its separately payable fees.
        counterfactual = replace(problem, offers=tuple(offers), fees=(0.,)*count, bids=(0,)*count, funded_demands=None)
        result, certificate = solve(counterfactual, max_nodes=max_nodes)
        quantities = [0]*count
        for o, q in zip(offers,result[0]):
            quantities[o.material] += int(q)
        return quantities, float(result[4]), certificate

    original, spend, certificate = hypothetical()
    bids = [original[m] if references[m] is not None and references[m].supplier == problem.incumbents[m] else 0 for m in range(count)]
    demands = []
    cache = {}
    for offer in problem.offers:
        key = (offer.material, offer.price, offer.lot)
        if key not in cache:
            cache[key] = hypothetical(offer.material,offer)[0][offer.material]
        demands.append(cache[key])
    return dict(bids=tuple(bids), funded_demands=tuple(demands), reference_quantities=tuple(original),
                reference_goods=spend, reference_quotes=tuple(o.price if o is not None else None for o in references),
                reference_certificate=certificate,
                semantics='Stock-unconstrained joint funding at declared reference quotes; candidate value tables remain explicit assumptions.')


def plan(problem, max_nodes=100000):
    """Fund, freeze bids, and solve jointly with every fallback constraint inside
    the action space. A violating basket is never repaired after selection.
    """
    intentions = funded_intentions(problem, max_nodes)
    funded = replace(problem, bids=intentions['bids'], funded_demands=intentions['funded_demands'])
    result, certificate = solve(funded, max_nodes)
    return funded, result, dict(funding=intentions, selection=certificate)


def replenishment_plan(problem, max_nodes=100000):
    """D3 comparison policy: existing deficits, most units, then least payment.

    Reference funding uses the same joint quantity objective without supplier
    stock limits or switching fees. Actual fee-aware choice keeps those funded
    quote limits inside its feasible action space.
    """
    from .replenishment import solve as refill
    n=len(problem.held)
    targets=tuple(s-h for s,h in zip(problem.slots,problem.held))
    lots={o.lot for o in problem.offers}
    if len(lots)>1:
        raise ValueError('within-tier replenishment requires a uniform lot')
    lot=next(iter(lots),1)
    references=[]
    for m in range(n):
        offers=[o for o in problem.offers if o.material==m]
        references.append(next((o for o in offers if o.supplier==problem.incumbents[m]),
                               min(offers,key=lambda o:(o.price,o.supplier),default=None)))
    def hypothetical(material=-1,replacement=None):
        refs=[replacement if m==material else o for m,o in enumerate(references)]
        offers=tuple(Offer(m,o.supplier,o.price,targets[m],lot) for m,o in enumerate(refs) if o is not None)
        result=refill(targets,offers,(-1,)*n,(0,)*n,(0.,)*n,problem.cash,problem.spaces,problem.free_space,lot,max_nodes)
        q=[0]*n
        for o,x in zip(offers,result[0]):
            q[o.material]+=int(x)
        return q
    quantities=hypothetical()
    bids=tuple(quantities[m] if o is not None and o.supplier==problem.incumbents[m] else 0 for m,o in enumerate(references))
    demands=[];cache={}
    for o in problem.offers:
        key=(o.material,o.price)
        if key not in cache:
            cache[key]=hypothetical(o.material,o)[o.material]
        demands.append(cache[key])
    funded=replace(problem,bids=bids,funded_demands=tuple(demands))
    result=refill(targets,problem.offers,problem.incumbents,bids,problem.fees,problem.cash,
                  problem.spaces,problem.free_space,lot,max_nodes,funded_demands=demands)
    return funded,result
