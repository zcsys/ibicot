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
  assert.deepEqual([3,4,5].map((c) => products.filter((p) => p.complexity === c).length), [6,4,2]);
  for (const neighbor of M.T2_ADJACENCY[sector]) assert.ok(M.T2_ADJACENCY[neighbor].includes(sector), 'Symmetric adjacency');
}
for (const p of M.PRODUCTS) {
  assert.ok([1,2].includes(p.complexity));
  assert.equal(p.equipmentPrice, M.machineryPrice(p.complexity));
  assert.equal(p.role, p.complexity === 1 ? 'retail' : 'intermediate');
}
assert.deepEqual([1,2,3,4,5].map(M.machineryPrice), [15000,75000,375000,1875000,9375000]);
assert.equal(M.T2_PRODUCTS.length, 120);
assert.equal(new Set(M.T2_PRODUCTS.map((product) => product.name)).size, 120);
assert.equal(new Set(M.T2_PRODUCTS.map((product) => product.code)).size, 120);
assert.deepEqual(Array.from(M.T2_COMPLEXITY_COUNTS), [0, 0, 60, 40, 20]);
assert.deepEqual([1, 2, 3, 4, 5].map((c) => M.T2_PRODUCTS.filter((p) => p.complexity === c).length), [0, 0, 60, 40, 20]);
for (const product of M.T2_PRODUCTS) {
  assert.equal(product.ingredients.reduce((sum, [material, quantity]) => sum + quantity * (material < 4 ? 1 : 2), 0), product.complexity);
  assert.ok(product.ingredients.every(([material, quantity]) => material >= 0 && material < 10 && Number.isInteger(quantity) && quantity > 0));
  assert.equal(product.capacity, [3, 2, 1][product.complexity - 3]);
}
assert.ok(M.T2_PRODUCTS.every((product) => product.complexity >= 3 && product.complexity <= 5));
assert.ok(M.T2_PRODUCTS.every((product) => product.equipmentPrice === 15000 * 5 ** (product.complexity - 1)));
assert.equal(M.PRODUCTS.find((product) => product.code === 'W+E').name, 'Clay');
assert.equal(M.PRODUCTS.find((product) => product.code === 'F+A').name, 'Smoke');
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
