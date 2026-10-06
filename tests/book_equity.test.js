'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
worker.send({ type: 'watchCompanies', watches: { T0: [0], T1: [0] } });
worker.send({ type: 'select', tier: 'T2', id: 0 });
for (let t = 0; t < 20; t++) worker.step();
const before = worker.snapshot(), { W } = worker.inspect();
// A posted quote is not a transaction. Doubling every quote cannot create
// shareholder equity from unsold goods, in any aggregate or company view.
for (const prices of [W.t0Price, W.t1Price, W.t2Price])
  for (let i = 0; i < prices.length; i++) if (Number.isFinite(prices[i])) prices[i] *= 2;
const after = worker.snapshot();
for (const tier of ['t0', 't1', 't2']) assert.equal(after.tiers[tier].equity, before.tiers[tier].equity);
for (const key of ['T0:0', 'T1:0']) assert.equal(after.expandedDetails[key].equity, before.expandedDetails[key].equity);
assert.equal(after.selected.equity, before.selected.equity);
for (const rows of ['t0Companies', 'companies', 'cohorts', 'tier2Industries'])
  after[rows].forEach((row, i) => assert.equal(row.equity, before[rows][i].equity));
console.log('Book equity: changing unsold quotes creates no equity in any tier or company view: ok');
