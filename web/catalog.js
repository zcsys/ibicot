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
  // Authored refinery roster (Star Business naming catalog §5): compact
  // American corporate identities, in material order. The generic company
  // bases for numbered firms live in the Star Business catalog §9.
  const T1_COMPANY_NAMES = Object.freeze([
    'Clearwater Process Supply', 'Red Mesa Metals', 'High Current Materials', 'Open Range Gas Products',
    'Hardline Industrial Ceramics', 'Heatway Process Materials', 'Crossweave Fiber Products',
    'Sunridge Electronic Materials', 'Ridgeback Composite Products', 'Navarro Process Chemicals',
  ]);
  // Ten refined materials (Star Business naming catalog §3). ``code`` is the
  // legacy recipe key retained as an internal compatibility key; ``symbol`` is
  // the new market symbol shown on recipes and market cards.
  const PRODUCTS = Object.freeze([
    { code: 'W', symbol: 'IF', name: 'Industrial Fluid', inputs: { Water: 1 } },
    { code: 'E', symbol: 'BA', name: 'Bulk Alloy', inputs: { Earth: 1 } },
    { code: 'F', symbol: 'EC', name: 'Energy Carrier', inputs: { Fire: 1 } },
    { code: 'A', symbol: 'PG', name: 'Process Gas', inputs: { Air: 1 } },
    { code: 'W+E', symbol: 'CS', name: 'Ceramic Stock', inputs: { Water: 1, Earth: 1 } },
    { code: 'W+F', symbol: 'TC', name: 'Thermal Compound', inputs: { Water: 1, Fire: 1 } },
    { code: 'W+A', symbol: 'TF', name: 'Technical Fiber', inputs: { Water: 1, Air: 1 } },
    { code: 'E+F', symbol: 'SC', name: 'Semiconductor Crystal', inputs: { Earth: 1, Fire: 1 } },
    { code: 'E+A', symbol: 'PC', name: 'Polymer Composite', inputs: { Earth: 1, Air: 1 } },
    { code: 'F+A', symbol: 'AR', name: 'Active Reagent', inputs: { Fire: 1, Air: 1 } },
  ].map((p, index) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, companyName: T1_COMPANY_NAMES[index], inputs: Object.freeze(p.inputs), complexity,
      role: 'intermediate-only',
      consumerValue: complexity === 1 ? 1.875 : 3.75, equipmentPrice: T1_BASIC_MACHINERY });
  }));

  const WORLD_STORY = Object.freeze({ name: 'Star Business',
    tagline: 'Build the Colony. Supply the Fleet.', population: 1000000,
    producers: 'Autonomous refineries and manufacturers building a colony into a supply base',
    consumers: 'One million consumers buying, switching suppliers, and keeping the colony running',
    player: 'Human investor', entry: 'An initial investment in a refinery or manufacturing business',
    competitors: Object.freeze(['Opportunist human investors', 'Robotic executive agents']),
    alphaPlayableTiers: Object.freeze(['T1']),
    purpose: 'Building a manufacturing colony into the supply base for a coming galactic war',
    demandScope: 'Housing, medical equipment, gardens, archives, rescue vehicles, and everyday trade',
    society: 'Humans and robots in a manufacturing colony in 4259',
    roboticGeneration: 'The colony economy that must keep working before the fighting starts',
    conflict: 'A coming galactic war' });

  // Ten manufacturing sectors (Star Business naming catalog §6): industry
  // names identify the market, not the prestige of its largest producer.
  const T2_SECTOR_DEFINITIONS = Object.freeze([
    Object.freeze({"name":"Power & Utilities","description":"Power distribution, generation, storage, and thermal management."}),
    Object.freeze({"name":"Propulsion & Flight Systems","description":"Propulsion hardware, flight controls, and navigation equipment."}),
    Object.freeze({"name":"Shipbuilding & Orbital Structures","description":"Ship hulls, docking structures, and orbital construction components."}),
    Object.freeze({"name":"Housing & Life Support","description":"Pressurized housing, settlement structures, and essential living infrastructure."}),
    Object.freeze({"name":"Robotics & Field Services","description":"Service robots, repair platforms, and replaceable robotic components."}),
    Object.freeze({"name":"Computing & Communications","description":"Computing hardware, network equipment, and communication systems."}),
    Object.freeze({"name":"Sensors & Medical Equipment","description":"Survey sensors, scientific instruments, and medical diagnostic equipment."}),
    Object.freeze({"name":"Industrial Tooling & Mining Supplies","description":"Cutting tools, wear parts, passive fixtures, and mining attachments."}),
    Object.freeze({"name":"Freight & Warehouse Equipment","description":"Cargo handling, shipping containers, storage hardware, and supply transport equipment."}),
    Object.freeze({"name":"Defense & Emergency Systems","description":"Defensive equipment, emergency containment, evacuation, and rescue systems."}),
  ]);
  const T2_SECTORS = Object.freeze(T2_SECTOR_DEFINITIONS.map(sector => sector.name));
  // Authored manufacturing roster (Star Business naming catalog §6): authored
  // identities per sector. They are cohort labels, not mandatory parents.
  const T2_SECTOR_MANUFACTURERS = Object.freeze([
    Object.freeze({"sector":"Power & Utilities","company":"Switchyard Power Systems"}),
    Object.freeze({"sector":"Propulsion & Flight Systems","company":"Burnline Aerospace"}),
    Object.freeze({"sector":"Shipbuilding & Orbital Structures","company":"Rivet Point Shipbuilding"}),
    Object.freeze({"sector":"Housing & Life Support","company":"Homefront Habitat Systems"}),
    Object.freeze({"sector":"Robotics & Field Services","company":"Workhorse Service Robotics"}),
    Object.freeze({"sector":"Computing & Communications","company":"Copperline Electronics"}),
    Object.freeze({"sector":"Sensors & Medical Equipment","company":"Benchmark Instrument Corporation"}),
    Object.freeze({"sector":"Industrial Tooling & Mining Supplies","company":"Redridge Tool & Supply"}),
    Object.freeze({"sector":"Freight & Warehouse Equipment","company":"Crossdock Cargo Systems"}),
    Object.freeze({"sector":"Defense & Emergency Systems","company":"Hardstop Defense Systems"}),
  ]);
  const T2_MANUFACTURER_BY_SECTOR = Object.freeze(Object.fromEntries(
    T2_SECTOR_MANUFACTURERS.map(m => [m.sector, m.company])));
  // Tier 1 material -> manufacturing sector (Star Business 1:1 mapping; mirrors core/model.py).
  const T1_SECTOR_BY_CODE = Object.freeze({
    'W': 'Housing & Life Support',
    'E': 'Industrial Tooling & Mining Supplies',
    'F': 'Power & Utilities',
    'A': 'Sensors & Medical Equipment',
    'W+E': 'Shipbuilding & Orbital Structures',
    'W+F': 'Propulsion & Flight Systems',
    'W+A': 'Freight & Warehouse Equipment',
    'E+F': 'Computing & Communications',
    'E+A': 'Robotics & Field Services',
    'F+A': 'Defense & Emergency Systems',
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
    t0Equity: 75000000, t0License: 22000000, t0Machinery: 12250000, t0Reserve: 1000000,
    t0Capacity: 200000, t0Storage: 500000,
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
    wholesalePriceResponse: .05, marketAnchorBand: .02, priceObservationTicks: 30,
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
    [0, "Main Feeder Bar", "W,E,F", 1, "Components", "Good", true],
    [0, "Grid Intake Module", "F,W+E", 1, "Components", "Good", true],
    [0, "Backup Battery Rack", "W,E,F,A", 1, "Assemblies", "Good", true],
    [0, "Voltage Converter", "W,F,E+F", 1, "Assemblies", "Good", true],
    [0, "Coolant Exchange Block", "F,A,E+A", 1, "Assemblies", "Good", true],
    [0, "Pulse Capacitor Rack", "W,F,F+A", 1, "Assemblies", "Good", true],
    [0, "Solar Roof Panel", "E,F,W+E", 1, "Assemblies", "Good", true],
    [0, "Radiator Wing", "F,A,W+F", 1, "Assemblies", "Good", true],
    [0, "Station Reactor Package", "W,E,F,W+E", 1, "Systems", "Good", true],
    [0, "High-Energy Storage Vessel", "W,F,A,W+F", 1, "Systems", "Good", true],
    [0, "Orbital Solar Farm", "E,F,A,W+A", 1, "Systems", "Good", true],
    [0, "Remote Power Station", "W,E,F,E+F", 1, "Systems", "Good", true],
    [0, "Emergency Battery Room", "W,F,A,E+A", 1, "Systems", "Good", true],
    [0, "Peak Power Reactor", "E,F,A,F+A", 1, "Systems", "Good", true],
    [0, "Field Power Module", "F,W+A,F+A", 1, "Systems", "Good", true],
    [0, "Waste Heat Generator", "F,E+F,F+A", 1, "Systems", "Good", true],
    [0, "Wireless Power Transmitter", "F,E+A,F+A", 1, "Systems", "Good", true],
    [0, "Wireless Power Receiver", "F,W+E,W+F", 1, "Systems", "Good", true],
    [0, "Stellar Collection Array", "F,W+A,E+F", 1, "Systems", "Good", true],
    [0, "Long-Life Generator", "F,E+A,F+A", 1, "Systems", "Good", true],
    [1, "Engine Nozzle Insert", "W,W+F", 1, "Components", "Good", true],
    [1, "Propellant Feed Cartridge", "E,W+F", 1, "Consumables", "Good", true],
    [1, "Attitude Thruster Pack", "W,E,W+F", 1, "Assemblies", "Good", true],
    [1, "Ion Acceleration Grid", "E,F,W+F", 1, "Assemblies", "Good", true],
    [1, "Plasma Feed Injector", "E,A,W+F", 1, "Assemblies", "Good", true],
    [1, "Propellant Control Valve", "W+E,W+F", 1, "Assemblies", "Good", true],
    [1, "Flight Reference Gyro", "W+F,W+A", 1, "Assemblies", "Good", true],
    [1, "Inertial Guidance Module", "W+F,E+F", 1, "Assemblies", "Good", true],
    [1, "Ion Cruise Engine", "W,E,A,W+F", 1, "Systems", "Good", true],
    [1, "Plasma Transfer Engine", "E,F,A,W+F", 1, "Systems", "Good", true],
    [1, "Fusion Main Engine", "W,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Pulse Propulsion Chamber", "E,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Light Sail Assembly", "F,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Magnetic Sail Assembly", "A,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Gravity Assist Computer", "W,W+F,F+A", 1, "Systems", "Good", true],
    [1, "Deep Space Flight Controller", "E,W+E,W+F", 1, "Systems", "Good", true],
    [1, "Orbital Maneuvering Engine", "F,W+F,W+A", 1, "Systems", "Good", true],
    [1, "Descent Engine Package", "A,W+F,E+F", 1, "Systems", "Good", true],
    [1, "Launch Assist Booster", "W,W+F,E+A", 1, "Systems", "Good", true],
    [1, "Heavy Tow Engine", "E,W+F,F+A", 1, "Systems", "Good", true],
    [2, "Hull Skin Panel", "F,W+E", 1, "Components", "Good", true],
    [2, "Primary Frame Beam", "A,W+E", 1, "Components", "Good", true],
    [2, "Pressure Bulkhead", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Crew Access Hatch", "F,A,W+E", 1, "Assemblies", "Good", true],
    [2, "Docking Adapter Ring", "W,E,W+E", 1, "Assemblies", "Good", true],
    [2, "Viewport Armor Cover", "W+E,W+F", 1, "Assemblies", "Good", true],
    [2, "Landing Gear Assembly", "W+E,E+A", 1, "Assemblies", "Good", true],
    [2, "Cargo Ramp Assembly", "W+E,F+A", 1, "Assemblies", "Good", true],
    [2, "Orbital Construction Frame", "W,E,F,W+E", 1, "Systems", "Good", true],
    [2, "Scout Vessel Frame", "W,E,A,W+E", 1, "Systems", "Good", true],
    [2, "Heavy Freight Hull", "F,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Survey Vessel Chassis", "A,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Mining Tender Hull", "W,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Dock Tug Chassis", "E,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Escort Ship Hull", "F,W+E,E+F", 1, "Systems", "Good", true],
    [2, "Launch Stage Body", "A,W+E,E+A", 1, "Systems", "Good", true],
    [2, "Crew Capsule Shell", "W,W+E,F+A", 1, "Systems", "Good", true],
    [2, "Station Center Truss", "E,W+E,W+F", 1, "Systems", "Good", true],
    [2, "Multiport Dock Frame", "F,W+E,W+A", 1, "Systems", "Good", true],
    [2, "Shipyard Support Frame", "A,W+E,E+F", 1, "Systems", "Good", true],
    [3, "Interior Wall Panel", "W,F,A", 1, "Components", "Good", true],
    [3, "Foundation Anchor Kit", "W,W+F", 1, "Components", "Good", true],
    [3, "Pressure Wall Section", "W,E,F,A", 1, "Assemblies", "Good", true],
    [3, "Personnel Airlock Gate", "W,F,W+A", 1, "Assemblies", "Good", true],
    [3, "Utility Floor Panel", "W,F,E+F", 1, "Assemblies", "Good", true],
    [3, "Freshwater Pipe Section", "W,E,E+A", 1, "Assemblies", "Good", true],
    [3, "Radiation Barrier Sheet", "W,F,F+A", 1, "Assemblies", "Good", true],
    [3, "Daylight Ceiling Panel", "W,A,W+E", 1, "Assemblies", "Good", true],
    [3, "Residential Pressure Module", "W,E,F,W+E", 1, "Systems", "Good", true],
    [3, "Orbital Housing Shell", "W,F,A,W+F", 1, "Systems", "Good", true],
    [3, "Frontier Community Center", "W,E,F,W+A", 1, "Systems", "Good", true],
    [3, "Rotating Habitat Bearing Hub", "W,F,A,E+F", 1, "Systems", "Good", true],
    [3, "Asteroid Foundation Kit", "W,E,F,E+A", 1, "Systems", "Good", true],
    [3, "Remote Shelter Module", "W,F,A,F+A", 1, "Systems", "Good", true],
    [3, "Mixed-Crew Housing Unit", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Grow Room Enclosure", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Medical Isolation Suite", "W,E+A,F+A", 1, "Systems", "Good", true],
    [3, "Garden Dome Shell", "W,W+E,W+F", 1, "Systems", "Good", true],
    [3, "Underground Habitat Liner", "W,W+A,E+F", 1, "Systems", "Good", true],
    [3, "Orbital Tether Foundation", "W,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Servo Joint Module", "W,E+A", 1, "Components", "Good", true],
    [4, "Actuator Link", "E,E+A", 1, "Components", "Good", true],
    [4, "Utility Gripper", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Quick-Change Wrist Coupler", "W,E,E+A", 1, "Assemblies", "Good", true],
    [4, "All-Terrain Drive Wheel", "F,A,E+A", 1, "Assemblies", "Good", true],
    [4, "Service Arm Assembly", "W+E,E+A", 1, "Assemblies", "Good", true],
    [4, "Grip Pressure Sensor", "W+F,E+A", 1, "Assemblies", "Good", true],
    [4, "Fluid Actuator Pack", "W+A,E+A", 1, "Assemblies", "Good", true],
    [4, "Facility Service Robot", "E,F,A,E+A", 1, "Systems", "Good", true],
    [4, "Hull Cleaning Robot", "W,E,F,E+A", 1, "Systems", "Good", true],
    [4, "Equipment Inspection Rover", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Mine Safety Scout", "E,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Hull Patch Robot", "F,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Cargo Handling Rover", "A,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Medical Handling Robot", "W,W+F,E+A", 1, "Systems", "Good", true],
    [4, "Vacuum Service Robot", "E,W+A,E+A", 1, "Systems", "Good", true],
    [4, "Site Survey Rover", "F,E+F,E+A", 1, "Systems", "Good", true],
    [4, "Utility Inspection Crawler", "A,E+A,F+A", 1, "Systems", "Good", true],
    [4, "Building Maintenance Robot", "W,W+E,E+A", 1, "Systems", "Good", true],
    [4, "Salvage Handling Robot", "E,W+F,E+A", 1, "Systems", "Good", true],
    [5, "Circuit Interconnect Strip", "F,E+F", 1, "Components", "Good", true],
    [5, "Solid-State Memory Tile", "A,E+F", 1, "Components", "Good", true],
    [5, "Equipment Control Board", "W,E,E+F", 1, "Assemblies", "Good", true],
    [5, "Learning Memory Module", "F,A,E+F", 1, "Assemblies", "Good", true],
    [5, "Local Network Radio", "E+F,E+A", 1, "Assemblies", "Good", true],
    [5, "Signal Booster Card", "E+F,F+A", 1, "Assemblies", "Good", true],
    [5, "Industrial Network Switch", "W+E,E+F", 1, "Assemblies", "Good", true],
    [5, "Packet Buffer Module", "W+F,E+F", 1, "Assemblies", "Good", true],
    [5, "General Computing Rack", "W,E,A,E+F", 1, "Systems", "Good", true],
    [5, "Flight Computing Rack", "E,F,A,E+F", 1, "Systems", "Good", true],
    [5, "Autonomous Scheduling Server", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Radiation-Tolerant Computer", "A,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Quantum Compute Cartridge", "W,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Colony Edge Server", "E,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Fleet Operations Server", "F,E+F,F+A", 1, "Systems", "Good", true],
    [5, "Orbital Relay Station", "A,W+E,E+F", 1, "Systems", "Good", true],
    [5, "Laser Data Terminal", "W,W+F,E+F", 1, "Systems", "Good", true],
    [5, "Deep Space Radio Station", "E,W+A,E+F", 1, "Systems", "Good", true],
    [5, "Interplanetary Network Gateway", "F,E+F,E+A", 1, "Systems", "Good", true],
    [5, "Long-Term Archive Server", "A,E+F,F+A", 1, "Systems", "Good", true],
    [6, "Optical Sensor Element", "A,W+A", 1, "Components", "Good", true],
    [6, "Radiation Detector Sheet", "A,E+F", 1, "Components", "Good", true],
    [6, "Material Analysis Head", "W,E,F,A", 1, "Assemblies", "Good", true],
    [6, "Tracking Radar Dish", "W,A,W+F", 1, "Assemblies", "Good", true],
    [6, "Laser Mapping Head", "W,A,W+A", 1, "Assemblies", "Good", true],
    [6, "Thermal Inspection Camera", "E,A,E+F", 1, "Assemblies", "Good", true],
    [6, "Magnetic Survey Sensor", "F,A,E+A", 1, "Assemblies", "Good", true],
    [6, "Seismic Monitoring Unit", "W,A,F+A", 1, "Assemblies", "Good", true],
    [6, "Deep Space Telescope", "W,F,A,W+E", 1, "Systems", "Good", true],
    [6, "Planetary Mapping Satellite", "W,E,A,W+F", 1, "Systems", "Good", true],
    [6, "Asteroid Survey Drone", "W,F,A,W+A", 1, "Systems", "Good", true],
    [6, "Long-Range Recon Probe", "W,E,A,E+F", 1, "Systems", "Good", true],
    [6, "Sample Collection Rover", "W,F,A,E+A", 1, "Systems", "Good", true],
    [6, "Subsurface Survey Kit", "W,E,A,F+A", 1, "Systems", "Good", true],
    [6, "Orbital Mapping Imager", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Particle Monitoring Station", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Solar Activity Monitor", "A,E+A,F+A", 1, "Systems", "Good", true],
    [6, "Radio Observation Array", "A,W+E,W+F", 1, "Systems", "Good", true],
    [6, "Medical Imaging Bed", "A,W+A,E+F", 1, "Systems", "Good", true],
    [6, "Planet Detection Instrument", "A,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Replaceable Cutting Tooth", "E,E+A", 1, "Components", "Good", true],
    [7, "Precision Abrasive Pack", "E,F+A", 1, "Consumables", "Good", true],
    [7, "Rock Drill Crown", "E,A,W+E", 1, "Assemblies", "Good", true],
    [7, "Crusher Jaw Insert", "E,F,W+F", 1, "Assemblies", "Good", true],
    [7, "Surface Finishing Disc", "E,A,W+A", 1, "Assemblies", "Good", true],
    [7, "Crucible Liner", "W,E,E+F", 1, "Assemblies", "Good", true],
    [7, "Casting Die Set", "E,F,E+A", 1, "Assemblies", "Good", true],
    [7, "Welding Contact Kit", "E,A,F+A", 1, "Assemblies", "Good", true],
    [7, "Furnace Refractory Kit", "E,F,A,W+E", 1, "Systems", "Good", true],
    [7, "Drill Alignment Frame", "W,E,A,W+F", 1, "Systems", "Good", true],
    [7, "Excavator Bucket Assembly", "E,F,A,W+A", 1, "Systems", "Good", true],
    [7, "Crusher Rebuild Kit", "W,E,A,E+F", 1, "Systems", "Good", true],
    [7, "Separator Drum Liner", "E,F,A,E+A", 1, "Systems", "Good", true],
    [7, "Refining Tank Liner", "W,E,F,F+A", 1, "Systems", "Good", true],
    [7, "Smelter Wear Kit", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Casting Fixture Rack", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Precision Workholding Table", "E,E+A,F+A", 1, "Systems", "Good", true],
    [7, "Additive Build Plate", "E,W+E,W+F", 1, "Systems", "Good", true],
    [7, "Extrusion Tooling Set", "E,W+A,E+F", 1, "Systems", "Good", true],
    [7, "Crystal Growth Fixture", "E,E+A,F+A", 1, "Systems", "Good", true],
    [8, "Cargo Tie-Down", "W,W+A", 1, "Components", "Good", true],
    [8, "Tamper-Evident Cargo Seal", "E,W+A", 1, "Components", "Good", true],
    [8, "Food-Grade Shipping Drum", "W,E,W+A", 1, "Assemblies", "Good", true],
    [8, "Warehouse Storage Rack", "F,A,W+A", 1, "Assemblies", "Good", true],
    [8, "Cargo Transfer Adapter", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Gravity Conveyor Section", "W+A,E+F", 1, "Assemblies", "Good", true],
    [8, "Container Lock Assembly", "W+A,E+A", 1, "Assemblies", "Good", true],
    [8, "Heavy-Duty Shipping Pallet", "W+A,F+A", 1, "Assemblies", "Good", true],
    [8, "Orbital Shipping Container", "W,E,F,W+A", 1, "Systems", "Good", true],
    [8, "Medical Cold-Chain Container", "W,E,A,W+A", 1, "Systems", "Good", true],
    [8, "Pressurized Cargo Box", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Hazardous Materials Container", "E,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Self-Driving Cargo Cart", "F,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Bulk Food Storage Bin", "A,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Cargo Transfer Airlock", "W,W+A,E+F", 1, "Systems", "Good", true],
    [8, "Orbital Container Rack", "E,W+A,E+A", 1, "Systems", "Good", true],
    [8, "Ship Loading Platform", "F,W+A,F+A", 1, "Systems", "Good", true],
    [8, "Spaceport Cargo Crane", "A,W+E,W+A", 1, "Systems", "Good", true],
    [8, "Propellant Transfer Station", "W,W+F,W+A", 1, "Systems", "Good", true],
    [8, "Medical Gas Storage Tank", "E,W+A,E+F", 1, "Systems", "Good", true],
    [9, "Shielding Fabric", "F,F+A", 1, "Components", "Good", true],
    [9, "Impact Absorber Block", "A,F+A", 1, "Components", "Good", true],
    [9, "Fragment Armor Panel", "W,E,F+A", 1, "Assemblies", "Good", true],
    [9, "Radiation Guard Panel", "F,A,F+A", 1, "Assemblies", "Good", true],
    [9, "Emergency Pressure Curtain", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Fire Containment Door", "W+E,F+A", 1, "Assemblies", "Good", true],
    [9, "Search-and-Rescue Beacon", "W+F,F+A", 1, "Assemblies", "Good", true],
    [9, "Electrical Surge Arrestor", "W+A,F+A", 1, "Assemblies", "Good", true],
    [9, "Emergency Isolation Valve", "W,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Rescue Cable Winch", "E,F,A,F+A", 1, "Systems", "Good", true],
    [9, "Electromagnetic Defense Array", "F,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Radiation Shelter Module", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Emergency Hull Seal Kit", "W,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Automatic Fire Suppression Pack", "E,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Point Defense Drone", "F,W+F,F+A", 1, "Systems", "Good", true],
    [9, "Collision Warning System", "A,W+A,F+A", 1, "Systems", "Good", true],
    [9, "Crew Evacuation Pod", "W,E+F,F+A", 1, "Systems", "Good", true],
    [9, "Autonomous Rescue Shuttle", "E,E+A,F+A", 1, "Systems", "Good", true],
    [9, "Perimeter Warning Network", "F,W+E,F+A", 1, "Systems", "Good", true],
    [9, "Solar Radiation Protection System", "A,W+F,F+A", 1, "Systems", "Good", true],
    [3, "Reserved Housing 001", "W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Housing 002", "W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Housing 003", "W,W,W,W,W", 1, "Components", "Good", false],
    [3, "Reserved Housing 004", "W,W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 005", "W,W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 006", "W,W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 007", "W,W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 008", "W,W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 009", "W,W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 010", "W,W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 011", "W,W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 012", "W,W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 013", "W,W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 014", "W,W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 015", "W,W,W,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 016", "W,W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 017", "W,W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 018", "W,W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 019", "W,W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 020", "W,W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 021", "W,W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 022", "W,W,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 023", "W,W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 024", "W,W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 025", "W,W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 026", "W,W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 027", "W,W,E,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 028", "W,W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 029", "W,W,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 030", "W,W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 031", "W,W,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 032", "W,W,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 033", "W,W,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 034", "W,W,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 035", "W,W,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 036", "W,W,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 037", "W,W,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 038", "W,W,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 039", "W,W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 040", "W,W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 041", "W,W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 042", "W,W,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 043", "W,W,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 044", "W,W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 045", "W,W,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 046", "W,W,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 047", "W,W,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 048", "W,W,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 049", "W,W,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 050", "W,W,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 051", "W,W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 052", "W,W,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 053", "W,W,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 054", "W,W,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 055", "W,W,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 056", "W,W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 057", "W,W,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 058", "W,W,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 059", "W,W,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 060", "W,W,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 061", "W,W,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 062", "W,W,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 063", "W,W,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 064", "W,W,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 065", "W,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 066", "W,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 067", "W,E,E,E,E", 1, "Components", "Good", false],
    [3, "Reserved Housing 068", "W,E,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 069", "W,E,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 070", "W,E,E,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 071", "W,E,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 072", "W,E,E,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 073", "W,E,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 074", "W,E,E,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 075", "W,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 076", "W,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 077", "W,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 078", "W,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 079", "W,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 080", "W,E,E,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 081", "W,E,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 082", "W,E,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 083", "W,E,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 084", "W,E,F,A,A", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 085", "W,E,F,W+F", 1, "Components", "Good", false],
    [3, "Reserved Housing 086", "W,E,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 087", "W,E,A,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 088", "W,E,A,A,A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 089", "W,E,A,E+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 090", "W,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 091", "W,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 092", "W,F,F,F,F", 1, "Components", "Good", false],
    [3, "Reserved Housing 093", "W,F,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 094", "W,F,F,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 095", "W,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 096", "W,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 097", "W,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 098", "W,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 099", "W,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 100", "W,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 101", "W,F,F,F+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 102", "W,F,A,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 103", "W,F,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 104", "W,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 105", "W,F,W+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 106", "W,F,E+A", 1, "Components", "Good", false],
    [3, "Reserved Housing 107", "W,A,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 108", "W,A,A,A", 1, "Components", "Good", false],
    [3, "Reserved Housing 109", "W,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 110", "W,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 111", "W,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 112", "W,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 113", "W,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 114", "W,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 115", "W,A,A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 116", "W,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 117", "W,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 118", "W,W+E", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 119", "W,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 120", "W,W+E,W+A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 121", "W,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 122", "W,W+F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 123", "W,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 124", "W,W+A,E+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 125", "W,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 126", "W,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 127", "W,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 128", "W,E+F,E+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 129", "W,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 130", "W,F+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 131", "W,F+A,F+A", 1, "Components", "Good", false],
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
    [2, "Reserved Shipbuilding 142", "E,E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 143", "E,E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 144", "E,E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 145", "E,E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 146", "E,E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 147", "E,E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 148", "E,E,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 149", "E,E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 150", "E,E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 151", "E,E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 152", "E,E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 153", "E,E,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 154", "E,E,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 155", "E,E,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 156", "E,E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 157", "E,E,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 158", "E,E,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 159", "E,E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 160", "E,E,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 161", "E,E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 162", "E,E,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 163", "E,E,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 164", "E,E,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 165", "E,E,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 166", "E,E,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 167", "E,E,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 168", "E,E,A,F+A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 169", "E,E,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 170", "E,E,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 171", "E,E,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 172", "E,E,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 173", "E,E,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 174", "E,E,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 175", "E,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 176", "E,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 177", "E,F,F,F,F", 1, "Components", "Good", false],
    [7, "Reserved Tooling 178", "E,F,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 179", "E,F,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 180", "E,F,F,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 181", "E,F,F,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 182", "E,F,F,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 183", "E,F,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 184", "E,F,F,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 185", "E,F,F,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 186", "E,F,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 187", "E,F,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 188", "E,F,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 189", "E,F,A,A,A", 1, "Components", "Good", false],
    [8, "Reserved Freight 190", "E,F,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 191", "E,F,E+F", 1, "Components", "Good", false],
    [9, "Reserved Defense 192", "E,F,F+A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 193", "E,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 194", "E,A,A,A", 1, "Components", "Good", false],
    [7, "Reserved Tooling 195", "E,A,A,A,A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 196", "E,A,A,W+E", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 197", "E,A,A,W+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 198", "E,A,A,W+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 199", "E,A,A,E+F", 1, "Components", "Good", false],
    [4, "Reserved Robotics 200", "E,A,A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 201", "E,A,A,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 202", "E,A,E+A", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 203", "E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 204", "E,W+E,W+E", 1, "Components", "Good", false],
    [2, "Reserved Shipbuilding 205", "E,W+E,E+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 206", "E,W+F,W+F", 1, "Components", "Good", false],
    [1, "Reserved Propulsion 207", "E,W+F,E+F", 1, "Components", "Good", false],
    [8, "Reserved Freight 208", "E,W+A,W+A", 1, "Components", "Good", false],
    [8, "Reserved Freight 209", "E,W+A,F+A", 1, "Components", "Good", false],
    [5, "Reserved Computing 210", "E,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 211", "E,E+F,E+F", 1, "Components", "Good", false],
    [5, "Reserved Computing 212", "E,E+F,F+A", 1, "Components", "Good", false],
    [4, "Reserved Robotics 213", "E,E+A,E+A", 1, "Components", "Good", false],
    [9, "Reserved Defense 214", "E,F+A,F+A", 1, "Components", "Good", false],
    [0, "Reserved Power 215", "F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 216", "F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 217", "F,F,F,F,F", 1, "Components", "Good", false],
    [0, "Reserved Power 218", "F,F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Power 219", "F,F,F,A", 1, "Components", "Good", false],
    [0, "Reserved Power 220", "F,F,F,A,A", 1, "Components", "Good", false],
  ];

  // ---- build the catalog from the recipe list ----
  // Production equipment classes (Star Business naming catalog §7): bench, cell
  // and hall communicate increasing installation scale; the noun after
  // "Production" distinguishes the purchase.
  const EQUIPMENT_CLASS = Object.freeze({ 3: 'Production Bench', 4: 'Production Cell', 5: 'Production Hall' });
  const EQUIPMENT_CONFIG = Object.freeze({ 3: 'Component Production', 4: 'Assembly Production', 5: 'Systems Production' });
  // The two Water companies are the only producers of complete production and
  // refining machinery (Star Business naming catalog §4).
  const EQUIPMENT_MAKERS = Object.freeze(['Bluegate Water & Machine Co.', 'Coldwell Ice & Machine Inc.']);
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

  const T2_Catalog = Object.freeze(recipes.map((r, i) => buildT2(r, i)));
  const T2_PRODUCTS = Object.freeze(T2_Catalog.filter((p) => p.invented).map((p, i) => Object.freeze({ ...p, id: i })));
  const T2_UNINVENTED_PRODUCTS = Object.freeze(T2_Catalog.filter((p) => !p.invented));
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
    sales, stock, demand = sales, available = sales, stepScale = 1,
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
    // Adaptive derivative-following: grow on continuation, keep the step on
    // reversal (no halving). This may still quote at cost.
    const scale = clamp(stepScale * (nextDirection !== direction ? 1.0 : 1.2), 0.01, 1);
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
    T2_Catalog, T2_UNINVENTED_PRODUCTS,
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
    T2_SECTOR_MANUFACTURERS, T2_MANUFACTURER_BY_SECTOR, EQUIPMENT_MAKERS, EQUIPMENT_CONFIG,
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
