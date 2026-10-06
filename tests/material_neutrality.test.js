'use strict';
const assert=require('node:assert/strict');
const {createWorker}=require('./worker_harness');
const coefficients=[.06300942264646832,-.04392290011188903,.04295221508707713,-.10469018339337738,
 .04315910125231126,.07731750977525126,-.029468014643701048,-.02466162998123834,-.03479081289591769,.02910958450527392];
const w=createWorker({t2FirmCount:1,endUserCount:1,compoundMarkupPremium:.3450413223140495,
 procurementBasicReferenceCost:1.875,procurementCompoundReferenceCost:4.386363636363636,
 tier2MaterialBalance:coefficients,procurementMaterialBalance:coefficients,
 tier2BaseMarkup:303.35619212885484,procurementBaseMarkup:303.35619212885484,
 tier2MarkupPremium:0,procurementMarkupPremium:0,
 tier2CompoundStandardization:1.4464096129187596,procurementCompoundStandardization:1.4464096129187596,
 tier2ComplexitySpecialization:.5712676196653342,procurementComplexitySpecialization:.5712676196653342,
 tier2DemandFactor:1.0963105123649461});
const {W,cfg}=w.inspect(),M=w.model,flows=new Float64Array(10),margins=[],quantities={3:[],4:[],5:[]},unitProfits={3:[],4:[],5:[]};
// Measured shopping exposure of the full 1m-channel initial population, before
// cost shocks, stock drawdowns and adaptive competition. This is an analytic
// nominal calibration check, never a reduced-world profit experiment.
const exposure=1978.4239861114008;
for(const product of M.T2_PRODUCTS) {
 const cost=M.initialTier2Cost(product,cfg), reference=M.referenceTier2Cost(product,cfg);
 assert.ok(Math.abs(cost-reference)<1e-12);
 const profile=M.procurementProfile(product,cfg,reference), q=exposure*profile.quantityFactor;
 for(const [material,units] of product.ingredients)flows[material]+=units*q;
 margins.push(q*cost*M.tier2StartingMarkup(product,cfg));
 quantities[product.complexity].push(q);unitProfits[product.complexity].push(cost*profile.markup);
}
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
for(let i=0;i<4;i++)near(flows[i],flows[0]);
for(let i=4;i<10;i++)near(flows[i],flows[4]);
const rawFlows=Float64Array.from(flows.slice(0,4));
for(let compound=4;compound<10;compound++)for(const [element,units] of Object.entries(M.PRODUCTS[compound].inputs))rawFlows[M.ELEMENTS.indexOf(element)]+=flows[compound]*units;
for(const flow of rawFlows)near(flow,rawFlows[0]);
for(let material=0;material<10;material++) {
 const unitProfit=material<4?.375:2.75*(cfg.markup+cfg.compoundMarkupPremium);
 const equity=material<4?20000:80000;
 near(flows[material]*unitProfit/(100*equity),1/M.TIME.ticksPerAge);
}
near(rawFlows.reduce((s,q)=>s+q)*.25/(20*1000000),1/M.TIME.ticksPerAge);
near(margins.reduce((s,gp)=>s+gp)/(61950*302500),1/M.TIME.ticksPerAge);
assert.ok(Math.max(...margins)-Math.min(...margins)<1e-8);
const average=xs=>xs.reduce((a,b)=>a+b)/xs.length;
for(const [lower,higher] of [[3,4],[4,5]]) {
 assert.ok(average(quantities[lower])>average(quantities[higher]));
 assert.ok(average(unitProfits[lower])<average(unitProfits[higher]));
}
const frozen=W.t2ReferenceCost.slice();cfg.markup=10;cfg.baseCost=100;cfg.compoundMarkupPremium=10;
for(let p=0;p<M.T2_PRODUCTS.length;p++)near(W.t2ReferenceCost[p],frozen[p]);
console.log('Nominal all-material and raw symmetry, compensated Tier 2 opportunity, complexity ordering and frozen procurement benchmarks: ok');
