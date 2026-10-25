# Current-runtime native qualification preparation

Status: authored and Python-tested; **Dart compilation and native execution are pending**. This does not supersede frozen152 or qualify the current application. The lead owns Flutter, builds and devices. The harness remains outside the mobile source tree during the lead's pinned analysis window.

## Files and prerequisites

- Staged source: `staged/current_runtime_test.dart`. After the lead releases its analysis window, copy its exact reviewed bytes to `game/mobile/integration_test/current_runtime_test.dart`, compile/analyze, repair any finding with new pins, then freeze the current candidate. Do not copy it into a prior candidate's immutable source.
- Runner: `tool/verify_current_runtime.py`; author probes: `tool/test_current_runtime_verification.py`. Existing `verify_native.py`, native driver and build tooling are reused without edits. The runner refuses to execute while the harness is only staged.
- `report-data.schema.json` describes the native driver's result. `verification.json` is the host report. All source/result/log/screenshot/native-file bytes are pinned in its `evidence_sha256`; archive the final report's own SHA externally when reviewing it.
- The future host gate needs an explicit `test_current_runtime_verification.py` selection; the existing `test_native_*.py` glob does not include it. The lead owns that shared build-tool change.
- Use the exact same candidate, reviewed runner/harness bytes, device, label and run ID for a preparation/recovery pair. Every independent fresh scenario needs a new run ID; existing fixture trees are never erased automatically.
- Run only on a dedicated, already selected simulator/emulator with the application installed by this candidate. No uninstalls, reset commands, native screen automation, credentials or network endpoints are part of this program. Physical devices and production/store qualification remain open.
- Protected tablet `F103390E-7B7C-4F0B-9404-5E029C7131FF` is refused before any external process. Approved dedicated devices from the previous lane were phone `F05BE4B0-52C1-4CA1-B721-BD64AE559E3F`, tablet `089884DC-AD2A-4D69-8C60-C50271AC21BF`, and Android `emulator-5556`; the lead must rediscover availability before any use. The runner does not boot devices.

## Isolation and overrides

Native fixtures live under the actual app support directory at `native-current-verification/<label>-<run-id>/<group>`; cache tests use the same unique namespace under the native temporary directory. The normal `tideglass` save is never selected. All predecessor, study, enrollment and cache contents are explicitly synthetic.

Actual `TideglassBootstrap` has two global side effects that require explicit handling. Its startup soundtrack maintenance can create an empty shared temporary cache. The harness first refuses any existing nonempty/non-directory/symlink shared cache, so it never removes an existing archive; only an absent or empty shared cache is permitted. Reminder service initialization can cancel OS notification IDs. The harness therefore injects the real notification service and a fixture-local preference file with a no-op gateway that rejects permission/schedule/settings requests. This is not notification-delivery proof. Injected services are disposed by the harness because Bootstrap does not own them.

Service URL must be empty and commerce, supporter and rewarded-ad defines must be false. Audio is disabled for these additional cases. Existing qualified gameplay/audio/lifecycle/appearance and native-clock scenarios remain separate in the prior protocol; they should be rerun for a final candidate rather than inferred from these tests.

## Exact scenario allowlist

| Scenario | Group | Actual assertion / expected status | Required predecessor |
|---|---|---|---|
| `runtime-lock-exclusion` | save-lock | Separate Dart isolate holds production FFI flock; contender waits, then stale revision conflicts; generation remains1. Pass. | None |
| `runtime-save-hold-beforeWrite` | save-beforeWrite | Seed0; real save1 pauses at commit probe while lock held; external SIGKILL. Expected interrupted. | None |
| `runtime-save-recover-beforeWrite` | save-beforeWrite | Different process loads0, saves2, proving released native lock. Pass. | hold-beforeWrite |
| `runtime-save-hold-afterFlush` | save-afterFlush | Seed0; real save1 pauses after temporary generation flush; SIGKILL. Expected interrupted. | None |
| `runtime-save-recover-afterFlush` | save-afterFlush | Different process loads committed0, saves2. Pass. | hold-afterFlush |
| `runtime-save-hold-afterRename` | save-afterRename | Seed0; real save1 pauses after generation rename; SIGKILL. Expected interrupted. | None |
| `runtime-save-recover-afterRename` | save-afterRename | Different process loads1, saves2. Pass. | hold-afterRename |
| `runtime-transition-start` | transition | Inject synthetic predecessor1.5R/s; production Bootstrap settles60s to90R before adopting current1R/s; preferences retained. Pass. | None |
| `runtime-transition-reopen` | transition | Default empty predecessor registration at61s yields91R; same-cursor reopen stays91R. Pass. | transition-start |
| `runtime-study-default` | study | Empty provision bypasses recorder opening; native study support files stay absent. Pass. | None |
| `runtime-study-enroll` | study | Actual synthetic consent UI; durable app_start before harbor; actual interaction and isolated native files. Pass. | None |
| `runtime-study-restart` | study | New OS/logical process; original install/first launch/first record hash retained; one new app_start; no invented terminal. Pass. | study-enroll |
| `runtime-study-crash-hold` | study | Same synthetic enrollment, then held checkpoint and real host SIGKILL. Expected interrupted, **not a native fatal/crash claim**. | None |
| `runtime-study-crash-reopen` | study | New OS process retains enrollment/chain and records restart after independently observed kill. Pass. | study-crash-hold |
| `runtime-study-capacity` | study | Inject8record/32768byte bound; production recorder exhausts with gap and production settings show stopped status. Pass. | None |
| `runtime-study-storage-withdraw` | study | Fixture-only stale CAS guard causes real file refusal; production status visible; actual UI withdrawal erases registry/events/eligibility, leaves stop marker. Pass. | None |
| `runtime-study-withdraw-reopen` | study | New process respects tombstone; no active session/re-enrollment; erased files remain erased. Pass. | study-storage-withdraw |
| `runtime-cache-grace` | temp/cache | Actual native files:3export quota; fourth refused before download; backward/23h clock retains;25h cleans; held action prevents cleanup/concurrent export; oversized file refused. Pass. | None |

The8record capacity limit, predecessor, rate, time cursor and cache clock are test injections. Sparse oversized file data are synthetic. No natural pacing, full-disk/power-loss, OS cache guarantee, actual receiving-app read, external user or real consent is claimed.

## Execution recipe — lead only, after review and handoff

From the repository root, use this one runner. It supplies the pinned native driver, exact identity defines, `--keep-app-running`, a180second native driver timeout and `--no-pub`. Its outer timeout allows startup/build. Do not run a second Flutter operation in parallel.

```sh
python3 tool/verify_current_runtime.py /absolute/path/to/frozen-candidate \
  --device F05BE4B0-52C1-4CA1-B721-BD64AE559E3F --label ios-phone \
  --scenario runtime-save-hold-afterFlush --run-id final-current-save-flush-01
```

The printed evidence directory contains `verification.json`. Preparation is usable only when its `status` is `expected-interrupted`, `passed` is false, and no verification errors remain. Shell exit0 here means the expected interruption protocol completed; it is **not a passed test**. Use the exact returned report path for recovery:

```sh
python3 tool/verify_current_runtime.py /absolute/path/to/frozen-candidate \
  --device F05BE4B0-52C1-4CA1-B721-BD64AE559E3F --label ios-phone \
  --scenario runtime-save-recover-afterFlush --run-id final-current-save-flush-01 \
  --predecessor /absolute/path/to/preparation/verification.json
```

Use the table's matching start/reopen pair in the same way. Standalone cases omit `--predecessor`. Repeat the18-case matrix for each approved device only after the first phone cases pass; retain every failed attempt with its actual source pins. Current fixed presets support iOS simulator and Android emulator identifiers, not macOS or physical devices.

## Host proof and report schema

Normal pass requires exit0, a positive-count actual native framework success marker, independent driver success, no framework/uncaught/teardown errors, matching result identity, `completed:true`, scenario-specific asserted values, intact candidate/source/helper pins and independently observed process termination. The runner uses the existing strict completion helper, including E/flutter uncaught failures. A host stop preserves installation and the isolated save.

Each killed preparation prints one anchored `TIDEGLASS_RUNTIME_KILL_READY` JSON marker. The host verifies its candidate/harness/verification/scenario/PID, reads only the exact fixture checkpoint, and verifies bytes against its marker hash. It checks the actual simulator's app container/executable (iOS) or exact bundle cmdline and pidof (Android). Immediately after identity validation and before SIGKILL it saves the entire observed byte prefix as `pre-kill.log`, rejects any native framework/uncaught/build error in it, and records its byte length/hash. The host then records the exact signal action and polls for process disappearance. The full log and host observations remain attached. Post-kill driver lost-connection cleanup is separate. Any successful framework/driver completion in killed preparation is rejected. No kill marker alone can qualify a process stop.

Recovery revalidates predecessor source identities, evidence bytes, checkpoint identity and stage, pre-kill prefix, actual host termination and saved-generation pins. It must independently pass normal completion and use a different OS PID. The result's previous-verification/checkpoint/PID fields must match the predecessor exactly. The current checkpoint may not be replaced during recovery. Save/transition generations are exported from fixed paths after process termination and pinned individually.

For every study case the host reads **only** fixed files under the synthetic group: `support/tideglass-study.json` (≤2MiB), `support/tideglass-study-eligibility.json` (≤4096bytes), `support/tideglass-study.json.withdrawn` (≤4096bytes), or records their observed absence. Native files are captured after termination, including killed study preparations. Raw records and eligibility are decoded with the existing Python study decoder; chain, bounded capacity, candidate/synthetic registry and withdrawal tombstone/sidecars are checked independently. This is structural interoperability proof, not protocol enrollment or crash adjudication. The synthetic protocol hash is intentionally a placeholder.

Host `verification.json` contains identity/command/source pins; `status` (`passed`, `expected-interrupted`, `failed`); `passed` (true only for normal pass); `exit_code`; error list; native stop or kill ledger; checkpoint and generation metadata; study artifact presence/hash/size metadata and decoding summary; predecessor report path/SHA; source drift checks; and `evidence_sha256`. Failure reports and any resulting app/fixture state are preserved for inspection. The runner does not silently reset or reinstall the ordinary app after failure; restoring a candidate's normal app remains an explicit lead action.

## Remaining implementation and qualification gates

1. Lead release of analysis window; compile and analyze exact staged source; repair actual errors with updated pins.
2. Independent review of runner/fixtures/Python cases, then full current host gates and final candidate builds. Existing older candidate success cannot substitute for new FFI/native plugin qualification.
3. Actual18-case native runs plus the baseline protocol on dedicated iPhone/Android/tablet; verify strict logs and source snapshots after each run.
4. Production consented crash linkage remains a local implementation gap. See `CRASH_LINK_PROPOSAL.md`; harness-only logical-process↔OS-PID mapping cannot replace it.
5. No participant recruitment,10,000 observed sessions, physical hardware testing, signing, store acceptance or public hosting has been supplied or claimed.
