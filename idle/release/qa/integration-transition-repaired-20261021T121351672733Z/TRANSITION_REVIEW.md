# Independent economic transition and writer-isolation review

The repaired host implementation is qualified for the bounded compatible-transition behavior tested here. ECON001 is closed at this pin. The old writer-isolation defect is independently reproduced against its preserved implementation and repaired by the current kernel lock. This review recommends retaining the existing bounded mathematical decisions; it does not accept a complete persistence, native, commerce or release package.

## Exact inputs and executions

The 36 core/persistence/contract inputs match author freeze `source-v2-20261021T121308Z`, index SHA-256 `3e299f1bfac9f932f26a4a8a9a2be3f6e6846230b900207bea1848444e1ad4ec`. The independent source-map fingerprint is `f01f874355b963ac5927f57ae1586b9de0ec50af81edf8dd267708a896fb12be`. All copied and live inputs were rehashed after execution without drift. Tests ran in a separate frozen workspace, with offline dependency resolution.

| Execution | Result | Attribution and boundary |
|---|---:|---|
| Core full suite | 208 pass | 196 author cases plus 12 independently written transition probes, rerun by QA |
| Persistence full suite | 28 pass | QA reran author fault, locking, import and transition cases; includes real separate isolates and SIGKILL child processes |
| Core/persistence analyzers | Clean | Separate frozen packages |
| Historical writer exclusion | Expected failure | Same isolate test against original `f8aebe4…` implementation: a second isolate committed a SaveSnapshot while the first held its lock |
| Actual bootstrap, ordinary bootstrap, worker and previous QA replay | 18 pass | Root executed exclusive Flutter lane; QA inspected all four new bootstrap cases, rehashed 524 archived inputs, checked before/after equality and raw logs. Not independently rerun by QA |
| Current numerical bridge | 62 exact rows; 15,365 assertions | Independently executed in initial review; all eight core files byte-identical to repaired review. Details in `NUMERIC_EVIDENCE_BRIDGE.json` |

No Flutter process was launched by this reviewer during the shared native lane. The native candidate152 predates these changes and cannot qualify this new FFI lock or transition adapter.

## Findings and repairs

**ECON001 — nested transition callback deadlock.** Original A→B→A callback nesting replaced the ancestor lock identity with B, so A queued behind its own outstanding operation. The bounded independent probe failed with a timeout. The repair preserves an immutable set of every ancestor canonical directory and rejects reentry before queueing. The same assertion now passes. Original failed ten-case and expanded twelve-case runs remain under `integration-transition-initial-20261021T120817091439Z`; the expanded harness drains a timed-out future before cleanup without weakening the expectation.

**Writer isolation — author finding independently confirmed.** Dart's old process-scoped FileLock allowed a second isolate to commit through another isolate's lock. The preserved old source fails the unchanged exclusion test. The new nonblocking `flock` on separately opened file descriptions excludes cooperating isolates/processes, retains a stable lock inode, and releases through descriptor closure after SIGKILL. Reproduced author cases kill a child before write, after flush and after rename; a later writer either commits from the old generation or rejects its stale revision after the committed rename. These are host process-death tests, not sudden power-loss or filesystem fsync guarantees.

**Two author-identified hardening changes independently rechecked.** Compatible registration now requires both old and destination cursor validators. Retry receipts bind the complete original envelope digest, so altered payloads with reused save/branch/revision/pins/cursor cannot impersonate the original operation. Both expanded probes failed on the initial pin and pass on v2. This report does not claim independent discovery of these two issues.

## What the transition establishes

An immutable, code-owned registry authorizes a specific version and economic digest, its old validators, and its compatible migration. Save data and remote configuration cannot register executable rules. The shipped v1 predecessor list is empty. Synthetic 3/2 author and independent 5/4 predecessor fixtures qualify the mechanism; they are not released historical economies.

The independent probes exercise wrong version/digest, foreign source, duplicate registry identity, old/destination cursor mismatch, unauthorized or backward interval, canonical alias contention, nested callbacks, all three write-stage ambiguities, retry after later normal writes, retry after explicit import, and altered-envelope identity. The 5/4 fixture settles a three-microsecond old interval as three currency micro-units plus exactly 0.75 micro-unit residue; eleven later baseline microseconds produce fourteen micro-units with that residue unchanged. No tolerance is used to authorize a purchase or prestige award.

Callbacks run under the writer lock. Precommit failures may recompute a pure callback; external service grants or UI reward side effects are forbidden by the callback contract. Only the committed generation is authoritative. A post-rename retry recognizes the receipt without settlement; later normal writes retain the receipt and the latest progress. Explicit import creates a new branch and clears the local transition receipt.

The actual bootstrap captures its target once, runs the old compiled engine through the existing isolate worker, commits old settlement and destination identity atomically, then exposes a baseline controller. Root's four actual bootstrap cases cover old 1.5 R/s for sixty seconds, baseline 1 R/s afterward, reopen without extra credit, preference preservation, wall-clock rollback at the durable cursor without income, and wrong/unregistered pin rejection without rewriting game generations. In a rollback, `max(target, saved cursor)` authorizes no new production; it preserves already settled time. The adapter covers compatible main-economy changes with the same pinned dossier/season content and unchanged currency basis. It is not evidence for arbitrary content, currency-denomination or scenario-rule migration.

The current nonregular lock checks reject links/directories; the identical lock source also passed the initial independent FIFO/directory/symlink/regular-file subprocess checks. Canonical paths share queues and reentry checks. This is cooperative application writer exclusion, not a defense against a malicious same-user process replacing private files. Platform-specific FFI availability still needs the next native candidate on Android/iOS.

## Numerical and scope bridge

The new state identity and guards leave the 62 numeric/timeline outputs byte-identical to the earlier reference (SHA-256 `8f713d34938cf526136f5ebdaaeb7fc6f584c82616cade78b7c991367480a9b1`). The independent main cache/eviction/large-number probe passes 12,195 assertions; corrected twelve-dossier/season permutations pass 2,658; additional scenario state-key checks pass 512. The fixed economy JSON remains `9e5b9bc…`. This supports retaining M1-01/M1-02 and S03/S29 at their exact existing mathematical scope. It does not restore invalidated cache-era balance conclusions or transfer old native timing to changed code.

`scope-audit.json` preserves all 44 requirement verification clauses and all 65 original package acceptance/dependency lists. It adds current transition evidence in both directions for S12/S14/S28/S40 and the numerical bridge for S03/S29. The previous comprehensive semantic audit remains the baseline for unrelated requirements; they are not silently re-reviewed or promoted here. M1-03/M1-04/M3-01/M3-10/M5-07 keep their complete original criteria and upstream dependencies. Bootstrap contributions remain distinct. No status or production file was edited by QA.

The scoped host S14 mechanism is now evidenced. Complete current native builds, physical-device/power-loss evidence, final release defect status, store/provider delivery, real participants and calendar observations remain separate obligations. User resources remain unavailable for external gates.
