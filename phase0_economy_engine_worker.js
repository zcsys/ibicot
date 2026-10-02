'use strict';

// Browser worker for the source-controlled simulation.
importScripts('./engine/model.js', './engine/reference_kernel.js');

const M = self.Phase0Model;
const E = M.ELEMENTS;
const P = M.PRODUCTS;
const PB = Object.fromEntries(P.map((p) => [p.code, p]));
const PI = Object.fromEntries(P.map((p, i) => [p.code, i]));
const EI = Object.fromEntries(E.map((e, i) => [e, i]));
const T2P = self.Phase0Model.T2_PRODUCTS;
const T2_SECTORS = self.Phase0Model.T2_SECTORS;
const T1P = P.map(product => ({ name: product.companyName, product: product.code }));
const T0P = [
  ['Atlas Resource Robotics', [E[0],E[1],E[2],E[3]]],
  ['Axiom Extraction Systems', [E[0],E[1],E[2],E[3]]],
  ['Civic Materials Network', [E[0],E[1],E[2]]],
  ['Colony Resource Authority', [E[0],E[1],E[3]]],
  ['Gaia Extraction Works', [E[0],E[2],E[3]]],
  ['Integrated Resource Robotics', [E[1],E[2],E[3]]],
  ['Hydro Mineral Works', [E[0],E[1]]],
  ['Solar Resource Works', [E[0],E[2]]],
  ['Atmospheric Resource Works', [E[0],E[3]]],
  ['Thermal Mineral Works', [E[1],E[2]]],
  ['Mineral Air Works', [E[1],E[3]]],
  ['Integrated Thermal Works', [E[2],E[3]]],
  ['Aquifer Robotics', [E[0]]],
  ['River Basin Robotics', [E[0]]],
  ['Mineral Quarry Robotics', [E[1]]],
  ['Subsurface Mining Robotics', [E[1]]],
  ['Solar Heat Robotics', [E[2]]],
  ['Geothermal Energy Robotics', [E[2]]],
  ['Atmospheric Capture Robotics', [E[3]]],
  ['Air Separation Robotics', [E[3]]],
].map((x, i) => ({ id: i, name: x[0], elements: x[1] }));
const N0 = 20,
  N1 = 1000,
  N2_FIRMS = 50000,
  N_END_USERS = M.COLONY_STORY.population,
  MAX_T2_LINES = 250000,
  NP = 10,
  NE = 4,
  MONTH = 30;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const complexity = (code) => M.complexity(PB[code]);
const markup = (code, c) => c.markup + c.compoundMarkupPremium * Math.max(0, complexity(code) - 1);
const quantW = (x, floor = 0) => {
  if (!Number.isFinite(x)) return x;
  const r = Math.round(x * 1e5) / 1e5;
  const fq = Math.ceil((floor - 1e-12) * 1e5) / 1e5;
  return Math.max(r, fq);
};
const quantR = (x, floor = 0) => {
  if (!Number.isFinite(x)) return x;
  const r = Math.round(x * 100) / 100;
  const fq = Math.ceil((floor - 1e-12) * 100) / 100;
  return Math.max(r, fq);
};
const hashSeed = (seed, tick) => {
  let x = ((seed >>> 0) ^ Math.imul((tick + 1) >>> 0, 0x9e3779b1)) >>> 0;
  x = Math.imul(x ^ (x >>> 16), 0x85ebca6b) >>> 0;
  x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35) >>> 0;
  return (x ^ (x >>> 16)) >>> 0;
};
class RNG {
  constructor(seed) {
    this.s = seed >>> 0 || 1;
  }
  next() {
    let x = this.s;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.s = x >>> 0;
    return this.s / 4294967296;
  }
  uniform(a, b) {
    return a + (b - a) * this.next();
  }
}
const qDemand = (qmax, ref, p, eta) =>
  qmax > 0 && ref > 0 && p >= 0 && eta > 0 ? qmax / (1 + Math.pow(p / ref, eta)) : 0;

let cfg,
  tick = 0,
  month = 0,
  running = false,
  mode = 'fixed',
  targetTPS = 30,
  timer = null,
  W,
  sourceState = { activeOrders: 0, fulfilledOrders: 0 };
let equipment,
  eqBook,
  controller,
  online,
  playerPrices,
  selectedTierControl = 'T1',
  selectedT2Id = 0,
  selectedId = 0,
  lastSnapshot = null;
let lastReportAt = 0,
  lastReportTick = 0;
let analyticsHistory = [];
let tier2CompanyHistory = [], tier2HistoryCompany = -1;
let prevT0Inventory = new Float64Array(N0 * 4),
  prevT1Finished = new Float64Array(N1 * NP),
  prevT1FinishedCohort = new Float64Array(N1 * NP);
let tickStartT0Inventory = new Float64Array(N0 * 4),
  tickStartT1Finished = new Float64Array(N1 * NP);
let lastTickT0Produced = new Float64Array(N0 * 4),
  lastTickT1Made = new Float64Array(N1 * NP);
let watchedCompanies = { T0: new Set(), T1: new Set() };
let watchedCompanyHistory = {};
let workerStats = { steps: 0, lastTickMs: 0, totalTickMs: 0 };
let tier2Query = { page: 0, pageSize: 50, search: '', sector: '', controller: '', sort: 'id', descending: false };
function tier2Company(id, detailed = true) {
  if (!Number.isInteger(id) || id < 0 || id >= cfg.t2FirmCount) return null;
  const products = [];
  let finished = 0, made = 0, sold = 0, revenue = 0, cogs = 0, raw = 0, value = 0, capacity = 0;
  const required = new Map();
  for (let slot = 0; slot < W.t2FirmLineCount[id]; slot++) {
    const line = W.t2FirmLines[id * 5 + slot], product = T2P[W.t2LineProduct[line]];
    products.push({ line, code: product.code, name: product.name, primaryMaterial: PB[product.primaryMaterial].name, complexity: product.complexity,
      recipe: product.ingredients.map(([p,q]) => `${q} ${P[p].name}`).join(' + '),
      price: W.t2Price[line], unitCost: W.t2FinBasis[line] || W.t2UnitCost[line], capacity: product.capacity,
      finished: W.t2Fin[line], made: W.t2Made[line], sold: W.t2Sold[line],
      revenue: W.t2Revenue[line], cogs: W.t2COGS[line], grossProfit: W.t2Revenue[line] - W.t2COGS[line],
      margin: W.t2Revenue[line] ? (W.t2Revenue[line] - W.t2COGS[line]) / W.t2Revenue[line] : 0,
      utilization: W.t2Made[line] / product.capacity,
      demandEMA: W.t2DemandEMA[line], salesEMA: W.t2SalesEMA[line],
      stockCoverage: W.t2SalesEMA[line] > 0 ? W.t2Fin[line] / W.t2SalesEMA[line] : null, reliability: W.t2Rel[line] });
    capacity += product.capacity;
    if (detailed) for (const [material, quantity] of product.ingredients) {
      const need = required.get(material) || { consumed: 0, capacityNeed: 0 };
      need.consumed += W.t2Made[line] * quantity; need.capacityNeed += product.capacity * quantity;
      required.set(material, need);
    }
    finished += W.t2Fin[line]; made += W.t2Made[line]; sold += W.t2Sold[line];
    revenue += W.t2Revenue[line]; cogs += W.t2COGS[line]; value += W.t2Fin[line] * W.t2Price[line];
  }
  const inputs = [];
  for (let material = 0; material < NP; material++) {
    const basic = material < 4, index = id * (basic ? NE : NP) + material;
    const quantity = (basic ? W.t2Raw : W.t2T1Raw)[index], basis = (basic ? W.t2RawBasis : W.t2T1Basis)[index];
    raw += quantity; value += quantity * basis;
    if (detailed && (quantity > 0 || required.has(material))) {
      const supplier = W.t2Preferred[id * NP + material], seller = supplier < 0 ? -1 : Math.floor(supplier / NP);
      const need = required.get(material) || { consumed: 0, capacityNeed: 0 };
      inputs.push({ name: P[material].name, sourceTier: 'T1', stock: quantity, basis,
        value: quantity * basis, consumed: need.consumed, capacityNeed: need.capacityNeed,
        capacityCoverage: need.capacityNeed ? quantity / need.capacityNeed : 0, supplier, supplierId: seller,
        supplierName: seller < 0 ? null :
          T1P[Math.floor(seller / 100)].name + ' ' + String(seller % 100 + 1).padStart(3, '0'),
        supplierPrice: supplier < 0 ? null : W.t1Price[supplier],
        supplierReliability: supplier < 0 ? null : W.t1Rel[supplier] });
    }
  }
  const eligibleEquipment = detailed ? T2P.filter((p) => p.complexity <= W.t2Capability[id] &&
    M.relatedSector(W.t2Sector[id], p.sectorIndex) && !self.Phase0ReferenceKernel.hasTier2Product(W, id, p.id))
    .map((p) => ({ code: p.code, name: p.name, price: p.equipmentPrice, complexity: p.complexity })) : [];
  return { tier: 'T2', id, name: T2_SECTORS[W.t2Sector[id]] + ' Robot Factory ' + String(id + 1).padStart(5, '0'),
    sector: T2_SECTORS[W.t2Sector[id]], capability: W.t2Capability[id],
    controller: W.t2Controller[id] ? 'PLAYER' : 'BOT', online: !!W.t2Online[id],
    cash: W.t2Cash[id], eqBook: W.t2EqBook[id], equipmentBookValue: W.t2EqBook[id],
    equity: W.t2Cash[id] + W.t2EqBook[id] + value, inventory: raw + finished, raw, finished,
    made, sold, revenue, cogs, grossProfit: revenue - cogs, capacity,
    utilization: capacity ? made / capacity : 0, margin: revenue ? (revenue - cogs) / revenue : 0,
    lineCount: products.length, sellThrough: finished + sold ? sold / (finished + sold) : 0,
    reliability: products.reduce((n, p) => n + p.reliability, 0) / Math.max(1, products.length),
    native: products[0]?.code, price: products[0]?.price, equipment: products.map((p) => p.code), products, inputs, eligibleEquipment };
}
function tier2Page() {
  const query = tier2Query, search = query.search.toLowerCase(), matches = [];
  for (let id = 0; id < cfg.t2FirmCount; id++) {
    const sector = T2_SECTORS[W.t2Sector[id]], control = W.t2Controller[id] ? 'PLAYER' : 'BOT';
    if (query.sector && query.sector !== sector || query.controller && query.controller !== control) continue;
    let text = sector + ' Robot Factory ' + String(id + 1).padStart(5, '0') + ' ' + control;
    for (let slot = 0; slot < W.t2FirmLineCount[id]; slot++)
      text += ' ' + T2P[W.t2LineProduct[W.t2FirmLines[id * 5 + slot]]].name;
    if (search && !text.toLowerCase().includes(search)) continue;
    matches.push(id);
  }
  if (query.sort !== 'id') {
    const values = new Map();
    const sortValue = (id) => {
      if (!values.has(id)) values.set(id, tier2Company(id, false)[query.sort]);
      return values.get(id);
    };
    matches.sort((a, b) => typeof sortValue(a) === 'string' ? sortValue(a).localeCompare(sortValue(b)) || a - b : sortValue(a) - sortValue(b) || a - b);
  }
  if (query.descending) matches.reverse();
  const page = Math.min(Math.max(0, query.page), Math.max(0, Math.ceil(matches.length / query.pageSize) - 1));
  return { page, pageSize: query.pageSize, total: matches.length,
    rows: matches.slice(page * query.pageSize, (page + 1) * query.pageSize).map((id) => tier2Company(id, false)) };
}

function defaultCfg() {
  return {
    seed: 12345,
    dbar: 1,
    theta: 0.15,
    sigma: 0.005,
    dmin: 0.7,
    dmax: 1.4,
    capacity: M.ECONOMY_DEFAULTS.capacity,
    targetInventory: M.ECONOMY_DEFAULTS.targetInventory,
    maxInventory: M.ECONOMY_DEFAULTS.maxInventory,
    baseCost: 1,
    retailTargetInventory: M.ECONOMY_DEFAULTS.retailTargetInventory,
    retailMaxInventory: M.ECONOMY_DEFAULTS.retailMaxInventory,
    retailInitialCash: M.ECONOMY_DEFAULTS.retailInitialCash,
    basicEquipmentCapacity: M.ECONOMY_DEFAULTS.basicEquipmentCapacity,
    compoundEquipmentCapacity: M.ECONOMY_DEFAULTS.compoundEquipmentCapacity,
    manufacturingCostPerUnit: 0.25,
    minWholesaleLot: M.ECONOMY_DEFAULTS.minWholesaleLot,
    k: 0.35,
    alpha: 0.15,
    markup: 0.25,
    compoundMarkupPremium: 0.15,
    wholesalePriceResponse: 0.05,
    priceObservationTicks: 30,
    consumerSearchOffers: 5,
    vmin: 0.9,
    vmax: 1.5,
    demandQtyMin: 1,
    demandQtyMax: 10,
    elasticityMin: 1,
    elasticityMax: 2,
    taumin: 0.05,
    taumax: 0.2,
    reliabilityAlpha: 0.15,
    switchingStableBand: 0.025,
    endUserCount: N_END_USERS,
    t2FirmCount: N2_FIRMS,
    initialCash: M.ECONOMY_DEFAULTS.initialCash,
    inventoryCoverageTicks: M.ECONOMY_DEFAULTS.inventoryCoverageTicks,
    tier2WorkingCashTicks: M.ECONOMY_DEFAULTS.tier2WorkingCashTicks,
    tier2MinimumCash: M.ECONOMY_DEFAULTS.tier2MinimumCash,
    consumerActivation: 0.1,
    tier2DemandFactor: 0.45,
    tier2ReservationPremium: 0.45,
  };
}
function normalizeConfig(c) {
  const defaults = defaultCfg(), d = { ...defaults, ...c };
  for (const key of Object.keys(defaults)) if (!Number.isFinite(d[key])) d[key] = defaults[key];
  d.seed = Math.floor(d.seed) >>> 0;
  for (const key of ['capacity','targetInventory','maxInventory','retailTargetInventory','retailMaxInventory','retailInitialCash','initialCash','baseCost','manufacturingCostPerUnit','tier2MinimumCash'])
    d[key] = Math.max(0, d[key]);
  for (const key of ['alpha','reliabilityAlpha','consumerActivation']) d[key] = clamp(d[key], 0, 1);
  d.dmin = Math.max(0.01, d.dmin); d.dmax = Math.max(d.dmin, d.dmax); d.dbar = clamp(d.dbar, d.dmin, d.dmax);
  d.theta = clamp(d.theta, 0, 1); d.sigma = Math.max(0, d.sigma);
  d.taumin = Math.max(0, d.taumin); d.taumax = Math.max(d.taumin, d.taumax);
  d.switchingStableBand = Math.max(1e-9, d.switchingStableBand);
  d.tier2DemandFactor = clamp(d.tier2DemandFactor, 0.01, 1);
  d.tier2ReservationPremium = Math.max(0, d.tier2ReservationPremium);
  d.markup = Math.max(0, d.markup); d.compoundMarkupPremium = Math.max(0, d.compoundMarkupPremium);
  d.k = clamp(d.k, 0, 1);
  d.priceObservationTicks = Math.max(1, Math.min(360, Math.floor(d.priceObservationTicks)));
  d.consumerSearchOffers = Math.max(1, Math.min(20, Math.floor(d.consumerSearchOffers)));
  d.vmin = Math.max(0.01, d.vmin); d.vmax = Math.max(d.vmin, d.vmax);
  d.maxInventory = Math.max(d.targetInventory, d.maxInventory);
  d.retailMaxInventory = Math.max(d.retailTargetInventory, d.retailMaxInventory);
  d.taumin = Math.min(d.taumin, d.taumax);
  d.taumax = Math.max(d.taumin, d.taumax);
  d.demandQtyMin = Math.max(1, Math.min(100, Math.floor(d.demandQtyMin)));
  d.demandQtyMax = Math.max(d.demandQtyMin, Math.min(100, Math.floor(d.demandQtyMax)));
  d.elasticityMin = Math.max(0.05, Math.min(10, d.elasticityMin));
  d.elasticityMax = Math.max(d.elasticityMin, Math.min(10, d.elasticityMax));
  d.minWholesaleLot = Math.max(1, Math.floor(d.minWholesaleLot));
  d.inventoryCoverageTicks = Math.max(1, Math.min(30, d.inventoryCoverageTicks));
  d.tier2WorkingCashTicks = Math.max(1, Math.min(360, d.tier2WorkingCashTicks));
  d.endUserCount = Math.max(1, Math.min(N_END_USERS, Math.floor(d.endUserCount || N_END_USERS)));
  d.t2FirmCount = Math.max(1, Math.min(N2_FIRMS, Math.floor(d.t2FirmCount || N2_FIRMS)));
  d.basicEquipmentCapacity = Math.max(1, Math.floor(d.basicEquipmentCapacity));
  d.compoundEquipmentCapacity = Math.max(1, Math.floor(d.compoundEquipmentCapacity));
  d.wholesalePriceResponse = clamp(
    Number.isFinite(+d.wholesalePriceResponse) ? +d.wholesalePriceResponse : 0.05,
    0.001,
    1,
  );
  return d;
}
function priceLearningViews(prefix, count) {
  return { [`${prefix}LearnProfit`]: new Float64Array(count),
    [`${prefix}LearnSales`]: new Float64Array(count),
    [`${prefix}LearnTicks`]: new Uint16Array(count),
    [`${prefix}LearnPrevious`]: new Float64Array(count),
    [`${prefix}LearnDemand`]: new Float64Array(count),
    [`${prefix}LearnStock`]: new Float64Array(count),
    [`${prefix}LearnStep`]: new Float64Array(count),
    [`${prefix}LearnDirection`]: new Int8Array(count),
    [`${prefix}Demand`]: new Float64Array(count),
    [`${prefix}DemandEMA`]: new Float64Array(count) };
}
function sourceViews() {
  return {
    ...priceLearningViews('t0', N0 * NE),
    ...priceLearningViews('t1', N1 * NP),
    ...priceLearningViews('t2', MAX_T2_LINES),
    difficulty: new Float64Array(4),
    t0Inv: new Float64Array(N0 * 4),
    t0Cash: new Float64Array(N0),
    t0Price: new Float64Array(N0 * 4),
    t0Cost: new Float64Array(N0 * 4),
    t0InvBasis: new Float64Array(N0 * 4),
    t0COGS: new Float64Array(N0 * 4),
    t0SalesEMA: new Float64Array(N0 * 4),
    t0PrevPrice: new Float64Array(N0 * 4),
    t0Rel: new Float64Array(N0 * 4),
    t0Stability: new Float64Array(N0 * 4),
    t0Req: new Float64Array(4),
    t0FundedReq: new Float64Array(4),
    t0Ful: new Float64Array(4),
    t0Sold: new Float64Array(N0 * 4),
    t0Revenue: new Float64Array(N0 * 4),
    raw: new Float64Array(N1 * 4),
    rawBasis: new Float64Array(N1 * 4),
    t1Cash: new Float64Array(N1),
    t1EqBook: new Float64Array(N1),
    t1Controller: new Uint8Array(N1),
    t1Operates: new Uint8Array(N1 * 10),
    t1Price: new Float64Array(N1 * 10),
    t1PrevPrice: new Float64Array(N1 * 10),
    t1PriceStability: new Float64Array(N1 * 10),
    t1Rel: new Float64Array(N1 * 10),
    t1UnitCost: new Float64Array(N1 * 10),
    t1ReplacementCost: new Float64Array(N1 * 10),
    t1Fin: new Float64Array(N1 * 10),
    t1FinBasis: new Float64Array(N1 * 10),
    t1SalesEMA: new Float64Array(N1 * 10),
    t1Sold: new Float64Array(N1 * 10),
    t1Rev: new Float64Array(N1 * 10),
    t1COGS: new Float64Array(N1 * 10),
    t1IntermediateSold: new Float64Array(NP),
    t1IntermediateRevenue: new Float64Array(NP),
    t1InputNeed: new Float64Array(N1 * 4),
    t1PurchaseReq: new Float64Array(N1 * 4),
    t1LastBuy: new Float64Array(N1 * 4),
    t1Bought: new Float64Array(N1),
    preferredWholesale: new Int32Array(N1 * 4),
    playerPrice: new Float64Array(N1 * 10),
    active: new Float64Array(NP),
    potential: new Float64Array(NP),
    fulfilled: new Float64Array(NP),
    priceLost: new Float64Array(NP),
    stockUnmet: new Float64Array(NP),
    t0RelAttempts: new Float64Array(N0 * 4),
    t0RelFulfilled: new Float64Array(N0 * 4),
    t0RelChecks: new Float64Array(N0 * 4),
    t0RelAvailable: new Float64Array(N0 * 4),
    t0RelPriceSum: new Float64Array(N0 * 4),
    t0RelPriceSamples: new Uint32Array(N0 * 4),
    t1RelAttempts: new Float64Array(N1 * 10),
    t1RelFulfilled: new Float64Array(N1 * 10),
    t1RelAvailChecks: new Float64Array(N1 * 10),
    t1RelAvailable: new Float64Array(N1 * 10),
    t1RelPriceSum: new Float64Array(N1 * 10),
    t1RelPriceSamples: new Uint32Array(N1 * 10),
    // Sparse Tier 2 firm/product-line state.  Product lines are capped rather
    // than allocating one record for every firm/product combination.
    t2Cash: new Float64Array(N2_FIRMS),
    t2Bought: new Float64Array(N2_FIRMS),
    t2EqBook: new Float64Array(N2_FIRMS),
    t2LastSaleTick: new Uint32Array(N2_FIRMS),
    t2Raw: new Float64Array(N2_FIRMS * NE),
    t2RawBasis: new Float64Array(N2_FIRMS * NE),
    t2T1Raw: new Float64Array(N2_FIRMS * NP),
    t2T1Basis: new Float64Array(N2_FIRMS * NP),
    t2Controller: new Uint8Array(N2_FIRMS),
    t2Capability: new Uint8Array(N2_FIRMS),
    t2Sector: new Uint8Array(N2_FIRMS),
    t2LineFirm: new Uint16Array(MAX_T2_LINES),
    t2LineProduct: new Uint8Array(MAX_T2_LINES),
    t2Fin: new Float64Array(MAX_T2_LINES),
    t2FinBasis: new Float64Array(MAX_T2_LINES),
    t2UnitCost: new Float64Array(MAX_T2_LINES),
    t2ReplacementCost: new Float64Array(MAX_T2_LINES),
    t2Price: new Float64Array(MAX_T2_LINES),
    t2PlayerPrice: new Float64Array(MAX_T2_LINES),
    t2SalesEMA: new Float64Array(MAX_T2_LINES),
    t2Sold: new Float64Array(MAX_T2_LINES),
    t2Revenue: new Float64Array(MAX_T2_LINES),
    t2COGS: new Float64Array(MAX_T2_LINES),
    t2LineCount: 0,
    t2SectorProducts: new Uint8Array(T2_SECTORS.length * T2P.length),
    t2SectorProductWeight: new Float64Array(T2_SECTORS.length * T2P.length),
    t2SectorCount: new Uint8Array(T2_SECTORS.length),
    // End users are intentionally compact and are never copied to snapshots.
    t2Online: new Uint8Array(N2_FIRMS),
    t2FirmLines: new Int32Array(N2_FIRMS * 5),
    t2FirmLineCount: new Uint8Array(N2_FIRMS),
    t2Preferred: new Int32Array(N2_FIRMS * NP),
    t2Made: new Float64Array(MAX_T2_LINES),
    t2Rel: new Float64Array(MAX_T2_LINES),
    t2RelAttempts: new Uint32Array(MAX_T2_LINES),
    t2RelFulfilled: new Uint32Array(MAX_T2_LINES),
    t2RelAvailable: new Uint32Array(MAX_T2_LINES),
    t2RelPriceSum: new Float64Array(MAX_T2_LINES),
    t2RelPriceSamples: new Uint32Array(MAX_T2_LINES),
    t2MonthSold: new Float64Array(MAX_T2_LINES),
    t2MonthlyCapacity: new Float64Array(MAX_T2_LINES),
    endBasketCount: new Uint8Array(N_END_USERS),
    endBasket: new Uint8Array(N_END_USERS * 5),
    endPreferredProduct: new Int16Array(N_END_USERS * 5),
    endPreferredSupplier: new Int32Array(N_END_USERS * 5),
    endLastMarket: new Int16Array(N_END_USERS),
    endLastSupplier: new Int32Array(N_END_USERS),
    endLastQ: new Uint8Array(N_END_USERS),
    endLastFulfilled: new Uint8Array(N_END_USERS),
    endPrimarySector: new Uint8Array(N_END_USERS),
    endSecondarySector: new Uint8Array(N_END_USERS),
    endQMax: new Float32Array(N_END_USERS),
    endChoke: new Float32Array(N_END_USERS),
    endEta: new Float32Array(N_END_USERS),
    endPotential: new Float64Array(NP + T2P.length),
    endActive: new Float64Array(NP + T2P.length),
    endFulfilled: new Float64Array(NP + T2P.length),
    endPriceLost: new Float64Array(NP + T2P.length),
    endStockUnmet: new Float64Array(NP + T2P.length),
  };
}
function initEngine() {
  W = sourceViews();
  sourceState = { activeOrders: 0, fulfilledOrders: 0 };
}
function reset(c) {
  cfg = normalizeConfig(c);
  tick = 0;
  month = 0;
  running = false;
  analyticsHistory = [];
  watchedCompanyHistory = {};
  tier2CompanyHistory = []; tier2HistoryCompany = -1;
  prevT0Inventory.fill(0);
  prevT1Finished.fill(0);
  prevT1FinishedCohort.fill(0);
  tickStartT0Inventory.fill(0);
  tickStartT1Finished.fill(0);
  lastTickT0Produced.fill(0);
  lastTickT1Made.fill(0);
  self.Phase0ReferenceKernel.zero(W);
  for (const tier of ['t0', 't1', 't2']) {
    W[`${tier}LearnPrevious`].fill(NaN);
    W[`${tier}LearnStep`].fill(1);
    for (let i = 0; i < W[`${tier}LearnDirection`].length; i++)
      W[`${tier}LearnDirection`][i] = ((i + cfg.seed) % 2) ? 1 : -1;
  }
  W.difficulty.fill(cfg.dbar);
  W.t0Cash.fill(cfg.initialCash);
  W.t0Rel.fill(0.5);
  W.t0Stability.fill(1);
  W.t0Req.fill(0);
  W.t0Ful.fill(0);
  W.t0PrevPrice.fill(NaN);
  W.t0Price.fill(NaN);
  W.t0Cost.fill(0);
  for (let i = 0; i < N0; i++)
    for (let e = 0; e < NE; e++)
      if (T0P[i].elements.includes(E[e])) {
        const idx = i * 4 + e;
        const cost = cfg.baseCost * cfg.dbar;
        W.t0Cost[idx] = cost;
        W.t0DemandEMA[idx] = cfg.targetInventory / T0P[i].elements.length / cfg.inventoryCoverageTicks;
        W.t0Price[idx] = quantW(cost * (1 + cfg.markup));
        W.t0PrevPrice[idx] = W.t0Price[idx];
      }
  equipment = Array.from({ length: N1 }, (_, id) => [T1P[Math.floor(id / 100)].product]);
  eqBook = new Float64Array(N1);
  controller = new Uint8Array(N1);
  online = new Uint8Array(N1);
  playerPrices = Array.from({ length: N1 }, () => ({}));
  W.t1Cash.fill(cfg.retailInitialCash);
  W.t1EqBook.fill(0);
  W.t1Controller.fill(0);
  W.t1Operates.fill(0);
  W.t1Price.fill(NaN);
  W.t1PrevPrice.fill(NaN);
  W.t1PriceStability.fill(1);
  W.t1Rel.fill(0);
  W.t1UnitCost.fill(0);
  W.t1Fin.fill(0);
  W.t1FinBasis.fill(0);
  W.t1SalesEMA.fill(0);
  W.t1LastBuy.fill(NaN);
  W.preferredWholesale.fill(-1);
  W.playerPrice.fill(NaN);
  const initialW = new Float64Array(4);
  for (let e = 0; e < 4; e++) {
    let sum = 0,
      n = 0;
    for (let i = 0; i < N0; i++)
      if (T0P[i].elements.includes(E[e])) {
        sum += W.t0Price[i * 4 + e];
        n++;
      }
    initialW[e] = sum / n;
  }
  for (let id = 0; id < N1; id++) {
    const code = equipment[id][0],
      pi = PI[code],
      p = PB[code],
      eq = p.equipmentPrice,
      uc =
        Object.entries(p.inputs).reduce((s, [e, r]) => s + initialW[EI[e]] * r, 0) +
        cfg.manufacturingCostPerUnit,
      price = quantR(uc * (1 + markup(code, cfg)), uc);
    eqBook[id] = eq;
    W.t1EqBook[id] = eq;
    W.t1Operates[id * 10 + pi] = 1;
    W.t1Rel[id * 10 + pi] = 0.5;
    W.t1UnitCost[id * 10 + pi] = uc;
    W.t1Price[id * 10 + pi] = price;
    W.t1PrevPrice[id * 10 + pi] = price;
  }
  for (let id = 0; id < N1; id++) {
    for (let e = 0; e < NE; e++) {
      let best = -1,
        bp = Infinity;
      for (let s = 0; s < N0; s++)
        if (T0P[s].elements.includes(E[e])) {
          const p = W.t0Price[s * 4 + e];
          if (p < bp - 1e-12 || (Math.abs(p - bp) <= 1e-12 && s < best)) {
            best = s;
            bp = p;
          }
        }
      W.preferredWholesale[id * 4 + e] = best;
    }
  }
  initializeTier2();
  initializeConsumers();
  for (let firm = 0; firm < N1; firm++) {
    const p = Math.floor(firm / 100);
    W.t1DemandEMA[firm * NP + p] = p < 4 ? 60 : 200;
  }
  lastReportAt = performance.now();
  lastReportTick = 0;
  workerStats = { steps: 0, lastTickMs: 0, totalTickMs: 0 };
  sourceState = { activeOrders: 0, fulfilledOrders: 0, activatedConsumers: 0, consumerPayments: 0 };
  publish();
}
function initializeTier2() {
  W.t2LineCount = 0;
  W.t2FirmLines.fill(-1); W.t2Preferred.fill(-1); W.t2PlayerPrice.fill(NaN); W.t2Rel.fill(0.5);
  W.t2SectorCount.fill(0);
  for (const product of T2P) {
    const count = W.t2SectorCount[product.sectorIndex]++, index = product.sectorIndex * T2P.length + count;
    W.t2SectorProducts[index] = product.id;
    W.t2SectorProductWeight[index] = (count ? W.t2SectorProductWeight[index - 1] : 0) + product.demandWeight;
  }
  let firm = 0;
  for (const band of M.T2_CAPABILITY_BANDS) {
    const c = band.complexity;
    const count = c === 5 ? cfg.t2FirmCount - firm : Math.floor(cfg.t2FirmCount * band.share);
    const products = T2P.filter((p) => p.complexity === c);
    const floor = Math.min(100, Math.floor(count / products.length));
    const weights = products.map((p) => p.demandWeight * (0.8 + 0.4 * hashSeed(cfg.seed, 4000000 + p.id) / 4294967296));
    const remainder = count - floor * products.length, weight = weights.reduce((sum, value) => sum + value, 0);
    const quota = products.map((p, index) => floor + Math.floor(remainder * weights[index] / weight));
    for (let left = count - quota.reduce((sum, n) => sum + n, 0), k = 0; left > 0; left--, k++) quota[k % quota.length]++;
    products.forEach((core, p) => {
      for (let n = 0; n < quota[p]; n++, firm++) {
        W.t2Capability[firm] = c; W.t2Sector[firm] = core.sectorIndex;
        self.Phase0ReferenceKernel.addTier2Line(W, cfg, firm, core, false);
        const total = band.startingLines;
        const candidates = T2P.filter((x) => x.id !== core.id && x.complexity <= c && M.relatedSector(core.sectorIndex, x.sectorIndex));
        for (let extra = 1; extra < total; extra++) {
          const eligible = candidates.filter((x) => !self.Phase0ReferenceKernel.hasTier2Product(W, firm, x.id));
          const weights = eligible.map((x) => x.needWeight * (x.sectorIndex === core.sectorIndex ? 2 : 1));
          let draw = hashSeed(cfg.seed, firm * 5 + extra) / 4294967296 * weights.reduce((sum, weight) => sum + weight, 0);
          let product = eligible.at(-1);
          for (let index = 0; index < eligible.length; index++) { draw -= weights[index]; if (draw < 0) { product = eligible[index]; break; } }
          if (product) self.Phase0ReferenceKernel.addTier2Line(W, cfg, firm, product, false);
        }
        const portfolio = Array.from({ length: W.t2FirmLineCount[firm] }, (_, slot) =>
          T2P[W.t2LineProduct[W.t2FirmLines[firm * 5 + slot]]]);
        W.t2Cash[firm] = M.tier2StartingCash(portfolio, cfg);
      }
    });
  }
}
function initializeConsumers() {
  W.endPreferredProduct.fill(-1); W.endPreferredSupplier.fill(-1);
  W.endLastMarket.fill(-1); W.endLastSupplier.fill(-1);
  for (let id = 0; id < cfg.endUserCount; id++) {
    const a = hashSeed(cfg.seed, 8000000 + id), b = hashSeed(cfg.seed, 9000000 + id);
    const count = 2 + a % 4;
    let draw = hashSeed(cfg.seed, 10000000 + id) / 4294967296 * M.T2_SECTOR_WEIGHTS.reduce((sum, weight) => sum + weight, 0), primary = T2_SECTORS.length - 1;
    for (let sector = 0; sector < T2_SECTORS.length; sector++) { draw -= M.T2_SECTOR_WEIGHTS[sector]; if (draw < 0) { primary = sector; break; } }
    W.endBasketCount[id] = count; W.endPrimarySector[id] = primary; W.endBasket[id * 5] = primary;
    const sectors = M.T2_ADJACENCY[primary];
    for (let slot = 1; slot < count; slot++) {
      let sector = slot === 1 ? sectors[b % sectors.length] : (primary + 1 + ((b >>> (slot * 3)) % (T2_SECTORS.length - 1))) % T2_SECTORS.length;
      let duplicate = true;
      while (duplicate) {
        duplicate = false;
        for (let previous = 0; previous < slot; previous++) if (W.endBasket[id * 5 + previous] === sector) duplicate = true;
        if (duplicate) sector = (sector + 1) % T2_SECTORS.length;
      }
      W.endBasket[id * 5 + slot] = sector;
    }
    W.endSecondarySector[id] = W.endBasket[id * 5 + 1];
    W.endQMax[id] = cfg.demandQtyMin + a % (cfg.demandQtyMax - cfg.demandQtyMin + 1);
    W.endChoke[id] = cfg.vmin + b / 4294967296 * (cfg.vmax - cfg.vmin);
    W.endEta[id] = cfg.elasticityMin + ((a >>> 8) % 1000) / 1000 * (cfg.elasticityMax - cfg.elasticityMin);
  }
}
function updateLive(c) {
  if (c.endUserCount !== undefined && c.endUserCount !== cfg.endUserCount ||
      c.t2FirmCount !== undefined && c.t2FirmCount !== cfg.t2FirmCount) throw new Error('Population changes require Reset.');
  cfg = normalizeConfig({ ...cfg, ...c });
  for (let id = 0; id < cfg.endUserCount; id++) {
    const a = hashSeed(cfg.seed, 8000000 + id), b = hashSeed(cfg.seed, 9000000 + id);
    W.endQMax[id] = cfg.demandQtyMin + a % (cfg.demandQtyMax - cfg.demandQtyMin + 1);
    W.endChoke[id] = cfg.vmin + b / 4294967296 * (cfg.vmax - cfg.vmin);
    W.endEta[id] = cfg.elasticityMin + ((a >>> 8) % 1000) / 1000 * (cfg.elasticityMax - cfg.elasticityMin);
  }
}
function rawSum(id) {
  const b = id * 4;
  return W.raw[b] + W.raw[b + 1] + W.raw[b + 2] + W.raw[b + 3];
}
function finSum(id) {
  const b = id * 10;
  let s = 0;
  for (let p = 0; p < NP; p++) if (W.t1Operates[b + p]) s += W.t1Fin[b + p];
  return s;
}
function step() {
  const tickStarted = performance.now();
  const t = tick + 1;
  tickStartT0Inventory.set(W.t0Inv);
  tickStartT1Finished.set(W.t1Fin);
  self.Phase0ReferenceKernel.tick({
    W,
    cfg,
    tick: t,
    products: P,
    profiles: T0P,
    t2Products: T2P,
    state: sourceState,
  });
  for (let i = 0; i < N0; i++)
    for (let e = 0; e < NE; e++) {
      const idx = i * NE + e;
      lastTickT0Produced[idx] =
        Math.max(0, (W.t0Inv[idx] || 0) - (tickStartT0Inventory[idx] || 0) + (W.t0Sold[idx] || 0));
    }
  for (let id = 0; id < N1; id++)
    for (let p = 0; p < NP; p++) {
      const idx = id * NP + p;
      lastTickT1Made[idx] =
        Math.max(0, (W.t1Fin[idx] || 0) - (tickStartT1Finished[idx] || 0) + (W.t1Sold[idx] || 0));
    }
  tick = t;
  month = Math.floor(t / MONTH);
  workerStats.steps++;
  workerStats.lastTickMs = performance.now() - tickStarted;
  workerStats.totalTickMs += workerStats.lastTickMs;
}
function marketAverages() {
  const wVol = [0, 0, 0, 0],
    wRev = [0, 0, 0, 0],
    rVol = new Float64Array(10),
    rRev = new Float64Array(10),
    rCounts = new Uint16Array(10);
  for (let i = 0; i < N0; i++)
    for (let e = 0; e < 4; e++)
      if (T0P[i].elements.includes(E[e])) {
        const idx = i * 4 + e;
        wVol[e] += W.t0Sold[idx];
        wRev[e] += W.t0Revenue[idx];
      }
  for (let id = 0; id < N1; id++)
    for (let p = 0; p < NP; p++)
      if (W.t1Operates[id * 10 + p]) {
        rVol[p] += W.t1Sold[id * 10 + p];
        rRev[p] += W.t1Rev[id * 10 + p];
        rCounts[p]++;
      }
  const wP = wVol.map((v, e) => (v ? wRev[e] / v : W.t0Price.filter ? 0 : 0));
  for (let e = 0; e < 4; e++)
    if (!wVol[e]) {
      let s = 0,
        n = 0;
      for (let id = 0; id < N0; id++)
        if (T0P[id].elements.includes(E[e])) {
          s += W.t0Price[id * 4 + e];
          n++;
        }
      wP[e] = n ? s / n : NaN;
    }
  const rP = new Float64Array(10);
  for (let p = 0; p < 10; p++) {
    if (rVol[p]) rP[p] = rRev[p] / rVol[p];
    else {
      let s = 0,
        n = 0;
      for (let id = 0; id < N1; id++)
        if (W.t1Operates[id * 10 + p] && Number.isFinite(W.t1Price[id * 10 + p])) {
          s += W.t1Price[id * 10 + p];
          n++;
        }
      rP[p] = n ? s / n : NaN;
    }
  }
  let wv = wVol[0] + wVol[1] + wVol[2] + wVol[3],
    wr = wRev[0] + wRev[1] + wRev[2] + wRev[3],
    rv = 0,
    rr = 0;
  for (let p = 0; p < 10; p++) {
    rv += rVol[p];
    rr += rRev[p];
  }
  return {
    wVol,
    wRev,
    rVol,
    rRev,
    wP,
    rP,
    wAvg: wv ? wr / wv : wP.reduce((sum, price) => sum + price, 0) / NE,
    rAvg: rv ? rr / rv : rP.reduce((sum, price) => sum + price, 0) / NP,
    wVolume: wv,
    rVolume: rv,
  };
}
function sumArray(a) {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += Number(a[i]) || 0;
  return s;
}
function hhi(vols) {
  const total = sumArray(vols);
  if (total <= 0) return 0;
  let h = 0;
  for (let i = 0; i < vols.length; i++) {
    const sh = (Number(vols[i]) || 0) / total;
    h += sh * sh;
  }
  return h;
}
function marketReliability(values, volumes) {
  let total = 0,
    w = 0,
    active = 0;
  for (let i = 0; i < values.length; i++) {
    const r = Number(values[i]);
    if (!Number.isFinite(r)) continue;
    active++;
    const v = Math.max(0, Number(volumes[i]) || 0);
    total += v;
    w += v * r;
  }
  return active
    ? total > 0
      ? w / total
      : values.reduce((a, v) => a + (Number(v) || 0), 0) / active
    : 0;
}
function markedT0Equity(wP) {
  let total = 0;
  for (let i = 0; i < N0; i++) {
    const b = i * 4;
    let inv = 0;
    for (let e = 0; e < 4; e++) inv += W.t0Inv[b + e] * (wP[e] || 0);
    total += W.t0Cash[i] + inv;
  }
  return total;
}
function cohortAnalytics(m) {
  const cohorts = [];
  for (let cidx = 0; cidx < 10; cidx++) {
    const start = cidx * 100,
      end = start + 100,
      pIdx = PI[T1P[cidx].product],
      product = T1P[cidx].product;
    let price = 0,
      uc = 0,
      finished = 0,
      raw = 0,
      cash = 0,
      equity = 0,
      made = 0,
      sold = 0,
      revenue = 0,
      cogs = 0,
      rel = 0,
      stability = 0,
      eqCount = 0,
      players = 0;
    for (let id = start; id < end; id++) {
      const b = id * NP + pIdx,
        rb = id * 4;
      const stock = W.t1Fin[b] || 0,
        basis = W.t1FinBasis[b] || 0;
      const p = W.t1Price[b];
      if (Number.isFinite(p)) {
        price += p;
        eqCount++;
      }
      uc += W.t1UnitCost[b] || 0;
      finished += stock;
      for (let e = 0; e < 4; e++) raw += W.raw[rb + e] || 0;
      cash += W.t1Cash[id] || 0;
      const invVal = (() => {
        let v = 0;
        for (let e = 0; e < 4; e++) v += (W.raw[rb + e] || 0) * (m.wP[e] || 0);
        for (let p2 = 0; p2 < NP; p2++)
          if (W.t1Operates[id * NP + p2]) v += (W.t1Fin[id * NP + p2] || 0) * (m.rP[p2] || 0);
        return v;
      })();
      equity += W.t1Cash[id] + W.t1EqBook[id] + invVal;
      // Cohorts group companies, so their totals include every installed line.
      for (let p = 0; p < NP; p++) {
        if (!W.t1Operates[id * NP + p]) continue;
        const index = id * NP + p;
        made += lastTickT1Made[index] || 0;
        sold += W.t1Sold[index] || 0;
        revenue += W.t1Rev[index] || 0;
        cogs += W.t1COGS[index] || 0;
        if (p !== pIdx) finished += W.t1Fin[index] || 0;
      }
      rel += W.t1Rel[b] || 0;
      stability += W.t1PriceStability[b] || 0;
      if (controller[id]) players++;
      prevT1FinishedCohort[b] = W.t1Fin[b] || 0;
    }
    const marketVol = m.rVol[pIdx] || 0;
    cohorts.push({
      code: product,
      displayName: P[pIdx].name,
      name: T1P[cidx].name,
      firms: end - start,
      equipment: complexity(product) === 1 ? 'Basic' : 'Compound',
      avgPrice: eqCount ? price / eqCount : NaN,
      avgUnitCost: uc / (end - start),
      finished,
      raw,
      inventory: finished + raw,
      cash,
      equity,
      made,
      sold,
      revenue,
      cogs,
      grossProfit: revenue - cogs,
      margin: revenue ? (revenue - cogs) / revenue : 0,
      reliability: rel / (end - start),
      priceStability: stability / (end - start),
      marketShare: marketVol ? W.t1Sold.subarray(start * NP, end * NP)
        .reduce((total, value, index) => total + (index % NP === pIdx ? value : 0), 0) / marketVol : 0,
      players,
    });
  }
  return cohorts;
}
function buildAnalytics(m) {
  const t0Inventory = sumArray(W.t0Inv),
    t0Cash = sumArray(W.t0Cash),
    t0Sold = sumArray(W.t0Sold),
    t0Revenue = sumArray(W.t0Revenue);
  const t0Produced = new Array(4).fill(0),
    t0Vol = [0, 0, 0, 0],
    t0HHI = [0, 0, 0, 0],
    t0Rel = [[], [], [], []];
  for (let i = 0; i < N0; i++)
    for (let e = 0; e < 4; e++)
      if (T0P[i].elements.includes(E[e])) {
        const idx = i * 4 + e;
        const cur = W.t0Inv[idx] || 0,
          prev = prevT0Inventory[idx] || 0,
          sold = W.t0Sold[idx] || 0;
        t0Produced[e] += lastTickT0Produced[idx] || 0;
        t0Vol[e] += sold;
        t0Rel[e].push(W.t0Rel[idx]);
        prevT0Inventory[idx] = cur;
      }
  for (let e = 0; e < 4; e++) {
    const vols = [];
    for (let i = 0; i < N0; i++)
      if (T0P[i].elements.includes(E[e])) vols.push(W.t0Sold[i * 4 + e] || 0);
    t0HHI[e] = hhi(vols);
  }
  let t1Raw = 0,
    t1Finished = 0,
    t1Cash = 0,
    t1Sold = 0,
    t1Revenue = 0,
    t1COGS = 0,
    t1Made = 0,
    t1Equity = 0,
    activeFirms = 0,
    players = 0,
    relWeighted = 0,
    relN = 0;
  for (let id = 0; id < N1; id++) {
    const rb = id * 4;
    let raw = 0,
      finished = 0,
      eqv = W.t1Cash[id] + W.t1EqBook[id];
    for (let e = 0; e < 4; e++) {
      raw += W.raw[rb + e] || 0;
      eqv += (W.raw[rb + e] || 0) * (m.wP[e] || 0);
    }
    t1Raw += raw;
    t1Finished += finished;
    t1Cash += W.t1Cash[id] || 0;
    if (W.t1Controller[id]) players++;
    let any = false;
    for (let p = 0; p < NP; p++)
      if (W.t1Operates[id * NP + p]) {
        const idx = id * NP + p,
          fin = W.t1Fin[idx] || 0;
        finished += fin;
        eqv += fin * (m.rP[p] || 0);
        t1Sold += W.t1Sold[idx] || 0;
        t1Revenue += W.t1Rev[idx] || 0;
        t1COGS += W.t1COGS[idx] || 0;
        t1Made += lastTickT1Made[idx] || 0;
        prevT1Finished[idx] = fin;
        relWeighted += W.t1Rel[idx] || 0;
        relN++;
        any = true;
      }
    if (any) activeFirms++;
    t1Finished += finished;
    t1Equity += eqv;
  }
  let t2Cash = 0, t2Inventory = 0, t2Sold = 0, t2Revenue = 0, t2COGS = 0, t2Equity = 0, t2Made = 0;
  for (let line = 0; line < W.t2LineCount; line++) {
    t2Inventory += W.t2Fin[line] || 0; t2Sold += W.t2Sold[line] || 0;
    t2Equity += W.t2Fin[line] * W.t2Price[line]; t2Made += W.t2Made[line];
    t2Revenue += W.t2Revenue[line] || 0; t2COGS += W.t2COGS[line] || 0;
  }
  for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
    t2Cash += W.t2Cash[firm]; t2Equity += W.t2Cash[firm] + W.t2EqBook[firm];
    for (let p = 0; p < NP; p++) {
      const basic = p < NE, index = firm * (basic ? NE : NP) + p;
      const quantity = (basic ? W.t2Raw : W.t2T1Raw)[index];
      t2Inventory += quantity; t2Equity += quantity * (basic ? W.t2RawBasis : W.t2T1Basis)[index];
    }
  }
  const potential = sumArray(W.endPotential || W.potential),
    active = sumArray(W.endActive || W.active),
    fulfilled = sumArray(W.endFulfilled || W.fulfilled),
    priceLost = sumArray(W.endPriceLost || W.priceLost),
    stockUnmet = sumArray(W.endStockUnmet || W.stockUnmet);
  const orderTotal = sourceState.activeOrders,
    fulfilledOrders = sourceState.fulfilledOrders;
  const cohort = cohortAnalytics(m);
  const latest = {
    tick,
    wholesaleAvg: m.wAvg,
    retailAvg: m.rAvg,
    wVolume: m.wVolume,
    rVolume: m.rVolume,
    t0Inventory,
    t1Inventory: t1Raw + t1Finished,
    t0Equity: markedT0Equity(m.wP),
    t1Equity,
    t2Cash,
    t2Equity,
    t2Made,
    t2Inventory,
    t2Sold,
    t2Revenue,
    t2COGS,
    t0Cash,
    t1Cash,
    retailPotential: potential,
    retailActive: active,
    retailFulfilled: fulfilled,
    priceLost,
    stockUnmet,
    t1GrossProfit: t1Revenue - t1COGS,
    avgT0Reliability: t0Rel.flat().length
      ? t0Rel.flat().reduce((a, v) => a + (Number(v) || 0), 0) / t0Rel.flat().length
      : 0,
    avgT1Reliability: relN ? relWeighted / relN : 0,
  };
  if (analyticsHistory.at(-1)?.tick === tick) analyticsHistory[analyticsHistory.length - 1] = latest;
  else analyticsHistory.push(latest);
  if (analyticsHistory.length > 240) analyticsHistory.shift();
  return {
    cohort,
    latest,
    t0Inventory,
    t0Cash,
    t0Sold,
    t0Revenue,
    t0Equity: markedT0Equity(m.wP),
    t0Produced,
    t0Vol,
    t0HHI,
    t1Raw,
    t1Finished,
    t1Cash,
    activeFirms,
    players,
    t1Made,
    t1Sold,
    t1Revenue,
    t1COGS,
    t1Equity,
    t2Cash,
    t2Equity,
    t2Made,
    t2Inventory,
    t2Sold,
    t2Revenue,
    t2COGS,
    t2Lines: W.t2LineCount,
    potential,
    active,
    fulfilled,
    priceLost,
    stockUnmet,
    orderTotal,
    fulfilledOrders,
    unitFillRate: active ? fulfilled / active : 0,
    orderFillRate: orderTotal ? fulfilledOrders / orderTotal : 0,
    priceLossShare: potential ? priceLost / potential : 0,
    stockUnmetShare: active ? stockUnmet / active : 0,
    retailRevenue: sourceState.consumerPayments || 0,
    difficultyMean: (W.difficulty[0] + W.difficulty[1] + W.difficulty[2] + W.difficulty[3]) / 4,
    difficultyMin: Math.min(...W.difficulty),
    difficultyMax: Math.max(...W.difficulty),
  };
}
function companyDetail(tier, id) {
  if (tier === 'T2') return tier2Company(id);
  id = Math.max(0, id | 0);
  if (tier === 'T0') {
    const co = T0P[id];
    if (!co) return null;
    const marketPrices = marketAverages().wP;
    const elements = [];
    let inventory = 0,
      prod = 0,
      sold = 0,
      revenue = 0,
      equity = W.t0Cash[id];
    for (const e of E) {
      if (!co.elements.includes(e)) continue;
      const i = EI[e],
        idx = id * 4 + i,
        stock = W.t0Inv[idx] || 0,
        invVal = stock * (marketPrices[i] || 0);
      inventory += stock;
      prod += lastTickT0Produced[idx] || 0;
      sold += W.t0Sold[idx] || 0;
      revenue += W.t0Revenue[idx] || 0;
      equity += invVal;
      elements.push({
        element: e,
        stock,
        cost: W.t0Cost[idx],
        price: W.t0Price[idx],
        production: lastTickT0Produced[idx] || 0,
        sold: W.t0Sold[idx] || 0,
        revenue: W.t0Revenue[idx] || 0,
        reliability: W.t0Rel[idx] || 0,
        stability: W.t0Stability[idx] || 0,
        reliabilityAttempts: t0RelAttemptsCount(id, i),
      });
    }
    return {
      tier: 'T0',
      id,
      name: co.name,
      elements: co.elements,
      cash: W.t0Cash[id],
      inventory,
      equity,
      made: prod,
      sold,
      revenue,
      productionCost: elements.reduce((total, element) => total + element.production * element.cost, 0),
      operatingCashFlow: revenue - elements.reduce((total, element) => total + element.production * element.cost, 0),
      capacity: cfg.capacity,
      targetInventory: cfg.targetInventory,
      maxInventory: cfg.maxInventory,
      status: 'ACTIVE',
      elementData: elements,
    };
  }
  const piBase = T1P[Math.floor(id / 100)];
  if (!piBase) return null;
  const raw = [];
  for (const e of E) {
    const i = EI[e],
      idx = id * 4 + i;
    raw.push({
      element: e,
      stock: W.raw[idx] || 0,
      basis: W.rawBasis[idx] || 0,
      lastBuy: Number.isFinite(W.t1LastBuy[idx]) ? W.t1LastBuy[idx] : null,
      inputNeed: W.t1InputNeed[idx] || 0,
      purchaseRequest: W.t1PurchaseReq[idx] || 0,
      preferredSupplier: W.preferredWholesale[id * 4 + i] ?? -1,
    });
  }
  const products = [];
  let inv = 0,
    eqv = W.t1Cash[id] + W.t1EqBook[id],
    made = 0,
    sold = 0,
    revenue = 0,
    cogs = 0;
  for (let p = 0; p < NP; p++)
    if (W.t1Operates[id * NP + p]) {
      const idx = id * NP + p,
        fin = W.t1Fin[idx] || 0;
      inv += fin;
      eqv += fin * (marketAverages().rP[p] || 0);
      made += lastTickT1Made[idx] || 0;
      sold += W.t1Sold[idx] || 0;
      revenue += W.t1Rev[idx] || 0;
      cogs += W.t1COGS[idx] || 0;
      products.push({
        product: P[p].code,
        price: W.t1Price[idx],
        unitCost: W.t1UnitCost[idx],
        finished: fin,
        finishedBasis: W.t1FinBasis[idx] || 0,
        salesEMA: W.t1SalesEMA[idx] || 0,
        demandEMA: W.t1DemandEMA[idx] || 0,
        made: lastTickT1Made[idx] || 0,
        sold: W.t1Sold[idx] || 0,
        revenue: W.t1Rev[idx] || 0,
        cogs: W.t1COGS[idx] || 0,
        reliability: W.t1Rel[idx] || 0,
        priceStability: W.t1PriceStability[idx] || 0,
        reliabilityAttempts: t1RelAttemptsCount(id, p),
      });
    }
  for (const x of raw) inv += x.stock;
  for (const e of E) eqv += W.raw[id * 4 + EI[e]] * (marketAverages().wP[EI[e]] || 0);
  return {
    tier: 'T1',
    id,
    name: piBase.name + ' ' + String((id % 100) + 1).padStart(3, '0'),
    native: piBase.product,
    controller: controller[id] ? 'PLAYER' : 'BOT',
    online: !!online[id],
    cash: W.t1Cash[id],
    equipment: [...equipment[id]],
    equipmentBookValue: W.t1EqBook[id],
    inventory: inv,
    equity: eqv,
    raw,
    products,
    made,
    sold,
    revenue,
    cogs,
    grossProfit: revenue - cogs,
    reliability: products.length
      ? products.reduce((a, x) => a + x.reliability, 0) / products.length
      : 0,
  };
}
function t0RelAttemptsCount(id, i) {
  return W.t0RelAttempts[id * 4 + i] || 0;
}
function t1RelAttemptsCount(id, p) {
  return W.t1RelAttempts[id * NP + p] || 0;
}
function watchedDetails() {
  const out = {};
  for (const id of watchedCompanies.T0)
    if (id >= 0 && id < N0) out['T0:' + id] = companyDetail('T0', id);
  for (const id of watchedCompanies.T1)
    if (id >= 0 && id < N1) out['T1:' + id] = companyDetail('T1', id);
  for (const key of Object.keys(watchedCompanyHistory))
    if (!out[key]) delete watchedCompanyHistory[key];
  for (const [key, detail] of Object.entries(out)) {
    const history = watchedCompanyHistory[key] || (watchedCompanyHistory[key] = []);
    const point = { tick };
    for (const field of ['cash', 'equity', 'made', 'sold', 'revenue', 'cogs', 'grossProfit', 'productionCost', 'operatingCashFlow'])
      if (Number.isFinite(detail[field])) point[field] = detail[field];
    if (history.at(-1)?.tick === tick) history[history.length - 1] = point;
    else history.push(point);
    if (history.length > 240) history.shift();
    detail.history = history;
  }
  return out;
}
function companySummariesT0(m) {
  const out = [];
  for (let id = 0; id < N0; id++) {
    const prof = T0P[id];
    let inv = 0,
      prod = 0,
      sold = 0,
      rev = 0,
      rel = 0,
      n = 0,
      eq = W.t0Cash[id];
    for (let e = 0; e < NE; e++)
      if (prof.elements.includes(E[e])) {
        const idx = id * 4 + e;
        const stock = W.t0Inv[idx] || 0;
        inv += stock;
        prod += lastTickT0Produced[idx] || 0;
        sold += W.t0Sold[idx] || 0;
        rev += W.t0Revenue[idx] || 0;
        rel += W.t0Rel[idx] || 0;
        n++;
        eq += stock * (m.wP[e] || 0);
      }
    out.push({
      id,
      name: prof.name,
      elements: [...prof.elements],
      cash: W.t0Cash[id],
      inventory: inv,
      equity: eq,
      production: prod,
      sold,
      revenue: rev,
      avgPrice: n ? prof.elements.reduce((a, e) => a + W.t0Price[id * 4 + EI[e]], 0) / n : NaN,
      reliability: n ? rel / n : 0,
    });
  }
  return out;
}
function productReadyStock(pi) {
  let s = 0;
  for (let id = 0; id < N1; id++) s += W.t1Fin[id * NP + pi] || 0;
  return s;
}
function productSupplyCapacity(pi) {
  let cap = 0;
  const unitCap = pi < 4 ? cfg.basicEquipmentCapacity : cfg.compoundEquipmentCapacity;
  for (let id = 0; id < N1; id++) if (W.t1Operates[id * NP + pi]) cap += unitCap;
  return cap;
}
function publish() {
  const m = marketAverages(),
    now = performance.now(),
    elapsed = Math.max(0.001, (now - lastReportAt) / 1000),
    intervalTicks = tick - lastReportTick;
  const tps = intervalTicks / elapsed;
  lastReportAt = now;
  lastReportTick = tick;
  const sid = Math.max(0, Math.min(N1 - 1, selectedId)),
    scode = T1P[Math.floor(sid / 100)].product,
    spi = PI[scode];
  const analytics = buildAnalytics(m);
  const companies = [];
  for (let id = 0; id < N1; id++) {
    const pi = PI[T1P[Math.floor(id / 100)].product],
      b = id * 10;
    let raw = 0,
      fin = 0,
      totalSold = 0,
      totalRevenue = 0,
      totalCOGS = 0,
      totalMade = 0,
      rel = 0,
      relN = 0;
    for (let e = 0; e < 4; e++) raw += W.raw[id * 4 + e] || 0;
    for (let p = 0; p < NP; p++)
      if (W.t1Operates[id * NP + p]) {
        fin += W.t1Fin[id * NP + p] || 0;
        totalSold += W.t1Sold[id * NP + p] || 0;
        totalRevenue += W.t1Rev[id * NP + p] || 0;
        totalCOGS += W.t1COGS[id * NP + p] || 0;
        totalMade +=
          lastTickT1Made[id * NP + p] || 0;
        rel += W.t1Rel[id * NP + p] || 0;
        relN++;
      }
    companies.push({
      id,
      name: T1P[Math.floor(id / 100)].name + ' ' + String((id % 100) + 1).padStart(3, '0'),
      native: T1P[Math.floor(id / 100)].product,
      controller: controller[id] ? 'PLAYER' : 'BOT',
      equipment: [...equipment[id]],
      price: W.t1Price[b + pi],
      raw,
      finished: fin,
      inventory: raw + fin,
      cash: W.t1Cash[id],
      equity:
        W.t1Cash[id] +
        W.t1EqBook[id] +
        (() => {
          let v = 0;
          for (let e = 0; e < 4; e++) v += (W.raw[id * 4 + e] || 0) * (m.wP[e] || 0);
          for (let p = 0; p < NP; p++)
            if (W.t1Operates[id * NP + p]) v += (W.t1Fin[id * NP + p] || 0) * (m.rP[p] || 0);
          return v;
        })(),
      made: totalMade,
      sold: totalSold,
      revenue: totalRevenue,
      grossProfit: totalRevenue - totalCOGS,
      reliability: relN ? rel / relN : 0,
    });
  }
  const productStats = P.map((p, i) => {
    const suppliers = [];
    for (let id = 0; id < N1; id++)
      if (W.t1Operates[id * NP + i])
        suppliers.push({ id, vol: W.t1Sold[id * NP + i] || 0, rel: W.t1Rel[id * NP + i] || 0 });
    return {
      code: p.code,
      name: p.name,
      complexity: p.complexity,
      role: p.role,
      firms: suppliers.length,
      machineryPrice: p.equipmentPrice,
      capacity: i < 4 ? cfg.basicEquipmentCapacity : cfg.compoundEquipmentCapacity,
      productionCapacity: productSupplyCapacity(i),
      made: suppliers.reduce((n, x) => n + (lastTickT1Made[x.id * NP + i] || 0), 0),
      sold: m.rVol[i],
      cogs: suppliers.reduce((n, x) => n + (W.t1COGS[x.id * NP + i] || 0), 0),
      avgPrice: suppliers.reduce((n, x) => n + W.t1Price[x.id * NP + i], 0) / Math.max(1, suppliers.length),
      avgUnitCost: suppliers.reduce((n, x) => n + W.t1UnitCost[x.id * NP + i], 0) / Math.max(1, suppliers.length),
      retailPrice: m.rP[i],
      volume: m.rVol[i],
      consumerVolume: W.endFulfilled[i],
      intermediateVolume: W.t1IntermediateSold[i],
      intermediateRevenue: W.t1IntermediateRevenue[i],
      revenue: m.rRev[i],
      supplyCapacity: productSupplyCapacity(i),
      readyStock: productReadyStock(i),
      potential: (W.endPotential || W.potential)[i],
      active: (W.endActive || W.active)[i],
      fulfilled: (W.endFulfilled || W.fulfilled)[i],
      priceLost: (W.endPriceLost || W.priceLost)[i],
      stockUnmet: (W.endStockUnmet || W.stockUnmet)[i],
      hhi: hhi(suppliers.map((x) => x.vol)),
      reliability: marketReliability(
        suppliers.map((x) => x.rel),
        suppliers.map((x) => x.vol),
      ),
      fillRate: (W.endActive || W.active)[i] ? (W.endFulfilled || W.fulfilled)[i] / (W.endActive || W.active)[i] : 0,
    };
  });
  const t2ProductStats = T2P.map((p) => ({ code: p.code, name: p.name, sector: p.sector,
    complexity: p.complexity, primaryMaterial: PB[p.primaryMaterial].name, machineryPrice: p.equipmentPrice, capacity: p.capacity,
    recipe: p.ingredients.map(([material, quantity]) => `${quantity} ${P[material].name}`).join(' + '),
    firms: 0, avgPrice: 0, avgUnitCost: 0, productionCapacity: 0, readyStock: 0, made: 0, sold: 0, revenue: 0, cogs: 0, reliability: 0, hhi: 0,
    potential: W.endPotential[NP + p.id], active: W.endActive[NP + p.id], fulfilled: W.endFulfilled[NP + p.id],
    stockUnmet: W.endStockUnmet[NP + p.id],
    fillRate: W.endActive[NP + p.id] ? W.endFulfilled[NP + p.id] / W.endActive[NP + p.id] : 0 }));
  for (let line = 0; line < W.t2LineCount; line++) {
    const p = t2ProductStats[W.t2LineProduct[line]];
    p.firms++; p.avgPrice += W.t2Price[line]; p.readyStock += W.t2Fin[line]; p.made += W.t2Made[line];
    p.avgUnitCost += W.t2FinBasis[line] || W.t2UnitCost[line]; p.productionCapacity += p.capacity;
    p.sold += W.t2Sold[line]; p.revenue += W.t2Revenue[line]; p.cogs += W.t2COGS[line]; p.reliability += W.t2Rel[line];
    p.hhi += W.t2Sold[line] ** 2;
  }
  for (const p of t2ProductStats) {
    p.avgPrice /= Math.max(1, p.firms); p.reliability /= Math.max(1, p.firms);
    p.avgUnitCost /= Math.max(1, p.firms);
    p.hhi = p.sold ? p.hhi / p.sold ** 2 : 0; p.grossProfit = p.revenue - p.cogs;
    p.margin = p.revenue ? p.grossProfit / p.revenue : 0;
    p.utilization = p.productionCapacity ? p.made / p.productionCapacity : 0;
  }
  const t2Cohorts = T2_SECTORS.map((name) => ({ name, firms: 0, lines: 0, players: 0, online: 0, cash: 0, equity: 0,
    equipmentBookValue: 0, raw: 0, inventory: 0, capacity: 0, made: 0, sold: 0, revenue: 0, cogs: 0, grossProfit: 0 }));
  for (let firm = 0; firm < cfg.t2FirmCount; firm++) {
    const c = t2Cohorts[W.t2Sector[firm]]; c.firms++; c.cash += W.t2Cash[firm];
    c.players += W.t2Controller[firm]; c.online += W.t2Controller[firm] && W.t2Online[firm] ? 1 : 0;
    c.equipmentBookValue += W.t2EqBook[firm]; c.equity += W.t2Cash[firm] + W.t2EqBook[firm];
    for (let material = 0; material < NP; material++) {
      const basic = material < NE, index = firm * (basic ? NE : NP) + material;
      const stock = (basic ? W.t2Raw : W.t2T1Raw)[index];
      c.raw += stock; c.equity += stock * (basic ? W.t2RawBasis : W.t2T1Basis)[index];
    }
    for (let slot = 0; slot < W.t2FirmLineCount[firm]; slot++) {
      const line = W.t2FirmLines[firm * 5 + slot];
      c.lines++; c.inventory += W.t2Fin[line]; c.made += W.t2Made[line]; c.sold += W.t2Sold[line];
      c.capacity += T2P[W.t2LineProduct[line]].capacity; c.equity += W.t2Fin[line] * W.t2Price[line];
      c.revenue += W.t2Revenue[line]; c.cogs += W.t2COGS[line]; c.grossProfit += W.t2Revenue[line] - W.t2COGS[line];
    }
  }
  for (const c of t2Cohorts) {
    c.utilization = c.capacity ? c.made / c.capacity : 0; c.margin = c.revenue ? c.grossProfit / c.revenue : 0;
  }
  // Industry markets follow the product's sector, whereas firm cohorts follow
  // the home sector. Adjacent-sector portfolios must not conflate the two.
  const summarizeMarkets = (products, name) => {
    const summary = { name, products: products.length, lines: 0, capacity: 0, readyStock: 0, made: 0, sold: 0,
      revenue: 0, cogs: 0, active: 0, fulfilled: 0, stockUnmet: 0, reliability: 0 };
    for (const p of products) {
      for (const key of ['made','sold','revenue','cogs','active','fulfilled','stockUnmet','readyStock']) summary[key] += p[key];
      summary.lines += p.firms; summary.capacity += p.productionCapacity; summary.reliability += p.reliability * p.firms;
    }
    summary.reliability /= Math.max(1, summary.lines);
    summary.grossProfit = summary.revenue - summary.cogs;
    summary.margin = summary.revenue ? summary.grossProfit / summary.revenue : 0;
    summary.utilization = summary.capacity ? summary.made / summary.capacity : 0;
    summary.fillRate = summary.active ? summary.fulfilled / summary.active : 0;
    summary.volumeShare = analytics.t2Sold ? summary.sold / analytics.t2Sold : 0;
    return summary;
  };
  const t2Industries = T2_SECTORS.map((name, index) => ({ ...summarizeMarkets(t2ProductStats.filter((p) => p.sector === name), name), primaryMaterial: PB[M.T2_SECTOR_DEFINITIONS[index].primaryMaterial].name }));
  const t2Complexity = M.TIER_BOUNDARIES.T2.map((complexity) => ({ ...summarizeMarkets(t2ProductStats.filter((p) => p.complexity === complexity), 'Complexity ' + complexity), complexity }));
  const t2Totals = summarizeMarkets(t2ProductStats, 'All Tier 2 industries');
  const productCategories = [1, 2, 3, 4, 5].map((complexity) => {
    const products = (complexity < 3 ? productStats : t2ProductStats).filter(p => p.complexity === complexity);
    const summary = summarizeMarkets(products, 'C-' + complexity);
    return { ...summary, complexity, tier: complexity < 3 ? 'Tier 1' : 'Tier 2',
      role: complexity < 3 ? 'Business inputs' : 'Human consumer goods',
      machineryPrice: products[0].machineryPrice,
      unitCapacity: products[0].capacity,
      avgPrice: products.reduce((n, p) => n + p.avgPrice * p.firms, 0) / Math.max(1, summary.lines),
      avgUnitCost: products.reduce((n, p) => n + p.avgUnitCost * p.firms, 0) / Math.max(1, summary.lines),
      soldPerLine: summary.lines ? summary.sold / summary.lines : NaN,
      profitPerLine: summary.lines ? summary.grossProfit / summary.lines : NaN };
  });
  analytics.latest.t2Industries = t2Industries.map(({ name, made, sold, active, fulfilled, revenue, cogs, grossProfit, utilization, fillRate }) =>
    ({ name, made, sold, active, fulfilled, revenue, cogs, grossProfit, utilization, fillRate }));
  Object.assign(analytics.latest, { t2GrossProfit: t2Totals.grossProfit, t2Capacity: t2Totals.capacity,
    t2Utilization: t2Totals.utilization, t2Desired: t2Totals.active, t2Fulfilled: t2Totals.fulfilled, t2FillRate: t2Totals.fillRate });
  const selectedTier2Company = selectedTierControl === 'T2' ? tier2Company(selectedT2Id) : null;
  if (!selectedTier2Company || tier2HistoryCompany !== selectedT2Id) {
    tier2CompanyHistory = []; tier2HistoryCompany = selectedTier2Company ? selectedT2Id : -1;
  }
  if (selectedTier2Company) {
    const c = selectedTier2Company;
    const point = { tick, id: c.id, cash: c.cash, equity: c.equity, made: c.made, sold: c.sold,
      revenue: c.revenue, cogs: c.cogs, grossProfit: c.grossProfit, utilization: c.utilization };
    if (tier2CompanyHistory.at(-1)?.tick === tick) tier2CompanyHistory[tier2CompanyHistory.length - 1] = point;
    else tier2CompanyHistory.push(point);
    if (tier2CompanyHistory.length > 240) tier2CompanyHistory.shift();
  }
  const elementStats = E.map((e, i) => ({
    name: e,
    code: ['W', 'E', 'F', 'A'][i],
    price: m.wP[i],
    volume: m.wVol[i],
    difficulty: W.difficulty[i],
    hhi: analytics.t0HHI[i],
    reliability: marketReliability(t0RelSafe(i), t0VolsFor(i)),
  }));
  lastSnapshot = {
    colony: { ...M.COLONY_STORY, population: cfg.endUserCount },
    tick,
    month,
    tps,
    mode,
    targetTPS,
    difficulty: {
      [E[0]]: W.difficulty[0],
      [E[1]]: W.difficulty[1],
      [E[2]]: W.difficulty[2],
      [E[3]]: W.difficulty[3],
    },
    wholesaleAvg: m.wAvg,
    retailAvg: m.rAvg,
    wholesaleVolume: m.wVolume,
    retailVolume: m.rVolume,
    retailOrders: analytics.orderTotal,
    fulfilledOrders: analytics.fulfilledOrders,
    elements: elementStats,
    products: productStats,
    tier2Products: t2ProductStats,
    productCategories,
    tier2Cohorts: t2Cohorts,
    tier2Industries: t2Industries,
    tier2Complexity: t2Complexity,
    tier2CompanyHistory,
    tier2Companies: tier2Page(),
    performance: { lastTickMs: workerStats.lastTickMs, averageTickMs: workerStats.totalTickMs / Math.max(1, workerStats.steps),
      stateBytes: Object.values(W).reduce((n, a) => n + (a?.byteLength || 0), 0), activeLines: W.t2LineCount,
      activatedConsumers: sourceState.activatedConsumers || 0, orders: sourceState.activeOrders || 0 },
    cohorts: analytics.cohort,
    t0Companies: companySummariesT0(m),
    analyticsHistory,
    tiers: {
      t0: {
        firms: N0,
        bought: sumArray(analytics.t0Produced),
        made: sumArray(analytics.t0Produced),
        productionCost: W.t0Cost.reduce((total, cost, index) => total + cost * lastTickT0Produced[index], 0),
        inventory: analytics.t0Inventory,
        cash: analytics.t0Cash,
        equity: analytics.t0Equity,
        sold: analytics.t0Sold,
        revenue: analytics.t0Revenue,
        productionByElement: analytics.t0Produced,
        hhi: analytics.t0HHI,
        reliability: analytics.latest.avgT0Reliability,
      },
      t1: {
        firms: N1,
        inventory: analytics.latest.t1Inventory,
        raw: analytics.t1Raw,
        finished: analytics.t1Finished,
        cash: analytics.t1Cash,
        equity: analytics.t1Equity,
        bought: sumArray(W.t1Bought),
        made: analytics.t1Made,
        sold: analytics.t1Sold,
        revenue: analytics.t1Revenue,
        cogs: analytics.t1COGS,
        grossProfit: analytics.t1Revenue - analytics.t1COGS,
        activeFirms: analytics.activeFirms,
        players: analytics.players,
        reliability: analytics.latest.avgT1Reliability,
      },
      t2: {
        firms: cfg.t2FirmCount,
        activeLines: analytics.t2Lines,
        inventory: analytics.t2Inventory,
        finished: sumArray(W.t2Fin.subarray(0, W.t2LineCount)),
        stockCoverage: sumArray(W.t2SalesEMA.subarray(0, W.t2LineCount)) > 0 ?
          sumArray(W.t2Fin.subarray(0, W.t2LineCount)) / sumArray(W.t2SalesEMA.subarray(0, W.t2LineCount)) : null,
        tradingFirms360: W.t2LastSaleTick.subarray(0, cfg.t2FirmCount).reduce((count, last) =>
          count + (last > 0 && tick - last < 360), 0),
        cash: analytics.t2Cash,
        equity: analytics.t2Equity,
        bought: sumArray(W.t2Bought),
        made: analytics.t2Made,
        sold: analytics.t2Sold,
        revenue: analytics.t2Revenue,
        cogs: analytics.t2COGS,
        grossProfit: analytics.t2Revenue - analytics.t2COGS,
        capacity: t2Totals.capacity, utilization: t2Totals.utilization, margin: t2Totals.margin,
        desired: t2Totals.active, fulfilled: t2Totals.fulfilled, fillRate: t2Totals.fillRate,
      },
      endUsers: {
        population: cfg.endUserCount,
        potential: analytics.potential,
        active: analytics.active,
        fulfilled: analytics.fulfilled,
        priceLost: analytics.priceLost,
        stockUnmet: analytics.stockUnmet,
        orders: analytics.orderTotal,
        fulfilledOrders: analytics.fulfilledOrders,
        unitFillRate: analytics.unitFillRate,
        orderFillRate: analytics.orderFillRate,
        priceLossShare: analytics.priceLossShare,
        stockUnmetShare: analytics.stockUnmetShare,
        revenue: analytics.retailRevenue,
      },
    },
    companies,
    selected: selectedTier2Company || {
      tier: 'T1',
      products: companyDetail('T1', sid).products,
      id: sid,
      name: T1P[Math.floor(sid / 100)].name + ' ' + String((sid % 100) + 1).padStart(3, '0'),
      native: scode,
      controller: controller[sid] ? 'PLAYER' : 'BOT',
      online: !!online[sid],
      price: W.t1Price[sid * 10 + spi],
      cash: W.t1Cash[sid],
      finished: W.t1Fin[sid * 10 + spi],
      inventory: rawSum(sid) + finSum(sid),
      eqBook: W.t1EqBook[sid],
      equipment: [...equipment[sid]],
      reliability: W.t1Rel[sid * 10 + spi],
    },
    engine: 'source',
    expandedDetails: watchedDetails(),
  };
  lastSnapshot.endUsers = lastSnapshot.tiers.endUsers;
  lastSnapshot.tiers.t3 = lastSnapshot.endUsers;
  lastSnapshot.tiers.t0.operatingCashFlow = lastSnapshot.tiers.t0.revenue - lastSnapshot.tiers.t0.productionCost;
  // Charts and summary cards share the same aggregate values for each tick.
  analytics.latest.tiers = Object.fromEntries(Object.entries(lastSnapshot.tiers).map(([tier, stats]) =>
    [tier, Object.fromEntries(Object.entries(stats).map(([key, value]) => [key, Array.isArray(value) ? [...value] : value]))]));
  analytics.latest.difficulty = [...W.difficulty];
  analytics.latest.elementPrices = [...m.wP];
  analytics.latest.materialPrices = [...m.rP];
  self.postMessage({ type: 'snapshot', data: lastSnapshot });
}
function t0RelSafe(ei) {
  const v = [];
  for (let i = 0; i < N0; i++)
    if (T0P[i].elements.includes(E[ei])) v.push(W.t0Rel[i * 4 + ei] || 0);
  return v;
}
function t0VolsFor(ei) {
  const v = [];
  for (let i = 0; i < N0; i++)
    if (T0P[i].elements.includes(E[ei])) v.push(W.t0Sold[i * 4 + ei] || 0);
  return v;
}

// The sole entry point for advancing economic state. Run, Run Max, and Step
// must all use this function; their modes only change scheduling and rendering.
function advanceSimulationTick() {
  step();
}
function runLoop() {
  if (!running) return;
  if (mode === 'max') {
    const start = performance.now();
    while (running && performance.now() - start < 45) advanceSimulationTick();
    publish();
    timer = setTimeout(runLoop, 0);
    return;
  }
  advanceSimulationTick();
  publish();
  timer = setTimeout(runLoop, 500);
}
self.onmessage = async (event) => {
  const message = event.data;
  try {
    if (message.type === 'init') {
      initEngine();
      reset(message.cfg || defaultCfg());
      return;
    }
    if (message.type === 'run') {
      const nextMode = message.mode || 'fixed';
      if (running && mode === nextMode) return;
      // Switching modes replaces the pending loop instead of adding another.
      if (timer !== null) clearTimeout(timer);
      running = true;
      mode = nextMode;
      runLoop();
      return;
    }
    if (message.type === 'pause') {
      running = false;
      if (timer) clearTimeout(timer);
      publish();
      return;
    }
    if (message.type === 'step') {
      if (!running) {
        advanceSimulationTick();
        publish();
      }
      return;
    }
    if (message.type === 'reset') {
      running = false;
      if (timer) clearTimeout(timer);
      reset(message.cfg || defaultCfg());
      return;
    }
    if (message.type === 'applyConfig') {
      updateLive(message.cfg);
      publish();
      return;
    }
    if (message.type === 'tier2Query') {
      const allowedSorts = ['id','name','sector','cash','equity','inventory','raw','finished','capacity','utilization','margin','revenue','grossProfit','reliability'];
      tier2Query = { page: Math.max(0, message.page | 0), pageSize: 50,
        search: String(message.search || '').slice(0, 100), sector: String(message.sector || ''),
        controller: String(message.controller || ''), sort: allowedSorts.includes(message.sort) ? message.sort : 'id',
        descending: !!message.descending };
      publish(); return;
    }
    if (message.type === 'select') {
      selectedTierControl = message.tier === 'T2' ? 'T2' : 'T1';
      if (selectedTierControl === 'T2') {
        selectedT2Id = Math.max(0, Math.min(cfg.t2FirmCount - 1, message.id | 0));
        publish(); return;
      }
      selectedId = Math.max(0, Math.min(N1 - 1, message.id | 0));
      publish();
      return;
    }
    if (message.type === 'companyDetail') {
      self.postMessage({
        type: 'companyDetail',
        data: companyDetail(message.tier === 'T0' ? 'T0' : message.tier === 'T2' ? 'T2' : 'T1', message.id | 0),
      });
      return;
    }
    if (message.type === 'watchCompanies') {
      watchedCompanies.T0 = new Set(
        (message.watches?.T0 || []).map((x) => x | 0).filter((x) => x >= 0 && x < N0),
      );
      watchedCompanies.T1 = new Set(
        (message.watches?.T1 || []).map((x) => x | 0).filter((x) => x >= 0 && x < N1),
      );
      publish();
      return;
    }
    if (message.type === 'player') {
      const id = message.id;
      if (message.tier === 'T2') {
        if (!Number.isInteger(id) || id < 0 || id >= cfg.t2FirmCount) throw new Error('Invalid Tier 2 company.');
        const product = M.T2_PRODUCT_BY_CODE[message.code];
        if (message.controller === 'PLAYER' && (!product || !self.Phase0ReferenceKernel.hasTier2Product(W, id, product.id) ||
            !Number.isFinite(message.price) || message.price < 0)) throw new Error('Select an installed product and a valid non-negative price.');
        W.t2Controller[id] = message.controller === 'PLAYER' ? 1 : 0; W.t2Online[id] = message.online ? 1 : 0;
        if (W.t2Controller[id])
          for (let slot = 0; slot < W.t2FirmLineCount[id]; slot++) {
            const line = W.t2FirmLines[id * 5 + slot];
            if (W.t2LineProduct[line] === product.id) {
              W.t2PlayerPrice[line] = Math.max(message.price, W.t2FinBasis[line] || W.t2UnitCost[line], 0.01);
              W.t2Price[line] = W.t2PlayerPrice[line];
              W.t2LearnProfit[line] = W.t2LearnSales[line] = W.t2LearnDemand[line] = W.t2LearnTicks[line] = 0;
              W.t2LearnStep[line] = 1;
              W.t2LearnPrevious[line] = NaN;
            }
          }
        selectedTierControl = 'T2'; selectedT2Id = id; publish(); return;
      }
      if (!Number.isInteger(id) || id < 0 || id >= N1 || !PB[message.code] || !equipment[id].includes(message.code)) throw new Error('Invalid Tier 1 company or product.');
      selectedTierControl = 'T1';
      selectedId = id;
      controller[id] = message.controller === 'PLAYER' ? 1 : 0;
      online[id] = message.online ? 1 : 0;
      W.t1Controller[id] = controller[id];
      const index = id * 10 + PI[message.code];
      if (controller[id] && Number.isFinite(message.price)) {
        playerPrices[id][message.code] = quantR(message.price);
        W.playerPrice[index] = playerPrices[id][message.code];
        W.t1LearnProfit[index] = W.t1LearnSales[index] = W.t1LearnDemand[index] = W.t1LearnTicks[index] = 0;
        W.t1LearnStep[index] = 1;
        W.t1LearnPrevious[index] = NaN;
      }
      publish();
      return;
    }
    if (message.type === 'buyEquipment') {
      const id = message.id,
        code = message.code,
        product = PB[code];
      if (message.tier === 'T2') {
        try {
          if (!Number.isInteger(id) || id < 0 || id >= cfg.t2FirmCount || !W.t2Controller[id]) throw new Error('Only player-controlled Tier 2 companies can buy machinery.');
          self.Phase0ReferenceKernel.addTier2Line(W, cfg, id, M.T2_PRODUCT_BY_CODE[code]);
          publish(); self.postMessage({ type: 'equipmentResult', ok: true });
        } catch (error) { self.postMessage({ type: 'equipmentResult', ok: false, msg: error.message }); }
        return;
      }
      if (controller[id] !== 1 || !product || equipment[id].includes(code)) {
        self.postMessage({
          type: 'equipmentResult',
          ok: false,
          msg: 'Only PLAYER-controlled companies can buy new equipment.',
        });
        return;
      }
      if (W.t1Cash[id] + 1e-9 < product.equipmentPrice) {
        self.postMessage({ type: 'equipmentResult', ok: false, msg: 'Insufficient cash.' });
        return;
      }
      W.t1Cash[id] -= product.equipmentPrice;
      W.t1EqBook[id] += product.equipmentPrice;
      eqBook[id] += product.equipmentPrice;
      equipment[id].push(code);
      const index = id * 10 + PI[code],
        inputCost = Object.entries(product.inputs).reduce(
          (total, [element, ratio]) => total + lastFiniteWholesale(element) * ratio,
          0,
        );
      W.t1Operates[index] = 1;
      W.t1UnitCost[index] = inputCost + cfg.manufacturingCostPerUnit;
      W.t1Rel[index] = 0.5;
      W.t1Price[index] = quantR(
        W.t1UnitCost[index] * (1 + markup(code, cfg)),
        W.t1UnitCost[index],
      );
      W.t1PrevPrice[index] = W.t1Price[index];
      publish();
      self.postMessage({ type: 'equipmentResult', ok: true });
    }
  } catch (error) {
    if (['player','applyConfig','select'].includes(message.type))
      self.postMessage({ type: 'actionResult', ok: false, msg: error.message || String(error) });
    else self.postMessage({ type: 'error', message: error?.stack || String(error) });
  }
};
function lastFiniteWholesale(e) {
  const ei = EI[e];
  let best = Infinity;
  for (let i = 0; i < N0; i++)
    if (T0P[i].elements.includes(e)) best = Math.min(best, W.t0Price[i * 4 + ei]);
  return Number.isFinite(best) ? best : cfg.baseCost;
}
