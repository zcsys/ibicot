/*
 * Canonical, editable Phase 0 model primitives.
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
  const T1_COMPOUND_MACHINERY = 75000;
  const T2_ROUTE_SETUP = 1000;
  // Per-unit quotes support fractional cents for bulk inputs. At the
  // thousand-unit wholesale minimum this precision represents one cent.
  const MIN_UNIT_PRICE = 0.00001;
  const TIER_BOUNDARIES = Object.freeze({ T1: Object.freeze([1, 2]), T2: Object.freeze([3, 4, 5]) });
  const T1_COMPANY_NAMES = Object.freeze([
    'Aster Water Systems', 'Meridian Mineral Refining', 'Helion Energy Cells', 'Cirrus Chemical Works',
    'Vanguard Ceramic Materials', 'Caldera Thermal Materials', 'Spindle Fiber Industries',
    'Lattice Semiconductor Materials', 'Truss Polymer Works', 'Catalyst Active Materials',
  ]);
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
  ].map((p, index) => {
    const complexity = Object.values(p.inputs).reduce((sum, quantity) => sum + quantity, 0);
    return Object.freeze({ ...p, companyName: T1_COMPANY_NAMES[index], inputs: Object.freeze(p.inputs), complexity,
      role: 'intermediate-only',
      consumerValue: complexity === 1 ? 1.875 : 3.75, equipmentPrice: complexity === 1 ? T1_BASIC_MACHINERY : T1_COMPOUND_MACHINERY });
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
  // Design priors for galactic demand, independent of the number of markets.
  const T2_SECTOR_WEIGHTS = Object.freeze(Array(10).fill(1));
  // Procurement baskets have equal access to every other sector; no hub
  // industry receives extra demand merely from having more neighbors.
  const T2_ADJACENCY = Object.freeze(T2_SECTORS.map((_,core) =>
    Object.freeze(T2_SECTORS.map((_,i)=>i).filter(i=>i!==core))));
  const T2_MAX_PRODUCTS_PER_FIRM = 4;
  // Bulk upstream firms and small downstream workshops serve the same population.
  // Stock coverage is measured against sales, not against idle nameplate capacity.
  const ECONOMY_DEFAULTS = Object.freeze({ capacity: 10000, targetInventory: 500000,
    maxInventory: 1000000, initialCash: 1000000, retailTargetInventory: 600,
    retailMaxInventory: 1200, retailInitialCash: 5000, basicEquipmentCapacity: 320,
    compoundEquipmentCapacity: 240, minWholesaleLot: 1000, inventoryCoverageTicks: 3,
    tier2WorkingCashTicks: 30, tier2MinimumCash: 2500, tier2MarkupPremium: .05, tier2CompanyCapacity: 6, tier2InventoryCapacity: 60, tier1InventoryCapacity: 6000,
    tier2BaseMarkup: -1, procurementBaseMarkup: .25, procurementMarkupPremium: .05,
    tier2CompoundStandardization: 0, tier2ComplexitySpecialization: 0,
    procurementCompoundStandardization: 0, procurementComplexitySpecialization: 0,
    procurementBasicReferenceCost: 1.875, procurementCompoundReferenceCost: 3.85,
    tier2ConversionCostScale: 1, procurementConversionReferenceScale: 1 });
  const t2Capacity = () => ECONOMY_DEFAULTS.tier2CompanyCapacity;
  // Player-facing ownership and progression gates. These are entry/ownership
  // costs, orthogonal to the bot economy: paying a license or founding a house
  // does not move simulated economy cash. They are reference prices for the
  // account/ownership layer, not economy parameters.
  const PROGRESSION_DEFAULTS = Object.freeze({
    startingLicenses: Object.freeze(['T1']),
    // null = not for sale (the 20 Tier 0 magnates are team-controlled).
    licenseCosts: Object.freeze({ T1: 0, T2: 10000000, T0: null }),
    houseFoundingCost: 50000000,
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
    [0, "Power Busbar", "F,F,F", 1, "Components", "Good"],
    [0, "Grid Charge Collector", "E,F,F", 1, "Components", "Good"],
    [0, "Thermal Fuse", "F,W+F", 1, "Components", "Good"],
    [0, "Reactor Coolant Cartridge", "E,F,A", 1, "Consumables", "Good"],
    [0, "Energy Cell Coupler", "W,W+F", 1, "Components", "Good"],
    [0, "Battery Array", "F,F,F,F", 0.8, "Assemblies", "Good"],
    [0, "Power Converter", "E,F,F,F", 0.8, "Assemblies", "Good"],
    [0, "Heat Exchanger", "F,F,W+F", 0.8, "Assemblies", "Good"],
    [0, "Capacitor Bank", "W,E,F,F", 0.8, "Assemblies", "Good"],
    [0, "Solar Tile", "E,F,F,A", 0.8, "Assemblies", "Good"],
    [0, "Radiator Panel", "F,F,A,A", 0.8, "Assemblies", "Good"],
    [0, "Induction Coil", "F,F,E+A", 0.8, "Assemblies", "Good"],
    [0, "Turbine Rotor", "W,F,W+F", 0.8, "Assemblies", "Good"],
    [0, "Reactor Coolant Pump", "E,F,W+F", 0.8, "Assemblies", "Good"],
    [0, "Superconducting Cable", "W+F,W+F", 0.8, "Assemblies", "Good"],
    [0, "Fuel Pellet Magazine", "W,W,F,A", 0.8, "Assemblies", "Good"],
    [0, "Power Distribution Module", "W+F,F+A", 0.8, "Assemblies", "Good"],
    [0, "Fusion Reactor Core", "F,F,F,F,F", 0.65, "Systems", "Good"],
    [0, "Antimatter Containment Chamber", "E,F,F,F,F", 0.65, "Systems", "Good"],
    [0, "Orbital Solar Collector", "F,F,F,W+F", 0.65, "Systems", "Good"],
    [0, "Deep Space Power Plant", "W,E,F,F,F", 0.65, "Systems", "Good"],
    [0, "Station Battery Vault", "E,F,F,F,A", 0.65, "Systems", "Good"],
    [0, "High Flux Reactor", "E,E,F,F,F", 0.65, "Systems", "Good"],
    [0, "Field Generator Pod", "F,F,F,W+E", 0.65, "Systems", "Good"],
    [0, "Thermal Recovery Array", "W,F,F,W+F", 0.65, "Systems", "Good"],
    [0, "Beam Power Transmitter", "E,F,F,W+F", 0.65, "Systems", "Good"],
    [0, "Beam Power Receiver", "F,F,A,W+F", 0.65, "Systems", "Good"],
    [0, "Stellar Flux Collector", "F,W+F,W+F", 0.65, "Systems", "Good"],
    [0, "Isotope Generator", "W,E,F,F,A", 0.65, "Systems", "Good"],
    [0, "Shipboard Microreactor", "W,W,F,F,A", 0.65, "Systems", "Good"],
    [0, "High Voltage Switching Rack", "W,F,F,A,A", 0.65, "Systems", "Good"],
    [0, "Reactor Shield Assembly", "W,F,F,W+A", 0.65, "Systems", "Good"],
    [0, "Radiator Wing", "E,E,F,F,A", 0.65, "Systems", "Good"],
    [0, "Cryogenic Energy Reservoir", "E,F,F,W+A", 0.65, "Systems", "Good"],
    [0, "Flywheel Storage Unit", "F,F,A,W+E", 0.65, "Systems", "Good"],
    [0, "Magnetic Energy Store", "F,W+F,F+A", 0.65, "Systems", "Good"],
    [0, "Hospital Backup Generator", "W,E,F,W+F", 0.65, "Systems", "Good"],
    [0, "Grid Synchronization Controller", "E,F,A,W+F", 0.65, "Systems", "Good"],
    [0, "Plasma Energy Converter", "W,W,F,W+F", 0.65, "Systems", "Good"],
    [0, "Reactor Ignition Assembly", "F,A,A,W+F", 0.65, "Systems", "Good"],
    [0, "Power Regulation Rack", "F,W+F,W+A", 0.65, "Systems", "Good"],
    [0, "Waste Heat Recovery Plant", "W,W+F,W+F", 0.65, "Systems", "Good"],
    [1, "Thruster Nozzle", "W,F,F", 1, "Components", "Good"],
    [1, "Propellant Cartridge", "F,F,A", 1, "Consumables", "Good"],
    [1, "Reaction Mass Tank", "F,F+A", 1, "Components", "Good"],
    [1, "Thrust Bearing", "W,W,F", 1, "Components", "Good"],
    [1, "Ignition Electrode", "A,F+A", 1, "Components", "Good"],
    [1, "Maneuvering Thruster", "W,F,F,F", 0.8, "Assemblies", "Good"],
    [1, "Ion Accelerator", "F,F,F,A", 0.8, "Assemblies", "Good"],
    [1, "Plasma Injector", "F,F,F+A", 0.8, "Assemblies", "Good"],
    [1, "Fuel Metering Valve", "W,F,F,A", 0.8, "Assemblies", "Good"],
    [1, "Navigation Gyroscope", "W,W,F,F", 0.8, "Assemblies", "Good"],
    [1, "Inertial Reference Unit", "F,F,W+E", 0.8, "Assemblies", "Good"],
    [1, "Magnetic Nozzle", "W,F,F+A", 0.8, "Assemblies", "Good"],
    [1, "Reaction Wheel", "E,F,F+A", 0.8, "Assemblies", "Good"],
    [1, "Trajectory Computer", "F,A,F+A", 0.8, "Assemblies", "Good"],
    [1, "Star Tracker", "F+A,F+A", 0.8, "Assemblies", "Good"],
    [1, "Thrust Vector Actuator", "W,F,A,A", 0.8, "Assemblies", "Good"],
    [1, "Propellant Preheater", "W,W,F+A", 0.8, "Assemblies", "Good"],
    [1, "Ion Drive Assembly", "W,F,F,F,F", 0.65, "Systems", "Good"],
    [1, "Plasma Drive Assembly", "F,F,F,F,A", 0.65, "Systems", "Good"],
    [1, "Fusion Torch Engine", "F,F,F,F+A", 0.65, "Systems", "Good"],
    [1, "Antimatter Drive Chamber", "W,F,F,F,A", 0.65, "Systems", "Good"],
    [1, "Solar Sail Rig", "W,W,F,F,F", 0.65, "Systems", "Good"],
    [1, "Magnetic Sail Rig", "F,F,F,A,A", 0.65, "Systems", "Good"],
    [1, "Gravity Assist Navigation Rack", "F,F,F,W+A", 0.65, "Systems", "Good"],
    [1, "Deep Space Guidance Array", "W,F,F,F+A", 0.65, "Systems", "Good"],
    [1, "Orbital Transfer Engine", "E,F,F,F+A", 0.65, "Systems", "Good"],
    [1, "Landing Engine Cluster", "F,F,A,F+A", 0.65, "Systems", "Good"],
    [1, "Launch Booster Module", "F,F+A,F+A", 0.65, "Systems", "Good"],
    [1, "Asteroid Tug Drive", "W,W,E,F,F", 0.65, "Systems", "Good"],
    [1, "Station Keeping Thruster Bank", "W,E,E,F,F", 0.65, "Systems", "Good"],
    [1, "Interplanetary Cruise Engine", "W,F,F,W+E", 0.65, "Systems", "Good"],
    [1, "Propellant Recycling Plant", "W,F,F,E+A", 0.65, "Systems", "Good"],
    [1, "High Impulse Maneuvering Pack", "E,F,F,A,A", 0.65, "Systems", "Good"],
    [1, "Precision Docking Drive", "E,F,F,E+A", 0.65, "Systems", "Good"],
    [1, "Atmospheric Entry Control Pack", "F,F,A,E+A", 0.65, "Systems", "Good"],
    [1, "Autonomous Flight Controller", "W,W,W,F,F", 0.65, "Systems", "Good"],
    [1, "Relativistic Navigation Array", "W,E,F,F+A", 0.65, "Systems", "Good"],
    [1, "Drive Thermal Management Pack", "W,F,A,F+A", 0.65, "Systems", "Good"],
    [1, "Fuel Injection Manifold", "E,F,A,F+A", 0.65, "Systems", "Good"],
    [1, "Engine Test Chamber", "W,W,F,F+A", 0.65, "Systems", "Good"],
    [1, "Long Range Flight Computer", "F,A,A,F+A", 0.65, "Systems", "Good"],
    [1, "Emergency Return Drive", "W,F+A,F+A", 0.65, "Systems", "Good"],
    [2, "Hull Plate", "E,E,E", 1, "Components", "Good"],
    [2, "Frame Spar", "E,E,F", 1, "Components", "Good"],
    [2, "Pressure Seal", "W,E,F", 1, "Components", "Good"],
    [2, "Structural Rivet", "W,E,A", 1, "Components", "Good"],
    [2, "Bulkhead Panel", "E,E,E,E", 0.8, "Assemblies", "Good"],
    [2, "Pressure Hatch", "E,E,E,F", 0.8, "Assemblies", "Good"],
    [2, "Docking Collar", "E,E,E+A", 0.8, "Assemblies", "Good"],
    [2, "Window Shield", "E,E,W+E", 0.8, "Assemblies", "Good"],
    [2, "Landing Strut", "W,E,E,F", 0.8, "Assemblies", "Good"],
    [2, "Cargo Bay Door", "E,E,F,A", 0.8, "Assemblies", "Good"],
    [2, "Hull Sensor Strip", "E,E,A,A", 0.8, "Assemblies", "Good"],
    [2, "Debris Bumper", "E,E,E+F", 0.8, "Assemblies", "Good"],
    [2, "Structural Truss", "W,E,F,A", 0.8, "Assemblies", "Good"],
    [2, "Fuel Tank Shell", "W,W,E,F", 0.8, "Assemblies", "Good"],
    [2, "Insulated Hull Panel", "W,E,A,A", 0.8, "Assemblies", "Good"],
    [2, "Radiation Resistant Window", "W,A,W+F", 0.8, "Assemblies", "Good"],
    [2, "Orbital Platform Frame", "E,E,E,E,E", 0.65, "Systems", "Good"],
    [2, "Reconnaissance Ship Hull", "E,E,E,E,F", 0.65, "Systems", "Good"],
    [2, "Freighter Hull", "E,E,E,E+A", 0.65, "Systems", "Good"],
    [2, "Survey Ship Hull", "E,E,E,W+E", 0.65, "Systems", "Good"],
    [2, "Mining Barge Hull", "W,E,E,E,F", 0.65, "Systems", "Good"],
    [2, "Orbital Tug Hull", "E,E,E,F,A", 0.65, "Systems", "Good"],
    [2, "Patrol Cruiser Hull", "E,E,E,F,F", 0.65, "Systems", "Good"],
    [2, "Launch Vehicle Body", "E,E,E,W+A", 0.65, "Systems", "Good"],
    [2, "Reentry Capsule Shell", "W,E,E,E+A", 0.65, "Systems", "Good"],
    [2, "Station Spine", "E,E,F,E+A", 0.65, "Systems", "Good"],
    [2, "Docking Hub Structure", "E,E,A,E+A", 0.65, "Systems", "Good"],
    [2, "Shipyard Gantry", "W,E,E,W+E", 0.65, "Systems", "Good"],
    [2, "Medical Transport Chassis", "E,E,F,W+E", 0.65, "Systems", "Good"],
    [2, "Rotating Station Ring", "E,E,A,W+E", 0.65, "Systems", "Good"],
    [2, "High Pressure Vessel", "W,E,E,F,A", 0.65, "Systems", "Good"],
    [2, "Cryogenic Tank Assembly", "W,W,E,E,F", 0.65, "Systems", "Good"],
    [2, "Deployable Ship Radiator Frame", "W,E,E,A,A", 0.65, "Systems", "Good"],
    [2, "Meteoroid Shield Array", "W,E,E,E+F", 0.65, "Systems", "Good"],
    [2, "Deep Space Hull Section", "E,E,F,W+A", 0.65, "Systems", "Good"],
    [2, "Repair Dock Frame", "W,W,W,E,E", 0.65, "Systems", "Good"],
    [2, "Heavy Lift Landing Gear", "E,W+E,W+F", 0.65, "Systems", "Good"],
    [2, "Variable Geometry Wing", "E,W+E,F+A", 0.65, "Systems", "Good"],
    [2, "Atmospheric Skimmer Body", "W,W,E,F,A", 0.65, "Systems", "Good"],
    [2, "Fleet Carrier Deck", "W,E,F,A,A", 0.65, "Systems", "Good"],
    [2, "Evacuation Craft Hull", "W,E,A,W+F", 0.65, "Systems", "Good"],
    [2, "Orbital Drydock Shell", "W,W,E,W+F", 0.65, "Systems", "Good"],
    [3, "Habitat Tile", "W,W+E", 1, "Components", "Good"],
    [3, "Habitat Anchor Bolt", "E,W+E", 1, "Components", "Good"],
    [3, "Shelter Insulation Blanket", "F,W+E", 1, "Components", "Good"],
    [3, "Life Support Mount", "W,W,E", 1, "Components", "Good"],
    [3, "Pressure Wall", "W+E,W+E", 0.8, "Assemblies", "Good"],
    [3, "Airlock Door", "W,W,W+E", 0.8, "Assemblies", "Good"],
    [3, "Habitat Floor Deck", "W+E,E+A", 0.8, "Assemblies", "Good"],
    [3, "Water Distribution Conduit", "W,E,W+E", 0.8, "Assemblies", "Good"],
    [3, "Radiation Screen", "W,F,W+E", 0.8, "Assemblies", "Good"],
    [3, "Light Panel", "W,A,W+E", 0.8, "Assemblies", "Good"],
    [3, "Atmosphere Reservoir", "E,F,W+E", 0.8, "Assemblies", "Good"],
    [3, "Shelter Thermal Curtain", "E,A,W+E", 0.8, "Assemblies", "Good"],
    [3, "Hydroponic Rack Frame", "W,W,W,F", 0.8, "Assemblies", "Good"],
    [3, "Habitat Window", "W+E,W+F", 0.8, "Assemblies", "Good"],
    [3, "Water Recovery Cartridge", "W+E,F+A", 0.8, "Assemblies", "Good"],
    [3, "Air Circulation Fan", "W,W,W+F", 0.8, "Assemblies", "Good"],
    [3, "Habitat Pressure Module", "W,W+E,W+E", 0.65, "Systems", "Good"],
    [3, "Orbital Habitat Shell", "W,W+E,E+A", 0.65, "Systems", "Good"],
    [3, "Civilian Outpost Module", "W,W,W,W+E", 0.65, "Systems", "Good"],
    [3, "Rotating Habitat Hub", "E,W+E,W+E", 0.65, "Systems", "Good"],
    [3, "Asteroid Settlement Anchor", "F,W+E,W+E", 0.65, "Systems", "Good"],
    [3, "Deep Space Shelter", "A,W+E,W+E", 0.65, "Systems", "Good"],
    [3, "Worker Quarters Module", "W,W,E,W+E", 0.65, "Systems", "Good"],
    [3, "Food Cultivation Chamber", "W,W,F,W+E", 0.65, "Systems", "Good"],
    [3, "Hospital Isolation Module", "W,W,A,W+E", 0.65, "Systems", "Good"],
    [3, "Greenhouse Dome", "E,W+E,E+A", 0.65, "Systems", "Good"],
    [3, "Subsurface Outpost Liner", "F,W+E,E+A", 0.65, "Systems", "Good"],
    [3, "Orbital Elevator Anchor", "A,W+E,E+A", 0.65, "Systems", "Good"],
    [3, "Space Elevator Cable Drum", "W,E,F,W+E", 0.65, "Systems", "Good"],
    [3, "Solar Shade Assembly", "W,E,A,W+E", 0.65, "Systems", "Good"],
    [3, "Nutrient Synthesis Plant", "W,F,A,W+E", 0.65, "Systems", "Good"],
    [3, "Habitat Thermal Buffer Wall", "W,A,A,W+E", 0.65, "Systems", "Good"],
    [3, "Modular Station Extension", "W,W+E,W+F", 0.65, "Systems", "Good"],
    [3, "Emergency Housing Mold", "W,W+E,F+A", 0.65, "Systems", "Good"],
    [3, "Atmosphere Control Rack", "E,F,A,W+E", 0.65, "Systems", "Good"],
    [3, "Water Recycling Plant", "W,W,W,E,F", 0.65, "Systems", "Good"],
    [3, "Settlement Power Corridor", "W,W,W,F,A", 0.65, "Systems", "Good"],
    [3, "Deployable Landing Platform", "F,W+E,W+F", 0.65, "Systems", "Good"],
    [3, "Station Expansion Truss", "F,W+E,F+A", 0.65, "Systems", "Good"],
    [3, "Orbital Ring Segment", "A,W+E,W+F", 0.65, "Systems", "Good"],
    [3, "Patient Recovery Module", "W,W,W,F+A", 0.65, "Systems", "Good"],
    [3, "Evacuation Shelter Capsule", "W,W,A,W+F", 0.65, "Systems", "Good"],
    [4, "Robot Joint", "W,E+A", 1, "Components", "Good"],
    [4, "Actuator Rod", "E,E+A", 1, "Components", "Good"],
    [4, "Prosthetic Grip Pad", "A,E+A", 1, "Components", "Good"],
    [4, "Motor Winding", "W,F+A", 1, "Components", "Good"],
    [4, "Precision Actuator Bearing", "E,A,A", 1, "Components", "Good"],
    [4, "Robot Hand", "E+A,E+A", 0.8, "Assemblies", "Good"],
    [4, "Tool Changer", "E+F,E+A", 0.8, "Assemblies", "Good"],
    [4, "Locomotion Wheel", "E+A,F+A", 0.8, "Assemblies", "Good"],
    [4, "Manipulator Arm", "W,F,E+A", 0.8, "Assemblies", "Good"],
    [4, "Force Feedback Unit", "E,F,E+A", 0.8, "Assemblies", "Good"],
    [4, "Hydraulic Actuator", "E,A,E+A", 0.8, "Assemblies", "Good"],
    [4, "Magnetic Gripper", "F,A,E+A", 0.8, "Assemblies", "Good"],
    [4, "Precision Servo", "A,A,E+A", 0.8, "Assemblies", "Good"],
    [4, "Robot Vision Head", "W+F,E+A", 0.8, "Assemblies", "Good"],
    [4, "Autonomous Control Board", "E+F,F+A", 0.8, "Assemblies", "Good"],
    [4, "Joint Cooling Jacket", "W,A,F+A", 0.8, "Assemblies", "Good"],
    [4, "Manipulator Wrist", "A,A,F+A", 0.8, "Assemblies", "Good"],
    [4, "Assembly Robot", "W,E+A,E+A", 0.65, "Systems", "Good"],
    [4, "Welding Robot", "E,E+A,E+A", 0.65, "Systems", "Good"],
    [4, "Inspection Robot", "F,E+A,E+A", 0.65, "Systems", "Good"],
    [4, "Excavation Robot", "W,E+F,E+A", 0.65, "Systems", "Good"],
    [4, "Hull Repair Robot", "E,E+F,E+A", 0.65, "Systems", "Good"],
    [4, "Cargo Handling Robot", "F,E+F,E+A", 0.65, "Systems", "Good"],
    [4, "Microassembly Robot", "A,E+F,E+A", 0.65, "Systems", "Good"],
    [4, "Vacuum Work Robot", "W,E+A,F+A", 0.65, "Systems", "Good"],
    [4, "Survey Walker", "E,E+A,F+A", 0.65, "Systems", "Good"],
    [4, "Maintenance Crawler", "F,E+A,F+A", 0.65, "Systems", "Good"],
    [4, "Station Construction Robot", "A,E+A,F+A", 0.65, "Systems", "Good"],
    [4, "Precision Machining Robot", "W,E,F,E+A", 0.65, "Systems", "Good"],
    [4, "Autonomous Foundry Robot", "W,F,A,E+A", 0.65, "Systems", "Good"],
    [4, "Mine Rescue Robot", "E,F,A,E+A", 0.65, "Systems", "Good"],
    [4, "Asteroid Anchoring Robot", "W,A,A,E+A", 0.65, "Systems", "Good"],
    [4, "Robotic Fabrication Cell", "W,W+F,E+A", 0.65, "Systems", "Good"],
    [4, "Surgical Robot Manipulator", "W,E+F,F+A", 0.65, "Systems", "Good"],
    [4, "Magnetic Hull Repair Robot", "E,A,A,E+A", 0.65, "Systems", "Good"],
    [4, "Radiation Hardened Robot", "E,W+F,E+A", 0.65, "Systems", "Good"],
    [4, "Modular Robot Chassis", "E,E+F,F+A", 0.65, "Systems", "Good"],
    [4, "Swarm Coordination Unit", "F,A,A,E+A", 0.65, "Systems", "Good"],
    [4, "Robot Refurbishment Rack", "F,W+F,E+A", 0.65, "Systems", "Good"],
    [4, "Autonomous Assembly Line", "A,W+F,E+A", 0.65, "Systems", "Good"],
    [4, "Heavy Lift Exoskeleton", "A,A,A,E+A", 0.65, "Systems", "Good"],
    [4, "Medical Assistance Robot", "A,F+A,F+A", 0.65, "Systems", "Good"],
    [5, "Circuit Trace", "F,E+F", 1, "Components", "Good"],
    [5, "Memory Wafer", "W,E+F", 1, "Components", "Good"],
    [5, "Optical Fiber", "W,F,A", 1, "Components", "Good"],
    [5, "Processor Substrate", "F,A,A", 1, "Components", "Good"],
    [5, "Logic Board", "F,F,E+F", 0.8, "Assemblies", "Good"],
    [5, "Learning Terminal Memory Bank", "W,F,E+F", 0.8, "Assemblies", "Good"],
    [5, "Civilian Network Transceiver", "E,F,E+F", 0.8, "Assemblies", "Good"],
    [5, "Signal Amplifier", "F,A,E+F", 0.8, "Assemblies", "Good"],
    [5, "Network Switch", "E,E,F,F", 0.8, "Assemblies", "Good"],
    [5, "Data Buffer", "F,F,W+A", 0.8, "Assemblies", "Good"],
    [5, "Clock Module", "W+F,E+F", 0.8, "Assemblies", "Good"],
    [5, "Quantum Control Chip", "W,E,E+F", 0.8, "Assemblies", "Good"],
    [5, "Thermal Processor Plate", "F,A,W+F", 0.8, "Assemblies", "Good"],
    [5, "Archive Integrity Board", "W+A,E+F", 0.8, "Assemblies", "Good"],
    [5, "Antenna Tile", "E,F,A,A", 0.8, "Assemblies", "Good"],
    [5, "Timing Reference Unit", "A,A,W+F", 0.8, "Assemblies", "Good"],
    [5, "Core Processor Rack", "F,F,F,E+F", 0.65, "Systems", "Good"],
    [5, "Navigation Compute Rack", "F,E+F,E+F", 0.65, "Systems", "Good"],
    [5, "Autonomous Planning Core", "W,F,F,E+F", 0.65, "Systems", "Good"],
    [5, "Radiation Hardened Computer", "E,F,F,E+F", 0.65, "Systems", "Good"],
    [5, "Quantum Processing Module", "F,F,A,E+F", 0.65, "Systems", "Good"],
    [5, "Settlement Compute Node", "F,W+F,E+F", 0.65, "Systems", "Good"],
    [5, "Fleet Coordination Server", "F,F,F,E+A", 0.65, "Systems", "Good"],
    [5, "Orbital Communication Relay", "W,E,F,E+F", 0.65, "Systems", "Good"],
    [5, "Laser Communication Terminal", "W,F,A,E+F", 0.65, "Systems", "Good"],
    [5, "Deep Space Radio Array", "E,F,A,E+F", 0.65, "Systems", "Good"],
    [5, "Interplanetary Router", "W,W,F,E+F", 0.65, "Systems", "Good"],
    [5, "Cultural Archive Vault", "E,E,F,E+F", 0.65, "Systems", "Good"],
    [5, "High Bandwidth Link Module", "F,W+A,E+F", 0.65, "Systems", "Good"],
    [5, "Encrypted Communication Rack", "F,E+F,F+A", 0.65, "Systems", "Good"],
    [5, "Signal Routing Matrix", "W,W+F,E+F", 0.65, "Systems", "Good"],
    [5, "Photonic Compute Module", "E,F,F,W+E", 0.65, "Systems", "Good"],
    [5, "Sensor Fusion Computer", "E,W+F,E+F", 0.65, "Systems", "Good"],
    [5, "Life Support Control Computer", "A,W+F,E+F", 0.65, "Systems", "Good"],
    [5, "Industrial Control Server", "F,F,A,A,A", 0.65, "Systems", "Good"],
    [5, "Instruction Simulation Computer", "W,F,A,W+F", 0.65, "Systems", "Good"],
    [5, "Cryogenic Compute Cabinet", "W,W,E,E+F", 0.65, "Systems", "Good"],
    [5, "Fault Tolerant Memory Array", "W,W+A,E+F", 0.65, "Systems", "Good"],
    [5, "Clock Synchronization Array", "E,W+A,E+F", 0.65, "Systems", "Good"],
    [5, "Remote Learning Terminal", "W,W,W,E+F", 0.65, "Systems", "Good"],
    [5, "Communication Beam Director", "W,W,F,A,A", 0.65, "Systems", "Good"],
    [5, "Public Archive Recovery Appliance", "A,W+F,W+F", 0.65, "Systems", "Good"],
    [6, "Sensor Lens", "A,E+F", 1, "Components", "Good"],
    [6, "Detector Film", "E,E+F", 1, "Components", "Good"],
    [6, "Probe Casing", "A,W+E", 1, "Components", "Good"],
    [6, "Sterile Sampling Vial", "A,A,A", 1, "Components", "Good"],
    [6, "Diagnostic Calibration Target", "A,W+F", 1, "Components", "Good"],
    [6, "Spectrometer Head", "E+F,E+F", 0.8, "Assemblies", "Good"],
    [6, "Radar Antenna", "A,A,E+F", 0.8, "Assemblies", "Good"],
    [6, "Lidar Emitter", "W+E,E+F", 0.8, "Assemblies", "Good"],
    [6, "Thermal Diagnostic Detector", "W,A,E+F", 0.8, "Assemblies", "Good"],
    [6, "Magnetic Field Sensor", "E,A,E+F", 0.8, "Assemblies", "Good"],
    [6, "Seismic Sensor", "A,A,W+E", 0.8, "Assemblies", "Good"],
    [6, "Radiation Counter", "A,A,A,A", 0.8, "Assemblies", "Good"],
    [6, "Breathing Gas Analyzer", "F,A,W+E", 0.8, "Assemblies", "Good"],
    [6, "Thermal Imaging Unit", "W,W,E+F", 0.8, "Assemblies", "Good"],
    [6, "Gravimetric Sensor", "E,A,A,A", 0.8, "Assemblies", "Good"],
    [6, "Airborne Particle Detector", "W,W,A,A", 0.8, "Assemblies", "Good"],
    [6, "Clinical Imaging Module", "W+F,W+A", 0.8, "Assemblies", "Good"],
    [6, "Astronomical Telescope", "A,E+F,E+F", 0.65, "Systems", "Good"],
    [6, "Planetary Survey Probe", "A,W+E,E+F", 0.65, "Systems", "Good"],
    [6, "Asteroid Mapping Probe", "W,E+F,E+F", 0.65, "Systems", "Good"],
    [6, "Deep Space Scout Probe", "E,E+F,E+F", 0.65, "Systems", "Good"],
    [6, "Surface Sampling Rover", "A,A,A,E+F", 0.65, "Systems", "Good"],
    [6, "Subsurface Survey Package", "W,A,A,E+F", 0.65, "Systems", "Good"],
    [6, "Orbital Imaging Array", "W,W+E,E+F", 0.65, "Systems", "Good"],
    [6, "Cosmic Ray Observatory", "E,A,A,E+F", 0.65, "Systems", "Good"],
    [6, "Solar Observation Platform", "E,W+E,E+F", 0.65, "Systems", "Good"],
    [6, "Radio Astronomy Array", "F,A,A,E+F", 0.65, "Systems", "Good"],
    [6, "Medical Imaging Scanner", "F,W+E,E+F", 0.65, "Systems", "Good"],
    [6, "Exoplanet Imaging Instrument", "A,A,A,W+E", 0.65, "Systems", "Good"],
    [6, "Atmospheric Survey Balloon", "A,A,A,A,A", 0.65, "Systems", "Good"],
    [6, "Ocean World Sonar Package", "W,E,A,E+F", 0.65, "Systems", "Good"],
    [6, "Ice Penetrating Radar", "W,W,A,E+F", 0.65, "Systems", "Good"],
    [6, "Water Quality Laboratory", "E,E,A,E+F", 0.65, "Systems", "Good"],
    [6, "Mineral Analysis Station", "E,A,A,W+E", 0.65, "Systems", "Good"],
    [6, "High Resolution Mapping Array", "F,A,A,W+E", 0.65, "Systems", "Good"],
    [6, "Long Baseline Interferometer", "A,W+A,E+F", 0.65, "Systems", "Good"],
    [6, "Tissue Analysis Instrument", "A,E+F,F+A", 0.65, "Systems", "Good"],
    [6, "Field Diagnostic Laboratory", "E,A,A,A,A", 0.65, "Systems", "Good"],
    [6, "Deep Bore Sampling Instrument", "W,E,A,A,A", 0.65, "Systems", "Good"],
    [6, "Pathogen Sampling Probe", "E,F,A,A,A", 0.65, "Systems", "Good"],
    [6, "Hazard Mapping Array", "A,W+E,F+A", 0.65, "Systems", "Good"],
    [6, "Precision Metrology Bench", "W,W,A,A,A", 0.65, "Systems", "Good"],
    [7, "Drill Tooth", "W,E,E", 1, "Components", "Good"],
    [7, "Abrasive Grain Pack", "E,E,A", 1, "Consumables", "Good"],
    [7, "Cutting Insert", "E,F+A", 1, "Components", "Good"],
    [7, "Lubricant Cartridge", "E,W+F", 1, "Consumables", "Good"],
    [7, "Drill Head", "W,E,E,E", 0.8, "Assemblies", "Good"],
    [7, "Crushing Jaw", "E,E,E,A", 0.8, "Assemblies", "Good"],
    [7, "Grinding Wheel", "E,E,F+A", 0.8, "Assemblies", "Good"],
    [7, "Smelting Crucible", "E,E,W+F", 0.8, "Assemblies", "Good"],
    [7, "Casting Mold", "W,E,E,A", 0.8, "Assemblies", "Good"],
    [7, "Welding Electrode Bank", "W,W,E,E", 0.8, "Assemblies", "Good"],
    [7, "Extrusion Die", "E,E,W+A", 0.8, "Assemblies", "Good"],
    [7, "Ore Separator", "W,E,F+A", 0.8, "Assemblies", "Good"],
    [7, "Induction Heater", "E,A,F+A", 0.8, "Assemblies", "Good"],
    [7, "Industrial Pump", "W,E,W+F", 0.8, "Assemblies", "Good"],
    [7, "Pressure Filter", "E,A,W+F", 0.8, "Assemblies", "Good"],
    [7, "Tool Cooling Block", "W+A,F+A", 0.8, "Assemblies", "Good"],
    [7, "Vacuum Furnace Liner", "W,E,E,E,E", 0.65, "Systems", "Good"],
    [7, "Asteroid Drill Rig", "E,E,E,E,A", 0.65, "Systems", "Good"],
    [7, "Regolith Excavator", "E,E,E,F+A", 0.65, "Systems", "Good"],
    [7, "Ore Crushing Plant", "E,E,E,W+F", 0.65, "Systems", "Good"],
    [7, "Magnetic Separation Plant", "W,E,E,E,A", 0.65, "Systems", "Good"],
    [7, "Electrochemical Refinery", "W,W,E,E,E", 0.65, "Systems", "Good"],
    [7, "Plasma Smelter", "E,E,E,A,A", 0.65, "Systems", "Good"],
    [7, "Vacuum Casting Plant", "E,E,E,E+F", 0.65, "Systems", "Good"],
    [7, "Precision Milling Center", "W,E,E,F+A", 0.65, "Systems", "Good"],
    [7, "Additive Fabrication Unit", "E,E,F,F+A", 0.65, "Systems", "Good"],
    [7, "Heavy Extrusion Press", "E,E,A,F+A", 0.65, "Systems", "Good"],
    [7, "Crystal Growth Chamber", "W,E,E,W+F", 0.65, "Systems", "Good"],
    [7, "Semiconductor Fabrication Rack", "E,E,F,W+F", 0.65, "Systems", "Good"],
    [7, "Polymer Synthesis Reactor", "E,E,A,W+F", 0.65, "Systems", "Good"],
    [7, "Composite Curing Chamber", "E,F+A,F+A", 0.65, "Systems", "Good"],
    [7, "Industrial Electrolyzer", "W,W,E,E,A", 0.65, "Systems", "Good"],
    [7, "Molecular Separation Column", "W,E,E,W+A", 0.65, "Systems", "Good"],
    [7, "Automated Tool Foundry", "E,E,F,A,A", 0.65, "Systems", "Good"],
    [7, "Deep Core Boring Rig", "E,W+F,F+A", 0.65, "Systems", "Good"],
    [7, "Ice Extraction Plant", "E,E,A,A,A", 0.65, "Systems", "Good"],
    [7, "Metal Recovery Plant", "W,E,A,F+A", 0.65, "Systems", "Good"],
    [7, "Volatile Capture Plant", "W,W,E,F+A", 0.65, "Systems", "Good"],
    [7, "Industrial Heat Treatment Cell", "E,A,A,F+A", 0.65, "Systems", "Good"],
    [7, "High Pressure Synthesis Chamber", "E,W+A,F+A", 0.65, "Systems", "Good"],
    [7, "Continuous Production Furnace", "E,W+F,W+F", 0.65, "Systems", "Good"],
    [7, "Autonomous Ore Processing Line", "E,A,A,W+F", 0.65, "Systems", "Good"],
    [8, "Cargo Strap", "W,W+A", 1, "Components", "Good"],
    [8, "Container Seal", "F,E+A", 1, "Components", "Good"],
    [8, "Packing Foam", "W,W,W", 1, "Components", "Good"],
    [8, "Tie Down Clamp", "W,W,A", 1, "Components", "Good"],
    [8, "Nutrient Cargo Canister", "W,W,E+A", 0.8, "Assemblies", "Good"],
    [8, "Provisioning Storage Rack", "W+A,E+A", 0.8, "Assemblies", "Good"],
    [8, "Transfer Coupler", "W,E,E+A", 0.8, "Assemblies", "Good"],
    [8, "Conveyor Segment", "W,A,E+A", 0.8, "Assemblies", "Good"],
    [8, "Docking Clamp", "W,W,W+A", 0.8, "Assemblies", "Good"],
    [8, "Pallet Chassis", "W,W,W,W", 0.8, "Assemblies", "Good"],
    [8, "Cargo Tracking Tag", "W,E,W+A", 0.8, "Assemblies", "Good"],
    [8, "Thermal Cargo Liner", "W,W,W,E", 0.8, "Assemblies", "Good"],
    [8, "Magnetic Cargo Lock", "W,W,W,A", 0.8, "Assemblies", "Good"],
    [8, "Potable Water Transfer Hose", "W,W,E,A", 0.8, "Assemblies", "Good"],
    [8, "Cargo Pod", "W,W+A,E+A", 0.65, "Systems", "Good"],
    [8, "Medical Cryogenic Vessel", "W,W,W,E+A", 0.65, "Systems", "Good"],
    [8, "Pressurized Freight Container", "A,E+A,E+A", 0.65, "Systems", "Good"],
    [8, "Hazardous Cargo Vault", "W,W,E,E+A", 0.65, "Systems", "Good"],
    [8, "Autonomous Cargo Pallet", "W,W,F,E+A", 0.65, "Systems", "Good"],
    [8, "Nutrition Reserve Silo", "W,W,A,E+A", 0.65, "Systems", "Good"],
    [8, "Vacuum Cargo Transfer Unit", "E,W+A,E+A", 0.65, "Systems", "Good"],
    [8, "Orbital Freight Rack", "F,W+A,E+A", 0.65, "Systems", "Good"],
    [8, "Ship Loading Gantry", "A,W+A,E+A", 0.65, "Systems", "Good"],
    [8, "Dockside Cargo Crane", "W,W,W,W+A", 0.65, "Systems", "Good"],
    [8, "Fuel Transfer Assembly", "W,W,W,W,W", 0.65, "Systems", "Good"],
    [8, "Medical Oxygen Storage Vault", "W,E,A,E+A", 0.65, "Systems", "Good"],
    [8, "Automated Sorting Machine", "W,W,E,W+A", 0.65, "Systems", "Good"],
    [8, "Food Preservation Chamber", "W,W,F,W+A", 0.65, "Systems", "Good"],
    [8, "Modular Warehouse Block", "W,W,A,W+A", 0.65, "Systems", "Good"],
    [8, "Intermodal Cargo Frame", "W,W,W,W,E", 0.65, "Systems", "Good"],
    [8, "Orbital Cargo Capsule", "W,W,W,W,F", 0.65, "Systems", "Good"],
    [8, "Cargo Ejection System", "W,W,W,W,A", 0.65, "Systems", "Good"],
    [8, "Civilian Resupply Pod", "W,E,F,W+A", 0.65, "Systems", "Good"],
    [8, "Microgravity Conveyor Array", "W,W,W,E,A", 0.65, "Systems", "Good"],
    [8, "Station Freight Elevator", "W,W+F,W+A", 0.65, "Systems", "Good"],
    [8, "Robotic Inventory Rack", "W,W+A,F+A", 0.65, "Systems", "Good"],
    [8, "Bulk Gas Storage Array", "W,W,W,A,A", 0.65, "Systems", "Good"],
    [8, "Biological Sample Transport Pod", "W,W,W,W+F", 0.65, "Systems", "Good"],
    [8, "Fleet Provisioning Module", "W,W,E,A,A", 0.65, "Systems", "Good"],
    [8, "Docking Alignment Rig", "W,W,A,F+A", 0.65, "Systems", "Good"],
    [8, "Container Repair Press", "W,A,A,W+F", 0.65, "Systems", "Good"],
    [8, "Heavy Cargo Transfer Platform", "W,W+F,F+A", 0.65, "Systems", "Good"],
    [9, "Shield Mesh", "A,W+A", 1, "Components", "Good"],
    [9, "Impact Foam", "E,W+A", 1, "Components", "Good"],
    [9, "Pressure Suit Repair Patch", "F,W+A", 1, "Components", "Good"],
    [9, "Fire Suppressant Cartridge", "W,A,A", 1, "Consumables", "Good"],
    [9, "Debris Shield", "W+A,W+A", 0.8, "Assemblies", "Good"],
    [9, "Radiation Shield", "A,A,W+A", 0.8, "Assemblies", "Good"],
    [9, "Pressure Barrier", "W+E,W+A", 0.8, "Assemblies", "Good"],
    [9, "Fire Isolation Panel", "W,A,W+A", 0.8, "Assemblies", "Good"],
    [9, "Emergency Beacon", "E,A,W+A", 0.8, "Assemblies", "Good"],
    [9, "Surge Protector", "F,A,W+A", 0.8, "Assemblies", "Good"],
    [9, "Leak Detection Unit", "W,F,W+A", 0.8, "Assemblies", "Good"],
    [9, "Civilian Hazard Warning Sensor", "E,F,W+A", 0.8, "Assemblies", "Good"],
    [9, "Combat Armor Plate", "W,A,A,A", 0.8, "Assemblies", "Good"],
    [9, "Blast Door", "F,A,A,A", 0.8, "Assemblies", "Good"],
    [9, "Containment Valve", "A,W+A,W+A", 0.65, "Systems", "Good"],
    [9, "Rescue Tether Reel", "A,W+E,W+A", 0.65, "Systems", "Good"],
    [9, "Electromagnetic Shield Array", "W,W+A,W+A", 0.65, "Systems", "Good"],
    [9, "Radiation Shelter Core", "E,W+A,W+A", 0.65, "Systems", "Good"],
    [9, "Hull Breach Containment Pack", "F,W+A,W+A", 0.65, "Systems", "Good"],
    [9, "Fire Suppression Module", "A,A,A,W+A", 0.65, "Systems", "Good"],
    [9, "Defence Interceptor Drone", "W,A,A,W+A", 0.65, "Systems", "Good"],
    [9, "Collision Avoidance Array", "W,W+E,W+A", 0.65, "Systems", "Good"],
    [9, "Emergency Escape Pod", "E,A,A,W+A", 0.65, "Systems", "Good"],
    [9, "Automated Rescue Craft", "E,W+E,W+A", 0.65, "Systems", "Good"],
    [9, "Early Warning Sensor Grid", "F,A,A,W+A", 0.65, "Systems", "Good"],
    [9, "Solar Storm Protection Array", "F,W+E,W+A", 0.65, "Systems", "Good"],
    [9, "Fleet Deflection Shield", "W,E,A,W+A", 0.65, "Systems", "Good"],
    [9, "Impact Absorption Frame", "W,F,A,W+A", 0.65, "Systems", "Good"],
    [9, "Reactor Containment Shell", "E,F,A,W+A", 0.65, "Systems", "Good"],
    [9, "Critical System Backup Rack", "E,E,A,W+A", 0.65, "Systems", "Good"],
    [9, "Emergency Cooling Assembly", "F,F,A,W+A", 0.65, "Systems", "Good"],
    [9, "Redundant Control Module", "A,W+F,W+A", 0.65, "Systems", "Good"],
    [9, "Pressure Recovery Plant", "A,W+A,F+A", 0.65, "Systems", "Good"],
    [9, "Damage Isolation Controller", "W,A,A,A,A", 0.65, "Systems", "Good"],
    [9, "Shielded Navigation Core", "F,A,A,A,A", 0.65, "Systems", "Good"],
    [9, "Continuity Archive Vault", "W,F,A,A,A", 0.65, "Systems", "Good"],
    [9, "Autonomous Damage Control Robot", "E,W+F,W+A", 0.65, "Systems", "Good"],
    [9, "Orbital Defence Barrier", "F,W+A,F+A", 0.65, "Systems", "Good"],
    [9, "Fortified Shelter Gate", "A,A,A,W+F", 0.65, "Systems", "Good"],
    [9, "Emergency Docking Module", "A,A,A,F+A", 0.65, "Systems", "Good"],
    [9, "Medical Evacuation Capsule", "W,A,A,F+A", 0.65, "Systems", "Good"],
    [9, "Civilian Refuge Shelter", "A,W+F,F+A", 0.65, "Systems", "Good"],
  ];
  const recipeWeightTotals = {};
  for (const [sector, , recipe, weight] of recipes) {
    const c = recipe.split(',').reduce((n, code) => n + PRODUCTS.find(p => p.code === code).complexity, 0);
    const key = sector + ':' + c;
    recipeWeightTotals[key] = (recipeWeightTotals[key] || 0) + weight;
  }
  const seenRecipes = new Set(), seenNames = new Set();
  const T2_CATALOGUE = Object.freeze(recipes.map(([sectorIndex, name, recipe, authoredNeedWeight, needType, kind], id) => {
    const inputs = {};
    for (const code of recipe.split(',')) inputs[code] = (inputs[code] || 0) + 1;
    const ingredients = Object.entries(inputs).map(([code, quantity]) =>
      Object.freeze([PRODUCTS.findIndex((p) => p.code === code), quantity]));
    const complexity = ingredients.reduce((c, [material, quantity]) => c + quantity * (material < 4 ? 1 : 2), 0);
    if (!TIER_BOUNDARIES.T2.includes(complexity)) throw new Error('Tier 2 recipes must be C-3 through C-5.');
    const key = recipeKey(inputs);
    if (seenRecipes.has(key)) throw new Error('Duplicate Tier 2 recipe: ' + key);
    seenRecipes.add(key);
    if (seenNames.has(name)) throw new Error('Duplicate Tier 2 name: ' + name);
    seenNames.add(name);
    if (!T2_NEED_TYPES.includes(needType) || kind !== 'Good') throw new Error('Invalid catalogue classification: ' + name);
    const composition = elementalComposition(inputs);
    // Preserve demand per sector/complexity when dividing it among more needs.
    const needWeight = authoredNeedWeight * ({3:2.4,4:1.65,5:1.3})[complexity] / recipeWeightTotals[sectorIndex + ':' + complexity];
    const primaryMaterial = ingredients.reduce((best, entry) =>
      entry[1] * PRODUCTS[entry[0]].complexity > best[1] * PRODUCTS[best[0]].complexity ? entry : best)[0];
    const dominantMaterial = PRODUCTS[primaryMaterial].code;
    const conversionCost = 0.5 * complexity;
    return Object.freeze({
      id, code: `T2-${String(id + 1).padStart(3, '0')}`, recipeKey: key, composition, name, kind, needType, sectorIndex,
      sector: T2_SECTORS[sectorIndex], primaryMaterial: dominantMaterial, complexity, inputs: Object.freeze(inputs),
      ingredients: Object.freeze(ingredients), equipmentClass: `Fabrication C-${complexity}`,
      equipmentPrice: T2_ROUTE_SETUP, capacity: t2Capacity(complexity),
      conversionCost, needWeight, demandWeight: needWeight * T2_SECTOR_WEIGHTS[sectorIndex],
      demandFactor: 0.45 ** (complexity - 1), reservationPremium: 1 + 0.45 * (complexity - 1),
      // Authored taste scale, independent of ingredient prices and markups.
      // At this scale (before private taste/premium), desired quantity halves.
      consumerValue: ({ 3: 8, 4: 12, 5: 16 })[complexity],
    });
  }));
  // Hamilton apportionment of 20 slots from the complete 44/116/260 pool:
  // quotas 2.095/5.524/12.381 -> 2/6/12. Identical for every sector.
  const INVENTED_PER_COMPLEXITY = Object.freeze({3: 2, 4: 6, 5: 12});
  const selected = new Set();
  const exposure = Array(10).fill(0);
  for (const c of [3,4,5]) {
    for (let slot = 0; slot < INVENTED_PER_COMPLEXITY[c]; slot++) {
      for (let sector = 0; sector < 10; sector++) {
        const eligible = T2_CATALOGUE.filter(p => p.sectorIndex === sector && p.complexity === c && !selected.has(p.code));
        const score = p => {
          const next = exposure.slice();
          for (const [material, q] of p.ingredients) next[material] += q;
          // Balance each material orbit: four basics and six pair compounds.
          return [next.slice(0,4), next.slice(4)].reduce((sum, values) => {
            const mean = values.reduce((a,b) => a+b,0) / values.length;
            return sum + values.reduce((n,v) => n + (v-mean)**2,0);
          },0);
        };
        eligible.sort((a,b) => score(a)-score(b) || a.recipeKey.localeCompare(b.recipeKey));
        const product = eligible[0]; selected.add(product.code);
        for (const [material,q] of product.ingredients) exposure[material] += q;
      }
    }
  }
  const T2_PRODUCTS = Object.freeze(T2_CATALOGUE.filter(p => selected.has(p.code)).map((p,id) =>
    Object.freeze({...p, id, invented: true, needWeight: 1 / INVENTED_PER_COMPLEXITY[p.complexity],
      demandWeight: 1 / 20})));
  const T2_UNINVENTED_PRODUCTS = Object.freeze(T2_CATALOGUE.filter(p => !selected.has(p.code)).map(p => Object.freeze({...p, invented: false})));
  const pool = [];
  const enumerateRecipes = (start, remaining, inputs) => {
    if (remaining === 0) {
      const key = recipeKey(inputs);
      pool.push(Object.freeze({ code: 'R-' + String(pool.length + 1).padStart(3, '0'),
        recipeKey: key, inputs: Object.freeze({...inputs}), composition: elementalComposition(inputs),
        complexity: Object.values(elementalComposition(inputs)).reduce((n, q) => n + q, 0) }));
      return;
    }
    for (let i = start; i < PRODUCTS.length; i++) {
      const p = PRODUCTS[i];
      if (p.complexity > remaining) continue;
      inputs[p.code] = (inputs[p.code] || 0) + 1;
      enumerateRecipes(i, remaining - p.complexity, inputs);
      if (--inputs[p.code] === 0) delete inputs[p.code];
    }
  };
  for (const c of [3,4,5]) enumerateRecipes(0, c, {});
  const T2_RECIPE_POOL = Object.freeze(pool);
  const T2_RECIPE_BY_KEY = Object.freeze(Object.fromEntries(pool.map(r => [r.recipeKey, r])));
  const T2_MATERIAL_COVERAGE = Object.freeze(PRODUCTS.map(material => Object.freeze({
    code: material.code, name: material.name,
    possible: Object.freeze([3,4,5].map(c => pool.filter(r => r.complexity === c && r.inputs[material.code]).length)),
    active: Object.freeze([3,4,5].map(c => T2_PRODUCTS.filter(r => r.complexity === c && r.inputs[material.code]).length)),
  })));
  if (pool.length !== 420 || T2_CATALOGUE.length !== pool.length || T2_PRODUCTS.length !== 200 || T2_PRODUCTS.some(p => !T2_RECIPE_BY_KEY[p.recipeKey]))
    throw new Error('Active markets must have distinct recipes from the complete 420-recipe pool.');
  const T2_COMPLEXITY_COUNTS = Object.freeze([1, 2, 3, 4, 5].map(c =>
    T2_PRODUCTS.filter(p => p.complexity === c).length));
  const T2_PRODUCT_BY_CODE = Object.freeze(Object.fromEntries(T2_PRODUCTS.map(p => [p.code, p])));
  const portfolioOptions = (products, maxWidth = T2_MAX_PRODUCTS_PER_FIRM) => {
    const options = [], pick = [];
    const visit = (start, remaining) => {
      if (!remaining) { options.push(Object.freeze(pick.slice())); return; }
      for (let i = start; i <= products.length - remaining; i++) {
        pick.push(products[i]); visit(i+1,remaining-1); pick.pop();
      }
    };
    for (let width = 1; width <= Math.min(maxWidth,products.length); width++) visit(0,width);
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
    const rawQuote = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const basicQuote = (rawQuote + cfg.manufacturingCostPerUnit) * (1 + cfg.markup);
    const compoundQuote = (2 * rawQuote + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
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
    const next = Math.max(floor, price * Math.exp(nextDirection * clamp(k, 0, 1) * response * scale));
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
    ((cfg.tier2BaseMarkup >= 0 ? cfg.tier2BaseMarkup : cfg.markup) + cfg.tier2MarkupPremium * (product.complexity-3)) *
    recipeMarginFactor(product, cfg.tier2CompoundStandardization, cfg.tier2ComplexitySpecialization, cfg.tier2MaterialBalance);
  const procurementProfile = (product,cfg,referenceCost) => {
    const markup = ((cfg.procurementBaseMarkup ?? .25) + (cfg.procurementMarkupPremium ?? .05) * (product.complexity-3)) *
      recipeMarginFactor(product, cfg.procurementCompoundStandardization, cfg.procurementComplexitySpecialization, cfg.procurementMaterialBalance);
    const baseline = .25;
    return Object.freeze({ markup, quantityFactor: cfg.tier2DemandFactor * baseline / (referenceCost * markup),
      valuation: 2 * referenceCost * (1+markup) / (1+baseline) });
  };
  const initialTier2Cost = (product, cfg) => {
    const raw = cfg.baseCost * cfg.dbar * (1 + cfg.markup);
    const basic = (raw + cfg.manufacturingCostPerUnit) * (1 + cfg.markup);
    const compound = (2 * raw + cfg.manufacturingCostPerUnit) *
      (1 + cfg.markup + cfg.compoundMarkupPremium);
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
    recipeKey,
    elementalComposition,
    T2_PRODUCT_BY_CODE,
    ECONOMY_DEFAULTS,
    finishedStockTarget,
    tier2StartingCash,
    TIER_BOUNDARIES,
    T2_SECTOR_WEIGHTS,
    T2_MAX_PRODUCTS_PER_FIRM, T1_BASIC_MACHINERY, T1_COMPOUND_MACHINERY, T2_ROUTE_SETUP, MIN_UNIT_PRICE,
    ELEMENTS,
    PRODUCTS,
    T2_PRODUCTS,
    T2_RECIPE_POOL,
    T2_RECIPE_BY_KEY,
    T2_MATERIAL_COVERAGE,
    T2_SECTORS,
    T2_NEED_TYPES,
    T2_SECTOR_DEFINITIONS,
    T2_ADJACENCY,
    relatedSector, portfolioOptions,
    T2_COMPLEXITY_COUNTS,
    t2Capacity,
    clamp,
    complexity,
    demandAtPrice,
    switchingCost,
    reliabilityScore,
    nextReliability,
    adaptivePrice,
    initialTier2Cost, referenceTier2Cost, tier2StartingMarkup, procurementProfile,
  });
})(typeof self !== 'undefined' ? self : globalThis);
