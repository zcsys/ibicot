'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { createWorker } = require('./worker_harness');
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const total = (rows, key) => rows.reduce((n, row) => n + row[key], 0);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < Math.max(1e-6, Math.abs(expected) * 1e-10), `${actual} != ${expected}`);
const check = s => {
  assert.deepEqual(s.productCategories.map(row => row.complexity), [1, 2, 3, 4, 5]);
  assert.deepEqual(s.productCategories.map(row => row.products), [4, 6, 20, 20, 20]);
  for (const [tier, rows] of [['t1', s.productCategories.slice(0, 2)], ['t2', s.productCategories.slice(2)]]) {
    for (const key of ['made', 'sold', 'revenue', 'cogs', 'grossProfit']) near(total(rows, key), s.tiers[tier][key]);
    near(total(rows, 'readyStock'), s.tiers[tier].finished);
    for (const row of rows) {
      near(row.machineryPrice, worker.model.machineryPrice(row.complexity));
      near(row.capacity, row.lines * row.unitCapacity);
      near(row.margin, row.revenue ? row.grossProfit / row.revenue : 0);
      near(row.profitPerLine, row.grossProfit / row.lines);
      near(row.soldPerLine, row.sold / row.lines);
    }
  }
};
check(worker.snapshot());
for (let i = 0; i < 36; i++) worker.step();
let s = worker.snapshot();
check(s);
// A Purified Water firm adds a Ceramic Composite line; its activity belongs to C-2, regardless of home cohort.
const { W } = worker.inspect();
const before = s.productCategories[1];
W.t1Operates[4] = 1; W.t1Fin[4] = 123; W.t1Sold[4] = 7; W.t1Rev[4] = 35; W.t1COGS[4] = 21;
s = worker.snapshot();
near(s.productCategories[1].lines, before.lines + 1);
near(s.productCategories[1].sold, before.sold + 7);
near(s.productCategories[1].revenue, before.revenue + 35);
near(s.productCategories[1].cogs, before.cogs + 21);
check(s);
const app = fs.readFileSync('phase0_economy_engine_app.js', 'utf8');
const html = fs.readFileSync('phase0_economy_engine.html', 'utf8');
const nodes = Object.fromEntries([...html.matchAll(/\bid="([^"]+)"/g)].map(match => [match[1], {value: '', innerHTML: ''}]));
nodes.categoryMetric = {value: 'profitPerLine', selectedOptions: [{textContent: 'Gross profit / line · $ / tick'}]};
let comparison;
const context = vm.createContext({$: id => {assert.ok(nodes[id]); return nodes[id];},
  meaningfulRatio: (n, d) => d > 0 ? n / d : NaN,
  drawComparison: (id, rows, metric) => { comparison = {id, rows, metric}; }, s});
vm.runInContext(app.slice(app.indexOf('  const tableSortColumns'), app.indexOf('  function updateSortIndicators')) +
  app.slice(app.indexOf('  function fmtMoney('), app.indexOf('  const chartColors')) +
  app.slice(app.indexOf('  function renderComparisons'), app.indexOf('  function render(s)')), context);
vm.runInContext('renderComparisons(s)', context);
for (const [id, expectedRows] of [['tierComparison', 3], ['productCategories', 5]]) {
  const rows = [...nodes[id].innerHTML.matchAll(/<tr>(.*?)<\/tr>/g)];
  assert.equal(rows.length, expectedRows);
  const headCount = html.slice(0, html.indexOf(`<tbody id="${id}"`)).split('<thead>').at(-1).match(/<th>/g).length;
  for (const row of rows) assert.equal((row[1].match(/<t[dh]>/g) || []).length, headCount);
  assert.ok(!/undefined|NaN/.test(nodes[id].innerHTML));
}
assert.equal(comparison.rows[1].active, 0, 'C-2 has no public demand');
assert.ok(Number.isNaN(comparison.rows[1].fillRate), 'C-2 public fulfillment is unavailable');
assert.equal(comparison.metric, 'profitPerLine');
vm.runInContext("tableSort.productCategories = {key: 'machineryPrice', direction: -1}; renderComparisons(s)", context);
assert.match(nodes.productCategories.innerHTML, /^<tr><th>C-5/);
worker.send({type: 'reset', cfg: {t2FirmCount: 1000, endUserCount: 20000}});
context.s = worker.snapshot();
vm.runInContext('renderComparisons(s)', context);
assert.ok(!/undefined|NaN/.test(nodes.productCategories.innerHTML));
assert.match(nodes.productCategories.innerHTML, /<td>—<\/td>/);
console.log('category totals, portfolio attribution, comparison rendering and sorting: ok');
