'use strict';

// Full-population financial and inventory audit, not a reduced/alternate model.
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const { createWorker } = require('./worker_harness');
const fs = require('node:fs');
const path = require('node:path');
const { createPriceAudit, assertPriceHealth } = require('./price_audit_helpers');
const ticks = Number(process.env.BALANCE_TICKS || 3600);
const seed = Number(process.env.BALANCE_SEED || 12345);
const initialCash = Number(process.env.BALANCE_T0_CASH || 1000000);
assert.ok(Number.isInteger(ticks) && ticks >= 720 && ticks % 360 === 0);
let priceAudit;
const worker = createWorker({ seed, initialCash }, { onBeforeTier0Reprice: W => priceAudit.onBeforeTier0Reprice(W) });
const { W, cfg } = worker.inspect(), model = worker.model;
assert.equal(cfg.endUserCount, 1000000);
assert.equal(cfg.t2FirmCount, 50000);
priceAudit = createPriceAudit(model, cfg, { windowStart: ticks - 360 + 1, windowTicks: 360 });
const sum = (a) => a.reduce((n, x) => n + x, 0);
const allCash = () => sum(W.t0Cash) + sum(W.t1Cash) + sum(W.t2Cash);
const sums = (names) => Object.fromEntries(names.map((name) => [name, sum(W[name])]));
const firmCash = (a) => ({ minimum: Math.min(...a), maximum: Math.max(...a),
  nearZero: a.reduce((n, x) => n + (x < 1), 0), total: sum(a) });
const window = { productSales: new Float64Array(model.T2_PRODUCTS.length),
  productProduction: new Float64Array(model.T2_PRODUCTS.length), materialSales: new Float64Array(10),
  materialProduction: new Float64Array(10), firmSales: new Float64Array(cfg.t2FirmCount),
  t0Production: new Float64Array(4), t0Sales: new Float64Array(4),
  t2Made: 0, t2Sold: 0, t2Capacity: 0, desired: 0, fulfilled: 0,
  revenue: 0, cogs: 0, consumerPayments: 0, costSinks: 0, equipmentSinks: 0 };
const initialTotalCash = allCash(), reports = [];
let injections = 0, sinks = 0, equipment = 0, maximumLedgerError = 0;
const started = performance.now();

for (let tick = 1; tick <= ticks; tick++) {
  const beforeT0 = W.t0Inv.slice(), beforeT1 = W.t1Fin.slice();
  priceAudit.begin(tick, W);
  worker.step();
  priceAudit.end(W);
  const state = worker.inspect().sourceState;
  injections += state.consumerPayments;
  sinks += state.costSinks;
  equipment += state.equipmentSinks;
  window.consumerPayments += state.consumerPayments;
  window.costSinks += state.costSinks;
  window.equipmentSinks += state.equipmentSinks;
  window.desired += sum(W.endActive);
  window.fulfilled += sum(W.endFulfilled);
  for (let index = 0; index < W.t0Inv.length; index++)
    window.t0Production[index % 4] += W.t0Inv[index] - beforeT0[index];
  // Resource sales count Tier 1 refinery transfers once. Tier 2 purchases
  // processed materials from Tier 1 and never adds a second Tier 0 phase.
  for (let index = 0; index < W.t0Sold.length; index++) {
    window.t0Sales[index % 4] += W.t0Sold[index];
    window.t0Production[index % 4] += W.t0Sold[index];
  }
  for (let index = 0; index < W.t1Fin.length; index++) {
    const market = index % 10;
    window.materialSales[market] += W.t1Sold[index];
    window.materialProduction[market] += Math.max(0, W.t1Fin[index] - beforeT1[index] + W.t1Sold[index]);
  }
  for (let line = 0; line < W.t2LineCount; line++) {
    const product = model.T2_PRODUCTS[W.t2LineProduct[line]], sold = W.t2Sold[line];
    window.productSales[product.id] += sold;
    window.productProduction[product.id] += W.t2Made[line];
    window.firmSales[W.t2LineFirm[line]] += sold;
    window.t2Made += W.t2Made[line]; window.t2Sold += sold;
    window.t2Capacity += product.capacity;
    window.revenue += W.t2Revenue[line]; window.cogs += W.t2COGS[line];
  }
  if (tick % 30 === 0) {
    const error = Math.abs(allCash() - (initialTotalCash + injections - sinks - equipment));
    maximumLedgerError = Math.max(maximumLedgerError, error);
    assert.ok(error < 1, `Cumulative cash ledger error at ${tick}: ${error}`);
    for (const name of ['t0Inv','t0Cash','raw','t1Fin','t1Cash','t2Cash','t2Raw','t2T1Raw','t2Fin'])
      for (const x of W[name]) assert.ok(Number.isFinite(x) && x >= -1e-7, `${name}: ${x}`);
    for (let firm = 0; firm < 20; firm++) {
      let stock = 0;
      for (let e = 0; e < 4; e++) stock += W.t0Inv[firm * 4 + e];
      assert.ok(stock <= cfg.maxInventory + 1e-7, `Tier 0 warehouse exceeded: ${firm}`);
      assert.ok(stock <= cfg.targetInventory + 1e-7, `Tier 0 target exceeded: ${firm}`);
    }
    for (let index = 0; index < W.t1Fin.length; index++) {
      assert.ok(W.t1Fin[index] <= cfg.retailTargetInventory + 1e-7);
      assert.ok(W.t1Fin[index] <= cfg.retailMaxInventory + 1e-7);
      if (W.t1Operates[index]) assert.ok(W.t1Price[index] + 1e-7 >=
        (W.t1FinBasis[index] || W.t1UnitCost[index]));
    }
    for (let line = 0; line < W.t2LineCount; line++) {
      const p = model.T2_PRODUCTS[W.t2LineProduct[line]];
      assert.ok(W.t2Fin[line] <= 2 * p.capacity + 1e-7);
      assert.ok(W.t2Price[line] + 1e-7 >= (W.t2FinBasis[line] || W.t2UnitCost[line]));
    }
  }
  if (tick % 360 === 0) {
    assert.ok(window.productSales.every((q) => q > 0), `Inactive final market at ${tick}`);
    assert.ok(window.productProduction.every((q) => q > 0), `No final production at ${tick}`);
    assert.ok(window.materialSales.every((q) => q > 0), `Inactive material market at ${tick}`);
    assert.ok(window.materialProduction.every((q) => q > 0), `No material production at ${tick}`);
    assert.ok(window.t0Sales.every((q) => q > 0));
    assert.ok(window.fulfilled / window.desired > 0.5);
    if (tick >= 720) {
      const utilization = window.t2Made / window.t2Capacity;
      const participation = window.firmSales.reduce((n, q) => n + (q > 0), 0) / cfg.t2FirmCount;
      assert.ok(utilization >= 0.10 && utilization <= 0.65, `Insufficient trading or no player headroom: ${utilization}`);
      assert.ok(participation >= 0.60, `Most bot firms are stranded: ${participation}`);
      assert.ok(sum(W.t2Fin) / (window.t2Sold / 360) <= 12, 'Excess final-good sales coverage');
      assert.ok(sum(W.t1Fin) / (sum(window.materialSales) / 360) <= 10, 'Excess material sales coverage');
      assert.ok(sum(W.t0Inv) / (sum(window.t0Sales) / 360) <= 10, 'Excess upstream sales coverage');
      assert.ok(window.revenue > window.cogs, 'Manufacturing must earn positive realized gross profit');
    }
    const snapshot = worker.snapshot();
    const report = { tick, seed, initialCash, lines: W.t2LineCount,
      cash: { t0: firmCash(W.t0Cash), t1: firmCash(W.t1Cash), t2: firmCash(W.t2Cash) },
      stock: sums(['t0Inv','raw','t1Fin','t2Raw','t2T1Raw','t2Fin']),
      window: { unitFill: window.fulfilled / window.desired,
        consumerUnitsPerTick: window.fulfilled / 360,
        t0ProductionPerTick: sum(window.t0Production) / 360,
        t0SalesPerTick: sum(window.t0Sales) / 360,
        t1ProductionPerTick: sum(window.materialProduction) / 360,
        t2ProductionPerTick: window.t2Made / 360,
        t2SalesPerTick: window.t2Sold / 360,
        t2Utilization: window.t2Made / window.t2Capacity,
        t2TradingFirms: window.firmSales.reduce((n, q) => n + (q > 0), 0),
        t2GrossMargin: (window.revenue - window.cogs) / window.revenue,
        consumerPaymentsPerTick: window.consumerPayments / 360,
        costSinksPerTick: window.costSinks / 360 },
      realizedMarginsByComplexity: snapshot.tier2Complexity.map((band) => ({ name: band.name, margin: band.margin })),
      maximumLedgerError, averageTickMs: (performance.now() - started) / tick };
    reports.push(report);
    console.log(JSON.stringify(report));
    for (const [key, value] of Object.entries(window)) {
      if (typeof value === 'number') window[key] = 0;
      else value.fill(0);
    }
  }
}
const pricing = priceAudit.report();
let priceFailure;
try { assertPriceHealth(pricing); } catch (error) { priceFailure = error; }
const finalReport = { result: priceFailure ? 'FAIL_PRICING' : 'PASS_ACCOUNTING_MARKET_BALANCE_AND_PRICING', seed, initialCash, ticks,
  allProductAndMaterialMarketsActive: true,
  productMarkets: model.T2_PRODUCTS.length, materialMarkets: model.PRODUCTS.length,
  maximumLedgerError, windows: reports, lastWindow: reports.at(-1), pricing };
const output = path.resolve(process.env.BALANCE_OUTPUT || `reports/scarcity-aware-${seed}-${ticks}.json`);
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(finalReport, null, 2) + '\n');
if (priceFailure) throw priceFailure;
console.log(JSON.stringify({ ...finalReport, pricing: pricing.byTier, windows: undefined, output }));
