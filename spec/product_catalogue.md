<!-- Current rebalance: 200 invented markets, 220 reserved recipes; capital calibration in progress. -->
# Robotic Space Generation: complete product map

The Robotic Space Generation serves a far-future human society preparing for a major galactic war. Robotic factories manufacture goods for fleet readiness and civilian continuity, including shelter, nutrition, healthcare equipment, learning hardware, communications, transport and industry. One million external procurement agents represent final purchasing needs, rather than a demographic population. Every market supplies physical goods.

## Complete market space

All **420** possible C-3–C-5 processed-input recipes have catalogue names: **200 invented** and **220 reserved**. There is exactly one market per recipe, with one name and one code, T2-001 through T2-420. There are no unnamed routes, merged codes or aliases. The galactic catalogue replaces the earlier colony catalogue; historical product-code meanings are not preserved. Reload/reset starts the new world.

| Galactic sector | C-3 | C-4 | C-5 | Markets |
| --- | --- | --- | --- | --- |
| Power & Energy | 2 | 6 | 12 | 20 |
| Propulsion & Navigation | 2 | 6 | 12 | 20 |
| Spacecraft & Hulls | 2 | 6 | 12 | 20 |
| Habitats & Life Support | 2 | 6 | 12 | 20 |
| Robotics & Automation | 2 | 6 | 12 | 20 |
| Computing & Communications | 2 | 6 | 12 | 20 |
| Science & Diagnostics | 2 | 6 | 12 | 20 |
| Mining & Industry | 2 | 6 | 12 | 20 |
| Logistics & Provisioning | 2 | 6 | 12 | 20 |
| Defence & Rescue | 2 | 6 | 12 | 20 |
| **Total invented** | **20** | **60** | **120** | **200** |

Each sector starts with 20 invented goods; its remaining authored recipes are reserved. This is a catalogue organization choice, not a manufacturing rule, material gate or independent combinatorial count. Every sector has the same invented complexity mix. Galactic applications and manufacturing materials are independent dimensions.

## Why the total is 420

The ten Tier 1 inputs comprise four C-1 basics and six C-2 compounds. Inputs may repeat and ingredient order is ignored. Complexity counts ancestry: each basic contributes one and each compound two.

| Complexity | Basic-only recipes | One C-2 compound | Two C-2 compounds | Distinct recipes and markets |
| --- | --- | --- | --- | --- |
| C-3 | 20 | 24 | 0 | **44** |
| C-4 | 35 | 60 | 21 | **116** |
| C-5 | 56 | 120 | 84 | **260** |
| **Total** | **111** | **204** | **105** | **420** |

A + B equals B + A as separate inputs, but differs from an already manufactured compound (A+B). For actual material codes: W + A is a pair of basics; W+A is Synthetic Fibers. WF + A differs from W + FA even though their expanded ancestry matches. Flattening all intermediates would leave 111 raw compositions and lose distinct manufacturing routes. The model independently enumerates weighted multisets and verifies equality between the complete pool and catalogue recipe keys, with 200 active recipes.

## Material inputs

| Code | Tier 1 material | Complexity | Raw ancestry |
| --- | --- | --- | --- |
| W | Purified Water | C-1 | Water |
| E | Refined Minerals | C-1 | Earth |
| F | Energy Cells | C-1 | Fire |
| A | Chemical Feedstock | C-1 | Air |
| W+E | Ceramic Composite | C-2 | Water + Earth |
| W+F | Thermal Compounds | C-2 | Water + Fire |
| W+A | Synthetic Fibers | C-2 | Water + Air |
| E+F | Semiconductor Substrate | C-2 | Earth + Fire |
| E+A | Structural Polymers | C-2 | Earth + Air |
| F+A | Active Compounds | C-2 | Fire + Air |

Tier 0 extracts from Gaia, the resource environment, reports these units as Made and sells to Tier 1. Its reported COGS is the acquisition basis of elements sold, and gross profit is revenue minus COGS. Extraction spending and operating cash flow are reported separately. Tier 1 supplies companies exclusively; population demand for all ten materials is zero. Their customer metrics describe funded company orders, delivered inputs and stock shortages. Tier 2 buys all inputs from Tier 1 and supplies external galactic procurement.

## Company names

Tier 0 includes broad resource groups such as Atlas Resources and Axiom Extraction
Systems, alongside focused extractors such as Deepwell Ice Extraction and Zephyr
Gas Separation. Tier 1 has a corporate family for each material cohort: Aster
Water Systems, Meridian Mineral Refining, Helion Energy Cells, Cirrus Chemical
Works, Vanguard Ceramic Materials, Caldera Thermal Materials, Spindle Fiber
Industries, Lattice Semiconductor Materials, Truss Polymer Works and Catalyst
Active Materials. Each family has firms 001–100.

| Tier 2 sector | Company family |
| --- | --- |
| Power & Energy | Helion Power Industries |
| Propulsion & Navigation | Vector Drive Systems |
| Spacecraft & Hulls | Keel Spacecraft Works |
| Habitats & Life Support | Haven Habitat Systems |
| Robotics & Automation | Forge Automation |
| Computing & Communications | Relay Computing and Communications |
| Science & Diagnostics | Prism Scientific Instruments |
| Mining & Industry | Stratum Industrial Machinery |
| Logistics & Provisioning | Waypoint Supply Industries |
| Defence & Rescue | Sentinel Defence and Rescue Systems |

Tier 2 names include a unique five-digit firm number. Company search accepts that
displayed name as well as sectors and products. These labels describe businesses
supplying wartime readiness and civilian continuity; they confer no demand, cost,
capacity or profit advantage.

## Physical forms and economic interpretation

Consumables are replacement charges, cartridges and abrasive packs. Nutrition and healthcare are supplied through cultivation equipment, nutrient synthesis, preservation, diagnostic instruments and medical robots; education uses learning terminals, communications and simulation computers. These are manufactured goods, not services. Other C-3/C-4/C-5 outputs are classified as components, assemblies and systems respectively. These tags organize goods; all delivered units use the same inventory, production, purchase, payment and COGS rules. No rental, subscription, admission, consultation or upkeep service is sold. Repairs are represented by physical equipment, tools and replacement goods.

Recipes are abstract manufacturing requirements rather than literal chemistry or engineering bills of materials. The catalogue covers fleet readiness and civilian needs; it does not simulate orbital mechanics, colonization, installed fleets, maintenance schedules, demographic change or health. The fixed million-agent demand baseline remains price-sensitive, with heterogeneous sector baskets and unlimited final purchasing funds.

Each sector has equal initial demand weight. Every active good has equal selection
weight within its sector; benchmark quantity adjusts for recipe cost and nominal
markup so complex goods receive fewer unit orders and higher starting markups.
61,950 firms cover every one-to-four-product portfolio once in each sector,
providing 1,160 suppliers per product and 232,000 starting routes. Factory output
and storage are shared. Basic/compound refinery capacity remains 320/240 and
wholesale lots remain 1,000.

Prices respond to funded scarcity, unsold stock and costs. Price increases can
ration demand; they cannot restore physical capacity. Read fulfillment alongside
volume, quotes and price-suppressed demand. The 220 reserved recipes are inactive;
invention and marketing remain future work. See the [research protocol](market_logic_research.md)
for the uncompleted Age/ROE calibration and its fixed-rule requirements.

The historical, all-invented [0x2D0-tick full-population audit](../reports/robotic-space-generation-12345-720.json) passed with all 420 goods and all ten Tier 1 material markets producing and trading. The final 0x168 ticks fulfilled 99.46% of desired units, purchased 61,420.71 units per tick and had 49,977 Tier 2 firms trading. Utilization was 18.84%, realized gross margin was 11.76%, and maximum cash-ledger residual was below $0.000014. These are observed results for this seed and window, not demand targets or guarantees.

## Complete goods catalogue

### Power & Energy

Civilian and fleet power generation, storage, distribution and thermal control.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-001 · Reserved | Power Busbar | Components | C-3 | 3 × F | 3 × Fire |
| T2-002 · Reserved | Grid Charge Collector | Components | C-3 | E + 2 × F | Earth + 2 × Fire |
| T2-003 · Invented | Thermal Fuse | Components | C-3 | F + W+F | Water + 2 × Fire |
| T2-004 · Invented | Reactor Coolant Cartridge | Consumables | C-3 | E + F + A | Earth + Fire + Air |
| T2-005 · Reserved | Energy Cell Coupler | Components | C-3 | W + W+F | 2 × Water + Fire |
| T2-006 · Reserved | Battery Array | Assemblies | C-4 | 4 × F | 4 × Fire |
| T2-007 · Reserved | Power Converter | Assemblies | C-4 | E + 3 × F | Earth + 3 × Fire |
| T2-008 · Invented | Heat Exchanger | Assemblies | C-4 | 2 × F + W+F | Water + 3 × Fire |
| T2-009 · Reserved | Capacitor Bank | Assemblies | C-4 | W + E + 2 × F | Water + Earth + 2 × Fire |
| T2-010 · Invented | Solar Tile | Assemblies | C-4 | E + 2 × F + A | Earth + 2 × Fire + Air |
| T2-011 · Reserved | Radiator Panel | Assemblies | C-4 | 2 × F + 2 × A | 2 × Fire + 2 × Air |
| T2-012 · Invented | Induction Coil | Assemblies | C-4 | 2 × F + E+A | Earth + 2 × Fire + Air |
| T2-013 · Invented | Turbine Rotor | Assemblies | C-4 | W + F + W+F | 2 × Water + 2 × Fire |
| T2-014 · Invented | Reactor Coolant Pump | Assemblies | C-4 | E + F + W+F | Water + Earth + 2 × Fire |
| T2-015 · Reserved | Superconducting Cable | Assemblies | C-4 | 2 × W+F | 2 × Water + 2 × Fire |
| T2-016 · Reserved | Fuel Pellet Magazine | Assemblies | C-4 | 2 × W + F + A | 2 × Water + Fire + Air |
| T2-017 · Invented | Power Distribution Module | Assemblies | C-4 | W+F + F+A | Water + 2 × Fire + Air |
| T2-018 · Reserved | Fusion Reactor Core | Systems | C-5 | 5 × F | 5 × Fire |
| T2-019 · Reserved | Antimatter Containment Chamber | Systems | C-5 | E + 4 × F | Earth + 4 × Fire |
| T2-020 · Reserved | Orbital Solar Collector | Systems | C-5 | 3 × F + W+F | Water + 4 × Fire |
| T2-021 · Invented | Deep Space Power Plant | Systems | C-5 | W + E + 3 × F | Water + Earth + 3 × Fire |
| T2-022 · Invented | Station Battery Vault | Systems | C-5 | E + 3 × F + A | Earth + 3 × Fire + Air |
| T2-023 · Reserved | High Flux Reactor | Systems | C-5 | 2 × E + 3 × F | 2 × Earth + 3 × Fire |
| T2-024 · Reserved | Field Generator Pod | Systems | C-5 | 3 × F + W+E | Water + Earth + 3 × Fire |
| T2-025 · Invented | Thermal Recovery Array | Systems | C-5 | W + 2 × F + W+F | 2 × Water + 3 × Fire |
| T2-026 · Invented | Beam Power Transmitter | Systems | C-5 | E + 2 × F + W+F | Water + Earth + 3 × Fire |
| T2-027 · Invented | Beam Power Receiver | Systems | C-5 | 2 × F + A + W+F | Water + 3 × Fire + Air |
| T2-028 · Reserved | Stellar Flux Collector | Systems | C-5 | F + 2 × W+F | 2 × Water + 3 × Fire |
| T2-029 · Invented | Isotope Generator | Systems | C-5 | W + E + 2 × F + A | Water + Earth + 2 × Fire + Air |
| T2-030 · Reserved | Shipboard Microreactor | Systems | C-5 | 2 × W + 2 × F + A | 2 × Water + 2 × Fire + Air |
| T2-031 · Reserved | High Voltage Switching Rack | Systems | C-5 | W + 2 × F + 2 × A | Water + 2 × Fire + 2 × Air |
| T2-032 · Reserved | Reactor Shield Assembly | Systems | C-5 | W + 2 × F + W+A | 2 × Water + 2 × Fire + Air |
| T2-033 · Invented | Radiator Wing | Systems | C-5 | 2 × E + 2 × F + A | 2 × Earth + 2 × Fire + Air |
| T2-034 · Reserved | Cryogenic Energy Reservoir | Systems | C-5 | E + 2 × F + W+A | Water + Earth + 2 × Fire + Air |
| T2-035 · Invented | Flywheel Storage Unit | Systems | C-5 | 2 × F + A + W+E | Water + Earth + 2 × Fire + Air |
| T2-036 · Invented | Magnetic Energy Store | Systems | C-5 | F + W+F + F+A | Water + 3 × Fire + Air |
| T2-037 · Invented | Hospital Backup Generator | Systems | C-5 | W + E + F + W+F | 2 × Water + Earth + 2 × Fire |
| T2-038 · Invented | Grid Synchronization Controller | Systems | C-5 | E + F + A + W+F | Water + Earth + 2 × Fire + Air |
| T2-039 · Reserved | Plasma Energy Converter | Systems | C-5 | 2 × W + F + W+F | 3 × Water + 2 × Fire |
| T2-040 · Invented | Reactor Ignition Assembly | Systems | C-5 | F + 2 × A + W+F | Water + 2 × Fire + 2 × Air |
| T2-041 · Reserved | Power Regulation Rack | Systems | C-5 | F + W+F + W+A | 2 × Water + 2 × Fire + Air |
| T2-042 · Reserved | Waste Heat Recovery Plant | Systems | C-5 | W + 2 × W+F | 3 × Water + 2 × Fire |

### Propulsion & Navigation

Civilian transport and fleet propulsion, maneuvering and route control.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-043 · Reserved | Thruster Nozzle | Components | C-3 | W + 2 × F | Water + 2 × Fire |
| T2-044 · Reserved | Propellant Cartridge | Consumables | C-3 | 2 × F + A | 2 × Fire + Air |
| T2-045 · Reserved | Reaction Mass Tank | Components | C-3 | F + F+A | 2 × Fire + Air |
| T2-046 · Invented | Thrust Bearing | Components | C-3 | 2 × W + F | 2 × Water + Fire |
| T2-047 · Invented | Ignition Electrode | Components | C-3 | A + F+A | Fire + 2 × Air |
| T2-048 · Reserved | Maneuvering Thruster | Assemblies | C-4 | W + 3 × F | Water + 3 × Fire |
| T2-049 · Reserved | Ion Accelerator | Assemblies | C-4 | 3 × F + A | 3 × Fire + Air |
| T2-050 · Reserved | Plasma Injector | Assemblies | C-4 | 2 × F + F+A | 3 × Fire + Air |
| T2-051 · Invented | Fuel Metering Valve | Assemblies | C-4 | W + 2 × F + A | Water + 2 × Fire + Air |
| T2-052 · Reserved | Navigation Gyroscope | Assemblies | C-4 | 2 × W + 2 × F | 2 × Water + 2 × Fire |
| T2-053 · Invented | Inertial Reference Unit | Assemblies | C-4 | 2 × F + W+E | Water + Earth + 2 × Fire |
| T2-054 · Invented | Magnetic Nozzle | Assemblies | C-4 | W + F + F+A | Water + 2 × Fire + Air |
| T2-055 · Invented | Reaction Wheel | Assemblies | C-4 | E + F + F+A | Earth + 2 × Fire + Air |
| T2-056 · Invented | Trajectory Computer | Assemblies | C-4 | F + A + F+A | 2 × Fire + 2 × Air |
| T2-057 · Reserved | Star Tracker | Assemblies | C-4 | 2 × F+A | 2 × Fire + 2 × Air |
| T2-058 · Invented | Thrust Vector Actuator | Assemblies | C-4 | W + F + 2 × A | Water + Fire + 2 × Air |
| T2-059 · Reserved | Propellant Preheater | Assemblies | C-4 | 2 × W + F+A | 2 × Water + Fire + Air |
| T2-060 · Reserved | Ion Drive Assembly | Systems | C-5 | W + 4 × F | Water + 4 × Fire |
| T2-061 · Reserved | Plasma Drive Assembly | Systems | C-5 | 4 × F + A | 4 × Fire + Air |
| T2-062 · Reserved | Fusion Torch Engine | Systems | C-5 | 3 × F + F+A | 4 × Fire + Air |
| T2-063 · Reserved | Antimatter Drive Chamber | Systems | C-5 | W + 3 × F + A | Water + 3 × Fire + Air |
| T2-064 · Reserved | Solar Sail Rig | Systems | C-5 | 2 × W + 3 × F | 2 × Water + 3 × Fire |
| T2-065 · Reserved | Magnetic Sail Rig | Systems | C-5 | 3 × F + 2 × A | 3 × Fire + 2 × Air |
| T2-066 · Reserved | Gravity Assist Navigation Rack | Systems | C-5 | 3 × F + W+A | Water + 3 × Fire + Air |
| T2-067 · Reserved | Deep Space Guidance Array | Systems | C-5 | W + 2 × F + F+A | Water + 3 × Fire + Air |
| T2-068 · Reserved | Orbital Transfer Engine | Systems | C-5 | E + 2 × F + F+A | Earth + 3 × Fire + Air |
| T2-069 · Invented | Landing Engine Cluster | Systems | C-5 | 2 × F + A + F+A | 3 × Fire + 2 × Air |
| T2-070 · Reserved | Launch Booster Module | Systems | C-5 | F + 2 × F+A | 3 × Fire + 2 × Air |
| T2-071 · Invented | Asteroid Tug Drive | Systems | C-5 | 2 × W + E + 2 × F | 2 × Water + Earth + 2 × Fire |
| T2-072 · Invented | Station Keeping Thruster Bank | Systems | C-5 | W + 2 × E + 2 × F | Water + 2 × Earth + 2 × Fire |
| T2-073 · Reserved | Interplanetary Cruise Engine | Systems | C-5 | W + 2 × F + W+E | 2 × Water + Earth + 2 × Fire |
| T2-074 · Invented | Propellant Recycling Plant | Systems | C-5 | W + 2 × F + E+A | Water + Earth + 2 × Fire + Air |
| T2-075 · Invented | High Impulse Maneuvering Pack | Systems | C-5 | E + 2 × F + 2 × A | Earth + 2 × Fire + 2 × Air |
| T2-076 · Invented | Precision Docking Drive | Systems | C-5 | E + 2 × F + E+A | 2 × Earth + 2 × Fire + Air |
| T2-077 · Invented | Atmospheric Entry Control Pack | Systems | C-5 | 2 × F + A + E+A | Earth + 2 × Fire + 2 × Air |
| T2-078 · Reserved | Autonomous Flight Controller | Systems | C-5 | 3 × W + 2 × F | 3 × Water + 2 × Fire |
| T2-079 · Invented | Relativistic Navigation Array | Systems | C-5 | W + E + F + F+A | Water + Earth + 2 × Fire + Air |
| T2-080 · Invented | Drive Thermal Management Pack | Systems | C-5 | W + F + A + F+A | Water + 2 × Fire + 2 × Air |
| T2-081 · Invented | Fuel Injection Manifold | Systems | C-5 | E + F + A + F+A | Earth + 2 × Fire + 2 × Air |
| T2-082 · Invented | Engine Test Chamber | Systems | C-5 | 2 × W + F + F+A | 2 × Water + 2 × Fire + Air |
| T2-083 · Reserved | Long Range Flight Computer | Systems | C-5 | F + 2 × A + F+A | 2 × Fire + 3 × Air |
| T2-084 · Invented | Emergency Return Drive | Systems | C-5 | W + 2 × F+A | Water + 2 × Fire + 2 × Air |

### Spacecraft & Hulls

Transport, evacuation and fleet spacecraft structures, pressure vessels and orbital platforms.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-085 · Reserved | Hull Plate | Components | C-3 | 3 × E | 3 × Earth |
| T2-086 · Reserved | Frame Spar | Components | C-3 | 2 × E + F | 2 × Earth + Fire |
| T2-087 · Invented | Pressure Seal | Components | C-3 | W + E + F | Water + Earth + Fire |
| T2-088 · Invented | Structural Rivet | Components | C-3 | W + E + A | Water + Earth + Air |
| T2-089 · Reserved | Bulkhead Panel | Assemblies | C-4 | 4 × E | 4 × Earth |
| T2-090 · Reserved | Pressure Hatch | Assemblies | C-4 | 3 × E + F | 3 × Earth + Fire |
| T2-091 · Reserved | Docking Collar | Assemblies | C-4 | 2 × E + E+A | 3 × Earth + Air |
| T2-092 · Reserved | Window Shield | Assemblies | C-4 | 2 × E + W+E | Water + 3 × Earth |
| T2-093 · Invented | Landing Strut | Assemblies | C-4 | W + 2 × E + F | Water + 2 × Earth + Fire |
| T2-094 · Invented | Cargo Bay Door | Assemblies | C-4 | 2 × E + F + A | 2 × Earth + Fire + Air |
| T2-095 · Invented | Hull Sensor Strip | Assemblies | C-4 | 2 × E + 2 × A | 2 × Earth + 2 × Air |
| T2-096 · Reserved | Debris Bumper | Assemblies | C-4 | 2 × E + E+F | 3 × Earth + Fire |
| T2-097 · Invented | Structural Truss | Assemblies | C-4 | W + E + F + A | Water + Earth + Fire + Air |
| T2-098 · Invented | Fuel Tank Shell | Assemblies | C-4 | 2 × W + E + F | 2 × Water + Earth + Fire |
| T2-099 · Invented | Insulated Hull Panel | Assemblies | C-4 | W + E + 2 × A | Water + Earth + 2 × Air |
| T2-100 · Reserved | Radiation Resistant Window | Assemblies | C-4 | W + A + W+F | 2 × Water + Fire + Air |
| T2-101 · Reserved | Orbital Platform Frame | Systems | C-5 | 5 × E | 5 × Earth |
| T2-102 · Reserved | Reconnaissance Ship Hull | Systems | C-5 | 4 × E + F | 4 × Earth + Fire |
| T2-103 · Reserved | Freighter Hull | Systems | C-5 | 3 × E + E+A | 4 × Earth + Air |
| T2-104 · Reserved | Survey Ship Hull | Systems | C-5 | 3 × E + W+E | Water + 4 × Earth |
| T2-105 · Reserved | Mining Barge Hull | Systems | C-5 | W + 3 × E + F | Water + 3 × Earth + Fire |
| T2-106 · Reserved | Orbital Tug Hull | Systems | C-5 | 3 × E + F + A | 3 × Earth + Fire + Air |
| T2-107 · Reserved | Patrol Cruiser Hull | Systems | C-5 | 3 × E + 2 × F | 3 × Earth + 2 × Fire |
| T2-108 · Reserved | Launch Vehicle Body | Systems | C-5 | 3 × E + W+A | Water + 3 × Earth + Air |
| T2-109 · Reserved | Reentry Capsule Shell | Systems | C-5 | W + 2 × E + E+A | Water + 3 × Earth + Air |
| T2-110 · Reserved | Station Spine | Systems | C-5 | 2 × E + F + E+A | 3 × Earth + Fire + Air |
| T2-111 · Invented | Docking Hub Structure | Systems | C-5 | 2 × E + A + E+A | 3 × Earth + 2 × Air |
| T2-112 · Invented | Shipyard Gantry | Systems | C-5 | W + 2 × E + W+E | 2 × Water + 3 × Earth |
| T2-113 · Reserved | Medical Transport Chassis | Systems | C-5 | 2 × E + F + W+E | Water + 3 × Earth + Fire |
| T2-114 · Invented | Rotating Station Ring | Systems | C-5 | 2 × E + A + W+E | Water + 3 × Earth + Air |
| T2-115 · Invented | High Pressure Vessel | Systems | C-5 | W + 2 × E + F + A | Water + 2 × Earth + Fire + Air |
| T2-116 · Reserved | Cryogenic Tank Assembly | Systems | C-5 | 2 × W + 2 × E + F | 2 × Water + 2 × Earth + Fire |
| T2-117 · Invented | Deployable Ship Radiator Frame | Systems | C-5 | W + 2 × E + 2 × A | Water + 2 × Earth + 2 × Air |
| T2-118 · Invented | Meteoroid Shield Array | Systems | C-5 | W + 2 × E + E+F | Water + 3 × Earth + Fire |
| T2-119 · Reserved | Deep Space Hull Section | Systems | C-5 | 2 × E + F + W+A | Water + 2 × Earth + Fire + Air |
| T2-120 · Invented | Repair Dock Frame | Systems | C-5 | 3 × W + 2 × E | 3 × Water + 2 × Earth |
| T2-121 · Invented | Heavy Lift Landing Gear | Systems | C-5 | E + W+E + W+F | 2 × Water + 2 × Earth + Fire |
| T2-122 · Invented | Variable Geometry Wing | Systems | C-5 | E + W+E + F+A | Water + 2 × Earth + Fire + Air |
| T2-123 · Invented | Atmospheric Skimmer Body | Systems | C-5 | 2 × W + E + F + A | 2 × Water + Earth + Fire + Air |
| T2-124 · Invented | Fleet Carrier Deck | Systems | C-5 | W + E + F + 2 × A | Water + Earth + Fire + 2 × Air |
| T2-125 · Invented | Evacuation Craft Hull | Systems | C-5 | W + E + A + W+F | 2 × Water + Earth + Fire + Air |
| T2-126 · Reserved | Orbital Drydock Shell | Systems | C-5 | 2 × W + E + W+F | 3 × Water + Earth + Fire |

### Habitats & Life Support

Shelter, food cultivation, water recovery, atmosphere control and physical care facilities.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-127 · Invented | Habitat Tile | Components | C-3 | W + W+E | 2 × Water + Earth |
| T2-128 · Invented | Habitat Anchor Bolt | Components | C-3 | E + W+E | Water + 2 × Earth |
| T2-129 · Reserved | Shelter Insulation Blanket | Components | C-3 | F + W+E | Water + Earth + Fire |
| T2-130 · Reserved | Life Support Mount | Components | C-3 | 2 × W + E | 2 × Water + Earth |
| T2-131 · Reserved | Pressure Wall | Assemblies | C-4 | 2 × W+E | 2 × Water + 2 × Earth |
| T2-132 · Reserved | Airlock Door | Assemblies | C-4 | 2 × W + W+E | 3 × Water + Earth |
| T2-133 · Invented | Habitat Floor Deck | Assemblies | C-4 | W+E + E+A | Water + 2 × Earth + Air |
| T2-134 · Invented | Water Distribution Conduit | Assemblies | C-4 | W + E + W+E | 2 × Water + 2 × Earth |
| T2-135 · Reserved | Radiation Screen | Assemblies | C-4 | W + F + W+E | 2 × Water + Earth + Fire |
| T2-136 · Invented | Light Panel | Assemblies | C-4 | W + A + W+E | 2 × Water + Earth + Air |
| T2-137 · Reserved | Atmosphere Reservoir | Assemblies | C-4 | E + F + W+E | Water + 2 × Earth + Fire |
| T2-138 · Invented | Shelter Thermal Curtain | Assemblies | C-4 | E + A + W+E | Water + 2 × Earth + Air |
| T2-139 · Reserved | Hydroponic Rack Frame | Assemblies | C-4 | 3 × W + F | 3 × Water + Fire |
| T2-140 · Invented | Habitat Window | Assemblies | C-4 | W+E + W+F | 2 × Water + Earth + Fire |
| T2-141 · Invented | Water Recovery Cartridge | Assemblies | C-4 | W+E + F+A | Water + Earth + Fire + Air |
| T2-142 · Reserved | Air Circulation Fan | Assemblies | C-4 | 2 × W + W+F | 3 × Water + Fire |
| T2-143 · Reserved | Habitat Pressure Module | Systems | C-5 | W + 2 × W+E | 3 × Water + 2 × Earth |
| T2-144 · Invented | Orbital Habitat Shell | Systems | C-5 | W + W+E + E+A | 2 × Water + 2 × Earth + Air |
| T2-145 · Reserved | Civilian Outpost Module | Systems | C-5 | 3 × W + W+E | 4 × Water + Earth |
| T2-146 · Reserved | Rotating Habitat Hub | Systems | C-5 | E + 2 × W+E | 2 × Water + 3 × Earth |
| T2-147 · Reserved | Asteroid Settlement Anchor | Systems | C-5 | F + 2 × W+E | 2 × Water + 2 × Earth + Fire |
| T2-148 · Reserved | Deep Space Shelter | Systems | C-5 | A + 2 × W+E | 2 × Water + 2 × Earth + Air |
| T2-149 · Reserved | Worker Quarters Module | Systems | C-5 | 2 × W + E + W+E | 3 × Water + 2 × Earth |
| T2-150 · Reserved | Food Cultivation Chamber | Systems | C-5 | 2 × W + F + W+E | 3 × Water + Earth + Fire |
| T2-151 · Invented | Hospital Isolation Module | Systems | C-5 | 2 × W + A + W+E | 3 × Water + Earth + Air |
| T2-152 · Invented | Greenhouse Dome | Systems | C-5 | E + W+E + E+A | Water + 3 × Earth + Air |
| T2-153 · Invented | Subsurface Outpost Liner | Systems | C-5 | F + W+E + E+A | Water + 2 × Earth + Fire + Air |
| T2-154 · Invented | Orbital Elevator Anchor | Systems | C-5 | A + W+E + E+A | Water + 2 × Earth + 2 × Air |
| T2-155 · Reserved | Space Elevator Cable Drum | Systems | C-5 | W + E + F + W+E | 2 × Water + 2 × Earth + Fire |
| T2-156 · Invented | Solar Shade Assembly | Systems | C-5 | W + E + A + W+E | 2 × Water + 2 × Earth + Air |
| T2-157 · Invented | Nutrient Synthesis Plant | Systems | C-5 | W + F + A + W+E | 2 × Water + Earth + Fire + Air |
| T2-158 · Invented | Habitat Thermal Buffer Wall | Systems | C-5 | W + 2 × A + W+E | 2 × Water + Earth + 2 × Air |
| T2-159 · Reserved | Modular Station Extension | Systems | C-5 | W + W+E + W+F | 3 × Water + Earth + Fire |
| T2-160 · Invented | Emergency Housing Mold | Systems | C-5 | W + W+E + F+A | 2 × Water + Earth + Fire + Air |
| T2-161 · Invented | Atmosphere Control Rack | Systems | C-5 | E + F + A + W+E | Water + 2 × Earth + Fire + Air |
| T2-162 · Reserved | Water Recycling Plant | Systems | C-5 | 3 × W + E + F | 3 × Water + Earth + Fire |
| T2-163 · Reserved | Settlement Power Corridor | Systems | C-5 | 3 × W + F + A | 3 × Water + Fire + Air |
| T2-164 · Reserved | Deployable Landing Platform | Systems | C-5 | F + W+E + W+F | 2 × Water + Earth + 2 × Fire |
| T2-165 · Reserved | Station Expansion Truss | Systems | C-5 | F + W+E + F+A | Water + Earth + 2 × Fire + Air |
| T2-166 · Invented | Orbital Ring Segment | Systems | C-5 | A + W+E + W+F | 2 × Water + Earth + Fire + Air |
| T2-167 · Reserved | Patient Recovery Module | Systems | C-5 | 3 × W + F+A | 3 × Water + Fire + Air |
| T2-168 · Invented | Evacuation Shelter Capsule | Systems | C-5 | 2 × W + A + W+F | 3 × Water + Fire + Air |

### Robotics & Automation

Industrial, repair, medical and rescue robots, actuators, tooling and autonomous machinery.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-169 · Reserved | Robot Joint | Components | C-3 | W + E+A | Water + Earth + Air |
| T2-170 · Invented | Actuator Rod | Components | C-3 | E + E+A | 2 × Earth + Air |
| T2-171 · Invented | Prosthetic Grip Pad | Components | C-3 | A + E+A | Earth + 2 × Air |
| T2-172 · Reserved | Motor Winding | Components | C-3 | W + F+A | Water + Fire + Air |
| T2-173 · Reserved | Precision Actuator Bearing | Components | C-3 | E + 2 × A | Earth + 2 × Air |
| T2-174 · Invented | Robot Hand | Assemblies | C-4 | 2 × E+A | 2 × Earth + 2 × Air |
| T2-175 · Invented | Tool Changer | Assemblies | C-4 | E+F + E+A | 2 × Earth + Fire + Air |
| T2-176 · Invented | Locomotion Wheel | Assemblies | C-4 | E+A + F+A | Earth + Fire + 2 × Air |
| T2-177 · Reserved | Manipulator Arm | Assemblies | C-4 | W + F + E+A | Water + Earth + Fire + Air |
| T2-178 · Reserved | Force Feedback Unit | Assemblies | C-4 | E + F + E+A | 2 × Earth + Fire + Air |
| T2-179 · Reserved | Hydraulic Actuator | Assemblies | C-4 | E + A + E+A | 2 × Earth + 2 × Air |
| T2-180 · Reserved | Magnetic Gripper | Assemblies | C-4 | F + A + E+A | Earth + Fire + 2 × Air |
| T2-181 · Reserved | Precision Servo | Assemblies | C-4 | 2 × A + E+A | Earth + 3 × Air |
| T2-182 · Invented | Robot Vision Head | Assemblies | C-4 | W+F + E+A | Water + Earth + Fire + Air |
| T2-183 · Invented | Autonomous Control Board | Assemblies | C-4 | E+F + F+A | Earth + 2 × Fire + Air |
| T2-184 · Invented | Joint Cooling Jacket | Assemblies | C-4 | W + A + F+A | Water + Fire + 2 × Air |
| T2-185 · Reserved | Manipulator Wrist | Assemblies | C-4 | 2 × A + F+A | Fire + 3 × Air |
| T2-186 · Reserved | Assembly Robot | Systems | C-5 | W + 2 × E+A | Water + 2 × Earth + 2 × Air |
| T2-187 · Reserved | Welding Robot | Systems | C-5 | E + 2 × E+A | 3 × Earth + 2 × Air |
| T2-188 · Reserved | Inspection Robot | Systems | C-5 | F + 2 × E+A | 2 × Earth + Fire + 2 × Air |
| T2-189 · Reserved | Excavation Robot | Systems | C-5 | W + E+F + E+A | Water + 2 × Earth + Fire + Air |
| T2-190 · Invented | Hull Repair Robot | Systems | C-5 | E + E+F + E+A | 3 × Earth + Fire + Air |
| T2-191 · Invented | Cargo Handling Robot | Systems | C-5 | F + E+F + E+A | 2 × Earth + 2 × Fire + Air |
| T2-192 · Invented | Microassembly Robot | Systems | C-5 | A + E+F + E+A | 2 × Earth + Fire + 2 × Air |
| T2-193 · Reserved | Vacuum Work Robot | Systems | C-5 | W + E+A + F+A | Water + Earth + Fire + 2 × Air |
| T2-194 · Reserved | Survey Walker | Systems | C-5 | E + E+A + F+A | 2 × Earth + Fire + 2 × Air |
| T2-195 · Reserved | Maintenance Crawler | Systems | C-5 | F + E+A + F+A | Earth + 2 × Fire + 2 × Air |
| T2-196 · Invented | Station Construction Robot | Systems | C-5 | A + E+A + F+A | Earth + Fire + 3 × Air |
| T2-197 · Invented | Precision Machining Robot | Systems | C-5 | W + E + F + E+A | Water + 2 × Earth + Fire + Air |
| T2-198 · Invented | Autonomous Foundry Robot | Systems | C-5 | W + F + A + E+A | Water + Earth + Fire + 2 × Air |
| T2-199 · Invented | Mine Rescue Robot | Systems | C-5 | E + F + A + E+A | 2 × Earth + Fire + 2 × Air |
| T2-200 · Reserved | Asteroid Anchoring Robot | Systems | C-5 | W + 2 × A + E+A | Water + Earth + 3 × Air |
| T2-201 · Invented | Robotic Fabrication Cell | Systems | C-5 | W + W+F + E+A | 2 × Water + Earth + Fire + Air |
| T2-202 · Invented | Surgical Robot Manipulator | Systems | C-5 | W + E+F + F+A | Water + Earth + 2 × Fire + Air |
| T2-203 · Invented | Magnetic Hull Repair Robot | Systems | C-5 | E + 2 × A + E+A | 2 × Earth + 3 × Air |
| T2-204 · Reserved | Radiation Hardened Robot | Systems | C-5 | E + W+F + E+A | Water + 2 × Earth + Fire + Air |
| T2-205 · Invented | Modular Robot Chassis | Systems | C-5 | E + E+F + F+A | 2 × Earth + 2 × Fire + Air |
| T2-206 · Reserved | Swarm Coordination Unit | Systems | C-5 | F + 2 × A + E+A | Earth + Fire + 3 × Air |
| T2-207 · Reserved | Robot Refurbishment Rack | Systems | C-5 | F + W+F + E+A | Water + Earth + 2 × Fire + Air |
| T2-208 · Invented | Autonomous Assembly Line | Systems | C-5 | A + W+F + E+A | Water + Earth + Fire + 2 × Air |
| T2-209 · Reserved | Heavy Lift Exoskeleton | Systems | C-5 | 3 × A + E+A | Earth + 4 × Air |
| T2-210 · Reserved | Medical Assistance Robot | Systems | C-5 | A + 2 × F+A | 2 × Fire + 3 × Air |

### Computing & Communications

Civilian and fleet processors, archives, networks, communications and learning hardware.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-211 · Invented | Circuit Trace | Components | C-3 | F + E+F | Earth + 2 × Fire |
| T2-212 · Reserved | Memory Wafer | Components | C-3 | W + E+F | Water + Earth + Fire |
| T2-213 · Invented | Optical Fiber | Components | C-3 | W + F + A | Water + Fire + Air |
| T2-214 · Reserved | Processor Substrate | Components | C-3 | F + 2 × A | Fire + 2 × Air |
| T2-215 · Reserved | Logic Board | Assemblies | C-4 | 2 × F + E+F | Earth + 3 × Fire |
| T2-216 · Invented | Learning Terminal Memory Bank | Assemblies | C-4 | W + F + E+F | Water + Earth + 2 × Fire |
| T2-217 · Invented | Civilian Network Transceiver | Assemblies | C-4 | E + F + E+F | 2 × Earth + 2 × Fire |
| T2-218 · Invented | Signal Amplifier | Assemblies | C-4 | F + A + E+F | Earth + 2 × Fire + Air |
| T2-219 · Reserved | Network Switch | Assemblies | C-4 | 2 × E + 2 × F | 2 × Earth + 2 × Fire |
| T2-220 · Reserved | Data Buffer | Assemblies | C-4 | 2 × F + W+A | Water + 2 × Fire + Air |
| T2-221 · Invented | Clock Module | Assemblies | C-4 | W+F + E+F | Water + Earth + 2 × Fire |
| T2-222 · Invented | Quantum Control Chip | Assemblies | C-4 | W + E + E+F | Water + 2 × Earth + Fire |
| T2-223 · Reserved | Thermal Processor Plate | Assemblies | C-4 | F + A + W+F | Water + 2 × Fire + Air |
| T2-224 · Invented | Archive Integrity Board | Assemblies | C-4 | W+A + E+F | Water + Earth + Fire + Air |
| T2-225 · Reserved | Antenna Tile | Assemblies | C-4 | E + F + 2 × A | Earth + Fire + 2 × Air |
| T2-226 · Reserved | Timing Reference Unit | Assemblies | C-4 | 2 × A + W+F | Water + Fire + 2 × Air |
| T2-227 · Reserved | Core Processor Rack | Systems | C-5 | 3 × F + E+F | Earth + 4 × Fire |
| T2-228 · Reserved | Navigation Compute Rack | Systems | C-5 | F + 2 × E+F | 2 × Earth + 3 × Fire |
| T2-229 · Reserved | Autonomous Planning Core | Systems | C-5 | W + 2 × F + E+F | Water + Earth + 3 × Fire |
| T2-230 · Reserved | Radiation Hardened Computer | Systems | C-5 | E + 2 × F + E+F | 2 × Earth + 3 × Fire |
| T2-231 · Reserved | Quantum Processing Module | Systems | C-5 | 2 × F + A + E+F | Earth + 3 × Fire + Air |
| T2-232 · Reserved | Settlement Compute Node | Systems | C-5 | F + W+F + E+F | Water + Earth + 3 × Fire |
| T2-233 · Reserved | Fleet Coordination Server | Systems | C-5 | 3 × F + E+A | Earth + 3 × Fire + Air |
| T2-234 · Invented | Orbital Communication Relay | Systems | C-5 | W + E + F + E+F | Water + 2 × Earth + 2 × Fire |
| T2-235 · Invented | Laser Communication Terminal | Systems | C-5 | W + F + A + E+F | Water + Earth + 2 × Fire + Air |
| T2-236 · Invented | Deep Space Radio Array | Systems | C-5 | E + F + A + E+F | 2 × Earth + 2 × Fire + Air |
| T2-237 · Reserved | Interplanetary Router | Systems | C-5 | 2 × W + F + E+F | 2 × Water + Earth + 2 × Fire |
| T2-238 · Reserved | Cultural Archive Vault | Systems | C-5 | 2 × E + F + E+F | 3 × Earth + 2 × Fire |
| T2-239 · Reserved | High Bandwidth Link Module | Systems | C-5 | F + W+A + E+F | Water + Earth + 2 × Fire + Air |
| T2-240 · Invented | Encrypted Communication Rack | Systems | C-5 | F + E+F + F+A | Earth + 3 × Fire + Air |
| T2-241 · Invented | Signal Routing Matrix | Systems | C-5 | W + W+F + E+F | 2 × Water + Earth + 2 × Fire |
| T2-242 · Reserved | Photonic Compute Module | Systems | C-5 | E + 2 × F + W+E | Water + 2 × Earth + 2 × Fire |
| T2-243 · Invented | Sensor Fusion Computer | Systems | C-5 | E + W+F + E+F | Water + 2 × Earth + 2 × Fire |
| T2-244 · Invented | Life Support Control Computer | Systems | C-5 | A + W+F + E+F | Water + Earth + 2 × Fire + Air |
| T2-245 · Invented | Industrial Control Server | Systems | C-5 | 2 × F + 3 × A | 2 × Fire + 3 × Air |
| T2-246 · Invented | Instruction Simulation Computer | Systems | C-5 | W + F + A + W+F | 2 × Water + 2 × Fire + Air |
| T2-247 · Reserved | Cryogenic Compute Cabinet | Systems | C-5 | 2 × W + E + E+F | 2 × Water + 2 × Earth + Fire |
| T2-248 · Invented | Fault Tolerant Memory Array | Systems | C-5 | W + W+A + E+F | 2 × Water + Earth + Fire + Air |
| T2-249 · Invented | Clock Synchronization Array | Systems | C-5 | E + W+A + E+F | Water + 2 × Earth + Fire + Air |
| T2-250 · Reserved | Remote Learning Terminal | Systems | C-5 | 3 × W + E+F | 3 × Water + Earth + Fire |
| T2-251 · Invented | Communication Beam Director | Systems | C-5 | 2 × W + F + 2 × A | 2 × Water + Fire + 2 × Air |
| T2-252 · Reserved | Public Archive Recovery Appliance | Systems | C-5 | A + 2 × W+F | 2 × Water + 2 × Fire + Air |

### Science & Diagnostics

Scientific instruments, medical diagnostics, environmental monitoring and survey equipment.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-253 · Invented | Sensor Lens | Components | C-3 | A + E+F | Earth + Fire + Air |
| T2-254 · Reserved | Detector Film | Components | C-3 | E + E+F | 2 × Earth + Fire |
| T2-255 · Reserved | Probe Casing | Components | C-3 | A + W+E | Water + Earth + Air |
| T2-256 · Reserved | Sterile Sampling Vial | Components | C-3 | 3 × A | 3 × Air |
| T2-257 · Invented | Diagnostic Calibration Target | Components | C-3 | A + W+F | Water + Fire + Air |
| T2-258 · Reserved | Spectrometer Head | Assemblies | C-4 | 2 × E+F | 2 × Earth + 2 × Fire |
| T2-259 · Reserved | Radar Antenna | Assemblies | C-4 | 2 × A + E+F | Earth + Fire + 2 × Air |
| T2-260 · Invented | Lidar Emitter | Assemblies | C-4 | W+E + E+F | Water + 2 × Earth + Fire |
| T2-261 · Invented | Thermal Diagnostic Detector | Assemblies | C-4 | W + A + E+F | Water + Earth + Fire + Air |
| T2-262 · Invented | Magnetic Field Sensor | Assemblies | C-4 | E + A + E+F | 2 × Earth + Fire + Air |
| T2-263 · Reserved | Seismic Sensor | Assemblies | C-4 | 2 × A + W+E | Water + Earth + 2 × Air |
| T2-264 · Reserved | Radiation Counter | Assemblies | C-4 | 4 × A | 4 × Air |
| T2-265 · Invented | Breathing Gas Analyzer | Assemblies | C-4 | F + A + W+E | Water + Earth + Fire + Air |
| T2-266 · Reserved | Thermal Imaging Unit | Assemblies | C-4 | 2 × W + E+F | 2 × Water + Earth + Fire |
| T2-267 · Reserved | Gravimetric Sensor | Assemblies | C-4 | E + 3 × A | Earth + 3 × Air |
| T2-268 · Invented | Airborne Particle Detector | Assemblies | C-4 | 2 × W + 2 × A | 2 × Water + 2 × Air |
| T2-269 · Invented | Clinical Imaging Module | Assemblies | C-4 | W+F + W+A | 2 × Water + Fire + Air |
| T2-270 · Invented | Astronomical Telescope | Systems | C-5 | A + 2 × E+F | 2 × Earth + 2 × Fire + Air |
| T2-271 · Invented | Planetary Survey Probe | Systems | C-5 | A + W+E + E+F | Water + 2 × Earth + Fire + Air |
| T2-272 · Reserved | Asteroid Mapping Probe | Systems | C-5 | W + 2 × E+F | Water + 2 × Earth + 2 × Fire |
| T2-273 · Reserved | Deep Space Scout Probe | Systems | C-5 | E + 2 × E+F | 3 × Earth + 2 × Fire |
| T2-274 · Reserved | Surface Sampling Rover | Systems | C-5 | 3 × A + E+F | Earth + Fire + 3 × Air |
| T2-275 · Reserved | Subsurface Survey Package | Systems | C-5 | W + 2 × A + E+F | Water + Earth + Fire + 2 × Air |
| T2-276 · Invented | Orbital Imaging Array | Systems | C-5 | W + W+E + E+F | 2 × Water + 2 × Earth + Fire |
| T2-277 · Reserved | Cosmic Ray Observatory | Systems | C-5 | E + 2 × A + E+F | 2 × Earth + Fire + 2 × Air |
| T2-278 · Invented | Solar Observation Platform | Systems | C-5 | E + W+E + E+F | Water + 3 × Earth + Fire |
| T2-279 · Reserved | Radio Astronomy Array | Systems | C-5 | F + 2 × A + E+F | Earth + 2 × Fire + 2 × Air |
| T2-280 · Invented | Medical Imaging Scanner | Systems | C-5 | F + W+E + E+F | Water + 2 × Earth + 2 × Fire |
| T2-281 · Reserved | Exoplanet Imaging Instrument | Systems | C-5 | 3 × A + W+E | Water + Earth + 3 × Air |
| T2-282 · Reserved | Atmospheric Survey Balloon | Systems | C-5 | 5 × A | 5 × Air |
| T2-283 · Invented | Ocean World Sonar Package | Systems | C-5 | W + E + A + E+F | Water + 2 × Earth + Fire + Air |
| T2-284 · Invented | Ice Penetrating Radar | Systems | C-5 | 2 × W + A + E+F | 2 × Water + Earth + Fire + Air |
| T2-285 · Invented | Water Quality Laboratory | Systems | C-5 | 2 × E + A + E+F | 3 × Earth + Fire + Air |
| T2-286 · Invented | Mineral Analysis Station | Systems | C-5 | E + 2 × A + W+E | Water + 2 × Earth + 2 × Air |
| T2-287 · Reserved | High Resolution Mapping Array | Systems | C-5 | F + 2 × A + W+E | Water + Earth + Fire + 2 × Air |
| T2-288 · Invented | Long Baseline Interferometer | Systems | C-5 | A + W+A + E+F | Water + Earth + Fire + 2 × Air |
| T2-289 · Invented | Tissue Analysis Instrument | Systems | C-5 | A + E+F + F+A | Earth + 2 × Fire + 2 × Air |
| T2-290 · Reserved | Field Diagnostic Laboratory | Systems | C-5 | E + 4 × A | Earth + 4 × Air |
| T2-291 · Reserved | Deep Bore Sampling Instrument | Systems | C-5 | W + E + 3 × A | Water + Earth + 3 × Air |
| T2-292 · Reserved | Pathogen Sampling Probe | Systems | C-5 | E + F + 3 × A | Earth + Fire + 3 × Air |
| T2-293 · Invented | Hazard Mapping Array | Systems | C-5 | A + W+E + F+A | Water + Earth + Fire + 2 × Air |
| T2-294 · Reserved | Precision Metrology Bench | Systems | C-5 | 2 × W + 3 × A | 2 × Water + 3 × Air |

### Mining & Industry

Resource extraction, refining, fabrication and tooling for civilian and fleet production.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-295 · Reserved | Drill Tooth | Components | C-3 | W + 2 × E | Water + 2 × Earth |
| T2-296 · Reserved | Abrasive Grain Pack | Consumables | C-3 | 2 × E + A | 2 × Earth + Air |
| T2-297 · Invented | Cutting Insert | Components | C-3 | E + F+A | Earth + Fire + Air |
| T2-298 · Invented | Lubricant Cartridge | Consumables | C-3 | E + W+F | Water + Earth + Fire |
| T2-299 · Reserved | Drill Head | Assemblies | C-4 | W + 3 × E | Water + 3 × Earth |
| T2-300 · Reserved | Crushing Jaw | Assemblies | C-4 | 3 × E + A | 3 × Earth + Air |
| T2-301 · Reserved | Grinding Wheel | Assemblies | C-4 | 2 × E + F+A | 2 × Earth + Fire + Air |
| T2-302 · Reserved | Smelting Crucible | Assemblies | C-4 | 2 × E + W+F | Water + 2 × Earth + Fire |
| T2-303 · Invented | Casting Mold | Assemblies | C-4 | W + 2 × E + A | Water + 2 × Earth + Air |
| T2-304 · Invented | Welding Electrode Bank | Assemblies | C-4 | 2 × W + 2 × E | 2 × Water + 2 × Earth |
| T2-305 · Reserved | Extrusion Die | Assemblies | C-4 | 2 × E + W+A | Water + 2 × Earth + Air |
| T2-306 · Reserved | Ore Separator | Assemblies | C-4 | W + E + F+A | Water + Earth + Fire + Air |
| T2-307 · Invented | Induction Heater | Assemblies | C-4 | E + A + F+A | Earth + Fire + 2 × Air |
| T2-308 · Invented | Industrial Pump | Assemblies | C-4 | W + E + W+F | 2 × Water + Earth + Fire |
| T2-309 · Invented | Pressure Filter | Assemblies | C-4 | E + A + W+F | Water + Earth + Fire + Air |
| T2-310 · Invented | Tool Cooling Block | Assemblies | C-4 | W+A + F+A | Water + Fire + 2 × Air |
| T2-311 · Reserved | Vacuum Furnace Liner | Systems | C-5 | W + 4 × E | Water + 4 × Earth |
| T2-312 · Reserved | Asteroid Drill Rig | Systems | C-5 | 4 × E + A | 4 × Earth + Air |
| T2-313 · Reserved | Regolith Excavator | Systems | C-5 | 3 × E + F+A | 3 × Earth + Fire + Air |
| T2-314 · Reserved | Ore Crushing Plant | Systems | C-5 | 3 × E + W+F | Water + 3 × Earth + Fire |
| T2-315 · Invented | Magnetic Separation Plant | Systems | C-5 | W + 3 × E + A | Water + 3 × Earth + Air |
| T2-316 · Reserved | Electrochemical Refinery | Systems | C-5 | 2 × W + 3 × E | 2 × Water + 3 × Earth |
| T2-317 · Reserved | Plasma Smelter | Systems | C-5 | 3 × E + 2 × A | 3 × Earth + 2 × Air |
| T2-318 · Reserved | Vacuum Casting Plant | Systems | C-5 | 3 × E + E+F | 4 × Earth + Fire |
| T2-319 · Invented | Precision Milling Center | Systems | C-5 | W + 2 × E + F+A | Water + 2 × Earth + Fire + Air |
| T2-320 · Invented | Additive Fabrication Unit | Systems | C-5 | 2 × E + F + F+A | 2 × Earth + 2 × Fire + Air |
| T2-321 · Reserved | Heavy Extrusion Press | Systems | C-5 | 2 × E + A + F+A | 2 × Earth + Fire + 2 × Air |
| T2-322 · Reserved | Crystal Growth Chamber | Systems | C-5 | W + 2 × E + W+F | 2 × Water + 2 × Earth + Fire |
| T2-323 · Invented | Semiconductor Fabrication Rack | Systems | C-5 | 2 × E + F + W+F | Water + 2 × Earth + 2 × Fire |
| T2-324 · Reserved | Polymer Synthesis Reactor | Systems | C-5 | 2 × E + A + W+F | Water + 2 × Earth + Fire + Air |
| T2-325 · Invented | Composite Curing Chamber | Systems | C-5 | E + 2 × F+A | Earth + 2 × Fire + 2 × Air |
| T2-326 · Invented | Industrial Electrolyzer | Systems | C-5 | 2 × W + 2 × E + A | 2 × Water + 2 × Earth + Air |
| T2-327 · Invented | Molecular Separation Column | Systems | C-5 | W + 2 × E + W+A | 2 × Water + 2 × Earth + Air |
| T2-328 · Reserved | Automated Tool Foundry | Systems | C-5 | 2 × E + F + 2 × A | 2 × Earth + Fire + 2 × Air |
| T2-329 · Invented | Deep Core Boring Rig | Systems | C-5 | E + W+F + F+A | Water + Earth + 2 × Fire + Air |
| T2-330 · Reserved | Ice Extraction Plant | Systems | C-5 | 2 × E + 3 × A | 2 × Earth + 3 × Air |
| T2-331 · Invented | Metal Recovery Plant | Systems | C-5 | W + E + A + F+A | Water + Earth + Fire + 2 × Air |
| T2-332 · Invented | Volatile Capture Plant | Systems | C-5 | 2 × W + E + F+A | 2 × Water + Earth + Fire + Air |
| T2-333 · Reserved | Industrial Heat Treatment Cell | Systems | C-5 | E + 2 × A + F+A | Earth + Fire + 3 × Air |
| T2-334 · Invented | High Pressure Synthesis Chamber | Systems | C-5 | E + W+A + F+A | Water + Earth + Fire + 2 × Air |
| T2-335 · Invented | Continuous Production Furnace | Systems | C-5 | E + 2 × W+F | 2 × Water + Earth + 2 × Fire |
| T2-336 · Reserved | Autonomous Ore Processing Line | Systems | C-5 | E + 2 × A + W+F | Water + Earth + Fire + 2 × Air |

### Logistics & Provisioning

Cargo handling, food preservation, medical storage, provisioning and distribution hardware.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-337 · Invented | Cargo Strap | Components | C-3 | W + W+A | 2 × Water + Air |
| T2-338 · Invented | Container Seal | Components | C-3 | F + E+A | Earth + Fire + Air |
| T2-339 · Reserved | Packing Foam | Components | C-3 | 3 × W | 3 × Water |
| T2-340 · Reserved | Tie Down Clamp | Components | C-3 | 2 × W + A | 2 × Water + Air |
| T2-341 · Invented | Nutrient Cargo Canister | Assemblies | C-4 | 2 × W + E+A | 2 × Water + Earth + Air |
| T2-342 · Invented | Provisioning Storage Rack | Assemblies | C-4 | W+A + E+A | Water + Earth + 2 × Air |
| T2-343 · Invented | Transfer Coupler | Assemblies | C-4 | W + E + E+A | Water + 2 × Earth + Air |
| T2-344 · Invented | Conveyor Segment | Assemblies | C-4 | W + A + E+A | Water + Earth + 2 × Air |
| T2-345 · Reserved | Docking Clamp | Assemblies | C-4 | 2 × W + W+A | 3 × Water + Air |
| T2-346 · Reserved | Pallet Chassis | Assemblies | C-4 | 4 × W | 4 × Water |
| T2-347 · Invented | Cargo Tracking Tag | Assemblies | C-4 | W + E + W+A | 2 × Water + Earth + Air |
| T2-348 · Reserved | Thermal Cargo Liner | Assemblies | C-4 | 3 × W + E | 3 × Water + Earth |
| T2-349 · Reserved | Magnetic Cargo Lock | Assemblies | C-4 | 3 × W + A | 3 × Water + Air |
| T2-350 · Invented | Potable Water Transfer Hose | Assemblies | C-4 | 2 × W + E + A | 2 × Water + Earth + Air |
| T2-351 · Invented | Cargo Pod | Systems | C-5 | W + W+A + E+A | 2 × Water + Earth + 2 × Air |
| T2-352 · Reserved | Medical Cryogenic Vessel | Systems | C-5 | 3 × W + E+A | 3 × Water + Earth + Air |
| T2-353 · Reserved | Pressurized Freight Container | Systems | C-5 | A + 2 × E+A | 2 × Earth + 3 × Air |
| T2-354 · Reserved | Hazardous Cargo Vault | Systems | C-5 | 2 × W + E + E+A | 2 × Water + 2 × Earth + Air |
| T2-355 · Invented | Autonomous Cargo Pallet | Systems | C-5 | 2 × W + F + E+A | 2 × Water + Earth + Fire + Air |
| T2-356 · Invented | Nutrition Reserve Silo | Systems | C-5 | 2 × W + A + E+A | 2 × Water + Earth + 2 × Air |
| T2-357 · Invented | Vacuum Cargo Transfer Unit | Systems | C-5 | E + W+A + E+A | Water + 2 × Earth + 2 × Air |
| T2-358 · Invented | Orbital Freight Rack | Systems | C-5 | F + W+A + E+A | Water + Earth + Fire + 2 × Air |
| T2-359 · Invented | Ship Loading Gantry | Systems | C-5 | A + W+A + E+A | Water + Earth + 3 × Air |
| T2-360 · Reserved | Dockside Cargo Crane | Systems | C-5 | 3 × W + W+A | 4 × Water + Air |
| T2-361 · Reserved | Fuel Transfer Assembly | Systems | C-5 | 5 × W | 5 × Water |
| T2-362 · Reserved | Medical Oxygen Storage Vault | Systems | C-5 | W + E + A + E+A | Water + 2 × Earth + 2 × Air |
| T2-363 · Invented | Automated Sorting Machine | Systems | C-5 | 2 × W + E + W+A | 3 × Water + Earth + Air |
| T2-364 · Invented | Food Preservation Chamber | Systems | C-5 | 2 × W + F + W+A | 3 × Water + Fire + Air |
| T2-365 · Invented | Modular Warehouse Block | Systems | C-5 | 2 × W + A + W+A | 3 × Water + 2 × Air |
| T2-366 · Reserved | Intermodal Cargo Frame | Systems | C-5 | 4 × W + E | 4 × Water + Earth |
| T2-367 · Reserved | Orbital Cargo Capsule | Systems | C-5 | 4 × W + F | 4 × Water + Fire |
| T2-368 · Reserved | Cargo Ejection System | Systems | C-5 | 4 × W + A | 4 × Water + Air |
| T2-369 · Invented | Civilian Resupply Pod | Systems | C-5 | W + E + F + W+A | 2 × Water + Earth + Fire + Air |
| T2-370 · Reserved | Microgravity Conveyor Array | Systems | C-5 | 3 × W + E + A | 3 × Water + Earth + Air |
| T2-371 · Invented | Station Freight Elevator | Systems | C-5 | W + W+F + W+A | 3 × Water + Fire + Air |
| T2-372 · Reserved | Robotic Inventory Rack | Systems | C-5 | W + W+A + F+A | 2 × Water + Fire + 2 × Air |
| T2-373 · Reserved | Bulk Gas Storage Array | Systems | C-5 | 3 × W + 2 × A | 3 × Water + 2 × Air |
| T2-374 · Reserved | Biological Sample Transport Pod | Systems | C-5 | 3 × W + W+F | 4 × Water + Fire |
| T2-375 · Reserved | Fleet Provisioning Module | Systems | C-5 | 2 × W + E + 2 × A | 2 × Water + Earth + 2 × Air |
| T2-376 · Reserved | Docking Alignment Rig | Systems | C-5 | 2 × W + A + F+A | 2 × Water + Fire + 2 × Air |
| T2-377 · Invented | Container Repair Press | Systems | C-5 | W + 2 × A + W+F | 2 × Water + Fire + 2 × Air |
| T2-378 · Reserved | Heavy Cargo Transfer Platform | Systems | C-5 | W + W+F + F+A | 2 × Water + 2 × Fire + Air |

### Defence & Rescue

Fleet defence, civilian protection, emergency response, rescue and evacuation equipment.

| Code | Good | Form | Complexity | Processed inputs per unit | Raw ancestry |
| --- | --- | --- | --- | --- | --- |
| T2-379 · Invented | Shield Mesh | Components | C-3 | A + W+A | Water + 2 × Air |
| T2-380 · Reserved | Impact Foam | Components | C-3 | E + W+A | Water + Earth + Air |
| T2-381 · Invented | Pressure Suit Repair Patch | Components | C-3 | F + W+A | Water + Fire + Air |
| T2-382 · Reserved | Fire Suppressant Cartridge | Consumables | C-3 | W + 2 × A | Water + 2 × Air |
| T2-383 · Reserved | Debris Shield | Assemblies | C-4 | 2 × W+A | 2 × Water + 2 × Air |
| T2-384 · Reserved | Radiation Shield | Assemblies | C-4 | 2 × A + W+A | Water + 3 × Air |
| T2-385 · Invented | Pressure Barrier | Assemblies | C-4 | W+E + W+A | 2 × Water + Earth + Air |
| T2-386 · Invented | Fire Isolation Panel | Assemblies | C-4 | W + A + W+A | 2 × Water + 2 × Air |
| T2-387 · Invented | Emergency Beacon | Assemblies | C-4 | E + A + W+A | Water + Earth + 2 × Air |
| T2-388 · Invented | Surge Protector | Assemblies | C-4 | F + A + W+A | Water + Fire + 2 × Air |
| T2-389 · Invented | Leak Detection Unit | Assemblies | C-4 | W + F + W+A | 2 × Water + Fire + Air |
| T2-390 · Invented | Civilian Hazard Warning Sensor | Assemblies | C-4 | E + F + W+A | Water + Earth + Fire + Air |
| T2-391 · Reserved | Combat Armor Plate | Assemblies | C-4 | W + 3 × A | Water + 3 × Air |
| T2-392 · Reserved | Blast Door | Assemblies | C-4 | F + 3 × A | Fire + 3 × Air |
| T2-393 · Reserved | Containment Valve | Systems | C-5 | A + 2 × W+A | 2 × Water + 3 × Air |
| T2-394 · Invented | Rescue Tether Reel | Systems | C-5 | A + W+E + W+A | 2 × Water + Earth + 2 × Air |
| T2-395 · Reserved | Electromagnetic Shield Array | Systems | C-5 | W + 2 × W+A | 3 × Water + 2 × Air |
| T2-396 · Reserved | Radiation Shelter Core | Systems | C-5 | E + 2 × W+A | 2 × Water + Earth + 2 × Air |
| T2-397 · Invented | Hull Breach Containment Pack | Systems | C-5 | F + 2 × W+A | 2 × Water + Fire + 2 × Air |
| T2-398 · Reserved | Fire Suppression Module | Systems | C-5 | 3 × A + W+A | Water + 4 × Air |
| T2-399 · Reserved | Defence Interceptor Drone | Systems | C-5 | W + 2 × A + W+A | 2 × Water + 3 × Air |
| T2-400 · Invented | Collision Avoidance Array | Systems | C-5 | W + W+E + W+A | 3 × Water + Earth + Air |
| T2-401 · Reserved | Emergency Escape Pod | Systems | C-5 | E + 2 × A + W+A | Water + Earth + 3 × Air |
| T2-402 · Invented | Automated Rescue Craft | Systems | C-5 | E + W+E + W+A | 2 × Water + 2 × Earth + Air |
| T2-403 · Invented | Early Warning Sensor Grid | Systems | C-5 | F + 2 × A + W+A | Water + Fire + 3 × Air |
| T2-404 · Invented | Solar Storm Protection Array | Systems | C-5 | F + W+E + W+A | 2 × Water + Earth + Fire + Air |
| T2-405 · Reserved | Fleet Deflection Shield | Systems | C-5 | W + E + A + W+A | 2 × Water + Earth + 2 × Air |
| T2-406 · Invented | Impact Absorption Frame | Systems | C-5 | W + F + A + W+A | 2 × Water + Fire + 2 × Air |
| T2-407 · Invented | Reactor Containment Shell | Systems | C-5 | E + F + A + W+A | Water + Earth + Fire + 2 × Air |
| T2-408 · Reserved | Critical System Backup Rack | Systems | C-5 | 2 × E + A + W+A | Water + 2 × Earth + 2 × Air |
| T2-409 · Invented | Emergency Cooling Assembly | Systems | C-5 | 2 × F + A + W+A | Water + 2 × Fire + 2 × Air |
| T2-410 · Invented | Redundant Control Module | Systems | C-5 | A + W+F + W+A | 2 × Water + Fire + 2 × Air |
| T2-411 · Reserved | Pressure Recovery Plant | Systems | C-5 | A + W+A + F+A | Water + Fire + 3 × Air |
| T2-412 · Reserved | Damage Isolation Controller | Systems | C-5 | W + 4 × A | Water + 4 × Air |
| T2-413 · Reserved | Shielded Navigation Core | Systems | C-5 | F + 4 × A | Fire + 4 × Air |
| T2-414 · Reserved | Continuity Archive Vault | Systems | C-5 | W + F + 3 × A | Water + Fire + 3 × Air |
| T2-415 · Reserved | Autonomous Damage Control Robot | Systems | C-5 | E + W+F + W+A | 2 × Water + Earth + Fire + Air |
| T2-416 · Invented | Orbital Defence Barrier | Systems | C-5 | F + W+A + F+A | Water + 2 × Fire + 2 × Air |
| T2-417 · Reserved | Fortified Shelter Gate | Systems | C-5 | 3 × A + W+F | Water + Fire + 3 × Air |
| T2-418 · Reserved | Emergency Docking Module | Systems | C-5 | 3 × A + F+A | Fire + 4 × Air |
| T2-419 · Reserved | Medical Evacuation Capsule | Systems | C-5 | W + 2 × A + F+A | Water + Fire + 3 × Air |
| T2-420 · Invented | Civilian Refuge Shelter | Systems | C-5 | A + W+F + F+A | Water + 2 × Fire + 2 × Air |
