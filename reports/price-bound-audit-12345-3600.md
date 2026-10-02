# Price-bound audit: 3,600 ticks

Fresh default configuration, seed 12345. Canonical worker with 20 T0 firms, 1,000 T1 firms, 50,000 T2 firms and 1,000,000 consumers. Actual transactions measured over ticks 3,241–3,600. All 134 markets traded. Runtime: 411.3 seconds.

| Market group | Markets | Units at floor | Units at ceiling | Units within 1% of floor |
|---|---:|---:|---:|---:|
| T0 raw materials | 4 | 0.00% | No ceiling | 0.00% |
| T1 retail basics | 4 | 0.00% | 0.00% | 0.00% |
| T1 intermediates | 6 | 99.99% | 100.00% | 100.00% |
| T2 finished goods | 120 | 48.82% | 0.00% | 99.93% |

Percentages are shares of units sold, not shares of posted offers or averages of market percentages. Floor and ceiling shares overlap when the permitted price range collapses.

## Findings

- Every C-2 intermediate market traded at both bounds in every measured tick. Clay, Steam, Lava, Dust and Smoke sold 100% of units at the coincident bounds. Mist sold 99.9316% at its floor and 99.9940% at its ceiling; all Mist trades were within 1% of the floor.
- All 120 T2 product markets had floor trades. 115 had floor trades on every measured tick. Their combined exact-floor share was 48.8177%, with 99.9309% of units within 1% of the floor. No T2 trades occurred at a ceiling.
- T2 floor trades varied by market: Phoenix Balm 76.4477%, Surveying Compass 75.7350%, Spirit Mirror 73.6361%. A market containing floor trades does not imply that every seller or its weighted average price is exactly at the floor.
- T0 and C-1 retail basics had neither exact-bound trades nor trades within 1% of their floors.

## Model causes

1. `engine/model.js:206–210` applies the same `2 * vmax` ceiling to every T1 product. Default `vmax=1.5` means $3. The effective ceiling is `max(cost * 1.08, 3)`. When an intermediate costs more than $2.7778, the floor exceeds $3 and the allowed price range collapses. Its price then follows cost regardless of inventory or demand. T2 uses product-scaled ceilings, so this specific collapse is concentrated in T1 intermediates.
2. The same pricing function uses `stock / salesEMA` against three ticks of coverage. Production targets `ceil(3 * salesEMA)`, plus a bootstrap minimum. When a firm replenishes to its target without capacity binding, rounding means its pre-sale coverage is at least three ticks, often higher. That creates repeated downward pressure even with steady sales, with no normal-margin restoring term. A numerical reproduction at sales EMA 1.2 yields stock target 4, coverage 3.3333, and a price reduction. The long run shows widespread T2 floor concentration consistent with this mechanism.

These observations identify defects in price formation and its coupling to inventory targeting. They do not independently establish that consumer reservation prices, activation probabilities or elasticity require a particular recalibration.

## Reproduce

```sh
node tests/price_bound_audit.js
```

Full per-market results: [JSON report](price-bound-audit-12345-3600.json). The audit observes the canonical worker and separates T0 trades before and after repricing. It does not change the economic rules.

## All markets

| Tier | Market | Average traded price | Units sold | Floor share | Ceiling share | Within 1% of floor | Ticks with floor trades |
|---|---|---:|---:|---:|---:|---:|---:|
| T0 | Water | $1.2840 | 25,294,830 | 0.00% | No ceiling | 0.00% | 0/360 |
| T0 | Earth | $1.2794 | 24,100,570 | 0.00% | No ceiling | 0.00% | 0/360 |
| T0 | Fire | $1.2767 | 17,399,610 | 0.00% | No ceiling | 0.00% | 0/360 |
| T0 | Air | $1.2771 | 19,192,690 | 0.00% | No ceiling | 0.00% | 0/360 |
| T1 | Water | $2.6315 | 2,599,351 | 0.00% | 0.00% | 0.00% | 0/360 |
| T1 | Earth | $2.6310 | 2,606,748 | 0.00% | 0.00% | 0.00% | 0/360 |
| T1 | Fire | $2.6302 | 2,602,503 | 0.00% | 0.00% | 0.00% | 0/360 |
| T1 | Air | $2.6320 | 2,596,069 | 0.00% | 0.00% | 0.00% | 0/360 |
| T1 | Clay | $3.0402 | 7,160,040 | 100.00% | 100.00% | 100.00% | 360/360 |
| T1 | Steam | $3.0367 | 4,030,832 | 100.00% | 100.00% | 100.00% | 360/360 |
| T1 | Mist | $3.0454 | 4,794,959 | 99.93% | 99.99% | 100.00% | 360/360 |
| T1 | Lava | $3.0307 | 4,506,059 | 100.00% | 100.00% | 100.00% | 360/360 |
| T1 | Dust | $3.0391 | 3,930,639 | 100.00% | 100.00% | 100.00% | 360/360 |
| T1 | Smoke | $3.0360 | 3,281,046 | 100.00% | 100.00% | 100.00% | 360/360 |
| T2 | Glazed Pot | $6.2858 | 447,749 | 50.99% | 0.00% | 100.00% | 360/360 |
| T2 | Water Jug | $6.2911 | 430,750 | 40.29% | 0.00% | 100.00% | 360/360 |
| T2 | Steam Cooker | $6.2842 | 410,869 | 57.12% | 0.00% | 100.00% | 360/360 |
| T2 | Smoke Hood | $6.2815 | 344,971 | 62.23% | 0.00% | 100.00% | 360/360 |
| T2 | Ceramic Basin | $6.2586 | 378,047 | 53.00% | 0.00% | 100.00% | 360/360 |
| T2 | Cooling Vessel | $6.2932 | 346,590 | 57.90% | 0.00% | 100.00% | 360/360 |
| T2 | Ceramic Stove | $8.7193 | 112,933 | 58.55% | 0.00% | 100.00% | 360/360 |
| T2 | Condensing Cabinet | $8.7316 | 99,969 | 57.98% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Decanter | $8.7336 | 94,423 | 63.21% | 0.00% | 100.00% | 360/360 |
| T2 | Purifying Filter | $8.7272 | 120,323 | 57.02% | 0.00% | 100.00% | 360/360 |
| T2 | Self-Warming Hearth | $10.6414 | 30,209 | 44.42% | 0.00% | 100.00% | 360/360 |
| T2 | Living Glass Cabinet | $10.6490 | 25,809 | 35.19% | 0.00% | 100.00% | 360/360 |
| T2 | Fired Brick | $6.2857 | 409,551 | 52.04% | 0.00% | 100.00% | 360/360 |
| T2 | Stone Cement | $6.2843 | 377,055 | 58.21% | 0.00% | 100.00% | 360/360 |
| T2 | Insulated Tile | $6.2474 | 335,697 | 58.43% | 0.00% | 100.00% | 360/360 |
| T2 | Clay Pipe | $6.2609 | 352,432 | 35.56% | 0.00% | 100.00% | 360/360 |
| T2 | Foundation Block | $6.2765 | 364,050 | 57.92% | 0.00% | 100.00% | 360/360 |
| T2 | Weather Sealant | $6.2822 | 291,478 | 55.12% | 0.00% | 100.00% | 360/360 |
| T2 | Glazed Roof Tile | $8.7186 | 100,447 | 54.95% | 0.00% | 100.00% | 360/360 |
| T2 | Cloud Insulation | $8.7335 | 90,648 | 69.29% | 0.00% | 100.00% | 360/360 |
| T2 | Smoke Vent | $8.7201 | 85,468 | 68.87% | 0.00% | 100.00% | 360/360 |
| T2 | Reinforced Ceramic Panel | $8.7312 | 95,630 | 55.60% | 0.00% | 100.00% | 360/360 |
| T2 | Weatherproof Arch | $10.6503 | 25,439 | 42.73% | 0.00% | 100.00% | 360/360 |
| T2 | Floating Keystone | $10.6582 | 22,028 | 54.06% | 0.00% | 100.00% | 360/360 |
| T2 | Glass Shard | $6.2469 | 347,623 | 50.48% | 0.00% | 100.00% | 360/360 |
| T2 | Ceramic Vase | $6.2857 | 303,664 | 52.98% | 0.00% | 100.00% | 360/360 |
| T2 | Porcelain Bead | $6.2884 | 276,079 | 54.56% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Seed | $6.2931 | 277,047 | 47.33% | 0.00% | 100.00% | 360/360 |
| T2 | Glass Bottle | $6.2760 | 361,423 | 48.43% | 0.00% | 100.00% | 360/360 |
| T2 | Glazed Dish | $6.2902 | 333,143 | 42.19% | 0.00% | 100.00% | 360/360 |
| T2 | Stained Glass | $8.7175 | 80,864 | 61.35% | 0.00% | 100.00% | 360/360 |
| T2 | Porcelain Vessel | $8.7237 | 91,087 | 45.90% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Prism | $8.7263 | 76,460 | 65.79% | 0.00% | 100.00% | 360/360 |
| T2 | Smoke Glass | $8.7124 | 80,808 | 70.60% | 0.00% | 100.00% | 360/360 |
| T2 | Rainbow Crystal | $10.6174 | 20,920 | 58.16% | 0.00% | 100.00% | 360/360 |
| T2 | Phoenix Porcelain | $10.6486 | 22,906 | 49.21% | 0.00% | 100.00% | 360/360 |
| T2 | Red Pigment | $6.2770 | 344,784 | 50.67% | 0.00% | 100.00% | 360/360 |
| T2 | Soot Dye | $6.2852 | 330,830 | 44.94% | 0.00% | 100.00% | 360/360 |
| T2 | Mineral Thread | $6.2572 | 373,864 | 40.00% | 0.00% | 100.00% | 360/360 |
| T2 | Cloud Felt | $6.2938 | 346,058 | 11.53% | 0.00% | 98.20% | 360/360 |
| T2 | Clay Mordant | $6.2944 | 315,032 | 38.64% | 0.00% | 99.99% | 360/360 |
| T2 | Steam-Set Cloth | $6.2710 | 302,687 | 7.98% | 0.00% | 99.91% | 288/360 |
| T2 | Silken Cloud Cloth | $8.7430 | 90,282 | 61.36% | 0.00% | 99.99% | 360/360 |
| T2 | Enamel Pigment | $8.7195 | 83,854 | 54.96% | 0.00% | 100.00% | 360/360 |
| T2 | Luminous Dye | $8.7194 | 79,537 | 51.37% | 0.00% | 100.00% | 360/360 |
| T2 | Weatherproof Fabric | $8.7346 | 94,970 | 67.21% | 0.00% | 100.00% | 360/360 |
| T2 | Enchanted Tapestry | $10.6651 | 21,629 | 46.05% | 0.00% | 100.00% | 360/360 |
| T2 | Aurora Silk | $10.6264 | 23,324 | 67.25% | 0.00% | 100.00% | 360/360 |
| T2 | Mineral Elixir | $6.2870 | 341,151 | 47.85% | 0.00% | 100.00% | 360/360 |
| T2 | Calming Vapor | $6.2910 | 311,889 | 57.60% | 0.00% | 100.00% | 360/360 |
| T2 | Distilled Essence | $6.2870 | 353,043 | 42.21% | 0.00% | 99.99% | 360/360 |
| T2 | Binding Resin | $6.2854 | 282,491 | 52.62% | 0.00% | 100.00% | 360/360 |
| T2 | Smoke Catalyst | $6.2826 | 295,809 | 52.07% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Reagent | $6.2943 | 313,909 | 53.66% | 0.00% | 100.00% | 360/360 |
| T2 | Restorative Potion | $8.7272 | 93,258 | 50.53% | 0.00% | 100.00% | 360/360 |
| T2 | Clarity Draught | $8.7352 | 82,173 | 67.01% | 0.00% | 100.00% | 360/360 |
| T2 | Phoenix Balm | $8.7179 | 77,207 | 76.45% | 0.00% | 100.00% | 360/360 |
| T2 | Transmutation Solvent | $8.7253 | 88,568 | 68.28% | 0.00% | 100.00% | 360/360 |
| T2 | Royal Elixir | $10.6252 | 23,147 | 32.37% | 0.00% | 100.00% | 352/360 |
| T2 | Philosopher Tonic | $10.6505 | 21,320 | 50.29% | 0.00% | 100.00% | 360/360 |
| T2 | Chisel | $6.2778 | 327,233 | 56.99% | 0.00% | 100.00% | 360/360 |
| T2 | Steam Valve | $6.2566 | 341,908 | 48.83% | 0.00% | 100.00% | 360/360 |
| T2 | Potter Wheel | $6.2884 | 300,159 | 49.38% | 0.00% | 100.00% | 360/360 |
| T2 | Grinding Disc | $6.2862 | 313,996 | 53.59% | 0.00% | 100.00% | 360/360 |
| T2 | Ceramic Bearing | $6.2854 | 326,454 | 51.29% | 0.00% | 100.00% | 360/360 |
| T2 | Bellows Assembly | $6.2619 | 271,729 | 21.80% | 0.00% | 100.00% | 326/360 |
| T2 | Steam Turbine | $8.7141 | 84,464 | 54.87% | 0.00% | 100.00% | 360/360 |
| T2 | Clockwork Gear | $8.7181 | 94,546 | 58.87% | 0.00% | 100.00% | 360/360 |
| T2 | Pressure Gauge | $8.7257 | 89,721 | 55.43% | 0.00% | 100.00% | 360/360 |
| T2 | Hydraulic Press | $8.7267 | 79,381 | 55.65% | 0.00% | 100.00% | 360/360 |
| T2 | Aether Engine | $10.6400 | 23,747 | 42.48% | 0.00% | 100.00% | 360/360 |
| T2 | Alchemist Automaton | $10.6499 | 20,666 | 50.27% | 0.00% | 100.00% | 360/360 |
| T2 | Oil Lamp | $6.2867 | 314,237 | 44.56% | 0.00% | 100.00% | 360/360 |
| T2 | Wind Flute | $6.2866 | 263,580 | 5.49% | 0.00% | 96.33% | 345/360 |
| T2 | Glass Lens | $6.2526 | 287,222 | 22.76% | 0.00% | 100.00% | 314/360 |
| T2 | Signal Lantern | $6.2802 | 275,698 | 57.41% | 0.00% | 100.00% | 360/360 |
| T2 | Steam Whistle | $6.2538 | 252,991 | 52.75% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Dial | $6.2944 | 239,430 | 52.22% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Lantern | $8.7248 | 79,401 | 69.84% | 0.00% | 100.00% | 360/360 |
| T2 | Resonant Chime | $8.7252 | 66,120 | 50.46% | 0.00% | 100.00% | 360/360 |
| T2 | Optical Instrument | $8.7244 | 74,404 | 66.57% | 0.00% | 100.00% | 360/360 |
| T2 | Surveying Compass | $8.7174 | 69,792 | 75.74% | 0.00% | 100.00% | 360/360 |
| T2 | Storm Organ | $10.6558 | 17,983 | 57.56% | 0.00% | 100.00% | 360/360 |
| T2 | Phoenix Lantern | $10.6443 | 21,308 | 59.86% | 0.00% | 100.00% | 360/360 |
| T2 | Crystal Pendant | $6.2943 | 263,618 | 53.07% | 0.00% | 100.00% | 360/360 |
| T2 | Ember Ring | $6.2742 | 250,242 | 62.72% | 0.00% | 100.00% | 360/360 |
| T2 | Incense Censer | $6.2822 | 227,915 | 60.96% | 0.00% | 100.00% | 360/360 |
| T2 | Rune Tablet | $6.2850 | 275,713 | 53.63% | 0.00% | 100.00% | 360/360 |
| T2 | Aether Token | $6.2575 | 230,428 | 56.21% | 0.00% | 100.00% | 360/360 |
| T2 | Moon Glass | $6.2980 | 240,438 | 40.82% | 0.00% | 99.99% | 360/360 |
| T2 | Moonstone Ornament | $8.7357 | 71,246 | 60.41% | 0.00% | 100.00% | 360/360 |
| T2 | Arcane Seal | $8.7135 | 65,956 | 67.65% | 0.00% | 100.00% | 360/360 |
| T2 | Spirit Mirror | $8.7300 | 62,578 | 73.64% | 0.00% | 100.00% | 360/360 |
| T2 | Runic Reliquary | $8.7276 | 74,588 | 57.88% | 0.00% | 100.00% | 360/360 |
| T2 | Philosopher Vessel | $10.6470 | 18,627 | 37.79% | 0.00% | 100.00% | 360/360 |
| T2 | Astral Crown | $10.6478 | 17,331 | 56.68% | 0.00% | 100.00% | 360/360 |
| T2 | Seedling Pot | $6.2941 | 386,613 | 38.19% | 0.00% | 100.00% | 360/360 |
| T2 | Mineral Fertilizer | $6.2916 | 414,270 | 33.79% | 0.00% | 100.00% | 360/360 |
| T2 | Irrigation Nozzle | $6.2834 | 371,053 | 50.30% | 0.00% | 100.00% | 360/360 |
| T2 | Clay Mulch | $6.2883 | 354,944 | 53.42% | 0.00% | 99.99% | 360/360 |
| T2 | Mist Irrigator | $6.2934 | 382,482 | 48.75% | 0.00% | 100.00% | 360/360 |
| T2 | Smoke Repellent | $6.2837 | 325,998 | 47.93% | 0.00% | 100.00% | 360/360 |
| T2 | Greenhouse Pane | $8.7252 | 102,929 | 65.37% | 0.00% | 100.00% | 360/360 |
| T2 | Soil Conditioner | $8.7265 | 108,011 | 53.13% | 0.00% | 100.00% | 360/360 |
| T2 | Steam Cultivator | $8.7157 | 92,321 | 61.03% | 0.00% | 100.00% | 360/360 |
| T2 | Reservoir Liner | $8.7354 | 97,790 | 58.30% | 0.00% | 100.00% | 360/360 |
| T2 | Evergreen Terrarium | $10.6634 | 25,883 | 47.85% | 0.00% | 100.00% | 360/360 |
| T2 | Raincalling Sprinkler | $10.6625 | 24,078 | 28.95% | 0.00% | 100.00% | 360/360 |
| T2 | Healing Tonic | $6.2884 | 397,910 | 43.35% | 0.00% | 100.00% | 360/360 |
| T2 | Purifying Salve | $6.2947 | 382,290 | 38.66% | 0.00% | 99.99% | 360/360 |
| T2 | Sterile Dressing | $6.2577 | 368,951 | 37.67% | 0.00% | 100.00% | 360/360 |
| T2 | Mineral Compress | $6.2925 | 354,055 | 42.91% | 0.00% | 100.00% | 360/360 |
| T2 | Cooling Poultice | $6.2936 | 353,724 | 47.09% | 0.00% | 100.00% | 360/360 |
| T2 | Warming Liniment | $6.2838 | 324,168 | 47.73% | 0.00% | 100.00% | 360/360 |
| T2 | Healing Unguent | $8.7259 | 107,708 | 50.93% | 0.00% | 100.00% | 360/360 |
| T2 | Breathing Inhaler | $8.7310 | 102,298 | 54.41% | 0.00% | 100.00% | 360/360 |
| T2 | Sterilizing Apparatus | $8.7167 | 91,841 | 65.55% | 0.00% | 100.00% | 360/360 |
| T2 | Restorative Bath | $8.7361 | 96,972 | 58.47% | 0.00% | 100.00% | 360/360 |
| T2 | Regenerative Elixir | $10.6576 | 27,898 | 48.03% | 0.00% | 100.00% | 360/360 |
| T2 | Vitality Infuser | $10.6558 | 25,761 | 52.59% | 0.00% | 100.00% | 360/360 |
