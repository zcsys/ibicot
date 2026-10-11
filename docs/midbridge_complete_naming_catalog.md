# Midbridge Colony complete naming catalog

**Midbridge Colony · 4259 — naming catalog, 11 October 2026.** This is the complete reference for the approved resource, product, company, sector, and equipment names. T1 and T2 companies use activity-based stems. The names have not yet been implemented.

The catalog contains four raw resources, twenty T0 companies, fourteen refined materials, fourteen paired sectors, and 255 manufactured products. Every one of the 269 recipes has a named installation. The four existing general equipment-class names are retained because they already fit this vocabulary.

## Fixed identity and display names

| Entity | Name or display form |
|---|---|
| Game | Midbridge Colony |
| Year | 4259 |
| Gaia | Gaia 0x0 |
| T0 tier | Extractors |
| T1 tier | Refineries |
| T2 tier | Manufacturers |
| T3 tier | Distributors |
| T0 company | `<name> <global hex company number>` |
| Every T1 company | `<generic stem> <global hex company number>` |
| Every T2 company | `<facility stem> <global hex company number>` |
| T3 company | `Distributor <global hex company number>` |

Company numbers remain globally unique, lowercase hexadecimal identifiers. T1 and T2 each use one activity-based company stem per sector, including the first company. Neither tier has flagship names. Product IDs, sector IDs, equipment IDs, and machine-family IDs retain their existing identities.

## Raw resources

W, E, F, and A are stable slot codes for the new resource names. Raw resources remain distinct from their C1 refined outputs.

| Resource ID | Slot | Fixed name | Resource definition |
|---|---|---|---|
| RAW-W | W | Organics | carbon-based matter: biomass and everything life is built from |
| RAW-E | E | Inorganics | non-metallic, non-carbon matter: silicates, salts, water, gases, free hydrogen |
| RAW-F | F | Metals | stable metals, extracted as metals |
| RAW-A | A | Radioactives | anything defined by unstable nuclei, including radioactive metals |

## T0 companies

The twenty company names and their existing resource coverage are listed below. For example, `Associated Silica, Incorporated 0x10` uses the existing global number.

| Company number | Company ID | Name | Extracts |
|---|---|---|---|
| 0x1 | T0-01 | Raw Materials Corp. | Organics + Inorganics + Metals + Radioactives |
| 0x2 | T0-02 | Elements Inc. | Organics + Inorganics + Metals + Radioactives |
| 0x3 | T0-03 | General Resources Corporation | Organics + Inorganics + Metals |
| 0x4 | T0-04 | Integrated Extraction Corp., Inc. | Organics + Inorganics + Radioactives |
| 0x5 | T0-05 | Planetary Industries, Inc. | Organics + Metals + Radioactives |
| 0x6 | T0-06 | Federated Supply Incorporated | Inorganics + Metals + Radioactives |
| 0x7 | T0-07 | Standard Fiber & Mineral, Inc. | Organics + Inorganics |
| 0x8 | T0-08 | Advanced Materials, Inc. | Organics + Metals |
| 0x9 | T0-09 | The People's Extraction Co., Inc. | Organics + Radioactives |
| 0xa | T0-10 | Premier Harvest, Inc. | Inorganics + Metals |
| 0xb | T0-11 | Universal Material Extraction Corp. | Inorganics + Radioactives |
| 0xc | T0-12 | The Oligarch | Metals + Radioactives |
| 0xd | T0-13 | Meta Organics, Inc. | Organics |
| 0xe | T0-14 | Old Toby & Daughters, Inc. | Organics |
| 0xf | T0-15 | Planetary Salt Corporation | Inorganics |
| 0x10 | T0-16 | Associated Silica, Incorporated | Inorganics |
| 0x11 | T0-17 | The Metal Mining Co., Inc. | Metals |
| 0x12 | T0-18 | The Union Metal, Inc. | Metals |
| 0x13 | T0-19 | Amalgamated Isotopes Corp. | Radioactives |
| 0x14 | T0-20 | United Radioactives Company | Radioactives |

The existing machinery supplier remains the company at `0x7`, named **Standard Fiber & Mineral, Inc.** in this catalog. This changes its display name only; its machinery role and all other company duties remain attached to their existing identities.

## T1 materials and refinery sectors

Each refined material has one refinery sector and one company stem. Material symbols retain their fixed slot notation.

| T1 sector | Refinery-sector name | Material ID | Symbol | Fixed material name |
|---|---|---|---|---|
| S1-01 | Biochemical Refining | C1-001 | W | Biochemical Feedstock |
| S1-02 | Inorganic Refining | C1-002 | E | Inorganic Concentrate |
| S1-03 | Metal Smelting | C1-003 | F | Metal Ingots |
| S1-04 | Isotope Refining | C1-004 | A | Isotope Feed |
| S1-05 | Polymer Processing | C2-001 | WW | Engineered Polymers |
| S1-06 | Fine Chemical Refining | C2-002 | WE | Fine Chemicals |
| S1-07 | Catalyst Production | C2-003 | WF | Catalysts |
| S1-08 | Radiopharmaceutical Processing | C2-004 | WA | Radiopharmaceuticals |
| S1-09 | Ceramic Processing | C2-005 | EE | Technical Ceramics |
| S1-10 | Semiconductor Fabrication | C2-006 | EF | Semiconductor Wafers |
| S1-11 | Shielding Material Production | C2-007 | EA | Radiation Shielding |
| S1-12 | Alloy Refining | C2-008 | FF | Structural Alloys |
| S1-13 | Reactor Fuel Processing | C2-009 | FA | Reactor Fuel |
| S1-14 | Isotope Cell Production | C2-010 | AA | Isotope Power Cells |

## T1 company names

Every T1 company uses its sector's activity-based stem followed by its global hex company number, including the first company in each material cohort. The fourteen company stems are listed below.

| T1 sector | Material ID | Company stem |
|---|---|---|
| S1-01 | C1-001 | Biochemical Plant |
| S1-02 | C1-002 | Concentrate Works |
| S1-03 | C1-003 | Metal Smelter |
| S1-04 | C1-004 | Isotope Plant |
| S1-05 | C2-001 | Polymer Works |
| S1-06 | C2-002 | Fine Chemical Plant |
| S1-07 | C2-003 | Catalyst Works |
| S1-08 | C2-004 | Radiochemical Lab |
| S1-09 | C2-005 | Ceramic Kiln |
| S1-10 | C2-006 | Wafer Fab |
| S1-11 | C2-007 | Shielding Plant |
| S1-12 | C2-008 | Alloy Foundry |
| S1-13 | C2-009 | Fuel Fabrication Plant |
| S1-14 | C2-010 | Power Cell Plant |

## T2 application sectors

Each named sector keeps its existing preferred material and paired refinery sector. These labels do not change recipe membership.

| T2 sector | Application-sector name | Paired T1 sector | Preferred material |
|---|---|---|---|
| S2-01 | Biochemical Products | S1-01 | Biochemical Feedstock (C1-001) |
| S2-02 | Inorganic Products | S1-02 | Inorganic Concentrate (C1-002) |
| S2-03 | Metal Products | S1-03 | Metal Ingots (C1-003) |
| S2-04 | Isotope Products | S1-04 | Isotope Feed (C1-004) |
| S2-05 | Polymer Goods | S1-05 | Engineered Polymers (C2-001) |
| S2-06 | Specialty Chemicals | S1-06 | Fine Chemicals (C2-002) |
| S2-07 | Catalytic Products | S1-07 | Catalysts (C2-003) |
| S2-08 | Medical Isotope Products | S1-08 | Radiopharmaceuticals (C2-004) |
| S2-09 | Ceramic Goods | S1-09 | Technical Ceramics (C2-005) |
| S2-10 | Electronic Components | S1-10 | Semiconductor Wafers (C2-006) |
| S2-11 | Radiation Protection | S1-11 | Radiation Shielding (C2-007) |
| S2-12 | Alloy Components | S1-12 | Structural Alloys (C2-008) |
| S2-13 | Reactor Fuel Products | S1-13 | Reactor Fuel (C2-009) |
| S2-14 | Isotope Power Systems | S1-14 | Isotope Power Cells (C2-010) |

## T2 company stems

Every stem ends with the literal lowercase word `facility`. The existing global company number follows the stem when displayed.

| sector_id | facility_stem |
|---|---|
| S2-01 | Biochemical processing facility |
| S2-02 | Inorganic processing facility |
| S2-03 | Metal fabrication facility |
| S2-04 | Isotope processing facility |
| S2-05 | Polymer fabrication facility |
| S2-06 | Specialty chemical processing facility |
| S2-07 | Catalyst fabrication facility |
| S2-08 | Medical isotope processing facility |
| S2-09 | Ceramic fabrication facility |
| S2-10 | Electronic component fabrication facility |
| S2-11 | Radiation shielding fabrication facility |
| S2-12 | Alloy fabrication facility |
| S2-13 | Reactor fuel fabrication facility |
| S2-14 | Isotope power assembly facility |

## Recipe quantities and availability

Each recipe produces one item of its named output. Each input column means one item; repeating the same input means two items. C1 consumes one raw item. C2 consumes two raw items directly from T0. C3 uses C1 and C2; C4 uses either C1 and C3 or two C2 items.

Immediate ingredient IDs define each recipe. Different routes stay distinct even when raw ancestry matches. Product complexity equals the sum of raw ancestry units. Raw items occupy one storage space, and C1 through C4 outputs occupy one through four spaces. Names add no performance statistics or chemical process requirements.

Starting selection is retained: 105 T2 recipes are invented and 150 are uninvented. All fourteen T1 recipes are available at the start. Naming a product or its installation does not unlock it. Original symbolic formulas, ingredient quantities, and output quantities are included for every recipe in the JSON companion.

## T1 refined materials

The fourteen material names and display symbols are listed with their recipes below. Company stems and named refinery sectors appear above.

### C1 basic materials

| Recipe ID | Fixed product name | Display symbol | Input 1 | Input 2 | Sector |
|---|---|---|---|---|---|
| C1-001 | Biochemical Feedstock | W | Organics (RAW-W) | — | S1-01 |
| C1-002 | Inorganic Concentrate | E | Inorganics (RAW-E) | — | S1-02 |
| C1-003 | Metal Ingots | F | Metals (RAW-F) | — | S1-03 |
| C1-004 | Isotope Feed | A | Radioactives (RAW-A) | — | S1-04 |

### C2 compound materials

| Recipe ID | Fixed product name | Display symbol | Input 1 | Input 2 | Sector |
|---|---|---|---|---|---|
| C2-001 | Engineered Polymers | WW | Organics (RAW-W) | Organics (RAW-W) | S1-05 |
| C2-002 | Fine Chemicals | WE | Organics (RAW-W) | Inorganics (RAW-E) | S1-06 |
| C2-003 | Catalysts | WF | Organics (RAW-W) | Metals (RAW-F) | S1-07 |
| C2-004 | Radiopharmaceuticals | WA | Organics (RAW-W) | Radioactives (RAW-A) | S1-08 |
| C2-005 | Technical Ceramics | EE | Inorganics (RAW-E) | Inorganics (RAW-E) | S1-09 |
| C2-006 | Semiconductor Wafers | EF | Inorganics (RAW-E) | Metals (RAW-F) | S1-10 |
| C2-007 | Radiation Shielding | EA | Inorganics (RAW-E) | Radioactives (RAW-A) | S1-11 |
| C2-008 | Structural Alloys | FF | Metals (RAW-F) | Metals (RAW-F) | S1-12 |
| C2-009 | Reactor Fuel | FA | Metals (RAW-F) | Radioactives (RAW-A) | S1-13 |
| C2-010 | Isotope Power Cells | AA | Radioactives (RAW-A) | Radioactives (RAW-A) | S1-14 |

## T2 C3 manufactured products

Each recipe combines one C1 material with one C2 material. There are 40 products: 36 starting and four uninvented.

### C3 products using Biochemical Feedstock

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C3-001 | Biopolymer Resin | Biochemical Feedstock (C1-001) | Engineered Polymers (C2-001) | S2-05 | Starting |
| C3-002 | Culture Nutrients | Biochemical Feedstock (C1-001) | Fine Chemicals (C2-002) | S2-06 | Starting |
| C3-003 | Enzyme Catalysts | Biochemical Feedstock (C1-001) | Catalysts (C2-003) | S2-07 | Starting |
| C3-004 | Diagnostic Tracers | Biochemical Feedstock (C1-001) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C3-005 | Porous Ceramic Filters | Biochemical Feedstock (C1-001) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C3-006 | Biosensor Chips | Biochemical Feedstock (C1-001) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C3-007 | Organic Shielding Blocks | Biochemical Feedstock (C1-001) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C3-008 | Composite Beams | Biochemical Feedstock (C1-001) | Structural Alloys (C2-008) | S2-12 | Starting |
| C3-009 | Carbon Fuel Pellets | Biochemical Feedstock (C1-001) | Reactor Fuel (C2-009) | S2-13 | Uninvented |
| C3-010 | Encapsulated Power Cells | Biochemical Feedstock (C1-001) | Isotope Power Cells (C2-010) | S2-14 | Starting |

### C3 products using Inorganic Concentrate

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C3-011 | Mineral Insulation Foam | Inorganic Concentrate (C1-002) | Engineered Polymers (C2-001) | S2-05 | Starting |
| C3-012 | Process Electrolytes | Inorganic Concentrate (C1-002) | Fine Chemicals (C2-002) | S2-06 | Starting |
| C3-013 | Supported Catalysts | Inorganic Concentrate (C1-002) | Catalysts (C2-003) | S2-07 | Starting |
| C3-014 | Mineral Tracer Beads | Inorganic Concentrate (C1-002) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C3-015 | Ceramic Insulators | Inorganic Concentrate (C1-002) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C3-016 | Doped Semiconductor Dies | Inorganic Concentrate (C1-002) | Semiconductor Wafers (C2-006) | S2-10 | Uninvented |
| C3-017 | Shielding Tiles | Inorganic Concentrate (C1-002) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C3-018 | Corrosion Resistant Plates | Inorganic Concentrate (C1-002) | Structural Alloys (C2-008) | S2-12 | Starting |
| C3-019 | Ceramic Fuel Pellets | Inorganic Concentrate (C1-002) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C3-020 | Ceramic Power Capsules | Inorganic Concentrate (C1-002) | Isotope Power Cells (C2-010) | S2-14 | Starting |

### C3 products using Metal Ingots

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C3-021 | Reinforced Polymer Panels | Metal Ingots (C1-003) | Engineered Polymers (C2-001) | S2-05 | Starting |
| C3-022 | Electroplating Salts | Metal Ingots (C1-003) | Fine Chemicals (C2-002) | S2-06 | Uninvented |
| C3-023 | Catalytic Mesh | Metal Ingots (C1-003) | Catalysts (C2-003) | S2-07 | Starting |
| C3-024 | Tracer Capsules | Metal Ingots (C1-003) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C3-025 | Ceramic Bearing Inserts | Metal Ingots (C1-003) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C3-026 | Power Transistors | Metal Ingots (C1-003) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C3-027 | Shielded Containers | Metal Ingots (C1-003) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C3-028 | Precision Gears | Metal Ingots (C1-003) | Structural Alloys (C2-008) | S2-12 | Starting |
| C3-029 | Fuel Rods | Metal Ingots (C1-003) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C3-030 | Nuclear Battery Packs | Metal Ingots (C1-003) | Isotope Power Cells (C2-010) | S2-14 | Starting |

### C3 products using Isotope Feed

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C3-031 | Radioactive Polymer Standards | Isotope Feed (C1-004) | Engineered Polymers (C2-001) | S2-05 | Starting |
| C3-032 | Isotope Reagents | Isotope Feed (C1-004) | Fine Chemicals (C2-002) | S2-06 | Starting |
| C3-033 | Radiolabeled Catalysts | Isotope Feed (C1-004) | Catalysts (C2-003) | S2-07 | Starting |
| C3-034 | Therapeutic Isotope Doses | Isotope Feed (C1-004) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C3-035 | Ceramic Radiation Sources | Isotope Feed (C1-004) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C3-036 | Radiation Detector Dies | Isotope Feed (C1-004) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C3-037 | Shielded Source Capsules | Isotope Feed (C1-004) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C3-038 | Alloy Source Pellets | Isotope Feed (C1-004) | Structural Alloys (C2-008) | S2-12 | Starting |
| C3-039 | Enriched Fuel Pellets | Isotope Feed (C1-004) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C3-040 | High Output Isotope Cells | Isotope Feed (C1-004) | Isotope Power Cells (C2-010) | S2-14 | Uninvented |

## T2 C4 products made from C1 and C3

Each recipe adds one C1 material to one specific C3 product. All 160 routes retain their distinct intermediate dependency: 14 are starting recipes and 146 are uninvented.

### C4 products adding Biochemical Feedstock

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-001 | Bioplastic Sheets | Biochemical Feedstock (C1-001) | Biopolymer Resin (C3-001) | S2-01 | Starting |
| C4-002 | Fermentation Feed | Biochemical Feedstock (C1-001) | Culture Nutrients (C3-002) | S2-01 | Uninvented |
| C4-003 | Immobilized Enzyme Beads | Biochemical Feedstock (C1-001) | Enzyme Catalysts (C3-003) | S2-01 | Uninvented |
| C4-004 | Assay Tracer Kits | Biochemical Feedstock (C1-001) | Diagnostic Tracers (C3-004) | S2-01 | Uninvented |
| C4-005 | Bioactive Filter Cartridges | Biochemical Feedstock (C1-001) | Porous Ceramic Filters (C3-005) | S2-01 | Uninvented |
| C4-006 | Bioassay Sensors | Biochemical Feedstock (C1-001) | Biosensor Chips (C3-006) | S2-01 | Uninvented |
| C4-007 | Fiber Shielding Boards | Biochemical Feedstock (C1-001) | Organic Shielding Blocks (C3-007) | S2-01 | Uninvented |
| C4-008 | Carbon Composite Trusses | Biochemical Feedstock (C1-001) | Composite Beams (C3-008) | S2-01 | Uninvented |
| C4-009 | Carbon Matrix Fuel Blocks | Biochemical Feedstock (C1-001) | Carbon Fuel Pellets (C3-009) | S2-01 | Uninvented |
| C4-010 | Polymer Sealed Power Modules | Biochemical Feedstock (C1-001) | Encapsulated Power Cells (C3-010) | S2-01 | Uninvented |
| C4-011 | Biofiber Insulation Panels | Biochemical Feedstock (C1-001) | Mineral Insulation Foam (C3-011) | S2-01 | Uninvented |
| C4-012 | Bioprocess Electrolytes | Biochemical Feedstock (C1-001) | Process Electrolytes (C3-012) | S2-01 | Uninvented |
| C4-013 | Bioprocess Catalyst Beads | Biochemical Feedstock (C1-001) | Supported Catalysts (C3-013) | S2-01 | Uninvented |
| C4-014 | Biological Tracer Beads | Biochemical Feedstock (C1-001) | Mineral Tracer Beads (C3-014) | S2-01 | Uninvented |
| C4-015 | Bioceramic Scaffolds | Biochemical Feedstock (C1-001) | Ceramic Insulators (C3-015) | S2-01 | Uninvented |
| C4-016 | Organic Interface Chips | Biochemical Feedstock (C1-001) | Doped Semiconductor Dies (C3-016) | S2-01 | Uninvented |
| C4-017 | Fiber Backed Shielding Tiles | Biochemical Feedstock (C1-001) | Shielding Tiles (C3-017) | S2-01 | Starting |
| C4-018 | Composite Hull Panels | Biochemical Feedstock (C1-001) | Corrosion Resistant Plates (C3-018) | S2-01 | Uninvented |
| C4-019 | Carbon Coated Fuel Pellets | Biochemical Feedstock (C1-001) | Ceramic Fuel Pellets (C3-019) | S2-01 | Uninvented |
| C4-020 | Resin Potted Power Capsules | Biochemical Feedstock (C1-001) | Ceramic Power Capsules (C3-020) | S2-01 | Uninvented |
| C4-021 | Fiber Reinforced Body Panels | Biochemical Feedstock (C1-001) | Reinforced Polymer Panels (C3-021) | S2-01 | Uninvented |
| C4-022 | Organic Plating Baths | Biochemical Feedstock (C1-001) | Electroplating Salts (C3-022) | S2-01 | Uninvented |
| C4-023 | Biocatalytic Mesh | Biochemical Feedstock (C1-001) | Catalytic Mesh (C3-023) | S2-01 | Starting |
| C4-024 | Tissue Tracer Capsules | Biochemical Feedstock (C1-001) | Tracer Capsules (C3-024) | S2-01 | Uninvented |
| C4-025 | Self Lubricating Bearing Inserts | Biochemical Feedstock (C1-001) | Ceramic Bearing Inserts (C3-025) | S2-01 | Uninvented |
| C4-026 | Resin Encapsulated Transistors | Biochemical Feedstock (C1-001) | Power Transistors (C3-026) | S2-01 | Uninvented |
| C4-027 | Resin Lined Shielded Containers | Biochemical Feedstock (C1-001) | Shielded Containers (C3-027) | S2-01 | Uninvented |
| C4-028 | Composite Drive Gears | Biochemical Feedstock (C1-001) | Precision Gears (C3-028) | S2-01 | Uninvented |
| C4-029 | Carbon Sleeved Fuel Rods | Biochemical Feedstock (C1-001) | Fuel Rods (C3-029) | S2-01 | Uninvented |
| C4-030 | Resin Potted Nuclear Batteries | Biochemical Feedstock (C1-001) | Nuclear Battery Packs (C3-030) | S2-01 | Starting |
| C4-031 | Polymer Tracer Films | Biochemical Feedstock (C1-001) | Radioactive Polymer Standards (C3-031) | S2-01 | Uninvented |
| C4-032 | Biological Isotope Reagents | Biochemical Feedstock (C1-001) | Isotope Reagents (C3-032) | S2-01 | Uninvented |
| C4-033 | Tagged Enzyme Preparations | Biochemical Feedstock (C1-001) | Radiolabeled Catalysts (C3-033) | S2-01 | Uninvented |
| C4-034 | Targeted Isotope Doses | Biochemical Feedstock (C1-001) | Therapeutic Isotope Doses (C3-034) | S2-01 | Uninvented |
| C4-035 | Resin Bound Radiation Sources | Biochemical Feedstock (C1-001) | Ceramic Radiation Sources (C3-035) | S2-01 | Uninvented |
| C4-036 | Bioassay Detector Chips | Biochemical Feedstock (C1-001) | Radiation Detector Dies (C3-036) | S2-01 | Uninvented |
| C4-037 | Polymer Encased Source Capsules | Biochemical Feedstock (C1-001) | Shielded Source Capsules (C3-037) | S2-01 | Uninvented |
| C4-038 | Carbon Bound Source Pellets | Biochemical Feedstock (C1-001) | Alloy Source Pellets (C3-038) | S2-01 | Uninvented |
| C4-039 | Organic Matrix Fuel Pellets | Biochemical Feedstock (C1-001) | Enriched Fuel Pellets (C3-039) | S2-01 | Uninvented |
| C4-040 | Resin Sealed Isotope Cells | Biochemical Feedstock (C1-001) | High Output Isotope Cells (C3-040) | S2-01 | Uninvented |

### C4 products adding Inorganic Concentrate

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-041 | Mineral Filled Resin | Inorganic Concentrate (C1-002) | Biopolymer Resin (C3-001) | S2-02 | Uninvented |
| C4-042 | Buffered Culture Media | Inorganic Concentrate (C1-002) | Culture Nutrients (C3-002) | S2-02 | Uninvented |
| C4-043 | Mineral Bound Enzymes | Inorganic Concentrate (C1-002) | Enzyme Catalysts (C3-003) | S2-02 | Uninvented |
| C4-044 | Buffered Diagnostic Tracers | Inorganic Concentrate (C1-002) | Diagnostic Tracers (C3-004) | S2-02 | Uninvented |
| C4-045 | Mineral Adsorption Filters | Inorganic Concentrate (C1-002) | Porous Ceramic Filters (C3-005) | S2-02 | Uninvented |
| C4-046 | Microfluidic Biosensor Chips | Inorganic Concentrate (C1-002) | Biosensor Chips (C3-006) | S2-02 | Starting |
| C4-047 | Mineral Composite Shielding | Inorganic Concentrate (C1-002) | Organic Shielding Blocks (C3-007) | S2-02 | Uninvented |
| C4-048 | Ceramic Coated Composite Beams | Inorganic Concentrate (C1-002) | Composite Beams (C3-008) | S2-02 | Uninvented |
| C4-049 | Ceramic Coated Carbon Fuel | Inorganic Concentrate (C1-002) | Carbon Fuel Pellets (C3-009) | S2-02 | Uninvented |
| C4-050 | Mineral Encased Power Cells | Inorganic Concentrate (C1-002) | Encapsulated Power Cells (C3-010) | S2-02 | Uninvented |
| C4-051 | Fire Barrier Foam Boards | Inorganic Concentrate (C1-002) | Mineral Insulation Foam (C3-011) | S2-02 | Uninvented |
| C4-052 | Battery Electrolytes | Inorganic Concentrate (C1-002) | Process Electrolytes (C3-012) | S2-02 | Starting |
| C4-053 | Mineral Catalyst Granules | Inorganic Concentrate (C1-002) | Supported Catalysts (C3-013) | S2-02 | Uninvented |
| C4-054 | Radiotracer Calibration Beads | Inorganic Concentrate (C1-002) | Mineral Tracer Beads (C3-014) | S2-02 | Uninvented |
| C4-055 | High Voltage Insulators | Inorganic Concentrate (C1-002) | Ceramic Insulators (C3-015) | S2-02 | Uninvented |
| C4-056 | Semiconductor Sensor Dies | Inorganic Concentrate (C1-002) | Doped Semiconductor Dies (C3-016) | S2-02 | Uninvented |
| C4-057 | Dense Shielding Tiles | Inorganic Concentrate (C1-002) | Shielding Tiles (C3-017) | S2-02 | Uninvented |
| C4-058 | Mineral Coated Armor Plates | Inorganic Concentrate (C1-002) | Corrosion Resistant Plates (C3-018) | S2-02 | Uninvented |
| C4-059 | Oxide Fuel Pellets | Inorganic Concentrate (C1-002) | Ceramic Fuel Pellets (C3-019) | S2-02 | Uninvented |
| C4-060 | Sealed Ceramic Power Capsules | Inorganic Concentrate (C1-002) | Ceramic Power Capsules (C3-020) | S2-02 | Uninvented |
| C4-061 | Mineral Coated Polymer Panels | Inorganic Concentrate (C1-002) | Reinforced Polymer Panels (C3-021) | S2-02 | Uninvented |
| C4-062 | Plating Bath Concentrates | Inorganic Concentrate (C1-002) | Electroplating Salts (C3-022) | S2-02 | Uninvented |
| C4-063 | Ceramic Supported Catalyst Mesh | Inorganic Concentrate (C1-002) | Catalytic Mesh (C3-023) | S2-02 | Uninvented |
| C4-064 | Mineral Filled Tracer Capsules | Inorganic Concentrate (C1-002) | Tracer Capsules (C3-024) | S2-02 | Uninvented |
| C4-065 | Ceramic Thrust Bearings | Inorganic Concentrate (C1-002) | Ceramic Bearing Inserts (C3-025) | S2-02 | Uninvented |
| C4-066 | Passivated Power Transistors | Inorganic Concentrate (C1-002) | Power Transistors (C3-026) | S2-02 | Uninvented |
| C4-067 | Ceramic Lined Shielded Containers | Inorganic Concentrate (C1-002) | Shielded Containers (C3-027) | S2-02 | Uninvented |
| C4-068 | Ceramic Coated Precision Gears | Inorganic Concentrate (C1-002) | Precision Gears (C3-028) | S2-02 | Starting |
| C4-069 | Oxide Coated Fuel Rods | Inorganic Concentrate (C1-002) | Fuel Rods (C3-029) | S2-02 | Uninvented |
| C4-070 | Ceramic Encased Nuclear Batteries | Inorganic Concentrate (C1-002) | Nuclear Battery Packs (C3-030) | S2-02 | Uninvented |
| C4-071 | Radioactive Mineral Polymer Standards | Inorganic Concentrate (C1-002) | Radioactive Polymer Standards (C3-031) | S2-02 | Uninvented |
| C4-072 | Isotope Calibration Solutions | Inorganic Concentrate (C1-002) | Isotope Reagents (C3-032) | S2-02 | Uninvented |
| C4-073 | Mineral Bound Radiocatalysts | Inorganic Concentrate (C1-002) | Radiolabeled Catalysts (C3-033) | S2-02 | Uninvented |
| C4-074 | Buffered Therapeutic Isotopes | Inorganic Concentrate (C1-002) | Therapeutic Isotope Doses (C3-034) | S2-02 | Uninvented |
| C4-075 | Glass Sealed Radiation Sources | Inorganic Concentrate (C1-002) | Ceramic Radiation Sources (C3-035) | S2-02 | Starting |
| C4-076 | Passivated Radiation Detector Dies | Inorganic Concentrate (C1-002) | Radiation Detector Dies (C3-036) | S2-02 | Uninvented |
| C4-077 | Ceramic Encased Source Capsules | Inorganic Concentrate (C1-002) | Shielded Source Capsules (C3-037) | S2-02 | Uninvented |
| C4-078 | Mineral Bound Source Pellets | Inorganic Concentrate (C1-002) | Alloy Source Pellets (C3-038) | S2-02 | Uninvented |
| C4-079 | Enriched Ceramic Fuel | Inorganic Concentrate (C1-002) | Enriched Fuel Pellets (C3-039) | S2-02 | Uninvented |
| C4-080 | Ceramic Sealed Isotope Cells | Inorganic Concentrate (C1-002) | High Output Isotope Cells (C3-040) | S2-02 | Uninvented |

### C4 products adding Metal Ingots

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-081 | Conductive Polymer Sheets | Metal Ingots (C1-003) | Biopolymer Resin (C3-001) | S2-03 | Uninvented |
| C4-082 | Metal Enriched Culture Nutrients | Metal Ingots (C1-003) | Culture Nutrients (C3-002) | S2-03 | Uninvented |
| C4-083 | Metal Supported Enzyme Catalysts | Metal Ingots (C1-003) | Enzyme Catalysts (C3-003) | S2-03 | Uninvented |
| C4-084 | Metal Bound Diagnostic Tracers | Metal Ingots (C1-003) | Diagnostic Tracers (C3-004) | S2-03 | Uninvented |
| C4-085 | Cased Ceramic Filters | Metal Ingots (C1-003) | Porous Ceramic Filters (C3-005) | S2-03 | Uninvented |
| C4-086 | Packaged Biosensor Chips | Metal Ingots (C1-003) | Biosensor Chips (C3-006) | S2-03 | Uninvented |
| C4-087 | Shielding Door Panels | Metal Ingots (C1-003) | Organic Shielding Blocks (C3-007) | S2-03 | Uninvented |
| C4-088 | Composite Structural Frames | Metal Ingots (C1-003) | Composite Beams (C3-008) | S2-03 | Uninvented |
| C4-089 | Canned Carbon Fuel Pellets | Metal Ingots (C1-003) | Carbon Fuel Pellets (C3-009) | S2-03 | Uninvented |
| C4-090 | Armored Power Cell Modules | Metal Ingots (C1-003) | Encapsulated Power Cells (C3-010) | S2-03 | Starting |
| C4-091 | Metal Faced Insulation Panels | Metal Ingots (C1-003) | Mineral Insulation Foam (C3-011) | S2-03 | Uninvented |
| C4-092 | Electrochemical Electrode Packs | Metal Ingots (C1-003) | Process Electrolytes (C3-012) | S2-03 | Uninvented |
| C4-093 | Catalyst Grids | Metal Ingots (C1-003) | Supported Catalysts (C3-013) | S2-03 | Uninvented |
| C4-094 | Sealed Mineral Tracer Sources | Metal Ingots (C1-003) | Mineral Tracer Beads (C3-014) | S2-03 | Uninvented |
| C4-095 | Ceramic Feedthrough Assemblies | Metal Ingots (C1-003) | Ceramic Insulators (C3-015) | S2-03 | Uninvented |
| C4-096 | Packaged Semiconductor Devices | Metal Ingots (C1-003) | Doped Semiconductor Dies (C3-016) | S2-03 | Uninvented |
| C4-097 | Shielding Wall Panels | Metal Ingots (C1-003) | Shielding Tiles (C3-017) | S2-03 | Uninvented |
| C4-098 | Structural Armor Sections | Metal Ingots (C1-003) | Corrosion Resistant Plates (C3-018) | S2-03 | Uninvented |
| C4-099 | Clad Ceramic Fuel Pellets | Metal Ingots (C1-003) | Ceramic Fuel Pellets (C3-019) | S2-03 | Uninvented |
| C4-100 | Metal Cased Power Capsules | Metal Ingots (C1-003) | Ceramic Power Capsules (C3-020) | S2-03 | Uninvented |
| C4-101 | Reinforced Equipment Housings | Metal Ingots (C1-003) | Reinforced Polymer Panels (C3-021) | S2-03 | Uninvented |
| C4-102 | Electroplating Anode Kits | Metal Ingots (C1-003) | Electroplating Salts (C3-022) | S2-03 | Uninvented |
| C4-103 | Catalytic Converter Cores | Metal Ingots (C1-003) | Catalytic Mesh (C3-023) | S2-03 | Uninvented |
| C4-104 | Sealed Tracer Source Assemblies | Metal Ingots (C1-003) | Tracer Capsules (C3-024) | S2-03 | Uninvented |
| C4-105 | Bearing Assemblies | Metal Ingots (C1-003) | Ceramic Bearing Inserts (C3-025) | S2-03 | Uninvented |
| C4-106 | Power Switching Modules | Metal Ingots (C1-003) | Power Transistors (C3-026) | S2-03 | Uninvented |
| C4-107 | Shielded Transport Casks | Metal Ingots (C1-003) | Shielded Containers (C3-027) | S2-03 | Uninvented |
| C4-108 | Gearbox Assemblies | Metal Ingots (C1-003) | Precision Gears (C3-028) | S2-03 | Uninvented |
| C4-109 | Fuel Rod Bundles | Metal Ingots (C1-003) | Fuel Rods (C3-029) | S2-03 | Starting |
| C4-110 | Nuclear Battery Banks | Metal Ingots (C1-003) | Nuclear Battery Packs (C3-030) | S2-03 | Uninvented |
| C4-111 | Metal Backed Radioactive Standards | Metal Ingots (C1-003) | Radioactive Polymer Standards (C3-031) | S2-03 | Uninvented |
| C4-112 | Metal Isotope Reagents | Metal Ingots (C1-003) | Isotope Reagents (C3-032) | S2-03 | Uninvented |
| C4-113 | Tagged Catalyst Grids | Metal Ingots (C1-003) | Radiolabeled Catalysts (C3-033) | S2-03 | Uninvented |
| C4-114 | Sealed Therapeutic Sources | Metal Ingots (C1-003) | Therapeutic Isotope Doses (C3-034) | S2-03 | Uninvented |
| C4-115 | Radiation Source Holders | Metal Ingots (C1-003) | Ceramic Radiation Sources (C3-035) | S2-03 | Uninvented |
| C4-116 | Radiation Detector Modules | Metal Ingots (C1-003) | Radiation Detector Dies (C3-036) | S2-03 | Starting |
| C4-117 | Source Storage Casks | Metal Ingots (C1-003) | Shielded Source Capsules (C3-037) | S2-03 | Uninvented |
| C4-118 | Alloy Source Cartridges | Metal Ingots (C1-003) | Alloy Source Pellets (C3-038) | S2-03 | Uninvented |
| C4-119 | Clad Enriched Fuel Pellets | Metal Ingots (C1-003) | Enriched Fuel Pellets (C3-039) | S2-03 | Uninvented |
| C4-120 | High Output Nuclear Battery Modules | Metal Ingots (C1-003) | High Output Isotope Cells (C3-040) | S2-03 | Uninvented |

### C4 products adding Isotope Feed

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-121 | Radioactive Resin Standards | Isotope Feed (C1-004) | Biopolymer Resin (C3-001) | S2-04 | Uninvented |
| C4-122 | Radiolabeled Culture Nutrients | Isotope Feed (C1-004) | Culture Nutrients (C3-002) | S2-04 | Uninvented |
| C4-123 | Tracer Enzyme Catalysts | Isotope Feed (C1-004) | Enzyme Catalysts (C3-003) | S2-04 | Uninvented |
| C4-124 | Dual Isotope Diagnostic Tracers | Isotope Feed (C1-004) | Diagnostic Tracers (C3-004) | S2-04 | Uninvented |
| C4-125 | Ceramic Tracer Filters | Isotope Feed (C1-004) | Porous Ceramic Filters (C3-005) | S2-04 | Uninvented |
| C4-126 | Isotope Reference Biosensors | Isotope Feed (C1-004) | Biosensor Chips (C3-006) | S2-04 | Uninvented |
| C4-127 | Source Loaded Organic Shields | Isotope Feed (C1-004) | Organic Shielding Blocks (C3-007) | S2-04 | Uninvented |
| C4-128 | Composite Source Supports | Isotope Feed (C1-004) | Composite Beams (C3-008) | S2-04 | Uninvented |
| C4-129 | Enriched Carbon Fuel | Isotope Feed (C1-004) | Carbon Fuel Pellets (C3-009) | S2-04 | Uninvented |
| C4-130 | Dual Source Encapsulated Cells | Isotope Feed (C1-004) | Encapsulated Power Cells (C3-010) | S2-04 | Uninvented |
| C4-131 | Radioactive Foam Standards | Isotope Feed (C1-004) | Mineral Insulation Foam (C3-011) | S2-04 | Uninvented |
| C4-132 | Radiolabeled Electrolytes | Isotope Feed (C1-004) | Process Electrolytes (C3-012) | S2-04 | Uninvented |
| C4-133 | Tagged Supported Catalysts | Isotope Feed (C1-004) | Supported Catalysts (C3-013) | S2-04 | Uninvented |
| C4-134 | Dual Isotope Tracer Beads | Isotope Feed (C1-004) | Mineral Tracer Beads (C3-014) | S2-04 | Starting |
| C4-135 | Ceramic Source Insulators | Isotope Feed (C1-004) | Ceramic Insulators (C3-015) | S2-04 | Uninvented |
| C4-136 | Isotope Reference Sensor Dies | Isotope Feed (C1-004) | Doped Semiconductor Dies (C3-016) | S2-04 | Uninvented |
| C4-137 | Source Loaded Shielding Tiles | Isotope Feed (C1-004) | Shielding Tiles (C3-017) | S2-04 | Uninvented |
| C4-138 | Alloy Source Plates | Isotope Feed (C1-004) | Corrosion Resistant Plates (C3-018) | S2-04 | Uninvented |
| C4-139 | Enriched Oxide Fuel | Isotope Feed (C1-004) | Ceramic Fuel Pellets (C3-019) | S2-04 | Uninvented |
| C4-140 | Dual Source Ceramic Cells | Isotope Feed (C1-004) | Ceramic Power Capsules (C3-020) | S2-04 | Uninvented |
| C4-141 | Radioactive Panel Standards | Isotope Feed (C1-004) | Reinforced Polymer Panels (C3-021) | S2-04 | Uninvented |
| C4-142 | Radiolabeled Plating Salts | Isotope Feed (C1-004) | Electroplating Salts (C3-022) | S2-04 | Uninvented |
| C4-143 | Tagged Catalytic Mesh | Isotope Feed (C1-004) | Catalytic Mesh (C3-023) | S2-04 | Uninvented |
| C4-144 | Dual Isotope Tracer Capsules | Isotope Feed (C1-004) | Tracer Capsules (C3-024) | S2-04 | Uninvented |
| C4-145 | Ceramic Wear Tracer Inserts | Isotope Feed (C1-004) | Ceramic Bearing Inserts (C3-025) | S2-04 | Uninvented |
| C4-146 | Isotope Reference Transistors | Isotope Feed (C1-004) | Power Transistors (C3-026) | S2-04 | Uninvented |
| C4-147 | Shielded Irradiation Containers | Isotope Feed (C1-004) | Shielded Containers (C3-027) | S2-04 | Uninvented |
| C4-148 | Gear Wear Tracers | Isotope Feed (C1-004) | Precision Gears (C3-028) | S2-04 | Uninvented |
| C4-149 | Enriched Fuel Rods | Isotope Feed (C1-004) | Fuel Rods (C3-029) | S2-04 | Uninvented |
| C4-150 | Dual Source Nuclear Batteries | Isotope Feed (C1-004) | Nuclear Battery Packs (C3-030) | S2-04 | Uninvented |
| C4-151 | Multi Isotope Polymer Standards | Isotope Feed (C1-004) | Radioactive Polymer Standards (C3-031) | S2-04 | Uninvented |
| C4-152 | Multi Isotope Reagent Sets | Isotope Feed (C1-004) | Isotope Reagents (C3-032) | S2-04 | Starting |
| C4-153 | Multi Isotope Catalyst Standards | Isotope Feed (C1-004) | Radiolabeled Catalysts (C3-033) | S2-04 | Uninvented |
| C4-154 | Combined Isotope Therapy Doses | Isotope Feed (C1-004) | Therapeutic Isotope Doses (C3-034) | S2-04 | Uninvented |
| C4-155 | Multi Isotope Ceramic Sources | Isotope Feed (C1-004) | Ceramic Radiation Sources (C3-035) | S2-04 | Uninvented |
| C4-156 | Calibrated Isotope Detector Dies | Isotope Feed (C1-004) | Radiation Detector Dies (C3-036) | S2-04 | Uninvented |
| C4-157 | Multi Isotope Source Capsules | Isotope Feed (C1-004) | Shielded Source Capsules (C3-037) | S2-04 | Uninvented |
| C4-158 | Multi Isotope Alloy Sources | Isotope Feed (C1-004) | Alloy Source Pellets (C3-038) | S2-04 | Uninvented |
| C4-159 | Blended Isotope Reactor Fuel | Isotope Feed (C1-004) | Enriched Fuel Pellets (C3-039) | S2-04 | Starting |
| C4-160 | Multi Source Isotope Power Modules | Isotope Feed (C1-004) | High Output Isotope Cells (C3-040) | S2-04 | Uninvented |

## T2 C4 products made from two C2 materials

These 55 recipes cover every unordered pair of C2 materials, including ten repeated pairs. All 55 are in the current starting catalog.

### Pairs beginning with Engineered Polymers or Fine Chemicals

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-161 | Polymer Laminates | Engineered Polymers (C2-001) | Engineered Polymers (C2-001) | S2-05 | Starting |
| C4-162 | Adhesive Sealants | Engineered Polymers (C2-001) | Fine Chemicals (C2-002) | S2-05 | Starting |
| C4-163 | Catalytic Membranes | Engineered Polymers (C2-001) | Catalysts (C2-003) | S2-07 | Starting |
| C4-164 | Tracer Patches | Engineered Polymers (C2-001) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C4-165 | Ceramic Polymer Composites | Engineered Polymers (C2-001) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C4-166 | Flexible Circuit Sheets | Engineered Polymers (C2-001) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C4-167 | Shielding Blankets | Engineered Polymers (C2-001) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C4-168 | Composite Pressure Housings | Engineered Polymers (C2-001) | Structural Alloys (C2-008) | S2-12 | Starting |
| C4-169 | Polymer Bound Fuel Blocks | Engineered Polymers (C2-001) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-170 | Flexible Isotope Battery Mats | Engineered Polymers (C2-001) | Isotope Power Cells (C2-010) | S2-14 | Starting |
| C4-171 | Laboratory Reagent Sets | Fine Chemicals (C2-002) | Fine Chemicals (C2-002) | S2-06 | Starting |
| C4-172 | Chemical Synthesis Catalysts | Fine Chemicals (C2-002) | Catalysts (C2-003) | S2-06 | Starting |
| C4-173 | Diagnostic Contrast Reagents | Fine Chemicals (C2-002) | Radiopharmaceuticals (C2-004) | S2-06 | Starting |
| C4-174 | Chemical Filter Monoliths | Fine Chemicals (C2-002) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C4-175 | Chemical Sensor Chips | Fine Chemicals (C2-002) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C4-176 | Shielding Grout | Fine Chemicals (C2-002) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C4-177 | Passivated Alloy Plates | Fine Chemicals (C2-002) | Structural Alloys (C2-008) | S2-12 | Starting |
| C4-178 | Fuel Conditioning Compounds | Fine Chemicals (C2-002) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-179 | Sealed Isotope Power Cartridges | Fine Chemicals (C2-002) | Isotope Power Cells (C2-010) | S2-14 | Starting |

### Pairs beginning with Catalysts or Radiopharmaceuticals

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-180 | Multistage Catalyst Charges | Catalysts (C2-003) | Catalysts (C2-003) | S2-07 | Starting |
| C4-181 | Radiotracer Synthesis Cartridges | Catalysts (C2-003) | Radiopharmaceuticals (C2-004) | S2-07 | Starting |
| C4-182 | Catalytic Ceramic Monoliths | Catalysts (C2-003) | Technical Ceramics (C2-005) | S2-07 | Starting |
| C4-183 | Gas Sensor Elements | Catalysts (C2-003) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C4-184 | Shielded Catalyst Cartridges | Catalysts (C2-003) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C4-185 | Catalytic Alloy Screens | Catalysts (C2-003) | Structural Alloys (C2-008) | S2-12 | Starting |
| C4-186 | Catalyst Bound Reactor Fuel | Catalysts (C2-003) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-187 | Isotope Powered Catalyst Cartridges | Catalysts (C2-003) | Isotope Power Cells (C2-010) | S2-14 | Starting |
| C4-188 | Multi Tracer Diagnostic Sets | Radiopharmaceuticals (C2-004) | Radiopharmaceuticals (C2-004) | S2-08 | Starting |
| C4-189 | Ceramic Tracer Implants | Radiopharmaceuticals (C2-004) | Technical Ceramics (C2-005) | S2-08 | Starting |
| C4-190 | Radiotracer Sensor Chips | Radiopharmaceuticals (C2-004) | Semiconductor Wafers (C2-006) | S2-08 | Starting |
| C4-191 | Shielded Medical Isotope Packs | Radiopharmaceuticals (C2-004) | Radiation Shielding (C2-007) | S2-08 | Starting |
| C4-192 | Radiotherapy Applicators | Radiopharmaceuticals (C2-004) | Structural Alloys (C2-008) | S2-12 | Starting |
| C4-193 | Medical Isotope Target Fuel | Radiopharmaceuticals (C2-004) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-194 | Isotope Heated Tracer Packs | Radiopharmaceuticals (C2-004) | Isotope Power Cells (C2-010) | S2-14 | Starting |

### Remaining ceramic electronic shielding alloy and power pairs

| Recipe ID | Proposed product name | Input 1 | Input 2 | Sector | Starting selection |
|---|---|---|---|---|---|
| C4-195 | Ceramic Tool Blanks | Technical Ceramics (C2-005) | Technical Ceramics (C2-005) | S2-09 | Starting |
| C4-196 | Ceramic Circuit Substrates | Technical Ceramics (C2-005) | Semiconductor Wafers (C2-006) | S2-09 | Starting |
| C4-197 | Shielding Bricks | Technical Ceramics (C2-005) | Radiation Shielding (C2-007) | S2-09 | Starting |
| C4-198 | Ceramic Armor Panels | Technical Ceramics (C2-005) | Structural Alloys (C2-008) | S2-09 | Starting |
| C4-199 | Reactor Fuel Tiles | Technical Ceramics (C2-005) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-200 | Ceramic Isotope Generators | Technical Ceramics (C2-005) | Isotope Power Cells (C2-010) | S2-14 | Starting |
| C4-201 | Integrated Circuit Arrays | Semiconductor Wafers (C2-006) | Semiconductor Wafers (C2-006) | S2-10 | Starting |
| C4-202 | Shielded Sensor Arrays | Semiconductor Wafers (C2-006) | Radiation Shielding (C2-007) | S2-10 | Starting |
| C4-203 | Industrial Control Boards | Semiconductor Wafers (C2-006) | Structural Alloys (C2-008) | S2-10 | Starting |
| C4-204 | Instrumented Fuel Elements | Semiconductor Wafers (C2-006) | Reactor Fuel (C2-009) | S2-10 | Starting |
| C4-205 | Autonomous Sensor Nodes | Semiconductor Wafers (C2-006) | Isotope Power Cells (C2-010) | S2-14 | Starting |
| C4-206 | Shielding Vault Blocks | Radiation Shielding (C2-007) | Radiation Shielding (C2-007) | S2-11 | Starting |
| C4-207 | Reactor Shield Assemblies | Radiation Shielding (C2-007) | Structural Alloys (C2-008) | S2-11 | Starting |
| C4-208 | Shielded Fuel Cartridges | Radiation Shielding (C2-007) | Reactor Fuel (C2-009) | S2-11 | Starting |
| C4-209 | Shielded Power Modules | Radiation Shielding (C2-007) | Isotope Power Cells (C2-010) | S2-11 | Starting |
| C4-210 | Heavy Structural Frames | Structural Alloys (C2-008) | Structural Alloys (C2-008) | S2-12 | Starting |
| C4-211 | Reactor Core Cassettes | Structural Alloys (C2-008) | Reactor Fuel (C2-009) | S2-12 | Starting |
| C4-212 | Structural Power Modules | Structural Alloys (C2-008) | Isotope Power Cells (C2-010) | S2-12 | Starting |
| C4-213 | Reactor Fuel Assemblies | Reactor Fuel (C2-009) | Reactor Fuel (C2-009) | S2-13 | Starting |
| C4-214 | Heated Fuel Cartridges | Reactor Fuel (C2-009) | Isotope Power Cells (C2-010) | S2-13 | Starting |
| C4-215 | Isotope Power Banks | Isotope Power Cells (C2-010) | Isotope Power Cells (C2-010) | S2-14 | Starting |

## Equipment classes

These four existing general class names are retained. Equipment names describe the existing machinery identities and do not change costs, capacity, storage footprint, or supplier eligibility.

| Complexity | Equipment class |
|---|---|
| C-1 | Feedstock Conditioner |
| C-2 | Compound Processor |
| C-3 | Component Fabricator |
| C-4 | Product Finisher |

## Extraction equipment

| Equipment ID | Raw resource | Equipment name |
|---|---|---|
| EX-W | Organics | Organic Matter Harvester |
| EX-E | Inorganics | Inorganic Material Extractor |
| EX-F | Metals | Metal Extractor |
| EX-A | Radioactives | Radioactive Material Extractor |

## Machine families

Family IDs preserve the established sector and complexity scheme. Four C3 family slots, S2-01 through S2-04, have no recipes in the current universe. Their names complete the existing family table; they do not introduce recipes, purchasable installations, or new equipment suppliers. Recipe counts below include both starting and uninvented recipes.

### T1 refinery families

| Family ID | Family name | Series label | Recipes |
|---|---|---|---|
| MF-S1-01-C1 | Biochemical Refining Units | Biochemical | 1 |
| MF-S1-02-C1 | Inorganic Concentration Units | Inorganic | 1 |
| MF-S1-03-C1 | Metal Casting Units | Metal | 1 |
| MF-S1-04-C1 | Isotope Separation Units | Isotope | 1 |
| MF-S1-05-C2 | Polymer Processing Units | Polymer | 1 |
| MF-S1-06-C2 | Fine Chemical Processing Units | Chemical | 1 |
| MF-S1-07-C2 | Catalyst Preparation Units | Catalytic | 1 |
| MF-S1-08-C2 | Radiopharmaceutical Processing Units | Medical Isotope | 1 |
| MF-S1-09-C2 | Ceramic Processing Units | Ceramic | 1 |
| MF-S1-10-C2 | Wafer Fabrication Units | Electronic | 1 |
| MF-S1-11-C2 | Shielding Material Processing Units | Shielding | 1 |
| MF-S1-12-C2 | Alloy Casting Units | Alloy | 1 |
| MF-S1-13-C2 | Reactor Fuel Processing Units | Fuel | 1 |
| MF-S1-14-C2 | Isotope Cell Fabrication Units | Isotope Power | 1 |

### T2 C3 component families

| Family ID | Family name | Series label | Recipes |
|---|---|---|---|
| MF-S2-01-C3 | Biochemical Component Cells | Biochemical | 0 |
| MF-S2-02-C3 | Inorganic Component Cells | Inorganic | 0 |
| MF-S2-03-C3 | Metal Component Cells | Metal | 0 |
| MF-S2-04-C3 | Isotope Component Cells | Isotope | 0 |
| MF-S2-05-C3 | Polymer Component Cells | Polymer | 4 |
| MF-S2-06-C3 | Chemical Component Cells | Chemical | 4 |
| MF-S2-07-C3 | Catalytic Component Cells | Catalytic | 4 |
| MF-S2-08-C3 | Medical Isotope Component Cells | Medical Isotope | 4 |
| MF-S2-09-C3 | Ceramic Component Cells | Ceramic | 4 |
| MF-S2-10-C3 | Electronic Component Cells | Electronic | 4 |
| MF-S2-11-C3 | Shielding Component Cells | Shielding | 4 |
| MF-S2-12-C3 | Alloy Component Cells | Alloy | 4 |
| MF-S2-13-C3 | Fuel Component Cells | Fuel | 4 |
| MF-S2-14-C3 | Isotope Power Component Cells | Isotope Power | 4 |

### T2 C4 finishing families

| Family ID | Family name | Series label | Recipes |
|---|---|---|---|
| MF-S2-01-C4 | Biochemical Finishing Lines | Biochemical | 40 |
| MF-S2-02-C4 | Inorganic Finishing Lines | Inorganic | 40 |
| MF-S2-03-C4 | Metal Finishing Lines | Metal | 40 |
| MF-S2-04-C4 | Isotope Finishing Lines | Isotope | 40 |
| MF-S2-05-C4 | Polymer Finishing Lines | Polymer | 2 |
| MF-S2-06-C4 | Chemical Finishing Lines | Chemical | 3 |
| MF-S2-07-C4 | Catalytic Finishing Lines | Catalytic | 4 |
| MF-S2-08-C4 | Medical Isotope Finishing Lines | Medical Isotope | 5 |
| MF-S2-09-C4 | Ceramic Finishing Lines | Ceramic | 6 |
| MF-S2-10-C4 | Electronic Finishing Lines | Electronic | 7 |
| MF-S2-11-C4 | Shielding Finishing Lines | Shielding | 7 |
| MF-S2-12-C4 | Alloy Finishing Lines | Alloy | 7 |
| MF-S2-13-C4 | Fuel Finishing Lines | Fuel | 7 |
| MF-S2-14-C4 | Isotope Power Finishing Lines | Isotope Power | 7 |

## Recipe installation names

Every recipe has one explicit installation name and family binding. C4 names use the product's singular form followed by Production Line. These names label the existing recipe installations; they do not create additional production lines or a new recipe type. Installation availability follows the product's starting-selection status above.

### T1 refining installations

| Recipe ID | Product name | Family ID | Installation name |
|---|---|---|---|
| C1-001 | Biochemical Feedstock | MF-S1-01-C1 | Biochemical Feedstock Refining Unit |
| C1-002 | Inorganic Concentrate | MF-S1-02-C1 | Inorganic Concentration Unit |
| C1-003 | Metal Ingots | MF-S1-03-C1 | Metal Ingot Casting Unit |
| C1-004 | Isotope Feed | MF-S1-04-C1 | Isotope Feed Separation Unit |
| C2-001 | Engineered Polymers | MF-S1-05-C2 | Engineered Polymer Processor |
| C2-002 | Fine Chemicals | MF-S1-06-C2 | Fine Chemical Processor |
| C2-003 | Catalysts | MF-S1-07-C2 | Catalyst Preparation Unit |
| C2-004 | Radiopharmaceuticals | MF-S1-08-C2 | Radiopharmaceutical Processor |
| C2-005 | Technical Ceramics | MF-S1-09-C2 | Technical Ceramic Kiln |
| C2-006 | Semiconductor Wafers | MF-S1-10-C2 | Semiconductor Wafer Fabricator |
| C2-007 | Radiation Shielding | MF-S1-11-C2 | Radiation Shielding Press |
| C2-008 | Structural Alloys | MF-S1-12-C2 | Structural Alloy Furnace |
| C2-009 | Reactor Fuel | MF-S1-13-C2 | Reactor Fuel Processor |
| C2-010 | Isotope Power Cells | MF-S1-14-C2 | Isotope Power Cell Assembler |

### T2 C3 installations

| Recipe ID | Product name | Family ID | Installation name |
|---|---|---|---|
| C3-001 | Biopolymer Resin | MF-S2-05-C3 | Biopolymer Resin Processor |
| C3-002 | Culture Nutrients | MF-S2-06-C3 | Culture Nutrient Mixer |
| C3-003 | Enzyme Catalysts | MF-S2-07-C3 | Enzyme Catalyst Processor |
| C3-004 | Diagnostic Tracers | MF-S2-08-C3 | Diagnostic Tracer Processor |
| C3-005 | Porous Ceramic Filters | MF-S2-09-C3 | Porous Ceramic Filter Former |
| C3-006 | Biosensor Chips | MF-S2-10-C3 | Biosensor Chip Fabricator |
| C3-007 | Organic Shielding Blocks | MF-S2-11-C3 | Organic Shielding Block Press |
| C3-008 | Composite Beams | MF-S2-12-C3 | Composite Beam Former |
| C3-009 | Carbon Fuel Pellets | MF-S2-13-C3 | Carbon Fuel Pellet Press |
| C3-010 | Encapsulated Power Cells | MF-S2-14-C3 | Power Cell Encapsulation Unit |
| C3-011 | Mineral Insulation Foam | MF-S2-05-C3 | Mineral Insulation Foam Processor |
| C3-012 | Process Electrolytes | MF-S2-06-C3 | Process Electrolyte Mixer |
| C3-013 | Supported Catalysts | MF-S2-07-C3 | Supported Catalyst Processor |
| C3-014 | Mineral Tracer Beads | MF-S2-08-C3 | Mineral Tracer Bead Former |
| C3-015 | Ceramic Insulators | MF-S2-09-C3 | Ceramic Insulator Former |
| C3-016 | Doped Semiconductor Dies | MF-S2-10-C3 | Semiconductor Die Processor |
| C3-017 | Shielding Tiles | MF-S2-11-C3 | Shielding Tile Press |
| C3-018 | Corrosion Resistant Plates | MF-S2-12-C3 | Corrosion Resistant Plate Processor |
| C3-019 | Ceramic Fuel Pellets | MF-S2-13-C3 | Ceramic Fuel Pellet Press |
| C3-020 | Ceramic Power Capsules | MF-S2-14-C3 | Ceramic Power Capsule Assembler |
| C3-021 | Reinforced Polymer Panels | MF-S2-05-C3 | Reinforced Polymer Panel Press |
| C3-022 | Electroplating Salts | MF-S2-06-C3 | Electroplating Salt Processor |
| C3-023 | Catalytic Mesh | MF-S2-07-C3 | Catalytic Mesh Fabricator |
| C3-024 | Tracer Capsules | MF-S2-08-C3 | Tracer Capsule Assembler |
| C3-025 | Ceramic Bearing Inserts | MF-S2-09-C3 | Ceramic Bearing Insert Grinder |
| C3-026 | Power Transistors | MF-S2-10-C3 | Power Transistor Fabricator |
| C3-027 | Shielded Containers | MF-S2-11-C3 | Shielded Container Assembler |
| C3-028 | Precision Gears | MF-S2-12-C3 | Precision Gear Cutter |
| C3-029 | Fuel Rods | MF-S2-13-C3 | Fuel Rod Assembler |
| C3-030 | Nuclear Battery Packs | MF-S2-14-C3 | Nuclear Battery Pack Assembler |
| C3-031 | Radioactive Polymer Standards | MF-S2-05-C3 | Radioactive Polymer Standard Processor |
| C3-032 | Isotope Reagents | MF-S2-06-C3 | Isotope Reagent Mixer |
| C3-033 | Radiolabeled Catalysts | MF-S2-07-C3 | Radiolabeled Catalyst Processor |
| C3-034 | Therapeutic Isotope Doses | MF-S2-08-C3 | Therapeutic Isotope Dose Processor |
| C3-035 | Ceramic Radiation Sources | MF-S2-09-C3 | Ceramic Radiation Source Former |
| C3-036 | Radiation Detector Dies | MF-S2-10-C3 | Radiation Detector Die Fabricator |
| C3-037 | Shielded Source Capsules | MF-S2-11-C3 | Shielded Source Capsule Assembler |
| C3-038 | Alloy Source Pellets | MF-S2-12-C3 | Alloy Source Pellet Press |
| C3-039 | Enriched Fuel Pellets | MF-S2-13-C3 | Enriched Fuel Pellet Press |
| C3-040 | High Output Isotope Cells | MF-S2-14-C3 | High Output Isotope Cell Assembler |

### T2 C4 installations from C1 and C3

| Recipe ID | Product name | Family ID | Installation name |
|---|---|---|---|
| C4-001 | Bioplastic Sheets | MF-S2-01-C4 | Bioplastic Sheet Production Line |
| C4-002 | Fermentation Feed | MF-S2-01-C4 | Fermentation Feed Production Line |
| C4-003 | Immobilized Enzyme Beads | MF-S2-01-C4 | Immobilized Enzyme Bead Production Line |
| C4-004 | Assay Tracer Kits | MF-S2-01-C4 | Assay Tracer Kit Production Line |
| C4-005 | Bioactive Filter Cartridges | MF-S2-01-C4 | Bioactive Filter Cartridge Production Line |
| C4-006 | Bioassay Sensors | MF-S2-01-C4 | Bioassay Sensor Production Line |
| C4-007 | Fiber Shielding Boards | MF-S2-01-C4 | Fiber Shielding Board Production Line |
| C4-008 | Carbon Composite Trusses | MF-S2-01-C4 | Carbon Composite Trusse Production Line |
| C4-009 | Carbon Matrix Fuel Blocks | MF-S2-01-C4 | Carbon Matrix Fuel Block Production Line |
| C4-010 | Polymer Sealed Power Modules | MF-S2-01-C4 | Polymer Sealed Power Module Production Line |
| C4-011 | Biofiber Insulation Panels | MF-S2-01-C4 | Biofiber Insulation Panel Production Line |
| C4-012 | Bioprocess Electrolytes | MF-S2-01-C4 | Bioprocess Electrolyte Production Line |
| C4-013 | Bioprocess Catalyst Beads | MF-S2-01-C4 | Bioprocess Catalyst Bead Production Line |
| C4-014 | Biological Tracer Beads | MF-S2-01-C4 | Biological Tracer Bead Production Line |
| C4-015 | Bioceramic Scaffolds | MF-S2-01-C4 | Bioceramic Scaffold Production Line |
| C4-016 | Organic Interface Chips | MF-S2-01-C4 | Organic Interface Chip Production Line |
| C4-017 | Fiber Backed Shielding Tiles | MF-S2-01-C4 | Fiber Backed Shielding Tile Production Line |
| C4-018 | Composite Hull Panels | MF-S2-01-C4 | Composite Hull Panel Production Line |
| C4-019 | Carbon Coated Fuel Pellets | MF-S2-01-C4 | Carbon Coated Fuel Pellet Production Line |
| C4-020 | Resin Potted Power Capsules | MF-S2-01-C4 | Resin Potted Power Capsule Production Line |
| C4-021 | Fiber Reinforced Body Panels | MF-S2-01-C4 | Fiber Reinforced Body Panel Production Line |
| C4-022 | Organic Plating Baths | MF-S2-01-C4 | Organic Plating Bath Production Line |
| C4-023 | Biocatalytic Mesh | MF-S2-01-C4 | Biocatalytic Mesh Production Line |
| C4-024 | Tissue Tracer Capsules | MF-S2-01-C4 | Tissue Tracer Capsule Production Line |
| C4-025 | Self Lubricating Bearing Inserts | MF-S2-01-C4 | Self Lubricating Bearing Insert Production Line |
| C4-026 | Resin Encapsulated Transistors | MF-S2-01-C4 | Resin Encapsulated Transistor Production Line |
| C4-027 | Resin Lined Shielded Containers | MF-S2-01-C4 | Resin Lined Shielded Container Production Line |
| C4-028 | Composite Drive Gears | MF-S2-01-C4 | Composite Drive Gear Production Line |
| C4-029 | Carbon Sleeved Fuel Rods | MF-S2-01-C4 | Carbon Sleeved Fuel Rod Production Line |
| C4-030 | Resin Potted Nuclear Batteries | MF-S2-01-C4 | Resin Potted Nuclear Battery Production Line |
| C4-031 | Polymer Tracer Films | MF-S2-01-C4 | Polymer Tracer Film Production Line |
| C4-032 | Biological Isotope Reagents | MF-S2-01-C4 | Biological Isotope Reagent Production Line |
| C4-033 | Tagged Enzyme Preparations | MF-S2-01-C4 | Tagged Enzyme Preparation Production Line |
| C4-034 | Targeted Isotope Doses | MF-S2-01-C4 | Targeted Isotope Dose Production Line |
| C4-035 | Resin Bound Radiation Sources | MF-S2-01-C4 | Resin Bound Radiation Source Production Line |
| C4-036 | Bioassay Detector Chips | MF-S2-01-C4 | Bioassay Detector Chip Production Line |
| C4-037 | Polymer Encased Source Capsules | MF-S2-01-C4 | Polymer Encased Source Capsule Production Line |
| C4-038 | Carbon Bound Source Pellets | MF-S2-01-C4 | Carbon Bound Source Pellet Production Line |
| C4-039 | Organic Matrix Fuel Pellets | MF-S2-01-C4 | Organic Matrix Fuel Pellet Production Line |
| C4-040 | Resin Sealed Isotope Cells | MF-S2-01-C4 | Resin Sealed Isotope Cell Production Line |
| C4-041 | Mineral Filled Resin | MF-S2-02-C4 | Mineral Filled Resin Production Line |
| C4-042 | Buffered Culture Media | MF-S2-02-C4 | Buffered Culture Medium Production Line |
| C4-043 | Mineral Bound Enzymes | MF-S2-02-C4 | Mineral Bound Enzyme Production Line |
| C4-044 | Buffered Diagnostic Tracers | MF-S2-02-C4 | Buffered Diagnostic Tracer Production Line |
| C4-045 | Mineral Adsorption Filters | MF-S2-02-C4 | Mineral Adsorption Filter Production Line |
| C4-046 | Microfluidic Biosensor Chips | MF-S2-02-C4 | Microfluidic Biosensor Chip Production Line |
| C4-047 | Mineral Composite Shielding | MF-S2-02-C4 | Mineral Composite Shielding Production Line |
| C4-048 | Ceramic Coated Composite Beams | MF-S2-02-C4 | Ceramic Coated Composite Beam Production Line |
| C4-049 | Ceramic Coated Carbon Fuel | MF-S2-02-C4 | Ceramic Coated Carbon Fuel Production Line |
| C4-050 | Mineral Encased Power Cells | MF-S2-02-C4 | Mineral Encased Power Cell Production Line |
| C4-051 | Fire Barrier Foam Boards | MF-S2-02-C4 | Fire Barrier Foam Board Production Line |
| C4-052 | Battery Electrolytes | MF-S2-02-C4 | Battery Electrolyte Production Line |
| C4-053 | Mineral Catalyst Granules | MF-S2-02-C4 | Mineral Catalyst Granule Production Line |
| C4-054 | Radiotracer Calibration Beads | MF-S2-02-C4 | Radiotracer Calibration Bead Production Line |
| C4-055 | High Voltage Insulators | MF-S2-02-C4 | High Voltage Insulator Production Line |
| C4-056 | Semiconductor Sensor Dies | MF-S2-02-C4 | Semiconductor Sensor Die Production Line |
| C4-057 | Dense Shielding Tiles | MF-S2-02-C4 | Dense Shielding Tile Production Line |
| C4-058 | Mineral Coated Armor Plates | MF-S2-02-C4 | Mineral Coated Armor Plate Production Line |
| C4-059 | Oxide Fuel Pellets | MF-S2-02-C4 | Oxide Fuel Pellet Production Line |
| C4-060 | Sealed Ceramic Power Capsules | MF-S2-02-C4 | Sealed Ceramic Power Capsule Production Line |
| C4-061 | Mineral Coated Polymer Panels | MF-S2-02-C4 | Mineral Coated Polymer Panel Production Line |
| C4-062 | Plating Bath Concentrates | MF-S2-02-C4 | Plating Bath Concentrate Production Line |
| C4-063 | Ceramic Supported Catalyst Mesh | MF-S2-02-C4 | Ceramic Supported Catalyst Mesh Production Line |
| C4-064 | Mineral Filled Tracer Capsules | MF-S2-02-C4 | Mineral Filled Tracer Capsule Production Line |
| C4-065 | Ceramic Thrust Bearings | MF-S2-02-C4 | Ceramic Thrust Bearing Production Line |
| C4-066 | Passivated Power Transistors | MF-S2-02-C4 | Passivated Power Transistor Production Line |
| C4-067 | Ceramic Lined Shielded Containers | MF-S2-02-C4 | Ceramic Lined Shielded Container Production Line |
| C4-068 | Ceramic Coated Precision Gears | MF-S2-02-C4 | Ceramic Coated Precision Gear Production Line |
| C4-069 | Oxide Coated Fuel Rods | MF-S2-02-C4 | Oxide Coated Fuel Rod Production Line |
| C4-070 | Ceramic Encased Nuclear Batteries | MF-S2-02-C4 | Ceramic Encased Nuclear Battery Production Line |
| C4-071 | Radioactive Mineral Polymer Standards | MF-S2-02-C4 | Radioactive Mineral Polymer Standard Production Line |
| C4-072 | Isotope Calibration Solutions | MF-S2-02-C4 | Isotope Calibration Solution Production Line |
| C4-073 | Mineral Bound Radiocatalysts | MF-S2-02-C4 | Mineral Bound Radiocatalyst Production Line |
| C4-074 | Buffered Therapeutic Isotopes | MF-S2-02-C4 | Buffered Therapeutic Isotope Production Line |
| C4-075 | Glass Sealed Radiation Sources | MF-S2-02-C4 | Glass Sealed Radiation Source Production Line |
| C4-076 | Passivated Radiation Detector Dies | MF-S2-02-C4 | Passivated Radiation Detector Die Production Line |
| C4-077 | Ceramic Encased Source Capsules | MF-S2-02-C4 | Ceramic Encased Source Capsule Production Line |
| C4-078 | Mineral Bound Source Pellets | MF-S2-02-C4 | Mineral Bound Source Pellet Production Line |
| C4-079 | Enriched Ceramic Fuel | MF-S2-02-C4 | Enriched Ceramic Fuel Production Line |
| C4-080 | Ceramic Sealed Isotope Cells | MF-S2-02-C4 | Ceramic Sealed Isotope Cell Production Line |
| C4-081 | Conductive Polymer Sheets | MF-S2-03-C4 | Conductive Polymer Sheet Production Line |
| C4-082 | Metal Enriched Culture Nutrients | MF-S2-03-C4 | Metal Enriched Culture Nutrient Production Line |
| C4-083 | Metal Supported Enzyme Catalysts | MF-S2-03-C4 | Metal Supported Enzyme Catalyst Production Line |
| C4-084 | Metal Bound Diagnostic Tracers | MF-S2-03-C4 | Metal Bound Diagnostic Tracer Production Line |
| C4-085 | Cased Ceramic Filters | MF-S2-03-C4 | Cased Ceramic Filter Production Line |
| C4-086 | Packaged Biosensor Chips | MF-S2-03-C4 | Packaged Biosensor Chip Production Line |
| C4-087 | Shielding Door Panels | MF-S2-03-C4 | Shielding Door Panel Production Line |
| C4-088 | Composite Structural Frames | MF-S2-03-C4 | Composite Structural Frame Production Line |
| C4-089 | Canned Carbon Fuel Pellets | MF-S2-03-C4 | Canned Carbon Fuel Pellet Production Line |
| C4-090 | Armored Power Cell Modules | MF-S2-03-C4 | Armored Power Cell Module Production Line |
| C4-091 | Metal Faced Insulation Panels | MF-S2-03-C4 | Metal Faced Insulation Panel Production Line |
| C4-092 | Electrochemical Electrode Packs | MF-S2-03-C4 | Electrochemical Electrode Pack Production Line |
| C4-093 | Catalyst Grids | MF-S2-03-C4 | Catalyst Grid Production Line |
| C4-094 | Sealed Mineral Tracer Sources | MF-S2-03-C4 | Sealed Mineral Tracer Source Production Line |
| C4-095 | Ceramic Feedthrough Assemblies | MF-S2-03-C4 | Ceramic Feedthrough Assembly Production Line |
| C4-096 | Packaged Semiconductor Devices | MF-S2-03-C4 | Packaged Semiconductor Device Production Line |
| C4-097 | Shielding Wall Panels | MF-S2-03-C4 | Shielding Wall Panel Production Line |
| C4-098 | Structural Armor Sections | MF-S2-03-C4 | Structural Armor Section Production Line |
| C4-099 | Clad Ceramic Fuel Pellets | MF-S2-03-C4 | Clad Ceramic Fuel Pellet Production Line |
| C4-100 | Metal Cased Power Capsules | MF-S2-03-C4 | Metal Cased Power Capsule Production Line |
| C4-101 | Reinforced Equipment Housings | MF-S2-03-C4 | Reinforced Equipment Housing Production Line |
| C4-102 | Electroplating Anode Kits | MF-S2-03-C4 | Electroplating Anode Kit Production Line |
| C4-103 | Catalytic Converter Cores | MF-S2-03-C4 | Catalytic Converter Core Production Line |
| C4-104 | Sealed Tracer Source Assemblies | MF-S2-03-C4 | Sealed Tracer Source Assembly Production Line |
| C4-105 | Bearing Assemblies | MF-S2-03-C4 | Bearing Assembly Production Line |
| C4-106 | Power Switching Modules | MF-S2-03-C4 | Power Switching Module Production Line |
| C4-107 | Shielded Transport Casks | MF-S2-03-C4 | Shielded Transport Cask Production Line |
| C4-108 | Gearbox Assemblies | MF-S2-03-C4 | Gearbox Assembly Production Line |
| C4-109 | Fuel Rod Bundles | MF-S2-03-C4 | Fuel Rod Bundle Production Line |
| C4-110 | Nuclear Battery Banks | MF-S2-03-C4 | Nuclear Battery Bank Production Line |
| C4-111 | Metal Backed Radioactive Standards | MF-S2-03-C4 | Metal Backed Radioactive Standard Production Line |
| C4-112 | Metal Isotope Reagents | MF-S2-03-C4 | Metal Isotope Reagent Production Line |
| C4-113 | Tagged Catalyst Grids | MF-S2-03-C4 | Tagged Catalyst Grid Production Line |
| C4-114 | Sealed Therapeutic Sources | MF-S2-03-C4 | Sealed Therapeutic Source Production Line |
| C4-115 | Radiation Source Holders | MF-S2-03-C4 | Radiation Source Holder Production Line |
| C4-116 | Radiation Detector Modules | MF-S2-03-C4 | Radiation Detector Module Production Line |
| C4-117 | Source Storage Casks | MF-S2-03-C4 | Source Storage Cask Production Line |
| C4-118 | Alloy Source Cartridges | MF-S2-03-C4 | Alloy Source Cartridge Production Line |
| C4-119 | Clad Enriched Fuel Pellets | MF-S2-03-C4 | Clad Enriched Fuel Pellet Production Line |
| C4-120 | High Output Nuclear Battery Modules | MF-S2-03-C4 | High Output Nuclear Battery Module Production Line |
| C4-121 | Radioactive Resin Standards | MF-S2-04-C4 | Radioactive Resin Standard Production Line |
| C4-122 | Radiolabeled Culture Nutrients | MF-S2-04-C4 | Radiolabeled Culture Nutrient Production Line |
| C4-123 | Tracer Enzyme Catalysts | MF-S2-04-C4 | Tracer Enzyme Catalyst Production Line |
| C4-124 | Dual Isotope Diagnostic Tracers | MF-S2-04-C4 | Dual Isotope Diagnostic Tracer Production Line |
| C4-125 | Ceramic Tracer Filters | MF-S2-04-C4 | Ceramic Tracer Filter Production Line |
| C4-126 | Isotope Reference Biosensors | MF-S2-04-C4 | Isotope Reference Biosensor Production Line |
| C4-127 | Source Loaded Organic Shields | MF-S2-04-C4 | Source Loaded Organic Shield Production Line |
| C4-128 | Composite Source Supports | MF-S2-04-C4 | Composite Source Support Production Line |
| C4-129 | Enriched Carbon Fuel | MF-S2-04-C4 | Enriched Carbon Fuel Production Line |
| C4-130 | Dual Source Encapsulated Cells | MF-S2-04-C4 | Dual Source Encapsulated Cell Production Line |
| C4-131 | Radioactive Foam Standards | MF-S2-04-C4 | Radioactive Foam Standard Production Line |
| C4-132 | Radiolabeled Electrolytes | MF-S2-04-C4 | Radiolabeled Electrolyte Production Line |
| C4-133 | Tagged Supported Catalysts | MF-S2-04-C4 | Tagged Supported Catalyst Production Line |
| C4-134 | Dual Isotope Tracer Beads | MF-S2-04-C4 | Dual Isotope Tracer Bead Production Line |
| C4-135 | Ceramic Source Insulators | MF-S2-04-C4 | Ceramic Source Insulator Production Line |
| C4-136 | Isotope Reference Sensor Dies | MF-S2-04-C4 | Isotope Reference Sensor Die Production Line |
| C4-137 | Source Loaded Shielding Tiles | MF-S2-04-C4 | Source Loaded Shielding Tile Production Line |
| C4-138 | Alloy Source Plates | MF-S2-04-C4 | Alloy Source Plate Production Line |
| C4-139 | Enriched Oxide Fuel | MF-S2-04-C4 | Enriched Oxide Fuel Production Line |
| C4-140 | Dual Source Ceramic Cells | MF-S2-04-C4 | Dual Source Ceramic Cell Production Line |
| C4-141 | Radioactive Panel Standards | MF-S2-04-C4 | Radioactive Panel Standard Production Line |
| C4-142 | Radiolabeled Plating Salts | MF-S2-04-C4 | Radiolabeled Plating Salt Production Line |
| C4-143 | Tagged Catalytic Mesh | MF-S2-04-C4 | Tagged Catalytic Mesh Production Line |
| C4-144 | Dual Isotope Tracer Capsules | MF-S2-04-C4 | Dual Isotope Tracer Capsule Production Line |
| C4-145 | Ceramic Wear Tracer Inserts | MF-S2-04-C4 | Ceramic Wear Tracer Insert Production Line |
| C4-146 | Isotope Reference Transistors | MF-S2-04-C4 | Isotope Reference Transistor Production Line |
| C4-147 | Shielded Irradiation Containers | MF-S2-04-C4 | Shielded Irradiation Container Production Line |
| C4-148 | Gear Wear Tracers | MF-S2-04-C4 | Gear Wear Tracer Production Line |
| C4-149 | Enriched Fuel Rods | MF-S2-04-C4 | Enriched Fuel Rod Production Line |
| C4-150 | Dual Source Nuclear Batteries | MF-S2-04-C4 | Dual Source Nuclear Battery Production Line |
| C4-151 | Multi Isotope Polymer Standards | MF-S2-04-C4 | Multi Isotope Polymer Standard Production Line |
| C4-152 | Multi Isotope Reagent Sets | MF-S2-04-C4 | Multi Isotope Reagent Set Production Line |
| C4-153 | Multi Isotope Catalyst Standards | MF-S2-04-C4 | Multi Isotope Catalyst Standard Production Line |
| C4-154 | Combined Isotope Therapy Doses | MF-S2-04-C4 | Combined Isotope Therapy Dose Production Line |
| C4-155 | Multi Isotope Ceramic Sources | MF-S2-04-C4 | Multi Isotope Ceramic Source Production Line |
| C4-156 | Calibrated Isotope Detector Dies | MF-S2-04-C4 | Calibrated Isotope Detector Die Production Line |
| C4-157 | Multi Isotope Source Capsules | MF-S2-04-C4 | Multi Isotope Source Capsule Production Line |
| C4-158 | Multi Isotope Alloy Sources | MF-S2-04-C4 | Multi Isotope Alloy Source Production Line |
| C4-159 | Blended Isotope Reactor Fuel | MF-S2-04-C4 | Blended Isotope Reactor Fuel Production Line |
| C4-160 | Multi Source Isotope Power Modules | MF-S2-04-C4 | Multi Source Isotope Power Module Production Line |

### T2 C4 installations from two C2 materials

| Recipe ID | Product name | Family ID | Installation name |
|---|---|---|---|
| C4-161 | Polymer Laminates | MF-S2-05-C4 | Polymer Laminate Production Line |
| C4-162 | Adhesive Sealants | MF-S2-05-C4 | Adhesive Sealant Production Line |
| C4-163 | Catalytic Membranes | MF-S2-07-C4 | Catalytic Membrane Production Line |
| C4-164 | Tracer Patches | MF-S2-08-C4 | Tracer Patche Production Line |
| C4-165 | Ceramic Polymer Composites | MF-S2-09-C4 | Ceramic Polymer Composite Production Line |
| C4-166 | Flexible Circuit Sheets | MF-S2-10-C4 | Flexible Circuit Sheet Production Line |
| C4-167 | Shielding Blankets | MF-S2-11-C4 | Shielding Blanket Production Line |
| C4-168 | Composite Pressure Housings | MF-S2-12-C4 | Composite Pressure Housing Production Line |
| C4-169 | Polymer Bound Fuel Blocks | MF-S2-13-C4 | Polymer Bound Fuel Block Production Line |
| C4-170 | Flexible Isotope Battery Mats | MF-S2-14-C4 | Flexible Isotope Battery Mat Production Line |
| C4-171 | Laboratory Reagent Sets | MF-S2-06-C4 | Laboratory Reagent Set Production Line |
| C4-172 | Chemical Synthesis Catalysts | MF-S2-06-C4 | Chemical Synthesis Catalyst Production Line |
| C4-173 | Diagnostic Contrast Reagents | MF-S2-06-C4 | Diagnostic Contrast Reagent Production Line |
| C4-174 | Chemical Filter Monoliths | MF-S2-09-C4 | Chemical Filter Monolith Production Line |
| C4-175 | Chemical Sensor Chips | MF-S2-10-C4 | Chemical Sensor Chip Production Line |
| C4-176 | Shielding Grout | MF-S2-11-C4 | Shielding Grout Production Line |
| C4-177 | Passivated Alloy Plates | MF-S2-12-C4 | Passivated Alloy Plate Production Line |
| C4-178 | Fuel Conditioning Compounds | MF-S2-13-C4 | Fuel Conditioning Compound Production Line |
| C4-179 | Sealed Isotope Power Cartridges | MF-S2-14-C4 | Sealed Isotope Power Cartridge Production Line |
| C4-180 | Multistage Catalyst Charges | MF-S2-07-C4 | Multistage Catalyst Charge Production Line |
| C4-181 | Radiotracer Synthesis Cartridges | MF-S2-07-C4 | Radiotracer Synthesis Cartridge Production Line |
| C4-182 | Catalytic Ceramic Monoliths | MF-S2-07-C4 | Catalytic Ceramic Monolith Production Line |
| C4-183 | Gas Sensor Elements | MF-S2-10-C4 | Gas Sensor Element Production Line |
| C4-184 | Shielded Catalyst Cartridges | MF-S2-11-C4 | Shielded Catalyst Cartridge Production Line |
| C4-185 | Catalytic Alloy Screens | MF-S2-12-C4 | Catalytic Alloy Screen Production Line |
| C4-186 | Catalyst Bound Reactor Fuel | MF-S2-13-C4 | Catalyst Bound Reactor Fuel Production Line |
| C4-187 | Isotope Powered Catalyst Cartridges | MF-S2-14-C4 | Isotope Powered Catalyst Cartridge Production Line |
| C4-188 | Multi Tracer Diagnostic Sets | MF-S2-08-C4 | Multi Tracer Diagnostic Set Production Line |
| C4-189 | Ceramic Tracer Implants | MF-S2-08-C4 | Ceramic Tracer Implant Production Line |
| C4-190 | Radiotracer Sensor Chips | MF-S2-08-C4 | Radiotracer Sensor Chip Production Line |
| C4-191 | Shielded Medical Isotope Packs | MF-S2-08-C4 | Shielded Medical Isotope Pack Production Line |
| C4-192 | Radiotherapy Applicators | MF-S2-12-C4 | Radiotherapy Applicator Production Line |
| C4-193 | Medical Isotope Target Fuel | MF-S2-13-C4 | Medical Isotope Target Fuel Production Line |
| C4-194 | Isotope Heated Tracer Packs | MF-S2-14-C4 | Isotope Heated Tracer Pack Production Line |
| C4-195 | Ceramic Tool Blanks | MF-S2-09-C4 | Ceramic Tool Blank Production Line |
| C4-196 | Ceramic Circuit Substrates | MF-S2-09-C4 | Ceramic Circuit Substrate Production Line |
| C4-197 | Shielding Bricks | MF-S2-09-C4 | Shielding Brick Production Line |
| C4-198 | Ceramic Armor Panels | MF-S2-09-C4 | Ceramic Armor Panel Production Line |
| C4-199 | Reactor Fuel Tiles | MF-S2-13-C4 | Reactor Fuel Tile Production Line |
| C4-200 | Ceramic Isotope Generators | MF-S2-14-C4 | Ceramic Isotope Generator Production Line |
| C4-201 | Integrated Circuit Arrays | MF-S2-10-C4 | Integrated Circuit Array Production Line |
| C4-202 | Shielded Sensor Arrays | MF-S2-10-C4 | Shielded Sensor Array Production Line |
| C4-203 | Industrial Control Boards | MF-S2-10-C4 | Industrial Control Board Production Line |
| C4-204 | Instrumented Fuel Elements | MF-S2-10-C4 | Instrumented Fuel Element Production Line |
| C4-205 | Autonomous Sensor Nodes | MF-S2-14-C4 | Autonomous Sensor Node Production Line |
| C4-206 | Shielding Vault Blocks | MF-S2-11-C4 | Shielding Vault Block Production Line |
| C4-207 | Reactor Shield Assemblies | MF-S2-11-C4 | Reactor Shield Assembly Production Line |
| C4-208 | Shielded Fuel Cartridges | MF-S2-11-C4 | Shielded Fuel Cartridge Production Line |
| C4-209 | Shielded Power Modules | MF-S2-11-C4 | Shielded Power Module Production Line |
| C4-210 | Heavy Structural Frames | MF-S2-12-C4 | Heavy Structural Frame Production Line |
| C4-211 | Reactor Core Cassettes | MF-S2-12-C4 | Reactor Core Cassette Production Line |
| C4-212 | Structural Power Modules | MF-S2-12-C4 | Structural Power Module Production Line |
| C4-213 | Reactor Fuel Assemblies | MF-S2-13-C4 | Reactor Fuel Assembly Production Line |
| C4-214 | Heated Fuel Cartridges | MF-S2-13-C4 | Heated Fuel Cartridge Production Line |
| C4-215 | Isotope Power Banks | MF-S2-14-C4 | Isotope Power Bank Production Line |

## Catalog coverage

| Tier and route | Complete catalog | Starting catalog | Uninvented |
|---|---|---|---|
| T0 raw resources | 4 | 4 | 0 |
| T1 C1 | 4 | 4 | 0 |
| T1 C2 | 10 | 10 | 0 |
| T2 C3 from C1 and C2 | 40 | 36 | 4 |
| T2 C4 from C1 and C3 | 160 | 14 | 146 |
| T2 C4 from two C2 materials | 55 | 55 | 0 |
| Refined and manufactured products | 269 | 119 | 150 |
| Including raw resources | 273 | 123 | 150 |

### T2 sector coverage

| Sector ID | Sector name | C3 | C4 | Total | Starting | Uninvented |
|---|---|---|---|---|---|---|
| S2-01 | Biochemical Products | 0 | 40 | 40 | 4 | 36 |
| S2-02 | Inorganic Products | 0 | 40 | 40 | 4 | 36 |
| S2-03 | Metal Products | 0 | 40 | 40 | 3 | 37 |
| S2-04 | Isotope Products | 0 | 40 | 40 | 3 | 37 |
| S2-05 | Polymer Goods | 4 | 2 | 6 | 6 | 0 |
| S2-06 | Specialty Chemicals | 4 | 3 | 7 | 6 | 1 |
| S2-07 | Catalytic Products | 4 | 4 | 8 | 8 | 0 |
| S2-08 | Medical Isotope Products | 4 | 5 | 9 | 9 | 0 |
| S2-09 | Ceramic Goods | 4 | 6 | 10 | 10 | 0 |
| S2-10 | Electronic Components | 4 | 7 | 11 | 10 | 1 |
| S2-11 | Radiation Protection | 4 | 7 | 11 | 11 | 0 |
| S2-12 | Alloy Components | 4 | 7 | 11 | 11 | 0 |
| S2-13 | Reactor Fuel Products | 4 | 7 | 11 | 10 | 1 |
| S2-14 | Isotope Power Systems | 4 | 7 | 11 | 10 | 1 |
| Total | 14 sectors | 40 | 215 | 255 | 105 | 150 |

## Completeness and source notes

The catalog covers four raw resources, twenty T0 names, fourteen material names, fourteen T1 sector names, fourteen T1 generic stems, fourteen T2 sector names, fourteen T2 facility stems, four equipment classes, four extraction-equipment types, 42 machine families, and 269 recipe-linked installation names. The 42 families comprise fourteen T1 and 28 T2 families.

All 273 goods names, including raw resources, are unique; all 269 installation names are unique. Stable IDs, recipes, ingredient quantities, output quantities, complexity, sector membership, and starting selection are preserved. The Markdown tables and JSON companion carry the same names and identifiers.

**The Oligarch** at `0xc` and **United Radioactives Company** at `0x14` are the two T0 names without Inc., Incorporated, Corp., or Corporation endings. Their approved wording is retained exactly.

The existing runtime still uses the old naming catalog. In particular, its current T1 and T2 flagship displays differ from the stem-only convention specified here. This remains a documented future naming change, not an implemented one. No supplier companies, production recipes, company populations, duties, or economic parameters are added or changed.

### Runtime data and companion JSON

- [Structural catalog](../catalogs/midbridge-4259-recursive/catalog.json) and [starting selection](../catalogs/midbridge-4259-recursive/starting-selection.json): the current recipe identities, quantities, sectors, and invention status.
- [Current runtime naming data](../catalogs/midbridge-4259-recursive/naming.json): names still loaded by the application while implementation is pending.
- [Complete naming JSON](midbridge_complete_naming_catalog.json): all approved names, stable identities, unchanged formulas, quantities, and machinery mappings. Its metadata records the retained runtime source-file hashes.
- [Naming integration](naming-integration.md): current runtime dependencies and the boundary between the approved catalog and its future implementation.
