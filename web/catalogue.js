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
  // Stature suffix: single-element refiners (C-1) are 'Inc.'; dual-element
  // integrated producers (C-2) are 'Corp.' (mirrors the element-coverage spectrum).
  const T1_COMPANY_NAMES = Object.freeze([
    'Aster Hydrite Foundry, Inc.', 'Meridian Territe Works, Inc.', 'Helion Pyrrite Cells, Inc.', 'Cirrus Aerite Works, Inc.',
    'Vanguard Ceramite Forge, Corp.', 'Caldera Thermalite Forge, Corp.', 'Spindle Fibrite Mills, Corp.',
    'Lattice Silicite Foundry, Corp.', 'Truss Polymerite Works, Corp.', 'Catalyst Reactite Works, Corp.',
  ]);
  const PRODUCTS = Object.freeze([
    { code: 'W', name: 'Hydrite', inputs: { Water: 1 } },
    { code: 'E', name: 'Territe', inputs: { Earth: 1 } },
    { code: 'F', name: 'Pyrrite', inputs: { Fire: 1 } },
    { code: 'A', name: 'Aerite', inputs: { Air: 1 } },
    { code: 'W+E', name: 'Ceramite', inputs: { Water: 1, Earth: 1 } },
    { code: 'W+F', name: 'Thermalite', inputs: { Water: 1, Fire: 1 } },
    { code: 'W+A', name: 'Fibrite', inputs: { Water: 1, Air: 1 } },
    { code: 'E+F', name: 'Silicite', inputs: { Earth: 1, Fire: 1 } },
    { code: 'E+A', name: 'Polymerite', inputs: { Earth: 1, Air: 1 } },
    { code: 'F+A', name: 'Reactite', inputs: { Fire: 1, Air: 1 } },
  ].map((p, index) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, companyName: T1_COMPANY_NAMES[index], inputs: Object.freeze(p.inputs), complexity,
      role: 'intermediate-only',
      consumerValue: complexity === 1 ? 1.875 : 3.75, equipmentPrice: T1_BASIC_MACHINERY });
  }));

  const WORLD_STORY = Object.freeze({ name: 'Robotic Space Generation', population: 1000000,
    producers: 'Robotic industry serving a far-future human society', consumers: 'External galactic procurement agents',
    player: 'Human investor', entry: 'An initial investment in a Tier 1 or Tier 2 business',
    competitors: Object.freeze(['Opportunist human investors', 'Robotic executive agents']),
    alphaPlayableTiers: Object.freeze(['T1']),
    purpose: 'Preparation for a major galactic war and continuity of civilian life',
    demandScope: 'Fleet readiness, civilian settlements, life support, healthcare, learning hardware and industrial supply',
    society: 'Human civilization in the far future',
    roboticGeneration: "Humanity's industrial vessel",
    conflict: 'Preparation for a major galactic war' });

  // Galactic application sectors are independent of manufacturing materials.
  const T2_SECTOR_DEFINITIONS = Object.freeze([
    Object.freeze({"name":"Power & Energy","description":"Civilian and fleet power generation, storage, distribution and thermal control"}),
    Object.freeze({"name":"Propulsion & Navigation","description":"Civilian transport and fleet propulsion, maneuvering and route control"}),
    Object.freeze({"name":"Spacecraft & Hulls","description":"Transport, evacuation and fleet spacecraft structures, pressure vessels and orbital platforms"}),
    Object.freeze({"name":"Habitats & Life Support","description":"Shelter, food cultivation, water recovery, atmosphere control and physical care facilities"}),
    Object.freeze({"name":"Robotics & Automation","description":"Industrial, repair, medical and rescue robots, actuators, tooling and autonomous machinery"}),
    Object.freeze({"name":"Computing & Communications","description":"Civilian and fleet processors, archives, networks, communications and learning hardware"}),
    Object.freeze({"name":"Science & Diagnostics","description":"Scientific instruments, medical diagnostics, environmental monitoring and survey equipment"}),
    Object.freeze({"name":"Mining & Industry","description":"Resource extraction, refining, fabrication and tooling for civilian and fleet production"}),
    Object.freeze({"name":"Logistics & Provisioning","description":"Cargo handling, food preservation, medical storage, provisioning and distribution hardware"}),
    Object.freeze({"name":"Defence & Rescue","description":"Fleet defence, civilian protection, emergency response, rescue and evacuation equipment"}),
  ]);
  const T2_SECTORS = Object.freeze(T2_SECTOR_DEFINITIONS.map(sector => sector.name));
  // Tier 1 material -> galactic sector (canon 1:1 mapping; mirrors core/model.py).
  const T1_SECTOR_BY_CODE = Object.freeze({
    'W': 'Habitats & Life Support',
    'E': 'Mining & Industry',
    'F': 'Power & Energy',
    'A': 'Science & Diagnostics',
    'W+E': 'Spacecraft & Hulls',
    'W+F': 'Propulsion & Navigation',
    'W+A': 'Logistics & Provisioning',
    'E+F': 'Computing & Communications',
    'E+A': 'Robotics & Automation',
    'F+A': 'Defence & Rescue',
  });
  // Design priors for galactic demand, independent of the number of markets.
  const T2_SECTOR_WEIGHTS = Object.freeze(Array(10).fill(1));
  // Procurement baskets have equal access to every other sector; no hub
  // industry receives extra demand merely from having more neighbors.
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
    [0, "Power Busbar", "W,E,F", 1, "Components", "Good", true],
    [0, "Grid Charge Collector", "F,W+E", 1, "Components", "Good", true],
    [0, "Battery Array", "W,E,F,A", 1, "Assemblies", "Good", true],
    [0, "Power Converter", "W,F,E+F", 1, "Assemblies", "Good", true],
    [0, "Heat Exchanger", "F,A,E+A", 1, "Assemblies", "Good", true],
    [0, "Capacitor Bank", "W,F,F+A", 1, "Assemblies", "Good", true],
    [0, "Solar Tile", "E,F,W+E", 1, "Assemblies", "Good", true],
    [0, "Radiator Panel", "F,A,W+F", 1, "Assemblies", "Good", true],
    [0, "Fusion Reactor Core", "W,E,F,W+E", 1, "Systems", "Good", true],
    [0, "Antimatter Containment Chamber", "W,F,A,W+F", 1, "Systems", "Good", true],
    [0, "Orbital Solar Collector", "E,F,A,W+A", 1, "Systems", "Good", true],
    [0, "Deep Space Power Plant", "W,E,F,E+F", 1, "Systems", "Good", true],
    [0, "Station Battery Vault", "W,F,A,E+A", 1, "Systems", "Good", true],
    [0, "High Flux Reactor", "E,F,A,F+A", 1, "Systems", "Good", true],
    [0, "Field Generator Pod", "F,W+A,F+A", 1, "Systems", "Good", true],
    [0, "Thermal Recovery Array", "F,E+F,F+A", 1, "Systems", "Good", true],
    [0, "Beam Power Transmitter", "F,E+A,F+A", 1, "Systems", "Good", true],
    [0, "Beam Power Receiver", "F,W+E,W+F", 1, "Systems", "Good", true],
    [0, "Stellar Flux Collector", "F,W+A,E+F", 1, "Systems", "Good", true],
    [0, "Isotope Generator", "F,E+A,F+A", 1, "Systems", "Good", true],
    [1, "Thruster Nozzle", "W,W+F", 1, "Components", "Good", true],
    [1, "Propellant Cartridge", "E,W+F", 1, "Consumables", "Good", true],
    [1, "Maneuvering Thruster", "W,E,W+F", 1, "Assemblies", "Good", true],
    [1, "Ion Accelerator", "E,F,W+F", 1, "Assemblies", "Good", true],
    [1, "Plasma Injector", "E,A,W+F", 1, "Assemblies", "Good", true],
    [1, "Fuel Metering Valve", "W+E,W+F", 1, "Assemblies", "Good", true],
    [1, "Navigation Gyroscope", "W+F,W+A", 1, "Assemblies", "Good", true],
    [1, "Inertial Reference Unit", "W+F,E+F", 1, "Assemblies", "Good", true],
    [1, "Ion Drive Assembly", "W,E,A,W+F", 1, "Systems", "Good", true],
    [1, "Plasma Drive Assembly", "E,F,A,W+F", 1, "Systems", "Good", true],
    [1, "Fusion Torch Engine", "W,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Antimatter Drive Chamber", "E,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Solar Sail Rig", "F,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Magnetic Sail Rig", "A,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Gravity Assist Navigation Rack", "W,W+F,F+A", 1, "Systems", "Good", true],
    [1, "Deep Space Guidance Array", "E,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Orbital Transfer Engine", "F,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Landing Engine Cluster", "A,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Launch Booster Module", "W,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Asteroid Tug Drive", "E,W+F,F+A", 1, "Systems", "Good", true],
    [2, "Hull Plate", "F,W+E", 1, "Components", "Good", true],
    [2, "Frame Spar", "A,W+E", 1, "Components", "Good", true],
    [2, "Bulkhead Panel", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Pressure Hatch", "F,A,W+E", 1, "Assemblies", "Good", true],
    [2, "Docking Collar", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Window Shield", "W+E,W+F", 1, "Assemblies", "Good", true],
    [2, "Landing Strut", "W+E,E+A", 1, "Assemblies", "Good", true],
    [2, "Cargo Bay Door", "W+E,F+A", 1, "Assemblies", "Good", true],
    [2, "Orbital Platform Frame", "W,E,F,W+E", 1, "Systems", "Good", true],
    [2, "Reconnaissance Ship Hull", "W,E,A,W+E", 1, "Systems", "Good", true],
    [2, "Freighter Hull", "F,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Survey Ship Hull", "A,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Mining Barge Hull", "W,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Orbital Tug Hull", "E,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Patrol Cruiser Hull", "F,W+E,E+F", 1, "Systems", "Good", true],
    [2, "Launch Vehicle Body", "A,W+E,E+A", 1, "Systems", "Good", true],
    [2, "Reentry Capsule Shell", "W,W+E,F+A", 1, "Systems", "Good", true],
    [2, "Station Spine", "E,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Docking Hub Structure", "F,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Shipyard Gantry", "A,W+E,E+F", 1, "Systems", "Good", true],
    [3, "Habitat Tile", "W,F,A", 1, "Components", "Good", true],
    [3, "Habitat Anchor Bolt", "W,W+F", 1, "Components", "Good", true],
    [3, "Pressure Wall", "W,E,F,A", 1, "Assemblies", "Good", true],
    [3, "Airlock Door", "W,F,W+A", 1, "Assemblies", "Good", true],
    [3, "Habitat Floor Deck", "W,F,E+F", 1, "Assemblies", "Good", true],
    [3, "Water Distribution Conduit", "W,E,E+A", 1, "Assemblies", "Good", true],
    [3, "Radiation Screen", "W,F,F+A", 1, "Assemblies", "Good", true],
    [3, "Light Panel", "W,A,W+E", 1, "Assemblies", "Good", true],
    [3, "Habitat Pressure Module", "W,E,F,W+E", 1, "Systems", "Good", true],
    [3, "Orbital Habitat Shell", "W,F,A,W+F", 1, "Systems", "Good", true],
    [3, "Civilian Outpost Module", "W,E,F,W+A", 1, "Systems", "Good", true],
    [3, "Rotating Habitat Hub", "W,F,A,E+F", 1, "Systems", "Good", true],
    [3, "Asteroid Settlement Anchor", "W,E,F,E+A", 1, "Systems", "Good", true],
    [3, "Deep Space Shelter", "W,F,A,F+A", 1, "Systems", "Good", true],
    [3, "Worker Quarters Module", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Food Cultivation Chamber", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Hospital Isolation Module", "W,E+A,F+A", 1, "Systems", "Good", true],
    [3, "Greenhouse Dome", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Subsurface Outpost Liner", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Orbital Elevator Anchor", "W,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Robot Joint", "W,E+A", 1, "Components", "Good", true],
    [4, "Actuator Rod", "E,E+A", 1, "Components", "Good", true],
    [4, "Robot Hand", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Tool Changer", "W,E,E+A", 1, "Assemblies", "Good", true],
    [4, "Locomotion Wheel", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Manipulator Arm", "W+E,E+A", 1, "Assemblies", "Good", true],
    [4, "Force Feedback Unit", "W+F,E+A", 1, "Assemblies", "Good", true],
    [4, "Hydraulic Actuator", "W+A,E+A", 1, "Assemblies", "Good", true],
    [4, "Assembly Robot", "E,F,A,E+A", 1, "Systems", "Good", true],
    [4, "Welding Robot", "W,E,F,E+A", 1, "Systems", "Good", true],
    [4, "Inspection Robot", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Excavation Robot", "E,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Hull Repair Robot", "F,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Cargo Handling Robot", "A,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Microassembly Robot", "W,W+F,E+A", 1, "Systems", "Good", true],
    [4, "Vacuum Work Robot", "E,W+A,E+A", 1, "Systems", "Good", true],
    [4, "Survey Walker", "F,E+F,E+A", 1, "Systems", "Good", true],
    [4, "Maintenance Crawler", "A,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Station Construction Robot", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Precision Machining Robot", "E,W+F,E+A", 1, "Systems", "Good", true],
    [5, "Circuit Trace", "F,E+F", 1, "Components", "Good", true],
    [5, "Memory Wafer", "A,E+F", 1, "Components", "Good", true],
    [5, "Logic Board", "W,E,E+F", 1, "Assemblies", "Good", true],
    [5, "Learning Terminal Memory Bank", "F,A,E+F", 1, "Assemblies", "Good", true],
    [5, "Civilian Network Transceiver", "E+F,E+A", 1, "Assemblies", "Good", true],
    [5, "Signal Amplifier", "E+F,F+A", 1, "Assemblies", "Good", true],
    [5, "Network Switch", "W+E,E+F", 1, "Assemblies", "Good", true],
    [5, "Data Buffer", "W+F,E+F", 1, "Assemblies", "Good", true],
    [5, "Core Processor Rack", "W,E,A,E+F", 1, "Systems", "Good", true],
    [5, "Navigation Compute Rack", "E,F,A,E+F", 1, "Systems", "Good", true],
    [5, "Autonomous Planning Core", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Radiation Hardened Computer", "A,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Quantum Processing Module", "W,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Settlement Compute Node", "E,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Fleet Coordination Server", "F,E+F,F+A", 1, "Systems", "Good", true],
    [5, "Orbital Communication Relay", "A,W+E,E+F", 1, "Systems", "Good", true],
    [5, "Laser Communication Terminal", "W,W+F,E+F", 1, "Systems", "Good", true],
    [5, "Deep Space Radio Array", "E,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Interplanetary Router", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Cultural Archive Vault", "A,E+F,F+A", 1, "Systems", "Good", true],
    [6, "Sensor Lens", "A,W+A", 1, "Components", "Good", true],
    [6, "Detector Film", "A,E+F", 1, "Components", "Good", true],
    [6, "Spectrometer Head", "W,E,F,A", 1, "Assemblies", "Good", true],
    [6, "Radar Antenna", "W,A,W+F", 1, "Assemblies", "Good", true],
    [6, "Lidar Emitter", "W,A,W+A", 1, "Assemblies", "Good", true],
    [6, "Thermal Diagnostic Detector", "E,A,E+F", 1, "Assemblies", "Good", true],
    [6, "Magnetic Field Sensor", "F,A,E+A", 1, "Assemblies", "Good", true],
    [6, "Seismic Sensor", "W,A,F+A", 1, "Assemblies", "Good", true],
    [6, "Astronomical Telescope", "W,F,A,W+E", 1, "Systems", "Good", true],
    [6, "Planetary Survey Probe", "W,E,A,W+F", 1, "Systems", "Good", true],
    [6, "Asteroid Mapping Probe", "W,F,A,W+A", 1, "Systems", "Good", true],
    [6, "Deep Space Scout Probe", "W,E,A,E+F", 1, "Systems", "Good", true],
    [6, "Surface Sampling Rover", "W,F,A,E+A", 1, "Systems", "Good", true],
    [6, "Subsurface Survey Package", "W,E,A,F+A", 1, "Systems", "Good", true],
    [6, "Orbital Imaging Array", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Cosmic Ray Observatory", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Solar Observation Platform", "A,E+A,F+A", 1, "Systems", "Good", true],
    [6, "Radio Astronomy Array", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Medical Imaging Scanner", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Exoplanet Imaging Instrument", "A,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Drill Tooth", "E,E+A", 1, "Components", "Good", true],
    [7, "Abrasive Grain Pack", "E,F+A", 1, "Consumables", "Good", true],
    [7, "Drill Head", "E,A,W+E", 1, "Assemblies", "Good", true],
    [7, "Crushing Jaw", "E,F,W+F", 1, "Assemblies", "Good", true],
    [7, "Grinding Wheel", "E,A,W+A", 1, "Assemblies", "Good", true],
    [7, "Smelting Crucible", "W,E,E+F", 1, "Assemblies", "Good", true],
    [7, "Casting Mold", "E,F,E+A", 1, "Assemblies", "Good", true],
    [7, "Welding Electrode Bank", "E,A,F+A", 1, "Assemblies", "Good", true],
    [7, "Vacuum Furnace Liner", "E,F,A,W+E", 1, "Systems", "Good", true],
    [7, "Asteroid Drill Rig", "W,E,A,W+F", 1, "Systems", "Good", true],
    [7, "Regolith Excavator", "E,F,A,W+A", 1, "Systems", "Good", true],
    [7, "Ore Crushing Plant", "W,E,A,E+F", 1, "Systems", "Good", true],
    [7, "Magnetic Separation Plant", "E,F,A,E+A", 1, "Systems", "Good", true],
    [7, "Electrochemical Refinery", "W,E,F,F+A", 1, "Systems", "Good", true],
    [7, "Plasma Smelter", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Vacuum Casting Plant", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Precision Milling Center", "E,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Additive Fabrication Unit", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Heavy Extrusion Press", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Crystal Growth Chamber", "E,E+A,F+A", 1, "Systems", "Good", true],
    [8, "Cargo Strap", "W,W+A", 1, "Components", "Good", true],
    [8, "Container Seal", "E,W+A", 1, "Components", "Good", true],
    [8, "Nutrient Cargo Canister", "W,E,W+A", 1, "Assemblies", "Good", true],
    [8, "Provisioning Storage Rack", "F,A,W+A", 1, "Assemblies", "Good", true],
    [8, "Transfer Coupler", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Conveyor Segment", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Docking Clamp", "W+A,E+A", 1, "Assemblies", "Good", true],
    [8, "Pallet Chassis", "W+A,F+A", 1, "Assemblies", "Good", true],
    [8, "Cargo Pod", "W,E,F,W+A", 1, "Systems", "Good", true],
    [8, "Medical Cryogenic Vessel", "W,E,A,W+A", 1, "Systems", "Good", true],
    [8, "Pressurized Freight Container", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Hazardous Cargo Vault", "E,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Autonomous Cargo Pallet", "F,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Nutrition Reserve Silo", "A,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Vacuum Cargo Transfer Unit", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Orbital Freight Rack", "E,W+A,E+A", 1, "Systems", "Good", true],
    [8, "Ship Loading Gantry", "F,W+A,F+A", 1, "Systems", "Good", true],
    [8, "Dockside Cargo Crane", "A,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Fuel Transfer Assembly", "W,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Medical Oxygen Storage Vault", "E,W+A,E+F", 1, "Systems", "Good", true],
    [9, "Shield Mesh", "F,F+A", 1, "Components", "Good", true],
    [9, "Impact Foam", "A,F+A", 1, "Components", "Good", true],
    [9, "Debris Shield", "W,E,F+A", 1, "Assemblies", "Good", true],
    [9, "Radiation Shield", "F,A,F+A", 1, "Assemblies", "Good", true],
    [9, "Pressure Barrier", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Fire Isolation Panel", "W+E,F+A", 1, "Assemblies", "Good", true],
    [9, "Emergency Beacon", "W+F,F+A", 1, "Assemblies", "Good", true],
    [9, "Surge Protector", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Containment Valve", "W,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Rescue Tether Reel", "E,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Electromagnetic Shield Array", "F,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Radiation Shelter Core", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Hull Breach Containment Pack", "W,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Fire Suppression Module", "E,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Defence Interceptor Drone", "F,W+F,F+A", 1, "Systems", "Good", true],
    [9, "Collision Avoidance Array", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Emergency Escape Pod", "W,E+F,F+A", 1, "Systems", "Good", true],
    [9, "Automated Rescue Craft", "E,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Early Warning Sensor Grid", "F,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Solar Storm Protection Array", "A,W+F,F+A", 1, "Systems", "Good", true],
    [3, "Reserved Habitats 001", "W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Habitats 002", "W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Habitats 003", "W,W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Habitats 004", "W,W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 005", "W,W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 006", "W,W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 007", "W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 008", "W,W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 009", "W,W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 010", "W,W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 011", "W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 012", "W,W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 013", "W,W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 014", "W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 015", "W,W,W,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 016", "W,W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 017", "W,W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 018", "W,W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 019", "W,W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 020", "W,W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 021", "W,W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 022", "W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 023", "W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 024", "W,W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 025", "W,W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 026", "W,W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 027", "W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 028", "W,W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 029", "W,W,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 030", "W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 031", "W,W,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 032", "W,W,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 033", "W,W,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 034", "W,W,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 035", "W,W,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 036", "W,W,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 037", "W,W,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 038", "W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 039", "W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 040", "W,W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 041", "W,W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 042", "W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 043", "W,W,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 044", "W,W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 045", "W,W,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 046", "W,W,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 047", "W,W,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 048", "W,W,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 049", "W,W,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 050", "W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 051", "W,W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 052", "W,W,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 053", "W,W,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 054", "W,W,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 055", "W,W,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 056", "W,W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 057", "W,W,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 058", "W,W,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 059", "W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 060", "W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 061", "W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 062", "W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 063", "W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 064", "W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 065", "W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 066", "W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 067", "W,E,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Habitats 068", "W,E,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 069", "W,E,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 070", "W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 071", "W,E,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 072", "W,E,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 073", "W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 074", "W,E,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 075", "W,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 076", "W,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 077", "W,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 078", "W,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 079", "W,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 080", "W,E,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 081", "W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 082", "W,E,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 083", "W,E,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 084", "W,E,F,A,A", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 085", "W,E,F,W+F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 086", "W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 087", "W,E,A,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 088", "W,E,A,A,A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 089", "W,E,A,E+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 090", "W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 091", "W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 092", "W,F,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Habitats 093", "W,F,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 094", "W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 095", "W,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 096", "W,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 097", "W,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 098", "W,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 099", "W,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 100", "W,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 101", "W,F,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 102", "W,F,A,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 103", "W,F,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 104", "W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 105", "W,F,W+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 106", "W,F,E+A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 107", "W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 108", "W,A,A,A", 1, "Components", "Good", false],
    [3, "Reserved Habitats 109", "W,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 110", "W,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 111", "W,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 112", "W,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 113", "W,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 114", "W,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 115", "W,A,A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 116", "W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 117", "W,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 118", "W,W+E", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 119", "W,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 120", "W,W+E,W+A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 121", "W,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 122", "W,W+F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 123", "W,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Logistics 124", "W,W+A,E+A", 1, "Components", "Good", false],
    [8, "Reserved Logistics 125", "W,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 126", "W,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 127", "W,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 128", "W,E+F,E+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 129", "W,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 130", "W,F+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 131", "W,F+A,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 132", "E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Mining 133", "E,E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Mining 134", "E,E,E,E,E", 1, "Components", "Good", false],
    [7, "Reserved Mining 135", "E,E,E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 136", "E,E,E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 137", "E,E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 138", "E,E,E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 139", "E,E,E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 140", "E,E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 141", "E,E,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 142", "E,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 143", "E,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 144", "E,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 145", "E,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 146", "E,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 147", "E,E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 148", "E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 149", "E,E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 150", "E,E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 151", "E,E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 152", "E,E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 153", "E,E,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 154", "E,E,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 155", "E,E,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 156", "E,E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 157", "E,E,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 158", "E,E,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 159", "E,E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 160", "E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 161", "E,E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 162", "E,E,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 163", "E,E,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 164", "E,E,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 165", "E,E,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 166", "E,E,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 167", "E,E,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 168", "E,E,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 169", "E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 170", "E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 171", "E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 172", "E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 173", "E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 174", "E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 175", "E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 176", "E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 177", "E,F,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Mining 178", "E,F,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 179", "E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 180", "E,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 181", "E,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 182", "E,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 183", "E,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 184", "E,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 185", "E,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 186", "E,F,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 187", "E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 188", "E,F,A,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 189", "E,F,A,A,A", 1, "Components", "Good", false],
    [8, "Reserved Logistics 190", "E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 191", "E,F,E+F", 1, "Components", "Good", false],
    [9, "Reserved Defence 192", "E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Mining 193", "E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 194", "E,A,A,A", 1, "Components", "Good", false],
    [7, "Reserved Mining 195", "E,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 196", "E,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 197", "E,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 198", "E,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 199", "E,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 200", "E,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 201", "E,A,A,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 202", "E,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 203", "E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 204", "E,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Spacecraft 205", "E,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 206", "E,W+F,W+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 207", "E,W+F,E+F", 1, "Components", "Good", false],
    [8, "Reserved Logistics 208", "E,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Logistics 209", "E,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 210", "E,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 211", "E,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 212", "E,E+F,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 213", "E,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defence 214", "E,F+A,F+A", 1, "Components", "Good", false],
    [0, "Reserved Power 215", "F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 216", "F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 217", "F,F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 218", "F,F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Power 219", "F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Power 220", "F,F,F,A,A", 1, "Components", "Good", false],
  ];

  // ---- build the catalogue from the recipe list ----
  const EQUIPMENT_CLASS = Object.freeze({ 3: 'Component Fabricator', 4: 'Assembly Fabricator', 5: 'Systems Fabricator' });
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
