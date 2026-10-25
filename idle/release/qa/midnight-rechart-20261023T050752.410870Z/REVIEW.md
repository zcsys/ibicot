# Independent midnight/Rechart collision review

**The identified M3-10 reset/account-day collision evidence gap is closed for the reviewed shared-core fixture.** Four cases pass independently at the final test pin: UTC offsets0/+180 minutes, each online/offline. This is additional clause evidence; it does not accept the whole package or remove its prerequisites.

Final test SHA256: `3de6787e7ac4f4fd653f1c4aca3f026128a207c83f8570447207ec3016d754c6`. Production source did not change. All nine core library files and two package inputs match frozen candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`. The added test is explicitly subsequent evidence against those unchanged libraries, not a claim that the original candidate manifest already contained it.

## Independent execution and oracle inspection

QA invoked the direct pinned Dart3.13.5 executable in `game/core`, running only `test/qa_midnight_rechart_test.dart` with the JSON reporter. No Flutter wrapper, mobile suite, simulator, device command, build or production/status edit ran. The four named tests complete successfully, none are skipped, stderr is empty, and the runner terminates with success. All four emitted records match the author's records exactly. The author’s scoped clean analyzer result is pinned and inspected, not presented as a separate QA analyzer execution.

The fixture genuinely aligns six events. Its existing elapsed time is599seconds, minimum Rechart duration600seconds, and the old fixed-offset account day has one second remaining. Focus and Support have one second left; their generation/completion phases also have one second remaining. At999,999microseconds none of those events has fired. The next microsecond reaches all six boundaries together.

Actual `engine.dart` control flow and the documented order agree: income over the preceding half-open interval; Focus expiry; Support expiry; Focus generation; Survey completion; calendar/token rollover; then the selected automatic Rechart. The test asserts that exact sequence at elapsed600,000,000microseconds. It checks five new Charts, wallet0, one gifted Skiff, retained lifetime, retained claimed10Notes/250XP, one new Focus charge and Survey, expired old token, and zero expired effect durations/phases.

QA separately evaluated the fixture’s income with80-digit Decimal arithmetic. The build goal clamps to five Skiffs, leaving15Skiffs plus one Nursery: base35R/s, no milestone or late-tier synergy. At100Charts the permanent multiplier is `1 + sqrt(10)`; combined Focus/Support is `1.45`. Therefore:

`floor(35 × (1 + sqrt(10)) × 1.45 × 1,000,000) = 211,235,591 micro-R`.

The unrounded result is211,235,591.253545…micro-R, safely away from the next integer boundary. It matches all four rows independently of the test’s production-rate lookup. This is a fixture-specific numerical check, not a universal error guarantee for irrational rates.

Whole two-second advancement equals999,999µs +1µs +1s, retaining all serialized economic fields, numeric residue, timers, selected policy and receipt data. Only local revision and event IDs are excluded, exactly as the documented chunking contract allows; event kind, timestamp, order and details remain compared. Zero-duration repetition produces no event or state change. A second contract claim and Survey collection reject; the one Survey collection adds exactly10Notes without adding XP.

The online/offline difference is intentional and tested: online new-day contracts snapshot the earned pre-reset rate at midnight; offline assignments remain unmaterialized until return and then snapshot the post-reset rate. Both preserve lifetime and purchase baselines without retroactive rewards. The offline cases use the first full-rate seconds of an absence and correctly carry the offset through chunks. They do not claim additional quarter-rate/cap collision permutations or persisted offline-settlement transaction coverage.

## Rejection assertion strengthened during review

The first independent passing test/source is retained under `first-version/`, SHA256 `46fa400433f0a89284a6cdf44db4376b85365411f1f36d15b3a8a85a17a014d6`. QA identified that the old-day grant used an invalid source and only asserted a generic rejection; this did not isolate the rejection reason, although the collision assertions were sound.

The author changed only that assertion. It now uses the actual old-day briefing identity for unused slot1, asserts `support_account_day_mismatch`, and verifies the returned state is unchanged. QA reproduced the exact diff against the preserved first source, then reran only the same four tests successfully. No economic expectation was weakened. `independent-exact-delta.patch` equals the author’s patch, and both successful runs remain distinct.

The34 final input hashes match after execution. The original before snapshot also retains the separate scope metadata update from `ed8ad9d9…` to `88c2320e…`. This was the root’s S10/S11 adoption, independently checked by the client; its adoption and review are pinned. It changes no test/core source, M3-10 criterion, package status or dependency. The first snapshot has not been rewritten to hide that concurrent update.

## Original scope retained

M3-10 remains:

> Test1/3/6 visits,2/8/24/48/72-hour absences, clock changes, bonus queues and reset/day-boundary collisions; report exact and approximate differences.

The machine-readable `verification.json` preserves the exact original sentence including its spacing and all original dependencies. Assigned reviewer remains **director**. M3-01, M3-02, M3-06 and M3-07 remain in progress; M3-03 is accepted. This report supplies the previously missing collision proof and supplements the existing visit/absence/clock/bonus/numeric evidence. It does not independently adjudicate those entire packages or infer native clock, elapsed-day, service/provider, human, performance or release readiness.

No remaining blocking finding in this narrow fixture. Ready for the next sealed native batch.
