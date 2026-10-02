'use strict';
const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');
const bot = createWorker(), player = createWorker();
const A = bot.inspect().W, B = player.inspect().W;
// A player observes an established market and takes over an active workshop
// with spare capacity. Selection uses visible recent sales, not a privileged
// supplier, assigned customers, or a guaranteed winning company number.
for (let tick = 0; tick < 120; tick++) { bot.step(); player.step(); }
let firm = -1;
for (let id = 0; id < bot.inspect().cfg.t2FirmCount; id++) {
  let sold = 0, capacity = 0;
  for (let slot = 0; slot < A.t2FirmLineCount[id]; slot++) {
    const line = A.t2FirmLines[id * 5 + slot];
    sold += A.t2Sold[line]; capacity += bot.model.T2_PRODUCTS[A.t2LineProduct[line]].capacity;
  }
  if (sold > 0 && sold < capacity * 0.5) { firm = id; break; }
}
assert.ok(firm >= 0, 'An observable active workshop with spare capacity');
const cash = B.t2Cash[firm], equipment = B.t2EqBook[firm], lines = B.t2FirmLineCount[firm];
// Refresh a quote from the product-market averages visible in the dashboard.
// A fixed authored markup is not a guarantee of a competitive price.
function quoteCompetition() {
  const markets=player.snapshot().tier2Products;
  for(let slot=0;slot<lines;slot++) {
    const line=B.t2FirmLines[firm*5+slot],product=player.model.T2_PRODUCTS[B.t2LineProduct[line]];
    const quote=markets.find(m=>m.code===product.code).avgPrice*.92;
    player.send({type:'player',tier:'T2',id:firm,controller:'PLAYER',online:true,code:product.code,price:quote});
  }
}
quoteCompetition();
assert.equal(B.t2Cash[firm], cash); assert.equal(B.t2EqBook[firm], equipment);
assert.equal(B.t2FirmLineCount[firm], lines);
assert.equal(B.t2Controller.reduce((n, flag) => n + flag, 0), 1);
console.log(`Comparing an 8% market-price undercut with identical established bot company ${firm + 1}`);
const results = [{ revenue: 0, cogs: 0, sold: 0 }, { revenue: 0, cogs: 0, sold: 0 }];
for (let tick = 0; tick < 180; tick++) {
  if(tick>0 && tick%30===0)quoteCompetition();
  bot.step(); player.step();
  for (const [index, W] of [A, B].entries()) for (let slot = 0; slot < lines; slot++) {
    const line = W.t2FirmLines[firm * 5 + slot];
    results[index].revenue += W.t2Revenue[line]; results[index].cogs += W.t2COGS[line];
    results[index].sold += W.t2Sold[line];
    assert.ok(W.t2Price[line] + 1e-7 >= (W.t2FinBasis[line] || W.t2UnitCost[line]));
  }
}
const profits = results.map((r) => r.revenue - r.cogs);
assert.ok(results.every((r) => r.sold > 0), JSON.stringify({ results, profits }));
assert.ok(results[1].sold > results[0].sold,JSON.stringify({results,profits}));
assert.ok(profits[1] > profits[0] * 1.05, JSON.stringify({ results, profits }));
assert.equal(B.t2EqBook[firm], equipment); assert.equal(B.t2FirmLineCount[firm], lines);
assert.equal(B.t2Controller.reduce((n, flag) => n + flag, 0), 1);
console.log(JSON.stringify({ result: 'PASS', strategy: '8% below observed market-average offers, refreshed every 30 ticks', firm: firm + 1,
  ticks: 180, bot: { ...results[0], profit: profits[0] }, player: { ...results[1], profit: profits[1] },
  profitImprovement: profits[1] / profits[0] - 1 }));
