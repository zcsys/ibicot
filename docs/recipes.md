# Recipe List

The full supply-chain recipes. Codes map to the T1 materials below; T2 goods are built from those materials. The recipe keys, ingredient quantities and complexity values are preserved exactly from the original `recipes.md`; the product concepts, names and sector labels follow the Star Business naming catalog. `Code` is the legacy recipe key retained as an internal compatibility key; `Symbol` is the new market symbol.

## T1 materials (10) — refined from the four raw elements

| Code | Symbol | Material | Recipe |
|---|---|---|---|
| W | IF | Industrial Fluid | 1 Water |
| E | BA | Bulk Alloy | 1 Earth |
| F | EC | Energy Carrier | 1 Fire |
| A | PG | Process Gas | 1 Air |
| W+E | CS | Ceramic Stock | 1 Water + 1 Earth |
| W+F | TC | Thermal Compound | 1 Water + 1 Fire |
| W+A | TF | Technical Fiber | 1 Water + 1 Air |
| E+F | SC | Semiconductor Crystal | 1 Earth + 1 Fire |
| E+A | PC | Polymer Composite | 1 Earth + 1 Air |
| F+A | AR | Active Reagent | 1 Fire + 1 Air |

## T2 goods (200) — manufactured from T1 materials

| Code | Good | Recipe | Complexity | Sector |
|---|---|---|---|---|
| T2-001 | Main Feeder Bar | 1 W + 1 E + 1 F | C-3 | Power & Utilities |
| T2-002 | Grid Intake Module | 1 F + 1 W+E | C-3 | Power & Utilities |
| T2-003 | Backup Battery Rack | 1 W + 1 E + 1 F + 1 A | C-4 | Power & Utilities |
| T2-004 | Voltage Converter | 1 W + 1 F + 1 E+F | C-4 | Power & Utilities |
| T2-005 | Coolant Exchange Block | 1 F + 1 A + 1 E+A | C-4 | Power & Utilities |
| T2-006 | Pulse Capacitor Rack | 1 W + 1 F + 1 F+A | C-4 | Power & Utilities |
| T2-007 | Solar Roof Panel | 1 E + 1 F + 1 W+E | C-4 | Power & Utilities |
| T2-008 | Radiator Wing | 1 F + 1 A + 1 W+F | C-4 | Power & Utilities |
| T2-009 | Station Reactor Package | 1 W + 1 E + 1 F + 1 W+E | C-5 | Power & Utilities |
| T2-010 | High-Energy Storage Vessel | 1 W + 1 F + 1 A + 1 W+F | C-5 | Power & Utilities |
| T2-011 | Orbital Solar Farm | 1 E + 1 F + 1 A + 1 W+A | C-5 | Power & Utilities |
| T2-012 | Remote Power Station | 1 W + 1 E + 1 F + 1 E+F | C-5 | Power & Utilities |
| T2-013 | Emergency Battery Room | 1 W + 1 F + 1 A + 1 E+A | C-5 | Power & Utilities |
| T2-014 | Peak Power Reactor | 1 E + 1 F + 1 A + 1 F+A | C-5 | Power & Utilities |
| T2-015 | Field Power Module | 1 F + 1 W+A + 1 F+A | C-5 | Power & Utilities |
| T2-016 | Waste Heat Generator | 1 F + 1 E+F + 1 F+A | C-5 | Power & Utilities |
| T2-017 | Wireless Power Transmitter | 1 F + 1 E+A + 1 F+A | C-5 | Power & Utilities |
| T2-018 | Wireless Power Receiver | 1 F + 1 W+E + 1 W+F | C-5 | Power & Utilities |
| T2-019 | Stellar Collection Array | 1 F + 1 W+A + 1 E+F | C-5 | Power & Utilities |
| T2-020 | Long-Life Generator | 1 F + 1 E+A + 1 F+A | C-5 | Power & Utilities |
| T2-021 | Engine Nozzle Insert | 1 W + 1 W+F | C-3 | Propulsion & Flight Systems |
| T2-022 | Propellant Feed Cartridge | 1 E + 1 W+F | C-3 | Propulsion & Flight Systems |
| T2-023 | Attitude Thruster Pack | 1 W + 1 E + 1 W+F | C-4 | Propulsion & Flight Systems |
| T2-024 | Ion Acceleration Grid | 1 E + 1 F + 1 W+F | C-4 | Propulsion & Flight Systems |
| T2-025 | Plasma Feed Injector | 1 E + 1 A + 1 W+F | C-4 | Propulsion & Flight Systems |
| T2-026 | Propellant Control Valve | 1 W+E + 1 W+F | C-4 | Propulsion & Flight Systems |
| T2-027 | Flight Reference Gyro | 1 W+F + 1 W+A | C-4 | Propulsion & Flight Systems |
| T2-028 | Inertial Guidance Module | 1 W+F + 1 E+F | C-4 | Propulsion & Flight Systems |
| T2-029 | Ion Cruise Engine | 1 W + 1 E + 1 A + 1 W+F | C-5 | Propulsion & Flight Systems |
| T2-030 | Plasma Transfer Engine | 1 E + 1 F + 1 A + 1 W+F | C-5 | Propulsion & Flight Systems |
| T2-031 | Fusion Main Engine | 1 W + 1 W+E + 1 W+F | C-5 | Propulsion & Flight Systems |
| T2-032 | Pulse Propulsion Chamber | 1 E + 1 W+F + 1 W+A | C-5 | Propulsion & Flight Systems |
| T2-033 | Light Sail Assembly | 1 F + 1 W+F + 1 E+F | C-5 | Propulsion & Flight Systems |
| T2-034 | Magnetic Sail Assembly | 1 A + 1 W+F + 1 E+A | C-5 | Propulsion & Flight Systems |
| T2-035 | Gravity Assist Computer | 1 W + 1 W+F + 1 F+A | C-5 | Propulsion & Flight Systems |
| T2-036 | Deep Space Flight Controller | 1 E + 1 W+E + 1 W+F | C-5 | Propulsion & Flight Systems |
| T2-037 | Orbital Maneuvering Engine | 1 F + 1 W+F + 1 W+A | C-5 | Propulsion & Flight Systems |
| T2-038 | Descent Engine Package | 1 A + 1 W+F + 1 E+F | C-5 | Propulsion & Flight Systems |
| T2-039 | Launch Assist Booster | 1 W + 1 W+F + 1 E+A | C-5 | Propulsion & Flight Systems |
| T2-040 | Heavy Tow Engine | 1 E + 1 W+F + 1 F+A | C-5 | Propulsion & Flight Systems |
| T2-041 | Hull Skin Panel | 1 F + 1 W+E | C-3 | Shipbuilding & Orbital Structures |
| T2-042 | Primary Frame Beam | 1 A + 1 W+E | C-3 | Shipbuilding & Orbital Structures |
| T2-043 | Pressure Bulkhead | 1 W + 1 E + 1 W+E | C-4 | Shipbuilding & Orbital Structures |
| T2-044 | Crew Access Hatch | 1 F + 1 A + 1 W+E | C-4 | Shipbuilding & Orbital Structures |
| T2-045 | Docking Adapter Ring | 1 W + 1 E + 1 W+E | C-4 | Shipbuilding & Orbital Structures |
| T2-046 | Viewport Armor Cover | 1 W+E + 1 W+F | C-4 | Shipbuilding & Orbital Structures |
| T2-047 | Landing Gear Assembly | 1 W+E + 1 E+A | C-4 | Shipbuilding & Orbital Structures |
| T2-048 | Cargo Ramp Assembly | 1 W+E + 1 F+A | C-4 | Shipbuilding & Orbital Structures |
| T2-049 | Orbital Construction Frame | 1 W + 1 E + 1 F + 1 W+E | C-5 | Shipbuilding & Orbital Structures |
| T2-050 | Scout Vessel Frame | 1 W + 1 E + 1 A + 1 W+E | C-5 | Shipbuilding & Orbital Structures |
| T2-051 | Heavy Freight Hull | 1 F + 1 W+E + 1 W+F | C-5 | Shipbuilding & Orbital Structures |
| T2-052 | Survey Vessel Chassis | 1 A + 1 W+E + 1 W+F | C-5 | Shipbuilding & Orbital Structures |
| T2-053 | Mining Tender Hull | 1 W + 1 W+E + 1 W+F | C-5 | Shipbuilding & Orbital Structures |
| T2-054 | Dock Tug Chassis | 1 E + 1 W+E + 1 W+A | C-5 | Shipbuilding & Orbital Structures |
| T2-055 | Escort Ship Hull | 1 F + 1 W+E + 1 E+F | C-5 | Shipbuilding & Orbital Structures |
| T2-056 | Launch Stage Body | 1 A + 1 W+E + 1 E+A | C-5 | Shipbuilding & Orbital Structures |
| T2-057 | Crew Capsule Shell | 1 W + 1 W+E + 1 F+A | C-5 | Shipbuilding & Orbital Structures |
| T2-058 | Station Center Truss | 1 E + 1 W+E + 1 W+F | C-5 | Shipbuilding & Orbital Structures |
| T2-059 | Multiport Dock Frame | 1 F + 1 W+E + 1 W+A | C-5 | Shipbuilding & Orbital Structures |
| T2-060 | Shipyard Support Frame | 1 A + 1 W+E + 1 E+F | C-5 | Shipbuilding & Orbital Structures |
| T2-061 | Interior Wall Panel | 1 W + 1 F + 1 A | C-3 | Housing & Life Support |
| T2-062 | Foundation Anchor Kit | 1 W + 1 W+F | C-3 | Housing & Life Support |
| T2-063 | Pressure Wall Section | 1 W + 1 E + 1 F + 1 A | C-4 | Housing & Life Support |
| T2-064 | Personnel Airlock Gate | 1 W + 1 F + 1 W+A | C-4 | Housing & Life Support |
| T2-065 | Utility Floor Panel | 1 W + 1 F + 1 E+F | C-4 | Housing & Life Support |
| T2-066 | Freshwater Pipe Section | 1 W + 1 E + 1 E+A | C-4 | Housing & Life Support |
| T2-067 | Radiation Barrier Sheet | 1 W + 1 F + 1 F+A | C-4 | Housing & Life Support |
| T2-068 | Daylight Ceiling Panel | 1 W + 1 A + 1 W+E | C-4 | Housing & Life Support |
| T2-069 | Residential Pressure Module | 1 W + 1 E + 1 F + 1 W+E | C-5 | Housing & Life Support |
| T2-070 | Orbital Housing Shell | 1 W + 1 F + 1 A + 1 W+F | C-5 | Housing & Life Support |
| T2-071 | Frontier Community Center | 1 W + 1 E + 1 F + 1 W+A | C-5 | Housing & Life Support |
| T2-072 | Rotating Habitat Bearing Hub | 1 W + 1 F + 1 A + 1 E+F | C-5 | Housing & Life Support |
| T2-073 | Asteroid Foundation Kit | 1 W + 1 E + 1 F + 1 E+A | C-5 | Housing & Life Support |
| T2-074 | Remote Shelter Module | 1 W + 1 F + 1 A + 1 F+A | C-5 | Housing & Life Support |
| T2-075 | Mixed-Crew Housing Unit | 1 W + 1 W+E + 1 W+F | C-5 | Housing & Life Support |
| T2-076 | Grow Room Enclosure | 1 W + 1 W+A + 1 E+F | C-5 | Housing & Life Support |
| T2-077 | Medical Isolation Suite | 1 W + 1 E+A + 1 F+A | C-5 | Housing & Life Support |
| T2-078 | Garden Dome Shell | 1 W + 1 W+E + 1 W+F | C-5 | Housing & Life Support |
| T2-079 | Underground Habitat Liner | 1 W + 1 W+A + 1 E+F | C-5 | Housing & Life Support |
| T2-080 | Orbital Tether Foundation | 1 W + 1 E+A + 1 F+A | C-5 | Housing & Life Support |
| T2-081 | Servo Joint Module | 1 W + 1 E+A | C-3 | Robotics & Field Services |
| T2-082 | Actuator Link | 1 E + 1 E+A | C-3 | Robotics & Field Services |
| T2-083 | Utility Gripper | 1 F + 1 A + 1 E+A | C-4 | Robotics & Field Services |
| T2-084 | Quick-Change Wrist Coupler | 1 W + 1 E + 1 E+A | C-4 | Robotics & Field Services |
| T2-085 | All-Terrain Drive Wheel | 1 F + 1 A + 1 E+A | C-4 | Robotics & Field Services |
| T2-086 | Service Arm Assembly | 1 W+E + 1 E+A | C-4 | Robotics & Field Services |
| T2-087 | Grip Pressure Sensor | 1 W+F + 1 E+A | C-4 | Robotics & Field Services |
| T2-088 | Fluid Actuator Pack | 1 W+A + 1 E+A | C-4 | Robotics & Field Services |
| T2-089 | Facility Service Robot | 1 E + 1 F + 1 A + 1 E+A | C-5 | Robotics & Field Services |
| T2-090 | Hull Cleaning Robot | 1 W + 1 E + 1 F + 1 E+A | C-5 | Robotics & Field Services |
| T2-091 | Equipment Inspection Rover | 1 W + 1 W+E + 1 E+A | C-5 | Robotics & Field Services |
| T2-092 | Mine Safety Scout | 1 E + 1 W+E + 1 E+A | C-5 | Robotics & Field Services |
| T2-093 | Hull Patch Robot | 1 F + 1 E+A + 1 F+A | C-5 | Robotics & Field Services |
| T2-094 | Cargo Handling Rover | 1 A + 1 W+E + 1 E+A | C-5 | Robotics & Field Services |
| T2-095 | Medical Handling Robot | 1 W + 1 W+F + 1 E+A | C-5 | Robotics & Field Services |
| T2-096 | Vacuum Service Robot | 1 E + 1 W+A + 1 E+A | C-5 | Robotics & Field Services |
| T2-097 | Site Survey Rover | 1 F + 1 E+F + 1 E+A | C-5 | Robotics & Field Services |
| T2-098 | Utility Inspection Crawler | 1 A + 1 E+A + 1 F+A | C-5 | Robotics & Field Services |
| T2-099 | Building Maintenance Robot | 1 W + 1 W+E + 1 E+A | C-5 | Robotics & Field Services |
| T2-100 | Salvage Handling Robot | 1 E + 1 W+F + 1 E+A | C-5 | Robotics & Field Services |
| T2-101 | Circuit Interconnect Strip | 1 F + 1 E+F | C-3 | Computing & Communications |
| T2-102 | Solid-State Memory Tile | 1 A + 1 E+F | C-3 | Computing & Communications |
| T2-103 | Equipment Control Board | 1 W + 1 E + 1 E+F | C-4 | Computing & Communications |
| T2-104 | Learning Memory Module | 1 F + 1 A + 1 E+F | C-4 | Computing & Communications |
| T2-105 | Local Network Radio | 1 E+F + 1 E+A | C-4 | Computing & Communications |
| T2-106 | Signal Booster Card | 1 E+F + 1 F+A | C-4 | Computing & Communications |
| T2-107 | Industrial Network Switch | 1 W+E + 1 E+F | C-4 | Computing & Communications |
| T2-108 | Packet Buffer Module | 1 W+F + 1 E+F | C-4 | Computing & Communications |
| T2-109 | General Computing Rack | 1 W + 1 E + 1 A + 1 E+F | C-5 | Computing & Communications |
| T2-110 | Flight Computing Rack | 1 E + 1 F + 1 A + 1 E+F | C-5 | Computing & Communications |
| T2-111 | Autonomous Scheduling Server | 1 F + 1 E+F + 1 E+A | C-5 | Computing & Communications |
| T2-112 | Radiation-Tolerant Computer | 1 A + 1 E+F + 1 E+A | C-5 | Computing & Communications |
| T2-113 | Quantum Compute Cartridge | 1 W + 1 W+A + 1 E+F | C-5 | Computing & Communications |
| T2-114 | Colony Edge Server | 1 E + 1 E+F + 1 E+A | C-5 | Computing & Communications |
| T2-115 | Fleet Operations Server | 1 F + 1 E+F + 1 F+A | C-5 | Computing & Communications |
| T2-116 | Orbital Relay Station | 1 A + 1 W+E + 1 E+F | C-5 | Computing & Communications |
| T2-117 | Laser Data Terminal | 1 W + 1 W+F + 1 E+F | C-5 | Computing & Communications |
| T2-118 | Deep Space Radio Station | 1 E + 1 W+A + 1 E+F | C-5 | Computing & Communications |
| T2-119 | Interplanetary Network Gateway | 1 F + 1 E+F + 1 E+A | C-5 | Computing & Communications |
| T2-120 | Long-Term Archive Server | 1 A + 1 E+F + 1 F+A | C-5 | Computing & Communications |
| T2-121 | Optical Sensor Element | 1 A + 1 W+A | C-3 | Sensors & Medical Equipment |
| T2-122 | Radiation Detector Sheet | 1 A + 1 E+F | C-3 | Sensors & Medical Equipment |
| T2-123 | Material Analysis Head | 1 W + 1 E + 1 F + 1 A | C-4 | Sensors & Medical Equipment |
| T2-124 | Tracking Radar Dish | 1 W + 1 A + 1 W+F | C-4 | Sensors & Medical Equipment |
| T2-125 | Laser Mapping Head | 1 W + 1 A + 1 W+A | C-4 | Sensors & Medical Equipment |
| T2-126 | Thermal Inspection Camera | 1 E + 1 A + 1 E+F | C-4 | Sensors & Medical Equipment |
| T2-127 | Magnetic Survey Sensor | 1 F + 1 A + 1 E+A | C-4 | Sensors & Medical Equipment |
| T2-128 | Seismic Monitoring Unit | 1 W + 1 A + 1 F+A | C-4 | Sensors & Medical Equipment |
| T2-129 | Deep Space Telescope | 1 W + 1 F + 1 A + 1 W+E | C-5 | Sensors & Medical Equipment |
| T2-130 | Planetary Mapping Satellite | 1 W + 1 E + 1 A + 1 W+F | C-5 | Sensors & Medical Equipment |
| T2-131 | Asteroid Survey Drone | 1 W + 1 F + 1 A + 1 W+A | C-5 | Sensors & Medical Equipment |
| T2-132 | Long-Range Recon Probe | 1 W + 1 E + 1 A + 1 E+F | C-5 | Sensors & Medical Equipment |
| T2-133 | Sample Collection Rover | 1 W + 1 F + 1 A + 1 E+A | C-5 | Sensors & Medical Equipment |
| T2-134 | Subsurface Survey Kit | 1 W + 1 E + 1 A + 1 F+A | C-5 | Sensors & Medical Equipment |
| T2-135 | Orbital Mapping Imager | 1 A + 1 W+E + 1 W+F | C-5 | Sensors & Medical Equipment |
| T2-136 | Particle Monitoring Station | 1 A + 1 W+A + 1 E+F | C-5 | Sensors & Medical Equipment |
| T2-137 | Solar Activity Monitor | 1 A + 1 E+A + 1 F+A | C-5 | Sensors & Medical Equipment |
| T2-138 | Radio Observation Array | 1 A + 1 W+E + 1 W+F | C-5 | Sensors & Medical Equipment |
| T2-139 | Medical Imaging Bed | 1 A + 1 W+A + 1 E+F | C-5 | Sensors & Medical Equipment |
| T2-140 | Planet Detection Instrument | 1 A + 1 E+A + 1 F+A | C-5 | Sensors & Medical Equipment |
| T2-141 | Replaceable Cutting Tooth | 1 E + 1 E+A | C-3 | Industrial Tooling & Mining Supplies |
| T2-142 | Precision Abrasive Pack | 1 E + 1 F+A | C-3 | Industrial Tooling & Mining Supplies |
| T2-143 | Rock Drill Crown | 1 E + 1 A + 1 W+E | C-4 | Industrial Tooling & Mining Supplies |
| T2-144 | Crusher Jaw Insert | 1 E + 1 F + 1 W+F | C-4 | Industrial Tooling & Mining Supplies |
| T2-145 | Surface Finishing Disc | 1 E + 1 A + 1 W+A | C-4 | Industrial Tooling & Mining Supplies |
| T2-146 | Crucible Liner | 1 W + 1 E + 1 E+F | C-4 | Industrial Tooling & Mining Supplies |
| T2-147 | Casting Die Set | 1 E + 1 F + 1 E+A | C-4 | Industrial Tooling & Mining Supplies |
| T2-148 | Welding Contact Kit | 1 E + 1 A + 1 F+A | C-4 | Industrial Tooling & Mining Supplies |
| T2-149 | Furnace Refractory Kit | 1 E + 1 F + 1 A + 1 W+E | C-5 | Industrial Tooling & Mining Supplies |
| T2-150 | Drill Alignment Frame | 1 W + 1 E + 1 A + 1 W+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-151 | Excavator Bucket Assembly | 1 E + 1 F + 1 A + 1 W+A | C-5 | Industrial Tooling & Mining Supplies |
| T2-152 | Crusher Rebuild Kit | 1 W + 1 E + 1 A + 1 E+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-153 | Separator Drum Liner | 1 E + 1 F + 1 A + 1 E+A | C-5 | Industrial Tooling & Mining Supplies |
| T2-154 | Refining Tank Liner | 1 W + 1 E + 1 F + 1 F+A | C-5 | Industrial Tooling & Mining Supplies |
| T2-155 | Smelter Wear Kit | 1 E + 1 W+E + 1 W+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-156 | Casting Fixture Rack | 1 E + 1 W+A + 1 E+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-157 | Precision Workholding Table | 1 E + 1 E+A + 1 F+A | C-5 | Industrial Tooling & Mining Supplies |
| T2-158 | Additive Build Plate | 1 E + 1 W+E + 1 W+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-159 | Extrusion Tooling Set | 1 E + 1 W+A + 1 E+F | C-5 | Industrial Tooling & Mining Supplies |
| T2-160 | Crystal Growth Fixture | 1 E + 1 E+A + 1 F+A | C-5 | Industrial Tooling & Mining Supplies |
| T2-161 | Cargo Tie-Down | 1 W + 1 W+A | C-3 | Freight & Warehouse Equipment |
| T2-162 | Tamper-Evident Cargo Seal | 1 E + 1 W+A | C-3 | Freight & Warehouse Equipment |
| T2-163 | Food-Grade Shipping Drum | 1 W + 1 E + 1 W+A | C-4 | Freight & Warehouse Equipment |
| T2-164 | Warehouse Storage Rack | 1 F + 1 A + 1 W+A | C-4 | Freight & Warehouse Equipment |
| T2-165 | Cargo Transfer Adapter | 1 W+A + 1 E+F | C-4 | Freight & Warehouse Equipment |
| T2-166 | Gravity Conveyor Section | 1 W+A + 1 E+F | C-4 | Freight & Warehouse Equipment |
| T2-167 | Container Lock Assembly | 1 W+A + 1 E+A | C-4 | Freight & Warehouse Equipment |
| T2-168 | Heavy-Duty Shipping Pallet | 1 W+A + 1 F+A | C-4 | Freight & Warehouse Equipment |
| T2-169 | Orbital Shipping Container | 1 W + 1 E + 1 F + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-170 | Medical Cold-Chain Container | 1 W + 1 E + 1 A + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-171 | Pressurized Cargo Box | 1 W + 1 W+A + 1 E+F | C-5 | Freight & Warehouse Equipment |
| T2-172 | Hazardous Materials Container | 1 E + 1 W+A + 1 E+F | C-5 | Freight & Warehouse Equipment |
| T2-173 | Self-Driving Cargo Cart | 1 F + 1 W+E + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-174 | Bulk Food Storage Bin | 1 A + 1 W+F + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-175 | Cargo Transfer Airlock | 1 W + 1 W+A + 1 E+F | C-5 | Freight & Warehouse Equipment |
| T2-176 | Orbital Container Rack | 1 E + 1 W+A + 1 E+A | C-5 | Freight & Warehouse Equipment |
| T2-177 | Ship Loading Platform | 1 F + 1 W+A + 1 F+A | C-5 | Freight & Warehouse Equipment |
| T2-178 | Spaceport Cargo Crane | 1 A + 1 W+E + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-179 | Propellant Transfer Station | 1 W + 1 W+F + 1 W+A | C-5 | Freight & Warehouse Equipment |
| T2-180 | Medical Gas Storage Tank | 1 E + 1 W+A + 1 E+F | C-5 | Freight & Warehouse Equipment |
| T2-181 | Shielding Fabric | 1 F + 1 F+A | C-3 | Defense & Emergency Systems |
| T2-182 | Impact Absorber Block | 1 A + 1 F+A | C-3 | Defense & Emergency Systems |
| T2-183 | Fragment Armor Panel | 1 W + 1 E + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-184 | Radiation Guard Panel | 1 F + 1 A + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-185 | Emergency Pressure Curtain | 1 W+A + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-186 | Fire Containment Door | 1 W+E + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-187 | Search-and-Rescue Beacon | 1 W+F + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-188 | Electrical Surge Arrestor | 1 W+A + 1 F+A | C-4 | Defense & Emergency Systems |
| T2-189 | Emergency Isolation Valve | 1 W + 1 F + 1 A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-190 | Rescue Cable Winch | 1 E + 1 F + 1 A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-191 | Electromagnetic Defense Array | 1 F + 1 W+A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-192 | Radiation Shelter Module | 1 A + 1 W+A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-193 | Emergency Hull Seal Kit | 1 W + 1 E+A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-194 | Automatic Fire Suppression Pack | 1 E + 1 W+E + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-195 | Point Defense Drone | 1 F + 1 W+F + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-196 | Collision Warning System | 1 A + 1 W+A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-197 | Crew Evacuation Pod | 1 W + 1 E+F + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-198 | Autonomous Rescue Shuttle | 1 E + 1 E+A + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-199 | Perimeter Warning Network | 1 F + 1 W+E + 1 F+A | C-5 | Defense & Emergency Systems |
| T2-200 | Solar Radiation Protection System | 1 A + 1 W+F + 1 F+A | C-5 | Defense & Emergency Systems |
