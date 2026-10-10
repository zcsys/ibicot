# Economy review fixes and validation

All 14 findings from the repository review have been addressed. The four P1 fixes passed their targeted regressions and the existing tests before work proceeded to P2. Machinery purchases now require enough existing storage for machinery plus goods; purchasing storage remains unavailable.

This change repairs execution, accounting, persistence, and control behavior. It preserves the calibration defaults. Changes to supplier selection, reliability, and storage can change the resulting economy even when parameter values stay the same. A successful simulation run establishes the tested invariants, not equal profitability or long-run equilibrium.

## Resolution of the 14 findings

| Finding | Resolution | Verification |
| --- | --- | --- |
| 1 P1 Zero quotes crash procurement | The numerical floor is one cent, the smallest positive quote compatible with whole-cent pricing. Player quote normalization clamps and rounds consistently. The catalog and canon agree. | Zero-price T1 override advances safely through both engines with a $0.01 quote and finite, nonnegative cash. |
| 2 P1 Supplier ranking disagrees with settlement | Ranking uses the adaptive fixed loyalty charge and actual order quantity. Procurement rechecks the decision after cash and stock caps. Retail partial fills must also justify the fixed fee. Stockouts waive the charge. | Shared Python/Numba selection tests plus separate raw, material, and retail purchase regressions, including cash-capped and partial challenger orders. |
| 3 P1 Browser initialization destroys the shared run | `init` attaches to the existing runtime. Server startup owns initial configuration; explicit Reset starts a new world. Snapshots provide configuration so browser controls reflect server values. | Repeated attachment preserves tick, running state, cash, configuration, world identity, and existing log contents. Two connected WebSockets also pass the attachment check. |
| 4 P1 Checkpoint load strands connected clients | Loading rebuilds the saved state before replacing the contents of the existing runtime object. HTTP state operations execute on the event loop, avoiding threadpool interleaving with ticks. Load pauses the runtime. | An existing client reference resumes the restored world. HTTP save/load with two connected WebSockets confirms that subsequent steps and HTTP snapshots agree. |
| 5 P2 Checkpoints lose administrative state | Version 2 saves ownership, licenses, house, accounting, online state, selections, and production snapshot metadata. Equipment, controllers, and player quotes reconstruct from authoritative arrays. Adaptive scalars and transient loyalty totals survive re-saving. Version 1 line arrays migrate to the expanded capacity. | Round-trip compares every world array and runtime metadata; duplicate equipment stays rejected. Legacy checkpoint loads and advances successfully. |
| 6 P2 Logged manufacturer equity excludes inventory | T2 log equity includes raw, intermediate, and finished inventories at their recorded book costs. | Controlled inventories increase logged equity by exactly $56, matching the dashboard snapshot. |
| 7 P2 JSON loyalty keys are ignored | Loyalty normalization accepts integer and JSON string keys at both nesting levels, preserves zero overrides, and does not mutate the input. | Explicit JSON overrides and a complete JSON configuration round-trip agree. |
| 8 P2 Market anchor control does nothing | `marketAnchorBand` is included in the dashboard configuration reader. | A Node test executes the actual `readCfg` function with a changed input and verifies the resulting value. |
| 9 P2 Manufacturer expansion cannot allocate a line | Line and learning arrays reserve up to four lines per configured firm, matching the firm limit. Existing eligibility, duplicate-product, cash, and limit checks remain. | An eligible player purchase creates a second line, debits cash, increases equipment book value, and survives the multiline engine parity test. |
| 10 P2 Procurement ignores machinery storage | Procurement subtracts every installed machine's footprint from the shared pool. Finished-goods targets share the remaining allocation across lines. Machinery purchases reject insufficient room before changing assets or cash. Configuration changes that would overflow existing storage are rejected. | Near-full T1/T2 procurement, rejected machinery purchases, and atomic storage-change regressions; full-population occupancy checked every tick. |
| 11 P2 Relationship change only recognizes the first offer | Relationship updates use actual transactions: one seller must have supplied the full final order. Empty earlier offers do not prevent a later full supplier from becoming incumbent. Split orders retain the existing relationship. | Empty-first-offer, single-full-fill, and split-fill cases run in both engines. |
| 12 P2 Manufacturer player quotes are cost-clamped | T2 player quotes use the same numerical guardrails and cent rounding as other tiers. A quote below cost is allowed; production still observes its profitability gate. | A $0.01 T2 quote remains in force after a tick and does not trigger loss-making production. |
| 13 P2 Live reference-cost changes diverge between engines | Both engines derive procurement reference costs from current configuration. Applying configuration refreshes the world's stored reference costs and loyalty cost denominators. | Every invented product is represented in a 32-tick parity fixture, with a mixed-complexity expanded firm and changed reference/conversion costs. World arrays match exactly; aggregate floating-point sums agree within $0.000001. |
| 14 P2 Partial retail orders count as full | Filled-order counts require the complete requested quantity. A seller's partial delivery is not full availability. A separate purchase-event count keeps partial purchases in AOV accounting. Uncompetitive quotes rejected before purchase do not become failed availability checks. | Full, partial, and split orders verify relationship, fulfillment, reliability, and quantity ledgers in both engines; the year audit independently reconstructs filled-order counts. |

Two related expansion defects were repaired while implementing points 9 and 10: Python production used the last planned line's complexity when charging another line's conversion cost, and newly purchased compound T1 machinery initialized input cost per batch rather than per item. T1 equipment purchases now also enter the equipment-sink accounting.

## Validation

- `./run.sh test` passes RNG, 35-tick determinism, 30-tick conservation/invariants, naming checks, and all 18 targeted review regressions.
- The parity regression explicitly assigns all 200 invented products. Ordinary reduced worlds take a product prefix and are not representative of all complexities; the earlier 6,000-firm check should not be interpreted as complete complexity coverage.
- An HTTP/WebSocket integration check covers two attached clients, save, load, and continued stepping through an existing connection.
- JavaScript syntax checks pass for `app.js`, `catalog.js`, and `bridge.js`. Catalog regeneration reproduces the checked-in JSON exactly. `git diff --check` passes.
- The independent year audit runs the default population and seed for 360 ticks. It checks finite/nonnegative cash and inventory, positive bounded active quotes, reliability bounds, whole-lot raw sales and integer downstream goods, shared storage occupancy, cash conservation, and both quantity and full-order ledgers on every tick. Raw extraction inventory may be fractional; wholesale sales remain whole lots.

### One year results

Default seed **137**, **20 extractors**, **1,000 refineries**, **60,000 manufacturers**, and **1,000,000 distributors**. All **360 ticks** passed the audit in **98.3 seconds**, including JIT startup.

| Group | Firms | Year equity ROI | Individual ROI minimum to maximum |
| --- | ---: | ---: | ---: |
| T0 | 20 | 6.9790% | 1.7583% to 12.6285% |
| T1 | 1,000 | 16.8846% | 1.2111% to 27.7868% |
| C3 | 36,000 | 0.5926% | 0.5311% to 0.6397% |
| C4 | 18,000 | 0.4148% | 0.3611% to 0.4926% |
| C5 | 6,000 | 0.2106% | 0.1784% to 0.2337% |

Full orders: **38.1677%** of **71,995,362** orders across the year. Quantity fill rate: **41.9441%**. Every manufacturer recorded at least one sale.

Maximum absolute per-tick cash-conservation residual: **$0.00000964**. Maximum storage occupancy including machinery: **12,495 / 20,000** for T1 and **5,018 / 20,000** for T2.

Final average quotes: T0 **$1.15650**, T1 **$2.03334**, C3 **$3.60000**, C4 **$3.98000**, C5 **$4.35000**.

Equity ROI includes inventory at book cost, machinery, and licenses. These are group aggregate returns from tick 0 to tick 360, not a steady-state profitability estimate. The spread is material: the technical fixes pass, but this run does not establish the canon’s equal-ROI fairness target.

The machine-readable result is saved in [economy review validation](economy-review-validation-2026-10-10.json).

## Further findings for discussion

These are outside the 14 requested repairs. Items 1–4 were fixed in a follow-up commit (see [Follow-up fixes](#follow-up-fixes)); item 5 is deferred to the operator:

1. **P2 Shared run scheduling is still tied to each WebSocket.** Each connection's Run command enters its own `_run_loop`, and each loop calls `rt.step()`. Two running clients can therefore advance one shared world through two schedulers. A disconnected running client can also leave `running` true with no loop advancing it. The attachment and checkpoint repairs do not establish a single server-owned scheduler. See `economy/server/service.py`, `ws_endpoint` and `_run_loop`.
2. **P2 Partial nested configuration patches can leave invalid state.** Reproduced with `apply_config({'t2Capacity': {'3': 30}})`: it raises `KeyError: 4` after assigning `{3: 30.0}` into the runtime config. The dashboard sends all three capacity values, but API callers can trigger this. General mapping normalization and transactional configuration application need a separate repair; the loyalty mapping and storage paths covered above are fixed.
3. **The design still conflicts over market-average pricing.** Canon axiom 2 prohibits a market-average target; section 12 specifies the going-rate anchor used by the implementation. Choosing which rule governs requires a design decision. The anchor slider now works; the pricing model has not been replaced.
4. **Loyalty documentation and bootstrap AOV disagree about 5% versus 10%.** The annual update uses `0.05`; the starting AOV inference divides by `0.10`, and README text still describes 10%. This deserves an explicit decision before changing bootstrap behavior.
5. **One year does not establish sustained equal equity ROI.** The measured group returns above differ materially. Longer runs and multiple seeds are needed after these behavioral corrections; the previous calibration traces are not interchangeable with the corrected kernel.

## Follow-up fixes

The four actionable follow-ups (items 1–4 above) were repaired in a second pass:

1. **Single server-owned scheduler.** `service.py` now owns one `_scheduler` task that ticks the world and broadcasts to all attached sockets through a `_ConnectionManager`; `ws_endpoint` no longer enters a per-connection run loop, and `_run_loop` is removed. Two clients can no longer advance one world through two schedulers, and a disconnecting client cannot strand `running` with no loop.
2. **Total, atomic configuration.** `_clamp_mapping` now fills missing mapping keys from defaults (matching the loyalty-mapping normalization), so a partial patch such as `{'t2Capacity': {'3': 30}}` produces a complete mapping. `apply_config` precomputes all derived values against the candidate before committing, so a failure cannot leave the runtime half-configured.
3. **Market-average pricing clarified.** Axiom 2 now forbids buyers and sellers *coordinating* on a common target price, while explicitly permitting a single firm to observe its market's realized going rate and position itself against it (§12.2). No behavioral change.
4. **Loyalty charge 5 % everywhere.** The bootstrap AOV inference now divides by `0.05` (was `0.10`), matching the annual `M = 0.05 × AOV / (unit_cost × 1.5)` re-derivation; the README and the `_init_loyalty_regime` comment now say 5 %.

Version 1 checkpoints cannot recover ownership metadata that was never saved. Loading preserves recoverable world state and reconstructs controls/equipment; missing administrative fields receive defaults. Version 2 checkpoints preserve those fields going forward. Existing checkpoints already above the newly enforced storage limit are not silently liquidated; procurement admits no additional goods while full, and existing goods can drain through sales.

## Reproduction

```sh
./run.sh test
PYTHONPATH="$PWD/.pydeps:$PWD" python3 -W ignore tools/review_year.py \
  --output stats/review-fixes-verified-2026-10-10
node --check web/app.js
node --check web/catalog.js
node --check web/bridge.js
node tools/dump_catalog.js /tmp/ibicot-catalog-check.json
cmp economy/core/catalog.json /tmp/ibicot-catalog-check.json
```

Use the Python 3.12 interpreter selected by `run.sh` if `python3` points to a different environment. The year audit writes monthly JSONL and a final JSON summary under its output directory; `stats/` remains git-ignored.
