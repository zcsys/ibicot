# Midbridge Colony: names only

The accepted names come from `docs/Midbridge_Colony_Naming_Catalog.md`, Appendix B. The user's restriction is authoritative: **apply names only**. The document is not a source of new game rules, fiction, company roles or entities.

`tools/apply_naming_catalog.py` verifies all 269 recipe IDs, formulas, input quantities, complexities, sector assignments and preferred materials against the existing structural generator. It writes the named catalog and `named-products.csv` under `catalogs/midbridge-4259-recursive/`. An explicit allowlist produces `naming.json`: only names, display symbols and the identifiers/structural facts needed to bind them to existing entities survive. `tools/build_midbridge_web.py` generates browser metadata from the same Python adapter. Run those two commands in that order. The original delivered document remains unmodified as source material.

## Applied mappings

- All 269 products and recipe-specific installations, fourteen material symbols, fourteen refinery sectors, fourteen application sectors, equipment classes, families and existing extraction-equipment types receive the supplied names.
- All twenty T0 companies are renamed in their existing roster positions. Resource coverage and auxiliary roles stay attached to the same companies. The existing machinery supplier, T0 local ID 6, becomes Claywell & Sons; it retains its machinery role.
- The first existing company in each T1 cohort and T2 sector uses the supplied flagship name. Others use the sector's generic stem. These are display-name assignments, not new company roles, privileges or populations.
- Global hex company numbers remain unchanged, starting with Gaia `0x0`. The document's per-stem suffix examples do not override global numbering.
- The game title is Midbridge Colony. Distributors retain their established role and name.

## Explicitly excluded

The Common Reserve Program, replacement tagline/setting prose, new material interpretations and product-use descriptions, extraction-only company roles, and four additional independent equipment makers are not imported into the game. The existing company duties remain intact. The source's rule section is not used to configure the economy.

## Compatibility and performance

Recipes, market indices, populations, production, prices, costs, storage, rent, demand calibration and company numbering are unchanged by this naming pass. Existing checkpoints retain their structural catalog revision; current names are resolved when snapshots are published. A running backend must reload code to publish the new roster; browser refresh alone cannot update backend metadata.

Names are startup metadata. The full browser reference renders once on expansion, not per tick. No strings are added to numeric simulation kernels or million-entry Distributor arrays. Tests check complete name coverage, machinery-family bindings, browser/Python parity, absence of excluded metadata and preservation of economic fields and company identity.
