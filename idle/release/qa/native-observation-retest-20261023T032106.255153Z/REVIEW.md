# Independent observation repair retest

Decision: **OBS-001 and OBS-002 are closed for the bounded staged collector. Recommend promotion of the exact pins below, followed by serialized Flutter analysis and the lead’s explicit source freeze.** No native execution or release acceptance is established by this review.

Reviewer: `/root/native_verifier`, different from repair author `/root/observation_repair`. Original failed implementation and evidence remain in `runtime-observation-staged` and `release/qa/native-observation-20261023T025313.166881Z`. This retest changes only this review directory. It runs no Flutter, simulator, emulator, Tideglass process, native export, provider or store action.

## Reproduced evidence

| Check | Result | Evidence |
|---|---|---|
| Author packet/source/output pins | Exact match; no drift | `input-integrity.json`, `inputs-before.json`, `inputs-after.json` |
| Original 21 methods plus 20 repair methods | 41 passed | `author-41-reproduction.log` |
| Original nine independent probes adapted to the actual descriptor-opening boundary | 9 passed | `reviewer-nine-reproduction.log`, `review_probes_descriptor_boundary.py` |
| Additional reviewer methods with adversarial subcases | 6 passed | `additional-six.log`, `additional_review_probes.py` |

These are 56 executed methods across the three suites, with overlap by design, not 56 different native scenarios. All fixtures are disposable and synthetic. The author suite’s real `ps`/`lsof` process is its own short-lived macOS child with a loopback listener; it does not observe Tideglass.

The original `Path.open` interception is obsolete because the repair opens descriptor-relative paths through `os.open`. I inspected the adaptation and replayed it independently in this review directory. It retains the rejection expectations, asserts the symlink/FIFO replacement actually occurred, preserves root identity provisioning, and uses the real bounded storage worker. `reviewer-replay-path-only.patch` records the only differences from the author’s adapted suite: paths locating the input packet. The obsolete original replay and its false `outside_bytes_read` sentinel remain preserved by the repair author and are not called a successful race injection.

## OBS-001 disposition

The directory chain is now opened and retained from `/` using no-follow, nonblocking directory descriptors. Every descendant is opened relative to its retained parent and checked against pre-open identity. The file is read only after a no-follow/nonblocking descriptor is verified as the same regular single-link file. Its metadata and hash come from that descriptor, and directory/named-file identity is checked again before the inventory is returned.

The original leaf-symlink, root-symlink and FIFO counterexamples now reject without returning outside-file hashes or blocking in `open`. Additional author regressions reproduce regular-file replacement, component/root/leaf changes, same-inode mutation, hard links, and size limits. The production per-sample traversal runs in a subprocess bounded by the host command’s remaining budget and a maximum two-second timeout; the actual stalled-child timeout and actual successful worker both reproduce. Constructor-to-worker root identity is mandatory.

Android storage raises an explicit unavailable result without executing a shell storage command. This closes the unsafe fallback, but leaves Android storage observation unqualified. Socket-only collection must remain `finalized-partial-observation`. It does not satisfy a whole-SDK storage audit or M5-03/S39 by itself.

The declared limits remain appropriate: these are checked selected-file observations, not an atomic filesystem snapshot or protection against a privileged mutation-and-restore adversary. Ordinary source/candidate validation is outside the per-sample worker’s hard timeout.

## OBS-002 disposition

The collecting/finalizing module captures its source bytes once, archives those exact bytes, and checks the running source and preserved archive again. Missing or altered collector archives now fail. Candidate manifest/source pins bind the exact runner, harness and completion verifier; finalization checks both the native runner’s archived pins and the observation’s preserved copies.

Completion uses the exact `native_log_errors` function extracted from the pinned verifier archive. It does not import an arbitrary live root or a cached `verify_native` module. The reviewer additionally proves that cached always-success verifiers cannot override native teardown, framework or late-error failures; unrelated module top-level code is not executed; malformed/multiple/decorated completion functions are rejected.

Current collector and candidate verifier changes injected during the final decision are rejected before publication. Separate mutations to observation, runner report, result and log are also rejected. Missing storage retains partial status and a second finalization cannot overwrite the first. Existing exact OPEN/CLOSE, process identity, positive native-test count, driver success, source integrity, explicit opt-in and timestamp containment checks remain intact.

## Exact promotion pins

| File in `release/native-privacy/runtime-observation-repaired/` | SHA256 |
|---|---|
| `runtime_observation.py` | `f3374fb77c83e2b12ff91a48b4c688aa07c7b66042dd75681f7ec2b5fc00febd` |
| `source/game/mobile/integration_test/current_runtime_test.dart` | `102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5` |
| `source/tool/verify_current_runtime.py` | `d849ab8feb642eb1b988f9a6d82558491b7ebef4c63768fb4fa132f49edf3804` |
| `observation-hook.patch` | `c8f2de0803bc9423871c3cfe26d768f519fec752348a7b42decf429d9b2a8c22` |
| `verification.json` | `de520c87f15d3dda0a5328410b26fff212b3d740e0eee426c08c5026e23e1c30` |

The optional two-file hook is unchanged from the first review and retains default behavior when unflagged. The exact current runner/harness/verifier must be included in the new frozen candidate; historical candidate outputs cannot qualify it. Baseline checks must precede promotion, and the lead must explicitly release the native build lane after Flutter analysis.

Five current native exports and the 58-cell protocol remain pending. Observations remain synthetic simulator/emulator evidence with no traffic-absence, startup coverage, physical-device, provider, participant-consent, store or release claim. No work-item or scope status was changed by this review.
