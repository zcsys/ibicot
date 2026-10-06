'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');
const context = { globalThis: {}, self: undefined, Math, Object };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('engine/model.js', 'utf8'), context, {
  filename: 'engine/model.js',
});
const M = context.Phase0Model;

assert.equal(M.ELEMENTS.length, 4);
assert.equal(M.PRODUCTS.length, 10);
assert.equal(M.T2_SECTORS.length, 10);
for (const [sector, name] of M.T2_SECTORS.entries()) {
  const products = M.T2_PRODUCTS.filter((p) => p.sector === name);
  assert.ok(products.length > 0);
  assert.ok([3,4,5].every(c=>products.some(p=>p.complexity===c)));
  for (const neighbor of M.T2_ADJACENCY[sector]) assert.ok(M.T2_ADJACENCY[neighbor].includes(sector), 'Symmetric adjacency');
}
for (const p of M.PRODUCTS) {
  assert.ok([1,2].includes(p.complexity));
  assert.equal(p.equipmentPrice, p.complexity === 1 ? M.T1_BASIC_MACHINERY : M.T1_COMPOUND_MACHINERY);
  assert.equal(p.role, 'intermediate-only');
}
assert.equal(M.T1_BASIC_MACHINERY, 15000);
assert.equal(M.T1_COMPOUND_MACHINERY, 75000);
assert.equal(M.T2_ROUTE_SETUP, 1000);
assert.equal(M.T2_PRODUCTS.length, 200);
assert.equal(M.T2_PRODUCTS.filter(p=>p.kind==='Good').length,200);
assert.equal(M.T2_PRODUCTS.filter(p=>p.kind==='Service').length,0);
for(const field of ['name','code','recipeKey']) assert.equal(new Set(M.T2_PRODUCTS.map(p=>p[field])).size,200);
assert.deepEqual(Array.from(M.T2_COMPLEXITY_COUNTS), [0,0,20,60,120]);
assert.equal(M.T2_RECIPE_POOL.length,420);
assert.equal(new Set(M.T2_RECIPE_POOL.map(p=>p.recipeKey)).size,420);
assert.equal(new Set(M.T2_RECIPE_POOL.map(p=>M.recipeKey(p.composition))).size,111);
assert.deepEqual([3,4,5].map(c=>M.T2_RECIPE_POOL.filter(p=>p.complexity===c).length),[44,116,260]);
for(const p of M.T2_PRODUCTS) assert.ok(M.T2_RECIPE_BY_KEY[p.recipeKey]);
assert.deepEqual(new Set(M.T2_CATALOGUE.map(p=>p.recipeKey)), new Set(M.T2_RECIPE_POOL.map(r=>r.recipeKey)));
for(const m of M.T2_MATERIAL_COVERAGE) assert.ok(m.active.every((n,i)=>n<=m.possible[i]));
for(const m of M.T2_MATERIAL_COVERAGE) assert.deepEqual(Array.from(m.possible), m.code.length===1 ? [16,44,116] : [4,16,44]);
// Independent coefficient count: four C-1 types and six C-2 types, with
// quantities allowed and order ignored, give 44/116/260 weighted multisets.
let coefficients=Array(6).fill(0);coefficients[0]=1;
for(const cost of [1,1,1,1,2,2,2,2,2,2])
  for(let total=cost;total<=5;total++)coefficients[total]+=coefficients[total-cost];
assert.deepEqual(coefficients.slice(3),[44,116,260]);
assert.equal(M.T2_RECIPE_POOL.length,coefficients.slice(3).reduce((a,b)=>a+b));
for(const sector of M.T2_SECTORS)for(const c of [3,4,5]) {
  const total=M.T2_PRODUCTS.filter(p=>p.sector===sector&&p.complexity===c).reduce((n,p)=>n+p.needWeight,0);
  assert.ok(Math.abs(total-1)<1e-10);
}
const equivalentTotals=M.T2_RECIPE_POOL.filter(p=>M.recipeKey(p.composition)===M.recipeKey({Water:1,Earth:0,Fire:1,Air:1}));
assert.ok(equivalentTotals.some(p=>p.inputs['W+A']&&p.inputs.F));
assert.ok(equivalentTotals.some(p=>p.inputs.W&&p.inputs['F+A']));
assert.equal(new Set(equivalentTotals.map(p=>p.code)).size,equivalentTotals.length);
for (const product of M.T2_PRODUCTS) {
  assert.equal(product.ingredients.reduce((sum, [material, quantity]) => sum + quantity * (material < 4 ? 1 : 2), 0), product.complexity);
  assert.ok(product.ingredients.every(([material, quantity]) => material >= 0 && material < 10 && Number.isInteger(quantity) && quantity > 0));
  assert.equal(product.capacity, M.ECONOMY_DEFAULTS.tier2CompanyCapacity);
}
assert.ok(M.T2_PRODUCTS.every((product) => product.complexity >= 3 && product.complexity <= 5));
assert.ok(M.T2_PRODUCTS.every((product) => product.equipmentPrice === M.T2_ROUTE_SETUP));
assert.equal(M.PRODUCTS.find((product) => product.code === 'W+E').name, 'Ceramic Composite');
assert.equal(M.PRODUCTS.find((product) => product.code === 'F+A').name, 'Active Compounds');
assert.equal(M.demandAtPrice(10, 4, 4, 1), 5);
assert.equal(M.switchingCost(0.5, 0.05, 0.2), 0.125);
assert.equal(M.reliabilityScore(1, 1, 1), 1);
assert.equal(M.nextReliability(0.5, 1, 0.15), 0.575);

const learned = M.adaptivePrice({ oldPrice: 1.25, unitCost: 1, profit: 10,
  previousProfit: 9, direction: 1, sales: 20, stock: 30 });
assert.ok(learned.price > 1.25);
assert.ok(M.adaptivePrice({ oldPrice: 1.25, unitCost: 1, profit: 8,
  previousProfit: 9, direction: 1, sales: 20, stock: 30 }).price < 1.25);
assert.ok(M.T2_PRODUCTS.every(p => p.consumerValue > 0 && !('referencePrice' in p)));
console.log('model contract: ok');
