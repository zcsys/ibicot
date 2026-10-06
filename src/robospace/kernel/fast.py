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

import numpy as np

from ..core import model as M
from ..core.rng import random_ as _rand
from ..kernel.tick import market_offers as _market_offers

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
RATIOS = np.array(M.catalogue_input_ratios, dtype=np.float64)


def t2_scale_arrays(cfg):
    """cfg-driven conversion, machinery, capacity and fill target per T2 product."""
    conv = np.array([M.conversion_cost(int(c), cfg) for c in T2_COMPLEXITY], dtype=np.float64)
    equip = np.array([cfg['t2Machinery'][int(c)] for c in T2_COMPLEXITY], dtype=np.float64)
    cap = np.array([cfg['t2Capacity'][int(c)] for c in T2_COMPLEXITY], dtype=np.float64)
    target = np.array([M.inventory_target(int(c), cfg) for c in T2_COMPLEXITY], dtype=np.float64)
    return conv, equip, cap, target


def procurement_arrays(cfg):
    qf = np.empty(N_T2, dtype=np.float64)
    val = np.empty(N_T2, dtype=np.float64)
    for i, p in enumerate(M.T2_PRODUCTS):
        prof = M.procurement_profile(p, cfg, M.reference_tier2_cost(p, cfg))
        qf[i] = prof['quantityFactor']
        val[i] = prof['valuation']
    return qf, val


# Flat Tier 0 profiles and Tier 1 product structure (for the Numba T1 kernel).
from ..core.state import T0P as _T0P  # noqa: E402
_EI = {e: i for i, e in enumerate(M.ELEMENTS)}
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
    output = np.array([int(p['outputQty']) for p in M.PRODUCTS], dtype=np.int64)
    target = np.array([M.inventory_target(p['complexity'], cfg) for p in M.PRODUCTS], dtype=np.float64)
    return output, target


def _flatten(offers):
    flat = []
    off = [0]
    for market in offers:
        flat.extend(market)
        off.append(len(flat))
    return np.array(flat, dtype=np.int64), np.array(off, dtype=np.int64)


if _HAVE_NUMBA:

    @_njit
    def _switching_cost(reliability, minimum, maximum):
        r = reliability
        if r < 0.0:
            r = 0.0
        elif r > 1.0:
            r = 1.0
        return minimum + (maximum - minimum) * r

    @_njit
    def _adaptive_price(old_price, profit, previous_profit, direction, sales,
                        stock, demand, available, step_scale, k, response):
        floor = MIN_UNIT_PRICE
        price = old_price if old_price > floor else floor
        if price > MAX_UNIT_PRICE:
            price = MAX_UNIT_PRICE
        next_direction = -1 if direction < 0 else 1
        if demand > available + 1e-9:
            next_direction = 1
        elif sales <= 0:
            if stock <= 0:
                return price, next_direction, step_scale
            next_direction = -1
        elif math.isfinite(previous_profit) and profit < previous_profit:
            next_direction = -next_direction
        kc = k
        if kc > 1.0:
            kc = 1.0
        if kc < 0.0:
            kc = 0.0
        scale = step_scale * (0.5 if next_direction != direction else 1.2)
        if scale < 0.01:
            scale = 0.01
        elif scale > 1.0:
            scale = 1.0
        e = price * math.exp(next_direction * kc * response * scale)
        nxt = e if e > floor else floor
        if nxt > MAX_UNIT_PRICE:
            nxt = MAX_UNIT_PRICE
        if nxt == price and next_direction < 0:
            next_direction = 1
        return nxt, next_direction, scale

    @_njit
    def _learned_quote(view_tier, price, ages, profits, sales, previous, direction, demand,
                       stocks, steps, opportunity, potential_opportunity, index, stock,
                       tick, price_observation_ticks, research_price_min_potential,
                       research_price_max_obs, research_price_min_opp, k, response):
        if ages[index] < price_observation_ticks or (tick + index) % price_observation_ticks != 0:
            return price[index] if price[index] > MIN_UNIT_PRICE else MIN_UNIT_PRICE
        if view_tier == 2 and research_price_min_potential > 0:
            stale = potential_opportunity[index] >= research_price_min_potential
        else:
            stale = ages[index] >= research_price_max_obs
        enough = research_price_min_opp == 0 or opportunity[index] >= research_price_min_opp or stale
        if enough:
            average = profits[index] / ages[index]
            nxt, d, s = _adaptive_price(price[index], average, previous[index],
                                        direction[index], sales[index], stock, demand[index],
                                        sales[index] + stocks[index], steps[index], k, response)
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
        return MAX_UNIT_PRICE if r > MAX_UNIT_PRICE else r

    @_njit
    def _contains(arr, start, end, val):
        for i in range(start, end):
            if arr[i] == val:
                return True
        return False

    @_njit
    def _choose_supplier_nb(offers_flat, start, end, stock, price, preferred, reliability,
                            taumin, taumax, best):
        if (preferred >= 0 and stock[preferred] >= 1 and math.isfinite(price[preferred])
                and (best < 0 or price[preferred] <= price[best] + _switching_cost(reliability[preferred], taumin, taumax))):
            return preferred
        if best >= 0:
            return best
        if start >= end:
            return -1
        empty = offers_flat[start]
        if (preferred >= 0 and _contains(offers_flat, start, end, preferred)
                and price[preferred] <= price[empty] + _switching_cost(reliability[preferred], taumin, taumax)):
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
    def _tier2_buy_make_price_nb(
        seed, tick, t2_firm_count, storage,
        t2_conversion, switching_stable_band, taumin, taumax, price_observation_ticks,
        research_price_min_potential, research_price_max_obs, research_price_min_opp, k, response,
        t1_fin, t1_price, t1_rel, t1_cash, t1_sold, t1_rev, t1_cogs, t1_fin_basis,
        t1_intermediate_sold, t1_intermediate_revenue, t1_demand, t1_rel_attempts,
        t1_rel_fulfilled, t1_rel_avail_checks, t1_rel_available, t1_opportunities,
        t2_cash, t2_raw, t2_raw_basis, t2_t1raw, t2_t1basis, t2_preferred,
        t2_firm_lines, t2_firm_line_count, t2_line_product, t2_controller,
        t2_fin, t2_fin_basis, t2_unit_cost, t2_replacement_cost, t2_price, t2_player_price,
        t2_made, t2_demand_ema, t2_sold, t2_revenue, t2_cogs, t2_bought,
        t2_rel_price_sum, t2_rel_price_samples, t2_monthly_capacity,
        t2_learn_ticks, t2_learn_profit, t2_learn_sales, t2_learn_previous,
        t2_learn_direction, t2_learn_demand, t2_learn_stock, t2_learn_step,
        t2_learn_opportunity, t2_learn_potential_opportunity,
        t1_offers_flat, t1_offers_off, qty_factor, valuation, t2_capacity, t2_output, t2_target):
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
                    taumin, taumax, best)

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
                    supplier_firm = supplier // NP
                    quote = t1_price[supplier]
                    u = 0.0
                    for mm in range(NP):
                        if mm < NE:
                            u += t2_raw[firm * NE + mm]
                        else:
                            u += t2_t1raw[firm * NP + mm]
                    for ss in range(t2_firm_line_count[firm]):
                        u += t2_fin[t2_firm_lines[firm * M4 + ss]]
                    room = storage - u
                    if room < 0.0:
                        room = 0.0
                    requested = math.ceil(need)
                    if room < requested:
                        requested = room
                    requested = math.floor(requested)
                    if requested < 0.0:
                        requested = 0.0
                    funded = min(requested, t2_cash[firm] / quote)
                    funded = math.floor(funded)
                    quantity = min(funded, t1_fin[supplier])
                    quantity = math.floor(quantity)
                    t1_demand[supplier] += funded
                    if funded > 0:
                        t1_opportunities[material] += 1
                    t1_rel_attempts[supplier] += 1
                    t1_rel_avail_checks[supplier] += 1
                    if quantity >= requested:
                        t1_rel_fulfilled[supplier] += 1
                    if t1_fin[supplier] >= requested:
                        t1_rel_available[supplier] += 1
                    if quantity <= 0:
                        continue
                    old = raw_x[idx]
                    payment = quantity * quote
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
                else:
                    nxt = _learned_quote(2, t2_price, t2_learn_ticks, t2_learn_profit,
                                         t2_learn_sales, t2_learn_previous, t2_learn_direction,
                                         t2_learn_demand, t2_learn_stock, t2_learn_step,
                                         t2_learn_opportunity, t2_learn_potential_opportunity,
                                         line, t2_fin[line], tick, price_observation_ticks,
                                         research_price_min_potential, research_price_max_obs,
                                         research_price_min_opp, k, response)
                t2_price[line] = nxt
                t2_rel_price_sum[line] += 1 - min(1.0, abs(nxt - previous)
                                                  / max(1e-9, previous * switching_stable_band))
                t2_rel_price_samples[line] += 1
                t2_monthly_capacity[line] += t2_capacity[pid]

        return cost_sinks

    @_njit
    def _clear_end_users_nb(
        seed, tick, end_user_count, consumer_activation, consumer_search_offers, taumin, taumax,
        tier2_reservation_premium, n_t2,
        end_basket_count, end_basket, end_need_product, end_preferred_product, end_preferred_supplier,
        end_last_market, end_last_supplier, end_last_q, end_last_fulfilled,
        end_qmax, end_choke, end_eta,
        end_potential, end_active, end_fulfilled, end_price_lost, end_stock_unmet,
        t2_sector_count, t2_sector_products, t2_sector_product_weight,
        offers_flat, offers_off, t2_firm_line_count, t2_line_firm,
        t2_fin, t2_price, t2_rel, t2_demand, t2_rel_attempts, t2_rel_fulfilled, t2_rel_available,
        t2_cash, t2_last_sale_tick, t2_sold, t2_revenue, t2_cogs, t2_fin_basis,
        t2_opportunities, t2_potential_orders, complexity, qty_factor, valuation):
        total_lines = offers_off[n_t2]
        cum = np.empty(total_lines, dtype=np.float64)
        for m in range(n_t2):
            start = offers_off[m]
            end = offers_off[m + 1]
            acc = 0.0
            for i in range(start, end):
                line = offers_flat[i]
                acc += 1.0 / t2_firm_line_count[t2_line_firm[line]]
                cum[i] = acc

        cand = np.empty(1 + consumer_search_offers, dtype=np.int64)
        orders = 0
        filled = 0
        activated = 0
        payments = 0.0

        for buyer in range(end_user_count):
            if _rand(seed, tick, buyer + 2000000) >= consumer_activation:
                continue
            activated += 1
            if _rand(seed, tick, buyer + 3000000) < 0.60:
                slot = 0
            else:
                slot = 1 + int(math.floor(_rand(seed, tick, buyer + 3100000) * (end_basket_count[buyer] - 1)))
            relationship = buyer * 5 + slot
            sector = end_basket[relationship]
            previous = end_need_product[relationship]
            if previous >= NP and _rand(seed, tick, buyer + 5100000) < 0.65:
                market = previous
            else:
                base = sector * n_t2
                count = t2_sector_count[sector]
                draw = _rand(seed, tick, buyer + 6000000) * t2_sector_product_weight[base + count - 1]
                offset = 0
                while offset < count - 1 and draw >= t2_sector_product_weight[base + offset]:
                    offset += 1
                market = NP + t2_sector_products[sector * n_t2 + offset]
            end_need_product[relationship] = market
            pid = market - NP
            cx = complexity[pid]
            latent = end_qmax[buyer] * qty_factor[pid]
            qmax = math.ceil(latent)
            rounding = _rand(seed, tick, buyer + 7000000)
            potential = math.floor(latent)
            if rounding < latent % 1:
                potential += 1
            end_last_market[buyer] = market
            if potential <= 0:
                continue
            t2_potential_orders[pid] += 1
            end_potential[market] += potential
            reference = valuation[pid]
            premium = 1 + tier2_reservation_premium * (cx - 1)
            choke = reference * end_choke[buyer] * premium
            if end_preferred_product[relationship] == market:
                preferred = end_preferred_supplier[relationship]
            else:
                preferred = -1
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
                friction = _switching_cost(t2_rel[preferred], taumin, taumax)
            else:
                friction = 0.0
            _sort_candidates(cand, n_cand, t2_price, preferred, friction)
            seller = cand[0] if n_cand > 0 else -1
            if seller < 0:
                desired = _demand_units(latent, choke, reference, end_eta[buyer], qmax, rounding)
            else:
                desired = _demand_units(latent, choke, t2_price[seller], end_eta[buyer], qmax, rounding)
            for ci in range(n_cand):
                candidate = cand[ci]
                requested = _demand_units(latent, choke, t2_price[candidate], end_eta[buyer], qmax, rounding)
                if requested <= 0:
                    break
                t2_demand[candidate] += requested
                t2_rel_attempts[candidate] += 1
                if t2_fin[candidate] >= requested:
                    seller = candidate
                    desired = requested
                    break
            end_last_market[buyer] = market
            end_last_supplier[buyer] = seller
            end_last_q[buyer] = desired
            end_active[market] += desired
            end_price_lost[market] += potential - desired
            if desired <= 0:
                continue
            orders += 1
            t2_opportunities[pid] += 1
            if seller < 0 or t2_fin[seller] < desired:
                end_stock_unmet[market] += desired
                continue
            payment = desired * t2_price[seller]
            payments += payment
            t2_fin[seller] -= desired
            t2_cash[t2_line_firm[seller]] += payment
            t2_last_sale_tick[t2_line_firm[seller]] = tick
            t2_sold[seller] += desired
            t2_revenue[seller] += payment
            t2_cogs[seller] += desired * t2_fin_basis[seller]
            t2_rel_fulfilled[seller] += 1
            t2_rel_available[seller] += 1
            end_preferred_product[relationship] = market
            end_preferred_supplier[relationship] = seller
            end_last_fulfilled[buyer] = desired
            end_fulfilled[market] += desired
            filled += 1

        return orders, filled, activated, payments

    @_njit
    def _observe_markets_nb(alpha, t2_line_count,
                            t0_price, t0_demand, t0_sales, t0_demand_ema, t0_sales_ema, t0_revenue, t0_cogs,
                            t0_learn_profit, t0_learn_sales, t0_learn_ticks, t0_learn_demand, t0_learn_stock, t0_inv,
                            t1_operates, t1_demand, t1_sales, t1_demand_ema, t1_sales_ema, t1_rev, t1_cogs,
                            t1_learn_profit, t1_learn_sales, t1_learn_ticks, t1_learn_demand, t1_learn_stock, t1_fin,
                            t2_demand, t2_sales, t2_demand_ema, t2_sales_ema, t2_revenue, t2_cogs,
                            t2_learn_profit, t2_learn_sales, t2_learn_ticks, t2_learn_demand, t2_learn_stock, t2_fin,
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
            t0_learn_stock[i] = t0_inv[i]
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
            t1_learn_stock[i] = t1_fin[i]
        for i in range(t2_line_count):
            mx = t2_demand[i] if t2_demand[i] > t2_sales[i] else t2_sales[i]
            t2_demand_ema[i] += alpha * (mx - t2_demand_ema[i])
            t2_sales_ema[i] += alpha * (t2_sales[i] - t2_sales_ema[i])
            t2_learn_profit[i] += t2_revenue[i] - t2_cogs[i]
            t2_learn_sales[i] += t2_sales[i]
            t2_learn_ticks[i] += 1
            t2_learn_demand[i] += mx
            t2_learn_stock[i] = t2_fin[i]
            t2_month_sold[i] += t2_sales[i]

    @_njit
    def _tier0_supplier_nb(seed, tick, buyer, e, preferred, prof_has, prof_n, t0_price, t0_rel,
                           t0_inv, min_lot, taumin, taumax):
        eff = np.empty(N0, dtype=np.float64)
        empty_price = 1.7976931348623157e308
        best = 1.7976931348623157e308
        for s in range(N0):
            if prof_has[s, e] == 0:
                eff[s] = float('nan')
                continue
            q = t0_price[s * NE + e]
            if not math.isfinite(q):
                eff[s] = float('nan')
                continue
            fric = 0.0
            if s != preferred:
                r = t0_rel[preferred * NE + e] if preferred >= 0 else 0.5
                if r < 0.0:
                    r = 0.0
                elif r > 1.0:
                    r = 1.0
                fric = taumin + (taumax - taumin) * r
            eff[s] = q + fric
            if eff[s] < empty_price - 1e-12:
                empty_price = eff[s]
            if t0_inv[s * NE + e] >= min_lot and eff[s] < best - 1e-12:
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
                if t0_inv[s * NE + e] >= min_lot:
                    total += 1.0 / prof_n[s]
            else:
                total += 1.0 / prof_n[s]
        if total == 0.0:
            return -1
        draw = _rand(seed, tick, buyer + 12000000 + e * 1300000) * total
        last = -1
        for s in range(N0):
            if not math.isfinite(eff[s]) or abs(eff[s] - tied_eff) > 1e-12:
                continue
            is_stocked = t0_inv[s * NE + e] >= min_lot
            if (has_stocked and is_stocked) or (not has_stocked):
                last = s
                draw -= 1.0 / prof_n[s]
                if draw < 0.0:
                    return s
        return last

    @_njit
    def _plan_and_buy_inputs_nb(
        seed, tick, min_lot, base_cost, t1_capacity, t1_conversion,
        storage, taumin, taumax,
        t0_price, t0_inv, t0_inv_basis, t0_rel, t0_cash, t0_req, t0_funded_req,
        t0_opportunities, t0_demand, t0_rel_attempts, t0_rel_fulfilled, t0_rel_checks,
        t0_rel_available, t0_sold, t0_revenue, t0_cogs, t0_ful, difficulty,
        t1_cash, t1_fin, t1_fin_basis, t1_price, t1_replacement_cost, t1_operates,
        t1_input_need, t1_purchase_req, t1_last_buy, t1_bought, raw, raw_basis,
        preferred_wholesale, prof_has, prof_n, t1_input_ratio, t1_output, t1_target, t1_is_basic):
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
                for e in range(NE):
                    suppliers[e] = _tier0_supplier_nb(
                        seed, tick, company, e, preferred_wholesale[raw_base + e],
                        prof_has, prof_n, t0_price, t0_rel, t0_inv, min_lot, taumin, taumax)
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
                    for e in range(NE):
                        ratio = t1_input_ratio[p, e]
                        if ratio == 0.0:
                            continue
                        supplier = suppliers[e]
                        q = t0_price[supplier * NE + e] if supplier >= 0 else t1_last_buy[raw_base + e]
                        raw_need = desired * ratio / output_qty
                        stocked = raw_need
                        if raw[raw_base + e] < stocked:
                            stocked = raw[raw_base + e]
                        if desired > 0:
                            qq = q if math.isfinite(q) else base_cost * difficulty[e]
                            replacement += (stocked * raw_basis[raw_base + e] + (raw_need - stocked) * qq) / desired
                        else:
                            replacement += (ratio / output_qty) * (q if math.isfinite(q) else raw_basis[raw_base + e])
                    t1_replacement_cost[product_base + p] = replacement
                    if desired > 0 and replacement > t1_price[product_base + p] + 1e-9:
                        continue
                    for e in range(NE):
                        ratio = t1_input_ratio[p, e]
                        if ratio == 0.0:
                            continue
                        need = desired * ratio / output_qty - raw[raw_base + e]
                        if need < 0.0:
                            need = 0.0
                        if need > 0.0:
                            t1_input_need[raw_base + e] += need if need > min_lot else min_lot
                for e in range(NE):
                    need = t1_input_need[raw_base + e]
                    if need <= 0.0:
                        continue
                    request = math.ceil(need / min_lot) * min_lot
                    t1_purchase_req[raw_base + e] = request
                    t0_req[e] += request
                    chosen = suppliers[e]
                    if chosen < 0:
                        continue
                    supplier_index = chosen * NE + e
                    quote = t0_price[supplier_index]
                    if quote < 0.0:
                        quote = 0.0
                    affordable = math.floor(max(0.0, t1_cash[company]) / max(1e-9, quote))
                    available = math.floor(max(0.0, t0_inv[supplier_index]))
                    held = 0.0
                    for material in range(NE):
                        held += raw[raw_base + material]
                    for output in range(NP):
                        held += t1_fin[product_base + output]
                    storage_room = math.floor(max(0.0, storage - held) / min_lot) * min_lot
                    funded = min(request, affordable, storage_room)
                    funded = math.floor(funded / min_lot) * min_lot
                    t0_funded_req[e] += funded
                    if funded > 0:
                        t0_opportunities[e] += 1
                    t0_demand[supplier_index] += funded
                    bought = min(funded, available)
                    bought = math.floor(bought / min_lot) * min_lot
                    attempt = 1 if request > 0 else 0
                    t0_rel_attempts[supplier_index] += attempt
                    t0_rel_fulfilled[supplier_index] += attempt if bought >= request else 0
                    t0_rel_checks[supplier_index] += attempt
                    t0_rel_available[supplier_index] += attempt if available >= request else 0
                    if bought <= 0:
                        continue
                    old_raw = raw[raw_base + e]
                    old_basis = raw_basis[raw_base + e]
                    payment = bought * quote
                    raw[raw_base + e] = old_raw + bought
                    t1_bought[company] += bought
                    raw_basis[raw_base + e] = (old_basis * old_raw + payment) / (old_raw + bought) if old_raw + bought > 0 else 0.0
                    t1_last_buy[raw_base + e] = quote
                    t1_cash[company] -= payment
                    t0_cash[chosen] += payment
                    t0_inv[supplier_index] -= bought
                    t0_sold[supplier_index] += bought
                    t0_revenue[supplier_index] += payment
                    t0_cogs[supplier_index] += bought * t0_inv_basis[supplier_index]
                    t0_ful[e] += bought
                    preferred_wholesale[raw_base + e] = chosen

# --------------------------------------------------------------------------
# Python wrappers (flatten + dispatch).
# --------------------------------------------------------------------------
def observe_markets_fast(W, cfg, profiles):
    if cfg['researchPriceMinimumOpportunities'] > 0:
        # Research candidate only (off by default) — fall back to the faithful
        # pure-Python path which computes the opportunity weights.
        from ..kernel.tick import observe_markets as _pure
        return _pure(W, cfg, profiles)
    _observe_markets_nb(
        float(cfg['alpha']), int(W.t2LineCount),
        W.t0Price, W.t0Demand, W.t0Sold, W.t0DemandEMA, W.t0SalesEMA, W.t0Revenue, W.t0COGS,
        W.t0LearnProfit, W.t0LearnSales, W.t0LearnTicks, W.t0LearnDemand, W.t0LearnStock, W.t0Inv,
        W.t1Operates, W.t1Demand, W.t1Sold, W.t1DemandEMA, W.t1SalesEMA, W.t1Rev, W.t1COGS,
        W.t1LearnProfit, W.t1LearnSales, W.t1LearnTicks, W.t1LearnDemand, W.t1LearnStock, W.t1Fin,
        W.t2Demand, W.t2Sold, W.t2DemandEMA, W.t2SalesEMA, W.t2Revenue, W.t2COGS,
        W.t2LearnProfit, W.t2LearnSales, W.t2LearnTicks, W.t2LearnDemand, W.t2LearnStock, W.t2Fin,
        W.t2MonthSold)


def plan_and_buy_inputs_fast(W, cfg, tick):
    t1_output, t1_target = t1_scale_arrays(cfg)
    t1_conv = np.array([M.conversion_cost(p['complexity'], cfg) for p in M.PRODUCTS], dtype=np.float64)
    _plan_and_buy_inputs_nb(
        cfg['seed'], tick, cfg['minWholesaleLot'],
        cfg['baseCost'], cfg['t1Capacity'], t1_conv,
        float(cfg['storage']), float(cfg['taumin']), float(cfg['taumax']),
        W.t0Price, W.t0Inv, W.t0InvBasis, W.t0Rel, W.t0Cash, W.t0Req, W.t0FundedReq,
        W.t0Opportunities, W.t0Demand, W.t0RelAttempts, W.t0RelFulfilled, W.t0RelChecks,
        W.t0RelAvailable, W.t0Sold, W.t0Revenue, W.t0COGS, W.t0Ful, W.difficulty,
        W.t1Cash, W.t1Fin, W.t1FinBasis, W.t1Price, W.t1ReplacementCost, W.t1Operates,
        W.t1InputNeed, W.t1PurchaseReq, W.t1LastBuy, W.t1Bought, W.raw, W.rawBasis,
        W.preferredWholesale, PROF_HAS, PROF_N, T1_INPUT_RATIO, t1_output, t1_target, T1_IS_BASIC)


def tier2_buy_make_price_fast(W, cfg, tick):
    t1_offers = _market_offers(W, 1, tick)
    flat, off = _flatten(t1_offers)
    qf, val = procurement_arrays(cfg)
    t2_conv, _, t2_cap, t2_target = t2_scale_arrays(cfg)
    cs = _tier2_buy_make_price_nb(
        cfg['seed'], tick, cfg['t2FirmCount'], float(cfg['storage']),
        t2_conv, float(cfg['switchingStableBand']),
        float(cfg['taumin']), float(cfg['taumax']), cfg['priceObservationTicks'],
        cfg['researchPriceMinimumPotentialOrders'], cfg['researchPriceMaxObservationTicks'],
        cfg['researchPriceMinimumOpportunities'], float(cfg['k']), float(cfg['wholesalePriceResponse']),
        W.t1Fin, W.t1Price, W.t1Rel, W.t1Cash, W.t1Sold, W.t1Rev, W.t1COGS, W.t1FinBasis,
        W.t1IntermediateSold, W.t1IntermediateRevenue, W.t1Demand, W.t1RelAttempts,
        W.t1RelFulfilled, W.t1RelAvailChecks, W.t1RelAvailable, W.t1Opportunities,
        W.t2Cash, W.t2Raw, W.t2RawBasis, W.t2T1Raw, W.t2T1Basis, W.t2Preferred,
        W.t2FirmLines, W.t2FirmLineCount, W.t2LineProduct, W.t2Controller,
        W.t2Fin, W.t2FinBasis, W.t2UnitCost, W.t2ReplacementCost, W.t2Price, W.t2PlayerPrice,
        W.t2Made, W.t2DemandEMA, W.t2Sold, W.t2Revenue, W.t2COGS, W.t2Bought,
        W.t2RelPriceSum, W.t2RelPriceSamples, W.t2MonthlyCapacity,
        W.t2LearnTicks, W.t2LearnProfit, W.t2LearnSales, W.t2LearnPrevious,
        W.t2LearnDirection, W.t2LearnDemand, W.t2LearnStock, W.t2LearnStep,
        W.t2LearnOpportunity, W.t2LearnPotentialOpportunity,
        flat, off, qf, val, t2_cap, T2_OUTPUT, t2_target)
    W.costSinks += cs
    return cs


def clear_end_users_fast(W, cfg, tick):
    offers = _market_offers(W, 2, tick)
    flat, off = _flatten(offers)
    qf, val = procurement_arrays(cfg)
    # Per-tick demand-ledger reset (mirrors the top of clearEndUsers in JS).
    W.endPotential.fill(0)
    W.endActive.fill(0)
    W.endFulfilled.fill(0)
    W.endPriceLost.fill(0)
    W.endStockUnmet.fill(0)
    W.endLastMarket.fill(-1)
    W.endLastSupplier.fill(-1)
    W.endLastQ.fill(0)
    W.endLastFulfilled.fill(0)
    return _clear_end_users_nb(
        cfg['seed'], tick, cfg['endUserCount'], float(cfg['consumerActivation']),
        cfg['consumerSearchOffers'], float(cfg['taumin']), float(cfg['taumax']),
        float(cfg['tier2ReservationPremium']), N_T2,
        W.endBasketCount, W.endBasket, W.endNeedProduct, W.endPreferredProduct, W.endPreferredSupplier,
        W.endLastMarket, W.endLastSupplier, W.endLastQ, W.endLastFulfilled,
        W.endQMax, W.endChoke, W.endEta,
        W.endPotential, W.endActive, W.endFulfilled, W.endPriceLost, W.endStockUnmet,
        W.t2SectorCount, W.t2SectorProducts, W.t2SectorProductWeight,
        flat, off, W.t2FirmLineCount, W.t2LineFirm,
        W.t2Fin, W.t2Price, W.t2Rel, W.t2Demand, W.t2RelAttempts, W.t2RelFulfilled, W.t2RelAvailable,
        W.t2Cash, W.t2LastSaleTick, W.t2Sold, W.t2Revenue, W.t2COGS, W.t2FinBasis,
        W.t2Opportunities, W.t2PotentialOrders, T2_COMPLEXITY, qf, val)
