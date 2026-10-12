"""Isolated retail selection and transactional settlement on real world arrays.

The production tick never imports this module. Caller can substitute this phase
in a versioned experimental runner; industrial procurement stays separately
identified. Market books include active lines with finite quotes, including
empty-stock offers. Five distinct lines plus the valid incumbent are sampled.
"""
import math
import numpy as np
from economy.core import model as M
from economy.core.rng import random_
from .jit import njit
from .discovery import sample_distinct
from .retail import solve_retail_into
from .observations import record_order
from .seller_exposure import record_exposure
from .retail_traces import capture as capture_trace


@njit
def clear_kernel(seed, tick, count, activation, multiple, premium, np1,
                 books, offsets, complexity, valuation, buyer_data, seller_data,
                 market_data, loyalty, observations, exposure=None, trace=None):
    products, preferred, last_market, last_supplier, last_q, last_fill, qmaxs, chokes, etas = buyer_data
    stock, prices, reliability, demand, attempts, available, cash, last_sale, sold, revenue, cogs, basis, owners, opportunities, potential_orders, fee_income = seller_data
    potential, active, fulfilled, price_lost, shortfall = market_data
    orders = filled_orders = activated = purchases = 0
    payments = 0.
    maximum = 0
    for i in range(count):
        maximum = max(maximum, int(math.ceil(qmaxs[i])))
    values = np.empty(maximum)
    quotes = np.empty(6)
    stocks = np.empty(6, dtype=np.int64)
    desired = np.empty(6, dtype=np.int64)
    allocation = np.empty(6, dtype=np.int64)
    solver_order = np.empty(6, dtype=np.int64)
    trace_q = np.empty(6, dtype=np.int64)
    trace_x = np.empty(6, dtype=np.int64)
    for buyer in range(count):
        if random_(seed, tick, buyer + 2000000) >= activation:
            continue
        activated += 1
        market = products[buyer]
        pid = market - np1
        last_market[buyer] = market
        # Explicit doubles keep NumPy scalar promotion in the Python reference
        # consistent with the native arithmetic used by the compiled curve.
        latent = float(qmaxs[buyer])
        rounding = random_(seed, tick, buyer + 7000000)
        potential_q = int(math.floor(latent)) + int(rounding < latent % 1)
        if potential_q <= 0:
            if trace is not None:
                slot=trace[0][buyer]
                if slot>=0:
                    trace[1][slot,0]=1
                    trace[1][slot,1]=market
                    trace[1][slot,2]=latent
                    trace[1][slot,3]=rounding
                    trace[1][slot,13]=potential_q
            continue
        potential_orders[pid] += 1
        potential[market] += potential_q
        half = valuation[pid] * chokes[buyer] * (1 + premium * (complexity[pid] - 1))
        ids = sample_distinct(books[offsets[pid]:offsets[pid + 1]], preferred[buyer], seed, tick, buyer, market)
        # A basket cannot consume more marginal values than available whole
        # items. Keep the original potential quantity for demand observations.
        value_count = 0
        for i in range(len(ids)):
            quotes[i] = prices[ids[i]]
            stocks[i] = int(stock[ids[i]])
            value_count = min(potential_q, value_count + max(0, stocks[i]))
        # Same inverse curve and arithmetic, only its reachable prefix.
        for unit in range(value_count):
            values[unit] = 0.
            quantile = unit + rounding
            if half > 0 and quantile < latent:
                values[unit] = half * (latent / max(quantile, 1e-12) - 1) ** (1 / float(etas[buyer]))
        incumbent = preferred[buyer]
        bid = 0
        fee = 0.
        for i in range(len(ids)):
            same_quote = -1
            for j in range(i):
                if quotes[j] == quotes[i]:
                    same_quote = j
                    break
            if same_quote >= 0:
                desired[i] = desired[same_quote]
            else:
                q = latent / (1 + (quotes[i] / half) ** etas[buyer]) if half > 0 else 0.
                desired[i] = int(math.floor(q)) + int(rounding < q % 1)
            if ids[i] == incumbent:
                bid = desired[i]
                fee = multiple * valuation[pid] * (1 + min(1., max(0., reliability[incumbent])))
        # Distributors have no stored cash constraint in the current economy.
        if value_count:
            objective, goods_cost, charge, new_incumbent = solve_retail_into(
                values, value_count, quotes, stocks, ids, len(ids), incumbent, bid, fee, 1e100,
                desired, allocation, solver_order)
        else:
            # The only feasible basket is empty. Continue through ordinary
            # request, reliability, exposure and preference reporting below.
            objective = goods_cost = charge = 0.
            new_incumbent = incumbent
            for i in range(len(ids)):
                allocation[i] = 0
        # Request traces follow ascending quote, even when allocation skips an
        # offer because of fees. Only positive chosen deliveries are requests;
        # an empty-stock no-purchase attempt may add one best-quote request.
        # Fee/valuation rejection alone creates no supplier request.
        ranks = np.argsort(quotes[:len(ids)])
        if trace is not None:
            capture_trace(trace,buyer,market,latent,rounding,half,etas[buyer],incumbent,bid,fee,
                          new_incumbent,charge,objective,goods_cost,potential_q,ids,quotes,stocks,desired,allocation,ranks)
        for i in range(len(ids)):
            trace_q[i] = 0
            trace_x[i] = 0
        legs = bought = 0
        primary = -1
        for rank in ranks:
            amount = allocation[rank]
            if amount <= 0:
                continue
            supplier = ids[rank]
            want = max(0, desired[rank] - bought)
            trace_q[legs] = desired[rank]
            trace_x[legs] = amount
            legs += 1
            demand[supplier] += want
            attempts[supplier] += 1
            available[supplier] += int(amount >= want)
            stock[supplier] -= amount
            value = amount * quotes[rank]
            cash[owners[supplier]] += value
            last_sale[owners[supplier]] = tick
            sold[supplier] += amount
            revenue[supplier] += value
            cogs[supplier] += amount * basis[supplier]
            if primary < 0:
                primary = supplier
            bought += amount
        if legs == 0 and len(ids):
            rank = ranks[0]
            # An empty stock offer is a real attempted request; rejection on
            # valuation/fee grounds is not a supplier reliability failure.
            if desired[rank] > 0 and stocks[rank] == 0:
                trace_q[0] = desired[rank]
                legs = 1
                demand[ids[rank]] += desired[rank]
                attempts[ids[rank]] += 1
        if exposure is not None:
            record_exposure(exposure, ids, stocks, desired, 1)
        record_order(observations, market, len(ids), trace_q, trace_x, legs,
                     incumbent, new_incumbent, charge)
        terminal = trace_q[legs - 1] if legs else 0
        last_supplier[buyer] = primary
        last_q[buyer] = terminal
        last_fill[buyer] = bought
        active[market] += terminal
        price_lost[market] += potential_q - terminal
        shortfall[market] += max(0, terminal - bought)
        fulfilled[market] += bought
        if terminal > 0:
            orders += 1
            opportunities[pid] += 1
        if bought > 0:
            purchases += 1
            filled_orders += int(bought >= terminal)
            preferred[buyer] = new_incumbent
        if charge > 0:
            cash[owners[incumbent]] += charge
            fee_income[owners[incumbent]] += charge
            loyalty[0][2] += 1
            loyalty[1][2] += charge
        payments += goods_cost + charge
    return orders, filled_orders, activated, payments, purchases


def clear_distributors(world, cfg, tick, observations, compiled=True, exposure=None, trace=None):
    world.sync_distributor_preferences()
    count = int(world.t2LineCount)
    books = []
    offsets = [0]
    for pid in range(len(M.T2_PRODUCTS)):
        books.extend(np.flatnonzero((world.t2LineProduct[:count] == pid)
                                   & np.isfinite(world.t2Price[:count])).tolist())
        offsets.append(len(books))
    valuation = np.array([M.procurement_profile(p, cfg, M.reference_tier2_cost(p, cfg))['valuation'] for p in M.T2_PRODUCTS])
    for name in ('marketPotential', 'marketActive', 'marketFulfilled', 'marketPriceLost', 'marketStockUnmet', 'distributorLastQ', 'distributorLastFulfilled'):
        getattr(world, name).fill(0)
    world.distributorLastMarket.fill(-1)
    world.distributorLastSupplier.fill(-1)
    observations.fill(0)
    return (clear_kernel if compiled else clear_kernel.py_func)(
        cfg['seed'], tick, cfg['distributorCount'], cfg['distributorActivation'], world.lm3,
        cfg['t2ReservationPremium'], M.NP, np.array(books, dtype=np.int64), np.array(offsets, dtype=np.int64),
        np.array([p['complexity'] for p in M.T2_PRODUCTS]), valuation,
        tuple(getattr(world, n) for n in ('distributorProduct', 'distributorPreferredSupplier', 'distributorLastMarket', 'distributorLastSupplier', 'distributorLastQ', 'distributorLastFulfilled', 'distributorQMax', 'distributorChoke', 'distributorEta')),
        tuple(getattr(world, n) for n in ('t2Fin', 't2Price', 't2Rel', 't2Demand', 't2RelAttempts', 't2RelAvailable', 't2Cash', 't2LastSaleTick', 't2Sold', 't2Revenue', 't2COGS', 't2FinBasis', 't2LineFirm', 't2Opportunities', 't2PotentialOrders', 't2SwitchingIncome')),
        tuple(getattr(world, n) for n in ('marketPotential', 'marketActive', 'marketFulfilled', 'marketPriceLost', 'marketStockUnmet')),
        (world.loyaltySwitches, world.loyaltyPenalties), observations, exposure, trace)
