'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 10, endUserCount: 10, consumerActivation: 0,
  retailTargetInventory: 100, retailMaxInventory: 120 });
const { W, cfg } = worker.inspect();
W.raw[0] = 1000; W.rawBasis[0] = 1; W.t1Cash[0] = 10000;
W.t1DemandEMA[0] = 100;
worker.step();
assert.equal(W.t1Fin[0], 100, 'Finished production stops at the desired level');
// Exercise the independent kernel guard, even with an inconsistent direct cfg.
// Normal worker messages normalize maximum >= desired before calling the kernel.
cfg.retailTargetInventory = 200;
worker.step();
assert.equal(W.t1Fin[0], 120, 'Production cannot exceed the configured hard maximum');
const raw = W.raw[0];
worker.step();
assert.equal(W.t1Fin[0], 120);
assert.equal(W.raw[0], raw, 'No inputs consumed while the hard warehouse limit is full');
cfg.retailMaxInventory = 80;
worker.step();
assert.equal(W.t1Fin[0], 120, 'Lowering a limit stops production but never destroys owned stock');
assert.equal(W.raw[0], raw);
console.log('inventory target and independent maximum guard: ok');
