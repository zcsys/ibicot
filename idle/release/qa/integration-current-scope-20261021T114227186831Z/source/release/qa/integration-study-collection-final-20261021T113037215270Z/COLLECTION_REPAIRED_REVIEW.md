# Independent study collection repair review

The repaired pure-Dart recorder and Python adjudicator pass this bounded review. This is implementation evidence for preparation, not a qualified study deployment or a release approval. The UI is explicitly excluded and has a separately reported pending-start ordering concern.

The reviewed 48-input fingerprint is `773be63e2e05586581df29a9bf10e40db51260c1d68a1261c7a8f6c5d646574b`. Recorder SHA-256 is `40be5e8ae640edfe67c6704074bbfb5a2f62fca2e8060b0d96cf50d22b72904f`; adjudicator is `b158d082812603f6f02576ddc950b834c06254e718e3e0efadb4bb26679b87b6`. All source inputs were copied before execution; frozen and live inputs still matched after the run. `snapshot.json` pins the exact source and independent probes. `verification.json` records every command and log digest.

## Reproduced checks

| Evidence | Result | Meaning |
|---|---:|---|
| Independent Dart adversarial cases | 9 pass | Actual disk CAS exclusion across two objects, isolates and path aliases; exact inactivity transition; immediate withdrawal stop after failed write; late sidecar veto; minimal-to-full erasure including disk reopen |
| Author recorder regressions independently replayed | 21 pass | Canonical storage, capacity, corruption/configuration rejection, deliberate enrollment, retry and durable withdrawal marker boundaries |
| Independent Python adjudication cases | 5 pass | No post-terminal inactivity restart, no untriggered background session, ordered same-second crash boundary, positive control and coverage subtraction |
| Author adjudicator/analyzer cases independently replayed | 30 pass | Strict inputs, fixed registry, missingness, returns, valid-session quality denominator and descriptive analysis |
| Scoped Dart analysis | Clean | Recorder and author fixture/test files only |
| Actual Dart generator → Python adjudication → analysis | Pass | Four exported files byte-identical; qualified data byte-identical and final report semantically identical to the preserved synthetic fixture |

There are 65 distinct executed test cases in this pin, not 65 people or sessions. The real generator produced three synthetic registries: a startup departure, an interactive return and an absent stream. Its output is code-path evidence only. No human enrollment, trusted device time, native crash, observed D30 or elapsed season was created.

## Findings and exact repairs

**STUDY002.** The original POSIX advisory file lock allowed simultaneous same-process writers to both commit the same generation. Independent tests reproduced this across objects, isolates and `/./` path aliases. The final implementation first obtains an atomic exclusive-create filesystem guard, then retains the advisory lock and expected-digest comparison. A collision fails without mutation. The recorder also rejects the reserved unknown-configuration label, matching the adjudicator.

**STUDY003.** The original adjudicator accepted an inactivity start after terminal, an inactivity start without its atomic triggering observation, and an old session crash after a later same-second process restart. The repair validates immediate event order, same identity/configuration and exact trigger, and bounds crash timing by the next session in record order. Positive legitimate inactivity and gap-subtracted coverage still pass.

**STUDY004.** Withdrawal now revokes collection synchronously before queued writes can proceed. A nonidentifying `.withdrawn` sidecar stops collection across reopen even if erasure fails. Its presence is checked again before rename, so a paused active write cannot commit after another store requests withdrawal. A failed erase remains retryable. The first repair incorrectly made any already-withdrawn state a no-op: default full erasure after previously approved minimal retention preserved the identifier. This review reproduced that in memory and after real disk reopen. The final repair permits stronger erasure and prevents a later weaker request from restoring data. All original assertions remain intact.

Initial failure evidence remains under `release/qa/integration-study-collection-20261021T110635265548Z/`. The intermediate repaired source and its seven-pass/two-fail erasure reproduction remain under `release/qa/integration-study-collection-repaired-20261021T112313207289Z/`; they are not overwritten by this passing pin.

## Limits and operational consequences

- A process death while holding the exclusive guard can leave it behind. Subsequent writes fail closed; there is no automatic lock stealing. Reads remain possible. Recovery requires an operator to establish that no writer exists before removing the guard. This is an explicit availability limit, not automatic crash-safe continuation.
- A sidecar or main-file write must succeed for withdrawal to survive process death. If both are refused, only current-process intent can be retained. Generic injected stores without `StudyWithdrawalStore` do not gain a durable sidecar contract. A partial sidecar is deliberately interpreted as a stop request.
- `exportRaw()` is a low-level persisted-document export; it does not embed a pending stop sidecar. UI must block exports during incomplete withdrawal. Ordinary failed-start recovery must preserve access to previously verified records. The moving Flutter integration is reviewed separately.
- The app-private filesystem, backup exclusion, actual deletion/encryption and power-loss/directory durability require native qualification. Hash chains do not prove a truthful clock, complete population, meaningful eligibility, authentic human actions or a genuine external crash report. A full rewritten chain can be forged.
- Successful opt-in recording begins only after its first durable enrollment. Native/pre-Dart crashes, pre-consent failures and failures before that write remain outside the collector. A fixed lawful enrollment registry must be retained independently of later return exports. Source qualification of real crash/linkage/coverage evidence remains a human operating obligation.
- Capacity bounds stop and disclose gaps rather than silently pruning early starts. The 4,096-record default must be qualified against the actual study event rate; it is not evidence of complete 30-day capture. Default local erasure cannot erase previously shared copies.
- No outbound collection, commercial provider, store account, real participants, physical hardware, causal experiment or original package acceptance is asserted.

## Two-direction scope contribution

| Original obligation | Concrete local contribution | Remaining requirement |
|---|---|---|
| S30 / M5-04, M6-01 | Explicit pre-bootstrap start API, valid-session preservation, frozen denominator inputs and independently replayed adjudication | Correct native/UI start ordering; qualified native crash collection including stated pre-Dart limit; actual 10,000-session sample and per-device critical-flow audit |
| S34 / M5-05, M6-01 | Exact configuration, lawful independent registry, missing-stream retention, coverage subtraction and descriptive D1/D7/D30 analysis | Approved preregistration/consent/recruitment, valid acquisition/exclusions, real observation windows and documented real evidence qualification |
| S39 / M5-03 | Immediate stop, durable stop-marker retry and full local identifier erasure across reopen | UI export/withdrawal review; native storage/backup/network audit and authority over already exported copies |
| S42 / M7-06 | Immutable source pins, preserved failures and reproducible synthetic preparation evidence | Exact complete release candidate and all original gates; this report grants no release approval |

Conversely, the recorder serves consented collection, the adjudicator serves source qualification, and the independent probes/fixtures serve local verification. They add no game rewards, economy constants, public web replacement or release-threshold changes. The comprehensive 44-obligation/65-package audit is separate; all original acceptance wording and dependency order remain binding. The three BOOT approvals remain preparation work, separate from original production acceptance.
