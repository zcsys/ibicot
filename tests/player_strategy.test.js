'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const config = { t2FirmCount: 1000, endUserCount: 20000 };
const bot = createWorker(config), player = createWorker(config);
const A = bot.inspect().W, B = player.inspect().W;
// The economy exists and trades before an investor chooses a company.
for (let tick = 0; tick < 120; tick++) { bot.step(); player.step(); }
let firm = -1, productIndex = -1;
for (let id = 0; id < 1000 && firm < 0; id++) {
  for (let p = 0; p < 10; p++) if (A.t1Sold[id * 10 + p] > 0) { firm = id; productIndex = p; break; }
}
assert.ok(firm >= 0, 'An established trading company can be selected');
const index = firm * 10 + productIndex, product = player.model.PRODUCTS[productIndex];
const cash = B.t1Cash[firm], book = B.t1EqBook[firm];
const stock = B.t1Fin.slice(firm * 10, firm * 10 + 10);
const raw = B.raw.slice(firm * 4, firm * 4 + 4);
const suppliers = B.preferredWholesale.slice(firm * 4, firm * 4 + 4);
const quote = B.t1Price[index];
player.send({ type: 'select', tier: 'T1', id: firm });
assert.equal(B.t1Controller[firm], 0, 'Inspection does not take control');
player.send({ type: 'player', tier: 'T1', id: firm, controller: 'PLAYER', online: true, code: product.code, price: quote });
assert.equal(B.t1Cash[firm], cash); assert.equal(B.t1EqBook[firm], book);
assert.deepEqual(B.t1Fin.slice(firm * 10, firm * 10 + 10), stock);
assert.deepEqual(B.raw.slice(firm * 4, firm * 4 + 4), raw);
assert.deepEqual(B.preferredWholesale.slice(firm * 4, firm * 4 + 4), suppliers);
assert.equal(B.t1Controller.reduce((n, flag) => n + flag, 0), 1);
let playerRevenue = 0, botRevenue = 0;
for (let tick = 0; tick < 180; tick++) {
  bot.step(); player.step();
  botRevenue += A.t1Rev[index]; playerRevenue += B.t1Rev[index];
  const floor = Math.max(player.model.MIN_UNIT_PRICE, B.t1FinBasis[index] || B.t1UnitCost[index], B.t1ReplacementCost[index]);
  assert.ok(Math.abs(B.t1Price[index] - Math.max(B.playerPrice[index], floor)) < 1e-7, 'Investor price persists subject to the normal cost floor');
}
assert.ok(playerRevenue > 0 && botRevenue > 0, 'Both controllers participate in the same operating market');
assert.equal(B.t1EqBook[firm], book, 'Takeover creates no equipment capital');
assert.equal(B.t2Controller.reduce((n, flag) => n + flag, 0), 0);
assert.ok(B.t2Revenue.some(value => value > 0), 'Tier 2 keeps operating under bots');
player.send({ type: 'player', tier: 'T1', id: firm, controller: 'BOT', online: true, code: product.code, price: quote });
assert.equal(B.t1Controller[firm], 0);
console.log(JSON.stringify({ result: 'PASS', tier: 'T1', firm: firm + 1, ticks: 180, botRevenue, playerRevenue, takeover: 'Existing capital and relationships preserved; no guaranteed advantage' }));
