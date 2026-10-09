/*
 * Canonical, editable Phase 1 model primitives.
 *
 * This file deliberately contains no browser-runtime boundary code. The
 * source kernel imports these definitions; keeping them here makes
 * topology and economic rules reviewable and testable in ordinary JavaScript.
 */
(function (root) {
  'use strict';

  const TIME = Object.freeze({
    ticksPerMonth: 30, monthsPerYear: 12, ticksPerYear: 360,
    yearsPerGeneration: 20, generationsPerAge: 24,
    ticksPerGeneration: 7200, ticksPerAge: 172800,
  });
  const calendarAt = tick => {
    const t = Math.floor(tick);
    const month = (Math.floor(t / TIME.ticksPerMonth) % TIME.monthsPerYear) + 1;
    const year = (Math.floor(t / TIME.ticksPerYear) % TIME.yearsPerGeneration) + 1;
    const generation = Math.floor(t / TIME.ticksPerGeneration);
    const age = Math.floor(t / TIME.ticksPerAge);
    return Object.freeze({
      tick: t, month, year, generation,
      generationHex: '0x' + generation.toString(16).toUpperCase(),
      age,
    });
  };
  const AGE_EQUITY_GROWTH = 2 ** (1 / TIME.ticksPerAge) - 1;
  const ELEMENTS = Object.freeze(['Water', 'Earth', 'Fire', 'Air']);
  // Machinery prices are explicit per category, not a formula. There is no
  // shared factory asset: each firm owns its equipment outright.
  const T1_BASIC_MACHINERY = 15000;
  const T1_COMPOUND_MACHINERY = 15000;
  const T2_ROUTE_SETUP = 1000;
  // Per-unit quotes support fractional cents for bulk inputs. At the
  // thousand-unit wholesale minimum this precision represents one cent.
  const MIN_UNIT_PRICE = 0.00001;
  const TIER_BOUNDARIES = Object.freeze({ T1: Object.freeze([1, 2]), T2: Object.freeze([3, 4, 5]) });
  // Named refinery roster (naming catalogue §5): a short house name plus an
  // honest trade descriptor, in material order. Additional refineries follow
  // the naming rules at the end of the catalogue.
  const T1_COMPANY_NAMES = Object.freeze([
    'Stillhouse Process Liquids', 'Anvil Reach Metals', 'Livewell Charge Refining', 'Clearbreath Gasworks',
    'Kilnward Ceramics', 'Temper House Fluids', 'Finefold Membranes',
    'Waferstead Crystalworks', 'Longstrand Composites', 'Active Bed Chemicals',
  ]);
  // Ten refined materials (naming catalogue §3). ``code`` is the legacy recipe
  // key retained as an internal compatibility key; ``symbol`` is the new
  // two-letter market symbol shown on recipes and trade cards.
  const PRODUCTS = Object.freeze([
    { code: 'W', symbol: 'PF', name: 'Process Fluid', inputs: { Water: 1 } },
    { code: 'E', symbol: 'SA', name: 'Structural Alloy', inputs: { Earth: 1 } },
    { code: 'F', symbol: 'CM', name: 'Charge Medium', inputs: { Fire: 1 } },
    { code: 'A', symbol: 'WG', name: 'Working Gas', inputs: { Air: 1 } },
    { code: 'W+E', symbol: 'MC', name: 'Mineral Ceramic', inputs: { Water: 1, Earth: 1 } },
    { code: 'W+F', symbol: 'TG', name: 'Thermal Gel', inputs: { Water: 1, Fire: 1 } },
    { code: 'W+A', symbol: 'MS', name: 'Membrane Stock', inputs: { Water: 1, Air: 1 } },
    { code: 'E+F', symbol: 'CC', name: 'Circuit Crystal', inputs: { Earth: 1, Fire: 1 } },
    { code: 'E+A', symbol: 'RC', name: 'Resin Composite', inputs: { Earth: 1, Air: 1 } },
    { code: 'F+A', symbol: 'RS', name: 'Reactive Salt', inputs: { Fire: 1, Air: 1 } },
  ].map((p, index) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, companyName: T1_COMPANY_NAMES[index], inputs: Object.freeze(p.inputs), complexity,
      role: 'intermediate-only',
      consumerValue: complexity === 1 ? 1.875 : 3.75, equipmentPrice: T1_BASIC_MACHINERY });
  }));

  const WORLD_STORY = Object.freeze({ name: 'Long Muster',
    tagline: 'A million lives. One supply chain. A war approaching.', population: 1000000,
    producers: 'Autonomous refining and manufacturing firms across a human–robot colony',
    consumers: 'One million resident consumers buying, switching suppliers and building lives',
    player: 'Human investor', entry: 'An initial investment in a refinery or manufacturing business',
    competitors: Object.freeze(['Opportunist human investors', 'Robotic executive agents']),
    alphaPlayableTiers: Object.freeze(['T1']),
    purpose: 'A colony expanding into a galactic supply network ahead of an expected war',
    demandScope: 'Escort hulls, warning networks, garden canopies, clinic beds, memory archives and everyday trade',
    society: 'A human–robot manufacturing colony in 4259',
    roboticGeneration: 'The mobilisation economy that must keep working before the fighting starts',
    conflict: 'A war approaching' });

  // Ten manufacturing sectors (naming catalogue §6): sectors name purchasing
  // domains rather than the prestige of their largest producer.
  const T2_SECTOR_DEFINITIONS = Object.freeze([
    Object.freeze({"name":"Grid & Thermal","description":"Power and heat services that keep a continuous-shift colony running"}),
    Object.freeze({"name":"Drives & Guidance","description":"Thrust hardware, navigation hardware and complete drive packages"}),
    Object.freeze({"name":"Hull & Dock Construction","description":"Shipyard purchase orders: structural form first, operational role second"}),
    Object.freeze({"name":"Settlement & Life Support","description":"Places and utilities shared by human residents and machine residents"}),
    Object.freeze({"name":"Robotics & Field Service","description":"Service bodies and replaceable parts; none is a production machine"}),
    Object.freeze({"name":"Computation & Signals","description":"The information function and the physical unit that performs it"}),
    Object.freeze({"name":"Survey & Diagnostics","description":"What is measured and whether the good is a sensor, instrument or deployed observatory"}),
    Object.freeze({"name":"Tooling & Extraction Hardware","description":"Consumables, passive tooling and fixtures that preserve the machinery monopoly"}),
    Object.freeze({"name":"Freight & Stores","description":"Handling and containment hardware; selling a container does not grant storage-fee rights"}),
    Object.freeze({"name":"Defence & Recovery","description":"Convoy survival, warning, containment and rescue in a colony preparing for war"}),
  ]);
  const T2_SECTORS = Object.freeze(T2_SECTOR_DEFINITIONS.map(sector => sector.name));
  // Named manufacturing roster (naming catalogue §6): authored identities per
  // sector, with an optional maker's mark for company badges. They are not
  // mandatory parents of every simulated firm.
  const T2_SECTOR_MANUFACTURERS = Object.freeze([
    Object.freeze({"sector":"Grid & Thermal","company":"Nightshift Powerworks","mark":"Two rail-shaped bars enclosing a small lit square."}),
    Object.freeze({"sector":"Drives & Guidance","company":"Farreach Drives","mark":"An offset ring with a single forward notch."}),
    Object.freeze({"sector":"Hull & Dock Construction","company":"Rivetline Shipbuilding","mark":"Three rivet dots along a bent hull line."}),
    Object.freeze({"sector":"Settlement & Life Support","company":"Hearthspan Habitation","mark":"A roof arc spanning two different-sized doorways."}),
    Object.freeze({"sector":"Robotics & Field Service","company":"Secondhand Robotics","mark":"Two unequal fingers meeting at one joint."}),
    Object.freeze({"sector":"Computation & Signals","company":"Packet House Electronics","mark":"Four squares with one open corner."}),
    Object.freeze({"sector":"Survey & Diagnostics","company":"Clearfield Instruments","mark":"A sighting cross broken by an open circle."}),
    Object.freeze({"sector":"Tooling & Extraction Hardware","company":"Boremark Tool Supply","mark":"A scored circle with one square cutting edge."}),
    Object.freeze({"sector":"Freight & Stores","company":"Turnaround Cargo Equipment","mark":"Two opposed arrows around a rectangular crate."}),
    Object.freeze({"sector":"Defence & Recovery","company":"Lastlight Protective Systems","mark":"A small lamp inside an incomplete shield."}),
  ]);
  const T2_MANUFACTURER_BY_SECTOR = Object.freeze(Object.fromEntries(
    T2_SECTOR_MANUFACTURERS.map(m => [m.sector, m.company])));
  // Tier 1 material -> manufacturing sector (naming catalogue 1:1 mapping; mirrors core/model.py).
  const T1_SECTOR_BY_CODE = Object.freeze({
    'W': 'Settlement & Life Support',
    'E': 'Tooling & Extraction Hardware',
    'F': 'Grid & Thermal',
    'A': 'Survey & Diagnostics',
    'W+E': 'Hull & Dock Construction',
    'W+F': 'Drives & Guidance',
    'W+A': 'Freight & Stores',
    'E+F': 'Computation & Signals',
    'E+A': 'Robotics & Field Service',
    'F+A': 'Defence & Recovery',
  });
  // Design priors for consumer demand, independent of the number of markets.
  const T2_SECTOR_WEIGHTS = Object.freeze(Array(10).fill(1));
  // Demand baskets have equal access to every other sector; no hub
  // sector receives extra demand merely from having more neighbors.
  const T2_ADJACENCY = Object.freeze(T2_SECTORS.map((_,core) =>
    Object.freeze(T2_SECTORS.map((_,i)=>i).filter(i=>i!==core))));
  const T2_MAX_PRODUCTS_PER_FIRM = 4;
  // Bulk upstream firms and small downstream workshops serve the same population.
  // Stock coverage is measured against sales, not against idle nameplate capacity.
  const ECONOMY_DEFAULTS = Object.freeze({
    seed: 137, difficultyTarget: 1, theta: .15, sigma: .005, difficultyMin: .7, difficultyMax: 1.4,
    consumerCount: 1000000, t2FirmCount: 60000,
    t0Equity: 75000000, t0License: 22000000, t0Machinery: 49000000, t0Reserve: 1000000,
    t0Capacity: 100000, t0Storage: 5000000,
    baseCost: 1, t0Markup: .25, minWholesaleLot: 1000,
    t1Equity: 1500000, t1License: 1000000, t1Machinery: 15000, t1Capacity: 2000,
    t1MaterialCost: 1.25, t1Markup: .25,
    t2Equity: 1500000, t2License: 1000000,
    t2Machinery: Object.freeze({ 3: 75000, 4: 375000, 5: 420000 }),
    t2Capacity: Object.freeze({ 3: 30, 4: 20, 5: 10 }),
    t2MaterialCost: 1.875, conversionFactor: .25,
    storage: 20000,
    footprint: Object.freeze({ 1: 1000, 2: 1000, 3: 3000, 4: 4000, 5: 5000 }),
    consumerSearchOffers: 5,
    consumerActivation: .2,
    chokeMin: 1.8, chokeMax: 3, elasticity: 2,
    productionMarginBand: .05,
    t2ReservationPremium: .25,
    pricingAggressiveness: .35, alpha: .15, reliabilityAlpha: .15, switchingStableBand: .025,
    wholesalePriceResponse: .05, priceObservationTicks: 30,
    loyaltyMultiple: Object.freeze({ 1: 83.33, 2: Object.freeze({ 3: 1.21, 4: 0.65, 5: 0.26 }), 3: 0.97 }),
    loyaltyEmaAlpha: .01,
    researchPriceMinimumOpportunities: 0, researchPriceMinimumPotentialOrders: 0,
    researchPriceMaxObservationTicks: 3600,
  });
  const t2Capacity = (complexity) => ECONOMY_DEFAULTS.t2Capacity[complexity];
  // Player-facing ownership and progression gates. These are entry/ownership
  // costs, orthogonal to the bot economy: paying a license or founding a house
  // does not move simulated economy cash. They are reference prices for the
  // account/ownership layer, not economy parameters.
  const PROGRESSION_DEFAULTS = Object.freeze({
    startingLicenses: Object.freeze(['T1']),
    // null = not for sale (the 20 Tier 0 magnates are team-controlled).
    licenseCosts: Object.freeze({ T1: 0, T2: 1000000, T0: null }),
    houseFoundingCost: 200000,
  });
  // Each output has one code and a distinct unordered Tier 1 input recipe.
  // Different processed intermediates can share raw ancestry without sharing identity.
  const recipeKey = inputs => Object.entries(inputs).sort(([a], [b]) => a.localeCompare(b))
    .map(([code, quantity]) => code + ':' + quantity).join('|');
  const elementalComposition = inputs => Object.freeze(Object.fromEntries(ELEMENTS.map(element =>
    [element, Object.entries(inputs).reduce((total, [code, quantity]) =>
      total + quantity * (PRODUCTS.find(p => p.code === code).inputs[element] || 0), 0)])));
  const T2_NEED_TYPES = Object.freeze(['Consumables', 'Components', 'Assemblies', 'Systems']);
  // All 420 recipes have names; 200 start invented and 220 remain reserved. No services.
  // Sector allocations describe applications; they impose no material gate.
const recipes = [
    [0, "Feeder Rail", "W,E,F", 1, "Components", "Good", true],
    [0, "Charge Intake", "F,W+E", 1, "Components", "Good", true],
    [0, "Reserve Cell Stack", "W,E,F,A", 1, "Assemblies", "Good", true],
    [0, "Load Balancer", "W,F,E+F", 1, "Assemblies", "Good", true],
    [0, "Heat Transfer Block", "F,A,E+A", 1, "Assemblies", "Good", true],
    [0, "Discharge Stack", "W,F,F+A", 1, "Assemblies", "Good", true],
    [0, "Sunskin Sheet", "E,F,W+E", 1, "Assemblies", "Good", true],
    [0, "Cooling Wing", "F,A,W+F", 1, "Assemblies", "Good", true],
    [0, "Baseload Core", "W,E,F,W+E", 1, "Systems", "Good", true],
    [0, "Pulse Reserve Chamber", "W,F,A,W+F", 1, "Systems", "Good", true],
    [0, "Sunward Collector Ring", "E,F,A,W+A", 1, "Systems", "Good", true],
    [0, "Frontier Generator Station", "W,E,F,E+F", 1, "Systems", "Good", true],
    [0, "Blackout Reserve Rack", "W,F,A,E+A", 1, "Systems", "Good", true],
    [0, "Peakload Generator", "E,F,A,F+A", 1, "Systems", "Good", true],
    [0, "Field Supply Pack", "F,W+A,F+A", 1, "Systems", "Good", true],
    [0, "Wasteheat Recovery Bank", "F,E+F,F+A", 1, "Systems", "Good", true],
    [0, "Powerbeam Emitter", "F,E+A,F+A", 1, "Systems", "Good", true],
    [0, "Powerbeam Rectenna", "F,W+E,W+F", 1, "Systems", "Good", true],
    [0, "Close-Orbit Collector", "F,W+A,E+F", 1, "Systems", "Good", true],
    [0, "Watchlight Generator", "F,E+A,F+A", 1, "Systems", "Good", true],
    [1, "Exhaust Throat", "W,W+F", 1, "Components", "Good", true],
    [1, "Reaction Mass Capsule", "E,W+F", 1, "Consumables", "Good", true],
    [1, "Trim Jet", "W,E,W+F", 1, "Assemblies", "Good", true],
    [1, "Ion Focusing Ring", "E,F,W+F", 1, "Assemblies", "Good", true],
    [1, "Plasma Feed Head", "E,A,W+F", 1, "Assemblies", "Good", true],
    [1, "Feed Regulator", "W+E,W+F", 1, "Assemblies", "Good", true],
    [1, "Attitude Rotor", "W+F,W+A", 1, "Assemblies", "Good", true],
    [1, "Drift Reference Block", "W+F,E+F", 1, "Assemblies", "Good", true],
    [1, "Cruise Ion Drive", "W,E,A,W+F", 1, "Systems", "Good", true],
    [1, "Transfer Plasma Drive", "E,F,A,W+F", 1, "Systems", "Good", true],
    [1, "Longburn Engine", "W,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Pulse Drive Vessel", "E,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Photon Sail Frame", "F,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Plasma Sail Loop", "A,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Slingshot Course Unit", "W,W+F,F+A", 1, "Systems", "Good", true],
    [1, "Farpoint Guidance Rack", "E,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Berthing Drive Pack", "F,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Touchdown Thrust Frame", "A,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Departure Booster Rack", "W,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Towboat Drive Block", "E,W+F,F+A", 1, "Systems", "Good", true],
    [2, "Outer Skin Blank", "F,W+E", 1, "Components", "Good", true],
    [2, "Loadbearing Rib", "A,W+E", 1, "Components", "Good", true],
    [2, "Compartment Partition", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Service Lock Hatch", "F,A,W+E", 1, "Assemblies", "Good", true],
    [2, "Berth Mating Ring", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Viewport Shutter", "W+E,W+F", 1, "Assemblies", "Good", true],
    [2, "Touchdown Leg", "W+E,E+A", 1, "Assemblies", "Good", true],
    [2, "Freight Aperture Gate", "W+E,F+A", 1, "Assemblies", "Good", true],
    [2, "Platform Truss Set", "W,E,F,W+E", 1, "Systems", "Good", true],
    [2, "Picket Cutter Frame", "W,E,A,W+E", 1, "Systems", "Good", true],
    [2, "Bulk Carrier Frame", "F,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Charting Vessel Frame", "A,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Prospector Barge Frame", "W,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Harbour Tug Frame", "E,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Convoy Escort Frame", "F,W+E,E+F", 1, "Systems", "Good", true],
    [2, "Ascent Stage Shell", "A,W+E,E+A", 1, "Systems", "Good", true],
    [2, "Return Capsule Body", "W,W+E,F+A", 1, "Systems", "Good", true],
    [2, "Station Backbone", "E,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Berth Junction Frame", "F,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Slipway Truss", "A,W+E,E+F", 1, "Systems", "Good", true],
    [3, "Interior Liner Sheet", "W,F,A", 1, "Components", "Good", true],
    [3, "Foundation Tie", "W,W+F", 1, "Components", "Good", true],
    [3, "Pressure Partition", "W,E,F,A", 1, "Assemblies", "Good", true],
    [3, "Lock Chamber Gate", "W,F,W+A", 1, "Assemblies", "Good", true],
    [3, "Service Deck Panel", "W,F,E+F", 1, "Assemblies", "Good", true],
    [3, "Potable Main Section", "W,E,E+A", 1, "Assemblies", "Good", true],
    [3, "Exposure Curtain", "W,F,F+A", 1, "Assemblies", "Good", true],
    [3, "Daycycle Luminaire", "W,A,W+E", 1, "Assemblies", "Good", true],
    [3, "Living Compartment", "W,E,F,W+E", 1, "Systems", "Good", true],
    [3, "Settlement Ring Shell", "W,F,A,W+F", 1, "Systems", "Good", true],
    [3, "Frontier Commons Module", "W,E,F,W+A", 1, "Systems", "Good", true],
    [3, "Spin Section Hub", "W,F,A,E+F", 1, "Systems", "Good", true],
    [3, "Rockhold Foundation", "W,E,F,E+A", 1, "Systems", "Good", true],
    [3, "Transit Refuge Module", "W,F,A,F+A", 1, "Systems", "Good", true],
    [3, "Mixed-Crew Quarters", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Cultivation Room Shell", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Isolation Ward Module", "W,E+A,F+A", 1, "Systems", "Good", true],
    [3, "Garden Pressure Canopy", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Buried Habitat Sleeve", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Tether Ground Footing", "W,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Service Joint Cartridge", "W,E+A", 1, "Components", "Good", true],
    [4, "Linkage Pushrod", "E,E+A", 1, "Components", "Good", true],
    [4, "Adaptive Grip Head", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Wrist Interface Ring", "W,E,E+A", 1, "Assemblies", "Good", true],
    [4, "Rubble Wheel", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Reach Limb", "W+E,E+A", 1, "Assemblies", "Good", true],
    [4, "Contact Sense Pad", "W+F,E+A", 1, "Assemblies", "Good", true],
    [4, "Pressure Muscle Pack", "W+A,E+A", 1, "Assemblies", "Good", true],
    [4, "Utility Attendant", "E,F,A,E+A", 1, "Systems", "Good", true],
    [4, "Hull Cleaning Crawler", "W,E,F,E+A", 1, "Systems", "Good", true],
    [4, "Faultfinding Walker", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Pit Scout", "E,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Patch Service Crawler", "F,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Freight Porter", "A,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Clinical Microhandler", "W,W+F,E+A", 1, "Systems", "Good", true],
    [4, "Exterior Service Walker", "E,W+A,E+A", 1, "Systems", "Good", true],
    [4, "Terrain Recon Rover", "F,E+F,E+A", 1, "Systems", "Good", true],
    [4, "Conduit Service Crawler", "A,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Settlement Caretaker", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Recovery Manipulator", "E,W+F,E+A", 1, "Systems", "Good", true],
    [5, "Signal Path Strip", "F,E+F", 1, "Components", "Good", true],
    [5, "State Storage Tile", "A,E+F", 1, "Components", "Good", true],
    [5, "Control Backplane", "W,E,E+F", 1, "Assemblies", "Good", true],
    [5, "Training Cache Block", "F,A,E+F", 1, "Assemblies", "Good", true],
    [5, "Local Link Radio", "E+F,E+A", 1, "Assemblies", "Good", true],
    [5, "Line Booster", "E+F,F+A", 1, "Assemblies", "Good", true],
    [5, "Packet Junction", "W+E,E+F", 1, "Assemblies", "Good", true],
    [5, "Message Queue Module", "W+F,E+F", 1, "Assemblies", "Good", true],
    [5, "Compute Service Rack", "W,E,A,E+F", 1, "Systems", "Good", true],
    [5, "Course Solver Rack", "E,F,A,E+F", 1, "Systems", "Good", true],
    [5, "Scheduling Engine", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Shielded Control Computer", "A,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Coherent Compute Cell", "W,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Neighbourhood Server", "E,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Convoy Network Server", "F,E+F,F+A", 1, "Systems", "Good", true],
    [5, "High-Orbit Repeater", "A,W+E,E+F", 1, "Systems", "Good", true],
    [5, "Tightbeam Link Terminal", "W,W+F,E+F", 1, "Systems", "Good", true],
    [5, "Longreach Radio Mast", "E,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Delay Network Gateway", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Continuity Archive", "A,E+F,F+A", 1, "Systems", "Good", true],
    [6, "Optical Pickup Blank", "A,W+A", 1, "Components", "Good", true],
    [6, "Exposure Sensing Sheet", "A,E+F", 1, "Components", "Good", true],
    [6, "Composition Reader", "W,E,F,A", 1, "Assemblies", "Good", true],
    [6, "Rangefinding Dish", "W,A,W+F", 1, "Assemblies", "Good", true],
    [6, "Laser Survey Head", "W,A,W+A", 1, "Assemblies", "Good", true],
    [6, "Heat Fault Imager", "E,A,E+F", 1, "Assemblies", "Good", true],
    [6, "Flux Pickup", "F,A,E+A", 1, "Assemblies", "Good", true],
    [6, "Ground Motion Pickup", "W,A,F+A", 1, "Assemblies", "Good", true],
    [6, "Longwatch Telescope", "W,F,A,W+E", 1, "Systems", "Good", true],
    [6, "World Survey Capsule", "W,E,A,W+F", 1, "Systems", "Good", true],
    [6, "Rock Census Probe", "W,F,A,W+A", 1, "Systems", "Good", true],
    [6, "Forward Survey Beacon", "W,E,A,E+F", 1, "Systems", "Good", true],
    [6, "Sample Return Rover", "W,F,A,E+A", 1, "Systems", "Good", true],
    [6, "Strata Listening Kit", "W,E,A,F+A", 1, "Systems", "Good", true],
    [6, "Orbital Mapping Camera", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Particle Watch Station", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Stellar Weather Monitor", "A,E+A,F+A", 1, "Systems", "Good", true],
    [6, "Deepband Listening Array", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Clinical Scan Bed", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Worldfinder Optics Rack", "A,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Cutter Insert", "E,E+A", 1, "Components", "Good", true],
    [7, "Lapping Grit Batch", "E,F+A", 1, "Consumables", "Good", true],
    [7, "Rotary Bit Crown", "E,A,W+E", 1, "Assemblies", "Good", true],
    [7, "Breaker Jaw Liner", "E,F,W+F", 1, "Assemblies", "Good", true],
    [7, "Finish Abrasion Disc", "E,A,W+A", 1, "Assemblies", "Good", true],
    [7, "Melt Vessel Sleeve", "W,E,E+F", 1, "Assemblies", "Good", true],
    [7, "Forming Die Block", "E,F,E+A", 1, "Assemblies", "Good", true],
    [7, "Joining Tip Cassette", "E,A,F+A", 1, "Assemblies", "Good", true],
    [7, "Furnace Hearth Set", "E,F,A,W+E", 1, "Systems", "Good", true],
    [7, "Drill Guide Frame", "W,E,A,W+F", 1, "Systems", "Good", true],
    [7, "Regolith Bucket Shell", "E,F,A,W+A", 1, "Systems", "Good", true],
    [7, "Crusher Wear Kit", "W,E,A,E+F", 1, "Systems", "Good", true],
    [7, "Separation Drum Sleeve", "E,F,A,E+A", 1, "Systems", "Good", true],
    [7, "Process Bath Liner", "W,E,F,F+A", 1, "Systems", "Good", true],
    [7, "Smelter Throat Set", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Casting Form Rack", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Workholding Fixture Bed", "E,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Deposition Build Tray", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Extrusion Die Cassette", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Crystal Seed Cradle", "E,E+A,F+A", 1, "Systems", "Good", true],
    [8, "Load Lash", "W,W+A", 1, "Components", "Good", true],
    [8, "Tamper Witness Strip", "E,W+A", 1, "Components", "Good", true],
    [8, "Ration Transport Drum", "W,E,W+A", 1, "Assemblies", "Good", true],
    [8, "Stores Shelf Frame", "F,A,W+A", 1, "Assemblies", "Good", true],
    [8, "Freight Dock Coupling", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Roller Track Section", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Berth Holding Claw", "W+A,E+A", 1, "Assemblies", "Good", true],
    [8, "Load Skid", "W+A,F+A", 1, "Assemblies", "Good", true],
    [8, "General Freight Capsule", "W,E,F,W+A", 1, "Systems", "Good", true],
    [8, "Coldchain Medical Carrier", "W,E,A,W+A", 1, "Systems", "Good", true],
    [8, "Sealed Goods Container", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Hazard Isolation Chest", "E,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Self-Routing Load Cart", "F,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Dry Ration Hopper", "A,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Vacuum Transfer Lock", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Orbital Stowage Frame", "E,W+A,E+A", 1, "Systems", "Good", true],
    [8, "Ship Loading Bridge", "F,W+A,F+A", 1, "Systems", "Good", true],
    [8, "Quayside Lift", "A,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Drivefeed Transfer Skid", "W,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Breathing Gas Vessel", "E,W+A,E+F", 1, "Systems", "Good", true],
    [9, "Field Screen Weave", "F,F+A", 1, "Components", "Good", true],
    [9, "Crush Cushion Block", "A,F+A", 1, "Components", "Good", true],
    [9, "Fragment Catch Panel", "W,E,F+A", 1, "Assemblies", "Good", true],
    [9, "Exposure Baffle", "F,A,F+A", 1, "Assemblies", "Good", true],
    [9, "Breach Stop Curtain", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Firebreak Shutter", "W+E,F+A", 1, "Assemblies", "Good", true],
    [9, "Distress Ping Unit", "W+F,F+A", 1, "Assemblies", "Good", true],
    [9, "Overload Arrestor", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Emergency Shutoff Block", "W,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Rescue Line Drum", "E,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Deflection Field Rack", "F,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Storm Refuge Capsule", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Pressure Patch Kit", "W,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Quench Response Pack", "E,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Screen Interceptor", "F,W+F,F+A", 1, "Systems", "Good", true],
    [9, "Close-Pass Warning Unit", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Abandon-Ship Capsule", "W,E+F,F+A", 1, "Systems", "Good", true],
    [9, "Recovery Launch", "E,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Approach Watch Network", "F,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Particle Storm Screen", "A,W+F,F+A", 1, "Systems", "Good", true],
    [3, "Reserved Settlement 001", "W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Settlement 002", "W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Settlement 003", "W,W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Settlement 004", "W,W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 005", "W,W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 006", "W,W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 007", "W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 008", "W,W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 009", "W,W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 010", "W,W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 011", "W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 012", "W,W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 013", "W,W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 014", "W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 015", "W,W,W,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 016", "W,W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 017", "W,W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 018", "W,W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 019", "W,W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 020", "W,W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 021", "W,W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 022", "W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 023", "W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 024", "W,W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 025", "W,W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 026", "W,W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 027", "W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 028", "W,W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 029", "W,W,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 030", "W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 031", "W,W,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 032", "W,W,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 033", "W,W,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 034", "W,W,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 035", "W,W,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 036", "W,W,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 037", "W,W,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 038", "W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 039", "W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 040", "W,W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 041", "W,W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 042", "W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 043", "W,W,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 044", "W,W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 045", "W,W,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 046", "W,W,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 047", "W,W,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 048", "W,W,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 049", "W,W,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 050", "W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 051", "W,W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 052", "W,W,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 053", "W,W,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 054", "W,W,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 055", "W,W,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 056", "W,W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 057", "W,W,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 058", "W,W,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Hull 059", "W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 060", "W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 061", "W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 062", "W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 063", "W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 064", "W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 065", "W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 066", "W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 067", "W,E,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Settlement 068", "W,E,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 069", "W,E,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 070", "W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 071", "W,E,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 072", "W,E,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 073", "W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 074", "W,E,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 075", "W,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 076", "W,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 077", "W,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 078", "W,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 079", "W,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 080", "W,E,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 081", "W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 082", "W,E,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 083", "W,E,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 084", "W,E,F,A,A", 1, "Components", "Good", false],
    [1, "Reserved Drives 085", "W,E,F,W+F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 086", "W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 087", "W,E,A,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 088", "W,E,A,A,A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 089", "W,E,A,E+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 090", "W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 091", "W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 092", "W,F,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Settlement 093", "W,F,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 094", "W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 095", "W,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 096", "W,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 097", "W,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 098", "W,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 099", "W,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 100", "W,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 101", "W,F,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 102", "W,F,A,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 103", "W,F,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 104", "W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 105", "W,F,W+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 106", "W,F,E+A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 107", "W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 108", "W,A,A,A", 1, "Components", "Good", false],
    [3, "Reserved Settlement 109", "W,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 110", "W,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 111", "W,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 112", "W,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 113", "W,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 114", "W,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 115", "W,A,A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 116", "W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 117", "W,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Hull 118", "W,W+E", 1, "Components", "Good", false],
    [2, "Reserved Hull 119", "W,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Hull 120", "W,W+E,W+A", 1, "Components", "Good", false],
    [2, "Reserved Hull 121", "W,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Drives 122", "W,W+F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 123", "W,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 124", "W,W+A,E+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 125", "W,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 126", "W,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computation 127", "W,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computation 128", "W,E+F,E+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 129", "W,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 130", "W,F+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 131", "W,F+A,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 132", "E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Tooling 133", "E,E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Tooling 134", "E,E,E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Tooling 135", "E,E,E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 136", "E,E,E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 137", "E,E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 138", "E,E,E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 139", "E,E,E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 140", "E,E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 141", "E,E,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 142", "E,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 143", "E,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 144", "E,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 145", "E,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 146", "E,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 147", "E,E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 148", "E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 149", "E,E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 150", "E,E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 151", "E,E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 152", "E,E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 153", "E,E,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 154", "E,E,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 155", "E,E,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 156", "E,E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 157", "E,E,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 158", "E,E,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 159", "E,E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 160", "E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 161", "E,E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 162", "E,E,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 163", "E,E,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 164", "E,E,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 165", "E,E,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 166", "E,E,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 167", "E,E,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 168", "E,E,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Hull 169", "E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 170", "E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 171", "E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 172", "E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 173", "E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 174", "E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 175", "E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 176", "E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 177", "E,F,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 178", "E,F,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 179", "E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 180", "E,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 181", "E,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 182", "E,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 183", "E,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 184", "E,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 185", "E,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 186", "E,F,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 187", "E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 188", "E,F,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 189", "E,F,A,A,A", 1, "Components", "Good", false],
    [8, "Reserved Freight 190", "E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 191", "E,F,E+F", 1, "Components", "Good", false],
    [9, "Reserved Defence 192", "E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 193", "E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 194", "E,A,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 195", "E,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Hull 196", "E,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Drives 197", "E,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 198", "E,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 199", "E,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 200", "E,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 201", "E,A,A,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 202", "E,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Hull 203", "E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Hull 204", "E,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Hull 205", "E,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Drives 206", "E,W+F,W+F", 1, "Components", "Good", false],
    [1, "Reserved Drives 207", "E,W+F,E+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 208", "E,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 209", "E,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computation 210", "E,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computation 211", "E,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computation 212", "E,E+F,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 213", "E,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 214", "E,F+A,F+A", 1, "Components", "Good", false],
    [0, "Reserved Grid 215", "F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Grid 216", "F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Grid 217", "F,F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Grid 218", "F,F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Grid 219", "F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Grid 220", "F,F,F,A,A", 1, "Components", "Good", false],
  ];

  // ---- build the catalogue from the recipe list ----
  // Production equipment classes (naming catalogue §7): bench, cell and hall
  // communicate increasing industrial scale; the noun after "Production"
  // distinguishes the purchase without magical fabrication language.
  const EQUIPMENT_CLASS = Object.freeze({ 3: 'Production Bench', 4: 'Production Cell', 5: 'Production Hall' });
  // The two Water houses are the only producers of complete production
  // machinery (naming catalogue §4).
  const EQUIPMENT_MAKERS = Object.freeze(['Meltwell Ice & Machine', 'Brinewright Water & Machine']);
  const EQUIPMENT_PRICE = Object.freeze({ 3: 75000, 4: 375000, 5: 420000 });
  const T2_CAPACITY = Object.freeze({ 3: 30, 4: 20, 5: 10 });
  const T2_CONVERSION_COST = Object.freeze({ 3: 0.5, 4: 0.75, 5: 1.0 });
  const T2_CONSUMER_VALUE = Object.freeze({ 3: 3.5, 4: 4.0, 5: 4.5 });
  const INVENTED_PER_COMPLEXITY = Object.freeze({ 3: 2, 4: 6, 5: 12 });

  const sectorSignature = (sectorIndex) => Object.keys(T1_SECTOR_BY_CODE)
    .find((code) => T1_SECTOR_BY_CODE[code] === T2_SECTORS[sectorIndex]);

  const buildT2 = (entry, id) => {
    const [sectorIndex, name, recipe, authoredNeedWeight, needType, kind, invented] = entry;
    const inputs = {};
    for (const code of recipe.split(',')) inputs[code] = (inputs[code] || 0) + 1;
    const ingredients = Object.entries(inputs)
      .map(([code, quantity]) => [PRODUCTS.findIndex((p) => p.code === code), quantity])
      .sort((a, b) => a[0] - b[0]);
    const complexity = ingredients.reduce((c, [material, quantity]) => c + quantity * (material < 4 ? 1 : 2), 0);
    const recipeKey = Object.entries(inputs).sort(([a], [b]) => a.localeCompare(b))
      .map(([code, quantity]) => code + ':' + quantity).join('|');
    return Object.freeze({
      id, code: `T2-${String(id + 1).padStart(3, '0')}`, name, kind, needType, sectorIndex,
      sector: T2_SECTORS[sectorIndex], primaryMaterial: sectorSignature(sectorIndex),
      manufacturer: T2_MANUFACTURER_BY_SECTOR[T2_SECTORS[sectorIndex]],
      complexity, inputs: Object.freeze(inputs), ingredients: Object.freeze(ingredients), recipeKey,
      equipmentClass: EQUIPMENT_CLASS[complexity], equipmentPrice: EQUIPMENT_PRICE[complexity],
      capacity: T2_CAPACITY[complexity], conversionCost: T2_CONVERSION_COST[complexity],
      needWeight: 1 / INVENTED_PER_COMPLEXITY[complexity], demandWeight: 1 / 20,
      demandFactor: 0.45 ** (complexity - 1), reservationPremium: 1 + 0.45 * (complexity - 1),
      consumerValue: T2_CONSUMER_VALUE[complexity], invented,
    });
  };

  const T2_CATALOGUE = Object.freeze(recipes.map((r, i) => buildT2(r, i)));
  const T2_PRODUCTS = Object.freeze(T2_CATALOGUE.filter((p) => p.invented).map((p, i) => Object.freeze({ ...p, id: i })));
  const T2_UNINVENTED_PRODUCTS = Object.freeze(T2_CATALOGUE.filter((p) => !p.invented));
  const T2_COMPLEXITY_COUNTS = Object.freeze([1, 2, 3, 4, 5].map((c) => T2_PRODUCTS.filter((p) => p.complexity === c).length));
  const T2_PRODUCT_BY_CODE = Object.freeze(Object.fromEntries(T2_PRODUCTS.map((p) => [p.code, p])));

  const portfolioOptions = (products, maxWidth = T2_MAX_PRODUCTS_PER_FIRM) => {
    const options = [], pick = [];
    const visit = (start, remaining) => {
      if (!remaining) { options.push(Object.freeze(pick.slice())); return; }
      for (let i = start; i <= products.length - remaining; i++) {
        pick.push(products[i]); visit(i + 1, remaining - 1); pick.pop();
      }
    };
    for (let width = 1; width <= Math.min(maxWidth, products.length); width++) visit(0, width);
    return Object.freeze(options);
  };
  const relatedSector = (core, sector) => core === sector || T2_ADJACENCY[core].includes(sector);

  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const complexity = (product) => product.complexity ?? Object.values(product.inputs).reduce((sum, quantity) => sum + quantity, 0);
  const finishedStockTarget = ({ salesEMA, coverageTicks, bootstrapStock, capacity,
    targetInventory, maxInventory }) => Math.max(0, Math.min(targetInventory, maxInventory,
      Math.max(Math.min(capacity, bootstrapStock), Math.ceil(Math.max(0, salesEMA) * coverageTicks))));
  const tier2StartingCash = (products, cfg) => {
    const direct = new Set();
    const rawQuote = cfg.baseCost * cfg.difficultyTarget * (1 + cfg.t0Markup);
    const basicQuote = (rawQuote + cfg.manufacturingCostPerUnit) * (1 + cfg.t0Markup);
    const compoundQuote = (2 * rawQuote + cfg.manufacturingCostPerUnit) *
      (1 + cfg.t0Markup + cfg.compoundMarkupPremium);
    const operatingCost = products.reduce((sum, product) => {
      for (const [material] of product.ingredients) if (material < 4) direct.add(material);
      const unitCost = product.conversionCost * (cfg.tier2ConversionCostScale ?? 1) + product.ingredients.reduce((cost, [material, quantity]) =>
        cost + quantity * (material < 4 ? basicQuote : compoundQuote), 0);
      return sum + cfg.tier2CompanyCapacity / products.length * unitCost;
    }, 0);
    const lotBuffer = direct.size * basicQuote;
    return Math.ceil(Math.max(cfg.tier2MinimumCash,
      operatingCost * cfg.tier2WorkingCashTicks + lotBuffer) / 50) * 50;
  };
  const demandAtPrice = (qMax, chokePrice, price, elasticity) =>
    qMax > 0 && chokePrice > 0 && price >= 0 && elasticity > 0
      ? qMax / (1 + Math.pow(price / chokePrice, elasticity))
      : 0;
  const loyaltyCost = (reliability, minimum, maximum) =>
    minimum + (maximum - minimum) * clamp(reliability, 0, 1);
  const reliabilityScore = (fulfillment, priceStability, availability) =>
    0.5 * clamp(fulfillment, 0, 1) +
    0.3 * clamp(priceStability, 0, 1) +
    0.2 * clamp(availability, 0, 1);
  const nextReliability = (current, score, alpha) =>
    clamp(current + clamp(alpha, 0, 1) * (score - current), 0, 1);
  // Derivative-following pricebot: Kephart, Hanson & Greenwald (2000), §3.2.
  // Total observed gross profit per tick is the objective, not margin per unit.
  // No consumer value, normal t0Markup or market-wide ideal enters this rule.
  const adaptivePrice = ({ oldPrice, unitCost, profit, previousProfit, direction = 1,
    sales, stock, demand = sales, available = sales + stock, stepScale = 1,
    pricingAggressiveness = 0.35, response = 0.05 }) => {
    const floor = Math.max(MIN_UNIT_PRICE, unitCost), price = Math.max(floor, oldPrice);
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
    const next = Math.max(floor, price * Math.exp(nextDirection * clamp(pricingAggressiveness, 0, 1) * response * scale));
    if (next === price && nextDirection < 0) nextDirection = 1;
    return { price: next, direction: nextDirection, stepScale: scale };
  };
  // Exogenous recipe profiles may express repeatable compound-based batches
  // and rarer bespoke fabrication. These engineering coefficients are fixed
  // configuration data; realized prices and equity targets never enter them.
  const recipeMarginFactor = (product, standardization = 0, specialization = 0, materialBalance = []) => {
    const compounds = product.ingredients.reduce((total, [material, units]) => total + (material >= 4 ? units : 0), 0);
    const materialTilt = product.ingredients.reduce((total, [material, units]) => total + units * (materialBalance[material] ?? 0), 0);
    return Math.exp(specialization * (product.complexity - 3) - standardization * compounds - materialTilt);
  };
  const tier2StartingMarkup = (product,cfg) =>
    ((cfg.tier2BaseMarkup >= 0 ? cfg.tier2BaseMarkup : cfg.t0Markup) + cfg.tier2MarkupPremium * (product.complexity-3)) *
    recipeMarginFactor(product, cfg.tier2CompoundStandardization, cfg.tier2ComplexitySpecialization, cfg.tier2MaterialBalance);
  const procurementProfile = (product,cfg,referenceCost) => {
    const t0Markup = ((cfg.procurementBaseMarkup ?? .25) + (cfg.procurementMarkupPremium ?? .05) * (product.complexity-3)) *
      recipeMarginFactor(product, cfg.procurementCompoundStandardization, cfg.procurementComplexitySpecialization, cfg.procurementMaterialBalance);
    const baseline = .25;
    return Object.freeze({ t0Markup,
      valuation: referenceCost * (1+t0Markup) / (1+baseline) });
  };
  const initialTier2Cost = (product, cfg) => {
    const raw = cfg.baseCost * cfg.difficultyTarget * (1 + cfg.t0Markup);
    const basic = (raw + cfg.manufacturingCostPerUnit) * (1 + cfg.t0Markup);
    const compound = (2 * raw + cfg.manufacturingCostPerUnit) *
      (1 + cfg.t0Markup + cfg.compoundMarkupPremium);
    return product.conversionCost * (cfg.tier2ConversionCostScale ?? 1) + product.ingredients.reduce((total, [material, quantity]) =>
      total + quantity * (material < 4 ? basic : compound), 0);
  };

  // Authored procurement engineering benchmarks, fixed for a simulation run.
  // They are independent of current supplier quotes and requested markups.
  const referenceTier2Cost = (product, cfg = {}) => product.conversionCost * (cfg.procurementConversionReferenceScale ?? 1) +
    product.ingredients.reduce((total, [material, quantity]) => total + quantity *
      (material < 4 ? (cfg.procurementBasicReferenceCost ?? 1.875) : (cfg.procurementCompoundReferenceCost ?? 3.85)), 0);

  root.Phase0Model = Object.freeze({
    TIME, calendarAt, AGE_EQUITY_GROWTH, INVENTED_PER_COMPLEXITY,
    T2_CATALOGUE, T2_UNINVENTED_PRODUCTS,
    WORLD_STORY,
    PROGRESSION_DEFAULTS,
        T2_PRODUCT_BY_CODE,
    ECONOMY_DEFAULTS,
    finishedStockTarget,
    tier2StartingCash,
    TIER_BOUNDARIES,
    T2_SECTOR_WEIGHTS,
    T2_MAX_PRODUCTS_PER_FIRM, T1_COMPANY_NAMES, T1_BASIC_MACHINERY, T1_COMPOUND_MACHINERY, T2_ROUTE_SETUP, MIN_UNIT_PRICE,
    ELEMENTS,
    PRODUCTS,
    T2_PRODUCTS,
    T2_SECTORS,
    T1_SECTOR_BY_CODE,
    T2_SECTOR_MANUFACTURERS, T2_MANUFACTURER_BY_SECTOR, EQUIPMENT_MAKERS,
    T2_NEED_TYPES,
    T2_SECTOR_DEFINITIONS,
    T2_ADJACENCY,
    relatedSector, portfolioOptions,
    T2_COMPLEXITY_COUNTS,
    t2Capacity,
    clamp,
    complexity,
    demandAtPrice,
    loyaltyCost,
    reliabilityScore,
    nextReliability,
    adaptivePrice,
    initialTier2Cost, referenceTier2Cost, tier2StartingMarkup, procurementProfile,
  });
})(typeof self !== 'undefined' ? self : globalThis);
