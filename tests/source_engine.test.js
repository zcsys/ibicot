'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');

async function run(ticks = 60, cfg = { endUserCount: 10000, t2FirmCount: 1000 }) {
  const messages = [];
  const self = {
    location: { href: 'http://localhost/phase0_economy_engine_worker.js' },
    postMessage: (message) => messages.push(message),
  };
  const context = {
    Array,
    Boolean,
    Date,
    Error,
    Float64Array,
    Int32Array,
    JSON,
    Math,
    Number,
    Object,
    Set,
    String,
    URL,
    Uint8Array,
    Uint16Array,
    Uint32Array,
    WebAssembly,
    console,
    self,
    performance: { now: () => 0 },
    setTimeout: () => 0,
    clearTimeout: () => {},
    fetch: async () => {
      throw new Error('The source engine must not fetch external runtime code.');
    },
  };
  vm.createContext(context);
  context.importScripts = (...paths) =>
    paths.forEach((path) =>
      vm.runInContext(fs.readFileSync(path.replace('./', ''), 'utf8'), context, { filename: path }),
    );
  vm.runInContext(fs.readFileSync('phase0_economy_engine_worker.js', 'utf8'), context, {
    filename: 'phase0_economy_engine_worker.js',
  });
  await self.onmessage({ data: { type: 'init', cfg } });
  for (let i = 0; i < ticks; i++) await self.onmessage({ data: { type: 'step' } });
  const snapshot = messages.at(-1).data;
  assert.equal(snapshot.engine, 'source');
  assert.equal(snapshot.tick, ticks);
  const numeric = [
    snapshot.wholesaleAvg,
    snapshot.retailAvg,
    snapshot.tiers.t0.inventory,
    snapshot.tiers.t0.cash,
    snapshot.tiers.t1.inventory,
    snapshot.tiers.t1.cash,
    snapshot.tiers.endUsers.potential,
    snapshot.tiers.endUsers.active,
    snapshot.tiers.endUsers.fulfilled,
  ];
  assert.ok(numeric.every(Number.isFinite), JSON.stringify({ tick: snapshot.tick, numeric }));
  assert.ok(numeric.slice(2).every((value) => value >= 0));
  assert.ok(snapshot.tiers.endUsers.fulfilled <= snapshot.tiers.endUsers.active);
  const compoundCohorts = snapshot.cohorts.slice(4);
  assert.ok(
    compoundCohorts.every((cohort) => cohort.made > 0 && cohort.sold > 0 && cohort.revenue > 0),
    'every compound market should produce and trade',
  );
  return {
    wholesale: snapshot.wholesaleAvg,
    retail: snapshot.retailAvg,
    fulfilled: snapshot.tiers.endUsers.fulfilled,
    equity: snapshot.tiers.t1.equity,
    fillRate: snapshot.tiers.endUsers.unitFillRate,
    wholesalePrices: JSON.parse(JSON.stringify(snapshot.elements.map(({ price }) => price))),
    maxT0Inventory: Math.max(...snapshot.t0Companies.map((company) => company.inventory)),
    compound: JSON.parse(
      JSON.stringify(
        compoundCohorts.map(({ code, made, sold, revenue }) => ({ code, made, sold, revenue })),
      ),
    ),
    products: JSON.parse(
      JSON.stringify(
        snapshot.products.map(({ code, active, fulfilled, revenue, intermediateVolume }) => ({
          code,
          active,
          fulfilled,
          revenue,
          intermediateVolume,
        })),
      ),
    ),
  };
}

(async () => {
  const first = await run();
  const second = await run();
  assert.deepEqual(second, first);
  const sustained = await run(360);
  assert.ok(
    sustained.fillRate >= 0.5,
    'the established economy should fulfill at least half of effective end-user demand',
  );
  assert.ok(
    sustained.wholesalePrices.every((price) => Number.isFinite(price) && price > 0),
    'market prices must remain finite and positive without an authored ceiling',
  );
  assert.ok(
    sustained.maxT0Inventory <= 60000,
    'a Tier 0 supplier must not produce beyond its total target inventory across elements',
  );
  assert.ok(
    sustained.compound.every((market) => market.made > 0 && market.sold > 0 && market.revenue > 0),
    'compound markets should remain active long-term',
  );
  assert.ok(
    sustained.products.every((market, index) => index < 4 ? market.active > 0 && market.fulfilled > 0 && market.revenue > 0 : market.active === 0 && market.fulfilled === 0 && market.intermediateVolume > 0),
    'C-1 markets must serve retail demand and C-2 markets must serve manufacturers only',
  );
  console.log('source engine: ok');
})().catch((error) => {
  console.error(error.stack);
  process.exitCode = 1;
});
