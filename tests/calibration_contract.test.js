'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const { W, cfg } = worker.inspect(), M = worker.model;
for (const [key, value] of Object.entries(M.ECONOMY_DEFAULTS)) assert.equal(cfg[key], value, key);
assert.equal(cfg.initialCash, 1000000);
assert.equal(cfg.capacity,10000); assert.equal(cfg.targetInventory,500000); assert.equal(cfg.maxInventory,1000000);
assert.equal(cfg.minWholesaleLot, 1000);
assert.deepEqual([3,4,5].map(M.t2Capacity), [6,6,6]);
assert.equal(M.T1_BASIC_MACHINERY, 15000); assert.equal(M.T1_COMPOUND_MACHINERY, 75000); assert.equal(M.T2_ROUTE_SETUP, 1000);
const target = (salesEMA) => M.finishedStockTarget({ salesEMA, coverageTicks: 3,
  bootstrapStock: 3, capacity: 3, targetInventory: 6, maxInventory: 6 });
assert.equal(target(0), 3); assert.equal(target(1.5), 5); assert.equal(target(100), 6);
assert.equal(M.finishedStockTarget({ salesEMA: 100, coverageTicks: 3, bootstrapStock: 16,
  capacity: 160, targetInventory: 600, maxInventory: 1200 }), 300);
for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
  const portfolio = Array.from({ length: W.t2FirmLineCount[firm] }, (_, slot) =>
    M.T2_PRODUCTS[W.t2LineProduct[W.t2FirmLines[firm * M.T2_MAX_PRODUCTS_PER_FIRM + slot]]]);
  assert.equal(W.t2Cash[firm], M.tier2StartingCash(portfolio, cfg));
  assert.ok(W.t2Cash[firm] >= cfg.tier2MinimumCash);
  assert.equal(W.t2EqBook[firm], portfolio.reduce((sum, p) => sum + p.equipmentPrice, 0), 'Tier 2 equipment is the sum of its owned routes');
  assert.ok(M.tier2StartingCash(portfolio, { ...cfg, baseCost: 10 }) > W.t2Cash[firm]);
}
// Execute the actual browser configuration reader. Check every model default,
// catching invisible UI overrides as well as stale initial HTML values.
const html = fs.readFileSync('phase0_economy_engine.html', 'utf8');
const app = fs.readFileSync('phase0_economy_engine_app.js', 'utf8');
const fields = Object.fromEntries([...html.matchAll(/<input\b[^>]*id="([^"]+)"[^>]*value="([^"]*)"[^>]*>/g)]
  .map((match) => [match[1], { value: match[2] }]));
const begin = app.indexOf('  const PARAMS = ['), end = app.indexOf('  for (let i = 0; i < 1000;', begin);
const context = { M, $: (id) => fields[id], Object };
vm.runInNewContext(app.slice(begin, end) + '\nthis.actualCfg = readCfg();', context);
for (const [key, value] of Object.entries(M.ECONOMY_DEFAULTS)) assert.equal(context.actualCfg[key], value, `UI ${key}`);
for (let tick = 0; tick < 60; tick++) worker.step();
assert.ok(W.t2Cash.every((cash) => Number.isFinite(cash) && cash >= 0));
// Wholesale transfers require funded, stocked 1,000-unit lots. Isolate Tier 1
// procurement so a sub-lot cash balance or stock cannot masquerade as a trade.
const wholesale = createWorker({ t2FirmCount: 1, endUserCount: 1,
  consumerActivation: 0, capacity: 0, sigma: 0 });
const R = wholesale.inspect().W;
R.t2FirmLineCount.fill(0); R.t1Cash.fill(0);
R.t1Cash[0] = 5000; R.t0Inv.fill(999);
wholesale.step();
assert.equal(R.t1Bought[0], 0, 'Stock below a wholesale lot cannot be delivered');
assert.equal(R.t0FundedReq.reduce((a,b)=>a+b,0), 1000);
R.t0Inv.fill(1000); R.t1Cash[0] = 999 * R.t0Price[0];
wholesale.step();
assert.equal(R.t1Bought[0], 0, 'Cash below the cost of a lot cannot buy fractions');
assert.equal(R.t0FundedReq.reduce((a,b)=>a+b,0), 0);
R.t1Cash[0] = 5000;
wholesale.step();
assert.equal(R.t1Bought[0], 1000);
assert.ok(R.raw[0] > 0 && R.t1Fin[0] > 0, 'Lot remainder buffers future production');
// Default compound-refinery cash covers both ingredient lots and conversion.
R.t1Cash.fill(0); R.t1Cash[400] = cfg.retailInitialCash; R.t0Inv.fill(1000);
wholesale.step();
assert.equal(R.t1Bought[400], 2000);
assert.ok(R.t1Cash[400] > 0 && R.t1Fin[400 * 10 + 4] > 0);
console.log('calibration defaults, 1,000-unit wholesale lots and compound cash reserves: ok');
