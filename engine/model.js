/*
 * Canonical, editable Phase 0 model primitives.
 *
 * This file deliberately contains no browser-runtime boundary code. The
 * source kernel imports these definitions; keeping them here makes
 * topology and economic rules reviewable and testable in ordinary JavaScript.
 */
(function (root) {
  'use strict';

  const ELEMENTS = Object.freeze(['Water', 'Earth', 'Fire', 'Air']);
  // One ancestry-based machinery curve, regardless of the owning firm tier.
  const machineryPrice = (complexity) => 15000 * 5 ** (complexity - 1);
  const TIER_BOUNDARIES = Object.freeze({ T1: Object.freeze([1, 2]), T2: Object.freeze([3, 4, 5]) });
  const PRODUCTS = Object.freeze([
    { code: 'W', name: 'Purified Water', inputs: { Water: 1 } },
    { code: 'E', name: 'Refined Minerals', inputs: { Earth: 1 } },
    { code: 'F', name: 'Energy Cells', inputs: { Fire: 1 } },
    { code: 'A', name: 'Chemical Feedstock', inputs: { Air: 1 } },
    { code: 'W+E', name: 'Ceramic Composite', inputs: { Water: 1, Earth: 1 } },
    { code: 'W+F', name: 'Thermal Compounds', inputs: { Water: 1, Fire: 1 } },
    { code: 'W+A', name: 'Synthetic Fibers', inputs: { Water: 1, Air: 1 } },
    { code: 'E+F', name: 'Semiconductor Substrate', inputs: { Earth: 1, Fire: 1 } },
    { code: 'E+A', name: 'Structural Polymers', inputs: { Earth: 1, Air: 1 } },
    { code: 'F+A', name: 'Active Compounds', inputs: { Fire: 1, Air: 1 } },
  ].map((p) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, companyName: p.name + ' Refinery', inputs: Object.freeze(p.inputs), complexity,
      role: 'intermediate-only',
      consumerValue: complexity === 1 ? 1.875 : 3.75, equipmentPrice: machineryPrice(complexity) });
  }));

  const COLONY_STORY = Object.freeze({ name: 'Midbridge', population: 1000000,
    producers: 'Robots', consumers: 'Humans', immortal: true,
    contract: 'Infinity contract', healthcareProductCode: 'T2-035',
    purpose: 'Consumer behavior experiment',
    participants: 'Selected humans who sought immortality and worked their way toward sealing the Infinity contract',
    widerHumanCondition: 'Most humans elsewhere work in many roles for robots under poor conditions' });

  // Each consumer sector requires its designated processed Tier 1 material.
  const T2_SECTOR_DEFINITIONS = Object.freeze([
    Object.freeze({ name: 'Food & Nutrition', primaryMaterial: 'W' }),
    Object.freeze({ name: 'Housing & Furniture', primaryMaterial: 'E' }),
    Object.freeze({ name: 'Household Energy', primaryMaterial: 'F' }),
    Object.freeze({ name: 'Hygiene & Personal Care', primaryMaterial: 'A' }),
    Object.freeze({ name: 'Home & Kitchen', primaryMaterial: 'W+E' }),
    Object.freeze({ name: 'Healthcare & Wellness', primaryMaterial: 'W+F' }),
    Object.freeze({ name: 'Clothing & Textiles', primaryMaterial: 'W+A' }),
    Object.freeze({ name: 'Electronics & Communication', primaryMaterial: 'E+F' }),
    Object.freeze({ name: 'Mobility & Transport', primaryMaterial: 'E+A' }),
    Object.freeze({ name: 'Leisure & Fitness', primaryMaterial: 'F+A' }),
  ]);
  const T2_SECTORS = Object.freeze(T2_SECTOR_DEFINITIONS.map(sector => sector.name));
  // Explicit demand priors: daily human needs outweigh specialized leisure purchases.
  // They are bootstrap design assumptions, not fitted market-size estimates.
  const T2_SECTOR_WEIGHTS = Object.freeze([1.20, 1.15, 1.30, 1.00, 0.85, 1.05, 1.10, 1.25, 0.90, 0.75]);
  // Related consumer sectors share manufacturing inputs and human needs.
  const T2_ADJACENCY = Object.freeze([
    [3, 4, 5],
    [2, 3, 4, 7, 8],
    [1, 4, 7, 8, 9],
    [0, 1, 4, 5, 6],
    [0, 1, 2, 3, 5, 7],
    [0, 3, 4, 6, 8, 9],
    [3, 5, 8, 9],
    [1, 2, 4, 8, 9],
    [1, 2, 5, 6, 7, 9],
    [2, 5, 6, 7, 8],
  ].map(Object.freeze));
  const T2_CAPABILITY_BANDS = Object.freeze([
    Object.freeze({ complexity: 3, share: 0.60, startingLines: 2 }),
    Object.freeze({ complexity: 4, share: 0.30, startingLines: 3 }),
    Object.freeze({ complexity: 5, share: 0.10, startingLines: 4 }),
  ]);
  const t2EquipmentPrice = machineryPrice;
  // Bulk upstream firms and small downstream workshops serve the same population.
  // Stock coverage is measured against sales, not against idle nameplate capacity.
  const ECONOMY_DEFAULTS = Object.freeze({ capacity: 20000, targetInventory: 60000,
    maxInventory: 120000, initialCash: 1000000, retailTargetInventory: 600,
    retailMaxInventory: 1200, retailInitialCash: 5000, basicEquipmentCapacity: 160,
    compoundEquipmentCapacity: 240, minWholesaleLot: 10, inventoryCoverageTicks: 3,
    tier2WorkingCashTicks: 30, tier2MinimumCash: 500 });
  const t2Capacity = (c) => ({ 3: 3, 4: 2, 5: 1 })[c];
  // Every product has one code, one unordered input recipe and one distinct
  // expanded four-element composition. Codes have no alternative spellings.
  const recipeKey = inputs => Object.entries(inputs).sort(([a], [b]) => a.localeCompare(b))
    .map(([code, quantity]) => code + ':' + quantity).join('|');
  const elementalComposition = inputs => Object.freeze(Object.fromEntries(ELEMENTS.map(element =>
    [element, Object.entries(inputs).reduce((total, [code, quantity]) =>
      total + quantity * (PRODUCTS.find(p => p.code === code).inputs[element] || 0), 0)])));
  const recipes = [
    [0,"Drinking Water Pack","W,W,W",1.3],
    [0,"Ready Meal","W,W+A",1.1],
    [0,"Family Meal Pack","W,W,W+E",0.9],
    [0,"Meal Preparation Kit","W,W,W+F",0.75],
    [0,"Complete Nutrition Pack","W,W+A,W+E",0.7],
    [0,"Automated Meal Station","W,W+F,E+F",0.6],
    [1,"Storage Shelf","E,E,E",1.3],
    [1,"Dining Chair","E,W+F",1.1],
    [1,"Bed Frame","E,E,W+F",0.9],
    [1,"Sofa","E,E,W+A",0.75],
    [1,"Modular Apartment Kit","E,W+E,E+A",0.7],
    [1,"Smart Home Climate System","E,W+A,W+E",0.6],
    [2,"Rechargeable Battery","F,F,F",1.3],
    [2,"LED Light Bulb","F,E+A",1.1],
    [2,"Portable Power Station","F,F,W+A",0.9],
    [2,"Home Battery","F,F,E+F",0.75],
    [2,"Household Energy Hub","F,E+F,F+A",0.7],
    [2,"Solar Home Power System","F,W+F,W+A",0.6],
    [3,"Cleaning Concentrate","A,A,A",1.3],
    [3,"Hand Soap","A,W+E",1.1],
    [3,"Air Purifier","A,A,E+F",0.9],
    [3,"Washing Machine","A,A,E+A",0.75],
    [3,"Smart Laundry System","A,W+A,E+A",0.7],
    [3,"Home Air & Water Care System","A,W+E,F+A",0.6],
    [4,"Cookware Set","W+E,E",1.3],
    [4,"Food Storage Set","W+E,W",1.1],
    [4,"Dinnerware Set","W+E,W+E",0.9],
    [4,"Induction Cooker","W+E,F+A",0.75],
    [4,"Dishwasher","W+E,W+A,F",0.7],
    [4,"Smart Kitchen Suite","W+E,E+F,E",0.6],
    [5,"First Aid Kit","W+F,F",1.3],
    [5,"Heat Therapy Pad","W+F,W",1.1],
    [5,"Home Medical Kit","W+F,W+F",0.9],
    [5,"Sleep Therapy Device","W+F,E+F",0.75],
    [5,"Immortality Treatment","W+F,E+F,A",0.7],
    [5,"Home Diagnostics Station","W+F,W+F,W",0.6],
    [6,"Yoga Pants","W+A,F",1.3],
    [6,"Everyday Shoes","W+A,A",1.1],
    [6,"Athletic Clothing Set","W+A,W+A",0.9],
    [6,"Weatherproof Jacket","W+A,W+E",0.75],
    [6,"Custom Clothing Wardrobe","W+A,E+A,W",0.7],
    [6,"Performance Sportswear Set","W+A,W+A,F",0.6],
    [7,"Wireless Earbuds","E+F,E",1.3],
    [7,"Portable Speaker","E+F,F",1.1],
    [7,"Laptop","E+F,E+F",0.9],
    [7,"Tablet","E+F,E,E",0.75],
    [7,"Smartphone","E+F,F+A,E",0.7],
    [7,"Home Entertainment System","E+F,W+E,F",0.6],
    [8,"Bicycle Helmet","E+A,E",1.3],
    [8,"Bicycle Light","E+A,A",1.1],
    [8,"Bicycle","E+A,E+A",0.9],
    [8,"Electric Scooter","E+A,F,F",0.75],
    [8,"Electric Bicycle","E+A,W+E,F",0.7],
    [8,"Personal Mobility Pod","E+A,E+A,F",0.6],
    [9,"Fitness Mat","F+A,F",1.3],
    [9,"Sports Bottle","F+A,A",1.1],
    [9,"Home Exercise Kit","F+A,F+A",0.9],
    [9,"Game Console","F+A,E,E",0.75],
    [9,"Connected Fitness Station","F+A,W+F,A",0.7],
    [9,"Immersive Gaming System","F+A,F+A,E",0.6],
  ];
  const seenRecipes = new Set(), seenCompositions = new Set();
  const T2_PRODUCTS = Object.freeze(recipes.map(([sectorIndex, name, recipe, needWeight], id) => {
    const inputs = {};
    for (const code of recipe.split(',')) inputs[code] = (inputs[code] || 0) + 1;
    const ingredients = Object.entries(inputs).map(([code, quantity]) =>
      Object.freeze([PRODUCTS.findIndex((p) => p.code === code), quantity]));
    const complexity = ingredients.reduce((c, [material, quantity]) => c + quantity * (material < 4 ? 1 : 2), 0);
    if (!TIER_BOUNDARIES.T2.includes(complexity)) throw new Error('Tier 2 recipes must be C-3 through C-5.');
    const key = recipeKey(inputs);
    if (seenRecipes.has(key)) throw new Error('Duplicate Tier 2 recipe: ' + key);
    seenRecipes.add(key);
    const composition = elementalComposition(inputs), compositionKey = recipeKey(composition);
    if (seenCompositions.has(compositionKey)) throw new Error('Duplicate elemental composition: ' + compositionKey);
    seenCompositions.add(compositionKey);
    const primaryMaterial = T2_SECTOR_DEFINITIONS[sectorIndex].primaryMaterial;
    if (!inputs[primaryMaterial]) throw new Error('Every sector product must consume its primary Tier 1 material.');
    const conversionCost = 0.5 * complexity;
    return Object.freeze({
      id, code: `T2-${String(id + 1).padStart(3, '0')}`, recipeKey: key, composition, name, sectorIndex,
      sector: T2_SECTORS[sectorIndex], primaryMaterial, complexity, inputs: Object.freeze(inputs),
      ingredients: Object.freeze(ingredients), equipmentClass: `Fabrication C-${complexity}`,
      equipmentPrice: t2EquipmentPrice(complexity), capacity: t2Capacity(complexity),
      conversionCost, needWeight, demandWeight: needWeight * T2_SECTOR_WEIGHTS[sectorIndex],
      demandFactor: 0.45 ** (complexity - 1), reservationPremium: 1 + 0.45 * (complexity - 1),
      // Authored taste scale, independent of ingredient prices and markups.
      // At this scale (before private taste/premium), desired quantity halves.
      consumerValue: ({ 3: 8, 4: 12, 5: 16 })[complexity],
    });
  }));
  const T2_COMPLEXITY_COUNTS = Object.freeze([1, 2, 3, 4, 5].map(c =>
    T2_PRODUCTS.filter(p => p.complexity === c).length));
  const T2_PRODUCT_BY_CODE = Object.freeze(Object.fromEntries(T2_PRODUCTS.map(p => [p.code, p])));
  const relatedSector = (core, sector) => core === sector || T2_ADJACENCY[core].includes(sector);

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const complexity = (product) => product.complexity ?? Object.values(product.inputs).reduce((sum, quantity) => sum + quantity, 0);
  const finishedStockTarget = ({ salesEMA, coverageTicks, bootstrapStock, capacity,
    targetInventory, maxInventory }) => Math.max(0, Math.min(targetInventory, maxInventory,
      Math.max(Math.min(capacity, bootstrapStock), Math.ceil(Math.max(0, salesEMA) * coverageTicks))));
  const tier2StartingCash = (products, cfg) => {
    const direct = new Set();
    const rawQuote = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const basicQuote = (rawQuote + cfg.manufacturingCostPerUnit) * (1 + cfg.markup);
    const compoundQuote = (2 * rawQuote + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
    const operatingCost = products.reduce((sum, product) => {
      for (const [material] of product.ingredients) if (material < 4) direct.add(material);
      const unitCost = product.conversionCost + product.ingredients.reduce((cost, [material, quantity]) =>
        cost + quantity * (material < 4 ? basicQuote : compoundQuote), 0);
      return sum + product.capacity * unitCost;
    }, 0);
    const lotBuffer = direct.size * basicQuote;
    return Math.ceil(Math.max(cfg.tier2MinimumCash,
      operatingCost * cfg.tier2WorkingCashTicks + lotBuffer) / 50) * 50;
  };
  const demandAtPrice = (qMax, chokePrice, price, elasticity) =>
    qMax > 0 && chokePrice > 0 && price >= 0 && elasticity > 0
      ? qMax / (1 + Math.pow(price / chokePrice, elasticity))
      : 0;
  const switchingCost = (reliability, minimum, maximum) =>
    minimum + (maximum - minimum) * clamp(reliability, 0, 1);
  const reliabilityScore = (fulfillment, priceStability, availability) =>
    0.5 * clamp(fulfillment, 0, 1) +
    0.3 * clamp(priceStability, 0, 1) +
    0.2 * clamp(availability, 0, 1);
  const nextReliability = (current, score, alpha) =>
    clamp(current + clamp(alpha, 0, 1) * (score - current), 0, 1);
  // Derivative-following pricebot: Kephart, Hanson & Greenwald (2000), §3.2.
  // Total observed gross profit per tick is the objective, not margin per unit.
  // No consumer value, normal markup or market-wide ideal enters this rule.
  const adaptivePrice = ({ oldPrice, unitCost, profit, previousProfit, direction = 1,
    sales, stock, demand = sales, available = sales + stock, stepScale = 1,
    k = 0.35, response = 0.05 }) => {
    const floor = Math.max(0.01, unitCost), price = Math.max(floor, oldPrice);
    let nextDirection = direction < 0 ? -1 : 1;
    // A received order which could not be served is evidence of scarcity,
    // including windows with no deliveries. No target margin is inferred.
    const scarce = demand > available + 1e-9;
    if (scarce) nextDirection = 1;
    else if (sales <= 0) {
      if (stock <= 0) return { price, direction: nextDirection, stepScale };
      nextDirection = -1;
    } else if (Number.isFinite(previousProfit) && profit < previousProfit) nextDirection *= -1;
    // Adaptive derivative-following: shrink experiments after reversals and
    // recover resolution on a consistent signal. This may still quote at cost.
    const scale = clamp(stepScale * (nextDirection !== direction ? 0.5 : 1.2), 0.01, 1);
    const next = Math.max(floor, price * Math.exp(nextDirection * clamp(k, 0, 1) * response * scale));
    if (next === price && nextDirection < 0) nextDirection = 1;
    return { price: next, direction: nextDirection, stepScale: scale };
  };
  const initialTier2Cost = (product, cfg) => {
    const raw = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const basic = (raw + cfg.manufacturingCostPerUnit) * (1 + cfg.markup);
    const compound = (2 * raw + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
    return product.conversionCost + product.ingredients.reduce((total, [material, quantity]) =>
      total + quantity * (material < 4 ? basic : compound), 0);
  };

  root.Phase0Model = Object.freeze({
    COLONY_STORY,
    recipeKey,
    elementalComposition,
    T2_PRODUCT_BY_CODE,
    machineryPrice,
    ECONOMY_DEFAULTS,
    finishedStockTarget,
    tier2StartingCash,
    TIER_BOUNDARIES,
    T2_SECTOR_WEIGHTS,
    T2_CAPABILITY_BANDS,
    ELEMENTS,
    PRODUCTS,
    T2_PRODUCTS,
    T2_SECTORS,
    T2_SECTOR_DEFINITIONS,
    T2_ADJACENCY,
    relatedSector,
    T2_COMPLEXITY_COUNTS,
    t2EquipmentPrice,
    t2Capacity,
    clamp,
    complexity,
    demandAtPrice,
    switchingCost,
    reliabilityScore,
    nextReliability,
    adaptivePrice,
    initialTier2Cost,
  });
})(typeof self !== 'undefined' ? self : globalThis);
