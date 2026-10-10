const assert = require('assert');
const P = require('../../web/profitability.js');
const cfg = {storage:20000,storageRentPerUnitYear:20.16};
const charge = 1120;
const firm = {grossProfit:100,revenue:200,products:[{grossProfit:40},{grossProfit:60}]};
P.company(firm,cfg,'T2');
assert(Math.abs(firm.netProfit-(100-charge)) < 1e-10);
assert(Math.abs(firm.products.reduce((a,p)=>a+p.netProfit,0)-firm.netProfit)<1e-10);
P.company(firm,cfg,'T2'); // Repeated rendering must not charge again.
assert(Math.abs(firm.netProfit-(100-charge)) < 1e-10);
const t0 = {grossProfit:100};P.company(t0,cfg,'T0');assert.equal(t0.netProfit,100);
const idle = {grossProfit:0};P.company(idle,cfg,'T1');assert.equal(idle.netProfit,-charge);
P.company(idle,{...cfg,storageRentPerUnitYear:0},'T1');assert.equal(idle.netProfit,0);
const s={cfg,tiers:{t0:{firms:1,grossProfit:100},t1:{firms:2,grossProfit:200},t2:{firms:2,activeLines:3,grossProfit:300}},
 productCategories:[{complexity:0,lines:1,grossProfit:100},{complexity:1,lines:2,grossProfit:200},{complexity:3,lines:2,grossProfit:200},{complexity:4,lines:1,grossProfit:100}],
 elements:[],tier2Products:[{firms:2,grossProfit:200},{firms:1,grossProfit:100}],tier2Industries:[{lines:3,grossProfit:300}],tier2Complexity:[],cohorts:[],tier2Cohorts:[],t0Companies:[],companies:[],tier2Companies:{rows:[]},selected:{tier:'T0'},expandedDetails:{}};
P.snapshot(s);
assert(Math.abs(s.tier2Products.reduce((n,p)=>n+p.netProfit,0)-s.tiers.t2.netProfit)<1e-10);
assert.equal(s.tiers.t2.netProfit,s.tier2Industries[0].netProfit);
assert.equal(s.productCategories[0].netProfitPerLine,100);
console.log('profitability: allocated rent, exemption, idle loss, multi-line allocation, totals and repeat rendering passed');

assert(Math.abs(firm.netMargin - (100-charge)/200) < 1e-12);
assert.equal(idle.netMargin,null);
const loss={grossProfit:-20,revenue:100};P.apply(loss,10);assert.equal(loss.netMargin,-.3);

const exempt={grossProfit:100,revenue:200,equity:1999999,storageRentExpense:0};P.company(exempt,cfg,'T2');assert.equal(exempt.netProfit,100);assert.equal(exempt.netMargin,.5);
const crossing={grossProfit:100,revenue:200,equity:1999000,storageRentExpense:1120};P.company(crossing,cfg,'T2');assert.equal(crossing.netProfit,-1020);
const transfers={grossProfit:100,revenue:200,storageRentExpense:40,switchingIncome:30,switchingExpense:50,
  products:[{grossProfit:40,revenue:80},{grossProfit:60,revenue:120}]};
P.company(transfers,cfg,'T2');assert.equal(transfers.netProfit,40);assert.equal(transfers.netMargin,.2);
assert.equal(transfers.products.reduce((n,p)=>n+p.netProfit,0),40);
P.company(transfers,cfg,'T2');assert.equal(transfers.netProfit,40);
const legacyMissing={grossProfit:100,revenue:200,netEarningsAvailable:false};
P.company(legacyMissing,cfg,'T2');assert.equal(legacyMissing.netProfit,null);assert.equal(legacyMissing.netMargin,null);
require('../../web/catalog.js');
for (const [previousProfit,profit,sign] of [[-100,-90,1],[-100,-110,-1],[-100,-101,0],[0,0,0],[0,10,1],[0,-10,-1]]) {
  const r=globalThis.Phase0Model.adaptivePrice({oldPrice:100,previousProfit,profit});
  assert.equal(Math.sign(r.price-100),sign);
}
for (const tier of ['T1','T2']) {
  for (const equity of [1999999,2000000,2000001]) {
    const legacy={grossProfit:100,revenue:200,equity};
    P.company(legacy,cfg,tier);
    assert.equal(legacy.netProfit,equity < 2000000 ? 100 : 100-charge);
  }
}
