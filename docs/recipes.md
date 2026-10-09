# Recipe List

The full supply-chain recipes. Codes map to the T1 materials below; T2 goods are built from those materials. The recipe keys, ingredient quantities and complexity values are preserved exactly from the original `recipes.md`; the product concepts, names and sector labels follow the Long Muster naming catalogue. `Code` is the legacy recipe key retained as an internal compatibility key; `Symbol` is the new two-letter market symbol.

## T1 materials (10) — refined from the four raw elements

| Code | Symbol | Material | Recipe |
|---|---|---|---|
| W | PF | Process Fluid | 1 Water |
| E | SA | Structural Alloy | 1 Earth |
| F | CM | Charge Medium | 1 Fire |
| A | WG | Working Gas | 1 Air |
| W+E | MC | Mineral Ceramic | 1 Water + 1 Earth |
| W+F | TG | Thermal Gel | 1 Water + 1 Fire |
| W+A | MS | Membrane Stock | 1 Water + 1 Air |
| E+F | CC | Circuit Crystal | 1 Earth + 1 Fire |
| E+A | RC | Resin Composite | 1 Earth + 1 Air |
| F+A | RS | Reactive Salt | 1 Fire + 1 Air |

## T2 goods (200) — manufactured from T1 materials

| Code | Good | Recipe | Complexity | Sector |
|---|---|---|---|---|
| T2-001 | Feeder Rail | 1 W + 1 E + 1 F | C-3 | Grid & Thermal |
| T2-002 | Charge Intake | 1 F + 1 W+E | C-3 | Grid & Thermal |
| T2-003 | Reserve Cell Stack | 1 W + 1 E + 1 F + 1 A | C-4 | Grid & Thermal |
| T2-004 | Load Balancer | 1 W + 1 F + 1 E+F | C-4 | Grid & Thermal |
| T2-005 | Heat Transfer Block | 1 F + 1 A + 1 E+A | C-4 | Grid & Thermal |
| T2-006 | Discharge Stack | 1 W + 1 F + 1 F+A | C-4 | Grid & Thermal |
| T2-007 | Sunskin Sheet | 1 E + 1 F + 1 W+E | C-4 | Grid & Thermal |
| T2-008 | Cooling Wing | 1 F + 1 A + 1 W+F | C-4 | Grid & Thermal |
| T2-009 | Baseload Core | 1 W + 1 E + 1 F + 1 W+E | C-5 | Grid & Thermal |
| T2-010 | Pulse Reserve Chamber | 1 W + 1 F + 1 A + 1 W+F | C-5 | Grid & Thermal |
| T2-011 | Sunward Collector Ring | 1 E + 1 F + 1 A + 1 W+A | C-5 | Grid & Thermal |
| T2-012 | Frontier Generator Station | 1 W + 1 E + 1 F + 1 E+F | C-5 | Grid & Thermal |
| T2-013 | Blackout Reserve Rack | 1 W + 1 F + 1 A + 1 E+A | C-5 | Grid & Thermal |
| T2-014 | Peakload Generator | 1 E + 1 F + 1 A + 1 F+A | C-5 | Grid & Thermal |
| T2-015 | Field Supply Pack | 1 F + 1 W+A + 1 F+A | C-5 | Grid & Thermal |
| T2-016 | Wasteheat Recovery Bank | 1 F + 1 E+F + 1 F+A | C-5 | Grid & Thermal |
| T2-017 | Powerbeam Emitter | 1 F + 1 E+A + 1 F+A | C-5 | Grid & Thermal |
| T2-018 | Powerbeam Rectenna | 1 F + 1 W+E + 1 W+F | C-5 | Grid & Thermal |
| T2-019 | Close-Orbit Collector | 1 F + 1 W+A + 1 E+F | C-5 | Grid & Thermal |
| T2-020 | Watchlight Generator | 1 F + 1 E+A + 1 F+A | C-5 | Grid & Thermal |
| T2-021 | Exhaust Throat | 1 W + 1 W+F | C-3 | Drives & Guidance |
| T2-022 | Reaction Mass Capsule | 1 E + 1 W+F | C-3 | Drives & Guidance |
| T2-023 | Trim Jet | 1 W + 1 E + 1 W+F | C-4 | Drives & Guidance |
| T2-024 | Ion Focusing Ring | 1 E + 1 F + 1 W+F | C-4 | Drives & Guidance |
| T2-025 | Plasma Feed Head | 1 E + 1 A + 1 W+F | C-4 | Drives & Guidance |
| T2-026 | Feed Regulator | 1 W+E + 1 W+F | C-4 | Drives & Guidance |
| T2-027 | Attitude Rotor | 1 W+F + 1 W+A | C-4 | Drives & Guidance |
| T2-028 | Drift Reference Block | 1 W+F + 1 E+F | C-4 | Drives & Guidance |
| T2-029 | Cruise Ion Drive | 1 W + 1 E + 1 A + 1 W+F | C-5 | Drives & Guidance |
| T2-030 | Transfer Plasma Drive | 1 E + 1 F + 1 A + 1 W+F | C-5 | Drives & Guidance |
| T2-031 | Longburn Engine | 1 W + 1 W+E + 1 W+F | C-5 | Drives & Guidance |
| T2-032 | Pulse Drive Vessel | 1 E + 1 W+F + 1 W+A | C-5 | Drives & Guidance |
| T2-033 | Photon Sail Frame | 1 F + 1 W+F + 1 E+F | C-5 | Drives & Guidance |
| T2-034 | Plasma Sail Loop | 1 A + 1 W+F + 1 E+A | C-5 | Drives & Guidance |
| T2-035 | Slingshot Course Unit | 1 W + 1 W+F + 1 F+A | C-5 | Drives & Guidance |
| T2-036 | Farpoint Guidance Rack | 1 E + 1 W+E + 1 W+F | C-5 | Drives & Guidance |
| T2-037 | Berthing Drive Pack | 1 F + 1 W+F + 1 W+A | C-5 | Drives & Guidance |
| T2-038 | Touchdown Thrust Frame | 1 A + 1 W+F + 1 E+F | C-5 | Drives & Guidance |
| T2-039 | Departure Booster Rack | 1 W + 1 W+F + 1 E+A | C-5 | Drives & Guidance |
| T2-040 | Towboat Drive Block | 1 E + 1 W+F + 1 F+A | C-5 | Drives & Guidance |
| T2-041 | Outer Skin Blank | 1 F + 1 W+E | C-3 | Hull & Dock Construction |
| T2-042 | Loadbearing Rib | 1 A + 1 W+E | C-3 | Hull & Dock Construction |
| T2-043 | Compartment Partition | 1 W + 1 E + 1 W+E | C-4 | Hull & Dock Construction |
| T2-044 | Service Lock Hatch | 1 F + 1 A + 1 W+E | C-4 | Hull & Dock Construction |
| T2-045 | Berth Mating Ring | 1 W + 1 E + 1 W+E | C-4 | Hull & Dock Construction |
| T2-046 | Viewport Shutter | 1 W+E + 1 W+F | C-4 | Hull & Dock Construction |
| T2-047 | Touchdown Leg | 1 W+E + 1 E+A | C-4 | Hull & Dock Construction |
| T2-048 | Freight Aperture Gate | 1 W+E + 1 F+A | C-4 | Hull & Dock Construction |
| T2-049 | Platform Truss Set | 1 W + 1 E + 1 F + 1 W+E | C-5 | Hull & Dock Construction |
| T2-050 | Picket Cutter Frame | 1 W + 1 E + 1 A + 1 W+E | C-5 | Hull & Dock Construction |
| T2-051 | Bulk Carrier Frame | 1 F + 1 W+E + 1 W+F | C-5 | Hull & Dock Construction |
| T2-052 | Charting Vessel Frame | 1 A + 1 W+E + 1 W+F | C-5 | Hull & Dock Construction |
| T2-053 | Prospector Barge Frame | 1 W + 1 W+E + 1 W+F | C-5 | Hull & Dock Construction |
| T2-054 | Harbour Tug Frame | 1 E + 1 W+E + 1 W+A | C-5 | Hull & Dock Construction |
| T2-055 | Convoy Escort Frame | 1 F + 1 W+E + 1 E+F | C-5 | Hull & Dock Construction |
| T2-056 | Ascent Stage Shell | 1 A + 1 W+E + 1 E+A | C-5 | Hull & Dock Construction |
| T2-057 | Return Capsule Body | 1 W + 1 W+E + 1 F+A | C-5 | Hull & Dock Construction |
| T2-058 | Station Backbone | 1 E + 1 W+E + 1 W+F | C-5 | Hull & Dock Construction |
| T2-059 | Berth Junction Frame | 1 F + 1 W+E + 1 W+A | C-5 | Hull & Dock Construction |
| T2-060 | Slipway Truss | 1 A + 1 W+E + 1 E+F | C-5 | Hull & Dock Construction |
| T2-061 | Interior Liner Sheet | 1 W + 1 F + 1 A | C-3 | Settlement & Life Support |
| T2-062 | Foundation Tie | 1 W + 1 W+F | C-3 | Settlement & Life Support |
| T2-063 | Pressure Partition | 1 W + 1 E + 1 F + 1 A | C-4 | Settlement & Life Support |
| T2-064 | Lock Chamber Gate | 1 W + 1 F + 1 W+A | C-4 | Settlement & Life Support |
| T2-065 | Service Deck Panel | 1 W + 1 F + 1 E+F | C-4 | Settlement & Life Support |
| T2-066 | Potable Main Section | 1 W + 1 E + 1 E+A | C-4 | Settlement & Life Support |
| T2-067 | Exposure Curtain | 1 W + 1 F + 1 F+A | C-4 | Settlement & Life Support |
| T2-068 | Daycycle Luminaire | 1 W + 1 A + 1 W+E | C-4 | Settlement & Life Support |
| T2-069 | Living Compartment | 1 W + 1 E + 1 F + 1 W+E | C-5 | Settlement & Life Support |
| T2-070 | Settlement Ring Shell | 1 W + 1 F + 1 A + 1 W+F | C-5 | Settlement & Life Support |
| T2-071 | Frontier Commons Module | 1 W + 1 E + 1 F + 1 W+A | C-5 | Settlement & Life Support |
| T2-072 | Spin Section Hub | 1 W + 1 F + 1 A + 1 E+F | C-5 | Settlement & Life Support |
| T2-073 | Rockhold Foundation | 1 W + 1 E + 1 F + 1 E+A | C-5 | Settlement & Life Support |
| T2-074 | Transit Refuge Module | 1 W + 1 F + 1 A + 1 F+A | C-5 | Settlement & Life Support |
| T2-075 | Mixed-Crew Quarters | 1 W + 1 W+E + 1 W+F | C-5 | Settlement & Life Support |
| T2-076 | Cultivation Room Shell | 1 W + 1 W+A + 1 E+F | C-5 | Settlement & Life Support |
| T2-077 | Isolation Ward Module | 1 W + 1 E+A + 1 F+A | C-5 | Settlement & Life Support |
| T2-078 | Garden Pressure Canopy | 1 W + 1 W+E + 1 W+F | C-5 | Settlement & Life Support |
| T2-079 | Buried Habitat Sleeve | 1 W + 1 W+A + 1 E+F | C-5 | Settlement & Life Support |
| T2-080 | Tether Ground Footing | 1 W + 1 E+A + 1 F+A | C-5 | Settlement & Life Support |
| T2-081 | Service Joint Cartridge | 1 W + 1 E+A | C-3 | Robotics & Field Service |
| T2-082 | Linkage Pushrod | 1 E + 1 E+A | C-3 | Robotics & Field Service |
| T2-083 | Adaptive Grip Head | 1 F + 1 A + 1 E+A | C-4 | Robotics & Field Service |
| T2-084 | Wrist Interface Ring | 1 W + 1 E + 1 E+A | C-4 | Robotics & Field Service |
| T2-085 | Rubble Wheel | 1 F + 1 A + 1 E+A | C-4 | Robotics & Field Service |
| T2-086 | Reach Limb | 1 W+E + 1 E+A | C-4 | Robotics & Field Service |
| T2-087 | Contact Sense Pad | 1 W+F + 1 E+A | C-4 | Robotics & Field Service |
| T2-088 | Pressure Muscle Pack | 1 W+A + 1 E+A | C-4 | Robotics & Field Service |
| T2-089 | Utility Attendant | 1 E + 1 F + 1 A + 1 E+A | C-5 | Robotics & Field Service |
| T2-090 | Hull Cleaning Crawler | 1 W + 1 E + 1 F + 1 E+A | C-5 | Robotics & Field Service |
| T2-091 | Faultfinding Walker | 1 W + 1 W+E + 1 E+A | C-5 | Robotics & Field Service |
| T2-092 | Pit Scout | 1 E + 1 W+E + 1 E+A | C-5 | Robotics & Field Service |
| T2-093 | Patch Service Crawler | 1 F + 1 E+A + 1 F+A | C-5 | Robotics & Field Service |
| T2-094 | Freight Porter | 1 A + 1 W+E + 1 E+A | C-5 | Robotics & Field Service |
| T2-095 | Clinical Microhandler | 1 W + 1 W+F + 1 E+A | C-5 | Robotics & Field Service |
| T2-096 | Exterior Service Walker | 1 E + 1 W+A + 1 E+A | C-5 | Robotics & Field Service |
| T2-097 | Terrain Recon Rover | 1 F + 1 E+F + 1 E+A | C-5 | Robotics & Field Service |
| T2-098 | Conduit Service Crawler | 1 A + 1 E+A + 1 F+A | C-5 | Robotics & Field Service |
| T2-099 | Settlement Caretaker | 1 W + 1 W+E + 1 E+A | C-5 | Robotics & Field Service |
| T2-100 | Recovery Manipulator | 1 E + 1 W+F + 1 E+A | C-5 | Robotics & Field Service |
| T2-101 | Signal Path Strip | 1 F + 1 E+F | C-3 | Computation & Signals |
| T2-102 | State Storage Tile | 1 A + 1 E+F | C-3 | Computation & Signals |
| T2-103 | Control Backplane | 1 W + 1 E + 1 E+F | C-4 | Computation & Signals |
| T2-104 | Training Cache Block | 1 F + 1 A + 1 E+F | C-4 | Computation & Signals |
| T2-105 | Local Link Radio | 1 E+F + 1 E+A | C-4 | Computation & Signals |
| T2-106 | Line Booster | 1 E+F + 1 F+A | C-4 | Computation & Signals |
| T2-107 | Packet Junction | 1 W+E + 1 E+F | C-4 | Computation & Signals |
| T2-108 | Message Queue Module | 1 W+F + 1 E+F | C-4 | Computation & Signals |
| T2-109 | Compute Service Rack | 1 W + 1 E + 1 A + 1 E+F | C-5 | Computation & Signals |
| T2-110 | Course Solver Rack | 1 E + 1 F + 1 A + 1 E+F | C-5 | Computation & Signals |
| T2-111 | Scheduling Engine | 1 F + 1 E+F + 1 E+A | C-5 | Computation & Signals |
| T2-112 | Shielded Control Computer | 1 A + 1 E+F + 1 E+A | C-5 | Computation & Signals |
| T2-113 | Coherent Compute Cell | 1 W + 1 W+A + 1 E+F | C-5 | Computation & Signals |
| T2-114 | Neighbourhood Server | 1 E + 1 E+F + 1 E+A | C-5 | Computation & Signals |
| T2-115 | Convoy Network Server | 1 F + 1 E+F + 1 F+A | C-5 | Computation & Signals |
| T2-116 | High-Orbit Repeater | 1 A + 1 W+E + 1 E+F | C-5 | Computation & Signals |
| T2-117 | Tightbeam Link Terminal | 1 W + 1 W+F + 1 E+F | C-5 | Computation & Signals |
| T2-118 | Longreach Radio Mast | 1 E + 1 W+A + 1 E+F | C-5 | Computation & Signals |
| T2-119 | Delay Network Gateway | 1 F + 1 E+F + 1 E+A | C-5 | Computation & Signals |
| T2-120 | Continuity Archive | 1 A + 1 E+F + 1 F+A | C-5 | Computation & Signals |
| T2-121 | Optical Pickup Blank | 1 A + 1 W+A | C-3 | Survey & Diagnostics |
| T2-122 | Exposure Sensing Sheet | 1 A + 1 E+F | C-3 | Survey & Diagnostics |
| T2-123 | Composition Reader | 1 W + 1 E + 1 F + 1 A | C-4 | Survey & Diagnostics |
| T2-124 | Rangefinding Dish | 1 W + 1 A + 1 W+F | C-4 | Survey & Diagnostics |
| T2-125 | Laser Survey Head | 1 W + 1 A + 1 W+A | C-4 | Survey & Diagnostics |
| T2-126 | Heat Fault Imager | 1 E + 1 A + 1 E+F | C-4 | Survey & Diagnostics |
| T2-127 | Flux Pickup | 1 F + 1 A + 1 E+A | C-4 | Survey & Diagnostics |
| T2-128 | Ground Motion Pickup | 1 W + 1 A + 1 F+A | C-4 | Survey & Diagnostics |
| T2-129 | Longwatch Telescope | 1 W + 1 F + 1 A + 1 W+E | C-5 | Survey & Diagnostics |
| T2-130 | World Survey Capsule | 1 W + 1 E + 1 A + 1 W+F | C-5 | Survey & Diagnostics |
| T2-131 | Rock Census Probe | 1 W + 1 F + 1 A + 1 W+A | C-5 | Survey & Diagnostics |
| T2-132 | Forward Survey Beacon | 1 W + 1 E + 1 A + 1 E+F | C-5 | Survey & Diagnostics |
| T2-133 | Sample Return Rover | 1 W + 1 F + 1 A + 1 E+A | C-5 | Survey & Diagnostics |
| T2-134 | Strata Listening Kit | 1 W + 1 E + 1 A + 1 F+A | C-5 | Survey & Diagnostics |
| T2-135 | Orbital Mapping Camera | 1 A + 1 W+E + 1 W+F | C-5 | Survey & Diagnostics |
| T2-136 | Particle Watch Station | 1 A + 1 W+A + 1 E+F | C-5 | Survey & Diagnostics |
| T2-137 | Stellar Weather Monitor | 1 A + 1 E+A + 1 F+A | C-5 | Survey & Diagnostics |
| T2-138 | Deepband Listening Array | 1 A + 1 W+E + 1 W+F | C-5 | Survey & Diagnostics |
| T2-139 | Clinical Scan Bed | 1 A + 1 W+A + 1 E+F | C-5 | Survey & Diagnostics |
| T2-140 | Worldfinder Optics Rack | 1 A + 1 E+A + 1 F+A | C-5 | Survey & Diagnostics |
| T2-141 | Cutter Insert | 1 E + 1 E+A | C-3 | Tooling & Extraction Hardware |
| T2-142 | Lapping Grit Batch | 1 E + 1 F+A | C-3 | Tooling & Extraction Hardware |
| T2-143 | Rotary Bit Crown | 1 E + 1 A + 1 W+E | C-4 | Tooling & Extraction Hardware |
| T2-144 | Breaker Jaw Liner | 1 E + 1 F + 1 W+F | C-4 | Tooling & Extraction Hardware |
| T2-145 | Finish Abrasion Disc | 1 E + 1 A + 1 W+A | C-4 | Tooling & Extraction Hardware |
| T2-146 | Melt Vessel Sleeve | 1 W + 1 E + 1 E+F | C-4 | Tooling & Extraction Hardware |
| T2-147 | Forming Die Block | 1 E + 1 F + 1 E+A | C-4 | Tooling & Extraction Hardware |
| T2-148 | Joining Tip Cassette | 1 E + 1 A + 1 F+A | C-4 | Tooling & Extraction Hardware |
| T2-149 | Furnace Hearth Set | 1 E + 1 F + 1 A + 1 W+E | C-5 | Tooling & Extraction Hardware |
| T2-150 | Drill Guide Frame | 1 W + 1 E + 1 A + 1 W+F | C-5 | Tooling & Extraction Hardware |
| T2-151 | Regolith Bucket Shell | 1 E + 1 F + 1 A + 1 W+A | C-5 | Tooling & Extraction Hardware |
| T2-152 | Crusher Wear Kit | 1 W + 1 E + 1 A + 1 E+F | C-5 | Tooling & Extraction Hardware |
| T2-153 | Separation Drum Sleeve | 1 E + 1 F + 1 A + 1 E+A | C-5 | Tooling & Extraction Hardware |
| T2-154 | Process Bath Liner | 1 W + 1 E + 1 F + 1 F+A | C-5 | Tooling & Extraction Hardware |
| T2-155 | Smelter Throat Set | 1 E + 1 W+E + 1 W+F | C-5 | Tooling & Extraction Hardware |
| T2-156 | Casting Form Rack | 1 E + 1 W+A + 1 E+F | C-5 | Tooling & Extraction Hardware |
| T2-157 | Workholding Fixture Bed | 1 E + 1 E+A + 1 F+A | C-5 | Tooling & Extraction Hardware |
| T2-158 | Deposition Build Tray | 1 E + 1 W+E + 1 W+F | C-5 | Tooling & Extraction Hardware |
| T2-159 | Extrusion Die Cassette | 1 E + 1 W+A + 1 E+F | C-5 | Tooling & Extraction Hardware |
| T2-160 | Crystal Seed Cradle | 1 E + 1 E+A + 1 F+A | C-5 | Tooling & Extraction Hardware |
| T2-161 | Load Lash | 1 W + 1 W+A | C-3 | Freight & Stores |
| T2-162 | Tamper Witness Strip | 1 E + 1 W+A | C-3 | Freight & Stores |
| T2-163 | Ration Transport Drum | 1 W + 1 E + 1 W+A | C-4 | Freight & Stores |
| T2-164 | Stores Shelf Frame | 1 F + 1 A + 1 W+A | C-4 | Freight & Stores |
| T2-165 | Freight Dock Coupling | 1 W+A + 1 E+F | C-4 | Freight & Stores |
| T2-166 | Roller Track Section | 1 W+A + 1 E+F | C-4 | Freight & Stores |
| T2-167 | Berth Holding Claw | 1 W+A + 1 E+A | C-4 | Freight & Stores |
| T2-168 | Load Skid | 1 W+A + 1 F+A | C-4 | Freight & Stores |
| T2-169 | General Freight Capsule | 1 W + 1 E + 1 F + 1 W+A | C-5 | Freight & Stores |
| T2-170 | Coldchain Medical Carrier | 1 W + 1 E + 1 A + 1 W+A | C-5 | Freight & Stores |
| T2-171 | Sealed Goods Container | 1 W + 1 W+A + 1 E+F | C-5 | Freight & Stores |
| T2-172 | Hazard Isolation Chest | 1 E + 1 W+A + 1 E+F | C-5 | Freight & Stores |
| T2-173 | Self-Routing Load Cart | 1 F + 1 W+E + 1 W+A | C-5 | Freight & Stores |
| T2-174 | Dry Ration Hopper | 1 A + 1 W+F + 1 W+A | C-5 | Freight & Stores |
| T2-175 | Vacuum Transfer Lock | 1 W + 1 W+A + 1 E+F | C-5 | Freight & Stores |
| T2-176 | Orbital Stowage Frame | 1 E + 1 W+A + 1 E+A | C-5 | Freight & Stores |
| T2-177 | Ship Loading Bridge | 1 F + 1 W+A + 1 F+A | C-5 | Freight & Stores |
| T2-178 | Quayside Lift | 1 A + 1 W+E + 1 W+A | C-5 | Freight & Stores |
| T2-179 | Drivefeed Transfer Skid | 1 W + 1 W+F + 1 W+A | C-5 | Freight & Stores |
| T2-180 | Breathing Gas Vessel | 1 E + 1 W+A + 1 E+F | C-5 | Freight & Stores |
| T2-181 | Field Screen Weave | 1 F + 1 F+A | C-3 | Defence & Recovery |
| T2-182 | Crush Cushion Block | 1 A + 1 F+A | C-3 | Defence & Recovery |
| T2-183 | Fragment Catch Panel | 1 W + 1 E + 1 F+A | C-4 | Defence & Recovery |
| T2-184 | Exposure Baffle | 1 F + 1 A + 1 F+A | C-4 | Defence & Recovery |
| T2-185 | Breach Stop Curtain | 1 W+A + 1 F+A | C-4 | Defence & Recovery |
| T2-186 | Firebreak Shutter | 1 W+E + 1 F+A | C-4 | Defence & Recovery |
| T2-187 | Distress Ping Unit | 1 W+F + 1 F+A | C-4 | Defence & Recovery |
| T2-188 | Overload Arrestor | 1 W+A + 1 F+A | C-4 | Defence & Recovery |
| T2-189 | Emergency Shutoff Block | 1 W + 1 F + 1 A + 1 F+A | C-5 | Defence & Recovery |
| T2-190 | Rescue Line Drum | 1 E + 1 F + 1 A + 1 F+A | C-5 | Defence & Recovery |
| T2-191 | Deflection Field Rack | 1 F + 1 W+A + 1 F+A | C-5 | Defence & Recovery |
| T2-192 | Storm Refuge Capsule | 1 A + 1 W+A + 1 F+A | C-5 | Defence & Recovery |
| T2-193 | Pressure Patch Kit | 1 W + 1 E+A + 1 F+A | C-5 | Defence & Recovery |
| T2-194 | Quench Response Pack | 1 E + 1 W+E + 1 F+A | C-5 | Defence & Recovery |
| T2-195 | Screen Interceptor | 1 F + 1 W+F + 1 F+A | C-5 | Defence & Recovery |
| T2-196 | Close-Pass Warning Unit | 1 A + 1 W+A + 1 F+A | C-5 | Defence & Recovery |
| T2-197 | Abandon-Ship Capsule | 1 W + 1 E+F + 1 F+A | C-5 | Defence & Recovery |
| T2-198 | Recovery Launch | 1 E + 1 E+A + 1 F+A | C-5 | Defence & Recovery |
| T2-199 | Approach Watch Network | 1 F + 1 W+E + 1 F+A | C-5 | Defence & Recovery |
| T2-200 | Particle Storm Screen | 1 A + 1 W+F + 1 F+A | C-5 | Defence & Recovery |
