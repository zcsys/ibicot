/* Source-first Phase 0 economy kernel.  This is intentionally plain JS so
 * every economic rule is editable and testable. */
(function (root) {
  'use strict';
  const M = root.Phase0Model;
  const NE = M.ELEMENTS.length,
    NP = M.PRODUCTS.length,
    N0 = 20,
    N1 = 1000,
    MONTH = 30;
  const clamp = M.clamp;
  const mix = (value) => {
    value >>>= 0;
    value = Math.imul(value ^ (value >>> 16), 0x85ebca6b);
    value = Math.imul(value ^ (value >>> 13), 0xc2b2ae35);
    return (value ^ (value >>> 16)) >>> 0;
  };
  const random = (seed, tick, stream) =>
    mix(
      (seed >>> 0) ^
        Math.imul((tick + 1) >>> 0, 0x9e3779b1) ^
        Math.imul((stream + 1) >>> 0, 0x85ebca6b),
    ) / 4294967296;
  const normal = (seed, tick, stream) =>
    Math.sqrt(-2 * Math.log(Math.max(1e-12, random(seed, tick, stream)))) *
    Math.cos(2 * Math.PI * random(seed, tick, stream + 1));
  const sum = (array) => {
    let value = 0;
    for (let i = 0; i < array.length; i++) value += array[i] || 0;
    return value;
  };
  const finite = (value) => (Number.isFinite(value) ? value : 0);
  // The catalogue and its ingredient maps are immutable. Numeric rows avoid
  // repeating string-key ingredient lookups for every planned route.
  // Custom mechanism fixtures retain fresh rows so mutable inputs stay live.
  const catalogueInputRatios = M.T2_PRODUCTS.map(product =>
    new Float64Array(M.PRODUCTS.map(material => product.inputs[material.code] || 0)));

  function zero(W) {
    for (const value of Object.values(W))
      if (value && typeof value.fill === 'function') value.fill(0);
  }

  function resetTick(W) {
    for (const name of [
      't0Opportunities', 't1Opportunities', 't2Opportunities', 't2PotentialOrders',
      't1Bought',
      't2Bought',
      't0Sold',
      't0Revenue',
      't0COGS',
      't0Demand',
      't1Demand',
      't2Demand',
      't1Sold',
      't1Rev',
      't1COGS',
      't1IntermediateSold',
      't1IntermediateRevenue',
      'active',
      'potential',
      'fulfilled',
      'priceLost',
      'stockUnmet',
      't0Ful',
      't0FundedReq',
      't1InputNeed',
      't1PurchaseReq',
    ])
      W[name].fill(0);
    if (W.t2Sold) {
      W.t2Sold.fill(0);
      W.t2Revenue.fill(0);
      W.t2COGS.fill(0);
      W.t2Made.fill(0);
    }
  }

  function updateEnvironment(W, cfg, tick) {
    for (let e = 0; e < NE; e++)
      W.difficulty[e] = clamp(
        W.difficulty[e] +
          cfg.theta * (cfg.dbar - W.difficulty[e]) +
          cfg.sigma * normal(cfg.seed, tick, e * 4),
        cfg.dmin,
        cfg.dmax,
      );
  }

  function produceTier0(W, cfg, profiles, tick) {
    for (let supplier = 0; supplier < N0; supplier++) {
      // Canonical material IDs make the schedule independent of profile list
      // order. Rotating positive routes gives scarce machine quanta and tied
      // remainders no permanent first/last-material preference.
      const elements = profiles[supplier].elements.map((element) => M.ELEMENTS.indexOf(element)).sort((a, b) => a - b);
      const targetPerElement = cfg.targetInventory / elements.length;
      const targets = elements.map((e) => M.finishedStockTarget({
        salesEMA: W.t0DemandEMA[supplier * NE + e], coverageTicks: cfg.inventoryCoverageTicks,
        bootstrapStock: Math.max(cfg.minWholesaleLot, Math.ceil(cfg.capacity * 0.1 / elements.length)),
        capacity: cfg.capacity, targetInventory: targetPerElement, maxInventory: cfg.maxInventory / elements.length }));
      const deficits = elements.map((e, n) => Math.max(0, targets[n] - W.t0Inv[supplier * NE + e]));
      let capacity = Math.max(0, cfg.capacity);
      // maxInventory is a company-wide warehouse limit, shared by every
      // element this supplier extracts—not a separate cap per element.
      let totalInventory = elements.reduce(
        (total, e) => total + Math.max(0, W.t0Inv[supplier * NE + e]),
        0,
      );
      const costs = elements.map(e => {
        const index = supplier * NE + e, cost = Math.max(1e-9, cfg.baseCost * W.difficulty[e]);
        W.t0Cost[index] = cost;
        if (!Number.isFinite(W.t0Price[index]) || W.t0Price[index] <= 0)
          W.t0Price[index] = cost * (1 + cfg.markup);
        return cost;
      });
      const positive = elements.map((_, n) => n).filter(n => deficits[n] > 0);
      if (!positive.length) continue;
      const start = ((cfg.seed >>> 0) + tick + supplier) % positive.length;
      const priority = positive.slice(start).concat(positive.slice(0, start));
      const rank = new Map(priority.map((n, position) => [n, position]));
      const make = (n, planned) => {
        const index = supplier * NE + elements[n], cost = costs[n];
        const warehouseHeadroom = Math.max(0, cfg.maxInventory - totalInventory);
        const affordable = Math.floor(Math.max(0, W.t0Cash[supplier]) / cost);
        const made = Math.max(0, Math.min(planned, deficits[n], capacity, warehouseHeadroom, affordable));
        const old = W.t0Inv[index];
        if (made > 0) W.t0InvBasis[index] = (old * W.t0InvBasis[index] + made * cost) / (old + made);
        W.t0Inv[index] += made;
        W.t0Cash[supplier] -= made * cost;
        W.costSinks += made * cost;
        capacity -= made;
        totalInventory += made;
        deficits[n] -= made;
        return made;
      };
      // Ensure every positive route can receive a machine unit when shared
      // capacity, storage and cash allow. Already-positive proportional
      // allocations need no reservation; reserve only sub-unit quotas, or
      // rotate all positive routes when there are fewer units than routes.
      // Otherwise a 1/2-unit
      // bootstrap deficit can round to zero forever and remain below the
      // wholesale discovery lot while siblings keep producing. This quantum
      // schedules physical production; it supplies no orders or earnings.
      const totalDeficit = deficits.reduce((total, deficit) => total + deficit, 0);
      const initialBudget = Math.max(0, Math.min(capacity, cfg.maxInventory - totalInventory, totalDeficit));
      // When cash can bind the bulk round, reserve feasible quanta first as
      // well: a bulk route must not consume cash which could fund one unit
      // on every positive sibling. Unaffordable routes still receive none.
      const cashCanBind = initialBudget * Math.max(...positive.map(n => costs[n])) > W.t0Cash[supplier];
      if (initialBudget < positive.length || cashCanBind)
        for (const n of priority) make(n, Math.min(1, deficits[n]));
      else {
        const reserved = new Set();
        // A reservation can shrink a sibling's quota below one. Recheck the
        // remaining routes until every unreserved quota is at least one.
        for (let pass = 0; pass < NE; pass++) {
          const total = deficits.reduce((value, deficit) => value + deficit, 0);
          const budget = Math.max(0, Math.min(capacity, cfg.maxInventory - totalInventory, total));
          const small = priority.filter(n => !reserved.has(n) && deficits[n] > 0 && budget * deficits[n] / total < 1);
          if (!small.length) break;
          for (const n of small) { make(n, Math.min(1, deficits[n])); reserved.add(n); }
        }
      }
      // Allocate the remaining machine time proportionally, using largest
      // fractional remainders and the same rotating neutral tie order. Cash
      // clamps can leave room for cheaper routes; re-apportion that room over
      // routes which can still afford at least one unit. Each such clamp
      // removes an affordable route, so at most NE+2 passes are needed,
      // including a final sub-unit capacity/target remainder if configured.
      for (let pass = 0; pass < NE + 2 && capacity > 1e-9; pass++) {
        const feasible = deficits.map((deficit, n) => Math.min(deficit,
          Math.floor(Math.max(0, W.t0Cash[supplier]) / costs[n])));
        const total = feasible.reduce((value, deficit) => value + deficit, 0);
        const budget = Math.max(0, Math.min(capacity, cfg.maxInventory - totalInventory, total));
        if (budget <= 1e-9) break;
        let plans;
        if (budget >= total) plans = feasible;
        else if (budget < 1) plans = feasible.map(deficit => budget * deficit / total);
        else {
          const whole = Math.floor(budget), quotas = feasible.map(deficit => whole * deficit / total);
          plans = quotas.map(Math.floor);
          let remainder = whole - plans.reduce((value, planned) => value + planned, 0);
          const order = priority.slice().sort((a, b) =>
            (quotas[b] - plans[b]) - (quotas[a] - plans[a]) || rank.get(a) - rank.get(b));
          for (const n of order) {
            const extra = Math.min(1, feasible[n] - plans[n], remainder);
            plans[n] += extra; remainder -= extra;
          }
        }
        let produced = 0;
        for (const n of priority) produced += make(n, plans[n]);
        if (produced <= 1e-9) break;
      }
    }
  }

  function tier0Supplier(W, cfg, profiles, e, preferred, buyer = 0, tick = 0) {
    let best = Infinity, emptyPrice = Infinity;
    const stocked = [], empty = [];
    for (let supplier = 0; supplier < N0; supplier++) {
      if (!profiles[supplier].elements.includes(M.ELEMENTS[e])) continue;
      const index = supplier * NE + e, quote = W.t0Price[index];
      if (!Number.isFinite(quote)) continue;
      const friction = supplier === preferred ? 0 : M.switchingCost(
        preferred >= 0 ? W.t0Rel[preferred * NE + e] : 0.5, cfg.taumin, cfg.taumax);
      const effective = quote + friction;
      if (effective < emptyPrice - 1e-12) { emptyPrice = effective; empty.length = 0; }
      if (Math.abs(effective - emptyPrice) <= 1e-12) empty.push(supplier);
      if (W.t0Inv[index] >= cfg.minWholesaleLot) {
        if (effective < best - 1e-12) { best = effective; stocked.length = 0; }
        if (Math.abs(effective - best) <= 1e-12) stocked.push(supplier);
      }
    }
    const tied = stocked.length ? stocked : empty;
    if (!tied.length) return -1;
    // Equal effective offers have no company-ID priority. A supplier's
    // company-wide capacity is shared across its listed elements, so tied
    // discovery uses its capacity share rather than multiplying exposure.
    const total = tied.reduce((sum, supplier) => sum + 1 / profiles[supplier].elements.length, 0);
    let draw = random(cfg.seed, tick, buyer + 12000000 + e * 1300000) * total;
    for (const supplier of tied) {
      draw -= 1 / profiles[supplier].elements.length;
      if (draw < 0) return supplier;
    }
    return tied[tied.length - 1];
  }

  function planAndBuyInputs(W, cfg, products, profiles, tick) {
    W.t0Req.fill(0);
    W.t0FundedReq.fill(0);
    // Interleave cohorts instead of processing all firms in cohort order.
    // This gives every product market a recurring chance to buy each input,
    // rather than letting whichever cohort is first drain a shared element.
    const firstCohort = tick % NP,
      firstFirm = (tick * 37) % 100;
    for (let round = 0; round < 100; round++)
      for (let cohortOrder = 0; cohortOrder < NP; cohortOrder++) {
        const cohort = (firstCohort + cohortOrder) % NP;
        const company = cohort * 100 + ((firstFirm + round) % 100);
        const rawBase = company * NE,
          productBase = company * NP;
        const suppliers = M.ELEMENTS.map((_, e) => tier0Supplier(W, cfg, profiles, e, W.preferredWholesale[rawBase + e], company, tick));
        for (let p = 0; p < NP; p++) {
          if (!W.t1Operates[productBase + p]) continue;
          const product = products[p],
            cap =
              Object.keys(product.inputs).length === 1
                ? cfg.basicEquipmentCapacity
                : cfg.compoundEquipmentCapacity;
          const target = tier1StockTarget(W, cfg, product, productBase + p);
          const desired = Math.max(
            0,
            Math.min(
              cap,
              target - W.t1Fin[productBase + p],
            ),
          );
          let replacement = cfg.manufacturingCostPerUnit;
          for (const [element, ratio] of Object.entries(product.inputs)) {
            const e = M.ELEMENTS.indexOf(element), supplier = suppliers[e];
            const quote = supplier >= 0 ? W.t0Price[supplier * NE + e] : W.t1LastBuy[rawBase + e];
            const stocked = Math.min(desired * ratio, W.raw[rawBase + e]);
            replacement += desired > 0 ? (stocked * W.rawBasis[rawBase + e] +
              (desired * ratio - stocked) * (Number.isFinite(quote) ? quote : cfg.baseCost * W.difficulty[e])) / desired :
              ratio * (Number.isFinite(quote) ? quote : W.rawBasis[rawBase + e]);
          }
          W.t1ReplacementCost[productBase + p] = replacement;
          // Inputs are derived demand: cash alone is not a reason to buy an
          // entire recipe whose expected proceeds fail to cover its cost.
          if (desired > 0 && replacement > W.t1Price[productBase + p] + 1e-9) continue;
          for (const [element, ratio] of Object.entries(product.inputs)) {
            const e = M.ELEMENTS.indexOf(element),
              need = Math.max(0, desired * ratio - W.raw[rawBase + e]);
            if (need > 0) W.t1InputNeed[rawBase + e] += Math.max(need, cfg.minWholesaleLot);
          }
        }
        for (let e = 0; e < NE; e++) {
          const need = W.t1InputNeed[rawBase + e];
          if (need <= 0) continue;
          const request = Math.ceil(need / cfg.minWholesaleLot) * cfg.minWholesaleLot;
          W.t1PurchaseReq[rawBase + e] = request;
          W.t0Req[e] += request;
          const chosen = suppliers[e];
          if (chosen < 0) continue;
          const supplierIndex = chosen * NE + e,
            quote = Math.max(0, W.t0Price[supplierIndex]);
          const affordable = Math.floor(Math.max(0, W.t1Cash[company]) / Math.max(1e-9, quote));
          const available = Math.floor(Math.max(0, W.t0Inv[supplierIndex]));
          let held = 0;
          for (let material = 0; material < NE; material++) held += W.raw[rawBase + material];
          for (let output = 0; output < NP; output++) held += W.t1Fin[productBase + output];
          const storageRoom = Math.floor(Math.max(0, cfg.tier1InventoryCapacity - held) / cfg.minWholesaleLot) * cfg.minWholesaleLot;
          // Price pressure uses only demand that the buyer can actually fund;
          // an unaffordable lot is not a scarcity signal.
          const funded =
            Math.floor(Math.min(request, affordable, storageRoom) / cfg.minWholesaleLot) * cfg.minWholesaleLot;
          W.t0FundedReq[e] += funded;
          if (funded > 0) W.t0Opportunities[e]++;
          W.t0Demand[supplierIndex] += funded;
          const bought =
            Math.floor(Math.min(funded, available) / cfg.minWholesaleLot) * cfg.minWholesaleLot;
          const attempt = request > 0 ? 1 : 0;
          W.t0RelAttempts[supplierIndex] += attempt;
          W.t0RelFulfilled[supplierIndex] += bought >= request ? attempt : 0;
          W.t0RelChecks[supplierIndex] += attempt;
          W.t0RelAvailable[supplierIndex] += available >= request ? attempt : 0;
          if (bought <= 0) continue;
          const oldRaw = W.raw[rawBase + e],
            oldBasis = W.rawBasis[rawBase + e],
            payment = bought * quote;
          W.raw[rawBase + e] = oldRaw + bought;
          W.t1Bought[company] += bought;
          W.rawBasis[rawBase + e] =
            oldRaw + bought > 0 ? (oldBasis * oldRaw + payment) / (oldRaw + bought) : 0;
          W.t1LastBuy[rawBase + e] = quote;
          W.t1Cash[company] -= payment;
          W.t0Cash[chosen] += payment;
          W.t0Inv[supplierIndex] -= bought;
          W.t0Sold[supplierIndex] += bought;
          W.t0Revenue[supplierIndex] += payment;
          W.t0COGS[supplierIndex] += bought * W.t0InvBasis[supplierIndex];
          W.t0Ful[e] += bought;
          W.preferredWholesale[rawBase + e] = chosen;
        }
      }
  }

  function tier1StockTarget(W, cfg, product, index) {
    const cap = M.complexity(product) === 1 ? cfg.basicEquipmentCapacity : cfg.compoundEquipmentCapacity;
    return M.finishedStockTarget({ salesEMA: W.t1DemandEMA[index], coverageTicks: cfg.inventoryCoverageTicks,
      bootstrapStock: Math.max(cfg.demandQtyMax, Math.ceil(cap * 0.1)), capacity: cap,
      targetInventory: cfg.retailTargetInventory, maxInventory: cfg.retailMaxInventory });
  }

  function manufacture(W, cfg, products) {
    for (let company = 0; company < N1; company++)
      for (let p = 0; p < NP; p++) {
        const index = company * NP + p;
        if (!W.t1Operates[index]) continue;
        const product = products[p],
          rawBase = company * NE;
        const cap = Object.keys(product.inputs).length === 1
            ? cfg.basicEquipmentCapacity
            : cfg.compoundEquipmentCapacity;
        const target = tier1StockTarget(W, cfg, product, index);
        let made = Math.min(cap, Math.max(0, target - W.t1Fin[index]));
        let inputCost = 0;
        for (const [element, ratio] of Object.entries(product.inputs)) {
          const e = M.ELEMENTS.indexOf(element);
          made = Math.min(made, Math.floor(W.raw[rawBase + e] / ratio));
          inputCost += ratio * W.rawBasis[rawBase + e];
        }
        made = Math.min(
          made,
          Math.floor(Math.max(0, W.t1Cash[company]) / Math.max(1e-9, cfg.manufacturingCostPerUnit)),
        );
        if (inputCost + cfg.manufacturingCostPerUnit > W.t1Price[index] + 1e-9) made = 0;
        if (made <= 0) continue;
        for (const [element, ratio] of Object.entries(product.inputs)) {
          const e = M.ELEMENTS.indexOf(element);
          W.raw[rawBase + e] -= made * ratio;
        }
        W.t1Cash[company] -= made * cfg.manufacturingCostPerUnit;
        W.costSinks += made * cfg.manufacturingCostPerUnit;
        const oldFin = W.t1Fin[index],
          oldBasis = W.t1FinBasis[index],
          unitCost = inputCost + cfg.manufacturingCostPerUnit;
        W.t1Fin[index] = oldFin + made;
        W.t1FinBasis[index] =
          oldFin + made > 0 ? (oldBasis * oldFin + unitCost * made) / (oldFin + made) : 0;
        W.t1UnitCost[index] = unitCost;
      }
  }

  function priceLearningView(W, tier) {
    return { tier, price: W[`${tier}Price`], ages: W[`${tier}LearnTicks`],
      profits: W[`${tier}LearnProfit`], sales: W[`${tier}LearnSales`],
      previous: W[`${tier}LearnPrevious`], direction: W[`${tier}LearnDirection`],
      demand: W[`${tier}LearnDemand`], stocks: W[`${tier}LearnStock`], steps: W[`${tier}LearnStep`],
      opportunity: W[`${tier}LearnOpportunity`], potentialOpportunity: W[`${tier}LearnPotentialOpportunity`] };
  }

  function learnedQuote(view, cfg, index, cost, stock, tick) {
    const { price, ages } = view;
    // Reading a dozen learning arrays is unnecessary between decision dates.
    // The posted offer still obeys the same current cost reservation each tick.
    if (ages[index] < cfg.priceObservationTicks || (tick + index) % cfg.priceObservationTicks !== 0)
      return Math.max(M.MIN_UNIT_PRICE, cost, price[index]);
    const { profits, sales, previous, direction, demand, stocks, steps } = view;
    const staleEvidence = view.tier === 't2' && cfg.researchPriceMinimumPotentialOrders > 0
      ? view.potentialOpportunity[index] >= cfg.researchPriceMinimumPotentialOrders
      : ages[index] >= cfg.researchPriceMaxObservationTicks;
    const enoughTraffic = !cfg.researchPriceMinimumOpportunities ||
      view.opportunity[index] >= cfg.researchPriceMinimumOpportunities || staleEvidence;
    if (enoughTraffic) {
      const average = profits[index] / ages[index];
      const result = M.adaptivePrice({ oldPrice: price[index], unitCost: cost,
        profit: average, previousProfit: previous[index], direction: direction[index],
        sales: sales[index], stock, demand: demand[index], available: sales[index] + stocks[index],
        stepScale: steps[index], k: cfg.k, response: cfg.wholesalePriceResponse });
      price[index] = result.price; direction[index] = result.direction; previous[index] = average;
      steps[index] = result.stepScale;
      profits[index] = sales[index] = demand[index] = ages[index] = 0;
      view.opportunity[index] = view.potentialOpportunity[index] = 0;
    }
    return Math.max(M.MIN_UNIT_PRICE, cost, price[index]);
  }

  function priceMarkets(W, cfg, profiles, products, tick) {
    const t0Learning = priceLearningView(W, 't0'), t1Learning = priceLearningView(W, 't1');
    for (let supplier = 0; supplier < N0; supplier++)
      for (let e = 0; e < NE; e++) {
        const index = supplier * NE + e;
        if (!Number.isFinite(W.t0Price[index])) continue;
        const previous = W.t0Price[index],
          next = learnedQuote(t0Learning, cfg, index, Math.max(W.t0Cost[index], W.t0InvBasis[index]), W.t0Inv[index], tick);
        W.t0PrevPrice[index] = previous;
        W.t0Price[index] = next;
        const stable =
          1 -
          Math.min(
            1,
            Math.abs(next - previous) /
              Math.max(1e-9, previous) /
              Math.max(1e-9, cfg.switchingStableBand),
          );
        W.t0Stability[index] = stable;
        W.t0RelPriceSum[index] += stable;
        W.t0RelPriceSamples[index]++;
      }
    for (let company = 0; company < N1; company++)
      for (let p = 0; p < NP; p++) {
        const index = company * NP + p;
        if (!W.t1Operates[index]) continue;
        const previous = W.t1Price[index],
          unit = Math.max(M.MIN_UNIT_PRICE, W.t1FinBasis[index] || W.t1UnitCost[index], W.t1ReplacementCost[index]);
        const next =
          W.t1Controller[company] && Number.isFinite(W.playerPrice[index])
            ? Math.max(W.playerPrice[index], unit)
          : learnedQuote(t1Learning, cfg, index, unit, W.t1Fin[index], tick);
        W.t1PrevPrice[index] = previous;
        W.t1Price[index] = next;
        const stable =
          1 -
          Math.min(
            1,
            Math.abs(next - previous) /
              Math.max(1e-9, previous) /
              Math.max(1e-9, cfg.switchingStableBand),
          );
        W.t1PriceStability[index] = stable;
        W.t1RelPriceSum[index] += stable;
        W.t1RelPriceSamples[index]++;
      }
  }

  function hasTier2Product(W, firm, productId) {
    for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++)
      if (W.t2LineProduct[W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]] === productId) return true;
    return false;
  }

  function addTier2Line(W, cfg, firm, product, paid = true) {
    if (!Number.isInteger(firm) || firm < 0 || firm >= cfg.t2FirmCount || !product)
      throw new Error('Invalid Tier 2 company or product.');
    if (!M.TIER_BOUNDARIES.T2.includes(product.complexity)) throw new Error('Tier 2 firms can only manufacture C-3 through C-5 products.');
    if (W.t2FirmLineCount[firm] >= M.T2_MAX_PRODUCTS_PER_FIRM || W.t2LineCount >= W.t2Fin.length)
      throw new Error('Company or economy product-line limit reached.');
    if (hasTier2Product(W, firm, product.id)) throw new Error('This product line is already installed.');
    if (product.complexity > W.t2Capability[firm] || W.t2Sector[firm] !== product.sectorIndex)
      throw new Error('Machinery requires an eligible sector and capability.');
    if (paid && W.t2Cash[firm] < product.equipmentPrice) throw new Error('Insufficient cash.');
    const line = W.t2LineCount++;
    W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + W.t2FirmLineCount[firm]++] = line;
    W.t2LineFirm[line] = firm; W.t2LineProduct[line] = product.id;
    W.t2UnitCost[line] = M.initialTier2Cost(product, cfg);
    W.t2LearnStep[line] = 1;
    W.t2Price[line] = Math.max(M.MIN_UNIT_PRICE, W.t2UnitCost[line] * (1 + M.tier2StartingMarkup(product,cfg)));
    W.t2LearnPrevious[line] = NaN; W.t2LearnDirection[line] = ((firm + cfg.seed) % 2) ? 1 : -1;
    W.t2PlayerPrice[line] = NaN; W.t2Rel[line] = 0.5; W.t2SalesEMA[line] = 0; W.t2DemandEMA[line] = cfg.initialDemandForecastScale ?? 1;
    if (paid) { W.t2Cash[firm] -= product.equipmentPrice; W.equipmentSinks = (W.equipmentSinks || 0) + product.equipmentPrice; }
    if (paid) W.t2EqBook[firm] += product.equipmentPrice;
    return line;
  }

  // Sorted market indices are built once per tick, not once per buyer. Empty
  // offers are skipped at transaction time, so one drained firm cannot block
  // the whole market. Rotating equal-price ties prevents permanent ID priority.
  function marketOffers(W, tier, tick) {
    const count = tier === 0 ? NE : tier === 1 ? NP : M.T2_PRODUCTS.length;
    const offers = Array.from({ length: count }, () => []);
    const price = tier === 0 ? W.t0Price : tier === 1 ? W.t1Price : W.t2Price;
    const stock = tier === 0 ? W.t0Inv : tier === 1 ? W.t1Fin : W.t2Fin;
    const total = tier === 0 ? N0 * NE : tier === 1 ? N1 * NP : W.t2LineCount;
    for (let i = 0; i < total; i++) {
      if (!Number.isFinite(price[i]) || tier === 1 && !W.t1Operates[i]) continue;
      const market = tier === 2 ? W.t2LineProduct[i] : i % count;
      offers[market].push(i);
    }
    for (const market of offers) {
      if (tier === 1) {
        // Rotate within the actual market. Global sparse-array indices would
        // put the rotation boundary outside this cohort most of the time,
        // handing its first listed supplier an unearned priority.
        const ranks = new Map(market.map((supplier, rank) => [supplier, rank]));
        market.sort((a, b) => price[a] - price[b] ||
          ((ranks.get(a) + tick) % market.length) - ((ranks.get(b) + tick) % market.length));
      } else market.sort((a, b) => price[a] - price[b] ||
        ((a + tick * 37) % total) - ((b + tick * 37) % total));
    }
    return offers;
  }

  function chooseSupplier(offers, stock, price, preferred, reliability, cfg, minimum = 1, knownBest) {
    let best = knownBest ?? -1;
    if (knownBest === undefined) for (const supplier of offers) if (stock[supplier] >= minimum) { best = supplier; break; }
    if (preferred >= 0 && stock[preferred] >= minimum && Number.isFinite(price[preferred]) &&
        (best < 0 || price[preferred] <= price[best] + M.switchingCost(reliability[preferred], cfg.taumin, cfg.taumax) * (cfg.materialSwitchingScale ?? 1)))
      return preferred;
    if (best >= 0) return best;
    // All offers are empty: send a funded request to a known posted supplier
    // rather than silently erasing input demand. The transfer still delivers 0.
    const empty = offers[0];
    if (empty === undefined) return -1;
    return preferred >= 0 && offers.includes(preferred) &&
      price[preferred] <= price[empty] + M.switchingCost(reliability[preferred], cfg.taumin, cfg.taumax) * (cfg.materialSwitchingScale ?? 1)
      ? preferred : empty;
  }

  function tier2InventoryUnits(W, firm) {
    let total = 0;
    for (let material = 0; material < NP; material++) total += material < NE ?
      W.t2Raw[firm * NE + material] : W.t2T1Raw[firm * NP + material];
    for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++)
      total += W.t2Fin[W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]];
    return total;
  }

  function transferTier2Input(W, cfg, firm, material, supplier, request) {
    const isBasic = material < 4;
    const stock = W.t1Fin, prices = W.t1Price, cash = W.t1Cash;
    const supplierFirm = Math.floor(supplier / NP);
    const quote = prices[supplier], requested = Math.max(0, Math.min(Math.ceil(request),
      Math.floor(cfg.tier2InventoryCapacity - tier2InventoryUnits(W, firm))));
    const funded = Math.floor(Math.min(requested, W.t2Cash[firm] / quote));
    const quantity = Math.floor(Math.min(funded, stock[supplier]));
    W.t1Demand[supplier] += funded;
    if (funded > 0) W.t1Opportunities[material]++;
    W.t1RelAttempts[supplier]++; W.t1RelAvailChecks[supplier]++;
    if (quantity >= requested) W.t1RelFulfilled[supplier]++;
    if (stock[supplier] >= requested) W.t1RelAvailable[supplier]++;
    if (quantity <= 0) return 0;
    const raw = isBasic ? W.t2Raw : W.t2T1Raw, basis = isBasic ? W.t2RawBasis : W.t2T1Basis;
    const index = firm * (isBasic ? NE : NP) + material, old = raw[index], payment = quantity * quote;
    basis[index] = (basis[index] * old + payment) / (old + quantity); raw[index] += quantity;
    W.t2Bought[firm] += quantity;
    W.t2Cash[firm] -= payment; cash[supplierFirm] += payment; stock[supplier] -= quantity;
    W.t1Sold[supplier] += quantity; W.t1Rev[supplier] += payment;
    W.t1COGS[supplier] += quantity * W.t1FinBasis[supplier];
    W.t1IntermediateSold[material] += quantity; W.t1IntermediateRevenue[material] += payment;
    W.t2Preferred[firm * NP + material] = supplier;
    return quantity;
  }

  function tier2BuyMakePrice(W, cfg, products, profiles, t2Products, tick) {
    const t2Learning = priceLearningView(W, 't2');
    const t1Offers = marketOffers(W, 1, tick);
    const procurementProfiles = t2Products.map(product => M.procurementProfile(product, cfg,
      W.t2ReferenceCost[product.id] || M.referenceTier2Cost(product)));
    const inputRatios = t2Products === M.T2_PRODUCTS && products === M.PRODUCTS ? catalogueInputRatios :
      t2Products.map(product => new Float64Array(products.map(material => product.inputs[material.code] || 0)));
    const needs = new Float64Array(NP), plans = new Float64Array(M.T2_MAX_PRODUCTS_PER_FIRM);
    const suppliers = new Int32Array(NP), offerHeads = new Uint32Array(NP);
    // Tier 1 stock only decreases during this phase. Advance through each
    // sorted market once; earned preference and friction are still evaluated
    // separately for every buyer against the current cheapest stocked offer.
    for (let order = 0; order < cfg.t2FirmCount; order++) {
      const firm = (order + tick * 137) % cfg.t2FirmCount;
      needs.fill(0); plans.fill(0);
      let remainingProduction = cfg.tier2CompanyCapacity;
      const inventoryRoom = Math.max(0, cfg.tier2InventoryCapacity - tier2InventoryUnits(W, firm));
      for (let material = 0; material < NP; material++) {
        const offers = t1Offers[material];
        while (offerHeads[material] < offers.length && W.t1Fin[offers[offerHeads[material]]] < 1) offerHeads[material]++;
        const best = offerHeads[material] < offers.length ? offers[offerHeads[material]] : -1;
        suppliers[material] = chooseSupplier(offers, W.t1Fin, W.t1Price,
          W.t2Preferred[firm * NP + material], W.t1Rel, cfg, 1, best);
      }
      for (let order = 0; order < W.t2FirmLineCount[firm]; order++) {
        const slot = (order + tick) % W.t2FirmLineCount[firm];
        const line = W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot], product = t2Products[W.t2LineProduct[line]];
        const capacityShare = cfg.tier2CompanyCapacity / W.t2FirmLineCount[firm];
        const stockShare = Math.max(1, Math.ceil(cfg.tier2InventoryCapacity / 2 / W.t2FirmLineCount[firm]));
        const procurement = procurementProfiles[product.id];
        const target = M.finishedStockTarget({ salesEMA: W.t2DemandEMA[line], coverageTicks: cfg.inventoryCoverageTicks,
          bootstrapStock: Math.min(stockShare, Math.ceil(cfg.demandQtyMax * procurement.quantityFactor)), capacity: cfg.tier2CompanyCapacity,
          targetInventory: stockShare, maxInventory: stockShare });
        let desired = Math.max(0, Math.floor(Math.min(remainingProduction, target - W.t2Fin[line])));
        // Reserve room for the whole input bundle across all planned outputs.
        // Compound quantities occupy one storage unit, regardless of ancestry.
        while (desired > 0) {
          let missing = 0;
          for (let material = 0; material < NP; material++) {
            const ratio = inputRatios[product.id][material];
            const held = material < NE ? W.t2Raw[firm * NE + material] : W.t2T1Raw[firm * NP + material];
            missing += Math.max(0, needs[material] + desired * ratio - held);
          }
          if (missing <= inventoryRoom) break;
          desired--;
        }
        let replacement = product.conversionCost * cfg.tier2ConversionCostScale;
        for (const [material, ratio] of product.ingredients) {
          const basic = material < 4, index = firm * (basic ? NE : NP) + material,
            raw = basic ? W.t2Raw : W.t2T1Raw, basis = basic ? W.t2RawBasis : W.t2T1Basis,
            prices = W.t1Price, offers = t1Offers[material];
          const supplier = suppliers[material] >= 0 ? suppliers[material] : offers[0];
          const quote = supplier !== undefined ? prices[supplier] : basis[index];
          const stocked = Math.min(desired * ratio, raw[index]);
          replacement += desired > 0 ? (stocked * basis[index] + (desired * ratio - stocked) * quote) / desired : ratio * quote;
        }
        W.t2ReplacementCost[line] = replacement;
        if (replacement > W.t2Price[line] + 1e-9) desired = 0;
        plans[slot] = desired; remainingProduction -= desired;
        for (const [material, ratio] of product.ingredients) needs[material] += desired * ratio;
      }
      for (let material = 0; material < NP; material++) {
        const basic = material < 4, index = firm * (basic ? NE : NP) + material;
        const raw = basic ? W.t2Raw : W.t2T1Raw;
        const need = Math.max(0, needs[material] - raw[index]);
        if (!need) continue;
        const supplier = suppliers[material];
        if (supplier >= 0) transferTier2Input(W, cfg, firm, material, supplier, need);
      }
      for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++) {
        const line = W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot], product = t2Products[W.t2LineProduct[line]];
        let made = plans[slot], inputCost = 0;
        for (const [material, ratio] of product.ingredients) {
          const basic = material < 4, index = firm * (basic ? NE : NP) + material;
          made = Math.min(made, Math.floor((basic ? W.t2Raw : W.t2T1Raw)[index] / ratio));
          inputCost += ratio * (basic ? W.t2RawBasis : W.t2T1Basis)[index];
        }
        const conversionCost = product.conversionCost * cfg.tier2ConversionCostScale;
        made = Math.min(made, Math.floor(W.t2Cash[firm] / conversionCost));
        if (inputCost + conversionCost > W.t2Price[line] + 1e-9) made = 0;
        if (made > 0) {
          for (const [material, ratio] of product.ingredients)
            (material < 4 ? W.t2Raw : W.t2T1Raw)[firm * (material < 4 ? NE : NP) + material] -= made * ratio;
          W.t2Cash[firm] -= made * conversionCost;
          W.costSinks += made * conversionCost;
          const old = W.t2Fin[line], unit = inputCost + conversionCost;
          W.t2FinBasis[line] = (old * W.t2FinBasis[line] + unit * made) / (old + made);
          W.t2Fin[line] += made; W.t2UnitCost[line] = unit; W.t2Made[line] = made;
        }
        const unit = Math.max(M.MIN_UNIT_PRICE, W.t2FinBasis[line] || W.t2UnitCost[line], W.t2ReplacementCost[line]), previous = W.t2Price[line];
        W.t2Price[line] = W.t2Controller[firm] && Number.isFinite(W.t2PlayerPrice[line])
          ? Math.max(W.t2PlayerPrice[line], unit)
          : learnedQuote(t2Learning, cfg, line, unit, W.t2Fin[line], tick);
        W.t2RelPriceSum[line] += 1 - Math.min(1, Math.abs(W.t2Price[line] - previous) /
          Math.max(1e-9, previous * cfg.switchingStableBand));
        W.t2RelPriceSamples[line]++;
        W.t2MonthlyCapacity[line] += cfg.tier2CompanyCapacity / W.t2FirmLineCount[firm];
      }
    }
  }

  function clearEndUsers(W, cfg, products, t2Products, tick) {
    const offers = marketOffers(W, 2, tick);
    const procurementProfiles = t2Products.map(product => M.procurementProfile(product, cfg,
      W.t2ReferenceCost[product.id] || M.referenceTier2Cost(product)));
    // One discovery budget per firm, divided among its listed products.
    // More routes broaden choice without multiplying customer exposure.
    const cumulativeOffers = offers.map(market => {
      const weights = new Float64Array(market.length); let total = 0;
      market.forEach((line,i) => { total += 1 / W.t2FirmLineCount[W.t2LineFirm[line]]; weights[i] = total; });
      return weights;
    });
    W.endPotential.fill(0); W.endActive.fill(0); W.endFulfilled.fill(0);
    W.endPriceLost.fill(0); W.endStockUnmet.fill(0);
    W.endLastMarket.fill(-1); W.endLastSupplier.fill(-1); W.endLastQ.fill(0); W.endLastFulfilled.fill(0);
    let orders = 0, filledOrders = 0, activated = 0, consumerPayments = 0;
    for (let buyer = 0; buyer < cfg.endUserCount; buyer++) {
      if (random(cfg.seed, tick, buyer + 2000000) >= cfg.consumerActivation) continue;
      activated++;
      const slot = random(cfg.seed, tick, buyer + 3000000) < 0.60 ? 0 :
        1 + Math.floor(random(cfg.seed, tick, buyer + 3100000) * (W.endBasketCount[buyer] - 1));
      const relationship = buyer * 5 + slot, sector = W.endBasket[relationship];
      let market;
      // Public demand belongs exclusively to Tier 2 finished systems.
      // Need persistence is independent of successful unit purchases. Making
      // only successful products repeat would give high-volume goods extra
      // demand, even when every market has equal authored opportunity.
      const previous = W.endNeedProduct[relationship];
      if (previous >= NP && random(cfg.seed, tick, buyer + 5100000) < 0.65) market = previous;
      else {
        const base = sector * t2Products.length, count = W.t2SectorCount[sector];
        const draw = random(cfg.seed, tick, buyer + 6000000) * W.t2SectorProductWeight[base + count - 1];
        let offset = 0;
        while (offset < count - 1 && draw >= W.t2SectorProductWeight[base + offset]) offset++;
        market = NP + W.t2SectorProducts[sector * t2Products.length + offset];
      }
      W.endNeedProduct[relationship] = market;
      const product = t2Products[market - NP], complexity = product.complexity;
      // Equal procurement spending opportunity, not equal physical quantities:
      // a higher-cost recipe receives fewer units and proportional valuation.
      // The reference is engineering cost at the initial external conditions,
      // independent of a seller's current quote or learned margin.
      const profile = procurementProfiles[product.id];
      const multiplier = profile.quantityFactor;
      const latentQuantity = W.endQMax[buyer] * multiplier;
      const qmax = Math.ceil(latentQuantity);
      const rounding = random(cfg.seed, tick, buyer + 7000000);
      // The same draw rounds the no-price wishlist and every priced order.
      // With no physical unit needed, all non-negative quotes imply zero
      // orders. Retain product-need memory without shopping for suppliers.
      const potentialQuantity = Math.floor(latentQuantity) + (rounding < latentQuantity % 1 ? 1 : 0);
      W.endLastMarket[buyer] = market;
      if (potentialQuantity <= 0) continue;
      W.t2PotentialOrders[market - NP]++;
      W.endPotential[market] += potentialQuantity;
      const reference = profile.valuation;
      const premium = 1 + cfg.tier2ReservationPremium * (complexity - 1);
      const choke = reference * W.endChoke[buyer] * premium;
      const stock = W.t2Fin, price = W.t2Price;
      const reliability = W.t2Rel, marketOffersList = offers[market - NP];
      const preferred = W.endPreferredProduct[relationship] === market ? W.endPreferredSupplier[relationship] : -1;
      // Comparison shopping with bounded information (Mark I / shopbots).
      // Empty posted offers remain discoverable: attempted orders reveal the
      // demand that fulfilled-sales-only inventory forecasts would censor.
      const candidates = [];
      if (preferred >= 0 && Number.isFinite(price[preferred])) candidates.push(preferred);
      for (let sample = 0; sample < cfg.consumerSearchOffers && marketOffersList.length; sample++) {
        const weights = cumulativeOffers[market-NP];
        const draw = random(cfg.seed,tick,buyer+8000000+sample*1100000) * weights[weights.length-1];
        let low=0, high=weights.length-1;
        while(low<high) { const middle=(low+high)>>>1; if(draw<weights[middle]) high=middle; else low=middle+1; }
        const candidate = marketOffersList[low];
        if (!candidates.includes(candidate)) candidates.push(candidate);
      }
      const friction = preferred >= 0 ? M.switchingCost(reliability[preferred], cfg.taumin, cfg.taumax) : 0;
      candidates.sort((a, b) => (price[a] + (a === preferred ? 0 : friction)) -
        (price[b] + (b === preferred ? 0 : friction)));
      let seller = candidates[0] ?? -1;
      const demand = (quote) => {
        const continuous = M.demandAtPrice(latentQuantity, choke, quote, W.endEta[buyer]);
        return Math.min(qmax, Math.floor(continuous) + (rounding < continuous % 1 ? 1 : 0));
      };
      let desired = demand(seller < 0 ? reference : price[seller]);
      for (const candidate of candidates) {
        const requested = demand(price[candidate]);
        if (requested <= 0) break;
        W.t2Demand[candidate] += requested;
        W.t2RelAttempts[candidate]++;
        if (stock[candidate] >= requested) { seller = candidate; desired = requested; break; }
      }
      W.endLastMarket[buyer] = market; W.endLastSupplier[buyer] = seller;
      W.endLastQ[buyer] = desired;
      W.endActive[market] += desired; W.endPriceLost[market] += potentialQuantity - desired;
      if (desired <= 0) continue;
      orders++; W.t2Opportunities[market - NP]++;
      if (seller < 0 || stock[seller] < desired) { W.endStockUnmet[market] += desired; continue; }
      const payment = desired * price[seller];
      consumerPayments += payment;
      stock[seller] -= desired;
      W.t2Cash[W.t2LineFirm[seller]] += payment;
      W.t2LastSaleTick[W.t2LineFirm[seller]] = tick;
      W.t2Sold[seller] += desired; W.t2Revenue[seller] += payment; W.t2COGS[seller] += desired * W.t2FinBasis[seller];
      W.t2RelFulfilled[seller]++; W.t2RelAvailable[seller]++;
      W.endPreferredProduct[relationship] = market; W.endPreferredSupplier[relationship] = seller;
      W.endLastFulfilled[buyer] = desired; W.endFulfilled[market] += desired; filledOrders++;
    }
    return { orders, filledOrders, activated, consumerPayments };
  }

  function clearRetail(W, cfg, products, tick, t2Products) {
    return clearEndUsers(W, cfg, products, t2Products, tick);
  }

  function updateReliability(W, cfg, tick) {
    if (tick % MONTH !== 0) return;
    for (let i = 0; i < N0 * NE; i++)
      if (Number.isFinite(W.t0Price[i])) {
        const attempts = W.t0RelAttempts[i],
          checks = W.t0RelChecks[i],
          score = M.reliabilityScore(
            attempts ? W.t0RelFulfilled[i] / attempts : 1,
            W.t0RelPriceSamples[i] ? W.t0RelPriceSum[i] / W.t0RelPriceSamples[i] : 1,
            checks ? W.t0RelAvailable[i] / checks : 1,
          );
        W.t0Rel[i] = M.nextReliability(W.t0Rel[i], score, cfg.reliabilityAlpha);
        W.t0RelAttempts[i] =
          W.t0RelFulfilled[i] =
          W.t0RelChecks[i] =
          W.t0RelAvailable[i] =
          W.t0RelPriceSum[i] =
          W.t0RelPriceSamples[i] =
            0;
      }
    for (let i = 0; i < N1 * NP; i++)
      if (W.t1Operates[i]) {
        const attempts = W.t1RelAttempts[i],
          checks = W.t1RelAvailChecks[i],
          score = M.reliabilityScore(
            attempts ? W.t1RelFulfilled[i] / attempts : 1,
            W.t1RelPriceSamples[i] ? W.t1RelPriceSum[i] / W.t1RelPriceSamples[i] : 1,
            checks ? W.t1RelAvailable[i] / checks : 1,
          );
        W.t1Rel[i] = M.nextReliability(W.t1Rel[i], score, cfg.reliabilityAlpha);
        W.t1RelAttempts[i] =
          W.t1RelFulfilled[i] =
          W.t1RelAvailChecks[i] =
          W.t1RelAvailable[i] =
          W.t1RelPriceSum[i] =
          W.t1RelPriceSamples[i] =
            0;
      }
  }

  function observeMarkets(W, cfg, profiles) {
    // Research candidate only (off by default): wait for an informative amount
    // of market order traffic before judging a price experiment. Unit counts
    // cannot substitute for order counts when wholesale lots contain 1,000.
    const opportunityWeights = cfg.researchPriceMinimumOpportunities > 0 ? {
      t0: new Float64Array(NE), t1: new Float64Array(NP), t2: new Float64Array(M.T2_PRODUCTS.length)
    } : null;
    if (opportunityWeights) {
      for (const profile of profiles) for (const element of profile.elements)
        opportunityWeights.t0[M.ELEMENTS.indexOf(element)] += 1 / profile.elements.length;
      for (let i = 0; i < N1 * NP; i++) if (W.t1Operates[i]) opportunityWeights.t1[i % NP]++;
      for (let i = 0; i < W.t2LineCount; i++)
        opportunityWeights.t2[W.t2LineProduct[i]] += 1 / W.t2FirmLineCount[W.t2LineFirm[i]];
    }
    for (const [tier, count] of [['t0', N0 * NE], ['t1', N1 * NP], ['t2', W.t2LineCount]]) {
      const sales = W[`${tier}Sold`], demand = W[`${tier}Demand`], forecast = W[`${tier}DemandEMA`], actualSales = W[`${tier}SalesEMA`],
        revenue = W[tier === 't1' ? 't1Rev' : `${tier}Revenue`], cogs = W[`${tier}COGS`],
        profits = W[`${tier}LearnProfit`], quantities = W[`${tier}LearnSales`], ages = W[`${tier}LearnTicks`],
        requests = W[`${tier}LearnDemand`], stocks = W[`${tier}LearnStock`],
        held = W[tier === 't0' ? 't0Inv' : tier === 't1' ? 't1Fin' : 't2Fin'];
      for (let i = 0; i < count; i++) {
        if (tier === 't0' && !Number.isFinite(W.t0Price[i]) || tier === 't1' && !W.t1Operates[i]) continue;
        // Multiple supplier attempts are local lost orders, not additional
        // aggregate consumer purchases. Firms see their own inquiries only.
        forecast[i] += cfg.alpha * (Math.max(demand[i], sales[i]) - forecast[i]);
        actualSales[i] += cfg.alpha * (sales[i] - actualSales[i]);
        profits[i] += revenue[i] - cogs[i]; quantities[i] += sales[i]; ages[i]++;
        if (opportunityWeights) {
          const market = tier === 't0' ? i % NE : tier === 't1' ? i % NP : W.t2LineProduct[i];
          const weight = tier === 't0' ? 1 / profiles[Math.floor(i / NE)].elements.length :
            tier === 't1' ? 1 : 1 / W.t2FirmLineCount[W.t2LineFirm[i]];
          W[`${tier}LearnOpportunity`][i] += W[`${tier}Opportunities`][market] * weight / opportunityWeights[tier][market];
          if (tier === 't2') W.t2LearnPotentialOpportunity[i] += W.t2PotentialOrders[market] * weight / opportunityWeights.t2[market];
        }
        requests[i] += Math.max(demand[i], sales[i]); stocks[i] = held[i];
        if (tier === 't2') W.t2MonthSold[i] += sales[i];
      }
    }
  }

  function expandTier2Bots(W, cfg, t2Products, tick) {
    if (tick % MONTH !== 0) return;
    for (let line = 0; line < W.t2LineCount; line++) {
      const attempts = W.t2RelAttempts[line];
      const score = M.reliabilityScore(attempts ? W.t2RelFulfilled[line] / attempts : 1,
        W.t2RelPriceSamples[line] ? W.t2RelPriceSum[line] / W.t2RelPriceSamples[line] : 1, attempts ? W.t2RelAvailable[line] / attempts : 1);
      W.t2Rel[line] = M.nextReliability(W.t2Rel[line], score, cfg.reliabilityAlpha);
      W.t2RelAttempts[line] = W.t2RelFulfilled[line] = W.t2RelAvailable[line] = 0;
      W.t2RelPriceSum[line] = 0; W.t2RelPriceSamples[line] = 0;
    }
    for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
      let sold = 0, capacity = 0;
      for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++) {
        const line = W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot];
        sold += W.t2MonthSold[line]; capacity += W.t2MonthlyCapacity[line];
      }
      if (!W.t2Controller[firm] && W.t2FirmLineCount[firm] < M.T2_MAX_PRODUCTS_PER_FIRM && capacity > 0 && sold / capacity >= 0.75) {
        const eligible = t2Products.filter((p) => p.complexity <= W.t2Capability[firm] &&
          W.t2Sector[firm] === p.sectorIndex && !hasTier2Product(W, firm, p.id));
        const product = eligible[(firm + tick) % eligible.length];
        if (product && W.t2Cash[firm] >= product.equipmentPrice * 1.6) addTier2Line(W, cfg, firm, product);
      }
    }
    W.t2MonthSold.fill(0); W.t2MonthlyCapacity.fill(0);
  }

  function tick({ W, cfg, tick, products, profiles, state, t2Products }) {
    resetTick(W);
    W.costSinks = 0;
    W.equipmentSinks = 0;
    updateEnvironment(W, cfg, tick);
    produceTier0(W, cfg, profiles, tick);
    planAndBuyInputs(W, cfg, products, profiles, tick);
    manufacture(W, cfg, products);
    priceMarkets(W, cfg, profiles, products, tick);
    tier2BuyMakePrice(W, cfg, products, profiles, t2Products, tick);
    const counts = clearRetail(W, cfg, products, tick, t2Products);
    observeMarkets(W, cfg, profiles);
    updateReliability(W, cfg, tick);
    expandTier2Bots(W, cfg, t2Products, tick);
    state.activatedConsumers = counts.activated;
    state.consumerPayments = counts.consumerPayments;
    state.costSinks = W.costSinks;
    state.equipmentSinks = W.equipmentSinks;
    state.activeOrders = counts.orders;
    state.fulfilledOrders = counts.filledOrders;
  }
  root.Phase0ReferenceKernel = Object.freeze({ zero, tick, tier0Supplier, marketOffers, chooseSupplier, addTier2Line, hasTier2Product, tier2InventoryUnits, transferTier2Input, clearEndUsers, tier2BuyMakePrice, expandTier2Bots });
})(typeof self !== 'undefined' ? self : globalThis);
