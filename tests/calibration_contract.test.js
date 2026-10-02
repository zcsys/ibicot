'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const { W, cfg } = worker.inspect(), M = worker.model;
for (const [key, value] of Object.entries(M.ECONOMY_DEFAULTS)) assert.equal(cfg[key], value, key);
assert.equal(cfg.initialCash, 1000000);
assert.equal(cfg.minWholesaleLot, 10);
assert.deepEqual([3,4,5].map(M.t2Capacity), [3,2,1]);
assert.deepEqual([1,2,3,4,5].map(M.machineryPrice), [15000,75000,375000,1875000,9375000]);
const target = (salesEMA) => M.finishedStockTarget({ salesEMA, coverageTicks: 3,
  bootstrapStock: 3, capacity: 3, targetInventory: 6, maxInventory: 6 });
assert.equal(target(0), 3); assert.equal(target(1.5), 5); assert.equal(target(100), 6);
assert.equal(M.finishedStockTarget({ salesEMA: 100, coverageTicks: 3, bootstrapStock: 16,
  capacity: 160, targetInventory: 600, maxInventory: 1200 }), 300);
for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
  const portfolio = Array.from({ length: W.t2FirmLineCount[firm] }, (_, slot) =>
    M.T2_PRODUCTS[W.t2LineProduct[W.t2FirmLines[firm * 5 + slot]]]);
  assert.equal(W.t2Cash[firm], M.tier2StartingCash(portfolio, cfg));
  assert.ok(W.t2Cash[firm] >= cfg.tier2MinimumCash);
  assert.ok(W.t2Cash[firm] < W.t2EqBook[firm] * 0.01, 'Operating reserves are not equipment-value endowments');
  assert.ok(M.tier2StartingCash(portfolio, { ...cfg, baseCost: 2 }) > W.t2Cash[firm]);
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
console.log('calibration targets, operating reserves, machinery and UI defaults: ok');
