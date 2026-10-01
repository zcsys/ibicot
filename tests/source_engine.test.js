'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');

async function run() {
  const messages = [];
  const self = { location: { href: 'http://localhost/phase0_economy_engine_worker.js' }, postMessage: message => messages.push(message) };
  const context = {
    Array, Boolean, Date, Error, Float64Array, Int32Array, JSON, Math, Number,
    Object, Set, String, URL, Uint8Array, Uint16Array, Uint32Array, WebAssembly,
    console, self, performance: { now: () => 0 }, setTimeout: () => 0, clearTimeout: () => {},
    fetch: async () => { throw new Error('The source engine must not fetch external runtime code.'); }
  };
  vm.createContext(context);
  context.importScripts = (...paths) => paths.forEach(path => vm.runInContext(fs.readFileSync(path.replace('./', ''), 'utf8'), context, { filename: path }));
  vm.runInContext(fs.readFileSync('phase0_economy_engine_worker.js', 'utf8'), context, { filename: 'phase0_economy_engine_worker.js' });
  await self.onmessage({ data: { type: 'init', cfg: {} } });
  for (let i = 0; i < 60; i++) await self.onmessage({ data: { type: 'step' } });
  const snapshot = messages.at(-1).data;
  assert.equal(snapshot.engine, 'source');
  assert.equal(snapshot.tick, 60);
  const numeric = [snapshot.wholesaleAvg, snapshot.retailAvg, snapshot.tiers.t0.inventory, snapshot.tiers.t0.cash, snapshot.tiers.t1.inventory, snapshot.tiers.t1.cash, snapshot.tiers.t2.potential, snapshot.tiers.t2.active, snapshot.tiers.t2.fulfilled];
  assert.ok(numeric.every(Number.isFinite));
  assert.ok(numeric.slice(2).every(value => value >= 0));
  assert.ok(snapshot.tiers.t2.fulfilled <= snapshot.tiers.t2.active);
  return { wholesale: snapshot.wholesaleAvg, retail: snapshot.retailAvg, fulfilled: snapshot.tiers.t2.fulfilled, equity: snapshot.tiers.t1.equity };
}

(async () => {
  const first = await run();
  const second = await run();
  assert.deepEqual(second, first);
  console.log('source engine: ok');
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
