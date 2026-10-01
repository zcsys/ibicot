'use strict';

const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');
const context = { globalThis: {}, self: undefined, Math, Object };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('engine/model.js', 'utf8'), context, { filename: 'engine/model.js' });
const M = context.Phase0Model;

assert.equal(M.ELEMENTS.length, 4);
assert.equal(M.PRODUCTS.length, 10);
assert.equal(M.demandAtPrice(10, 4, 4, 1), 5);
assert.equal(M.switchingCost(.5, .05, .2), .125);
assert.equal(M.reliabilityScore(1, 1, 1), 1);
assert.equal(M.nextReliability(.5, 1, .15), .575);

const wholesale = M.wholesalePrice({ oldPrice: 1.25, unitCost: 1, request: 100, fulfilled: 50, k: .35, minMargin: .08, vmax: 1.5 });
assert.ok(wholesale > 1.25 && wholesale >= 1.08);
const noDemand = M.wholesalePrice({ oldPrice: 1.25, unitCost: 1, request: 0, fulfilled: 0, k: .35, minMargin: .08, vmax: 1.5 });
assert.equal(noDemand, 1.25);
const retail = M.retailBotPrice({ oldPrice: 2, finishedCost: 1, stock: 0, salesEMA: 10, k: .35, minMargin: .08, vmax: 1.5 });
assert.ok(retail > 2);

console.log('model contract: ok');
