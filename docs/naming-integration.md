# Midbridge Colony naming integration

The [complete naming catalog](midbridge_complete_naming_catalog.md) and its
[JSON companion](midbridge_complete_naming_catalog.json) are the approved naming
sources. Their original delivery status says “not implemented”; the copies are
preserved unchanged as approval evidence. This document records implementation.

## Display contract

- Raw slots remain W, E, F, A, in that order: Organics, Inorganics, Metals,
  Radioactives. These are distinct from their C1 refined outputs.
- All 269 recipes (including 150 uninvented T2 products), installations, 42 machine
  families, four equipment classes, four extraction machines, fourteen refinery
  sectors and fourteen manufacturing sectors use their approved names.
- All twenty T0 firms retain their IDs and resource coverage. The machinery
  supplier remains local ID 6, global `0x7`: Standard Fiber & Mineral, Inc.
- Every T1 firm uses its sector's `generic_stem`; every T2 firm uses its sector's
  `facility_stem`, followed by its existing lowercase global hexadecimal number.
  The first company follows the same rule. There are no flagships.
- Gaia remains `Gaia 0x0`; T3 remains `Distributor <global hex number>`.

## Generation and runtime

Using the interpreter selected by `run.sh`:

```sh
python3 tools/build_naming_metadata.py
PYTHONPATH=.pydeps:. python3 tools/build_midbridge_web.py
```

The first command validates approved recipe IDs, formulas, ingredient quantities,
complexity, sector assignments, preferred materials, invention flags, machine
bindings and extractor coverage against the existing structure, then writes only
`catalogs/midbridge-4259-recursive/naming.json`. An allowlist excludes narrative,
new roles and economic settings. It does not regenerate structural catalogs,
calibration reports or historical exports.

`economy/core/midbridge.py` applies that metadata over the retained baseline
catalog. Raw display names, raw input keys and extractor coverage share the same
slot mapping. `economy/core/model.py` resolves company stems and global numbers.
The browser generator exports the adapted metadata, including `ELEMENTS`, to
`web/midbridge-catalog.js`; the dashboard's full reference uses one company-stem
column per tier. Names are resolved at startup, outside simulation loops.

`economy/core/catalog.json` and `web/catalog.js` retain template labels; they are
not current naming sources. Browser pages must load `midbridge-catalog.js` after
`catalog.js`. Superseded creative briefs and duplicate structural exports remain
removed. `tools/build_recursive_catalog.py` validates in memory without writing
runtime data; its `build` and `validate` functions remain available for calibration.
`starting-selection.json` and `consumption-calibration.json` remain unchanged.
The new naming generator replaces the deleted legacy `apply_naming_catalog.py`
workflow without restoring it or its duplicate exports.

## Compatibility and review

Stable recipe/equipment/family IDs, compact market indices, raw slot order,
company numbering, recipes, configuration, allocations and economic behavior are
unchanged. Checkpoint version 8 and catalog revision
`midbridge-invented-105-reverse-v7` remain unchanged. Old compatible checkpoints
resolve to the current display names when loaded by the updated backend. Existing
processes continue using their loaded metadata; this work does not restart them.

The reviewed implementation was reconciled into `new-recipes` on 12 October 2026,
preserving its existing research work and cleanup. See
[naming verification](naming-verification.md) for the baseline, checks and UI review.
