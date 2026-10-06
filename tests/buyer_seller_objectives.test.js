'use strict';

// Reduced constructed mechanics, not a calibration run. These checks exercise
// the actual public phases without worker ticks or transformed engine sources.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { parseArgs } = require('node:util');
const root = path.resolve(__dirname, '..');
const { values } = parseArgs({ options: {
  runtime: { type: 'string', default: root }, output: { type: 'string' },
} });
const runtime = path.resolve(values.runtime), output = values.output && path.resolve(values.output);
if (output) assert.ok(!fs.existsSync(output), 'JSON output must be a fresh file');
const receipt = file => {
  const bytes = fs.readFileSync(file);
  return { path: file, sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length };
};
const source = Object.fromEntries(['engine/model.js', 'engine/reference_kernel.js',
  'phase0_economy_engine_worker.js', 'tests/worker_harness.js']
  .map(file => [file, receipt(path.join(runtime, file))]));
const { createWorker } = require(path.join(runtime, 'tests/worker_harness.js'));
// A one-tick observation period makes every date eligible for the bot contrast
// below. No observation clock is advanced by this direct-phase fixture.
const fixtureConfig = { seed: 12345, t2FirmCount: 20, endUserCount: 256,
  consumerActivation: 1, sigma: 0, k: .35, priceObservationTicks: 1 };
const worker = createWorker(fixtureConfig);
worker.send({ type: 'setOwnershipEnforcement', enforced: false });
const { W: authentic, cfg } = worker.inspect(), M = worker.model, K = worker.kernel;
let clears = 0, factoryPhases = 0;
const groups = [], records = [];
const near = (a, b) => assert.ok(Math.abs(a - b) <= 1e-8 * Math.max(1, Math.abs(a), Math.abs(b)));

function oneOffer(W, productId = 0) {
  const product = M.T2_PRODUCTS[productId], sector = product.sectorIndex;
  W.t2LineCount = 1; W.t2LineFirm[0] = 0; W.t2LineProduct[0] = productId;
  W.t2FirmLineCount.fill(1); W.t2FirmLines.fill(-1); W.t2FirmLines[0] = 0;
  W.t2Price.fill(NaN); W.t2Price[0] = 4;
  // Deliberately abundant shelf stock isolates price response from stockouts.
  // This is not a warehouse-capacity or physically equilibrated-world fixture.
  W.t2Fin.fill(0); W.t2Fin[0] = 1000000; W.t2FinBasis[0] = .25;
  W.t2Sold.fill(0); W.t2Revenue.fill(0); W.t2COGS.fill(0); W.t2Demand.fill(0);
  W.endBasketCount.fill(2); W.endBasket.fill(sector); W.endNeedProduct.fill(M.PRODUCTS.length + productId);
  W.endPreferredProduct.fill(-1); W.endPreferredSupplier.fill(-1);
  W.t2SectorCount[sector] = 1; W.t2SectorProducts[sector * M.T2_PRODUCTS.length] = productId;
  W.t2SectorProductWeight[sector * M.T2_PRODUCTS.length] = 1;
  const profile = M.procurementProfile(product, cfg, W.t2ReferenceCost[productId]);
  for (let buyer = 0; buyer < cfg.endUserCount; buyer++) {
    W.endQMax[buyer] = (4 + buyer % 17) / profile.quantityFactor;
    W.endChoke[buyer] = (4 + buyer % 7) / profile.valuation;
    W.endEta[buyer] = [.6, 1, 1.4, 2][buyer % 4];
  }
  return W;
}
function clear(W) {
  clears++;
  return K.clearEndUsers(W, cfg, M.PRODUCTS, M.T2_PRODUCTS, 17);
}
function priceFactories(W) {
  factoryPhases++;
  K.tier2BuyMakePrice(W, cfg, M.PRODUCTS, [], M.T2_PRODUCTS, 1);
}
const base = oneOffer(structuredClone(authentic));

// The supplier, seed/tick, private values and available stock stay fixed.
// Repricing multiple sellers can reorder sampled discovery, so these tests do
// not assert monotonic individual sales across changing discovered suppliers.
let previous;
for (const price of [1, 2, 4, 8, 16, 32, 64, 256, 1000000]) {
  const W = structuredClone(base); W.t2Price[0] = price;
  const counts = clear(W);
  if (previous) {
    assert.deepEqual(W.endPotential, previous.endPotential, 'Posted price cannot change the no-price wishlist');
    for (let buyer = 0; buyer < cfg.endUserCount; buyer++) {
      assert.ok(W.endLastQ[buyer] <= previous.endLastQ[buyer], `Integer demand increased at buyer ${buyer}, price ${price}`);
      assert.ok(W.endLastFulfilled[buyer] <= previous.endLastFulfilled[buyer]);
    }
  }
  for (let buyer = 0; buyer < cfg.endUserCount; buyer++) assert.equal(W.endLastQ[buyer], W.endLastFulfilled[buyer]);
  near(counts.consumerPayments, W.t2Sold[0] * price);
  records.push({ case: 'fixed-offer-price', price, units: W.t2Sold[0], consumerPayments: counts.consumerPayments });
  previous = W;
}
assert.ok(records[0].units > records.at(-1).units, 'Price must have a meaningful demand effect');
groups.push('Integer demand is non-increasing in the price of the same discovered stocked offer');

// Accounting may change seller GP; it cannot manufacture higher buyer values
// or rewrite demand to repair the seller's loss at an already posted quote.
const normal = structuredClone(base), costChanged = structuredClone(base);
for (const key of ['t0Cost', 't0InvBasis', 't1UnitCost', 't1ReplacementCost', 't1FinBasis', 'rawBasis',
  't2UnitCost', 't2ReplacementCost', 't2RawBasis', 't2T1Basis', 't2FinBasis']) costChanged[key].fill(1000);
const normalCounts = clear(normal), changedCounts = clear(costChanged);
for (const name of ['endChoke', 'endQMax', 'endEta', 't2ReferenceCost', 'endNeedProduct', 'endPreferredProduct', 'endPreferredSupplier',
  'endPotential', 'endActive', 'endFulfilled', 'endPriceLost', 'endStockUnmet', 'endLastMarket', 'endLastSupplier', 'endLastQ', 'endLastFulfilled']) {
  assert.deepEqual(costChanged[name], normal[name], `Seller accounting leaked into buyer field ${name}`);
}
assert.deepEqual(changedCounts, normalCounts);
assert.deepEqual(costChanged.t2Sold, normal.t2Sold); assert.deepEqual(costChanged.t2Revenue, normal.t2Revenue);
assert.ok(normal.t2Sold[0] > 0); assert.notEqual(costChanged.t2COGS[0], normal.t2COGS[0]);
assert.ok(costChanged.t2Revenue[0] - costChanged.t2COGS[0] < 0);
records.push({ case: 'seller-accounting', units: normal.t2Sold[0], normalProfit: normal.t2Revenue[0] - normal.t2COGS[0],
  changedProfit: costChanged.t2Revenue[0] - costChanged.t2COGS[0], consumerOutcomeExact: true });
groups.push('Identical offers face identical demand after seller cost changes, even when the seller loses money');

// Manual pricing bypasses learner gates. Compare the actual factory phase
// under manual versus bot control with the same evidence: the bot must react,
// while the human's posted price remains free of that automatic adjustment.
const line = authentic.t2FirmLines[0], product = M.T2_PRODUCTS[authentic.t2LineProduct[line]];
const highQuote = 1000000000;
const financialBefore = Object.fromEntries(['t2Cash', 't2EqBook', 't2Fin', 't2Raw', 't2T1Raw']
  .map(name => [name, authentic[name].slice()]));
worker.send({ type: 'player', tier: 'T2', id: 0, controller: 'PLAYER', online: true, code: product.code, price: highQuote });
assert.equal(authentic.t2Price[line], highQuote); assert.equal(authentic.t2PlayerPrice[line], highQuote);
for (const [name, before] of Object.entries(financialBefore)) assert.deepEqual(authentic[name], before, 'Manual quote must not inject resources');
authentic.t2LearnTicks[line] = 100000; authentic.t2LearnSales[line] = 0; authentic.t2LearnProfit[line] = 0;
authentic.t2LearnDemand[line] = 0; authentic.t2LearnStock[line] = 60;
authentic.t2LearnPrevious[line] = 100; authentic.t2LearnDirection[line] = -1;
authentic.t2Fin[line] = 60; authentic.t2FinBasis[line] = 1;
const bot = structuredClone(authentic); bot.t2Controller[0] = 0;
priceFactories(authentic); priceFactories(bot);
assert.equal(authentic.t2Price[line], highQuote); assert.equal(authentic.t2PlayerPrice[line], highQuote);
assert.equal(authentic.t2LearnTicks[line], 100000, 'Manual branch must not consume bot evidence');
assert.ok(bot.t2Price[line] < highQuote, 'The same evidence must actually trigger a bot price reduction');
assert.equal(bot.t2LearnTicks[line], 0, 'Bot must consume the eligible observation window');
const manual = oneOffer(structuredClone(authentic), product.id); manual.t2Price[0] = highQuote;
const beforeCash = manual.t2Cash.slice(), beforeStock = manual.t2Fin[0];
const manualCounts = clear(manual);
assert.equal(manual.t2Sold[0], 0); assert.equal(manualCounts.consumerPayments, 0);
assert.deepEqual(manual.t2Cash, beforeCash); assert.equal(manual.t2Fin[0], beforeStock);
assert.equal(manual.t2Price[0], highQuote);
records.push({ case: 'manual-price', requestedQuote: highQuote, manualQuote: authentic.t2Price[line],
  botQuoteWithSameEvidence: bot.t2Price[line], units: manual.t2Sold[0], consumerPayments: manualCounts.consumerPayments });
groups.push('Manual T2 prices bypass an eligible bot adjustment and may earn zero sales');

assert.equal(worker.inspect().tick, 0);
for (const expected of Object.values(source)) assert.deepEqual(receipt(expected.path), expected, 'Runtime changed during test');
const result = { format: 'ibicot-buyer-seller-objectives-mechanics', version: 1, status: 'PASS',
  scope: 'Reduced constructed direct mechanics only; no calibration or universal market-sales monotonicity claim',
  node: process.version, test: receipt(__filename), runtime, source, fixtureConfig, groups, records,
  counts: { freshWorkers: 1, workerSteps: 0, kernelTicks: 0, directConsumerClears: clears, directT2FactoryPhases: factoryPhases, adminPriceMessages: 1 },
  boundaries: ['Manual prices remain subject to the existing cost floors; no below-cost loss-leader command is tested.',
    'Constructed buyer preferences and abundant stock isolate demand. Ordinary repricing may later change cost-inconsistent quotes.',
    'External procurement payments use the existing exogenous source, not a finite household wallet.'] };
if (output) fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
console.log('PASS buyer/seller objectives: 3 reduced mechanics groups, zero worker/kernel ticks');
