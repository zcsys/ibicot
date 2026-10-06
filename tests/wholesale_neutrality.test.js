'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({t2FirmCount:100,endUserCount:1000});
const {W,cfg} = worker.inspect();
const profiles = worker.snapshot().t0Companies;
assert.ok(W.preferredWholesale.every(id => id === -1), 'No unearned opening supplier attachment');
W.t0Inv.fill(10000);
const counts = new Uint32Array(20);
for (let buyer = 0; buyer < 100000; buyer++) {
  const e = buyer % 4;
  const supplier = worker.kernel.tier0Supplier(W,cfg,profiles,e,-1,buyer,1);
  assert.ok(profiles[supplier].elements.includes(worker.model.ELEMENTS[e]));
  counts[supplier]++;
}
// This catches both the lowest-ID monopoly and multiplicative exposure from
// listing more elements despite sharing one factory-wide output budget.
for (const count of counts) assert.ok(Math.abs(count - 5000) < 350, JSON.stringify(Array.from(counts)));
const e = 0, eligible = profiles.filter(p => p.elements.includes(worker.model.ELEMENTS[e]));
const cheap = eligible.at(-1).id;
W.t0Price[cheap*4+e] = .9;
for(let buyer=0;buyer<100;buyer++) assert.equal(worker.kernel.tier0Supplier(W,cfg,profiles,e,-1,buyer,1),cheap,'Cheaper stocked offers still win');
const preferred = eligible[0].id;
W.t0Price[cheap*4+e] = W.t0Price[preferred*4+e] - .01;
assert.equal(worker.kernel.tier0Supplier(W,cfg,profiles,e,preferred,1,1),preferred,'Established switching friction still applies');
W.t0Inv[preferred*4+e]=0;
assert.equal(worker.kernel.tier0Supplier(W,cfg,profiles,e,preferred,1,1),cheap,'Stockouts still permit switching');
console.log(JSON.stringify({result:'PASS',equalQuoteSelections:Array.from(counts),counts:[20,1000,61950],rule:'Shared-capacity tie exposure; relationships earned through trade'}));
