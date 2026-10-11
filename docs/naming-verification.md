# Approved naming implementation: review evidence

Implemented in the isolated `midbridge-approved-naming` branch, based on
`new-recipes` commit `f2b9b470fcf427a86915a721802f9505350e915d`.
Worktree: `/Users/csys/.codex/worktrees/midbridge-approved-naming/ibicot`.
The existing `dev` branch prevents Git from creating a `dev/…` branch.
The original verification below preceded integration. On 12 October 2026 the
user authorized reconciliation into `new-recipes`; the implementation is now in
that branch's working tree, uncommitted alongside the pre-existing work.

## Sources and isolation

The two approved sources were copied byte-for-byte from the shared checkout:

| Source | SHA-256 |
| --- | --- |
| `midbridge_complete_naming_catalog.md` | `a716b867787c746ecd08ee165c29049561eb86f810542ec1416605677d0f7a64` |
| `midbridge_complete_naming_catalog.json` | `92e00490a45a8a6f28ef6710791f48e94fc6456509323994e7ece19fec3178bf` |

No shared uncommitted changes, research files, recordings or checkpoints were
copied or modified. Dependencies were read from the shared `.pydeps`; Python
checks used `PYTHONDONTWRITEBYTECODE=1`. Numba cache, snapshots and test outputs
were confined to this worktree or temporary test directories. No active campaign
was operated. No heavy benchmark was run.

## Verification

- Five naming tests cover all 269 products/installations, all 1,008 T1 and 57,960
  T2 company names, raw slot coverage, equipment/families, excluded metadata,
  generator rejection of changed recipes/coverage/invention, and browser parity.
- `test_naming_catalog`, `test_company_numbers`, `test_midbridge`: 12 tests pass,
  including recipe/storage contracts, checkpoint identity and reference/compiled
  production parity.
- `test_review_fixes`: 27 tests pass, including reference/compiled paths,
  controls, multi-line ownership, accounting and checkpoint restoration.
- `test_kernel.py`: determinism (35 ticks) and conservation/invariants (30 ticks)
  pass. Its old first-company name expectation was updated; the naming function
  then passed independently. These are small test worlds, not population benchmarks.
- `node --check web/app.js`, formatting and profitability JavaScript tests pass.
- Naming and browser generators reproduce their outputs byte-for-byte;
  `git diff --check` passes.

A separate comparison executed the original committed adapter with original
catalog/naming files saved under `.naming-review/adapter-before`, then compared
all PRODUCT, T2 catalog and input-market records with the new adapter. Every
field other than display labels matched, with raw input names normalized to
slot indices. Structural catalog, starting selection, configuration, persistence
implementation and numeric kernels have no changes.

### Independent state baseline

Before edits, `.naming-review/capture.py` captured seed 137 with 200 manufacturers,
100 Distributors, default other settings, and ticks 0–3 through the explicit
reference path (`NB._HAVE_NUMBA=False`). Before/after snapshots retain **168
arrays**, all identical in dtype, shape and bytes at both endpoints. Configuration,
accounting scalars and other checkpoint JSON also match exactly. The old snapshot
loads and saves with identical arrays and metadata after removing the loader's
transient `runtimeMetadata` wrapper from the supplied scalar dictionary.

Evidence and scripts remain locally in the ignored `.naming-review/` directory:
`before[-initial].{npz,json}`, `after[-initial].{npz,json}`, `loaded.{npz,json}`,
`capture.py`, `compare.py`. To repeat the saved comparisons:

```sh
PYTHONPATH=/Users/csys/Desktop/ibicot/.pydeps:. PYTHONDONTWRITEBYTECODE=1 \
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 .naming-review/compare.py
```

The initial attempt to execute undecorated compiled loops with
`NUMBA_DISABLE_JIT=1` hit a pre-existing uint8 overflow before renaming. The
successful baseline used the reference path instead. Installed SciPy emits a
NumPy compatibility warning; it did not prevent the actual Numba parity tests.
This bounded validation does not claim long-run economic stability or performance.

### Rendered browser

Served the worktree on `127.0.0.1:8137` with 200 manufacturers and 100 Distributors,
paused at tick zero. The browser loaded the generated metadata and connected to
this isolated backend. Verified live extractor resource labels, refinery
installations, complete naming catalog, and searchable first-company names
`Biochemical Plant 0x15` and `Biochemical processing facility 0x405`. No flagship
columns or JavaScript errors appeared. Narrow-screen tables remain horizontally
scrollable. Screenshot: `.naming-review/catalog-ui.png`.

The temporary browser tab and isolated service are closed after verification.

## Reconciliation on 12 October 2026

Integrated the verified naming implementation into `/Users/csys/Desktop/ibicot`
on `new-recipes`. Preserved the current README research findings, removed legacy
exports and tools, in-memory structural generator, approved sources and all
research files. The naming generator is now `tools/build_naming_metadata.py`;
its tests and documentation use that path. No process was restarted or stopped,
and no recording, checkpoint or live configuration was operated. Existing
processes retain their loaded names until their next normal restart.

The original isolated worktree and its verification artifacts remain available.
Reconciliation evidence and pre-edit backups are stored there under
`.naming-review/reconciliation-2026-10-12/`.

Reconciliation checks passed: eight naming/company-number tests, JavaScript
syntax/formatting/profitability checks, in-memory structural validation, exact
generator reproducibility, and the saved 168-array/checkpoint comparison using
the integrated backend. Runtime code and rendered assets match the previously
reviewed isolated version byte-for-byte. Hash checks confirmed all 134 other
tracked/untracked paths (including deleted paths) remained unchanged. Existing
research prose in the overlapping README was retained. No new UI behavior was
introduced during reconciliation, so the earlier rendered verification applies.
