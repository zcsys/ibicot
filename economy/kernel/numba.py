"""Numba-accelerated hot loops for the economy kernel.

The pure-Python ``kernel/tick.py`` is the faithful reference (proven
bit-equivalent to the JS oracle).  This module re-implements the three hot
phases — Tier 2 buy/make/price, end-user clearing, and observation — as
``@njit`` functions over flat NumPy arrays, then wraps them so ``tick()`` can
dispatch here when Numba is available.

Bit-exactness is preserved: the 32-bit integer RNG is the same ``uint64``
implementation from ``core.rng``, whole-unit/lot rounding is integer arithmetic,
and Float64 aggregates stay within the declared 1e-9 tolerance.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from ..core import model as M
from ..core.rng import random_ as _rand
from ..kernel.tick import market_offers_table

try:
    from numba import njit as _njit
    _HAVE_NUMBA = True
except Exception:  # pragma: no cover
    _njit = None
    _HAVE_NUMBA = False

NE, NP, N0, N1 = M.NE, M.NP, M.N0, M.N1
M4 = M.T2_MAX_PRODUCTS_PER_FIRM
MIN_UNIT_PRICE = M.MIN_UNIT_PRICE
MAX_UNIT_PRICE = M.MAX_UNIT_PRICE
N_T2 = len(M.T2_PRODUCTS)


# --------------------------------------------------------------------------
# Flat per-product *structural* data (built once at import).  Scale values
# (conversion, machinery, capacity, target) are cfg-driven — see the
# t2_scale_arrays / t1_scale_arrays helpers.
# --------------------------------------------------------------------------
def _build_flat():
    comp, sector, outq, ing_m, ing_q, off = [], [], [], [], [], [0]
    for p in M.T2_PRODUCTS:
        comp.append(int(p['complexity']))
        sector.append(int(p['sectorIndex']))
        outq.append(int(p['outputQty']))
        for m, q in p['ingredients']:
            ing_m.append(int(m))
            ing_q.append(int(q))
        off.append(len(ing_m))
    return (np.array(comp, dtype=np.int64), np.array(sector, dtype=np.int64),
            np.array(outq, dtype=np.int64),
            np.array(ing_m, dtype=np.int64), np.array(ing_q, dtype=np.int64),
            np.array(off, dtype=np.int64))


T2_COMPLEXITY, T2_SECTOR, T2_OUTPUT, T2_ING_M, T2_ING_Q, T2_ING_OFF = _build_flat()
RATIOS = np.array(M.catalog_input_ratios, dtype=np.float64)


def _scale_key(cfg):
    """Hashable signature of the cfg values the per-tick scale arrays depend on."""
    return (
        float(cfg['conversionFactor']),
        float(cfg['t1MaterialCost']),
        float(cfg['t2MaterialCost']),
        float(cfg['storage']),
        tuple(sorted((int(k), float(v)) for k, v in cfg['t2Machinery'].items())),
        tuple(sorted((int(k), float(v)) for k, v in cfg['t2Capacity'].items())),
        tuple(sorted((int(k), float(v)) for k, v in cfg['footprint'].items())),
    )


@lru_cache(maxsize=64)
def _t2_scale_arrays_cached(key):
    conversion_factor, _t1_material, t2_material, storage, t2_machinery, t2_capacity, footprint = key
    t2_machinery = dict(t2_machinery)
    t2_capacity = dict(t2_capacity)
    footprint = dict(footprint)
    conv = np.array([conversion_factor * max(1, int(c) - 1) for c in T2_COMPLEXITY], dtype=np.float64)
    equip = np.array([t2_machinery[int(c)] for c in T2_COMPLEXITY], dtype=np.float64)
    cap = np.array([t2_capacity[int(c)] for c in T2_COMPLEXITY], dtype=np.float64)
    target = np.array([(storage - footprint[int(c)]) / 2.0 for c in T2_COMPLEXITY], dtype=np.float64)
    return conv, equip, cap, target


@lru_cache(maxsize=64)
def _procurement_arrays_cached(key):
    conversion_factor, _t1_material, t2_material, _storage, _t2_machinery, _t2_capacity, _footprint = key
    val = np.empty(N_T2, dtype=np.float64)
    for i, c in enumerate(T2_COMPLEXITY):
        val[i] = t2_material + conversion_factor * max(1, int(c) - 1)
    return val


@lru_cache(maxsize=64)
def _t1_scale_arrays_cached(key):
    _conversion_factor, _t1_material, _t2_material, storage, _t2_machinery, _t2_capacity, footprint = key
    footprint = dict(footprint)
    output = np.array([int(p['outputQty']) for p in M.PRODUCTS], dtype=np.int64)
    target = np.array([(storage - footprint[int(p['complexity'])]) / 2.0 for p in M.PRODUCTS], dtype=np.float64)
    return output, target


def t2_scale_arrays(cfg):
    """cfg-driven conversion, machinery, capacity and fill target per T2 product."""
    return _t2_scale_arrays_cached(_scale_key(cfg))


def procurement_arrays(cfg):
    return _procurement_arrays_cached(_scale_key(cfg))


# Flat Tier 0 profiles and Tier 1 product structure (for the Numba T1 kernel).
from ..core.state import T0P as _T0P  # noqa: E402
_EI = {element: i for i, element in enumerate(M.ELEMENTS)}
PROF_HAS = np.zeros((N0, NE), dtype=np.int8)
PROF_N = np.zeros(N0, dtype=np.int64)
for _s, _prof in enumerate(_T0P):
    PROF_N[_s] = len(_prof['elements'])
    for _e in _prof['element_indices']:
        PROF_HAS[_s, _e] = 1
T1_INPUT_RATIO = np.zeros((NP, NE), dtype=np.float64)
T1_IS_BASIC = np.zeros(NP, dtype=np.int8)
for _pi, _p in enumerate(M.PRODUCTS):
    for _e, _r in _p['inputs'].items():
        T1_INPUT_RATIO[_pi, _EI[_e]] = float(_r)
    T1_IS_BASIC[_pi] = 1 if len(_p['inputs']) == 1 else 0


def t1_scale_arrays(cfg):
    """cfg-driven conversion, machinery, capacity, target and output per T1 product."""
    return _t1_scale_arrays_cached(_scale_key(cfg))


if _HAVE_NUMBA:

    @_njit
    def _loyalty_surcharge(price, reliability):
        r = reliability
        if r < 0.0:
            r = 0.0
        elif r > 1.0:
            r = 1.0
        return 0.05 * price * (1.0 + r) / 1.5

    @_njit
    def _loyalty_charge(unit_cost, reliability, multiple):
        r = reliability
        if r < 0.0:
            r = 0.0
        elif r > 1.0:
            r = 1.0
        return multiple * unit_cost * (1.0 + r)

    @_njit
    def _round_cent(x):
        # Round half away from zero, to whole cents (matches model.round_to_cent).
        if x >= 0.0:
            return math.floor(x * 100.0 + 0.5) / 100.0
        return math.ceil(x * 100.0 - 0.5) / 100.0

    @_njit
    def _adaptive_price(old_price, profit, previous_profit, direction, sales,
                        stock, demand, available, step_scale, pricing_aggressiveness, response):
        floor = MIN_UNIT_PRICE
        price = old_price if old_price > floor else floor
        if price > MAX_UNIT_PRICE:
            price = MAX_UNIT_PRICE
        price = _round_cent(price)
        next_direction = -1 if direction < 0 else 1
        # Derivative-following with a dead band (see model.adaptive_price).
        if sales <= 0:
            if stock <= 0:
                return price, next_direction, step_scale
            next_direction = -1
        elif demand > available + 1e-9:
            next_direction = 1
        elif math.isfinite(previous_profit) and previous_profit > 0:
            change = (profit - previous_profit) / previous_profit
            if change < -0.02:
                next_direction = -next_direction
            elif change > 0.02:
                pass
            else:
                return price, next_direction, step_scale
        kc = pricing_aggressiveness
        if kc > 1.0:
            kc = 1.0
        if kc < 0.0:
            kc = 0.0
        scale = step_scale * (1.0 if next_direction != direction else 1.2)
        if scale < 0.01:
            scale = 0.01
        elif scale > 1.0:
            scale = 1.0
        exp_price = price * math.exp(next_direction * kc * response * scale)
        nxt = exp_price if exp_price > floor else floor
        if nxt > MAX_UNIT_PRICE:
            nxt = MAX_UNIT_PRICE
        nxt = _round_cent(nxt)
        if nxt == price and next_direction < 0:
            next_direction = 1
        return nxt, next_direction, scale

    @_njit
    def _learned_quote(view_tier, price, ages, profits, sales, previous, direction, demand,
                       steps, opportunity, potential_opportunity, index, stock,
                       tick, price_observation_ticks, research_price_min_potential,
                       research_price_max_obs, research_price_min_opp, pricing_aggressiveness, response):
        if ages[index] < price_observation_ticks or (tick + index) % price_observation_ticks != 0:
            return _round_cent(price[index] if price[index] > MIN_UNIT_PRICE else MIN_UNIT_PRICE)
        if view_tier == 2 and research_price_min_potential > 0:
            stale = potential_opportunity[index] >= research_price_min_potential
        else:
            stale = ages[index] >= research_price_max_obs
        enough = research_price_min_opp == 0 or opportunity[index] >= research_price_min_opp or stale
        if enough:
            average = profits[index] / ages[index]
            nxt, d, s = _adaptive_price(price[index], average, previous[index],
                                        direction[index], sales[index], stock, demand[index],
                                        sales[index], steps[index], pricing_aggressiveness, response)
            price[index] = nxt
            direction[index] = d
            previous[index] = average
            steps[index] = s
            profits[index] = 0.0
            sales[index] = 0.0
            demand[index] = 0.0
            ages[index] = 0
            opportunity[index] = 0.0
            potential_opportunity[index] = 0.0
        r = price[index] if price[index] > MIN_UNIT_PRICE else MIN_UNIT_PRICE
        if r > MAX_UNIT_PRICE:
            r = MAX_UNIT_PRICE
        return _round_cent(r)

    @_njit
    def _contains(arr, start, end, val):
        for i in range(start, end):
            if arr[i] == val:
                return True
        return False

    @_njit
    def _choose_supplier_nb(offers_flat, start, end, stock, price, preferred, reliability,
                            best):
        if (preferred >= 0 and stock[preferred] >= 1 and math.isfinite(price[preferred])
                and (best < 0 or price[preferred] <= price[best] + _loyalty_surcharge(price[best], reliability[preferred]))):
            return preferred
        if best >= 0:
            return best
        if start >= end:
            return -1
        empty = offers_flat[start]
        if (preferred >= 0 and _contains(offers_flat, start, end, preferred)
                and price[preferred] <= price[empty] + _loyalty_surcharge(price[empty], reliability[preferred])):
            return preferred
        return empty

    @_njit
    def _demand_at_price(q_max, choke_price, price, elasticity):
        if q_max > 0 and choke_price > 0 and price >= 0 and elasticity > 0:
            return q_max / (1.0 + (price / choke_price) ** elasticity)
        return 0.0

    @_njit
    def _demand_units(latent, choke, quote, eta, qmax, rounding):
        continuous = _demand_at_price(latent, choke, quote, eta)
        d = int(math.floor(continuous))
        if rounding < continuous % 1:
            d += 1
        if d > qmax:
            d = qmax
        return d

    @_njit
    def _sort_candidates(cand, n, price, preferred, friction):
        for i in range(1, n):
            key = cand[i]
            key_eff = price[key] + (0.0 if key == preferred else friction)
            j = i - 1
            while j >= 0:
                cj = cand[j]
                cj_eff = price[cj] + (0.0 if cj == preferred else friction)
                if cj_eff > key_eff:
                    cand[j + 1] = cand[j]
                    j -= 1
                else:
                    break
            cand[j + 1] = key

    @_njit
    def _operate_tier2_nb(
        seed, tick, t2_firm_count, storage,
        t2_conversion, switching_stable_band, t1_unit_cost, loyalty_multiple_t2, price_observation_ticks,
        research_price_min_potential, research_price_max_obs, research_price_min_opp, pricing_aggressiveness, response, margin_band,
        t1_fin, t1_price, t1_rel, t1_cash, t1_sold, t1_rev, t1_cogs, t1_fin_basis,
        t1_intermediate_sold, t1_intermediate_revenue, t1_demand, t1_rel_attempts,
        t1_rel_avail_checks, t1_rel_available, t1_opportunities,
        t2_cash, t2_raw, t2_raw_basis, t2_t1raw, t2_t1basis, t2_preferred,
        t2_firm_lines, t2_firm_line_count, t2_line_product, t2_controller,
        t2_fin, t2_fin_basis, t2_unit_cost, t2_replacement_cost, t2_price, t2_player_price,
        t2_made, t2_demand_ema, t2_sold, t2_revenue, t2_cogs, t2_bought,
        t2_rel_price_sum, t2_rel_price_samples, t2_monthly_capacity,
        t2_learn_ticks, t2_learn_profit, t2_learn_sales, t2_learn_previous,
        t2_learn_direction, t2_learn_demand, t2_learn_step,
        t2_learn_opportunity, t2_learn_potential_opportunity,
        t1_offers_flat, t1_offers_off, valuation, t2_capacity, t2_output, t2_target,
        t2_mat_spend, t2_mat_orders, loyalty_switches, loyalty_penalties):
        needs = np.zeros(NP, dtype=np.float64)
        plans = np.zeros(M4, dtype=np.float64)
        suppliers = np.zeros(NP, dtype=np.int64)
        offer_heads = np.zeros(NP, dtype=np.int64)
        cost_sinks = 0.0

        for order in range(t2_firm_count):
            firm = (order + tick * 137) % t2_firm_count
            for m in range(NP):
                needs[m] = 0.0
            for s in range(M4):
                plans[s] = 0.0
            firm_pid = int(t2_line_product[t2_firm_lines[firm * M4]])
            firm_cx = int(T2_COMPLEXITY[firm_pid]) - 3

            inv_units = 0.0
            for m in range(NP):
                if m < NE:
                    inv_units += t2_raw[firm * NE + m]
                else:
                    inv_units += t2_t1raw[firm * NP + m]
            for s in range(t2_firm_line_count[firm]):
                inv_units += t2_fin[t2_firm_lines[firm * M4 + s]]
            inventory_room = storage - inv_units
            if inventory_room < 0.0:
                inventory_room = 0.0

            for material in range(NP):
                start = t1_offers_off[material]
                end = t1_offers_off[material + 1]
                n_offers = end - start
                h = offer_heads[material]  # relative offset within this market
                while h < n_offers and t1_fin[t1_offers_flat[start + h]] < 1:
                    h += 1
                offer_heads[material] = h
                best = t1_offers_flat[start + h] if h < n_offers else -1
                preferred = t2_preferred[firm * NP + material]
                suppliers[material] = _choose_supplier_nb(
                    t1_offers_flat, start, end, t1_fin, t1_price, preferred, t1_rel,
                    best)

            line_count = t2_firm_line_count[firm]
            for order2 in range(line_count):
                slot = (order2 + tick) % line_count
                line = t2_firm_lines[firm * M4 + slot]
                pid = t2_line_product[line]
                capacity = t2_capacity[pid]
                output_qty = t2_output[pid]
                target = t2_target[pid]
                desired = capacity
                d2 = target - t2_fin[line]
                if d2 < desired:
                    desired = d2
                desired = math.floor(desired / output_qty)
                if desired < 0.0:
                    desired = 0.0
                while desired > 0:
                    missing = 0.0
                    for material in range(NP):
                        ratio = RATIOS[pid, material]
                        if material < NE:
                            held = t2_raw[firm * NE + material]
                        else:
                            held = t2_t1raw[firm * NP + material]
                        missing += max(0.0, needs[material] + desired * ratio - held)
                    if missing <= inventory_room:
                        break
                    desired -= 1
                replacement = t2_conversion[pid]
                current_cost = t2_conversion[pid]
                for gi in range(T2_ING_OFF[pid], T2_ING_OFF[pid + 1]):
                    material = T2_ING_M[gi]
                    ratio = T2_ING_Q[gi]
                    basic = material < 4
                    index = firm * (NE if basic else NP) + material
                    if basic:
                        raw_arr = t2_raw
                        basis_arr = t2_raw_basis
                    else:
                        raw_arr = t2_t1raw
                        basis_arr = t2_t1basis
                    os = t1_offers_off[material]
                    oe = t1_offers_off[material + 1]
                    supplier = suppliers[material] if suppliers[material] >= 0 else (t1_offers_flat[os] if os < oe else -1)
                    quote = t1_price[supplier] if supplier >= 0 else basis_arr[index]
                    current_cost += (ratio / output_qty) * quote
                    stocked = desired * ratio
                    if raw_arr[index] < stocked:
                        stocked = raw_arr[index]
                    if desired > 0:
                        replacement += (stocked * basis_arr[index] + (desired * ratio - stocked) * quote) / (desired * output_qty)
                    else:
                        replacement += (ratio / output_qty) * quote
                t2_replacement_cost[line] = replacement
                if replacement > t2_price[line] + 1e-9:
                    desired = 0.0
                # Elastic input demand (no hard freeze): throttle by the
                # marginal-cost/price ratio — reversed T3 curve: 0 at/above break-even, full at zero cost.
                r = current_cost / max(t2_price[line], 1e-9)
                desired = math.floor(desired * min(1.0, max(0.0, (1.0 - r) / margin_band)) + 0.5)
                plans[slot] = desired
                for gi in range(T2_ING_OFF[pid], T2_ING_OFF[pid + 1]):
                    material = T2_ING_M[gi]
                    ratio = T2_ING_Q[gi]
                    needs[material] += desired * ratio

            for material in range(NP):
                basic = material < 4
                index = firm * (NE if basic else NP) + material
                raw_arr = t2_raw if basic else t2_t1raw
                need = needs[material] - raw_arr[index]
                if need < 0.0:
                    need = 0.0
                if not need:
                    continue
                supplier = suppliers[material]
                if supplier >= 0:
                    is_basic = material < 4
                    raw_x = t2_raw if is_basic else t2_t1raw
                    basis_x = t2_raw_basis if is_basic else t2_t1basis
                    idx = firm * (NE if is_basic else NP) + material
                    inv_units = 0.0
                    for mm in range(NP):
                        if mm < NE:
                            inv_units += t2_raw[firm * NE + mm]
                        else:
                            inv_units += t2_t1raw[firm * NP + mm]
                    for ss in range(t2_firm_line_count[firm]):
                        inv_units += t2_fin[t2_firm_lines[firm * M4 + ss]]
                    room = storage - inv_units
                    if room < 0.0:
                        room = 0.0
                    requested = math.ceil(need)
                    if room < requested:
                        requested = room
                    requested = math.floor(requested)
                    if requested < 0.0:
                        requested = 0.0
                    pref = int(t2_preferred[firm * NP + material])
                    loyalty_charge = 0.0
                    if supplier != pref and pref >= 0 and t1_fin[pref] >= requested:
                        loyalty_charge = _loyalty_charge(t1_unit_cost, t1_rel[pref], loyalty_multiple_t2[firm_cx])
                        if loyalty_charge > t2_cash[firm]:
                            supplier = pref
                            loyalty_charge = 0.0
                    supplier_firm = supplier // NP
                    quote = t1_price[supplier]
                    funded = min(requested, max(0.0, t2_cash[firm] - loyalty_charge) / quote)
                    funded = math.floor(funded)
                    quantity = min(funded, t1_fin[supplier])
                    quantity = math.floor(quantity)
                    t1_demand[supplier] += funded
                    if funded > 0:
                        t1_opportunities[material] += 1
                    t1_rel_attempts[supplier] += 1
                    t1_rel_avail_checks[supplier] += 1
                    if t1_fin[supplier] >= requested:
                        t1_rel_available[supplier] += 1
                    if quantity <= 0:
                        continue
                    old = raw_x[idx]
                    payment = quantity * quote
                    t2_mat_spend[firm_cx] += payment
                    t2_mat_orders[firm_cx] += 1.0
                    basis_x[idx] = (basis_x[idx] * old + payment) / (old + quantity)
                    raw_x[idx] += quantity
                    t2_bought[firm] += quantity
                    t2_cash[firm] -= payment
                    t1_cash[supplier_firm] += payment
                    t1_fin[supplier] -= quantity
                    t1_sold[supplier] += quantity
                    t1_rev[supplier] += payment
                    t1_cogs[supplier] += quantity * t1_fin_basis[supplier]
                    t1_intermediate_sold[material] += quantity
                    t1_intermediate_revenue[material] += payment
                    if loyalty_charge > 0.0:
                        t2_cash[firm] -= loyalty_charge
                        t1_cash[pref // NP] += loyalty_charge
                        loyalty_switches[1] += 1.0
                        loyalty_penalties[1] += loyalty_charge
                    t2_preferred[firm * NP + material] = supplier

            for slot in range(line_count):
                line = t2_firm_lines[firm * M4 + slot]
                pid = t2_line_product[line]
                output_qty = t2_output[pid]
                made = plans[slot]
                input_cost = 0.0
                for gi in range(T2_ING_OFF[pid], T2_ING_OFF[pid + 1]):
                    material = T2_ING_M[gi]
                    ratio = T2_ING_Q[gi]
                    basic = material < 4
                    index = firm * (NE if basic else NP) + material
                    avail = (t2_raw if basic else t2_t1raw)[index] / ratio
                    avail = math.floor(avail)
                    if avail < made:
                        made = avail
                    input_cost += ratio * (t2_raw_basis if basic else t2_t1basis)[index]
                conversion_cost = t2_conversion[pid] * output_qty
                cash_avail = math.floor(t2_cash[firm] / conversion_cost)
                if cash_avail < made:
                    made = cash_avail
                input_cost_per_item = input_cost / output_qty
                conv_per_item = t2_conversion[pid]
                if input_cost_per_item + conv_per_item > t2_price[line] + 1e-9:
                    made = 0.0
                if made > 0:
                    for gi in range(T2_ING_OFF[pid], T2_ING_OFF[pid + 1]):
                        material = T2_ING_M[gi]
                        ratio = T2_ING_Q[gi]
                        if material < 4:
                            t2_raw[firm * NE + material] -= made * ratio
                        else:
                            t2_t1raw[firm * NP + material] -= made * ratio
                    made_items = made * output_qty
                    t2_cash[firm] -= made_items * conv_per_item
                    cost_sinks += made_items * conv_per_item
                    old = t2_fin[line]
                    unit = input_cost_per_item + conv_per_item
                    t2_fin_basis[line] = (old * t2_fin_basis[line] + unit * made_items) / (old + made_items)
                    t2_fin[line] += made_items
                    t2_unit_cost[line] = unit
                    t2_made[line] = made_items
                previous = t2_price[line]
                if t2_controller[firm] and math.isfinite(t2_player_price[line]):
                    nxt = t2_player_price[line]
                    if nxt < MIN_UNIT_PRICE:
                        nxt = MIN_UNIT_PRICE
                    if nxt > MAX_UNIT_PRICE:
                        nxt = MAX_UNIT_PRICE
                    nxt = _round_cent(nxt)
                else:
                    nxt = _learned_quote(2, t2_price, t2_learn_ticks, t2_learn_profit,
                                         t2_learn_sales, t2_learn_previous, t2_learn_direction,
                                         t2_learn_demand, t2_learn_step,
                                         t2_learn_opportunity, t2_learn_potential_opportunity,
                                         line, t2_fin[line], tick, price_observation_ticks,
                                         research_price_min_potential, research_price_max_obs,
                                         research_price_min_opp, pricing_aggressiveness, response)
                t2_price[line] = nxt
                t2_rel_price_sum[line] += 1 - min(1.0, max(0.0, nxt - previous)
                                                  / max(1e-9, previous * switching_stable_band))
                t2_rel_price_samples[line] += 1
                t2_monthly_capacity[line] += t2_capacity[pid]

        return cost_sinks

    @_njit
    def _clear_consumers_nb(
        seed, tick, consumer_count, consumer_activation, consumer_search_offers,
        loyalty_multiple_t3, tier2_reservation_premium, n_t2,
        consumer_product, consumer_preferred_supplier,
        consumer_last_market, consumer_last_supplier, consumer_last_q, consumer_last_fulfilled,
        consumer_qmax, consumer_choke, consumer_eta,
        market_potential, market_active, market_fulfilled, market_price_lost, market_stock_unmet,
        offers_flat, offers_off, t2_firm_line_count, t2_line_firm,
        t2_fin, t2_price, t2_rel, t2_demand, t2_rel_attempts, t2_rel_available,
        t2_cash, t2_last_sale_tick, t2_sold, t2_revenue, t2_cogs, t2_fin_basis,
        t2_opportunities, t2_potential_orders, complexity, valuation,
        loyalty_switches, loyalty_penalties):
        total_lines = offers_off[n_t2]
        cum = np.empty(total_lines, dtype=np.float64)
        for m in range(n_t2):
            start = offers_off[m]
            end = offers_off[m + 1]
            acc = 0.0
            for i in range(start, end):
                line = offers_flat[i]
                acc += 1.0
                cum[i] = acc

        cand = np.empty(1 + consumer_search_offers, dtype=np.int64)
        orders = 0
        filled = 0
        activated = 0
        payments = 0.0

        for buyer in range(consumer_count):
            if _rand(seed, tick, buyer + 2000000) >= consumer_activation:
                continue
            activated += 1
            market = consumer_product[buyer]
            pid = market - NP
            cx = complexity[pid]
            latent = consumer_qmax[buyer]
            qmax = math.ceil(latent)
            rounding = _rand(seed, tick, buyer + 7000000)
            potential = math.floor(latent)
            if rounding < latent % 1:
                potential += 1
            consumer_last_market[buyer] = market
            if potential <= 0:
                continue
            t2_potential_orders[pid] += 1
            market_potential[market] += potential
            reference = valuation[pid]
            premium = 1 + tier2_reservation_premium * (cx - 1)
            choke = reference * consumer_choke[buyer] * premium
            preferred = consumer_preferred_supplier[buyer]
            start = offers_off[pid]
            end = offers_off[pid + 1]
            n_cand = 0
            if preferred >= 0 and math.isfinite(t2_price[preferred]):
                cand[0] = preferred
                n_cand = 1
            for sample in range(consumer_search_offers):
                if start >= end:
                    break
                draw = _rand(seed, tick, buyer + 8000000 + sample * 1100000) * cum[end - 1]
                low = start
                high = end - 1
                while low < high:
                    middle = (low + high) >> 1
                    if draw < cum[middle]:
                        high = middle
                    else:
                        low = middle + 1
                candidate = offers_flat[low]
                if not _contains(cand, 0, n_cand, candidate):
                    cand[n_cand] = candidate
                    n_cand += 1
            if preferred >= 0:
                friction = _loyalty_surcharge(t2_price[preferred], t2_rel[preferred])
            else:
                friction = 0.0
            _sort_candidates(cand, n_cand, t2_price, preferred, friction)
            if n_cand > 0:
                cheapest = cand[0]
            else:
                cheapest = -1
            if preferred >= 0 and math.isfinite(t2_price[preferred]) \
                    and t2_fin[preferred] >= _demand_units(latent, choke, t2_price[preferred], consumer_eta[buyer], qmax, rounding):
                preferred_can_fulfill = True
            else:
                preferred_can_fulfill = False
            if cheapest >= 0 and t2_fin[cheapest] >= _demand_units(latent, choke, t2_price[cheapest], consumer_eta[buyer], qmax, rounding):
                full_filler = cheapest
            else:
                full_filler = -1
            bought = 0
            total_desired = 0
            primary = -1
            for ci in range(n_cand):
                candidate = cand[ci]
                q_at = _demand_units(latent, choke, t2_price[candidate], consumer_eta[buyer], qmax, rounding)
                want = q_at - bought
                if want < 0:
                    want = 0
                if want <= 0:
                    break
                total_desired = q_at
                t2_demand[candidate] += want
                t2_rel_attempts[candidate] += 1
                available = int(math.floor(t2_fin[candidate]))
                take = want if want < available else available
                if take <= 0:
                    continue
                if primary < 0:
                    primary = candidate
                t2_fin[candidate] -= take
                payment = take * t2_price[candidate]
                payments += payment
                t2_cash[t2_line_firm[candidate]] += payment
                t2_last_sale_tick[t2_line_firm[candidate]] = tick
                t2_sold[candidate] += take
                t2_revenue[candidate] += payment
                t2_cogs[candidate] += take * t2_fin_basis[candidate]
                t2_rel_available[candidate] += 1
                bought += take
                if bought >= q_at:
                    break
            consumer_last_market[buyer] = market
            consumer_last_supplier[buyer] = primary
            consumer_last_q[buyer] = total_desired
            market_active[market] += total_desired
            market_price_lost[market] += potential - total_desired
            if total_desired <= 0:
                continue
            orders += 1
            t2_opportunities[pid] += 1
            if bought < total_desired:
                market_stock_unmet[market] += total_desired - bought
            if bought <= 0:
                continue
            if full_filler >= 0:
                new_incumbent = full_filler
            elif preferred >= 0:
                new_incumbent = preferred
            else:
                new_incumbent = primary
            consumer_preferred_supplier[buyer] = new_incumbent
            consumer_last_fulfilled[buyer] = bought
            if primary != preferred and preferred_can_fulfill:
                charge = _loyalty_charge(reference, t2_rel[preferred], loyalty_multiple_t3)
                t2_cash[t2_line_firm[preferred]] += charge
                payments += charge
                loyalty_switches[2] += 1.0
                loyalty_penalties[2] += charge
            market_fulfilled[market] += bought
            filled += 1

        return orders, filled, activated, payments

    @_njit
    def _observe_markets_nb(alpha, t2_line_count,
                            t0_price, t0_demand, t0_sales, t0_demand_ema, t0_sales_ema, t0_revenue, t0_cogs,
                            t0_learn_profit, t0_learn_sales, t0_learn_ticks, t0_learn_demand,
                            t1_operates, t1_demand, t1_sales, t1_demand_ema, t1_sales_ema, t1_rev, t1_cogs,
                            t1_learn_profit, t1_learn_sales, t1_learn_ticks, t1_learn_demand,
                            t2_demand, t2_sales, t2_demand_ema, t2_sales_ema, t2_revenue, t2_cogs,
                            t2_learn_profit, t2_learn_sales, t2_learn_ticks, t2_learn_demand,
                            t2_month_sold):
        for i in range(80):
            if not math.isfinite(t0_price[i]):
                continue
            mx = t0_demand[i] if t0_demand[i] > t0_sales[i] else t0_sales[i]
            t0_demand_ema[i] += alpha * (mx - t0_demand_ema[i])
            t0_sales_ema[i] += alpha * (t0_sales[i] - t0_sales_ema[i])
            t0_learn_profit[i] += t0_revenue[i] - t0_cogs[i]
            t0_learn_sales[i] += t0_sales[i]
            t0_learn_ticks[i] += 1
            t0_learn_demand[i] += mx
        for i in range(10000):
            if not t1_operates[i]:
                continue
            mx = t1_demand[i] if t1_demand[i] > t1_sales[i] else t1_sales[i]
            t1_demand_ema[i] += alpha * (mx - t1_demand_ema[i])
            t1_sales_ema[i] += alpha * (t1_sales[i] - t1_sales_ema[i])
            t1_learn_profit[i] += t1_rev[i] - t1_cogs[i]
            t1_learn_sales[i] += t1_sales[i]
            t1_learn_ticks[i] += 1
            t1_learn_demand[i] += mx
        for i in range(t2_line_count):
            mx = t2_demand[i] if t2_demand[i] > t2_sales[i] else t2_sales[i]
            t2_demand_ema[i] += alpha * (mx - t2_demand_ema[i])
            t2_sales_ema[i] += alpha * (t2_sales[i] - t2_sales_ema[i])
            t2_learn_profit[i] += t2_revenue[i] - t2_cogs[i]
            t2_learn_sales[i] += t2_sales[i]
            t2_learn_ticks[i] += 1
            t2_learn_demand[i] += mx
            t2_month_sold[i] += t2_sales[i]

    @_njit
    def _tier0_supplier_nb(seed, tick, buyer, element, preferred, profile_has, profile_count, t0_price, t0_rel,
                           t0_inv, min_lot):
        eff = np.empty(N0, dtype=np.float64)
        empty_price = 1.7976931348623157e308
        best = 1.7976931348623157e308
        for s in range(N0):
            if profile_has[s, element] == 0:
                eff[s] = float('nan')
                continue
            q = t0_price[s * NE + element]
            if not math.isfinite(q):
                eff[s] = float('nan')
                continue
            fric = 0.0
            if s != preferred:
                r = t0_rel[preferred * NE + element] if preferred >= 0 else 0.5
                if r < 0.0:
                    r = 0.0
                elif r > 1.0:
                    r = 1.0
                fric = 0.05 * q * (1.0 + r) / 1.5
            eff[s] = q + fric
            if eff[s] < empty_price - 1e-12:
                empty_price = eff[s]
            if t0_inv[s * NE + element] >= min_lot and eff[s] < best - 1e-12:
                best = eff[s]
        has_stocked = best < 1.7976931348623157e308
        tied_eff = best if has_stocked else empty_price
        if tied_eff == 1.7976931348623157e308:
            return -1
        total = 0.0
        for s in range(N0):
            if not math.isfinite(eff[s]) or abs(eff[s] - tied_eff) > 1e-12:
                continue
            if has_stocked:
                if t0_inv[s * NE + element] >= min_lot:
                    total += 1.0 / profile_count[s]
            else:
                total += 1.0 / profile_count[s]
        if total == 0.0:
            return -1
        draw = _rand(seed, tick, buyer + 12000000 + element * 1300000) * total
        last = -1
        for s in range(N0):
            if not math.isfinite(eff[s]) or abs(eff[s] - tied_eff) > 1e-12:
                continue
            is_stocked = t0_inv[s * NE + element] >= min_lot
            if (has_stocked and is_stocked) or (not has_stocked):
                last = s
                draw -= 1.0 / profile_count[s]
                if draw < 0.0:
                    return s
        return last

    @_njit
    def _plan_and_buy_inputs_nb(
        seed, tick, min_lot, base_cost, t1_capacity, t1_conversion,
        storage, loyalty_multiple_t1, margin_band,
        t0_price, t0_inv, t0_inv_basis, t0_rel, t0_cash, t0_req, t0_funded_req,
        t0_opportunities, t0_demand, t0_rel_attempts, t0_rel_checks,
        t0_rel_available, t0_sold, t0_revenue, t0_cogs, t0_ful, difficulty,
        t1_cash, t1_fin, t1_fin_basis, t1_price, t1_replacement_cost, t1_operates,
        t1_input_need, t1_purchase_req, t1_last_buy, t1_bought, raw, raw_basis,
        preferred_wholesale, profile_has, profile_count, t1_input_ratio, t1_output, t1_target, t1_is_basic,
        loyalty_switches, loyalty_penalties):
        t0_req[:] = 0.0
        t0_funded_req[:] = 0.0
        first_cohort = tick % NP
        first_firm = (tick * 37) % 100
        for rnd in range(100):
            for cohort_order in range(NP):
                cohort = (first_cohort + cohort_order) % NP
                company = cohort * 100 + ((first_firm + rnd) % 100)
                raw_base = company * NE
                product_base = company * NP
                suppliers = np.empty(NE, dtype=np.int64)
                for element in range(NE):
                    suppliers[element] = _tier0_supplier_nb(
                        seed, tick, company, element, preferred_wholesale[raw_base + element],
                        profile_has, profile_count, t0_price, t0_rel, t0_inv, min_lot)
                for p in range(NP):
                    if t1_operates[product_base + p] == 0:
                        continue
                    cap = t1_capacity
                    output_qty = t1_output[p]
                    target = t1_target[p]
                    desired = cap
                    d2 = target - t1_fin[product_base + p]
                    if d2 < desired:
                        desired = d2
                    if desired < 0.0:
                        desired = 0.0
                    replacement = t1_conversion[p]
                    current_cost = t1_conversion[p]
                    for element in range(NE):
                        ratio = t1_input_ratio[p, element]
                        if ratio == 0.0:
                            continue
                        supplier = suppliers[element]
                        q = t0_price[supplier * NE + element] if supplier >= 0 else t1_last_buy[raw_base + element]
                        current_cost += (ratio / output_qty) * (q if math.isfinite(q) else base_cost * difficulty[element])
                        raw_need = desired * ratio / output_qty
                        stocked = raw_need
                        if raw[raw_base + element] < stocked:
                            stocked = raw[raw_base + element]
                        if desired > 0:
                            qq = q if math.isfinite(q) else base_cost * difficulty[element]
                            replacement += (stocked * raw_basis[raw_base + element] + (raw_need - stocked) * qq) / desired
                        else:
                            replacement += (ratio / output_qty) * (q if math.isfinite(q) else raw_basis[raw_base + element])
                    t1_replacement_cost[product_base + p] = replacement
                    # Elastic input demand (no hard freeze): throttle by the
                    # marginal-cost/price ratio — reversed T3 curve: 0 at/above break-even, full at zero cost.
                    r = current_cost / max(t1_price[product_base + p], 1e-9)
                    desired = math.floor(desired * min(1.0, max(0.0, (1.0 - r) / margin_band)) + 0.5)
                    for element in range(NE):
                        ratio = t1_input_ratio[p, element]
                        if ratio == 0.0:
                            continue
                        need = desired * ratio / output_qty - raw[raw_base + element]
                        if need < 0.0:
                            need = 0.0
                        if need > 0.0:
                            t1_input_need[raw_base + element] += need if need > min_lot else min_lot
                for element in range(NE):
                    need = t1_input_need[raw_base + element]
                    if need <= 0.0:
                        continue
                    request = math.ceil(need / min_lot) * min_lot
                    t1_purchase_req[raw_base + element] = request
                    t0_req[element] += request
                    chosen = suppliers[element]
                    if chosen < 0:
                        continue
                    pref = int(preferred_wholesale[raw_base + element])
                    loyalty_charge = 0.0
                    if chosen != pref and pref >= 0 and t0_inv[pref * NE + element] >= request:
                        loyalty_charge = _loyalty_charge(base_cost, t0_rel[pref * NE + element], loyalty_multiple_t1)
                        if loyalty_charge > t1_cash[company]:
                            chosen = pref
                            loyalty_charge = 0.0
                    supplier_index = chosen * NE + element
                    quote = t0_price[supplier_index]
                    if quote < 0.0:
                        quote = 0.0
                    affordable = math.floor(max(0.0, t1_cash[company] - loyalty_charge) / max(1e-9, quote))
                    available = math.floor(max(0.0, t0_inv[supplier_index]))
                    held = 0.0
                    for material in range(NE):
                        held += raw[raw_base + material]
                    for output in range(NP):
                        held += t1_fin[product_base + output]
                    storage_room = math.floor(max(0.0, storage - held) / min_lot) * min_lot
                    funded = min(request, affordable, storage_room)
                    funded = math.floor(funded / min_lot) * min_lot
                    t0_funded_req[element] += funded
                    if funded > 0:
                        t0_opportunities[element] += 1
                    t0_demand[supplier_index] += funded
                    bought = min(funded, available)
                    bought = math.floor(bought / min_lot) * min_lot
                    attempt = 1 if request > 0 else 0
                    t0_rel_attempts[supplier_index] += attempt
                    t0_rel_checks[supplier_index] += attempt
                    t0_rel_available[supplier_index] += attempt if available >= request else 0
                    if bought <= 0:
                        continue
                    old_raw = raw[raw_base + element]
                    old_basis = raw_basis[raw_base + element]
                    payment = bought * quote
                    raw[raw_base + element] = old_raw + bought
                    t1_bought[company] += bought
                    raw_basis[raw_base + element] = (old_basis * old_raw + payment) / (old_raw + bought) if old_raw + bought > 0 else 0.0
                    t1_last_buy[raw_base + element] = quote
                    t1_cash[company] -= payment
                    t0_cash[chosen] += payment
                    t0_inv[supplier_index] -= bought
                    t0_sold[supplier_index] += bought
                    t0_revenue[supplier_index] += payment
                    t0_cogs[supplier_index] += bought * t0_inv_basis[supplier_index]
                    t0_ful[element] += bought
                    if loyalty_charge > 0.0:
                        t1_cash[company] -= loyalty_charge
                        t0_cash[pref] += loyalty_charge
                        loyalty_switches[0] += 1.0
                        loyalty_penalties[0] += loyalty_charge
                    preferred_wholesale[raw_base + element] = chosen

# --------------------------------------------------------------------------
# Python wrappers (flatten + dispatch).
# --------------------------------------------------------------------------
def observe_markets(world, cfg, profiles):
    if cfg['researchPriceMinimumOpportunities'] > 0:
        # Research candidate only (off by default) — fall back to the faithful
        # pure-Python path which computes the opportunity weights.
        from ..kernel.tick import observe_markets as _pure
        return _pure(world, cfg, profiles)
    _observe_markets_nb(
        float(cfg['alpha']), int(world.t2LineCount),
        world.t0Price, world.t0Demand, world.t0Sold, world.t0DemandEMA, world.t0SalesEMA, world.t0Revenue, world.t0COGS,
        world.t0LearnProfit, world.t0LearnSales, world.t0LearnTicks, world.t0LearnDemand,
        world.t1Operates, world.t1Demand, world.t1Sold, world.t1DemandEMA, world.t1SalesEMA, world.t1Revenue, world.t1COGS,
        world.t1LearnProfit, world.t1LearnSales, world.t1LearnTicks, world.t1LearnDemand,
        world.t2Demand, world.t2Sold, world.t2DemandEMA, world.t2SalesEMA, world.t2Revenue, world.t2COGS,
        world.t2LearnProfit, world.t2LearnSales, world.t2LearnTicks, world.t2LearnDemand,
        world.t2MonthSold)


def plan_and_buy_inputs(world, cfg, tick):
    t1_output, t1_target = t1_scale_arrays(cfg)
    t1_conv = np.array([M.conversion_cost(p['complexity'], cfg) for p in M.PRODUCTS], dtype=np.float64)
    _plan_and_buy_inputs_nb(
        cfg['seed'], tick, cfg['minWholesaleLot'],
        cfg['baseCost'], cfg['t1Capacity'], t1_conv,
        float(cfg['storage']), float(world.lm1), float(cfg['productionMarginBand']),
        world.t0Price, world.t0Inv, world.t0InvBasis, world.t0Rel, world.t0Cash, world.t0Req, world.t0FundedReq,
        world.t0Opportunities, world.t0Demand, world.t0RelAttempts, world.t0RelChecks,
        world.t0RelAvailable, world.t0Sold, world.t0Revenue, world.t0COGS, world.t0Fulfilled, world.difficulty,
        world.t1Cash, world.t1Fin, world.t1FinBasis, world.t1Price, world.t1ReplacementCost, world.t1Operates,
        world.t1InputNeed, world.t1PurchaseReq, world.t1LastBuy, world.t1Bought, world.raw, world.rawBasis,
        world.preferredWholesale, PROF_HAS, PROF_N, T1_INPUT_RATIO, t1_output, t1_target, T1_IS_BASIC,
        world.loyaltySwitches, world.loyaltyPenalties)


def operate_tier2(world, cfg, tick):
    flat, off = market_offers_table(world, 1, tick)
    val = procurement_arrays(cfg)
    t2_conv, _, t2_cap, t2_target = t2_scale_arrays(cfg)
    t1_unit_cost = cfg['t1MaterialCost'] + cfg['conversionFactor']
    cs = _operate_tier2_nb(
        cfg['seed'], tick, cfg['t2FirmCount'], float(cfg['storage']),
        t2_conv, float(cfg['switchingStableBand']),
        t1_unit_cost, world.lm2, cfg['priceObservationTicks'],
        cfg['researchPriceMinimumPotentialOrders'], cfg['researchPriceMaxObservationTicks'],
        cfg['researchPriceMinimumOpportunities'], float(cfg['pricingAggressiveness']), float(cfg['wholesalePriceResponse']),
        float(cfg['productionMarginBand']),
        world.t1Fin, world.t1Price, world.t1Rel, world.t1Cash, world.t1Sold, world.t1Revenue, world.t1COGS, world.t1FinBasis,
        world.t1IntermediateSold, world.t1IntermediateRevenue, world.t1Demand, world.t1RelAttempts,
        world.t1RelAvailChecks, world.t1RelAvailable, world.t1Opportunities,
        world.t2Cash, world.t2Raw, world.t2RawBasis, world.t2T1Raw, world.t2T1Basis, world.t2Preferred,
        world.t2FirmLines, world.t2FirmLineCount, world.t2LineProduct, world.t2Controller,
        world.t2Fin, world.t2FinBasis, world.t2UnitCost, world.t2ReplacementCost, world.t2Price, world.t2PlayerPrice,
        world.t2Made, world.t2DemandEMA, world.t2Sold, world.t2Revenue, world.t2COGS, world.t2Bought,
        world.t2RelPriceSum, world.t2RelPriceSamples, world.t2MonthlyCapacity,
        world.t2LearnTicks, world.t2LearnProfit, world.t2LearnSales, world.t2LearnPrevious,
        world.t2LearnDirection, world.t2LearnDemand, world.t2LearnStep,
        world.t2LearnOpportunity, world.t2LearnPotentialOpportunity,
        flat, off, val, t2_cap, T2_OUTPUT, t2_target,
        world.t2MatSpend, world.t2MatOrders, world.loyaltySwitches, world.loyaltyPenalties)
    world.costSinks += cs
    return cs


def clear_consumers(world, cfg, tick):
    flat, off = market_offers_table(world, 2, tick)
    val = procurement_arrays(cfg)
    # Per-tick demand-ledger reset (mirrors the top of clearEndUsers in JS).
    world.marketPotential.fill(0)
    world.marketActive.fill(0)
    world.marketFulfilled.fill(0)
    world.marketPriceLost.fill(0)
    world.marketStockUnmet.fill(0)
    world.consumerLastMarket.fill(-1)
    world.consumerLastSupplier.fill(-1)
    world.consumerLastQ.fill(0)
    world.consumerLastFulfilled.fill(0)
    return _clear_consumers_nb(
        cfg['seed'], tick, cfg['consumerCount'],
        float(cfg['consumerActivation']), cfg['consumerSearchOffers'], float(world.lm3),
        float(cfg['t2ReservationPremium']), N_T2,
        world.consumerProduct, world.consumerPreferredSupplier,
        world.consumerLastMarket, world.consumerLastSupplier, world.consumerLastQ, world.consumerLastFulfilled,
        world.consumerQMax, world.consumerChoke, world.consumerEta,
        world.marketPotential, world.marketActive, world.marketFulfilled, world.marketPriceLost, world.marketStockUnmet,
        flat, off, world.t2FirmLineCount, world.t2LineFirm,
        world.t2Fin, world.t2Price, world.t2Rel, world.t2Demand, world.t2RelAttempts, world.t2RelAvailable,
        world.t2Cash, world.t2LastSaleTick, world.t2Sold, world.t2Revenue, world.t2COGS, world.t2FinBasis,
        world.t2Opportunities, world.t2PotentialOrders, T2_COMPLEXITY, val,
        world.loyaltySwitches, world.loyaltyPenalties)
