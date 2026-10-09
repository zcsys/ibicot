"""The 9-phase economy tick, aligned to ``docs/design_canon.md`` §12.4.

``tick()`` mutates a :class:`~economy.core.state.WorldState` in place and
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
round_to_cent = M.round_to_cent
M4 = M.T2_MAX_PRODUCTS_PER_FIRM


def tier1_stock_target(world, cfg, product, index):
    # canon: desired inventory = fill G, split 1:1 → finished target = G/2
    return M.inventory_target(M.complexity(product), cfg)


# --------------------------------------------------------------------------
# 1. Reset per-tick scratch
# --------------------------------------------------------------------------
_RESET_NAMES = [
    't0Opportunities', 't1Opportunities', 't2Opportunities', 't2PotentialOrders',
    't1Bought', 't2Bought', 't0Sold', 't0Revenue', 't0COGS', 't0Demand',
    't1Demand', 't2Demand', 't1Sold', 't1Revenue', 't1COGS', 't1IntermediateSold',
    't1IntermediateRevenue', 'active', 'potential', 'fulfilled', 'priceLost',
    'stockUnmet', 't0Fulfilled', 't0FundedReq', 't1InputNeed', 't1PurchaseReq',
    't2MatSpend', 't2MatOrders', 'loyaltySwitches', 'loyaltyPenalties',
]


def reset_tick(world: WorldState) -> None:
    for name in _RESET_NAMES:
        getattr(world, name).fill(0)
    world.t2Sold.fill(0)
    world.t2Revenue.fill(0)
    world.t2COGS.fill(0)
    world.t2Made.fill(0)


# --------------------------------------------------------------------------
# 2. Environment (difficulty)
# --------------------------------------------------------------------------
def update_environment(world, cfg, tick):
    for element in range(NE):
        world.difficulty[element] = M.clamp(
            world.difficulty[element] + cfg['theta'] * (cfg['difficultyTarget'] - world.difficulty[element])
            + cfg['sigma'] * normal_(cfg['seed'], tick, element * 4),
            cfg['difficultyMin'], cfg['difficultyMax'])


# --------------------------------------------------------------------------
# 3. Tier 0 extraction
# --------------------------------------------------------------------------
def operate_tier0(world, cfg, profiles, tick):
    seed = cfg['seed']
    for supplier in range(N0):
        elements = profiles[supplier]['element_indices']  # sorted ascending
        n_el = len(elements)
        # T0 targets half its storage (order-up-to 50 % of the pool), leaving
        # headroom rather than filling to the brim. Each element gets an even share.
        targets = [cfg['t0Storage'] / 2 / n_el for element in elements]
        deficits = [max(0.0, targets[n] - world.t0Inv[supplier * NE + elements[n]]) for n in range(n_el)]
        capacity = max(0.0, cfg['t0Capacity'])
        total_inventory = sum(max(0.0, world.t0Inv[supplier * NE + element]) for element in elements)
        costs = []
        for element in elements:
            index = supplier * NE + element
            cost = max(1e-9, cfg['baseCost'] * world.difficulty[element])
            world.t0Cost[index] = cost
            if not math.isfinite(world.t0Price[index]) or world.t0Price[index] <= 0:
                world.t0Price[index] = cost * (1 + cfg['t0Markup'])
            costs.append(cost)
        # Profit-gate extraction like T1/T2 manufacture: pull raw out of Gaia only
        # while the posted raw price covers the extraction cost, tapering as the
        # extraction margin thins (productionMarginBand).
        for n in range(n_el):
            index = supplier * NE + elements[n]
            price = world.t0Price[index]
            cost = costs[n]
            if cost > price + 1e-9:
                deficits[n] = 0.0
            else:
                margin = (price - cost) / max(price, 1e-9)
                deficits[n] *= min(1.0, max(0.0, margin / cfg['productionMarginBand']))
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
            headroom = max(0.0, cfg['t0Storage'] - total_inventory)
            affordable = math.floor(max(0.0, world.t0Cash[supplier]) / cost)
            made = max(0.0, min(planned, deficits[n], capacity, headroom, affordable))
            old = world.t0Inv[index]
            if made > 0:
                world.t0InvBasis[index] = (old * world.t0InvBasis[index] + made * cost) / (old + made)
            world.t0Inv[index] += made
            world.t0Cash[supplier] -= made * cost
            world.costSinks += made * cost
            capacity -= made
            total_inventory += made
            deficits[n] -= made
            return made

        total_deficit = sum(deficits)
        initial_budget = max(0.0, min(capacity, cfg['t0Storage'] - total_inventory, total_deficit))
        cash_can_bind = initial_budget * max(costs[n] for n in positive) > world.t0Cash[supplier]
        if initial_budget < len(positive) or cash_can_bind:
            for n in priority:
                make(n, min(1, deficits[n]))
        else:
            reserved = set()
            for _pass in range(NE):
                total = sum(deficits)
                budget = max(0.0, min(capacity, cfg['t0Storage'] - total_inventory, total))
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
            feasible = [min(deficits[n], math.floor(max(0.0, world.t0Cash[supplier]) / costs[n]))
                        for n in range(n_el)]
            total = sum(feasible)
            budget = max(0.0, min(capacity, cfg['t0Storage'] - total_inventory, total))
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
def tier0_supplier(world, cfg, profiles, element, preferred, buyer, tick):
    preferred = int(preferred)
    best = float('inf')
    empty_price = float('inf')
    stocked = []
    empty = []
    for supplier in range(N0):
        if M.ELEMENTS[element] not in profiles[supplier]['elements']:
            continue
        index = supplier * NE + element
        quote = world.t0Price[index]
        if not math.isfinite(quote):
            continue
        if supplier == preferred:
            friction = 0.0
        else:
            rel = world.t0Rel[preferred * NE + element] if preferred >= 0 else 0.5
            friction = M.loyalty_surcharge(quote, rel)
        effective = quote + friction
        if effective < empty_price - 1e-12:
            empty_price = effective
            empty = []
        if abs(effective - empty_price) <= 1e-12:
            empty.append(supplier)
        if world.t0Inv[index] >= cfg['minWholesaleLot']:
            if effective < best - 1e-12:
                best = effective
                stocked = []
            if abs(effective - best) <= 1e-12:
                stocked.append(supplier)
    tied = stocked if stocked else empty
    if not tied:
        return -1
    total = sum(1 / len(profiles[s]['elements']) for s in tied)
    draw = random_(cfg['seed'], tick, buyer + 12000000 + element * 1300000) * total
    for supplier in tied:
        draw -= 1 / len(profiles[supplier]['elements'])
        if draw < 0:
            return supplier
    return tied[-1]


def plan_and_buy_inputs(world, cfg, products, profiles, tick):
    world.t0Req.fill(0)
    world.t0FundedReq.fill(0)
    first_cohort = tick % NP
    first_firm = (tick * 37) % 100
    for rnd in range(100):
        for cohort_order in range(NP):
            cohort = (first_cohort + cohort_order) % NP
            company = cohort * 100 + ((first_firm + rnd) % 100)
            raw_base = company * NE
            product_base = company * NP
            suppliers = [tier0_supplier(world, cfg, profiles, element,
                                        world.preferredWholesale[raw_base + element], company, tick)
                         for element in range(NE)]
            for p in range(NP):
                if not world.t1Operates[product_base + p]:
                    continue
                product = products[p]
                cap = cfg['t1Capacity']
                output_qty = product['outputQty']                # count-preserving N→N
                target = tier1_stock_target(world, cfg, product, product_base + p)
                desired = max(0.0, min(cap, target - world.t1Fin[product_base + p]))
                replacement = M.conversion_cost(M.complexity(product), cfg)
                current_cost = M.conversion_cost(M.complexity(product), cfg)
                for element_name, ratio in product['inputs'].items():
                    element = M.ELEMENTS.index(element_name)
                    supplier = suppliers[element]
                    quote = world.t0Price[supplier * NE + element] if supplier >= 0 else world.t1LastBuy[raw_base + element]
                    current_cost += (ratio / output_qty) * (quote if math.isfinite(quote) else cfg['baseCost'] * world.difficulty[element])
                    raw_need = desired * ratio / output_qty
                    stocked = min(raw_need, world.raw[raw_base + element])
                    if desired > 0:
                        q = quote if math.isfinite(quote) else cfg['baseCost'] * world.difficulty[element]
                        replacement += (stocked * world.rawBasis[raw_base + element] + (raw_need - stocked) * q) / desired
                    else:
                        replacement += (ratio / output_qty) * (quote if math.isfinite(quote) else world.rawBasis[raw_base + element])
                world.t1ReplacementCost[product_base + p] = replacement
                # Elastic input demand (no hard freeze): throttle the buy/produce
                # quantity by the marginal-cost/price ratio — reversed T3 curve: 0 at/above break-even, full at zero cost.
                r = current_cost / max(world.t1Price[product_base + p], 1e-9)
                desired = math.floor(desired * min(1.0, max(0.0, (1.0 - r) / cfg['productionMarginBand'])) + 0.5)
                for element_name, ratio in product['inputs'].items():
                    element = M.ELEMENTS.index(element_name)
                    need = max(0.0, desired * ratio / output_qty - world.raw[raw_base + element])
                    if need > 0:
                        world.t1InputNeed[raw_base + element] += max(need, cfg['minWholesaleLot'])
            for element in range(NE):
                need = world.t1InputNeed[raw_base + element]
                if need <= 0:
                    continue
                request = math.ceil(need / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                world.t1PurchaseReq[raw_base + element] = request
                world.t0Req[element] += request
                chosen = suppliers[element]
                if chosen < 0:
                    continue
                preferred = int(world.preferredWholesale[raw_base + element])
                loyalty_charge = 0.0
                if chosen != preferred and preferred >= 0 and world.t0Inv[preferred * NE + element] >= request:
                    loyalty_charge = M.loyalty_charge(cfg['baseCost'], world.t0Rel[preferred * NE + element],
                                                    world.lm1)
                    if loyalty_charge > world.t1Cash[company]:
                        chosen = preferred
                        loyalty_charge = 0.0
                supplier_index = chosen * NE + element
                quote = max(0.0, world.t0Price[supplier_index])
                affordable = math.floor(max(0.0, world.t1Cash[company] - loyalty_charge) / max(1e-9, quote))
                available = math.floor(max(0.0, world.t0Inv[supplier_index]))
                held = 0.0
                for material in range(NE):
                    held += world.raw[raw_base + material]
                for output in range(NP):
                    held += world.t1Fin[product_base + output]
                storage_room = math.floor(max(0.0, cfg['storage'] - held)
                                          / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                funded = math.floor(min(request, affordable, storage_room) / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                world.t0FundedReq[element] += funded
                if funded > 0:
                    world.t0Opportunities[element] += 1
                world.t0Demand[supplier_index] += funded
                bought = math.floor(min(funded, available) / cfg['minWholesaleLot']) * cfg['minWholesaleLot']
                attempt = 1 if request > 0 else 0
                world.t0RelAttempts[supplier_index] += attempt
                world.t0RelChecks[supplier_index] += attempt
                world.t0RelAvailable[supplier_index] += attempt if available >= request else 0
                if bought <= 0:
                    continue
                old_raw = world.raw[raw_base + element]
                old_basis = world.rawBasis[raw_base + element]
                payment = bought * quote
                world.raw[raw_base + element] = old_raw + bought
                world.t1Bought[company] += bought
                world.rawBasis[raw_base + element] = (old_basis * old_raw + payment) / (old_raw + bought) if old_raw + bought > 0 else 0
                world.t1LastBuy[raw_base + element] = quote
                world.t1Cash[company] -= payment
                world.t0Cash[chosen] += payment
                world.t0Inv[supplier_index] -= bought
                world.t0Sold[supplier_index] += bought
                world.t0Revenue[supplier_index] += payment
                world.t0COGS[supplier_index] += bought * world.t0InvBasis[supplier_index]
                world.t0Fulfilled[element] += bought
                if loyalty_charge > 0.0:
                    world.t1Cash[company] -= loyalty_charge
                    world.t0Cash[preferred] += loyalty_charge
                    world.loyaltySwitches[0] += 1.0
                    world.loyaltyPenalties[0] += loyalty_charge
                world.preferredWholesale[raw_base + element] = chosen


# --------------------------------------------------------------------------
# 5. Tier 1 production
# --------------------------------------------------------------------------
def operate_tier1(world, cfg, products):
    # Per-product constants (cfg-driven scale + structural recipe), computed once
    # per tick so the firm loop avoids dict/index lookups.  ``products`` has only
    # ``NP`` entries; the firm loop is the hot part.
    convs = [M.conversion_cost(M.complexity(p), cfg) for p in products]
    targets = [M.inventory_target(M.complexity(p), cfg) for p in products]
    outputs = [int(p['outputQty']) for p in products]
    elem_lists = [[M.ELEMENTS.index(e) for e in p['inputs']] for p in products]
    ratio_lists = [[float(r) for r in p['inputs'].values()] for p in products]

    cap = cfg['t1Capacity']
    # Iterate only the operating firm-product slots (ascending index == the old
    # company-major, product-minor order, so shared raw/cash drain semantics are
    # unchanged while the ~9/10 no-op slots are skipped).
    for index in np.flatnonzero(world.t1Operates):
        company = index // NP
        p = index % NP
        raw_base = company * NE
        conv = convs[p]
        target = targets[p]
        output_qty = outputs[p]                                 # count-preserving N→N
        elems = elem_lists[p]
        ratios = ratio_lists[p]
        desired = min(cap, max(0.0, target - world.t1Fin[index]))
        made = math.floor(desired / output_qty)               # whole batches
        input_cost_per_item = 0.0
        for element, ratio in zip(elems, ratios):
            made = min(made, math.floor(world.raw[raw_base + element] / ratio))
            input_cost_per_item += ratio * world.rawBasis[raw_base + element]
        input_cost_per_item /= output_qty
        made = min(made, math.floor(max(0.0, world.t1Cash[company])
                                    / max(1e-9, conv * output_qty)))
        if input_cost_per_item + conv > world.t1Price[index] + 1e-9:
            made = 0
        if made <= 0:
            continue
        made_items = made * output_qty
        for element, ratio in zip(elems, ratios):
            world.raw[raw_base + element] -= made * ratio
        world.t1Cash[company] -= made_items * conv
        world.costSinks += made_items * conv
        old_fin = world.t1Fin[index]
        old_basis = world.t1FinBasis[index]
        unit_cost = input_cost_per_item + conv
        world.t1Fin[index] = old_fin + made_items
        world.t1FinBasis[index] = (old_basis * old_fin + unit_cost * made_items) / (old_fin + made_items) if old_fin + made_items > 0 else 0
        world.t1UnitCost[index] = unit_cost


# --------------------------------------------------------------------------
# 6. Pricing (T0 + T1)
# --------------------------------------------------------------------------
def price_learning_view(world, tier):
    return {
        'tier': tier,
        'price': getattr(world, f'{tier}Price'),
        'ages': getattr(world, f'{tier}LearnTicks'),
        'profits': getattr(world, f'{tier}LearnProfit'),
        'sales': getattr(world, f'{tier}LearnSales'),
        'previous': getattr(world, f'{tier}LearnPrevious'),
        'direction': getattr(world, f'{tier}LearnDirection'),
        'demand': getattr(world, f'{tier}LearnDemand'),
        'steps': getattr(world, f'{tier}LearnStep'),
        'opportunity': getattr(world, f'{tier}LearnOpportunity'),
        'potentialOpportunity': getattr(world, f'{tier}LearnPotentialOpportunity'),
    }


def learned_quote(view, cfg, index, stock, tick):
    price = view['price']
    ages = view['ages']
    if ages[index] < cfg['priceObservationTicks'] or (tick + index) % cfg['priceObservationTicks'] != 0:
        return round_to_cent(min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, price[index])))
    profits = view['profits']
    sales = view['sales']
    previous = view['previous']
    direction = view['direction']
    demand = view['demand']
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
            available=sales[index], step_scale=steps[index],
            pricing_aggressiveness=cfg['pricingAggressiveness'], response=cfg['wholesalePriceResponse'])
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
    return round_to_cent(min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, price[index])))


def _clamp_round_cent(price):
    """Vectorized ``round_to_cent(min(MAX, max(MIN, price)))`` for non-negative prices."""
    p = np.minimum(MAX_UNIT_PRICE, np.maximum(MIN_UNIT_PRICE, price))
    return np.floor(p * 100.0 + 0.5) / 100.0


def price_markets(world, cfg, profiles, products, tick):
    obs = cfg['priceObservationTicks']
    band = cfg['switchingStableBand']

    # ---- Tier 0 (wholesale) ----
    t0 = world.t0Price
    idx0 = np.arange(N0 * NE)
    valid0 = idx0[np.isfinite(t0)]
    prev0 = t0[valid0].copy()
    nxt0 = _clamp_round_cent(prev0)
    player0 = (world.t0Controller[valid0 // NE] != 0) & np.isfinite(world.t0PlayerPrice[valid0])
    if player0.any():
        nxt0 = np.where(player0, _clamp_round_cent(world.t0PlayerPrice[valid0]), nxt0)
    t0_learning = price_learning_view(world, 't0')
    due0 = (~player0) & (t0_learning['ages'][valid0] >= obs) & ((tick + valid0) % obs == 0)
    for j in np.flatnonzero(due0):
        i = int(valid0[j])
        nxt0[j] = learned_quote(t0_learning, cfg, i, world.t0Inv[i], tick)
    world.t0PrevPrice[valid0] = prev0
    world.t0Price[valid0] = nxt0
    stable0 = 1.0 - np.minimum(1.0, np.maximum(0.0, nxt0 - prev0)
                               / np.maximum(1e-9, prev0) / np.maximum(1e-9, band))
    world.t0Stability[valid0] = stable0
    world.t0RelPriceSum[valid0] += stable0
    world.t0RelPriceSamples[valid0] += 1

    # ---- Tier 1 (refined) ----
    t1 = world.t1Price
    idx1 = np.flatnonzero(world.t1Operates)
    prev1 = t1[idx1].copy()
    nxt1 = _clamp_round_cent(prev1)
    player1 = (world.t1Controller[idx1 // NP] != 0) & np.isfinite(world.playerPrice[idx1])
    if player1.any():
        nxt1 = np.where(player1, _clamp_round_cent(world.playerPrice[idx1]), nxt1)
    t1_learning = price_learning_view(world, 't1')
    due1 = (~player1) & (t1_learning['ages'][idx1] >= obs) & ((tick + idx1) % obs == 0)
    for j in np.flatnonzero(due1):
        i = int(idx1[j])
        nxt1[j] = learned_quote(t1_learning, cfg, i, world.t1Fin[i], tick)
    world.t1PrevPrice[idx1] = prev1
    world.t1Price[idx1] = nxt1
    stable1 = 1.0 - np.minimum(1.0, np.maximum(0.0, nxt1 - prev1)
                               / np.maximum(1e-9, prev1) / np.maximum(1e-9, band))
    world.t1PriceStability[idx1] = stable1
    world.t1RelPriceSum[idx1] += stable1
    world.t1RelPriceSamples[idx1] += 1


# --------------------------------------------------------------------------
# Tier 2 helpers
# --------------------------------------------------------------------------
def market_offers(world, tier, tick):
    if tier == 0:
        count = NE
        price = world.t0Price
        total = N0 * NE
    elif tier == 1:
        count = NP
        price = world.t1Price
        total = N1 * NP
    else:
        count = len(M.T2_PRODUCTS)
        price = world.t2Price
        total = int(world.t2LineCount)

    offers = [[] for _ in range(count)]
    for i in range(total):
        if not math.isfinite(price[i]) or (tier == 1 and not world.t1Operates[i]):
            continue
        market = int(world.t2LineProduct[i]) if tier == 2 else i % count
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


def market_offers_table(world, tier, tick):
    """Vectorized ``market_offers`` — returns ``(flat, off)`` NumPy arrays.

    ``flat`` is the concatenation of the per-market sorted offer lists (the same
    sequence ``market_offers`` yields, market 0 first then 1, …), and ``off`` is
    its length-``count+1`` offset table (``flat[off[m]:off[m+1]]`` = market ``m``).
    Identical ordering to ``market_offers``: each market is sorted by
    ``(price, tiebreak)``, where the tiebreak is a rotating index used to
    de-bias the cheapest-first walk.
    """
    count = NE if tier == 0 else (NP if tier == 1 else len(M.T2_PRODUCTS))
    if tier == 0:
        total = N0 * NE
        price = world.t0Price
        idx = np.arange(total)
        market = idx % count
        valid = np.isfinite(price)
    elif tier == 1:
        total = N1 * NP
        price = world.t1Price
        idx = np.arange(total)
        market = idx % count
        valid = np.isfinite(price) & (world.t1Operates != 0)
    else:
        total = int(world.t2LineCount)
        price = world.t2Price[:total]
        idx = np.arange(total)
        market = world.t2LineProduct[:total].astype(np.int64)
        valid = np.isfinite(price)

    idx = idx[valid]
    market = market[valid]
    p = price[valid]

    if tier == 1:
        # Original ranks each market list by ascending index before the sort, so
        # the within-market rank is the position in ascending-index order (among
        # valid entries — computed generally so gaps stay correct).
        order_m = np.argsort(market, kind='stable')
        grouped = market[order_m]
        uniq, first = np.unique(grouped, return_index=True)
        start = np.zeros(count, dtype=np.int64)
        start[uniq] = first
        rank = np.empty(market.size, dtype=np.int64)
        rank[order_m] = np.arange(market.size, dtype=np.int64) - start[grouped]
        sizes = np.bincount(market, minlength=count)
        tiebreak = (rank + tick) % sizes[market]
    else:
        tiebreak = (idx + tick * 37) % total

    order = np.lexsort((tiebreak, p, market))
    flat = idx[order]
    off = np.zeros(count + 1, dtype=np.int64)
    off[1:] = np.cumsum(np.bincount(market, minlength=count))
    return flat, off


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
                 + M.loyalty_surcharge(price[best], reliability[preferred]))):
        return preferred
    if best >= 0:
        return best
    if not offers:
        return -1
    empty = offers[0]
    if (preferred >= 0 and preferred in offers
            and price[preferred] <= price[empty]
            + M.loyalty_surcharge(price[empty], reliability[preferred])):
        return preferred
    return empty


def tier2_inventory_units(world, firm):
    total = 0.0
    for material in range(NP):
        if material < NE:
            total += world.t2Raw[firm * NE + material]
        else:
            total += world.t2T1Raw[firm * NP + material]
    for slot in range(int(world.t2FirmLineCount[firm])):
        total += world.t2Fin[world.t2FirmLines[firm * M4 + slot]]
    return total


def transfer_tier2_input(world, cfg, firm, material, supplier, request):
    is_basic = material < 4
    stock = world.t1Fin
    prices = world.t1Price
    cash = world.t1Cash
    requested = max(0.0, min(math.ceil(request),
                             math.floor(cfg['storage'] - tier2_inventory_units(world, firm))))
    preferred = int(world.t2Preferred[firm * NP + material])
    firm_pid = int(world.t2LineProduct[int(world.t2FirmLines[firm * M4])])
    firm_cx = M.T2_PRODUCTS[firm_pid]['complexity']
    loyalty_charge = 0.0
    if supplier != preferred and preferred >= 0 and stock[preferred] >= requested:
        loyalty_charge = M.loyalty_charge(cfg['t1MaterialCost'] + cfg['conversionFactor'],
                                        world.t1Rel[preferred], world.lm2[firm_cx - 3])
        if loyalty_charge > world.t2Cash[firm]:
            supplier = preferred
            loyalty_charge = 0.0
    supplier_firm = supplier // NP
    quote = prices[supplier]
    funded = math.floor(min(requested, max(0.0, world.t2Cash[firm] - loyalty_charge) / quote))
    quantity = math.floor(min(funded, stock[supplier]))
    world.t1Demand[supplier] += funded
    if funded > 0:
        world.t1Opportunities[material] += 1
    world.t1RelAttempts[supplier] += 1
    world.t1RelAvailChecks[supplier] += 1
    if stock[supplier] >= requested:
        world.t1RelAvailable[supplier] += 1
    if quantity <= 0:
        return 0
    if is_basic:
        raw = world.t2Raw
        basis = world.t2RawBasis
    else:
        raw = world.t2T1Raw
        basis = world.t2T1Basis
    index = firm * (NE if is_basic else NP) + material
    old = raw[index]
    payment = quantity * quote
    world.t2MatSpend[firm_cx - 3] += payment
    world.t2MatOrders[firm_cx - 3] += 1.0
    basis[index] = (basis[index] * old + payment) / (old + quantity)
    raw[index] += quantity
    world.t2Bought[firm] += quantity
    world.t2Cash[firm] -= payment
    cash[supplier_firm] += payment
    stock[supplier] -= quantity
    world.t1Sold[supplier] += quantity
    world.t1Revenue[supplier] += payment
    world.t1COGS[supplier] += quantity * world.t1FinBasis[supplier]
    world.t1IntermediateSold[material] += quantity
    world.t1IntermediateRevenue[material] += payment
    if loyalty_charge > 0.0:
        world.t2Cash[firm] -= loyalty_charge
        world.t1Cash[preferred // NP] += loyalty_charge
        world.loyaltySwitches[1] += 1.0
        world.loyaltyPenalties[1] += loyalty_charge
    world.t2Preferred[firm * NP + material] = supplier
    return quantity


# --------------------------------------------------------------------------
# 7. Tier 2 buy / make / price
# --------------------------------------------------------------------------
def operate_tier2(world, cfg, products, profiles, t2_products, tick):
    t2_learning = price_learning_view(world, 't2')
    t1_offers = market_offers(world, 1, tick)
    procurement_profiles = [
        M.procurement_profile(p, cfg, world.t2ReferenceCost[p['id']] or M.reference_tier2_cost(p))
        for p in t2_products
    ]
    input_ratios = M.catalog_input_ratios
    needs = [0.0] * NP
    plans = [0.0] * M4
    suppliers = [0] * NP
    offer_heads = [0] * NP

    for order in range(cfg['t2FirmCount']):
        firm = (order + tick * 137) % cfg['t2FirmCount']
        needs = [0.0] * NP
        plans = [0.0] * M4
        inventory_room = max(0.0, cfg['storage'] - tier2_inventory_units(world, firm))

        for material in range(NP):
            offers = t1_offers[material]
            while offer_heads[material] < len(offers) and world.t1Fin[offers[offer_heads[material]]] < 1:
                offer_heads[material] += 1
            best = offers[offer_heads[material]] if offer_heads[material] < len(offers) else -1
            suppliers[material] = choose_supplier(offers, world.t1Fin, world.t1Price,
                                                  world.t2Preferred[firm * NP + material],
                                                  world.t1Rel, cfg, 1, best)

        line_count = int(world.t2FirmLineCount[firm])
        for order2 in range(line_count):
            slot = (order2 + tick) % line_count
            line = int(world.t2FirmLines[firm * M4 + slot])
            product = t2_products[int(world.t2LineProduct[line])]
            c = product['complexity']
            output_qty = product['outputQty']              # count-preserving N→N
            capacity = cfg['t2Capacity'][c]                # per machine per tick
            target = M.inventory_target(c, cfg)            # fill G, finished = G/2
            desired = math.floor(min(capacity, max(0.0, target - world.t2Fin[line])) / output_qty)
            while desired > 0:
                missing = 0.0
                for material in range(NP):
                    ratio = input_ratios[product['id']][material]
                    if material < NE:
                        held = world.t2Raw[firm * NE + material]
                    else:
                        held = world.t2T1Raw[firm * NP + material]
                    missing += max(0.0, needs[material] + desired * ratio - held)
                if missing <= inventory_room:
                    break
                desired -= 1
            replacement = M.conversion_cost(c, cfg)
            current_cost = M.conversion_cost(c, cfg)
            for material, ratio in product['ingredients']:
                basic = material < 4
                index = firm * (NE if basic else NP) + material
                raw = world.t2Raw if basic else world.t2T1Raw
                basis = world.t2RawBasis if basic else world.t2T1Basis
                offers = t1_offers[material]
                supplier = suppliers[material] if suppliers[material] >= 0 else (offers[0] if offers else None)
                quote = world.t1Price[supplier] if supplier is not None else basis[index]
                current_cost += (ratio / output_qty) * quote
                stocked = min(desired * ratio, raw[index])
                if desired > 0:
                    replacement += (stocked * basis[index] + (desired * ratio - stocked) * quote) / (desired * output_qty)
                else:
                    replacement += (ratio / output_qty) * quote
            world.t2ReplacementCost[line] = replacement
            if replacement > world.t2Price[line] + 1e-9:
                desired = 0
            # Elastic input demand (no hard freeze): throttle the buy/produce
            # quantity by the marginal-cost/price ratio — reversed T3 curve: 0 at/above break-even, full at zero cost.
            r = current_cost / max(world.t2Price[line], 1e-9)
            desired = math.floor(desired * min(1.0, max(0.0, (1.0 - r) / cfg['productionMarginBand'])) + 0.5)
            plans[slot] = desired
            for material, ratio in product['ingredients']:
                needs[material] += desired * ratio

        for material in range(NP):
            basic = material < 4
            index = firm * (NE if basic else NP) + material
            raw = world.t2Raw if basic else world.t2T1Raw
            need = max(0.0, needs[material] - raw[index])
            if not need:
                continue
            supplier = suppliers[material]
            if supplier >= 0:
                transfer_tier2_input(world, cfg, firm, material, supplier, need)

        for slot in range(line_count):
            line = int(world.t2FirmLines[firm * M4 + slot])
            product = t2_products[int(world.t2LineProduct[line])]
            output_qty = product['outputQty']
            made = plans[slot]                              # batches
            input_cost = 0.0                                # per batch
            for material, ratio in product['ingredients']:
                basic = material < 4
                index = firm * (NE if basic else NP) + material
                made = min(made, math.floor((world.t2Raw if basic else world.t2T1Raw)[index] / ratio))
                input_cost += ratio * (world.t2RawBasis if basic else world.t2T1Basis)[index]
            conv_per_item = M.conversion_cost(c, cfg)
            conversion_cost = conv_per_item * output_qty
            made = min(made, math.floor(world.t2Cash[firm] / conversion_cost))
            input_cost_per_item = input_cost / output_qty
            if input_cost_per_item + conv_per_item > world.t2Price[line] + 1e-9:
                made = 0
            if made > 0:
                for material, ratio in product['ingredients']:
                    if material < 4:
                        world.t2Raw[firm * NE + material] -= made * ratio
                    else:
                        world.t2T1Raw[firm * NP + material] -= made * ratio
                made_items = made * output_qty
                world.t2Cash[firm] -= made_items * conv_per_item
                world.costSinks += made_items * conv_per_item
                old = world.t2Fin[line]
                unit = input_cost_per_item + conv_per_item
                world.t2FinBasis[line] = (old * world.t2FinBasis[line] + unit * made_items) / (old + made_items)
                world.t2Fin[line] += made_items
                world.t2UnitCost[line] = unit
                world.t2Made[line] = made_items
            previous = world.t2Price[line]
            if world.t2Controller[firm] and math.isfinite(world.t2PlayerPrice[line]):
                world.t2Price[line] = round_to_cent(min(MAX_UNIT_PRICE, max(MIN_UNIT_PRICE, world.t2PlayerPrice[line])))
            else:
                world.t2Price[line] = learned_quote(t2_learning, cfg, line, world.t2Fin[line], tick)
            world.t2RelPriceSum[line] += 1 - min(1.0, max(0.0, world.t2Price[line] - previous)
                                             / max(1e-9, previous * cfg['switchingStableBand']))
            world.t2RelPriceSamples[line] += 1
            world.t2MonthlyCapacity[line] += cfg['t2Capacity'][product['complexity']]


# --------------------------------------------------------------------------
# 8. End-user clearing (atomic retail)
# --------------------------------------------------------------------------
def clear_consumers(world, cfg, products, t2_products, tick):
    offers = market_offers(world, 2, tick)
    procurement_profiles = [
        M.procurement_profile(p, cfg, world.t2ReferenceCost[p['id']] or M.reference_tier2_cost(p))
        for p in t2_products
    ]
    cumulative_offers = []
    for market in offers:
        weights = [0.0] * len(market)
        total = 0.0
        for i, line in enumerate(market):
            total += 1.0
            weights[i] = total
        cumulative_offers.append(weights)

    world.marketPotential.fill(0)
    world.marketActive.fill(0)
    world.marketFulfilled.fill(0)
    world.marketPriceLost.fill(0)
    world.marketStockUnmet.fill(0)
    world.consumerLastMarket.fill(-1)
    world.consumerLastSupplier.fill(-1)
    world.consumerLastQ.fill(0)
    world.consumerLastFulfilled.fill(0)

    orders = 0
    filled_orders = 0
    activated = 0
    consumer_payments = 0.0
    seed = cfg['seed']
    n_t2 = len(t2_products)

    for buyer in range(cfg['consumerCount']):
        if random_(seed, tick, buyer + 2000000) >= cfg['consumerActivation']:
            continue
        activated += 1
        market = int(world.consumerProduct[buyer])
        product = t2_products[market - NP]
        complexity = product['complexity']
        profile = procurement_profiles[product['id']]
        latent_quantity = world.consumerQMax[buyer]
        qmax = math.ceil(latent_quantity)
        rounding = random_(seed, tick, buyer + 7000000)
        potential_quantity = math.floor(latent_quantity) + (1 if rounding < latent_quantity % 1 else 0)
        world.consumerLastMarket[buyer] = market
        if potential_quantity <= 0:
            continue
        world.t2PotentialOrders[market - NP] += 1
        world.marketPotential[market] += potential_quantity
        reference = profile['valuation']
        premium = 1 + cfg['t2ReservationPremium'] * (complexity - 1)
        choke = reference * world.consumerChoke[buyer] * premium
        stock = world.t2Fin
        price = world.t2Price
        reliability = world.t2Rel
        market_offers_list = offers[market - NP]
        preferred = int(world.consumerPreferredSupplier[buyer])
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
        friction = M.loyalty_surcharge(price[preferred], reliability[preferred]) if preferred >= 0 else 0.0
        candidates.sort(key=lambda a: price[a] + (0 if a == preferred else friction))

        def demand(quote):
            continuous = M.demand_at_price(latent_quantity, choke, quote, world.consumerEta[buyer])
            return min(qmax, math.floor(continuous) + (1 if rounding < continuous % 1 else 0))

        # Pre-drain checks, each against the seller's own-price demand.
        cheapest = candidates[0] if candidates else -1
        preferred_can_fulfill = (preferred >= 0 and math.isfinite(price[preferred])
                                 and stock[preferred] >= demand(price[preferred]))
        # The relationship only moves when a single seller fills the entire order
        # (evaluated pre-drain, since the drain depletes stock). A split keeps the incumbent.
        full_filler = cheapest if cheapest >= 0 and stock[cheapest] >= demand(price[cheapest]) else -1

        # Marginal-value demand: buy whole units in price order, stopping when the next
        # unit's marginal value falls below the seller's price. A rogue cheap seller
        # cannot inflate demand — the quantity is pinned to the marginal price.
        bought = 0
        total_desired = 0
        primary = -1
        for candidate in candidates:
            q_at = demand(price[candidate])
            want = max(0, q_at - bought)
            if want <= 0:
                break
            total_desired = q_at
            world.t2Demand[candidate] += want
            world.t2RelAttempts[candidate] += 1
            # Whole-number sale only.
            take = min(want, int(stock[candidate]))
            if take <= 0:
                continue
            if primary < 0:
                primary = candidate
            stock[candidate] -= take
            payment = take * price[candidate]
            consumer_payments += payment
            world.t2Cash[world.t2LineFirm[candidate]] += payment
            world.t2LastSaleTick[world.t2LineFirm[candidate]] = tick
            world.t2Sold[candidate] += take
            world.t2Revenue[candidate] += payment
            world.t2COGS[candidate] += take * world.t2FinBasis[candidate]
            world.t2RelAvailable[candidate] += 1
            bought += take
            if bought >= q_at:
                break
        world.consumerLastMarket[buyer] = market
        world.consumerLastSupplier[buyer] = primary
        world.consumerLastQ[buyer] = total_desired
        world.marketActive[market] += total_desired
        world.marketPriceLost[market] += potential_quantity - total_desired
        if total_desired <= 0:
            continue
        orders += 1
        world.t2Opportunities[market - NP] += 1
        if bought < total_desired:
            world.marketStockUnmet[market] += total_desired - bought
        if bought <= 0:
            continue
        if full_filler >= 0:
            new_incumbent = full_filler
        elif preferred >= 0:
            new_incumbent = preferred
        else:
            new_incumbent = primary
        world.consumerPreferredSupplier[buyer] = new_incumbent
        world.consumerLastFulfilled[buyer] = bought
        if primary != preferred and preferred_can_fulfill:
            charge = M.loyalty_charge(reference, reliability[preferred],
                                     world.lm3)
            world.t2Cash[world.t2LineFirm[preferred]] += charge
            consumer_payments += charge
            world.loyaltySwitches[2] += 1.0
            world.loyaltyPenalties[2] += charge
        world.marketFulfilled[market] += bought
        filled_orders += 1

    return {'orders': orders, 'filledOrders': filled_orders, 'activated': activated,
            'consumerPayments': consumer_payments}


# --------------------------------------------------------------------------
# 9. Observation, reliability, expansion
# --------------------------------------------------------------------------
def update_reliability(world, cfg, tick):
    if tick % MONTH != 0:
        return
    alpha = float(cfg['reliabilityAlpha'])

    def _step(rel, price_sum, price_samples, available, checks, valid):
        samples = price_samples[valid]
        ps = np.where(samples != 0, price_sum[valid] / np.maximum(samples, 1), 1.0)
        chk = checks[valid]
        av = np.where(chk != 0, available[valid] / np.maximum(chk, 1), 1.0)
        score = 0.5 * np.clip(ps, 0.0, 1.0) + 0.5 * np.clip(av, 0.0, 1.0)
        cur = rel[valid]
        rel[valid] = np.clip(cur + alpha * (score - cur), 0.0, 1.0)

    v0 = np.isfinite(world.t0Price)
    _step(world.t0Rel, world.t0RelPriceSum, world.t0RelPriceSamples,
          world.t0RelAvailable, world.t0RelChecks, v0)
    world.t0RelAttempts[v0] = 0
    world.t0RelChecks[v0] = 0
    world.t0RelAvailable[v0] = 0
    world.t0RelPriceSum[v0] = 0
    world.t0RelPriceSamples[v0] = 0

    v1 = world.t1Operates != 0
    _step(world.t1Rel, world.t1RelPriceSum, world.t1RelPriceSamples,
          world.t1RelAvailable, world.t1RelAvailChecks, v1)
    world.t1RelAttempts[v1] = 0
    world.t1RelAvailChecks[v1] = 0
    world.t1RelAvailable[v1] = 0
    world.t1RelPriceSum[v1] = 0
    world.t1RelPriceSamples[v1] = 0


def observe_markets(world, cfg, profiles):
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
            if world.t1Operates[i]:
                opp_weights['t1'][i % NP] += 1
        for i in range(int(world.t2LineCount)):
            opp_weights['t2'][int(world.t2LineProduct[i])] += 1 / world.t2FirmLineCount[world.t2LineFirm[i]]
    else:
        opp_weights = None

    for tier, count in (('t0', N0 * NE), ('t1', N1 * NP), ('t2', int(world.t2LineCount))):
        sales = getattr(world, f'{tier}Sold')
        demand = getattr(world, f'{tier}Demand')
        forecast = getattr(world, f'{tier}DemandEMA')
        actual_sales = getattr(world, f'{tier}SalesEMA')
        revenue = world.t1Revenue if tier == 't1' else getattr(world, f'{tier}Revenue')
        cogs = getattr(world, f'{tier}COGS')
        profits = getattr(world, f'{tier}LearnProfit')
        quantities = getattr(world, f'{tier}LearnSales')
        ages = getattr(world, f'{tier}LearnTicks')
        requests = getattr(world, f'{tier}LearnDemand')
        for i in range(count):
            if (tier == 't0' and not math.isfinite(world.t0Price[i])) or (tier == 't1' and not world.t1Operates[i]):
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
                    market = int(world.t2LineProduct[i])
                if tier == 't0':
                    weight = 1 / len(profiles[i // NE]['elements'])
                elif tier == 't1':
                    weight = 1
                else:
                    weight = 1 / world.t2FirmLineCount[world.t2LineFirm[i]]
                getattr(world, f'{tier}LearnOpportunity')[i] += \
                    getattr(world, f'{tier}Opportunities')[market] * weight / opp_weights[tier][market]
                if tier == 't2':
                    world.t2LearnPotentialOpportunity[i] += world.t2PotentialOrders[market] * weight / opp_weights['t2'][market]
            requests[i] += max(demand[i], sales[i])
            if tier == 't2':
                world.t2MonthSold[i] += sales[i]


def expand_tier2_bots(world, cfg, t2_products, tick):
    if tick % MONTH != 0:
        return
    n = int(world.t2LineCount)
    if n <= 0:
        return
    alpha = float(cfg['reliabilityAlpha'])
    samples = world.t2RelPriceSamples[:n]
    ps = np.where(samples != 0, world.t2RelPriceSum[:n] / np.maximum(samples, 1), 1.0)
    attempts = world.t2RelAttempts[:n]
    av = np.where(attempts != 0, world.t2RelAvailable[:n] / np.maximum(attempts, 1), 1.0)
    score = 0.5 * np.clip(ps, 0.0, 1.0) + 0.5 * np.clip(av, 0.0, 1.0)
    cur = world.t2Rel[:n]
    world.t2Rel[:n] = np.clip(cur + alpha * (score - cur), 0.0, 1.0)
    world.t2RelAttempts[:n] = 0
    world.t2RelAvailable[:n] = 0
    world.t2RelPriceSum[:n] = 0
    world.t2RelPriceSamples[:n] = 0
    # Canon §7: bots do not expand to multi-machine firms (holding-company
    # acquisition is deferred); firms stay single-machine and grow equity only.
    world.t2MonthSold.fill(0)
    world.t2MonthlyCapacity.fill(0)


# --------------------------------------------------------------------------
# Tick orchestrator
# --------------------------------------------------------------------------
def update_loyalty_regime(world, cfg, counts, tick):
    """End-of-tick: fold this tick's observed average order value into the
    per-class EMA every tick; re-derive the loyalty multiples
    ``M = 0.10 × AOV / (unit_cost × 1.5)`` once per year (the charge ≈ 10 % of
    a typical order at reliability 0.5).  Pure scalar math, identical for the
    NumPy and pure-Python paths."""
    alpha = float(cfg['loyaltyEmaAlpha'])
    one_minus = 1.0 - alpha

    # T1 raw buyer: spend = raw revenue, orders = raw purchase events.
    spend = float(np.sum(world.t0Revenue))
    orders = float(np.sum(world.t0Opportunities))
    if orders > 0.0:
        world.aov1 = alpha * (spend / orders) + one_minus * world.aov1

    # T2 material buyer, per complexity.
    for c in range(3):
        if world.t2MatOrders[c] > 0.0:
            world.aov2[c] = alpha * (world.t2MatSpend[c] / world.t2MatOrders[c]) + one_minus * world.aov2[c]

    # T3 consumer: spend = consumer payments, orders = fulfilled orders.
    orders = float(counts.get('filledOrders', 0) or 0)
    if orders > 0.0:
        world.aov3 = alpha * (float(counts.get('consumerPayments', 0) or 0) / orders) + one_minus * world.aov3

    # Re-derive M from the smoothed AOV once per year (piecewise-constant).
    if tick % M.TIME['ticksPerYear'] == 0:
        world.lm1 = 0.10 * world.aov1 / (world.lmUnitCost1 * 1.5)
        world.lm2 = 0.10 * world.aov2 / (world.lmUnitCost2 * 1.5)
        world.lm3 = 0.10 * world.aov3 / (world.lmUnitCost3 * 1.5)


def tick(world: WorldState, cfg, tick, products=None, profiles=None, t2_products=None, state=None):
    products = products if products is not None else M.PRODUCTS
    profiles = profiles if profiles is not None else T0P
    t2_products = t2_products if t2_products is not None else M.T2_PRODUCTS
    state = state if state is not None else {}

    reset_tick(world)
    world.costSinks = 0
    world.equipmentSinks = 0
    update_environment(world, cfg, tick)
    operate_tier0(world, cfg, profiles, tick)

    from . import numba as _numba
    if _numba._HAVE_NUMBA:
        _numba.plan_and_buy_inputs(world, cfg, tick)
    else:
        plan_and_buy_inputs(world, cfg, products, profiles, tick)
    operate_tier1(world, cfg, products)
    price_markets(world, cfg, profiles, products, tick)

    if _numba._HAVE_NUMBA:
        _numba.operate_tier2(world, cfg, tick)
        o, f, a, cp = _numba.clear_consumers(world, cfg, tick)
        counts = {'orders': o, 'filledOrders': f, 'activated': a, 'consumerPayments': cp}
    else:
        operate_tier2(world, cfg, products, profiles, t2_products, tick)
        counts = clear_consumers(world, cfg, products, t2_products, tick)

    if _numba._HAVE_NUMBA:
        _numba.observe_markets(world, cfg, profiles)
    else:
        observe_markets(world, cfg, profiles)
    update_reliability(world, cfg, tick)
    expand_tier2_bots(world, cfg, t2_products, tick)
    update_loyalty_regime(world, cfg, counts, tick)

    state['activatedConsumers'] = counts['activated']
    state['consumerPayments'] = counts['consumerPayments']
    state['costSinks'] = world.costSinks
    state['equipmentSinks'] = world.equipmentSinks
    state['activeOrders'] = counts['orders']
    state['fulfilledOrders'] = counts['filledOrders']
    return state
