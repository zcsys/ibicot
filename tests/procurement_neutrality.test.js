'use strict';
const assert = require('node:assert/strict');
require('../engine/model.js');
const M = globalThis.Phase0Model;
const cfg = { ...M.ECONOMY_DEFAULTS, tier2DemandFactor: 1, markup: .25 };
const expected = [], quantities = { 3: [], 4: [], 5: [] };
// At benchmark costs/quotes, every product offers the same expected gross
// profit per shopping occasion, including heterogeneous buyer elasticities.
for (const product of M.T2_PRODUCTS) {
  const cost = M.referenceTier2Cost(product), profile = M.procurementProfile(product, cfg, cost);
  const quote = cost * (1 + profile.markup);
  assert.equal(profile.markup, M.tier2StartingMarkup(product, cfg));
  let profit = 0;
  for (const elasticity of [.6, 1, 1.4, 2]) for (const chokeFactor of [.8, 1, 1.2]) {
    const demand = M.demandAtPrice(10 * profile.quantityFactor, profile.valuation * chokeFactor, quote, elasticity);
    profit += demand * (quote - cost);
  }
  expected.push(profit); quantities[product.complexity].push(profile.quantityFactor);
  const doubled = M.procurementProfile(product, { ...cfg, tier2DemandFactor: 2 }, cost);
  assert.equal(doubled.valuation, profile.valuation);
  assert.equal(doubled.quantityFactor, 2 * profile.quantityFactor);
}
assert.ok(Math.max(...expected) - Math.min(...expected) < 1e-10,
  'Default engineering and margin compensation must equalize expected opportunity');
const average = values => values.reduce((n, x) => n + x, 0) / values.length;
assert.ok(average(quantities[3]) > average(quantities[4]));
assert.ok(average(quantities[4]) > average(quantities[5]));
// The accounting target cannot change market preferences or pricing behavior.
const p = M.T2_PRODUCTS[0], reference = M.referenceTier2Cost(p);
assert.deepEqual(M.procurementProfile(p, { ...cfg, ageTarget: 1 }, reference),
  M.procurementProfile(p, { ...cfg, ageTarget: 1000000 }, reference));
console.log('Procurement: equal benchmark profit opportunity, lower complex unit orders, independent valuations: ok');

// Recipe composition changes physical flows while preserving benchmark gross
// earnings opportunity. Quotes and external valuation remain independent knobs.
const recipeCfg = { ...cfg, tier2BaseMarkup: 310, tier2MarkupPremium: 0,
  procurementBaseMarkup: 310, procurementMarkupPremium: 0,
  tier2CompoundStandardization: 1.398, procurementCompoundStandardization: 1.398,
  tier2ComplexitySpecialization: .557, procurementComplexitySpecialization: .557 };
const recipeEarnings = [], recipeQuantities = {3:[],4:[],5:[]}, recipeUnitMargins = {3:[],4:[],5:[]};
for (const product of M.T2_PRODUCTS) {
  const cost = M.referenceTier2Cost(product), profile = M.procurementProfile(product, recipeCfg, cost);
  assert.equal(profile.markup, M.tier2StartingMarkup(product, recipeCfg));
  const quote = cost * (1 + profile.markup);
  recipeEarnings.push(M.demandAtPrice(10 * profile.quantityFactor, profile.valuation, quote, 1.4) * cost * profile.markup);
  recipeQuantities[product.complexity].push(profile.quantityFactor);
  recipeUnitMargins[product.complexity].push(cost * profile.markup);
}
assert.ok(Math.max(...recipeEarnings) - Math.min(...recipeEarnings) < 1e-10);
for (const [lower,higher] of [[3,4],[4,5]]) {
  assert.ok(average(recipeQuantities[lower]) > average(recipeQuantities[higher]));
  assert.ok(average(recipeUnitMargins[lower]) < average(recipeUnitMargins[higher]));
}
console.log('Recipe profile: compensated opportunity, declining complex volume, increasing unit margins: ok');

// When baseline procurement data is calibrated independently, actual initial
// engineering costs and intended quotations can still offer equal earnings.
const calibrated = { ...recipeCfg, compoundMarkupPremium:.3450413223140495,
  baseCost:1,dbar:1,manufacturingCostPerUnit:.25,
  procurementBasicReferenceCost:1.875,
  procurementCompoundReferenceCost:2.75*(1+.25+.3450413223140495) };
const nativeExpected = [];
for (const product of M.T2_PRODUCTS) {
  const cost=M.initialTier2Cost(product,calibrated), reference=M.referenceTier2Cost(product,calibrated);
  assert.ok(Math.abs(cost-reference)<1e-12);
  const profile=M.procurementProfile(product,calibrated,reference), quote=cost*(1+M.tier2StartingMarkup(product,calibrated));
  nativeExpected.push(M.demandAtPrice(10*profile.quantityFactor,profile.valuation,quote,1.4)*(quote-cost));
  const shock={...calibrated,baseCost:100,markup:10,compoundMarkupPremium:10};
  assert.equal(M.referenceTier2Cost(product,shock),reference,'Supplier cost/markup changes cannot change authored benchmark inputs');
}
assert.ok(Math.max(...nativeExpected)-Math.min(...nativeExpected)<1e-10);
console.log('Calibrated engineering benchmarks: equal actual starting opportunity, independent of supplier cost shocks: ok');
