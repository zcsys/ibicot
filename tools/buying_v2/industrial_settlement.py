"""Atomic reference settlement for a solved T2 company input basket.

All validation completes before mutation. This is the reference transaction
contract; population execution still needs a compiled adapter and buyer model.
"""
import math
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from .industry_oracle import validate


def settle_t2(world, cfg, firm, phase, book, problem, allocation, materials, funded_demands, observations=None,exposure=None,trace=None):
    validate(problem)
    if phase not in M.TIER_BOUNDARIES['T2'] or not 0 <= firm < cfg['t2FirmCount']:
        raise ValueError('invalid buyer phase or identity')
    lines = world.t2FirmLines[firm*M.T2_MAX_PRODUCTS_PER_FIRM:firm*M.T2_MAX_PRODUCTS_PER_FIRM+int(world.t2FirmLineCount[firm])]
    phase_inputs = {m for line in lines if M.T2_PRODUCTS[int(world.t2LineProduct[line])]['complexity'] == phase
                    for m,q in M.T2_PRODUCTS[int(world.t2LineProduct[line])]['ingredients']}
    if any(m not in phase_inputs for m in materials):
        raise ValueError('input is not used in this production phase')
    native_class = M.T2_PRODUCTS[int(world.t2LineProduct[lines[0]])]['complexity']-3
    if len(materials) != len(problem.held) or len(set(materials)) != len(materials):
        raise ValueError('material mapping mismatch')
    if len(allocation) != len(problem.offers) or len(funded_demands) != len(allocation):
        raise ValueError('offer quantities mismatch')
    if float(world.t2Cash[firm]) != problem.cash:
        raise ValueError('buyer cash changed; replan')
    slots, _, allowed = K.tier2_storage_layout(world, cfg, firm)
    if any(m not in allowed for m in materials):
        raise ValueError('input not supported by company installations')
    arrays = []
    for j, m in enumerate(materials):
        if problem.spaces[j] != M.T2_INPUT_PRODUCTS[m]['complexity']:
            raise ValueError('input storage unit mismatch')
        raw, basis, width = (world.t2Raw, world.t2RawBasis, M.NE) if m < M.NE else (world.t2T1Raw, world.t2T1Basis, M.NI)
        index = firm * width + m
        if raw[index] != problem.held[j] or basis[index] != problem.basis[j]:
            raise ValueError('buyer inventory changed; replan')
        if int(world.t2Preferred[firm*M.NI+m]) != problem.incumbents[j]:
            raise ValueError('buyer preference changed; replan')
        arrays.append((raw, basis, index))
    bought = [0]*len(materials)
    goods = [0.]*len(materials)
    inventory_value = [h*b for h,b in zip(problem.held,problem.basis)]
    outside = [False]*len(materials)
    for i, (offer, q) in enumerate(zip(problem.offers, allocation)):
        if q < 0 or q != int(q) or q % offer.lot or q > offer.stock:
            raise ValueError('invalid allocated quantity')
        if funded_demands[i] < 0 or funded_demands[i] != int(funded_demands[i]):
            raise ValueError('invalid funded demand')
        seller = offer.supplier
        if seller not in book.offers[materials[offer.material]]:
            raise ValueError('supplier is not in this input market')
        if book.price[seller] != offer.price or math.floor(book.fin[seller]) != offer.stock:
            raise ValueError('supplier quote/stock changed; replan')
        bought[offer.material] += q
        goods[offer.material] += q*offer.price
        inventory_value[offer.material] += q*offer.price
        outside[offer.material] |= q > 0 and seller != problem.incumbents[offer.material]
    fees = [0.]*len(materials)
    for j, m in enumerate(materials):
        if bought[j] and problem.held[j]+bought[j] > min(problem.slots[j], math.floor(slots[m])):
            raise ValueError('input slot overflow')
        incumbent = problem.incumbents[j]
        inc = next((o for o in problem.offers if o.material == j and o.supplier == incumbent), None)
        valid_incumbent = incumbent in book.offers[m] and math.isfinite(book.price[incumbent])
        if valid_incumbent and inc is None:
            raise ValueError('valid incumbent availability must be included')
        if inc is not None:
            inc_index = next(i for i,o in enumerate(problem.offers) if o is inc)
            if funded_demands[inc_index] != problem.bids[j]:
                raise ValueError('incumbent bid differs from its funded quote demand')
        if outside[j] and inc is not None and problem.bids[j] > 0 and inc.stock >= problem.bids[j]:
            expected_fee = M.loyalty_charge(M.material_switching_reference(cfg), book.rel[incumbent], world.lm2[native_class])
            if abs(problem.fees[j]-expected_fee) > 1e-12*max(1.,abs(expected_fee)):
                raise ValueError('fee differs from the existing loyalty formula')
            fees[j] = expected_fee
    space = sum(q*problem.spaces[j] for j,q in enumerate(bought))
    live_room = K.tier2_goods_space(world,cfg,firm)-K.tier2_inventory_units(world,firm)
    if space > max(0., min(problem.free_space, live_room)):
        raise ValueError('total storage overflow')
    total = sum(goods)+sum(fees)
    if total > world.t2Cash[firm]:
        raise ValueError('cash exhausted')
    # Validate price-sensitive request legs before the first account is touched.
    order = sorted(range(len(allocation)), key=lambda i: (problem.offers[i].material, problem.offers[i].price, problem.offers[i].supplier))
    cumulative = [0]*len(materials)
    requests = [0]*len(allocation)
    preferences = list(problem.incumbents)
    for i in order:
        offer, q = problem.offers[i], allocation[i]
        if not q:
            continue
        j = offer.material
        requests[i] = max(0, funded_demands[i]-cumulative[j])
        if q > requests[i]:
            raise ValueError('allocation exceeds price-sensitive remaining request')
        cumulative[j] += q
        if funded_demands[i] > 0 and q >= funded_demands[i]:
            preferences[j] = offer.supplier
    if trace is not None:
        from .decision_traces import capture_problem
        capture_problem(trace,firm,problem,materials,allocation,requests,preferences,fees,1)
    # Commit all goods and fee entries. Product-order counts are separate from
    # the existing AOV successful-transaction count, which counts positive legs.
    for i in order:
        offer, q = problem.offers[i], allocation[i]
        if not q:
            continue
        j, seller = offer.material, offer.supplier
        m = materials[j]
        payment = q*offer.price
        book.demand[seller] += requests[i]
        book.attempts[seller] += 1
        book.checks[seller] += 1
        book.available[seller] += int(book.fin[seller] >= requests[i])
        book.opportunities[m] += 1
        book.fin[seller] -= q
        book.cash[book.owner[seller]] += payment
        book.sold[seller] += q
        book.revenue[seller] += payment
        book.cogs[seller] += q*book.basis[seller]
        book.intermediate_sold[m] += q
        book.intermediate_revenue[m] += payment
        world.t2MatSpend[native_class] += payment
        world.t2MatOrders[native_class] += 1
    for j, m in enumerate(materials):
        raw, basis, index = arrays[j]
        if bought[j]:
            basis[index] = inventory_value[j]/(problem.held[j]+bought[j])
            raw[index] += bought[j]
            world.t2Preferred[firm*M.NI+m] = preferences[j]
        if fees[j]:
            incumbent = problem.incumbents[j]
            owner = book.owner[incumbent]
            book.cash[owner] += fees[j]
            book.switch_income[owner] += fees[j]
            world.t2SwitchingExpense[firm] += fees[j]
            world.loyaltySwitches[1] += 1
            world.loyaltyPenalties[1] += fees[j]
    world.t2Cash[firm] -= total
    world.t2Bought[firm] += sum(bought)
    if exposure is not None:
        from .seller_exposure import record_exposure
        record_exposure(exposure,np.asarray([o.supplier for o in problem.offers],dtype=np.int64),
                        np.asarray([o.stock for o in problem.offers]),np.asarray(funded_demands),1)
    if observations is not None:
        from .industrial_observations import record_problem
        record_problem(observations,M.NE,materials,problem,allocation,requests,preferences,fees,funded_demands)
    return dict(goods=sum(goods), fees=sum(fees), quantities=bought, preferences=preferences,
                productOrders=sum(q>0 for q in bought), positiveLegs=sum(q>0 for q in allocation))
