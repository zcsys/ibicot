# Star Business
## Complete Naming Catalog — American Industrial Edition

**Game name: Star Business**  
**Tagline: Build the Colony. Supply the Fleet.**  
**Setting: 4259**

Naming logic: “Star” establishes the galactic setting; “Business” puts trade, competing companies, and the economy at the center of the game.

In 4259, humans and robots are building a manufacturing colony into the supply base for a coming galactic war. Twenty extraction giants supply 1,000 refineries. Those refineries feed 60,000 autonomous manufacturers. A million distributors buy, switch suppliers, and keep the colony running. Prices, reliability, loyalty, supply, and demand emerge from those decisions.

The American character comes from electric utilities, aerospace contractors, machine shops, railroad suppliers, company towns, truck stops, and warehouse catalogs. Large corporations sound broad and established. Specialized suppliers sound like businesses whose names belong on a loading dock. Products sound like things a purchasing manager can order and a maintenance crew can identify.

Housing, medical equipment, gardens, archives, and rescue vehicles still matter. The colony is preparing for war while a million customers continue to live and work inside its economy. The title names that economy; it does not imply that all companies belong to one parent corporation.

This edition supersedes the previous naming direction. It includes every requested category, both refining equipment classes, all three manufacturing equipment classes, all 200 goods, and the simple numbered-company rule. The authored company roster is completely reimagined. The four classical elements remain unchanged. Familiar functional terms are retained where they are already the clearest American industrial terms.

## 1. House Style

Naming logic: use direct American business and engineering language with a visible distinction between material, company, industry, equipment, and finished good.

- Use American English: aluminum, fiber, mold, center, defense, maneuver, pressurized, standardized.
- Use title case for catalog labels. Use lowercase for generic material, equipment, and product descriptions in sentences. Proper company names keep their capitalization.
- Materials identify trade stock. Companies identify businesses. Sectors identify purchasing domains. Goods identify physical purchases.
- Keep names short enough for a market row. Use longer names only when the distinction matters, such as Medical Cold-Chain Container versus Orbital Shipping Container.
- Keep the maker in its own field. “Mudrock” is never part of a generic equipment class or product name.
- Generated firms use a sector-specific generic name plus a `0x`-prefixed hex serial number. No house-name pool, location suffix, district, or berth is added to a company name.
- Avoid invented mineral suffixes, model years, military ranks, and prestige adjectives as substitutes for function.

## 2. Raw Elements — T0 Output

Naming logic: the four classical words remain the economy’s stable roots, while their descriptions use resource-industry language.

| Element | Resource Market | Typical Recovery |
|---|---|---|
| Water | Ice and aqueous resources | Ice harvesting, reservoir pumping, and comet recovery |
| Earth | Solid mineral resources | Ore extraction, rock cutting, and regolith collection |
| Fire | Harvestable energetic resources | Stellar collection, geothermal recovery, and energetic-stock capture |
| Air | Gaseous resources | Atmospheric collection, gas capture, and volatile separation |

Water, Earth, Fire, and Air are simulation resource classes. Their recipes are game abstractions, not literal chemical equations. Refining processes and application-specific grades are implicit; this catalog does not add hidden ingredients or change the supplied recipe quantities.

## 3. Refined Materials — All 10

Naming logic: recognizable industrial stock names communicate physical use without forcing every material to sound like a newly discovered mineral.

The legacy codes are compatibility keys. **W+E is one T1 material**, not two T1 purchases. Use the new symbols in compact bills of materials and the full names on market cards.

| Legacy Code | Material | Symbol | Raw Recipe | Trade Meaning |
|---|---|---|---|---|
| W | Industrial Fluid | IF | 1 Water | Standard liquid feedstock for cooling, hydraulic systems, cleaning, and wet processing. |
| E | Bulk Alloy | BA | 1 Earth | General-purpose metal stock for frames, electrical conductors, housings, and load-bearing parts. |
| F | Energy Carrier | EC | 1 Fire | Stabilized energy-bearing stock for power storage, discharge, and equipment activation. |
| A | Process Gas | PG | 1 Air | Conditioned gas stock for pressure systems, controlled atmospheres, and application-specific gas blends. |
| W+E | Ceramic Stock | CS | 1 Water + 1 Earth | Bonded mineral stock for rigid surfaces, electrical insulation, and heat-resistant structures. |
| W+F | Thermal Compound | TC | 1 Water + 1 Fire | Heat-transfer and heat-buffering stock for cooling loops and temperature-controlled equipment. |
| W+A | Technical Fiber | TF | 1 Water + 1 Air | Engineered fiber stock for flexible reinforcement, filtration, seals, and optical applications. |
| E+F | Semiconductor Crystal | SC | 1 Earth + 1 Fire | Electronic-grade crystal stock for processors, sensors, and optoelectronics. |
| E+A | Polymer Composite | PC | 1 Earth + 1 Air | Lightweight reinforced stock for molded parts, resilient joints, and protective housings. |
| F+A | Active Reagent | AR | 1 Fire + 1 Air | Stabilized chemical stock for controlled reactions, protective treatments, and discharge systems. |

## 4. Extraction Companies — All 20

Naming logic: diversified corporations get broad business names; specialized operators get resource names; the two-market operators put their special duty directly in the company name.

The distribution is **2 four-market + 4 three-market + 6 two-market + 8 single-market companies**. The six two-market slots are assigned to the six distinct element pairs, each with a special duty. The eight single-market companies are pure extractors.

### Four-Market Corporations

| ID | Company | Extraction Markets | Identity |
|---|---|---|---|
| T0-01 | Raw Materials Corp. | Water, Earth, Fire, Air | A first-generation supplier that expanded into every extraction market. |
| T0-02 | Elements Inc. | Water, Earth, Fire, Air | A diversified corporation built through acquisitions and long-distance concessions. |

### Three-Market Corporations With Civic Duties

| ID | Company | Extraction Markets | Duty | Player Service |
|---|---|---|---|---|
| T0-03 | Baseline Resource Corporation | Water, Earth, Fire | Policy | Colony Policy |
| T0-04 | Union Charter Resources Inc. | Water, Earth, Air | Administration | Business Registry |
| T0-05 | Signal Point Resources Corp. | Water, Fire, Air | Intelligence | Market Intelligence |
| T0-06 | Commonline Resources Company | Earth, Fire, Air | Community | Community Hub |

Baseline periodically sets main simulation parameters. Union Charter registers company names and maintains company records. Signal Point publishes sector statistics. Commonline operates the player forums. These responsibilities remain corporate charter duties, not separate extraction agents.

Baseline does not directly replace emergent prices with a fixed price list. Market Intelligence supplies economic information, not banking or advertising. Business Registry registers firms without selling promotional placement. Community Hub hosts discussion; paid advertising remains the Air pair’s exclusive business.

### Two-Market Operators

| ID | Company | Extraction Markets | Special Duty |
|---|---|---|---|
| T0-07 | Mudrock Machinery Co. | Water, Earth | Machinery manufacturing. |
| T0-08 | Steam Ridge Financial Inc. | Water, Fire | Financial services. |
| T0-09 | Cloudline Games & Entertainment Corporation | Water, Air | Games and entertainment. |
| T0-10 | Hotrock Utility Company | Earth, Fire | Utilities. |
| T0-11 | Dustline Spatial Solutions Corp. | Earth, Air | Warehouses, land, and industrial space. |
| T0-12 | Flare Basin Advertising Incorporated | Fire, Air | Advertising. |

### Single-Market Extractors

| ID | Company | Sole Extraction Market |
|---|---|---|
| T0-13 | Bluegate Water Co. | Water |
| T0-14 | Coldwell Ice Resources Inc. | Water |
| T0-15 | Bedrock Mining Corp. | Earth |
| T0-16 | Iron County Minerals Company | Earth |
| T0-17 | Furnace Creek Energy Inc. | Fire |
| T0-18 | Sunbelt Energy Corporation | Fire |
| T0-19 | Skyline Gas Co. | Air |
| T0-20 | Highband Atmospherics Inc. | Air |

### Special Duties That Follow the Two-Market Companies

**Machinery manufacturing — Mudrock Machinery Co.** Mudrock is the sole producer of complete refining and manufacturing machinery. This includes production robots and production installations. Other firms can supply parts, tooling, consumables, and service robots; they cannot independently sell complete output-producing machinery.

**Financial services — Steam Ridge Financial Inc.** Steam Ridge is the game’s financial institution, providing banking, lending, deposits, and financial settlement services. Ordinary firms can price goods, invoice customers, and receive payment without becoming financial institutions.

**Warehouses, land, and industrial space — Dustline Spatial Solutions Corp.** Dustline provides the colony’s warehousing, land, and industrial space. Display the charge for its facilities as **Storage Royalty** with Dustline as the recipient. Rates, allocation, and the accounting base remain simulation parameters.

**Advertising — Flare Basin Advertising Incorporated.** Flare Basin sells paid promotion and advertising distribution. A standard product listing, technical specification, civic notice, or ordinary forum post does not become an advertising business by existing.

**Games and entertainment — Cloudline Games & Entertainment Corporation.** Cloudline publishes games and entertainment.

**Utilities — Hotrock Utility Company.** Hotrock operates the colony’s utility services.

The all-market companies, civic-duty companies, and single-market extractors do not inherit any of these special duties.

## 5. Authored Refinery Companies — All 10

Naming logic: process suppliers use a compact American corporate identity plus the trade they actually perform. No refinery name implies that it builds the machinery it operates.

| ID | Material Sector | Authored Company | Generic Company Base |
|---|---|---|---|
| T1-01 | Industrial Fluid | Clearwater Process Supply | Industrial Fluids |
| T1-02 | Bulk Alloy | Red Mesa Metals | Alloy Refining |
| T1-03 | Energy Carrier | High Current Materials | Energy Materials |
| T1-04 | Process Gas | Open Range Gas Products | Process Gases |
| T1-05 | Ceramic Stock | Hardline Industrial Ceramics | Ceramic Materials |
| T1-06 | Thermal Compound | Heatway Process Materials | Thermal Materials |
| T1-07 | Technical Fiber | Crossweave Fiber Products | Technical Fibers |
| T1-08 | Semiconductor Crystal | Sunridge Electronic Materials | Semiconductor Materials |
| T1-09 | Polymer Composite | Ridgeback Composite Products | Composite Materials |
| T1-10 | Active Reagent | Navarro Process Chemicals | Active Chemicals |

These are the ten authored identities or cohort labels. They are not mandatory parent companies for the 1,000 refinery agents. The generic company base is the separate name used for numbered firms.

## 6. Manufacturing Sectors and Authored Companies — All 10 of Each

Naming logic: industry names identify the market; authored companies have the plain confidence of American aerospace, utility, and industrial suppliers.

| Sector ID | Sector | Company ID | Authored Company | Generic Company Base |
|---|---|---|---|---|
| S01 | Power & Utilities | T2-C01 | Switchyard Power Systems | Power Equipment |
| S02 | Propulsion & Flight Systems | T2-C02 | Burnline Aerospace | Propulsion Systems |
| S03 | Shipbuilding & Orbital Structures | T2-C03 | Rivet Point Shipbuilding | Shipbuilding Works |
| S04 | Housing & Life Support | T2-C04 | Homefront Habitat Systems | Habitat Systems |
| S05 | Robotics & Field Services | T2-C05 | Workhorse Service Robotics | Service Robotics |
| S06 | Computing & Communications | T2-C06 | Copperline Electronics | Computing Systems |
| S07 | Sensors & Medical Equipment | T2-C07 | Benchmark Instrument Corporation | Scientific Instruments |
| S08 | Industrial Tooling & Mining Supplies | T2-C08 | Redridge Tool & Supply | Industrial Tooling |
| S09 | Freight & Warehouse Equipment | T2-C09 | Crossdock Cargo Systems | Freight Equipment |
| S10 | Defense & Emergency Systems | T2-C10 | Hardstop Defense Systems | Defense Systems |

These are authored identities or cohort labels, not parent corporations for every numbered manufacturer. In particular, Industrial Tooling & Mining Supplies supplies tools and passive fixtures, while Robotics & Field Services supplies service robots. Complete factory machinery remains Mudrock Machinery Co.’s business.

## 7. Equipment Classes and Refining Configurations

Naming logic: the operation comes first, followed by a familiar installation scale: bench, cell, or hall. The existing production-class names remain useful in American manufacturing language and are retained.

**Market:** Machinery Market. **Sections:** Refining Equipment and Production Equipment. Both sections have the same sole eligible maker: **Mudrock Machinery Co.**. These sections do not create separate machinery markets.

| Class ID | Complexity | Equipment Class | Configuration Label |
|---|---|---|---|
| EQ-R1 | C-1 | Refining Bench | Single-Element Refining |
| EQ-R2 | C-2 | Refining Cell | Paired-Element Refining |
| EQ-P3 | C-3 | Production Bench | Component Production |
| EQ-P4 | C-4 | Production Cell | Assembly Production |
| EQ-P5 | C-5 | Production Hall | Systems Production |

Use these exact names instead of the unnamed refining installations and “Basic” / “Compound” labels. Complexity remains its own field. The three production complexity mappings follow the naming scheme; retain actual equipment eligibility rules in code rather than deriving new mechanics from a display label.

### All 10 Refining Configuration Names

| Material Sector | Generic Installation Name | Complexity |
|---|---|---|
| Industrial Fluid | Industrial Fluid Refining Bench | C-1 |
| Bulk Alloy | Bulk Alloy Refining Bench | C-1 |
| Energy Carrier | Energy Carrier Refining Bench | C-1 |
| Process Gas | Process Gas Refining Bench | C-1 |
| Ceramic Stock | Ceramic Stock Refining Cell | C-2 |
| Thermal Compound | Thermal Compound Refining Cell | C-2 |
| Technical Fiber | Technical Fiber Refining Cell | C-2 |
| Semiconductor Crystal | Semiconductor Crystal Refining Cell | C-2 |
| Polymer Composite | Polymer Composite Refining Cell | C-2 |
| Active Reagent | Active Reagent Refining Cell | C-2 |

A purchase card reads **Thermal Compound Refining Cell**, with **Maker: Mudrock Machinery Co.** and **Complexity: C-2** in separate fields. A production card reads **Production Hall**, with **Maker: Mudrock Machinery Co.** and **Supported Sector: Shipbuilding & Orbital Structures** in separate fields.

Bench, cell, and hall describe equipment packages and installation scale, not the literal size of every object they can build. These five classes sit outside the 200 finished goods. No new machinery recipes are invented by this catalog. Specialized factory robots and refining equipment are configurations of Mudrock machinery, not independent manufacturing markets.

## 8. Manufactured Goods — All 200

Naming logic: direct American procurement names distinguish parts, assemblies, and complete systems. A buyer should understand the item without learning a fictional vocabulary or a maker’s model-number system.

Every product retains its original ID, recipe quantities, and complexity from the attached `recipes.md`. A table’s sector applies to every row beneath it. New material symbols replace legacy recipe codes; all recipe inputs below are **refined T1 stock**, never raw elements.

Several product concepts have been deliberately changed to protect the machinery monopoly. Complete factory robots become service robots; complete industrial plants become passive tooling, wear kits, fixtures, or liners. Their original recipe slots stay intact. This is a catalog redesign, not a claim that every original product function is unchanged.

### 8.1. Power & Utilities

**Authored company:** Switchyard Power Systems. **Scope:** Power distribution, generation, storage, and thermal management.

Naming logic: Utility purchasing language: feeder, switchgear, cooling pack, generator, and power station.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-001 | Main Feeder Bar | 1 IF + 1 BA + 1 EC | C-3 |
| T2-002 | Grid Intake Module | 1 EC + 1 CS | C-3 |
| T2-003 | Backup Battery Rack | 1 IF + 1 BA + 1 EC + 1 PG | C-4 |
| T2-004 | Voltage Converter | 1 IF + 1 EC + 1 SC | C-4 |
| T2-005 | Coolant Exchange Block | 1 EC + 1 PG + 1 PC | C-4 |
| T2-006 | Pulse Capacitor Rack | 1 IF + 1 EC + 1 AR | C-4 |
| T2-007 | Solar Roof Panel | 1 BA + 1 EC + 1 CS | C-4 |
| T2-008 | Radiator Wing | 1 EC + 1 PG + 1 TC | C-4 |
| T2-009 | Station Reactor Package | 1 IF + 1 BA + 1 EC + 1 CS | C-5 |
| T2-010 | High-Energy Storage Vessel | 1 IF + 1 EC + 1 PG + 1 TC | C-5 |
| T2-011 | Orbital Solar Farm | 1 BA + 1 EC + 1 PG + 1 TF | C-5 |
| T2-012 | Remote Power Station | 1 IF + 1 BA + 1 EC + 1 SC | C-5 |
| T2-013 | Emergency Battery Room | 1 IF + 1 EC + 1 PG + 1 PC | C-5 |
| T2-014 | Peak Power Reactor | 1 BA + 1 EC + 1 PG + 1 AR | C-5 |
| T2-015 | Field Power Module | 1 EC + 1 TF + 1 AR | C-5 |
| T2-016 | Waste Heat Generator | 1 EC + 1 SC + 1 AR | C-5 |
| T2-017 | Wireless Power Transmitter | 1 EC + 1 PC + 1 AR | C-5 |
| T2-018 | Wireless Power Receiver | 1 EC + 1 CS + 1 TC | C-5 |
| T2-019 | Stellar Collection Array | 1 EC + 1 TF + 1 SC | C-5 |
| T2-020 | Long-Life Generator | 1 EC + 1 PC + 1 AR | C-5 |

### 8.2. Propulsion & Flight Systems

**Authored company:** Burnline Aerospace. **Scope:** Propulsion hardware, flight controls, and navigation equipment.

Naming logic: Aerospace supplier language distinguishes engine parts, control packages, and complete propulsion systems.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-021 | Engine Nozzle Insert | 1 IF + 1 TC | C-3 |
| T2-022 | Propellant Feed Cartridge | 1 BA + 1 TC | C-3 |
| T2-023 | Attitude Thruster Pack | 1 IF + 1 BA + 1 TC | C-4 |
| T2-024 | Ion Acceleration Grid | 1 BA + 1 EC + 1 TC | C-4 |
| T2-025 | Plasma Feed Injector | 1 BA + 1 PG + 1 TC | C-4 |
| T2-026 | Propellant Control Valve | 1 CS + 1 TC | C-4 |
| T2-027 | Flight Reference Gyro | 1 TC + 1 TF | C-4 |
| T2-028 | Inertial Guidance Module | 1 TC + 1 SC | C-4 |
| T2-029 | Ion Cruise Engine | 1 IF + 1 BA + 1 PG + 1 TC | C-5 |
| T2-030 | Plasma Transfer Engine | 1 BA + 1 EC + 1 PG + 1 TC | C-5 |
| T2-031 | Fusion Main Engine | 1 IF + 1 CS + 1 TC | C-5 |
| T2-032 | Pulse Propulsion Chamber | 1 BA + 1 TC + 1 TF | C-5 |
| T2-033 | Light Sail Assembly | 1 EC + 1 TC + 1 SC | C-5 |
| T2-034 | Magnetic Sail Assembly | 1 PG + 1 TC + 1 PC | C-5 |
| T2-035 | Gravity Assist Computer | 1 IF + 1 TC + 1 AR | C-5 |
| T2-036 | Deep Space Flight Controller | 1 BA + 1 CS + 1 TC | C-5 |
| T2-037 | Orbital Maneuvering Engine | 1 EC + 1 TC + 1 TF | C-5 |
| T2-038 | Descent Engine Package | 1 PG + 1 TC + 1 SC | C-5 |
| T2-039 | Launch Assist Booster | 1 IF + 1 TC + 1 PC | C-5 |
| T2-040 | Heavy Tow Engine | 1 BA + 1 TC + 1 AR | C-5 |

### 8.3. Shipbuilding & Orbital Structures

**Authored company:** Rivet Point Shipbuilding. **Scope:** Ship hulls, docking structures, and orbital construction components.

Naming logic: Shipyard language identifies structural parts and vessel roles without decorative ship-class names.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-041 | Hull Skin Panel | 1 EC + 1 CS | C-3 |
| T2-042 | Primary Frame Beam | 1 PG + 1 CS | C-3 |
| T2-043 | Pressure Bulkhead | 1 IF + 1 BA + 1 CS | C-4 |
| T2-044 | Crew Access Hatch | 1 EC + 1 PG + 1 CS | C-4 |
| T2-045 | Docking Adapter Ring | 1 IF + 1 BA + 1 CS | C-4 |
| T2-046 | Viewport Armor Cover | 1 CS + 1 TC | C-4 |
| T2-047 | Landing Gear Assembly | 1 CS + 1 PC | C-4 |
| T2-048 | Cargo Ramp Assembly | 1 CS + 1 AR | C-4 |
| T2-049 | Orbital Construction Frame | 1 IF + 1 BA + 1 EC + 1 CS | C-5 |
| T2-050 | Scout Vessel Frame | 1 IF + 1 BA + 1 PG + 1 CS | C-5 |
| T2-051 | Heavy Freight Hull | 1 EC + 1 CS + 1 TC | C-5 |
| T2-052 | Survey Vessel Chassis | 1 PG + 1 CS + 1 TC | C-5 |
| T2-053 | Mining Tender Hull | 1 IF + 1 CS + 1 TC | C-5 |
| T2-054 | Dock Tug Chassis | 1 BA + 1 CS + 1 TF | C-5 |
| T2-055 | Escort Ship Hull | 1 EC + 1 CS + 1 SC | C-5 |
| T2-056 | Launch Stage Body | 1 PG + 1 CS + 1 PC | C-5 |
| T2-057 | Crew Capsule Shell | 1 IF + 1 CS + 1 AR | C-5 |
| T2-058 | Station Center Truss | 1 BA + 1 CS + 1 TC | C-5 |
| T2-059 | Multiport Dock Frame | 1 EC + 1 CS + 1 TF | C-5 |
| T2-060 | Shipyard Support Frame | 1 PG + 1 CS + 1 SC | C-5 |

The shipyard support frame is passive structural equipment, not a complete shipbuilding machine. Scout Vessel Frame is the structural frame of a small reconnaissance spacecraft.

### 8.4. Housing & Life Support

**Authored company:** Homefront Habitat Systems. **Scope:** Pressurized housing, settlement structures, and essential living infrastructure.

Naming logic: Construction and building-supply language keeps everyday life visible inside the war economy.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-061 | Interior Wall Panel | 1 IF + 1 EC + 1 PG | C-3 |
| T2-062 | Foundation Anchor Kit | 1 IF + 1 TC | C-3 |
| T2-063 | Pressure Wall Section | 1 IF + 1 BA + 1 EC + 1 PG | C-4 |
| T2-064 | Personnel Airlock Gate | 1 IF + 1 EC + 1 TF | C-4 |
| T2-065 | Utility Floor Panel | 1 IF + 1 EC + 1 SC | C-4 |
| T2-066 | Freshwater Pipe Section | 1 IF + 1 BA + 1 PC | C-4 |
| T2-067 | Radiation Barrier Sheet | 1 IF + 1 EC + 1 AR | C-4 |
| T2-068 | Daylight Ceiling Panel | 1 IF + 1 PG + 1 CS | C-4 |
| T2-069 | Residential Pressure Module | 1 IF + 1 BA + 1 EC + 1 CS | C-5 |
| T2-070 | Orbital Housing Shell | 1 IF + 1 EC + 1 PG + 1 TC | C-5 |
| T2-071 | Frontier Community Center | 1 IF + 1 BA + 1 EC + 1 TF | C-5 |
| T2-072 | Rotating Habitat Bearing Hub | 1 IF + 1 EC + 1 PG + 1 SC | C-5 |
| T2-073 | Asteroid Foundation Kit | 1 IF + 1 BA + 1 EC + 1 PC | C-5 |
| T2-074 | Remote Shelter Module | 1 IF + 1 EC + 1 PG + 1 AR | C-5 |
| T2-075 | Mixed-Crew Housing Unit | 1 IF + 1 CS + 1 TC | C-5 |
| T2-076 | Grow Room Enclosure | 1 IF + 1 TF + 1 SC | C-5 |
| T2-077 | Medical Isolation Suite | 1 IF + 1 PC + 1 AR | C-5 |
| T2-078 | Garden Dome Shell | 1 IF + 1 CS + 1 TC | C-5 |
| T2-079 | Underground Habitat Liner | 1 IF + 1 TF + 1 SC | C-5 |
| T2-080 | Orbital Tether Foundation | 1 IF + 1 PC + 1 AR | C-5 |

Grow Room Enclosure and Garden Dome Shell are structures, not installed food-production machinery. Any complete production machinery fitted inside them comes from Mudrock Machinery Co. Mixed-Crew Housing Unit includes human living space and robot service accommodations.

### 8.5. Robotics & Field Services

**Authored company:** Workhorse Service Robotics. **Scope:** Service robots, repair platforms, and replaceable robotic components.

Naming logic: Parts-counter names for components and straightforward job names for robots; production robots remain Mudrock machinery.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-081 | Servo Joint Module | 1 IF + 1 PC | C-3 |
| T2-082 | Actuator Link | 1 BA + 1 PC | C-3 |
| T2-083 | Utility Gripper | 1 EC + 1 PG + 1 PC | C-4 |
| T2-084 | Quick-Change Wrist Coupler | 1 IF + 1 BA + 1 PC | C-4 |
| T2-085 | All-Terrain Drive Wheel | 1 EC + 1 PG + 1 PC | C-4 |
| T2-086 | Service Arm Assembly | 1 CS + 1 PC | C-4 |
| T2-087 | Grip Pressure Sensor | 1 TC + 1 PC | C-4 |
| T2-088 | Fluid Actuator Pack | 1 TF + 1 PC | C-4 |
| T2-089 | Facility Service Robot | 1 BA + 1 EC + 1 PG + 1 PC | C-5 |
| T2-090 | Hull Cleaning Robot | 1 IF + 1 BA + 1 EC + 1 PC | C-5 |
| T2-091 | Equipment Inspection Rover | 1 IF + 1 CS + 1 PC | C-5 |
| T2-092 | Mine Safety Scout | 1 BA + 1 CS + 1 PC | C-5 |
| T2-093 | Hull Patch Robot | 1 EC + 1 PC + 1 AR | C-5 |
| T2-094 | Cargo Handling Rover | 1 PG + 1 CS + 1 PC | C-5 |
| T2-095 | Medical Handling Robot | 1 IF + 1 TC + 1 PC | C-5 |
| T2-096 | Vacuum Service Robot | 1 BA + 1 TF + 1 PC | C-5 |
| T2-097 | Site Survey Rover | 1 EC + 1 SC + 1 PC | C-5 |
| T2-098 | Utility Inspection Crawler | 1 PG + 1 PC + 1 AR | C-5 |
| T2-099 | Building Maintenance Robot | 1 IF + 1 CS + 1 PC | C-5 |
| T2-100 | Salvage Handling Robot | 1 BA + 1 TC + 1 PC | C-5 |

These robots perform inspection, handling, cleaning, rescue support, or repair. None is a production-line robot. A complete manufacturing robot must be purchased from Mudrock Machinery Co. Service products do not imply that autonomous robot residents are property.

### 8.6. Computing & Communications

**Authored company:** Copperline Electronics. **Scope:** Computing hardware, network equipment, and communication systems.

Naming logic: Electronics-catalog language: board, card, switch, server, terminal, and rack.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-101 | Circuit Interconnect Strip | 1 EC + 1 SC | C-3 |
| T2-102 | Solid-State Memory Tile | 1 PG + 1 SC | C-3 |
| T2-103 | Equipment Control Board | 1 IF + 1 BA + 1 SC | C-4 |
| T2-104 | Learning Memory Module | 1 EC + 1 PG + 1 SC | C-4 |
| T2-105 | Local Network Radio | 1 SC + 1 PC | C-4 |
| T2-106 | Signal Booster Card | 1 SC + 1 AR | C-4 |
| T2-107 | Industrial Network Switch | 1 CS + 1 SC | C-4 |
| T2-108 | Packet Buffer Module | 1 TC + 1 SC | C-4 |
| T2-109 | General Computing Rack | 1 IF + 1 BA + 1 PG + 1 SC | C-5 |
| T2-110 | Flight Computing Rack | 1 BA + 1 EC + 1 PG + 1 SC | C-5 |
| T2-111 | Autonomous Scheduling Server | 1 EC + 1 SC + 1 PC | C-5 |
| T2-112 | Radiation-Tolerant Computer | 1 PG + 1 SC + 1 PC | C-5 |
| T2-113 | Quantum Compute Cartridge | 1 IF + 1 TF + 1 SC | C-5 |
| T2-114 | Colony Edge Server | 1 BA + 1 SC + 1 PC | C-5 |
| T2-115 | Fleet Operations Server | 1 EC + 1 SC + 1 AR | C-5 |
| T2-116 | Orbital Relay Station | 1 PG + 1 CS + 1 SC | C-5 |
| T2-117 | Laser Data Terminal | 1 IF + 1 TC + 1 SC | C-5 |
| T2-118 | Deep Space Radio Station | 1 BA + 1 TF + 1 SC | C-5 |
| T2-119 | Interplanetary Network Gateway | 1 EC + 1 SC + 1 PC | C-5 |
| T2-120 | Long-Term Archive Server | 1 PG + 1 SC + 1 AR | C-5 |

### 8.7. Sensors & Medical Equipment

**Authored company:** Benchmark Instrument Corporation. **Scope:** Survey sensors, scientific instruments, and medical diagnostic equipment.

Naming logic: Names state the measured quantity or operating role, followed by the physical instrument type.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-121 | Optical Sensor Element | 1 PG + 1 TF | C-3 |
| T2-122 | Radiation Detector Sheet | 1 PG + 1 SC | C-3 |
| T2-123 | Material Analysis Head | 1 IF + 1 BA + 1 EC + 1 PG | C-4 |
| T2-124 | Tracking Radar Dish | 1 IF + 1 PG + 1 TC | C-4 |
| T2-125 | Laser Mapping Head | 1 IF + 1 PG + 1 TF | C-4 |
| T2-126 | Thermal Inspection Camera | 1 BA + 1 PG + 1 SC | C-4 |
| T2-127 | Magnetic Survey Sensor | 1 EC + 1 PG + 1 PC | C-4 |
| T2-128 | Seismic Monitoring Unit | 1 IF + 1 PG + 1 AR | C-4 |
| T2-129 | Deep Space Telescope | 1 IF + 1 EC + 1 PG + 1 CS | C-5 |
| T2-130 | Planetary Mapping Satellite | 1 IF + 1 BA + 1 PG + 1 TC | C-5 |
| T2-131 | Asteroid Survey Drone | 1 IF + 1 EC + 1 PG + 1 TF | C-5 |
| T2-132 | Long-Range Recon Probe | 1 IF + 1 BA + 1 PG + 1 SC | C-5 |
| T2-133 | Sample Collection Rover | 1 IF + 1 EC + 1 PG + 1 PC | C-5 |
| T2-134 | Subsurface Survey Kit | 1 IF + 1 BA + 1 PG + 1 AR | C-5 |
| T2-135 | Orbital Mapping Imager | 1 PG + 1 CS + 1 TC | C-5 |
| T2-136 | Particle Monitoring Station | 1 PG + 1 TF + 1 SC | C-5 |
| T2-137 | Solar Activity Monitor | 1 PG + 1 PC + 1 AR | C-5 |
| T2-138 | Radio Observation Array | 1 PG + 1 CS + 1 TC | C-5 |
| T2-139 | Medical Imaging Bed | 1 PG + 1 TF + 1 SC | C-5 |
| T2-140 | Planet Detection Instrument | 1 PG + 1 PC + 1 AR | C-5 |

### 8.8. Industrial Tooling & Mining Supplies

**Authored company:** Redridge Tool & Supply. **Scope:** Cutting tools, wear parts, passive fixtures, and mining attachments.

Naming logic: Machine-shop and mine-supply language identifies what wears out, holds a part, or fits inside a separately purchased machine.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-141 | Replaceable Cutting Tooth | 1 BA + 1 PC | C-3 |
| T2-142 | Precision Abrasive Pack | 1 BA + 1 AR | C-3 |
| T2-143 | Rock Drill Crown | 1 BA + 1 PG + 1 CS | C-4 |
| T2-144 | Crusher Jaw Insert | 1 BA + 1 EC + 1 TC | C-4 |
| T2-145 | Surface Finishing Disc | 1 BA + 1 PG + 1 TF | C-4 |
| T2-146 | Crucible Liner | 1 IF + 1 BA + 1 SC | C-4 |
| T2-147 | Casting Die Set | 1 BA + 1 EC + 1 PC | C-4 |
| T2-148 | Welding Contact Kit | 1 BA + 1 PG + 1 AR | C-4 |
| T2-149 | Furnace Refractory Kit | 1 BA + 1 EC + 1 PG + 1 CS | C-5 |
| T2-150 | Drill Alignment Frame | 1 IF + 1 BA + 1 PG + 1 TC | C-5 |
| T2-151 | Excavator Bucket Assembly | 1 BA + 1 EC + 1 PG + 1 TF | C-5 |
| T2-152 | Crusher Rebuild Kit | 1 IF + 1 BA + 1 PG + 1 SC | C-5 |
| T2-153 | Separator Drum Liner | 1 BA + 1 EC + 1 PG + 1 PC | C-5 |
| T2-154 | Refining Tank Liner | 1 IF + 1 BA + 1 EC + 1 AR | C-5 |
| T2-155 | Smelter Wear Kit | 1 BA + 1 CS + 1 TC | C-5 |
| T2-156 | Casting Fixture Rack | 1 BA + 1 TF + 1 SC | C-5 |
| T2-157 | Precision Workholding Table | 1 BA + 1 PC + 1 AR | C-5 |
| T2-158 | Additive Build Plate | 1 BA + 1 CS + 1 TC | C-5 |
| T2-159 | Extrusion Tooling Set | 1 BA + 1 TF + 1 SC | C-5 |
| T2-160 | Crystal Growth Fixture | 1 BA + 1 PC + 1 AR | C-5 |

Crusher Rebuild Kit and Smelter Wear Kit contain passive replacement parts, not complete machines. Precision Workholding Table, Additive Build Plate, Extrusion Tooling Set, and Crystal Growth Fixture require separately purchased production equipment. None grants a tooling supplier the right to sell a refinery or factory.

### 8.9. Freight & Warehouse Equipment

**Authored company:** Crossdock Cargo Systems. **Scope:** Cargo handling, shipping containers, storage hardware, and supply transport equipment.

Naming logic: Warehouse and trucking terminology makes every item recognizable on a purchase order.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-161 | Cargo Tie-Down | 1 IF + 1 TF | C-3 |
| T2-162 | Tamper-Evident Cargo Seal | 1 BA + 1 TF | C-3 |
| T2-163 | Food-Grade Shipping Drum | 1 IF + 1 BA + 1 TF | C-4 |
| T2-164 | Warehouse Storage Rack | 1 EC + 1 PG + 1 TF | C-4 |
| T2-165 | Cargo Transfer Adapter | 1 TF + 1 SC | C-4 |
| T2-166 | Gravity Conveyor Section | 1 TF + 1 SC | C-4 |
| T2-167 | Container Lock Assembly | 1 TF + 1 PC | C-4 |
| T2-168 | Heavy-Duty Shipping Pallet | 1 TF + 1 AR | C-4 |
| T2-169 | Orbital Shipping Container | 1 IF + 1 BA + 1 EC + 1 TF | C-5 |
| T2-170 | Medical Cold-Chain Container | 1 IF + 1 BA + 1 PG + 1 TF | C-5 |
| T2-171 | Pressurized Cargo Box | 1 IF + 1 TF + 1 SC | C-5 |
| T2-172 | Hazardous Materials Container | 1 BA + 1 TF + 1 SC | C-5 |
| T2-173 | Self-Driving Cargo Cart | 1 EC + 1 CS + 1 TF | C-5 |
| T2-174 | Bulk Food Storage Bin | 1 PG + 1 TC + 1 TF | C-5 |
| T2-175 | Cargo Transfer Airlock | 1 IF + 1 TF + 1 SC | C-5 |
| T2-176 | Orbital Container Rack | 1 BA + 1 TF + 1 PC | C-5 |
| T2-177 | Ship Loading Platform | 1 EC + 1 TF + 1 AR | C-5 |
| T2-178 | Spaceport Cargo Crane | 1 PG + 1 CS + 1 TF | C-5 |
| T2-179 | Propellant Transfer Station | 1 IF + 1 TC + 1 TF | C-5 |
| T2-180 | Medical Gas Storage Tank | 1 BA + 1 TF + 1 SC | C-5 |

Freight-handling machinery moves or stores goods; it does not refine stock or manufacture saleable output. Warehouse hardware sales do not transfer Dustline Spatial Solutions Corp.’s storage royalty rights.

### 8.10. Defense & Emergency Systems

**Authored company:** Hardstop Defense Systems. **Scope:** Defensive equipment, emergency containment, evacuation, and rescue systems.

Naming logic: Defense-contractor language gives the mission and hardware type, while protecting room for rescue and civilian survival.

| Product ID | Good | T1 Recipe | Complexity |
|---|---|---|---|
| T2-181 | Shielding Fabric | 1 EC + 1 AR | C-3 |
| T2-182 | Impact Absorber Block | 1 PG + 1 AR | C-3 |
| T2-183 | Fragment Armor Panel | 1 IF + 1 BA + 1 AR | C-4 |
| T2-184 | Radiation Guard Panel | 1 EC + 1 PG + 1 AR | C-4 |
| T2-185 | Emergency Pressure Curtain | 1 TF + 1 AR | C-4 |
| T2-186 | Fire Containment Door | 1 CS + 1 AR | C-4 |
| T2-187 | Search-and-Rescue Beacon | 1 TC + 1 AR | C-4 |
| T2-188 | Electrical Surge Arrestor | 1 TF + 1 AR | C-4 |
| T2-189 | Emergency Isolation Valve | 1 IF + 1 EC + 1 PG + 1 AR | C-5 |
| T2-190 | Rescue Cable Winch | 1 BA + 1 EC + 1 PG + 1 AR | C-5 |
| T2-191 | Electromagnetic Defense Array | 1 EC + 1 TF + 1 AR | C-5 |
| T2-192 | Radiation Shelter Module | 1 PG + 1 TF + 1 AR | C-5 |
| T2-193 | Emergency Hull Seal Kit | 1 IF + 1 PC + 1 AR | C-5 |
| T2-194 | Automatic Fire Suppression Pack | 1 BA + 1 CS + 1 AR | C-5 |
| T2-195 | Point Defense Drone | 1 EC + 1 TC + 1 AR | C-5 |
| T2-196 | Collision Warning System | 1 PG + 1 TF + 1 AR | C-5 |
| T2-197 | Crew Evacuation Pod | 1 IF + 1 SC + 1 AR | C-5 |
| T2-198 | Autonomous Rescue Shuttle | 1 BA + 1 PC + 1 AR | C-5 |
| T2-199 | Perimeter Warning Network | 1 EC + 1 CS + 1 AR | C-5 |
| T2-200 | Solar Radiation Protection System | 1 PG + 1 TC + 1 AR | C-5 |

## 9. Numbered Companies — Simple, Stable Names

Naming logic: each sector has one recognizable generic business name. A `0x`-prefixed hex serial number identifies the individual company. The simplicity is intentional.

Use the **Generic Company Base** from sections 5 and 6, followed by a space and the firm’s `0x`-prefixed sector serial:

- Tier 1: `{Generic Company Base} 0x{Serial:x}` — for example, **Industrial Fluids 0x1**.
- Tier 2: `{Generic Company Base} 0x{Serial:x}` — for example, **Power Equipment 0x1**.

No zero-padding; the serial is written as a plain lowercase hex value after `0x`. Serials expand naturally when necessary. The ten Tier 1 bases and ten Tier 2 bases are all distinct, so numbering may restart at 1 independently in each sector without causing duplicate names.

### Complete Generic-Name Mapping

| Tier | Stable Sector Key | Generic Base | First Display Name |
|---|---|---|---|
| T1 | W | Industrial Fluids | Industrial Fluids 0x1 |
| T1 | E | Alloy Refining | Alloy Refining 0x1 |
| T1 | F | Energy Materials | Energy Materials 0x1 |
| T1 | A | Process Gases | Process Gases 0x1 |
| T1 | W+E | Ceramic Materials | Ceramic Materials 0x1 |
| T1 | W+F | Thermal Materials | Thermal Materials 0x1 |
| T1 | W+A | Technical Fibers | Technical Fibers 0x1 |
| T1 | E+F | Semiconductor Materials | Semiconductor Materials 0x1 |
| T1 | E+A | Composite Materials | Composite Materials 0x1 |
| T1 | F+A | Active Chemicals | Active Chemicals 0x1 |
| T2 | S01 | Power Equipment | Power Equipment 0x1 |
| T2 | S02 | Propulsion Systems | Propulsion Systems 0x1 |
| T2 | S03 | Shipbuilding Works | Shipbuilding Works 0x1 |
| T2 | S04 | Habitat Systems | Habitat Systems 0x1 |
| T2 | S05 | Service Robotics | Service Robotics 0x1 |
| T2 | S06 | Computing Systems | Computing Systems 0x1 |
| T2 | S07 | Scientific Instruments | Scientific Instruments 0x1 |
| T2 | S08 | Industrial Tooling | Industrial Tooling 0x1 |
| T2 | S09 | Freight Equipment | Freight Equipment 0x1 |
| T2 | S10 | Defense Systems | Defense Systems 0x1 |

### Deterministic Allocation

1. Group generated firms by tier and sector. Exclude explicitly authored identities from numbered-name allocation.
2. For initial migration, sort each group by immutable numeric agent ID in ascending numeric order. If IDs are nonnumeric strings, use their canonical UTF-8 byte order instead. Select one rule matching the actual ID type and keep it fixed.
3. Assign sector serials starting at 1 and persist them. Do not rebuild the sequence from the current active population.
4. For a new firm, atomically allocate the next unused serial in its tier and sector. Never recycle a retired company’s serial and never renumber surviving firms.
5. Persist the naming-sector key. Ordinary production changes do not rename the company. A deliberate registered sector change allocates a new serial in the destination sector and retires the old registered name.

```python
def company_display_name(tier, generic_base, sector_serial):
    if tier not in (1, 2) or sector_serial < 1:
        raise ValueError("Invalid tier or sector serial")
    return f"{generic_base} 0x{sector_serial:x}"
```

If allocation is even, 100 refineries in each material sector yield hex serials 0x1–0x64. Six thousand manufacturers in each manufacturing sector yield hex serials 0x1–0x1770. The same rule works with an uneven distribution: it requires no fixed population per sector.

Store the authored identity or cohort label in a separate field. Do not prepend Clearwater, Switchyard, or another authored company name to every agent in its cohort. For example, **Power Equipment 0x2a** is an independent firm name, not “Switchyard Power Systems 0x2a.”

## 10. Interface and Service Labels

Naming logic: use familiar American business software labels, with plain simulation metrics and clearly attributed corporate services.

| Surface or Concept | Display Label | Usage |
|---|---|---|
| Live economy view | Colony Overview | The watchable economy, its activity, and its condition. |
| Physical connection view | Supply Chain | Extraction through consumption. |
| T0 category | Resource Companies | The 20 extraction corporations. |
| T1 category | Refineries | The 1,000 refining agents. |
| T2 category | Manufacturers | The 60,000 manufacturing firms. |
| Buyer category | Distributors | The 1,000,000 distributors. |
| Raw trading | Element Markets | Water, Earth, Fire, and Air. |
| Refined-stock trading | Material Markets | The ten refined stocks. |
| Finished-goods trading | Product Markets | The 200 manufactured goods. |
| Equipment trading | Machinery Market | The single market supplied by Mudrock Machinery Co. |
| T1 machinery section | Refining Equipment | Refining Bench and Refining Cell configurations. |
| T2 machinery section | Production Equipment | Production Bench, Production Cell, and Production Hall. |
| Factory view | Production | Installed equipment, processes, and output. |
| Stock view | Inventory | Materials and finished goods on hand. |
| Facility capacity view | Storage | Capacity, utilization, and royalty charges. |
| Storage charge | Storage Royalty | Show Dustline Spatial Solutions Corp. as the recipient. |
| Financial services | Banking | Steam Ridge Financial Inc. is the sole provider. |
| Paid promotion | Advertising | Flare Basin Advertising Incorporated is the sole provider. |
| Policy service | Colony Policy | Provided by Baseline Resource Corporation. |
| Policy announcement | Policy Update | Show changed parameters and effective time. |
| Administrative service | Business Registry | Provided by Union Charter Resources Inc.. |
| Statistics service | Market Intelligence | Provided by Signal Point Resources Corp.. |
| Community service | Community Hub | Provided by Commonline Resources Company. |
| Forum list | Discussion Boards | Inside Community Hub. |
| Firm detail page | Company Profile | Display the exact registered name. |
| Maker field | Manufacturer | Separate from generic product and equipment names. |
| Asking price | Price | Show currency and unit separately. |
| Available quantity | Supply | State the applicable measurement window. |
| Requested quantity | Demand | Use the corresponding measurement window. |
| Reliability metric | Reliability | Explain the actual simulation definition in help text. |
| Buyer relationship metric | Supplier Loyalty | Keep it distinct from seller reliability. |
| Trade history | Transactions | Buyer, seller, product, quantity, price, and time. |

An example notification reads: “Backup battery racks are in short supply. Power Equipment 0x2a raised its price.” Another reads: “Mudrock Machinery Co. delivered a refining cell.” These use lowercase product and equipment names in prose while preserving registered company names.

## 11. Migration and Consistency

Naming logic: stable IDs carry identity; display names communicate the new setting. The naming change must not silently change economic mechanics.

- Keep W, E, F, A and their compound codes as internal material keys. Section 3 is their new display-name and symbol map.
- Keep T2-001 through T2-200 as product keys. Section 8 gives the complete replacement list and preserves every recipe and complexity.
- Keep the ten sector slots in their original order. Their display names change to section 6. The tooling sector’s narrower scope is deliberate because only Mudrock Machinery Co. may produce complete manufacturing equipment.
- For code already migrated against the earlier catalog, T0-01 through T0-20 preserve the same coverage and responsibility slots. Replace the names using section 4. T1-01 through T1-10 remain in material order; T2-C01 through T2-C10 remain in sector order.
- Equipment class IDs in this document are catalog keys. Map them to existing code IDs rather than changing stored IDs unnecessarily.
- The previous prohibitions on numeric display-name suffixes and the previous house/district/berth generation scheme are superseded. Use section 9 exclusively for generated company names.
- The policy, registry, intelligence, and community services are corporate functions. They do not create four more companies or expand their extraction coverage.
- Do not infer banking rights from a capacitor bank, advertising rights from a communications system, or storage royalties from a warehouse rack.
- The 200 goods do not include the five equipment classes. Recipe entries with identical ingredient lists remain distinct products because their manufacturing processes and tooling differ.
- No new fee rate, advertising effect, financing rule, production-machine recipe, or war mechanic is prescribed here.

### Completeness Check

| Category | Count or Coverage |
|---|---|
| Game name | 1: Star Business |
| Raw elements | 4, unchanged |
| Refined materials | 10 |
| Extraction companies | 20 |
| Four-market companies | 2 |
| Three-market companies | 4 |
| Two-market companies | 6 |
| Single-market companies | 8; two per element |
| Extractors per element | 10 |
| Civic roles | 4, one per three-market company |
| Special duties | 6, one per two-market company: machinery, finance, warehousing/land, advertising, games, utilities |
| Authored refinery identities | 10 |
| Manufacturing sectors | 10 |
| Authored manufacturing identities | 10 |
| Finished goods | 200; 20 per sector |
| Refining classes | 2 |
| Refining configuration names | 10 |
| Production classes | 3 |
| Generic company bases | 20 |
| Numbered-firm capacity | All 1,000 refineries and 60,000 manufacturers, including uneven sector populations |

Source: the attached `recipes.md` supplies the original material keys, product IDs, recipes, and complexity values. Company histories, replacement names, and presentation conventions are creative proposals for this setting.
