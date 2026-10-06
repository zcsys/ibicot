'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 10, endUserCount: 10, consumerActivation: 0,
  retailTargetInventory: 100, retailMaxInventory: 120 });
const { W, cfg } = worker.inspect();
// Isolate the production guard from downstream material withdrawals.
W.t2FirmLineCount.fill(0);
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
// Extraction shares one company capacity across materials. Equal deficits
// must not favor the element listed last; uneven deficits retain their ratios.
const extraction = createWorker({ t2FirmCount: 10, endUserCount: 10,
  consumerActivation: 0, sigma: 0 });
const { W: resources, cfg: resourceCfg } = extraction.inspect();
resources.t1Operates.fill(0); resources.t2FirmLineCount.fill(0);
function extractForDeficits(deficits) {
  resources.t0Inv.fill(0); resources.t0DemandEMA.fill(0);
  deficits.forEach((deficit, e) => { resources.t0DemandEMA[e] = deficit / resourceCfg.inventoryCoverageTicks; });
  extraction.step();
  return Array.from(resources.t0Inv.slice(0, 4));
}
assert.deepEqual(extractForDeficits([10000, 10000, 10000, 10000]), [2500, 2500, 2500, 2500]);
assert.deepEqual(extractForDeficits([3000, 3000, 3000, 3000]), [2500, 2500, 2500, 2500],
  'A final material stock target must not strand capacity needed by earlier materials');
assert.deepEqual(extractForDeficits([4000, 8000, 12000, 16000]), [1000, 2000, 3000, 4000]);
assert.deepEqual(extractForDeficits([16000, 12000, 8000, 4000]), [4000, 3000, 2000, 1000]);
console.log('inventory target and independent maximum guard: ok');
