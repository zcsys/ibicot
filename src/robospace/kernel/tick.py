"""The 9-phase economy tick, aligned to ``spec/design_canon.md`` §12.4.

``tick()`` mutates a :class:`~robospace.core.state.WorldState` in place and
returns the ephemeral tick result (orders, payments, sinks).
"""
from __future__ import annotations

import math

import numpy as np

from ..core import model as M
from ..core.rng import random_, normal_
from ..core.state import (T0P, WorldState, _has_tier2_product, add_tier2_line)

NE = M.NE
NP = M.NP
N0 = M.N0
N1 = M.N1
MONTH = M.MONTH
MIN_UNIT_PRICE = M.MIN_UNIT_PRICE
MAX_UNIT_PRICE = M.MAX_UNIT_PRICE
M4 = M.T2_MAX_PRODUCTS_PER_FIRM


def tier1_stock_target(W, cfg, product, index):
    # canon: desired inventory = fill G, split 1:1 → finished target = G/2
    return M.inventory_target(M.complexity(product), cfg)


# --------------------------------------------------------------------------
# 1. Reset per-tick scratch
# --------------------------------------------------------------------------
_RESET_NAMES = [
    't0Opportunities', 't1Opportunities', 't2Opportunities', 't2PotentialOrders',
    't1Bought', 't2Bought', 't0Sold', 't0Revenue', 't0COGS', 't0Demand',
    't1Demand', 't2Demand', 't1Sold', 't1Rev', 't1COGS', 't1IntermediateSold',
    't1IntermediateRevenue', 'active', 'potential', 'fulfilled', 'priceLost',
    'stockUnmet', 't0Ful', 't0FundedReq', 't1InputNeed', 't1PurchaseReq',
]


def reset_tick(W: WorldState) -> None:
    for name in _RESET_NAMES:
        getattr(W, name).fill(0)
    W.t2Sold.fill(0)
    W.t2Revenue.fill(0)
    W.t2COGS.fill(0)
    W.t2Made.fill(0)


# --------------------------------------------------------------------------
# 2. Environment (difficulty)
# --------------------------------------------------------------------------
def update_environment(W, cfg, tick):
    for e in range(NE):
        W.difficulty[e] = M.clamp(
            W.difficulty[e] + cfg['theta'] * (cfg['dbar'] - W.difficulty[e])
            + cfg['sigma'] * normal_(cfg['seed'], tick, e * 4),
            cfg['dmin'], cfg['dmax'])


# --------------------------------------------------------------------------
# 3. Tier 0 extraction
# --------------------------------------------------------------------------
def produce_tier0(W, cfg, profiles, tick):
    seed = cfg['seed']
    for supplier in range(N0):
        elements = profiles[supplier]['element_indices']  # sorted ascending
        n_el = len(elements)
        target_per_element = cfg['targetInventory'] / n_el
        bootstrap = max(cfg['minWholesaleLot'], math.ceil(cfg['capacity'] * 0.1 / n_el))
        targets = [
            M.finished_stock_target(W.t0DemandEMA[supplier * NE + e],
                                    cfg['inventoryCoverageTicks'], bootstrap,
                                    cfg['capacity'], target_per_element,
                                    cfg['maxInventory'] / n_el)
            for e in elements
        ]
        deficits = [max(0.0, targets[n] - W.t0Inv[supplier * NE + elements[n]]) for n in range(n_el)]
        capacity = max(0.0, cfg['capacity'])
        total_inventory = sum(max(0.0, W.t0Inv[supplier * NE + e]) for e in elements)
        costs = []
        for e in elements:
            index = supplier * NE + e
            cost = max(1e-9, cfg['baseCost'] * W.difficulty[e])
            W.t0Cost[index] = cost
            if not math.isfinite(W.t0Price[index]) or W.t0Price[index] <= 0:
                W.t0Price[index] = cost * (1 + cfg['markup'])
            costs.append(cost)
        positive = [n for n in range(n_el) if deficits[n] > 0]
        if not positive:
            continue
        start = (seed + tick + supplier) % len(positive)
        priority = positive[start:] + positive[:start]
        rank = {n: pos for pos, n in enumerate(priority)}

        def make(n, planned):
            nonlocal capacity, total_inventory
            index = supplier * NE + elements[n]
            cost = costs[n]
            headroom = max(0.0, cfg['maxInventory'] - total_inventory)
            affordable = math.floor(max(0.0, W.t0Cash[supplier]) / cost)
            made = max(0.0, min(planned, deficits[n], capacity, headroom, affordable))
            old = W.t0Inv[index]
            if made > 0:
                W.t0InvBasis[index] = (old * W.t0InvBasis[index] + made * cost) / (old + made)
            W.t0Inv[index] += made
            W.t0Cash[supplier] -= made * cost
            W.costSinks += made * cost
            capacity -= made
            total_inventory += made
            deficits[n] -= made
            return made

        total_deficit = sum(deficits)
        initial_budget = max(0.0, min(capacity, cfg['maxInventory'] - total_inventory, total_deficit))
        cash_can_bind = initial_budget * max(costs[n] for n in positive) > W.t0Cash[supplier]
        if initial_budget < len(positive) or cash_can_bind:
            for n in priority:
                make(n, min(1, deficits[n]))
        else:
            reserved = set()
            for _pass in range(NE):
                total = sum(deficits)
                budget = max(0.0, min(capacity, cfg['maxInventory'] - total_inventory, total))
                small = [n for n in priority
                         if n not in reserved and deficits[n] > 0 and budget * deficits[n] / total < 1]
                if not small:
                    break
                for n in small:
                    make(n, min(1, deficits[n]))
                    reserved.add(n)

        for _pass in range(NE + 2):
            if capacity <= 1e-9:
                break
            feasible = [min(deficits[n], math.floor(max(0.0, W.t0Cash[supplier]) / costs[n]))
                        for n in range(n_el)]
            total = sum(feasible)
            budget = max(0.0, min(capacity, cfg['maxInventory'] - total_inventory, total))
            if budget <= 1e-9:
                break
            if budget >= total:
                plans = list(feasible)
            elif budget < 1:
                plans = [budget * feasible[n] / total for n in range(n_el)]
            else:
                whole = math.floor(budget)
                quotas = [whole * feasible[n] / total for n in range(n_el)]
                plans = [math.floor(q) for q in quotas]
                remainder = whole - sum(plans)
                order = sorted(priority, key=lambda n: (-(quotas[n] - plans[n]), rank[n]))
                for n in order:
                    extra = min(1, feasible[n] - plans[n], remainder)
                    plans[n] += extra
                    remainder -= extra
            produced = 0.0
            for n in priority:
                produced += make(n, plans[n])
            if produced <= 1e-9:
                break


# --------------------------------------------------------------------------
# 4. Tier 1 input purchase
# --------------------------------------------------------------------------
def tier0_supplier(W, cfg, profiles, e, preferred, buyer, tick):
    preferred = int(preferred)
    best = float('inf')
    empty_price = float('inf')
    stocked = []
    empty = []
    for supplier in range(N0):
        if M.ELEMENTS[e] not in profiles[supplier]['elements']:
            continue
        index = supplier * NE + e
        quote = W.t0Price[index]
        if not math.isfinite(quote):
            continue
        if supplier == preferred:
            friction = 0.0
        else:
            rel = W.t0Rel[preferred * NE + e] if preferred >= 0 else 0.5
            friction = M.switching_cost(rel, cfg['taumin'], cfg['taumax'])
        effective = quote + friction
        if effective < empty_price - 1e-12:
            empty_price = effective
            empty = []
        if abs(effective - empty_price) <= 1e-12:
            empty.append(supplier)
        if W.t0Inv[index] >= cfg['minWholesaleLot']:
            if effective < best - 1e-12:
                best = effective
                stocked = []
            if abs(effective - best) <= 1e-12:
                stocked.append(supplier)
    tied = stocked if stocked else empty
    if not tied:
        return -1
    total = sum(1 / len(profiles[s]['elements']) for s in tied)
    draw = random_(cfg['seed'], tick, buyer + 12000000 + e * 1300000) * total
    for supplier in tied:
        draw -= 1 / len(profiles[supplier]['elements'])
        if draw < 0:
            return supplier
    return tied[-1]


def plan_and_buy_inputs(W, cfg, products, profiles, tick):
    W.t0Req.fill(0)
    W.t0FundedReq.fill(0)
    first_cohort = tick % NP
    first_firm = (tick * 37) % 100
    for rnd in range(100):
        for cohort_order in range(NP):
            cohort = (first_cohort + cohort_order) % NP
            company = cohort * 100 + ((first_firm + rnd) % 100)
            raw_base = company * NE
            product_base = company * NP
            suppliers = [tier0_supplier(W, cfg, profiles, e,
                                        W.preferredWholesale[raw_base + e], company, tick)
                         for e in range(NE)]
            for p in range(NP):
                if not W.t1Operates[product_base + p]:
                    continue
                product = products[p]
                cap = cfg['t1Capacity']
                output_qty = product['outputQty']                # count-preserving N→N
                target = tier1_stock_target(W, cfg, product, product_base + p)
                desired = max(0.0, min(cap, target - W.t1Fin[product_base + p]))
                replacement = M.conversion_cost(M.complexity(product), cfg)
                for element, ratio in product['inputs'].items():
                    e = M.ELEMENTS.index(element)
                    supplier = suppliers[e]
                    quote = W.t0Price[supplier * NE + e] if supplier >= 0 else W.t1LastBuy[raw_base + e]
                    raw_need = desired * ratio / output_qty
                    stocked = min(raw_need, W.raw[raw_base + e])
                    if desired > 0:
                        q = quote if math.isfinite(quote) else cfg['baseCost'] * W.difficulty[e]
                        replacement += (stocked * W.rawBasis[raw_base + e] + (raw_need - stocked) * q) / desired
                    else:
                        replacement += (ratio / output_qty) * (quote if math.isfinite(quote) else W.rawBasis[raw_base + e])
                W.t1ReplacementCost[product_base + p] = replacement
                if desired > 0 and replacement > W.t1Price[product_base + p] + 1e-9:
                    continue
                for element, ratio in product['inputs'].items():
                    e = M.ELEMENTS.index(element)
                    need = max(0.0, desired * ratio / output_qty - W.raw[raw_base + e])
                    if need > 0:
                        W.t1InputNeed[raw_base + e] += max(need, cfg['minWholesaleLot'])
            for e in range(NE):
                need = W.t1InputNeed[raw_base + e]
                if need <= 0:
                    continue
                request = math.ceil(need / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                W.t1PurchaseReq[raw_base + e] = request
                W.t0Req[e] += request
                chosen = suppliers[e]
                if chosen < 0:
                    continue
                supplier_index = chosen * NE + e
                quote = max(0.0, W.t0Price[supplier_index])
                affordable = math.floor(max(0.0, W.t1Cash[company]) / max(1e-9, quote))
                available = math.floor(max(0.0, W.t0Inv[supplier_index]))
                held = 0.0
                for material in range(NE):
                    held += W.raw[raw_base + material]
                for output in range(NP):
                    held += W.t1Fin[product_base + output]
                storage_room = math.floor(max(0.0, cfg['storage'] - held)
                                          / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                funded = math.floor(min(request, affordable, storage_room) / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                W.t0FundedReq[e] += funded
                if funded > 0:
                    W.t0Opportunities[e] += 1
                W.t0Demand[supplier_index] += funded
                bought = math.floor(min(funded, available) / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                attempt = 1 if request > 0 else 0
                W.t0RelAttempts[supplier_index] += attempt
                W.t0RelFulfilled[supplier_index] += attempt if bought >= request else 0
                W.t0RelChecks[supplier_index] += attempt
                W.t0RelAvailable[supplier_index] += attempt if available >= request else 0
                if bought <= 0:
                    continue
                old_raw = W.raw[raw_base + e]
                old_basis = W.rawBasis[raw_base + e]
                payment = bought * quote
                W.raw[raw_base + e] = old_raw + bought
                W.t1Bought[company] += bought
                W.rawBasis[raw_base + e] = (old_basis * old_raw + payment) / (old_raw + bought) if old_raw + bought > 0 else 0
                W.t1LastBuy[raw_base + e] = quote
                W.t1Cash[company] -= payment
                W.t0Cash[chosen] += payment
                W.t0Inv[supplier_index] -= bought
                W.t0Sold[supplier_index] += bought
                W.t0Revenue[supplier_index] += payment
                W.t0COGS[supplier_index] += bought * W.t0InvBasis[supplier_index]
                W.t0Ful[e] += bought
                W.preferredWholesale[raw_base + e] = chosen


# --------------------------------------------------------------------------
# 5. Tier 1 manufacture
# --------------------------------------------------------------------------
def manufacture(W, cfg, products):
    for company in range(N1):
        for p in range(NP):
            index = company * NP + p
            if not W.t1Operates[index]:
                continue
            product = products[p]
            raw_base = company * NE
            cap = cfg['t1Capacity']
            conv = M.conversion_cost(M.complexity(product), cfg)
            target = tier1_stock_target(W, cfg, product, index)
            output_qty = product['outputQty']                     # count-preserving N→N
            desired = min(cap, max(0.0, target - W.t1Fin[index]))
            made = math.floor(desired / output_qty)               # whole batches
            input_cost_per_item = 0.0
            for element, ratio in product['inputs'].items():
                e = M.ELEMENTS.index(element)
                made = min(made, math.floor(W.raw[raw_base + e] / ratio))
                input_cost_per_item += ratio * W.rawBasis[raw_base + e]
            input_cost_per_item /= output_qty
            made = min(made, math.floor(max(0.0, W.t1Cash[company])
                                        / max(1e-9, conv * output_qty)))
            if input_cost_per_item + conv > W.t1Price[index] + 1e-9:
                made = 0
            if made <= 0:
                continue
            made_items = made * output_qty
            for element, ratio in product['inputs'].items():
                e = M.ELEMENTS.index(element)
                W.raw[raw_base + e] -= made * ratio
            W.t1Cash[company] -= made_items * conv
            W.costSinks += made_items * conv
            old_fin = W.t1Fin[index]
            old_basis = W.t1FinBasis[index]
            unit_cost = input_cost_per_item + conv
            W.t1Fin[index] = old_fin + made_items
            W.t1FinBasis[index] = (old_basis * old_fin + unit_cost * made_items) / (old_fin + made_items) if old_fin + made_items > 0 else 0
            W.t1UnitCost[index] = unit_cost


# --------------------------------------------------------------------------
# 6. Pricing (T0 + T1)
# --------------------------------------------------------------------------
def price_learning_view(W, tier):
    return {
        'tier': tier,
        'price': getattr(W, f'{tier}Price'),
        'ages': getattr(W, f'{tier}LearnTicks'),
        'profits': getattr(W, f'{tier}LearnProfit'),
        'sales': getattr(W, f'{tier}LearnSales'),
        'previous': getattr(W, f'{tier}LearnPrevious'),
        'direction': getattr(W, f'{tier}LearnDirection'),
        'demand': getattr(W, f'{tier}LearnDemand'),
        'stocks': getattr(W, f'{tier}LearnStock'),
        'steps': getattr(W, f'{tier}LearnStep'),
        'opportunity': getattr(W, f'{tier}LearnOpportunity'),
        'potentialOpportunity': getattr(W, f'{tier}LearnPotentialOpportunity'),
    }


def learned_quote(view, cfg, index, stock, tick):
    price = view['price']
    ages = view['ages']
    if ages[index] < cfg['priceObservationTicks'] or (tick + index) % cfg['priceObservationTicks'] != 0:
        return min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, price[index]))
    profits = view['profits']
    sales = view['sales']
    previous = view['previous']
    direction = view['direction']
    demand = view['demand']
    stocks = view['stocks']
    steps = view['steps']
    if view['tier'] == 't2' and cfg['researchPriceMinimumPotentialOrders'] > 0:
        stale_evidence = view['potentialOpportunity'][index] >= cfg['researchPriceMinimumPotentialOrders']
    else:
        stale_evidence = ages[index] >= cfg['researchPriceMaxObservationTicks']
    enough_traffic = (not cfg['researchPriceMinimumOpportunities']
                      or view['opportunity'][index] >= cfg['researchPriceMinimumOpportunities']
                      or stale_evidence)
    if enough_traffic:
        average = profits[index] / ages[index]
        result = M.adaptive_price(
            old_price=price[index], profit=average,
            previous_profit=previous[index], direction=direction[index],
            sales=sales[index], stock=stock, demand=demand[index],
            available=sales[index] + stocks[index], step_scale=steps[index],
            k=cfg['k'], response=cfg['wholesalePriceResponse'])
        price[index] = result['price']
        direction[index] = result['direction']
        previous[index] = average
        steps[index] = result['stepScale']
        profits[index] = 0
        sales[index] = 0
        demand[index] = 0
        ages[index] = 0
        view['opportunity'][index] = 0
        view['potentialOpportunity'][index] = 0
    return min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, price[index]))


def price_markets(W, cfg, profiles, products, tick):
    t0_learning = price_learning_view(W, 't0')
    t1_learning = price_learning_view(W, 't1')
    for supplier in range(N0):
        for e in range(NE):
            index = supplier * NE + e
            if not math.isfinite(W.t0Price[index]):
                continue
            previous = W.t0Price[index]
            if W.t0Controller[supplier] and math.isfinite(W.t0PlayerPrice[index]):
                nxt = min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, W.t0PlayerPrice[index]))
            else:
                nxt = learned_quote(t0_learning, cfg, index, W.t0Inv[index], tick)
            W.t0PrevPrice[index] = previous
            W.t0Price[index] = nxt
            stable = 1 - min(1.0, abs(nxt - previous) / max(1e-9, previous)
                             / max(1e-9, cfg['switchingStableBand']))
            W.t0Stability[index] = stable
            W.t0RelPriceSum[index] += stable
            W.t0RelPriceSamples[index] += 1
    for company in range(N1):
        for p in range(NP):
            index = company * NP + p
            if not W.t1Operates[index]:
                continue
            previous = W.t1Price[index]
            if W.t1Controller[company] and math.isfinite(W.playerPrice[index]):
                nxt = min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, W.playerPrice[index]))
            else:
                nxt = learned_quote(t1_learning, cfg, index, W.t1Fin[index], tick)
            W.t1PrevPrice[index] = previous
            W.t1Price[index] = nxt
            stable = 1 - min(1.0, abs(nxt - previous) / max(1e-9, previous)
                             / max(1e-9, cfg['switchingStableBand']))
            W.t1PriceStability[index] = stable
            W.t1RelPriceSum[index] += stable
            W.t1RelPriceSamples[index] += 1


# --------------------------------------------------------------------------
# Tier 2 helpers
# --------------------------------------------------------------------------
def market_offers(W, tier, tick):
    if tier == 0:
        count = NE
        price = W.t0Price
        total = N0 * NE
    elif tier == 1:
        count = NP
        price = W.t1Price
        total = N1 * NP
    else:
        count = len(M.T2_PRODUCTS)
        price = W.t2Price
        total = int(W.t2LineCount)

    offers = [[] for _ in range(count)]
    for i in range(total):
        if not math.isfinite(price[i]) or (tier == 1 and not W.t1Operates[i]):
            continue
        market = int(W.t2LineProduct[i]) if tier == 2 else i % count
        offers[market].append(i)

    for market in offers:
        mlen = len(market)
        if tier == 1:
            ranks = {s: r for r, s in enumerate(market)}
            # NB: capture mlen — CPython empties the list during list.sort, so
            # len(market) inside the key is undefined (observed as 0).
            market.sort(key=lambda a: (price[a], (ranks[a] + tick) % mlen))
        else:
            market.sort(key=lambda a: (price[a], (a + tick * 37) % total))
    return offers


def choose_supplier(offers, stock, price, preferred, reliability, cfg, minimum=1, known_best=None):
    preferred = int(preferred)
    best = -1 if known_best is None else int(known_best)
    if known_best is None:
        for supplier in offers:
            if stock[supplier] >= minimum:
                best = supplier
                break
    if (preferred >= 0 and stock[preferred] >= minimum and math.isfinite(price[preferred])
            and (best < 0 or price[preferred] <= price[best]
                 + M.switching_cost(reliability[preferred], cfg['taumin'], cfg['taumax']))):
        return preferred
    if best >= 0:
        return best
    if not offers:
        return -1
    empty = offers[0]
    if (preferred >= 0 and preferred in offers
            and price[preferred] <= price[empty]
            + M.switching_cost(reliability[preferred], cfg['taumin'], cfg['taumax'])):
        return preferred
    return empty


def tier2_inventory_units(W, firm):
    total = 0.0
    for material in range(NP):
        if material < NE:
            total += W.t2Raw[firm * NE + material]
        else:
            total += W.t2T1Raw[firm * NP + material]
    for slot in range(int(W.t2FirmLineCount[firm])):
        total += W.t2Fin[W.t2FirmLines[firm * M4 + slot]]
    return total


def transfer_tier2_input(W, cfg, firm, material, supplier, request):
    is_basic = material < 4
    stock = W.t1Fin
    prices = W.t1Price
    cash = W.t1Cash
    supplier_firm = supplier // NP
    quote = prices[supplier]
    requested = max(0.0, min(math.ceil(request),
                             math.floor(cfg['storage'] - tier2_inventory_units(W, firm))))
    funded = math.floor(min(requested, W.t2Cash[firm] / quote))
    quantity = math.floor(min(funded, stock[supplier]))
    W.t1Demand[supplier] += funded
    if funded > 0:
        W.t1Opportunities[material] += 1
    W.t1RelAttempts[supplier] += 1
    W.t1RelAvailChecks[supplier] += 1
    if quantity >= requested:
        W.t1RelFulfilled[supplier] += 1
    if stock[supplier] >= requested:
        W.t1RelAvailable[supplier] += 1
    if quantity <= 0:
        return 0
    if is_basic:
        raw = W.t2Raw
        basis = W.t2RawBasis
    else:
        raw = W.t2T1Raw
        basis = W.t2T1Basis
    index = firm * (NE if is_basic else NP) + material
    old = raw[index]
    payment = quantity * quote
    basis[index] = (basis[index] * old + payment) / (old + quantity)
    raw[index] += quantity
    W.t2Bought[firm] += quantity
    W.t2Cash[firm] -= payment
    cash[supplier_firm] += payment
    stock[supplier] -= quantity
    W.t1Sold[supplier] += quantity
    W.t1Rev[supplier] += payment
    W.t1COGS[supplier] += quantity * W.t1FinBasis[supplier]
    W.t1IntermediateSold[material] += quantity
    W.t1IntermediateRevenue[material] += payment
    W.t2Preferred[firm * NP + material] = supplier
    return quantity


# --------------------------------------------------------------------------
# 7. Tier 2 buy / make / price
# --------------------------------------------------------------------------
def tier2_buy_make_price(W, cfg, products, profiles, t2_products, tick):
    t2_learning = price_learning_view(W, 't2')
    t1_offers = market_offers(W, 1, tick)
    procurement_profiles = [
        M.procurement_profile(p, cfg, W.t2ReferenceCost[p['id']] or M.reference_tier2_cost(p))
        for p in t2_products
    ]
    input_ratios = M.catalogue_input_ratios
    needs = [0.0] * NP
    plans = [0.0] * M4
    suppliers = [0] * NP
    offer_heads = [0] * NP

    for order in range(cfg['t2FirmCount']):
        firm = (order + tick * 137) % cfg['t2FirmCount']
        needs = [0.0] * NP
        plans = [0.0] * M4
        inventory_room = max(0.0, cfg['storage'] - tier2_inventory_units(W, firm))

        for material in range(NP):
            offers = t1_offers[material]
            while offer_heads[material] < len(offers) and W.t1Fin[offers[offer_heads[material]]] < 1:
                offer_heads[material] += 1
            best = offers[offer_heads[material]] if offer_heads[material] < len(offers) else -1
            suppliers[material] = choose_supplier(offers, W.t1Fin, W.t1Price,
                                                  W.t2Preferred[firm * NP + material],
                                                  W.t1Rel, cfg, 1, best)

        line_count = int(W.t2FirmLineCount[firm])
        for order2 in range(line_count):
            slot = (order2 + tick) % line_count
            line = int(W.t2FirmLines[firm * M4 + slot])
            product = t2_products[int(W.t2LineProduct[line])]
            c = product['complexity']
            output_qty = product['outputQty']              # count-preserving N→N
            capacity = cfg['t2Capacity'][c]                # per machine per tick
            target = M.inventory_target(c, cfg)            # fill G, finished = G/2
            desired = math.floor(min(capacity, max(0.0, target - W.t2Fin[line])) / output_qty)
            while desired > 0:
                missing = 0.0
                for material in range(NP):
                    ratio = input_ratios[product['id']][material]
                    if material < NE:
                        held = W.t2Raw[firm * NE + material]
                    else:
                        held = W.t2T1Raw[firm * NP + material]
                    missing += max(0.0, needs[material] + desired * ratio - held)
                if missing <= inventory_room:
                    break
                desired -= 1
            replacement = M.conversion_cost(c, cfg)
            for material, ratio in product['ingredients']:
                basic = material < 4
                index = firm * (NE if basic else NP) + material
                raw = W.t2Raw if basic else W.t2T1Raw
                basis = W.t2RawBasis if basic else W.t2T1Basis
                offers = t1_offers[material]
                supplier = suppliers[material] if suppliers[material] >= 0 else (offers[0] if offers else None)
                quote = W.t1Price[supplier] if supplier is not None else basis[index]
                stocked = min(desired * ratio, raw[index])
                if desired > 0:
                    replacement += (stocked * basis[index] + (desired * ratio - stocked) * quote) / (desired * output_qty)
                else:
                    replacement += (ratio / output_qty) * quote
            W.t2ReplacementCost[line] = replacement
            if replacement > W.t2Price[line] + 1e-9:
                desired = 0
            plans[slot] = desired
            for material, ratio in product['ingredients']:
                needs[material] += desired * ratio

        for material in range(NP):
            basic = material < 4
            index = firm * (NE if basic else NP) + material
            raw = W.t2Raw if basic else W.t2T1Raw
            need = max(0.0, needs[material] - raw[index])
            if not need:
                continue
            supplier = suppliers[material]
            if supplier >= 0:
                transfer_tier2_input(W, cfg, firm, material, supplier, need)

        for slot in range(line_count):
            line = int(W.t2FirmLines[firm * M4 + slot])
            product = t2_products[int(W.t2LineProduct[line])]
            output_qty = product['outputQty']
            made = plans[slot]                              # batches
            input_cost = 0.0                                # per batch
            for material, ratio in product['ingredients']:
                basic = material < 4
                index = firm * (NE if basic else NP) + material
                made = min(made, math.floor((W.t2Raw if basic else W.t2T1Raw)[index] / ratio))
                input_cost += ratio * (W.t2RawBasis if basic else W.t2T1Basis)[index]
            conv_per_item = M.conversion_cost(c, cfg)
            conversion_cost = conv_per_item * output_qty
            made = min(made, math.floor(W.t2Cash[firm] / conversion_cost))
            input_cost_per_item = input_cost / output_qty
            if input_cost_per_item + conv_per_item > W.t2Price[line] + 1e-9:
                made = 0
            if made > 0:
                for material, ratio in product['ingredients']:
                    if material < 4:
                        W.t2Raw[firm * NE + material] -= made * ratio
                    else:
                        W.t2T1Raw[firm * NP + material] -= made * ratio
                made_items = made * output_qty
                W.t2Cash[firm] -= made_items * conv_per_item
                W.costSinks += made_items * conv_per_item
                old = W.t2Fin[line]
                unit = input_cost_per_item + conv_per_item
                W.t2FinBasis[line] = (old * W.t2FinBasis[line] + unit * made_items) / (old + made_items)
                W.t2Fin[line] += made_items
                W.t2UnitCost[line] = unit
                W.t2Made[line] = made_items
            previous = W.t2Price[line]
            if W.t2Controller[firm] and math.isfinite(W.t2PlayerPrice[line]):
                W.t2Price[line] = min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, W.t2PlayerPrice[line]))
            else:
                W.t2Price[line] = learned_quote(t2_learning, cfg, line, W.t2Fin[line], tick)
            W.t2RelPriceSum[line] += 1 - min(1.0, abs(W.t2Price[line] - previous)
                                             / max(1e-9, previous * cfg['switchingStableBand']))
            W.t2RelPriceSamples[line] += 1
            W.t2MonthlyCapacity[line] += cfg['t2Capacity'][product['complexity']]


# --------------------------------------------------------------------------
# 8. End-user clearing (atomic retail)
# --------------------------------------------------------------------------
def clear_end_users(W, cfg, products, t2_products, tick):
    offers = market_offers(W, 2, tick)
    procurement_profiles = [
        M.procurement_profile(p, cfg, W.t2ReferenceCost[p['id']] or M.reference_tier2_cost(p))
        for p in t2_products
    ]
    cumulative_offers = []
    for market in offers:
        weights = [0.0] * len(market)
        total = 0.0
        for i, line in enumerate(market):
            total += 1 / W.t2FirmLineCount[W.t2LineFirm[line]]
            weights[i] = total
        cumulative_offers.append(weights)

    W.endPotential.fill(0)
    W.endActive.fill(0)
    W.endFulfilled.fill(0)
    W.endPriceLost.fill(0)
    W.endStockUnmet.fill(0)
    W.endLastMarket.fill(-1)
    W.endLastSupplier.fill(-1)
    W.endLastQ.fill(0)
    W.endLastFulfilled.fill(0)

    orders = 0
    filled_orders = 0
    activated = 0
    consumer_payments = 0.0
    seed = cfg['seed']
    n_t2 = len(t2_products)

    for buyer in range(cfg['endUserCount']):
        if random_(seed, tick, buyer + 2000000) >= cfg['consumerActivation']:
            continue
        activated += 1
        if random_(seed, tick, buyer + 3000000) < 0.60:
            slot = 0
        else:
            slot = 1 + math.floor(random_(seed, tick, buyer + 3100000) * (W.endBasketCount[buyer] - 1))
        relationship = buyer * 5 + slot
        sector = int(W.endBasket[relationship])
        previous = W.endNeedProduct[relationship]
        if previous >= NP and random_(seed, tick, buyer + 5100000) < 0.65:
            market = int(previous)
        else:
            base = sector * n_t2
            count = int(W.t2SectorCount[sector])
            draw = random_(seed, tick, buyer + 6000000) * W.t2SectorProductWeight[base + count - 1]
            offset = 0
            while offset < count - 1 and draw >= W.t2SectorProductWeight[base + offset]:
                offset += 1
            market = NP + int(W.t2SectorProducts[sector * n_t2 + offset])
        W.endNeedProduct[relationship] = market
        product = t2_products[market - NP]
        complexity = product['complexity']
        profile = procurement_profiles[product['id']]
        multiplier = profile['quantityFactor']
        latent_quantity = W.endQMax[buyer] * multiplier
        qmax = math.ceil(latent_quantity)
        rounding = random_(seed, tick, buyer + 7000000)
        potential_quantity = math.floor(latent_quantity) + (1 if rounding < latent_quantity % 1 else 0)
        W.endLastMarket[buyer] = market
        if potential_quantity <= 0:
            continue
        W.t2PotentialOrders[market - NP] += 1
        W.endPotential[market] += potential_quantity
        reference = profile['valuation']
        premium = 1 + cfg['tier2ReservationPremium'] * (complexity - 1)
        choke = reference * W.endChoke[buyer] * premium
        stock = W.t2Fin
        price = W.t2Price
        reliability = W.t2Rel
        market_offers_list = offers[market - NP]
        if W.endPreferredProduct[relationship] == market:
            preferred = int(W.endPreferredSupplier[relationship])
        else:
            preferred = -1
        candidates = []
        if preferred >= 0 and math.isfinite(price[preferred]):
            candidates.append(preferred)
        for sample in range(cfg['consumerSearchOffers']):
            if not market_offers_list:
                break
            weights = cumulative_offers[market - NP]
            draw = random_(seed, tick, buyer + 8000000 + sample * 1100000) * weights[-1]
            low = 0
            high = len(weights) - 1
            while low < high:
                middle = (low + high) >> 1
                if draw < weights[middle]:
                    high = middle
                else:
                    low = middle + 1
            candidate = market_offers_list[low]
            if candidate not in candidates:
                candidates.append(candidate)
        friction = M.switching_cost(reliability[preferred], cfg['taumin'], cfg['taumax']) if preferred >= 0 else 0.0
        candidates.sort(key=lambda a: price[a] + (0 if a == preferred else friction))
        seller = candidates[0] if candidates else -1

        def demand(quote):
            continuous = M.demand_at_price(latent_quantity, choke, quote, W.endEta[buyer])
            return min(qmax, math.floor(continuous) + (1 if rounding < continuous % 1 else 0))

        desired = demand(reference if seller < 0 else price[seller])
        for candidate in candidates:
            requested = demand(price[candidate])
            if requested <= 0:
                break
            W.t2Demand[candidate] += requested
            W.t2RelAttempts[candidate] += 1
            if stock[candidate] >= requested:
                seller = candidate
                desired = requested
                break
        W.endLastMarket[buyer] = market
        W.endLastSupplier[buyer] = seller
        W.endLastQ[buyer] = desired
        W.endActive[market] += desired
        W.endPriceLost[market] += potential_quantity - desired
        if desired <= 0:
            continue
        orders += 1
        W.t2Opportunities[market - NP] += 1
        if seller < 0 or stock[seller] < desired:
            W.endStockUnmet[market] += desired
            continue
        payment = desired * price[seller]
        consumer_payments += payment
        stock[seller] -= desired
        W.t2Cash[W.t2LineFirm[seller]] += payment
        W.t2LastSaleTick[W.t2LineFirm[seller]] = tick
        W.t2Sold[seller] += desired
        W.t2Revenue[seller] += payment
        W.t2COGS[seller] += desired * W.t2FinBasis[seller]
        W.t2RelFulfilled[seller] += 1
        W.t2RelAvailable[seller] += 1
        W.endPreferredProduct[relationship] = market
        W.endPreferredSupplier[relationship] = seller
        W.endLastFulfilled[buyer] = desired
        W.endFulfilled[market] += desired
        filled_orders += 1

    return {'orders': orders, 'filledOrders': filled_orders, 'activated': activated,
            'consumerPayments': consumer_payments}


# --------------------------------------------------------------------------
# 9. Observation, reliability, expansion
# --------------------------------------------------------------------------
def update_reliability(W, cfg, tick):
    if tick % MONTH != 0:
        return
    for i in range(N0 * NE):
        if math.isfinite(W.t0Price[i]):
            attempts = W.t0RelAttempts[i]
            checks = W.t0RelChecks[i]
            score = M.reliability_score(
                W.t0RelFulfilled[i] / attempts if attempts else 1,
                W.t0RelPriceSum[i] / W.t0RelPriceSamples[i] if W.t0RelPriceSamples[i] else 1,
                W.t0RelAvailable[i] / checks if checks else 1)
            W.t0Rel[i] = M.next_reliability(W.t0Rel[i], score, cfg['reliabilityAlpha'])
            W.t0RelAttempts[i] = 0
            W.t0RelFulfilled[i] = 0
            W.t0RelChecks[i] = 0
            W.t0RelAvailable[i] = 0
            W.t0RelPriceSum[i] = 0
            W.t0RelPriceSamples[i] = 0
    for i in range(N1 * NP):
        if W.t1Operates[i]:
            attempts = W.t1RelAttempts[i]
            checks = W.t1RelAvailChecks[i]
            score = M.reliability_score(
                W.t1RelFulfilled[i] / attempts if attempts else 1,
                W.t1RelPriceSum[i] / W.t1RelPriceSamples[i] if W.t1RelPriceSamples[i] else 1,
                W.t1RelAvailable[i] / checks if checks else 1)
            W.t1Rel[i] = M.next_reliability(W.t1Rel[i], score, cfg['reliabilityAlpha'])
            W.t1RelAttempts[i] = 0
            W.t1RelFulfilled[i] = 0
            W.t1RelAvailChecks[i] = 0
            W.t1RelAvailable[i] = 0
            W.t1RelPriceSum[i] = 0
            W.t1RelPriceSamples[i] = 0


def observe_markets(W, cfg, profiles):
    if cfg['researchPriceMinimumOpportunities'] > 0:
        opp_weights = {
            't0': [0.0] * NE,
            't1': [0.0] * NP,
            't2': [0.0] * len(M.T2_PRODUCTS),
        }
        for profile in profiles:
            for element in profile['elements']:
                opp_weights['t0'][M.ELEMENTS.index(element)] += 1 / len(profile['elements'])
        for i in range(N1 * NP):
            if W.t1Operates[i]:
                opp_weights['t1'][i % NP] += 1
        for i in range(int(W.t2LineCount)):
            opp_weights['t2'][int(W.t2LineProduct[i])] += 1 / W.t2FirmLineCount[W.t2LineFirm[i]]
    else:
        opp_weights = None

    for tier, count in (('t0', N0 * NE), ('t1', N1 * NP), ('t2', int(W.t2LineCount))):
        sales = getattr(W, f'{tier}Sold')
        demand = getattr(W, f'{tier}Demand')
        forecast = getattr(W, f'{tier}DemandEMA')
        actual_sales = getattr(W, f'{tier}SalesEMA')
        revenue = W.t1Rev if tier == 't1' else getattr(W, f'{tier}Revenue')
        cogs = getattr(W, f'{tier}COGS')
        profits = getattr(W, f'{tier}LearnProfit')
        quantities = getattr(W, f'{tier}LearnSales')
        ages = getattr(W, f'{tier}LearnTicks')
        requests = getattr(W, f'{tier}LearnDemand')
        stocks = getattr(W, f'{tier}LearnStock')
        held = W.t0Inv if tier == 't0' else (W.t1Fin if tier == 't1' else W.t2Fin)
        for i in range(count):
            if (tier == 't0' and not math.isfinite(W.t0Price[i])) or (tier == 't1' and not W.t1Operates[i]):
                continue
            forecast[i] += cfg['alpha'] * (max(demand[i], sales[i]) - forecast[i])
            actual_sales[i] += cfg['alpha'] * (sales[i] - actual_sales[i])
            profits[i] += revenue[i] - cogs[i]
            quantities[i] += sales[i]
            ages[i] += 1
            if opp_weights:
                if tier == 't0':
                    market = i % NE
                elif tier == 't1':
                    market = i % NP
                else:
                    market = int(W.t2LineProduct[i])
                if tier == 't0':
                    weight = 1 / len(profiles[i // NE]['elements'])
                elif tier == 't1':
                    weight = 1
                else:
                    weight = 1 / W.t2FirmLineCount[W.t2LineFirm[i]]
                getattr(W, f'{tier}LearnOpportunity')[i] += \
                    getattr(W, f'{tier}Opportunities')[market] * weight / opp_weights[tier][market]
                if tier == 't2':
                    W.t2LearnPotentialOpportunity[i] += W.t2PotentialOrders[market] * weight / opp_weights['t2'][market]
            requests[i] += max(demand[i], sales[i])
            stocks[i] = held[i]
            if tier == 't2':
                W.t2MonthSold[i] += sales[i]


def expand_tier2_bots(W, cfg, t2_products, tick):
    if tick % MONTH != 0:
        return
    for line in range(int(W.t2LineCount)):
        attempts = W.t2RelAttempts[line]
        score = M.reliability_score(
            W.t2RelFulfilled[line] / attempts if attempts else 1,
            W.t2RelPriceSum[line] / W.t2RelPriceSamples[line] if W.t2RelPriceSamples[line] else 1,
            W.t2RelAvailable[line] / attempts if attempts else 1)
        W.t2Rel[line] = M.next_reliability(W.t2Rel[line], score, cfg['reliabilityAlpha'])
        W.t2RelAttempts[line] = 0
        W.t2RelFulfilled[line] = 0
        W.t2RelAvailable[line] = 0
        W.t2RelPriceSum[line] = 0
        W.t2RelPriceSamples[line] = 0
    # Canon §7: bots do not expand to multi-machine firms (holding-company
    # acquisition is deferred); firms stay single-machine and grow equity only.
    W.t2MonthSold.fill(0)
    W.t2MonthlyCapacity.fill(0)


# --------------------------------------------------------------------------
# Tick orchestrator
# --------------------------------------------------------------------------
def tick(W: WorldState, cfg, tick, products=None, profiles=None, t2_products=None, state=None):
    products = products if products is not None else M.PRODUCTS
    profiles = profiles if profiles is not None else T0P
    t2_products = t2_products if t2_products is not None else M.T2_PRODUCTS
    state = state if state is not None else {}

    reset_tick(W)
    W.costSinks = 0
    W.equipmentSinks = 0
    update_environment(W, cfg, tick)
    produce_tier0(W, cfg, profiles, tick)

    from . import fast as _fast
    if _fast._HAVE_NUMBA:
        _fast.plan_and_buy_inputs_fast(W, cfg, tick)
    else:
        plan_and_buy_inputs(W, cfg, products, profiles, tick)
    manufacture(W, cfg, products)
    price_markets(W, cfg, profiles, products, tick)

    if _fast._HAVE_NUMBA:
        _fast.tier2_buy_make_price_fast(W, cfg, tick)
        o, f, a, cp = _fast.clear_end_users_fast(W, cfg, tick)
        counts = {'orders': o, 'filledOrders': f, 'activated': a, 'consumerPayments': cp}
    else:
        tier2_buy_make_price(W, cfg, products, profiles, t2_products, tick)
        counts = clear_end_users(W, cfg, products, t2_products, tick)

    if _fast._HAVE_NUMBA:
        _fast.observe_markets_fast(W, cfg, profiles)
    else:
        observe_markets(W, cfg, profiles)
    update_reliability(W, cfg, tick)
    expand_tier2_bots(W, cfg, t2_products, tick)

    state['activatedConsumers'] = counts['activated']
    state['consumerPayments'] = counts['consumerPayments']
    state['costSinks'] = W.costSinks
    state['equipmentSinks'] = W.equipmentSinks
    state['activeOrders'] = counts['orders']
    state['fulfilledOrders'] = counts['filledOrders']
    return state
