'use strict';

const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const v8 = require('node:v8');
const { createHash } = require('node:crypto');
const { performance } = require('node:perf_hooks');
const root = path.resolve(__dirname, '..');
const runtimeFiles = ['engine/model.js', 'engine/reference_kernel.js', 'phase0_economy_engine_worker.js'];
// These are worker closure fields, including the duplicate Tier 1 admin state
// used by later equipment and controller actions. Timers are execution handles,
// so imports are paused; every field affecting tick or snapshot state is saved.
const closureFields = ['cfg', 'tick', 'month', 'W', 'sourceState', 'equipment',
  'eqBook', 'controller', 'online', 'playerPrices', 'selectedTierControl',
  'selectedT2Id', 'selectedId', 'lastSnapshot', 'lastReportAt', 'lastReportTick',
  'analyticsHistory', 'tier2CompanyHistory', 'tier2HistoryCompany',
  'prevT0Inventory', 'prevT1Finished', 'prevT1FinishedCohort',
  'tickStartT0Inventory', 'tickStartT1Finished', 'lastTickT0Produced',
  'lastTickT1Made', 'watchedCompanies', 'watchedCompanyHistory', 'workerStats',
  'tier2Query', 'mode', 'targetTPS', 'adminAccounting', 'playerLicenses',
  'playerHouse', 'ownershipAccounting', 'ownershipEnforced'];
const detached = value => v8.deserialize(v8.serialize(value));

// Execute the actual worker sources in one native JS realm. A VM proxy around
// Math/typed arrays distorts million-agent timings; no alternate engine is used.
function createWorker(cfg = {}, runtime = {}) {
  const self = { postMessage(message) { this.lastMessage = message; if (message.type === 'snapshot') this.snapshot = message.data; } };
  const schedules = [];
  const texts = runtimeFiles.map(file => fs.readFileSync(path.join(root, file), 'utf8'));
  const sourceFingerprint = Object.fromEntries(runtimeFiles.map((file, index) =>
    [file, createHash('sha256').update(texts[index]).digest('hex')]));
  let source = texts.map(text => text.replace(/^importScripts\(.*\);$/m, '')).join('\n');
  if (runtime.onBeforeTier0Reprice) {
    const boundary = '    priceMarkets(W, cfg, profiles, products, tick);';
    if (source.split(boundary).length !== 2) throw new Error('Expected one wholesale repricing boundary');
    source = source.replace(boundary, '    onBeforeTier0Reprice(W);\n' + boundary);
  }
  const capture = `() => ({ ${closureFields.join(', ')} })`;
  const restore = `(saved) => {
    if (timer !== null) clearTimeout(timer);
    running = false; timer = null;
    for (const name of Object.keys(W)) if (!(name in saved.W)) delete W[name];
    for (const [name, value] of Object.entries(saved.W)) {
      if (ArrayBuffer.isView(value)) W[name].set(value); else W[name] = value;
    }
    ${closureFields.filter(name => name !== 'W').map(name => `${name} = saved.${name};`).join('\n')}
    self.snapshot = lastSnapshot;
    self.lastMessage = lastSnapshot ? { type: 'snapshot', data: lastSnapshot } : null;
  }`;
  const api = new Function('self', 'performance', 'setTimeout', 'clearTimeout', 'onBeforeTier0Reprice', source +
    `\nreturn { step, publish, reset, inspect: () => ({ W, cfg, tick, sourceState, adminAccounting: administrativeAccountingSnapshot() }), kernel: self.Phase0ReferenceKernel,
      model: self.Phase0Model, captureState: ${capture}, restoreState: ${restore}, normalizeStateConfig: normalizeConfig };`)
    (self, runtime.performance || performance,
      runtime.setTimeout || ((fn) => { schedules.push(fn); return schedules.length; }),
      runtime.clearTimeout || (() => {}), runtime.onBeforeTier0Reprice);
  const send = (data) => { self.onmessage({ data }); if (self.lastMessage?.type === 'error') throw new Error(self.lastMessage.message); };
  send({ type: 'init', cfg });
  const initialSchema = api.captureState();
  const typedShape = value => ({ type: value.constructor.name, length: value.length, bytes: value.byteLength });
  const worldShapes = Object.fromEntries(Object.entries(initialSchema.W).filter(([, value]) => ArrayBuffer.isView(value))
    .map(([name, value]) => [name, typedShape(value)]));
  const closureShapes = Object.fromEntries(closureFields.filter(name => ArrayBuffer.isView(initialSchema[name]))
    .map(name => [name, typedShape(initialSchema[name])]));
  function validateState(saved) {
    assert.ok(saved && typeof saved === 'object', 'Missing worker state');
    assert.equal(saved.format, 'ibicot-worker-state', 'Unsupported worker state format');
    assert.equal(saved.version, 1, 'Unsupported worker state version');
    assert.deepEqual(saved.sourceFingerprint, sourceFingerprint, 'Checkpoint runtime fingerprints differ');
    const state = saved.state;
    assert.ok(state && typeof state === 'object', 'Missing worker closure state');
    assert.deepEqual(Object.keys(state).sort(), [...closureFields].sort(), 'Worker closure fields differ');
    assert.deepEqual(state.cfg, api.normalizeStateConfig(state.cfg), 'Checkpoint config is not normalized');
    assert.deepEqual(state.cfg, api.inspect().cfg, 'Checkpoint config differs from destination worker');
    assert.ok(Number.isSafeInteger(state.tick) && state.tick >= 0, 'Invalid checkpoint tick');
    assert.equal(state.month, Math.floor(state.tick / api.model.TIME.ticksPerMonth), 'Checkpoint month differs from tick');
    assert.ok(state.W && typeof state.W === 'object', 'Missing checkpoint world');
    const scalarNames = ['t2LineCount', 'costSinks', 'equipmentSinks'];
    for (const name of Object.keys(state.W)) assert.ok(worldShapes[name] || scalarNames.includes(name), `Unknown world field ${name}`);
    for (const [name, shape] of Object.entries(worldShapes)) {
      assert.ok(ArrayBuffer.isView(state.W[name]), `Missing typed world field ${name}`);
      assert.deepEqual(typedShape(state.W[name]), shape, `Checkpoint shape differs for W.${name}`);
    }
    for (const name of scalarNames) if (name in state.W)
      assert.ok(Number.isFinite(state.W[name]) && state.W[name] >= 0, `Invalid world scalar ${name}`);
    const world = state.W, count = world.t2LineCount;
    assert.ok(Number.isInteger(count) && count <= world.t2LineFirm.length, 'Invalid Tier 2 line count');
    let listed = 0;
    for (let firm = 0; firm < state.cfg.t2FirmCount; firm++) {
      const width = world.t2FirmLineCount[firm];
      assert.ok(width >= 1 && width <= api.model.T2_MAX_PRODUCTS_PER_FIRM, `Invalid portfolio width ${firm}`);
      listed += width;
      for (let slot = 0; slot < width; slot++) {
        const line = world.t2FirmLines[firm * api.model.T2_MAX_PRODUCTS_PER_FIRM + slot];
        assert.ok(line >= 0 && line < count && world.t2LineFirm[line] === firm, `Invalid portfolio line ${firm}/${slot}`);
        const product = api.model.T2_PRODUCTS[world.t2LineProduct[line]];
        assert.ok(product && product.sectorIndex === world.t2Sector[firm], `Invalid portfolio sector ${firm}/${slot}`);
      }
    }
    assert.equal(listed, count, 'Tier 2 listed routes differ from line count');
    for (const [name, shape] of Object.entries(closureShapes)) {
      assert.ok(ArrayBuffer.isView(state[name]), `Missing typed closure field ${name}`);
      assert.deepEqual(typedShape(state[name]), shape, `Checkpoint shape differs for ${name}`);
    }
    for (const name of ['equipment', 'playerPrices']) assert.ok(Array.isArray(state[name]) && state[name].length === 1000, `Invalid ${name}`);
    for (let firm = 0; firm < 1000; firm++) {
      assert.ok(Array.isArray(state.equipment[firm]) && state.equipment[firm].every(code => api.model.PRODUCTS.some(p => p.code === code)), `Invalid equipment ${firm}`);
      assert.equal(new Set(state.equipment[firm]).size, state.equipment[firm].length, `Duplicate equipment ${firm}`);
      assert.ok(state.playerPrices[firm] && typeof state.playerPrices[firm] === 'object' && !Array.isArray(state.playerPrices[firm]), `Invalid player prices ${firm}`);
      assert.equal(state.controller[firm], world.t1Controller[firm], `Tier 1 controller mirrors differ ${firm}`);
      assert.equal(state.eqBook[firm], world.t1EqBook[firm], `Tier 1 machinery mirrors differ ${firm}`);
      for (const product of api.model.PRODUCTS)
        assert.equal(Boolean(world.t1Operates[firm * 10 + api.model.PRODUCTS.indexOf(product)]),
          state.equipment[firm].includes(product.code), `Tier 1 equipment mirrors differ ${firm}/${product.code}`);
    }
    const sourceKeys = ['activeOrders', 'fulfilledOrders', 'activatedConsumers', 'consumerPayments', 'costSinks', 'equipmentSinks'];
    assert.ok(state.sourceState && typeof state.sourceState === 'object', 'Missing transaction state');
    for (const name of sourceKeys.slice(0, state.tick > 0 ? 6 : 4))
      assert.ok(name in state.sourceState, `Missing transaction field ${name}`);
    for (const [name, value] of Object.entries(state.sourceState))
      assert.ok(sourceKeys.includes(name) && Number.isFinite(value) && value >= 0, `Invalid transaction field ${name}`);
    for (const name of ['analyticsHistory', 'tier2CompanyHistory']) assert.ok(Array.isArray(state[name]), `Invalid ${name}`);
    assert.ok(state.watchedCompanies?.T0 instanceof Set && state.watchedCompanies?.T1 instanceof Set, 'Invalid watched company sets');
    for (const [tier, limit] of [['T0', 20], ['T1', 1000]]) for (const firm of state.watchedCompanies[tier])
      assert.ok(Number.isInteger(firm) && firm >= 0 && firm < limit, `Invalid watched company ${tier}/${firm}`);
    assert.ok(state.watchedCompanyHistory && typeof state.watchedCompanyHistory === 'object', 'Invalid watched company histories');
    assert.ok(['T1', 'T2'].includes(state.selectedTierControl), 'Invalid selected tier');
    assert.ok(Number.isInteger(state.selectedId) && state.selectedId >= 0 && state.selectedId < 1000, 'Invalid selected Tier 1 company');
    assert.ok(Number.isInteger(state.selectedT2Id) && state.selectedT2Id >= 0 && state.selectedT2Id < state.cfg.t2FirmCount, 'Invalid selected Tier 2 company');
    assert.ok(state.tier2Query && typeof state.tier2Query === 'object', 'Missing company query');
    assert.ok(state.workerStats && Number.isSafeInteger(state.workerStats.steps) && state.workerStats.steps >= 0, 'Invalid worker statistics');
    for (const name of ['lastTickMs', 'totalTickMs']) assert.ok(Number.isFinite(state.workerStats[name]) && state.workerStats[name] >= 0, `Invalid worker timing ${name}`);
    assert.ok(Number.isFinite(state.lastReportAt) && state.lastReportAt >= 0, 'Invalid report time');
    assert.ok(Number.isSafeInteger(state.lastReportTick) && state.lastReportTick >= 0 && state.lastReportTick <= state.tick, 'Invalid report tick');
    assert.ok(state.lastSnapshot === null || typeof state.lastSnapshot === 'object', 'Invalid snapshot');
    assert.ok(['fixed', 'max'].includes(state.mode), 'Invalid execution mode');
    assert.ok(Number.isFinite(state.targetTPS) && state.targetTPS > 0, 'Invalid target tick rate');
    const ledger = state.adminAccounting;
    assert.ok(ledger && Number.isFinite(ledger.equipmentSinks) && ledger.equipmentSinks >= 0,
      'Invalid cumulative administrative equipment sinks');
    assert.ok(Number.isSafeInteger(ledger.sequence) && ledger.sequence >= 0, 'Invalid administrative action sequence');
    if (!ledger.sequence) {
      assert.equal(ledger.equipmentSinks, 0, 'An empty administrative ledger cannot have sinks');
      assert.equal(ledger.lastEquipmentReceipt, null, 'An empty administrative ledger cannot have a receipt');
    } else {
      const receipt = ledger.lastEquipmentReceipt;
      assert.ok(receipt && typeof receipt === 'object', 'Missing administrative equipment receipt');
      assert.equal(receipt.sequence, ledger.sequence, 'Administrative receipt sequence differs');
      assert.equal(receipt.cumulativeEquipmentSinks, ledger.equipmentSinks, 'Administrative receipt total differs');
      assert.ok(Number.isSafeInteger(receipt.tick) && receipt.tick >= 0 && receipt.tick <= state.tick, 'Invalid administrative receipt tick');
      assert.equal(receipt.generationHex, api.model.calendarAt(receipt.tick).generationHex, 'Administrative receipt calendar differs');
      assert.ok(['T1', 'T2'].includes(receipt.tier) && typeof receipt.ok === 'boolean', 'Invalid administrative receipt status');
      assert.ok(Number.isFinite(receipt.equipmentSink) && receipt.equipmentSink >= 0 &&
        receipt.equipmentSink <= ledger.equipmentSinks, 'Invalid administrative receipt sink');
      if (!receipt.ok) assert.equal(receipt.equipmentSink, 0, 'A rejected purchase cannot have an equipment sink');
    }
    return state;
  }
  const exportState = () => detached({ format: 'ibicot-worker-state', version: 1, sourceFingerprint, state: api.captureState() });
  const importState = saved => {
    // Validate and detach before touching the live world. Holding an inspect().W
    // or typed-array reference remains safe across an import.
    validateState(saved);
    const state = detached(saved.state);
    api.restoreState(state);
    schedules.length = 0;
    return api.inspect();
  };
  const { captureState, restoreState, normalizeStateConfig, ...publicApi } = api;
  return { ...publicApi, self, send, schedules, sourceFingerprint, exportState, importState,
    snapshot: () => { api.publish(); return self.snapshot; } };
}

module.exports = { createWorker };
