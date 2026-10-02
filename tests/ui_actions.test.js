'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');

// Execute the actual UI message handlers, not a parallel implementation.
const app = fs.readFileSync('phase0_economy_engine_app.js', 'utf8');
const start = app.indexOf("  $('applyPlayer').onclick =");
const end = app.indexOf('  initializeTableSorting();', start);
assert.ok(start >= 0 && end > start);
const controls = Object.fromEntries(Object.entries({
  playerTier: 'T2', t2PlayerCompany: '50000', playerCompany: '17',
  controller: 'PLAYER', online: 'true', playerProduct: 'installed',
  playerPrice: '12.5', equipmentProduct: 'eligible',
  applyPlayer: '', buyEquipment: '',
}).map(([id, value]) => [id, { value }]));
const messages = [];
const context = {
  $: (id) => controls[id], controlDirty: true,
  controlId: () => controls.playerTier.value === 'T2' ? +controls.t2PlayerCompany.value - 1 : +controls.playerCompany.value,
  worker: { postMessage: (message) => messages.push(message) },
};
vm.runInNewContext(app.slice(start, end), context);
for (const [tier, id] of [['T2', 49999], ['T1', 17]]) {
  controls.playerTier.value = tier;
  controls.applyPlayer.onclick();
  controls.buyEquipment.onclick();
  for (const message of messages.splice(0)) {
    assert.equal(message.tier, tier);
    assert.equal(message.id, id);
    assert.ok(['player', 'buyEquipment'].includes(message.type));
  }
}
console.log('tier-aware UI actions: ok');
