'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { createWorker } = require('./worker_harness');

const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 });
const total = (rows, key) => rows.reduce((value, row) => value + row[key], 0);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < Math.max(1e-6, Math.abs(expected) * 1e-10), `${actual} != ${expected}`);
worker.send({ type: 'watchCompanies', watches: { T0: [0], T1: [0] } });
let previousCash = worker.snapshot().tiers.t0.cash, previousEquity = worker.snapshot().tiers.t0.equity;
for (let i = 0; i < 35; i++) {
  worker.step();
  const s = worker.snapshot(), latest = s.analyticsHistory.at(-1);
  for (const tier of ['t0', 't1', 't2', 'endUsers']) assert.deepEqual(latest.tiers[tier], s.tiers[tier]);
  for (const industry of s.tier2Industries) {
    const historyIndustry = latest.t2Industries.find(row => row.name === industry.name);
    near(historyIndustry.fulfilled, industry.fulfilled);
    near(historyIndustry.active, industry.active);
  }
  near(s.tiers.t0.cash - previousCash, s.tiers.t0.operatingCashFlow);
  near(s.tiers.t0.equity - previousEquity, s.tiers.t0.grossProfit);
  near(s.tiers.t0.cogs, total(s.t0Companies,'cogs'));
  near(s.tiers.t0.grossProfit, s.tiers.t0.revenue - s.tiers.t0.cogs);
  near(s.expandedDetails['T0:0'].cogs, total(s.expandedDetails['T0:0'].elementData,'cogs'));
  near(s.tiers.t0.extractionSpending, s.tiers.t0.revenue - s.tiers.t0.operatingCashFlow);
  for (const key of ['cogs', 'grossProfit', 'extractionSpending', 'operatingCashFlow']) {
    near(total(s.t0Companies, key), s.tiers.t0[key]);
    near(total(s.elements, key), s.tiers.t0[key]);
  }
  assert.ok(!('productionCost' in s.tiers.t0));
  assert.equal(s.tiers.t0.bought,0);
  near(s.tiers.t0.made,s.tiers.t0.productionByElement.reduce((n,q)=>n+q,0));
  if(i===0) assert.ok(s.tiers.t0.made>0);
  near(s.expandedDetails['T0:0'].equity, s.t0Companies.find(company => company.id === 0).equity);
  previousCash = s.tiers.t0.cash; previousEquity = s.tiers.t0.equity;
  for (const key of ['cash', 'equity', 'made', 'sold', 'revenue', 'grossProfit']) near(total(s.cohorts, key), s.tiers.t1[key]);
  near(total(s.products, 'volume'), s.tiers.t1.sold);
  near(total(s.products, 'consumerVolume') + s.tiers.t2.sold, s.tiers.endUsers.fulfilled);
}
for (const tier of ['T0', 'T1']) {
  const detail = worker.self.snapshot.expandedDetails[tier + ':0'];
  assert.equal(detail.history.length, 36);
  assert.equal(new Set(detail.history.map(point => point.tick)).size, 36);
  near(detail.history.at(-1).made, detail.made);
  worker.publish();
  assert.equal(detail.history.length, 36, 'Same-tick reports must not duplicate company history');
}
// Expanded portfolios must appear in cohort totals, not just native lines.
const { W } = worker.inspect();
W.t1Operates[4] = 1; W.t1Fin[4] = 123; W.t1Sold[4] = 7; W.t1Rev[4] = 35; W.t1COGS[4] = 21;
let s = worker.snapshot();
for (const key of ['cash', 'equity', 'sold', 'revenue', 'grossProfit']) near(total(s.cohorts, key), s.tiers.t1[key]);
near(total(s.cohorts, 'finished'), s.tiers.t1.finished);

// Execute the actual dashboard renderer against real worker reports.
const html = fs.readFileSync('phase0_economy_engine.html', 'utf8');
const app = fs.readFileSync('phase0_economy_engine_app.js', 'utf8');
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(new Set(ids).size, ids.length, 'Dashboard IDs must be unique');
const nodes = Object.fromEntries(ids.map(id => [id, { value: '', textContent: '' }]));
const charts = {};
const context = {
  $: id => { assert.ok(nodes[id], `Missing dashboard element ${id}`); return nodes[id]; },
  M: worker.model, displayProduct: code => worker.model.PRODUCTS.find(p => p.code === code).name,
  drawLine: (id, history, series, labels) => { assert.ok(nodes[id], `Missing chart ${id}`); charts[id] = { history, series, labels }; },
  drawComparison: id => assert.ok(nodes[id], `Missing comparison ${id}`),
};
vm.createContext(context);
vm.runInContext(app.slice(app.indexOf('  function fmtMoney('), app.indexOf('  const chartColors')) +
  app.slice(app.indexOf('  const meaningfulRatio'), app.indexOf('  function render(s)')), context);
context.s = s;
vm.runInContext('renderDashboard(s)', context);
const money = value => '$' + value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
assert.equal(nodes.economyCash.textContent, money(s.tiers.t0.cash + s.tiers.t1.cash + s.tiers.t2.cash));
assert.equal(nodes.economySpending.textContent, money(s.tiers.endUsers.revenue), 'Consumer spending excludes intermediate revenue');
assert.equal(charts.equityChart.series.length, 3, 'All producer tiers must appear in overview graphs');
assert.equal(charts.productionChart.series.length, 3);
for (const [i,tier] of ['t0','t1','t2'].entries()) near(charts.productionChart.series[i].at(-1),s.tiers[tier].made);
assert.equal(nodes.t0Made.textContent,s.tiers.t0.made.toLocaleString());
assert.deepEqual(Array.from(charts.t0FinanceChart.labels),['Revenue','COGS','Gross profit','Extraction spending','Operating cash flow']);
nodes.overviewTier.value = 't1'; nodes.t1PriceProduct.value = '4';
vm.runInContext('renderDashboard(s)', context);
assert.equal(charts.equityChart.series.length, 1);
near(charts.equityChart.series[0].at(-1), s.tiers.t1.equity);
assert.equal(charts.retailChart.labels[0], worker.model.PRODUCTS[4].name);
near(charts.retailChart.series[0].at(-1), s.analyticsHistory.at(-1).materialPrices[4]);

worker.send({ type: 'reset', cfg: { t2FirmCount: 1000, endUserCount: 20000 } });
context.s = worker.snapshot();
vm.runInContext('renderDashboard(s)', context);
for (const id of ['fillRate', 'orderFillRate', 'unitFillRate', 't1Margin', 't1CustomerFill', 'priceLossShare', 'stockUnmetShare', 'wavg', 'ravg'])
  assert.equal(nodes[id].textContent, '—', `Undefined ${id} must not imply measured zero`);
assert.equal(worker.self.snapshot.expandedDetails['T0:0'].history.length, 1, 'Reset clears company chart history');
worker.send({ type: 'watchCompanies', watches: { T0: [], T1: [] } });
worker.send({ type: 'watchCompanies', watches: { T0: [0], T1: [] } });
assert.equal(worker.self.snapshot.expandedDetails['T0:0'].history.length, 1, 'Reopening starts a new company history');
console.log('dashboard totals, scope and histories: ok');
