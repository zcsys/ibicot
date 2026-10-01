/* Source-first Phase 0 economy kernel.  This is intentionally plain JS so
 * every economic rule is editable and testable. */
(function (root) {
  'use strict';
  const M = root.Phase0Model;
  const NE = 4, NP = 10, N0 = 20, N1 = 1000, N2 = 50000, MONTH = 30;
  const clamp = M.clamp;
  const mix = value => { value >>>= 0; value = Math.imul(value ^ (value >>> 16), 0x85ebca6b); value = Math.imul(value ^ (value >>> 13), 0xc2b2ae35); return (value ^ (value >>> 16)) >>> 0; };
  const random = (seed, tick, stream) => mix((seed >>> 0) ^ Math.imul((tick + 1) >>> 0, 0x9e3779b1) ^ Math.imul((stream + 1) >>> 0, 0x85ebca6b)) / 4294967296;
  const normal = (seed, tick, stream) => Math.sqrt(-2 * Math.log(Math.max(1e-12, random(seed, tick, stream)))) * Math.cos(2 * Math.PI * random(seed, tick, stream + 1));
  const sum = array => { let value = 0; for (let i = 0; i < array.length; i++) value += array[i] || 0; return value; };
  const finite = value => Number.isFinite(value) ? value : 0;

  function zero(W) { for (const value of Object.values(W)) if (value && typeof value.fill === 'function') value.fill(0); }

  function resetTick(W) {
    for (const name of ['t0Sold', 't0Revenue', 't1Sold', 't1Rev', 't1COGS', 'active', 'potential', 'fulfilled', 'priceLost', 'stockUnmet', 't0Ful', 't1InputNeed', 't1PurchaseReq']) W[name].fill(0);
  }

  function updateGaia(W, cfg, tick) {
    for (let e = 0; e < NE; e++) W.difficulty[e] = clamp(W.difficulty[e] + cfg.theta * (cfg.dbar - W.difficulty[e]) + cfg.sigma * normal(cfg.seed, tick, e * 4), cfg.dmin, cfg.dmax);
  }

  function produceTier0(W, cfg, profiles) {
    for (let supplier = 0; supplier < N0; supplier++) {
      const elements = profiles[supplier].elements.map(element => M.ELEMENTS.indexOf(element));
      const totalRequest = elements.reduce((total, e) => total + Math.max(0, W.t0Req[e]), 0);
      let capacity = Math.max(0, cfg.capacity);
      for (let n = 0; n < elements.length; n++) {
        const e = elements[n], index = supplier * NE + e, cost = Math.max(1e-9, cfg.baseCost * W.difficulty[e]);
        W.t0Cost[index] = cost;
        const share = totalRequest > 0 ? Math.max(0, W.t0Req[e]) / totalRequest : 1 / elements.length;
        const planned = n === elements.length - 1 ? capacity : Math.floor(capacity * share);
        const headroom = Math.max(0, cfg.maxInventory - W.t0Inv[index]);
        const affordable = Math.floor(Math.max(0, W.t0Cash[supplier]) / cost);
        const made = Math.max(0, Math.min(planned, headroom, affordable));
        W.t0Inv[index] += made; W.t0Cash[supplier] -= made * cost; capacity -= made;
        if (!Number.isFinite(W.t0Price[index]) || W.t0Price[index] <= 0) W.t0Price[index] = cost * (1 + cfg.markup);
      }
    }
  }

  function planAndBuyInputs(W, cfg, products, profiles, tick) {
    W.t0Req.fill(0);
    // Interleave cohorts instead of processing all firms in cohort order.
    // This gives every product market a recurring chance to buy each input,
    // rather than letting whichever cohort is first drain a shared element.
    const firstCohort = tick % NP, firstFirm = (tick * 37) % 100;
    for (let round = 0; round < 100; round++) for (let cohortOrder = 0; cohortOrder < NP; cohortOrder++) {
      const cohort = (firstCohort + cohortOrder) % NP;
      const company = cohort * 100 + (firstFirm + round) % 100;
      const rawBase = company * NE, productBase = company * NP;
      for (let p = 0; p < NP; p++) {
        if (!W.t1Operates[productBase + p]) continue;
        const product = products[p], cap = Object.keys(product.inputs).length === 1 ? cfg.basicEquipmentCapacity : cfg.compoundEquipmentCapacity;
        const desired = Math.max(0, Math.min(cap, cfg.retailTargetInventory - W.t1Fin[productBase + p], Math.ceil(W.t1SalesEMA[productBase + p])));
        for (const [element, ratio] of Object.entries(product.inputs)) {
          const e = M.ELEMENTS.indexOf(element), need = Math.max(0, desired * ratio - W.raw[rawBase + e]);
          if (need > 0) W.t1InputNeed[rawBase + e] += Math.max(need, cfg.minWholesaleLot);
        }
      }
      for (let e = 0; e < NE; e++) {
        const need = W.t1InputNeed[rawBase + e];
        if (need <= 0) continue;
        const request = Math.ceil(need / cfg.minWholesaleLot) * cfg.minWholesaleLot;
        W.t1PurchaseReq[rawBase + e] = request; W.t0Req[e] += request;
        const preferred = W.preferredWholesale[rawBase + e];
        let chosen = -1, best = Infinity;
        for (let supplier = 0; supplier < N0; supplier++) {
          if (!profiles[supplier].elements.includes(M.ELEMENTS[e])) continue;
          const index = supplier * NE + e, quote = W.t0Price[index], available = Math.floor(Math.max(0, W.t0Inv[index]));
          // Do not let an empty low-price supplier block access to other
          // stocked suppliers in the same element market.
          if (!Number.isFinite(quote) || available < cfg.minWholesaleLot) continue;
          const friction = supplier === preferred ? 0 : M.switchingCost(preferred >= 0 ? W.t0Rel[preferred * NE + e] : .5, cfg.taumin, cfg.taumax);
          if (quote + friction < best) { best = quote + friction; chosen = supplier; }
        }
        if (chosen < 0) continue;
        const supplierIndex = chosen * NE + e, quote = Math.max(0, W.t0Price[supplierIndex]);
        const affordable = Math.floor(Math.max(0, W.t1Cash[company]) / Math.max(1e-9, quote));
        const available = Math.floor(Math.max(0, W.t0Inv[supplierIndex]));
        const bought = Math.floor(Math.min(request, affordable, available) / cfg.minWholesaleLot) * cfg.minWholesaleLot;
        const attempt = request > 0 ? 1 : 0;
        W.t0RelAttempts[supplierIndex] += attempt; W.t0RelFulfilled[supplierIndex] += bought >= request ? attempt : 0;
        W.t0RelChecks[supplierIndex] += attempt; W.t0RelAvailable[supplierIndex] += available >= request ? attempt : 0;
        if (bought <= 0) continue;
        const oldRaw = W.raw[rawBase + e], oldBasis = W.rawBasis[rawBase + e], payment = bought * quote;
        W.raw[rawBase + e] = oldRaw + bought;
        W.rawBasis[rawBase + e] = oldRaw + bought > 0 ? (oldBasis * oldRaw + payment) / (oldRaw + bought) : 0;
        W.t1LastBuy[rawBase + e] = quote; W.t1Cash[company] -= payment;
        W.t0Cash[chosen] += payment; W.t0Inv[supplierIndex] -= bought; W.t0Sold[supplierIndex] += bought; W.t0Revenue[supplierIndex] += payment; W.t0Ful[e] += bought;
        W.preferredWholesale[rawBase + e] = chosen;
      }
    }
  }

  function manufacture(W, cfg, products) {
    for (let company = 0; company < N1; company++) for (let p = 0; p < NP; p++) {
      const index = company * NP + p; if (!W.t1Operates[index]) continue;
      const product = products[p], rawBase = company * NE;
      let made = Math.min(Object.keys(product.inputs).length === 1 ? cfg.basicEquipmentCapacity : cfg.compoundEquipmentCapacity, Math.max(0, cfg.retailTargetInventory - W.t1Fin[index]));
      let inputCost = 0;
      for (const [element, ratio] of Object.entries(product.inputs)) { const e = M.ELEMENTS.indexOf(element); made = Math.min(made, Math.floor(W.raw[rawBase + e] / ratio)); inputCost += ratio * W.rawBasis[rawBase + e]; }
      made = Math.min(made, Math.floor(Math.max(0, W.t1Cash[company]) / Math.max(1e-9, cfg.manufacturingCostPerUnit)));
      if (made <= 0) continue;
      for (const [element, ratio] of Object.entries(product.inputs)) { const e = M.ELEMENTS.indexOf(element); W.raw[rawBase + e] -= made * ratio; }
      W.t1Cash[company] -= made * cfg.manufacturingCostPerUnit;
      const oldFin = W.t1Fin[index], oldBasis = W.t1FinBasis[index], unitCost = inputCost + cfg.manufacturingCostPerUnit;
      W.t1Fin[index] = oldFin + made; W.t1FinBasis[index] = oldFin + made > 0 ? (oldBasis * oldFin + unitCost * made) / (oldFin + made) : 0; W.t1UnitCost[index] = unitCost;
    }
  }

  function priceMarkets(W, cfg) {
    for (let supplier = 0; supplier < N0; supplier++) for (let e = 0; e < NE; e++) {
      const index = supplier * NE + e; if (!Number.isFinite(W.t0Price[index])) continue;
      const previous = W.t0Price[index], next = M.wholesalePrice({ oldPrice: previous, unitCost: W.t0Cost[index], request: W.t0Req[e], fulfilled: W.t0Ful[e], k: cfg.k, minMargin: cfg.minMargin, vmax: cfg.vmax });
      W.t0PrevPrice[index] = previous; W.t0Price[index] = next; const stable = 1 - Math.min(1, Math.abs(next - previous) / Math.max(1e-9, previous) / Math.max(1e-9, cfg.switchingStableBand)); W.t0Stability[index] = stable; W.t0RelPriceSum[index] += stable; W.t0RelPriceSamples[index]++;
    }
    for (let company = 0; company < N1; company++) for (let p = 0; p < NP; p++) {
      const index = company * NP + p; if (!W.t1Operates[index]) continue; const previous = W.t1Price[index], unit = Math.max(0, W.t1FinBasis[index] || W.t1UnitCost[index]);
      const next = W.t1Controller[company] && Number.isFinite(W.playerPrice[index]) ? Math.max(W.playerPrice[index], unit * (1 + cfg.minMargin)) : M.retailBotPrice({ oldPrice: previous, finishedCost: unit, stock: W.t1Fin[index], salesEMA: W.t1SalesEMA[index], k: cfg.k, minMargin: cfg.minMargin, vmax: cfg.vmax });
      W.t1PrevPrice[index] = previous; W.t1Price[index] = next; const stable = 1 - Math.min(1, Math.abs(next - previous) / Math.max(1e-9, previous) / Math.max(1e-9, cfg.switchingStableBand)); W.t1PriceStability[index] = stable; W.t1RelPriceSum[index] += stable; W.t1RelPriceSamples[index]++;
    }
  }

  function clearRetail(W, cfg, products, tick) {
    const cheapest = new Int32Array(NP); cheapest.fill(-1);
    // Buyers can only fall back to a supplier that can actually fulfill an
    // order.  Otherwise an empty low-price firm captures all demand while
    // stocked producers, especially in compound markets, never make a sale.
    for (let p = 0; p < NP; p++) for (let company = 0; company < N1; company++) { const index = company * NP + p; if (W.t1Operates[index] && W.t1Fin[index] > 0 && (cheapest[p] < 0 || W.t1Price[index] < W.t1Price[cheapest[p] * NP + p])) cheapest[p] = company; }
    let orders = 0, filledOrders = 0;
    for (let buyer = 0; buyer < N2; buyer++) {
      const preferred = W.buyerPreferred[buyer], p = Math.floor(preferred / 100), fallback = cheapest[p]; let seller = preferred;
      if (seller < 0 || !W.t1Operates[seller * NP + p] || W.t1Fin[seller * NP + p] <= 0) seller = fallback;
      if (seller < 0) continue;
      const preferredPrice = W.t1Price[seller * NP + p];
      if (fallback >= 0 && fallback !== seller) { const effectiveFallback = W.t1Price[fallback * NP + p] + M.switchingCost(W.t1Rel[seller * NP + p], cfg.taumin, cfg.taumax); if (effectiveFallback < preferredPrice) seller = fallback; }
      const index = seller * NP + p, price = W.t1Price[index], qMax = W.buyerQMax[buyer], continuous = M.demandAtPrice(qMax, W.buyerChoke[buyer], price, W.buyerEta[buyer]);
      const desired = Math.max(0, Math.min(qMax, Math.floor(continuous) + (random(cfg.seed, tick, buyer + 900000) < continuous - Math.floor(continuous) ? 1 : 0)));
      W.buyerChosenSupplier[buyer] = seller; W.buyerEffectivePrice[buyer] = price; W.buyerLastQ[buyer] = desired; W.potential[p] += qMax; W.active[p] += desired; W.priceLost[p] += qMax - desired;
      if (desired <= 0) continue; orders++; W.t1RelAttempts[index]++; W.t1RelAvailChecks[index]++;
      if (W.t1Fin[index] + 1e-9 < desired) { W.stockUnmet[p] += desired; continue; }
      const cost = W.t1FinBasis[index], revenue = desired * price; W.t1Fin[index] -= desired; W.t1FinBasis[index] = W.t1Fin[index] > 0 ? cost : 0; W.t1Cash[seller] += revenue; W.t1Sold[index] += desired; W.t1Rev[index] += revenue; W.t1COGS[index] += desired * cost; W.fulfilled[p] += desired; filledOrders++; W.t1RelFulfilled[index]++; W.t1RelAvailable[index]++; W.buyerPreferred[buyer] = seller;
    }
    return { orders, filledOrders };
  }

  function updateReliability(W, cfg, tick) {
    for (let i = 0; i < N1 * NP; i++) if (W.t1Operates[i]) W.t1SalesEMA[i] = cfg.alpha * W.t1Sold[i] + (1 - cfg.alpha) * W.t1SalesEMA[i];
    if (tick % MONTH !== 0) return;
    for (let i = 0; i < N0 * NE; i++) if (Number.isFinite(W.t0Price[i])) { const attempts = W.t0RelAttempts[i], checks = W.t0RelChecks[i], score = M.reliabilityScore(attempts ? W.t0RelFulfilled[i] / attempts : 1, W.t0RelPriceSamples[i] ? W.t0RelPriceSum[i] / W.t0RelPriceSamples[i] : 1, checks ? W.t0RelAvailable[i] / checks : 1); W.t0Rel[i] = M.nextReliability(W.t0Rel[i], score, cfg.reliabilityAlpha); W.t0RelAttempts[i] = W.t0RelFulfilled[i] = W.t0RelChecks[i] = W.t0RelAvailable[i] = W.t0RelPriceSum[i] = W.t0RelPriceSamples[i] = 0; }
    for (let i = 0; i < N1 * NP; i++) if (W.t1Operates[i]) { const attempts = W.t1RelAttempts[i], checks = W.t1RelAvailChecks[i], score = M.reliabilityScore(attempts ? W.t1RelFulfilled[i] / attempts : 1, W.t1RelPriceSamples[i] ? W.t1RelPriceSum[i] / W.t1RelPriceSamples[i] : 1, checks ? W.t1RelAvailable[i] / checks : 1); W.t1Rel[i] = M.nextReliability(W.t1Rel[i], score, cfg.reliabilityAlpha); W.t1RelAttempts[i] = W.t1RelFulfilled[i] = W.t1RelAvailChecks[i] = W.t1RelAvailable[i] = W.t1RelPriceSum[i] = W.t1RelPriceSamples[i] = 0; }
  }

  function tick({ W, cfg, tick, products, profiles, state }) { resetTick(W); updateGaia(W, cfg, tick); produceTier0(W, cfg, profiles); planAndBuyInputs(W, cfg, products, profiles, tick); manufacture(W, cfg, products); priceMarkets(W, cfg); const counts = clearRetail(W, cfg, products, tick); updateReliability(W, cfg, tick); state.activeOrders = counts.orders; state.fulfilledOrders = counts.filledOrders; }
  root.Phase0ReferenceKernel = Object.freeze({ zero, tick });
})(typeof self !== 'undefined' ? self : globalThis);
