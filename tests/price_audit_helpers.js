'use strict';
const assert = require('node:assert/strict');

function createPriceAudit(model, cfg, { windowStart, windowTicks }) {
  const minimumUnitPrice = model.MIN_UNIT_PRICE;
  const markets = [
    ...model.ELEMENTS.map((name, id) => ({ tier: 0, id, name })),
    ...model.PRODUCTS.map((p, id) => ({ tier: 1, id, name: p.name })),
    ...model.T2_PRODUCTS.map((p) => ({ tier: 2, id: p.id, name: p.name, complexity: p.complexity })),
  ].map((m) => ({ ...m, units: 0, revenue: 0, floorUnits: 0, nearFloorUnits: 0,
    floorTicks: 0, dominantFloorTicks: 0, minTradedPrice: Infinity, maxTradedPrice: -Infinity,
    floorDistanceWeighted: 0 }));
  let currentTick = 0, oldPrices, oldCosts, beforeRepricing, prior;
  const add = (m, units, revenue, quote, floor) => {
    if (units <= 1e-7) return;
    assert.ok(Number.isFinite(quote) && Number.isFinite(floor) && floor > 0);
    assert.ok(Math.abs(revenue - units * quote) <= 1e-7 * Math.max(1, revenue),
      'Audit must attribute revenue to the actual transaction quote');
    m.units += units; m.revenue += revenue;
    m.minTradedPrice = Math.min(m.minTradedPrice, quote);
    m.maxTradedPrice = Math.max(m.maxTradedPrice, quote);
    if (Math.abs(quote-floor) <= 1e-8 * Math.max(1,quote,floor)) m.floorUnits += units;
    if (quote <= floor * 1.01) m.nearFloorUnits += units;
    m.floorDistanceWeighted += units * (quote / floor - 1);
  };
  return {
    begin(tick, W) {
      currentTick = tick;
      if (tick < windowStart) return;
      oldPrices = W.t0Price.slice(); oldCosts = W.t0Cost.map((cost,i)=>Math.max(minimumUnitPrice,cost,W.t0InvBasis[i]));
      prior = markets.map((m) => [m.units, m.floorUnits]);
    },
    onBeforeTier0Reprice(W) {
      if (currentTick < windowStart) return;
      beforeRepricing = { sold: W.t0Sold.slice(), revenue: W.t0Revenue.slice() };
    },
    end(W) {
      if (currentTick < windowStart) return;
      for (let i=0;i<W.t0Price.length;i++) {
        if (!Number.isFinite(W.t0Price[i])) continue;
        add(markets[i%4], beforeRepricing.sold[i], beforeRepricing.revenue[i], oldPrices[i], oldCosts[i]);
        add(markets[i%4], W.t0Sold[i]-beforeRepricing.sold[i], W.t0Revenue[i]-beforeRepricing.revenue[i], W.t0Price[i], Math.max(minimumUnitPrice,W.t0Cost[i],W.t0InvBasis[i]));
      }
      for (let i=0;i<W.t1Price.length;i++) if (W.t1Operates[i])
        add(markets[4+i%10], W.t1Sold[i], W.t1Rev[i], W.t1Price[i], Math.max(minimumUnitPrice,W.t1FinBasis[i]||W.t1UnitCost[i]));
      for (let i=0;i<W.t2LineCount;i++) {
        // Receipts can precede later changes to blended inventory bases.
        // Receipts and actual COGS retain the cost/quote of the delivered units.
        add(markets[14+W.t2LineProduct[i]], W.t2Sold[i], W.t2Revenue[i],
          W.t2Sold[i] ? W.t2Revenue[i]/W.t2Sold[i] : W.t2Price[i],
          W.t2Sold[i] ? W.t2COGS[i]/W.t2Sold[i] : Math.max(minimumUnitPrice,W.t2FinBasis[i]||W.t2UnitCost[i]));
      }
      markets.forEach((m,i) => {
        const units=m.units-prior[i][0], floor=m.floorUnits-prior[i][1];
        if (floor>1e-7) m.floorTicks++;
        if (units>0 && floor/units>=0.95) m.dominantFloorTicks++;
      });
    },
    report() {
      const results=markets.map((m) => {
        const perUnit=(value)=>m.units>0?value/m.units:null;
        return { ...m, averageTradedPrice:perUnit(m.revenue), floorShare:perUnit(m.floorUnits),
          nearFloorShare:perUnit(m.nearFloorUnits), averageFloorDistance:perUnit(m.floorDistanceWeighted),
          hasCeiling:false };
      });
      return { expectedMarketCount: markets.length, windowStart, windowTicks, priceModel:'scarcity-aware-adaptive-experiments',
        boundaryMeaning:'Variable-cost break-even reservation; no guaranteed markup or ceiling. Concentration is diagnostic, not an automatic model failure.',
        config:{priceObservationTicks:cfg.priceObservationTicks,startingMarkup:cfg.markup,consumerSearchOffers:cfg.consumerSearchOffers},
        inactiveMarkets:results.filter(m=>!m.units).map(m=>({tier:m.tier,name:m.name})),
        byTier:[0,1,2].map(tier=>{
          const ms=results.filter(m=>m.tier===tier), sum=key=>ms.reduce((n,m)=>n+m[key],0), units=sum('units');
          return {tier,markets:ms.length,units,floorShare:units?sum('floorUnits')/units:null,
            nearFloorShare:units?sum('nearFloorUnits')/units:null,
            marketsWithFloorTrades:ms.filter(m=>m.floorUnits>0).length,hasCeiling:false};
        }),markets:results };
    },
  };
}

function assertPriceHealth(report) {
  assert.ok(Number.isInteger(report.expectedMarketCount) && report.expectedMarketCount > 0);
  assert.equal(report.markets.length,report.expectedMarketCount,'Complete catalogue audit');
  assert.equal(report.inactiveMarkets.length,0,'Every market must trade');
  for (const m of report.markets) {
    assert.ok(m.units>0,`Inactive market: T${m.tier} ${m.name}`);
    assert.ok(Number.isFinite(m.averageTradedPrice) && m.averageTradedPrice>0,`Invalid traded price: ${m.name}`);
    assert.ok(Number.isFinite(m.averageFloorDistance) && m.averageFloorDistance>=-1e-7,`Below-cost default trading: ${m.name}`);
    assert.ok(m.floorShare>=0 && m.floorShare<=1 && m.nearFloorShare>=0 && m.nearFloorShare<=1,`Invalid boundary attribution: ${m.name}`);
  }
}
module.exports={createPriceAudit,assertPriceHealth};
