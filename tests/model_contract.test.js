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
assert.equal(M.demandAtPrice(10, 4, 4, 1), 5);
assert.equal(M.switchingCost(0.5, 0.05, 0.2), 0.125);
assert.equal(M.reliabilityScore(1, 1, 1), 1);
assert.equal(M.nextReliability(0.5, 1, 0.15), 0.575);

const wholesale = M.wholesalePrice({
  oldPrice: 1.25,
  unitCost: 1,
  request: 100,
  fulfilled: 50,
  k: 0.35,
  minMargin: 0.08,
  vmax: 1.5,
});
assert.ok(wholesale > 1.25 && wholesale >= 1.08);
const noDemand = M.wholesalePrice({
  oldPrice: 1.25,
  unitCost: 1,
  request: 0,
  fulfilled: 0,
  inventory: 2,
  inventoryTarget: 1,
  k: 0.35,
  minMargin: 0.08,
  vmax: 1.5,
});
assert.ok(
  noDemand < 1.25 && noDemand >= 1.08,
  'excess coverage should pull an inactive market toward its normal margin',
);
const excessStock = M.wholesalePrice({
  oldPrice: 1.5,
  unitCost: 1,
  request: 100,
  fulfilled: 100,
  inventory: 1000,
  k: 0.35,
  minMargin: 0.08,
  normalMargin: 0.25,
});
assert.ok(
  excessStock < 1.5 && excessStock >= 1.08,
  'ample stock and full fulfillment should lower wholesale price',
);
const retail = M.retailBotPrice({
  oldPrice: 2,
  finishedCost: 1,
  stock: 0,
  salesEMA: 10,
  k: 0.35,
  minMargin: 0.08,
  vmax: 1.5,
});
assert.ok(retail > 2);

console.log('model contract: ok');
