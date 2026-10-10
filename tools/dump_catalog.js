'use strict';
/*
 * One-time extractor: serialize the static catalog from web/catalog.js
 * into a JSON file that the Python kernel loads verbatim. This avoids hand
 * transcription of the 420-recipe catalog and the invented-market selection.
 *
 * Usage: node tools/dump_catalog.js [out.json]
 */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const out = process.argv[2] || path.join(root, 'economy', 'core', 'catalog.json');

global.self = globalThis;
require(path.join(root, 'web', 'catalog.js'));
const M = globalThis.Phase0Model;

const serializeT2 = (p) => ({
  id: p.id,
  code: p.code,
  name: p.name,
  recipeKey: p.recipeKey,
  kind: p.kind,
  needType: p.needType,
  sectorIndex: p.sectorIndex,
  sector: p.sector,
  primaryMaterial: p.primaryMaterial,
  manufacturer: p.manufacturer,
  complexity: p.complexity,
  inputs: p.inputs,
  ingredients: p.ingredients.map(([m, q]) => [m, q]),
  equipmentClass: p.equipmentClass,
  equipmentPrice: p.equipmentPrice,
  capacity: p.capacity,
  conversionCost: p.conversionCost,
  needWeight: p.needWeight,
  demandWeight: p.demandWeight,
  demandFactor: p.demandFactor,
  reservationPremium: p.reservationPremium,
  distributorValue: p.distributorValue,
  invented: !!p.invented,
});

const data = {
  TIME: M.TIME,
  ELEMENTS: M.ELEMENTS,
  T1_BASIC_MACHINERY: M.T1_BASIC_MACHINERY,
  T1_COMPOUND_MACHINERY: M.T1_COMPOUND_MACHINERY,
  T2_ROUTE_SETUP: M.T2_ROUTE_SETUP,
  MIN_UNIT_PRICE: M.MIN_UNIT_PRICE,
  TIER_BOUNDARIES: M.TIER_BOUNDARIES,
  T1_COMPANY_NAMES: M.T1_COMPANY_NAMES,
  PRODUCTS: M.PRODUCTS.map((p) => ({
    code: p.code, symbol: p.symbol, name: p.name, inputs: p.inputs, complexity: p.complexity,
    companyName: p.companyName, role: p.role, distributorValue: p.distributorValue, equipmentPrice: p.equipmentPrice,
  })),
  T2_SECTORS: M.T2_SECTORS,
  T2_SECTOR_DEFINITIONS: M.T2_SECTOR_DEFINITIONS.map((s) => ({ name: s.name, description: s.description })),
  T2_SECTOR_MANUFACTURERS: M.T2_SECTOR_MANUFACTURERS.map((s) => ({ sector: s.sector, company: s.company })),
  T2_MANUFACTURER_BY_SECTOR: M.T2_MANUFACTURER_BY_SECTOR,
  EQUIPMENT_MAKERS: M.EQUIPMENT_MAKERS,
  EQUIPMENT_CONFIG: M.EQUIPMENT_CONFIG,
  T2_SECTOR_WEIGHTS: M.T2_SECTOR_WEIGHTS,
  T2_ADJACENCY: M.T2_ADJACENCY,
  T2_NEED_TYPES: M.T2_NEED_TYPES,
  T2_MAX_PRODUCTS_PER_FIRM: M.T2_MAX_PRODUCTS_PER_FIRM,
  ECONOMY_DEFAULTS: M.ECONOMY_DEFAULTS,
  PROGRESSION_DEFAULTS: M.PROGRESSION_DEFAULTS,
  INVENTED_PER_COMPLEXITY: M.INVENTED_PER_COMPLEXITY,
  T2_PRODUCTS: M.T2_PRODUCTS.map(serializeT2),
  T2_Catalog: M.T2_Catalog.map(serializeT2),
  T2_UNINVENTED_PRODUCTS: M.T2_UNINVENTED_PRODUCTS.map(serializeT2),
  T2_COMPLEXITY_COUNTS: M.T2_COMPLEXITY_COUNTS,
  T2_Catalog_COUNT: M.T2_Catalog.length,
  WORLD_STORY: M.WORLD_STORY,
};

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(data, null, 1));
console.log('wrote', out);
console.log('PRODUCTS', data.PRODUCTS.length, 'T2_PRODUCTS', data.T2_PRODUCTS.length,
  'T2_Catalog', data.T2_Catalog.length, 'uninvented', data.T2_UNINVENTED_PRODUCTS.length);
