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
    { code: 'W', name: 'Water', inputs: { Water: 1 } },
    { code: 'E', name: 'Earth', inputs: { Earth: 1 } },
    { code: 'F', name: 'Fire', inputs: { Fire: 1 } },
    { code: 'A', name: 'Air', inputs: { Air: 1 } },
    { code: 'W+E', name: 'Clay', inputs: { Water: 1, Earth: 1 } },
    { code: 'W+F', name: 'Steam', inputs: { Water: 1, Fire: 1 } },
    { code: 'W+A', name: 'Mist', inputs: { Water: 1, Air: 1 } },
    { code: 'E+F', name: 'Lava', inputs: { Earth: 1, Fire: 1 } },
    { code: 'E+A', name: 'Dust', inputs: { Earth: 1, Air: 1 } },
    { code: 'F+A', name: 'Smoke', inputs: { Fire: 1, Air: 1 } },
  ].map((p) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, inputs: Object.freeze(p.inputs), complexity,
      role: complexity === 1 ? 'retail' : 'intermediate', equipmentPrice: machineryPrice(complexity) });
  }));

  const T2_SECTORS = Object.freeze([
    'Household', 'Construction', 'Ceramics & Glass', 'Textiles & Pigments',
    'Alchemy', 'Tools & Mechanisms', 'Illumination & Instruments', 'Arcana & Luxury',
    'Agriculture & Horticulture', 'Medicine & Wellness',
  ]);
  // Explicit demand priors: everyday necessities outweigh discretionary luxury.
  // They are bootstrap design assumptions, not fitted market-size estimates.
  const T2_SECTOR_WEIGHTS = Object.freeze([1.25, 1.15, 1.0, 1.05, 0.90, 1.0, 0.80, 0.50, 1.10, 1.25]);
  const T2_ADJACENCY = Object.freeze([
    [1,2,3,4,8,9], [0,2,5,8], [0,1,6,7], [0,4,7,8,9],
    [0,3,6,7,8,9], [1,6,7,8], [2,4,5,7], [2,3,4,5,6,9],
    [0,1,3,4,5,9], [0,3,4,7,8],
  ].map(Object.freeze));
  const T2_COMPLEXITY_COUNTS = Object.freeze([0, 0, 60, 40, 20]);
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
  // Authored catalogue: six C-3, four C-4 and two C-5 products in each sector.
  // Final field is a relative need-frequency prior, not a product-ID pattern.
  const recipes = [
    [0,'Glazed Pot','W+E,F',1.3], [0,'Water Jug','W+E,W',1.25], [0,'Steam Cooker','W+F,E',1.2],
    [0,'Smoke Hood','F+A,E',1.0], [0,'Ceramic Basin','W+E,A',1.1], [0,'Cooling Vessel','W+A,E',1.0],
    [0,'Ceramic Stove','W+E,E+F',0.9], [0,'Condensing Cabinet','W+F,W+A',0.8],
    [0,'Crystal Decanter','W+A,E+A',0.75], [0,'Purifying Filter','W+E,E+A',0.95],
    [0,'Self-Warming Hearth','W+E,E+F,F',0.7], [0,'Living Glass Cabinet','W+A,E+F,E',0.6],

    [1,'Fired Brick','W+E,F',1.4], [1,'Stone Cement','E+A,W',1.3], [1,'Insulated Tile','E+F,A',1.15],
    [1,'Clay Pipe','W+E,A',1.2], [1,'Foundation Block','E+F,E',1.25], [1,'Weather Sealant','F+A,W',1.0],
    [1,'Glazed Roof Tile','W+E,E+F',0.95], [1,'Cloud Insulation','W+A,E+A',0.85],
    [1,'Smoke Vent','F+A,E+A',0.8], [1,'Reinforced Ceramic Panel','W+E,W+E',0.9],
    [1,'Weatherproof Arch','W+E,E+A,F',0.7], [1,'Floating Keystone','E+A,W+A,E',0.6],

    [2,'Glass Shard','E+F,A',1.25], [2,'Ceramic Vase','W+E,F',1.1], [2,'Porcelain Bead','W+E,E',1.0],
    [2,'Crystal Seed','W+A,E',1.0], [2,'Glass Bottle','E+F,W',1.3], [2,'Glazed Dish','W+E,W',1.2],
    [2,'Stained Glass','E+F,E+A',0.8], [2,'Porcelain Vessel','W+E,W+F',0.9],
    [2,'Crystal Prism','W+A,E+F',0.75], [2,'Smoke Glass','E+F,F+A',0.8],
    [2,'Rainbow Crystal','W+A,E+F,A',0.6], [2,'Phoenix Porcelain','W+E,F+A,F',0.65],

    [3,'Red Pigment','E+F,W',1.2], [3,'Soot Dye','F+A,W',1.15], [3,'Mineral Thread','E+A,A',1.3],
    [3,'Cloud Felt','W+A,A',1.2], [3,'Clay Mordant','W+E,W',1.1], [3,'Steam-Set Cloth','W+F,A',1.05],
    [3,'Silken Cloud Cloth','W+A,W+A',0.85], [3,'Enamel Pigment','W+E,E+F',0.8],
    [3,'Luminous Dye','F+A,W+F',0.75], [3,'Weatherproof Fabric','W+A,E+A',0.9],
    [3,'Enchanted Tapestry','W+A,E+A,W',0.6], [3,'Aurora Silk','W+A,F+A,A',0.65],

    [4,'Mineral Elixir','E+A,W',1.2], [4,'Calming Vapor','W+A,F',1.1], [4,'Distilled Essence','W+F,W',1.25],
    [4,'Binding Resin','W+E,F',1.0], [4,'Smoke Catalyst','F+A,E',1.05], [4,'Crystal Reagent','W+A,E',1.1],
    [4,'Restorative Potion','W+E,W+F',0.9], [4,'Clarity Draught','W+A,E+A',0.8],
    [4,'Phoenix Balm','W+F,F+A',0.75], [4,'Transmutation Solvent','E+F,W+A',0.85],
    [4,'Royal Elixir','W+F,W+E,A',0.65], [4,'Philosopher Tonic','W+F,E+A,E',0.6],

    [5,'Chisel','E+F,E',1.2], [5,'Steam Valve','W+F,A',1.25], [5,'Potter Wheel','W+E,E',1.1],
    [5,'Grinding Disc','E+A,E',1.15], [5,'Ceramic Bearing','W+E,F',1.2], [5,'Bellows Assembly','F+A,A',1.0],
    [5,'Steam Turbine','W+F,E+F',0.85], [5,'Clockwork Gear','E+F,E+A',0.95],
    [5,'Pressure Gauge','W+F,E+A',0.9], [5,'Hydraulic Press','W+F,W+E',0.8],
    [5,'Aether Engine','W+F,E+F,A',0.7], [5,'Alchemist Automaton','E+F,E+A,W',0.6],

    [6,'Oil Lamp','F+A,W',1.3], [6,'Wind Flute','E+A,A',1.1], [6,'Glass Lens','E+F,A',1.2],
    [6,'Signal Lantern','F+A,F',1.15], [6,'Steam Whistle','W+F,A',1.05], [6,'Crystal Dial','W+A,E',1.0],
    [6,'Crystal Lantern','W+A,E+F',0.9], [6,'Resonant Chime','E+A,F+A',0.75],
    [6,'Optical Instrument','E+F,W+A',0.85], [6,'Surveying Compass','E+A,E+F',0.8],
    [6,'Storm Organ','W+A,F+A,E',0.6], [6,'Phoenix Lantern','W+F,F+A,E',0.7],

    [7,'Crystal Pendant','W+A,E',1.15], [7,'Ember Ring','E+F,F',1.1], [7,'Incense Censer','F+A,E',1.0],
    [7,'Rune Tablet','W+E,F',1.2], [7,'Aether Token','E+A,A',1.0], [7,'Moon Glass','W+A,W',1.05],
    [7,'Moonstone Ornament','W+E,W+A',0.85], [7,'Arcane Seal','E+F,F+A',0.8],
    [7,'Spirit Mirror','W+A,F+A',0.75], [7,'Runic Reliquary','W+E,E+A',0.9],
    [7,'Philosopher Vessel','W+E,E+F,A',0.65], [7,'Astral Crown','W+A,E+F,F',0.6],

    [8,'Seedling Pot','W+E,W',1.3], [8,'Mineral Fertilizer','E+A,W',1.4], [8,'Irrigation Nozzle','W+F,E',1.25],
    [8,'Clay Mulch','W+E,E',1.2], [8,'Mist Irrigator','W+A,E',1.3], [8,'Smoke Repellent','F+A,W',1.1],
    [8,'Greenhouse Pane','E+F,W+A',0.95], [8,'Soil Conditioner','W+E,E+A',1.0],
    [8,'Steam Cultivator','W+F,E+F',0.85], [8,'Reservoir Liner','W+E,W+A',0.9],
    [8,'Evergreen Terrarium','W+E,W+A,E',0.7], [8,'Raincalling Sprinkler','W+F,W+A,A',0.65],

    [9,'Healing Tonic','W+F,W',1.35], [9,'Purifying Salve','W+E,W',1.3], [9,'Sterile Dressing','W+F,A',1.25],
    [9,'Mineral Compress','E+A,W',1.2], [9,'Cooling Poultice','W+A,E',1.2], [9,'Warming Liniment','E+F,W',1.1],
    [9,'Healing Unguent','W+E,W+F',1.0], [9,'Breathing Inhaler','W+A,W+F',0.95],
    [9,'Sterilizing Apparatus','W+F,E+F',0.85], [9,'Restorative Bath','W+A,W+E',0.9],
    [9,'Regenerative Elixir','W+F,W+E,W',0.75], [9,'Vitality Infuser','W+A,E+F,W',0.7],
  ];
  const T2_PRODUCTS = Object.freeze(recipes.map(([sectorIndex, name, recipe, needWeight], id) => {
    const inputs = {};
    for (const code of recipe.split(',')) inputs[code] = (inputs[code] || 0) + 1;
    const ingredients = Object.entries(inputs).map(([code, quantity]) =>
      Object.freeze([PRODUCTS.findIndex((p) => p.code === code), quantity]));
    const complexity = ingredients.reduce((c, [material, quantity]) => c + quantity * (material < 4 ? 1 : 2), 0);
    if (!TIER_BOUNDARIES.T2.includes(complexity)) throw new Error('Tier 2 recipes must be C-3 through C-5.');
    const conversionCost = 0.5 * complexity;
    return Object.freeze({
      id, code: `T2-${String(id + 1).padStart(3, '0')}`, name, sectorIndex,
      sector: T2_SECTORS[sectorIndex], complexity, inputs: Object.freeze(inputs),
      ingredients: Object.freeze(ingredients), equipmentClass: `Craft ${complexity}`,
      equipmentPrice: t2EquipmentPrice(complexity), capacity: t2Capacity(complexity),
      conversionCost, needWeight, demandWeight: needWeight * T2_SECTOR_WEIGHTS[sectorIndex],
      demandFactor: 0.45 ** (complexity - 1), reservationPremium: 1 + 0.45 * (complexity - 1),
      // Authored taste scale, independent of ingredient prices and markups.
      // At this scale (before private taste/premium), desired quantity halves.
      consumerValue: ({ 3: 8, 4: 12, 5: 16 })[complexity],
    });
  }));
  const relatedSector = (core, sector) => core === sector || T2_ADJACENCY[core].includes(sector);

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const complexity = (product) => product.complexity ?? Object.values(product.inputs).reduce((sum, quantity) => sum + quantity, 0);
  const finishedStockTarget = ({ salesEMA, coverageTicks, bootstrapStock, capacity,
    targetInventory, maxInventory }) => Math.max(0, Math.min(targetInventory, maxInventory,
      Math.max(Math.min(capacity, bootstrapStock), Math.ceil(Math.max(0, salesEMA) * coverageTicks))));
  const tier2StartingCash = (products, cfg) => {
    const direct = new Set();
    const basicQuote = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const compoundQuote = (2 * basicQuote + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
    const operatingCost = products.reduce((sum, product) => {
      for (const [material] of product.ingredients) if (material < 4) direct.add(material);
      const unitCost = product.conversionCost + product.ingredients.reduce((cost, [material, quantity]) =>
        cost + quantity * (material < 4 ? basicQuote : compoundQuote), 0);
      return sum + product.capacity * unitCost;
    }, 0);
    const lotBuffer = direct.size * cfg.minWholesaleLot * basicQuote;
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
    const basic = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const compound = (2 * basic + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
    return product.conversionCost + product.ingredients.reduce((total, [material, quantity]) =>
      total + quantity * (material < 4 ? basic : compound), 0);
  };

  root.Phase0Model = Object.freeze({
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
