# S14 economic transition — author handoff

Status: implemented and host-validated; independent v2 review and native
qualification remain separate acceptance gates. No scope/program status or
shipped economic constant changed.

## Exact frozen inputs

`source-v2-20261021T121308Z/SOURCE_SHA256.json` indexes 36 source/config/test
inputs. Index SHA-256:
`3e299f1bfac9f932f26a4a8a9a2be3f6e6846230b900207bea1848444e1ad4ec`.
The earlier `source-20261021T120658Z` is preserved and superseded by v2 for
transition correctness. `AUTHOR_EVIDENCE.json` records pre/post library hashes.

Core changes are limited to rules identity, strict decode/command guards,
compatible state adoption and event identity. Four of the original eight core
library files changed; fixed arithmetic and economic parameter bytes did not.
Baseline economic digest remains
`9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6`.
State schema/event-order remain 4. Baseline serialized keys, order and values are
unchanged. `BASELINE_PARITY.json` proves byte-identical serialized states,
events, output, prices and prestige awards across 11 fixed traces against the
exact observed pre-edit core, including purchases one micro-R below/at/above
cost, prestige boundary, bonuses, automation and offline tail. This bounded
comparison is not an exhaustive mathematical equivalence proof.

The synthetic old rules exist only under core test support/fixtures, with
version `tideglass-economy-0.0.1` and exact producer output multiplier 3/2. They
are not a historical shipped release, a proposed rebalance or a production
remote rule. Fixture digest:
`9ecd3addb659b78144ecf733239b8003ab3af516897f7e7f7ee2c810955295c6`.

## Evidence

| Check | Result | Evidence |
|---|---:|---|
| Core analyzer/full tests | clean; 196 pass | `core-v2-tests.log` |
| Focused old→new core/repository tests | 20 included | `game/core/test/economic_transition_test.dart` |
| Persistence analyzer/full tests | clean; 28 pass | `persistence-v2-tests.log` |
| Isolate/process lock tests | 5 included | separate isolate; SIGKILL before write/after flush/after rename; nonregular lock rejection |
| Additional transition repository tests | 4 included | complete-envelope receipt, mandatory cursor validators, ancestor reentry, same-instance ambiguous rename |
| Scenario arithmetic regression | 2,658 assertions pass | `scenario-cache-regression.json` ; 14 rule sets and 26 full traces |
| Before/after baseline byte comparison | 11 cases identical | `BASELINE_PARITY.json`; hash `e08b5a2a2687bcd0bbc7f68fdf60fb9d0a6e23c07b47aff4fab45ba80b1f10b8` |
| Actual Flutter bootstrap integration | 18 checks passed, root-owned | `release/native-proof/root-transition-20261021T121321.388435Z` |

At 1 µs the synthetic old rate produces exactly 1 micro-R and half a micro-R of
carried residue. After the switch, another 1 µs under baseline earns exactly 1
micro-R and retains that residue. The 36 h old interval earns 145,800 R using the
old full-rate/quarter-rate windows; the following baseline second earns 1 R.
Zero pending time creates no income. Unknown version/digest, unauthorized or
backwards boundary, unclosed accumulator, wrong cursor/migration, stale writer,
changed source/boundary and predecessor import reject without replacing progress.

An injected failure before rename can recompute pure replay but never commits
it twice. A failure after rename reuses the persisted receipt, including on the
same repository instance without first calling load. Subsequent ordinary saves
retain that receipt and retry returns their newer state. Import clears it and
forks the branch.

## Findings and repairs

The author-created independent-isolate probe reproduced a pre-existing defect:
Dart FileLock permitted another isolate to commit through a held writer. The
original failure is preserved in `lock-before-repair.log`. Native POSIX flock
replaces this primitive and the three real process-termination cases pass.
Canonical alias lookup occurs before FIFO queue insertion; an intermediate
async canonicalization reordered same-instance queued saves and was repaired
before the accepted freeze. No failed intermediate log is a final pass claim.

Independent QA discovered ECON001: A→B→A callback reentry lost A from a
single-directory zone value and deadlocked. V2 carries an immutable set of
ancestor canonical directories and rejects ancestor reentry. QA independently
reproduced the author-identified missing cursor-validator and edited-source
receipt weaknesses as well. V2 requires both cursor validators and binds the
complete source envelope hash. Independent reviewer closure is pending; this
handoff does not self-approve those findings.

Root owns `bootstrap.dart`, `offline_replay.dart`, `client_economic_transition.dart`
and actual widget integration. Root registers compiled predecessors, supplies
old replay engines to the worker, settles all partitions, then starts the
baseline controller only after commit. The shipped predecessor list is empty.
Rollback uses the existing saved cursor as a zero-income transition boundary.

## Reproduction and limits

From `game/core`: `../../tool/dart analyze` and `../../tool/dart test`.
From `game/persistence`: the same two commands.
From repository root:
`python3 game/qa/run_scenario_memo_probe.py --output <new-output-prefix>` and
`python3 release/economy-transition/verify_baseline.py`.

The new native dependency is `ffi: 2.2.0`, already the resolved transitive
version in mobile/core. The persistence README documents libc symbols, flags,
regular-file checks and ABI constraints. Apple/Linux/Android constants were
checked against installed SDK headers; Android/iOS native AOT and device
power-loss tests remain platform work. Locks are advisory; the app-owned
directory and cooperating writers are assumptions. Pure settlement callbacks
must not mutate other stores or grant external rewards. Production replay
workers do not own repository descriptors; arbitrary forced writer-isolate
cancellation is outside the process-crash recovery claim.

This completes the author contribution to M1-01/M1-04/M3-01/M3-10 and
S12/S14/S28/S40. It does not declare those obligations accepted, beta approved,
release ready, human retention proven or finished v1.
