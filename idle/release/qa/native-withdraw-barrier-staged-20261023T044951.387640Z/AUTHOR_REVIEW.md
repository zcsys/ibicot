# Staged native withdrawal precondition synchronization

This is a test-only proposal, not a promoted source change or a passing withdrawal result. The live current runtime harness remains at SHA256 `102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5`. The frozen candidate and all production source remain unchanged.

The preserved 3b00 phone run `current-runtime-ios-phone-20261023T044453553593Z` failed at original harness line 845: the synthetic guard was expected absent but existed. The failure preceded guard injection and withdrawal. A later bounded fixture inspection found the guard absent and retained a completed production interaction record. This is consistent with an in-flight input-triggered writer; it does not independently establish a production defect or prove successful withdrawal.

Production `StudyGate._activity` submits an unawaited serialized recorder operation. `FileStudyStore.compareAndSwap` exclusively creates the guard and removes it in `finally`. `StudyRecorder.interactiveHarbor` uses the same serial queue and returns without writing when already interactive. Merely finding the Settings widget cannot establish completion of that native I/O.

The staged insertion checks the active, error-free session and exactly one current-process/session `harbor_interactive` record; awaits the existing public `interactiveHarbor` operation through `StudySession.capture`; then repeats the health checks and proves no extra interactive event was added. This drains earlier queued work without fabricating an activity or suppressing a storage error. The original guard-absence assertion, exclusive guard creation, refusal/error assertions, production withdrawal UI and separate-process withdrawal checks are byte-identical.

Author validation so far is source inspection plus exact insertion-only/suffix equality and hash checks in `stage-pins.json`. No Flutter analysis, host execution, or native retry has been performed for this staged repair. Root independently reviews the source and schedules validation.

Do not promote this harness before both Android default/enroll observations complete: the reviewed observer requires its archived harness to match the frozen candidate. After those observations are finalized, the lead may promote the separately reviewed test harness for fresh phone and Android withdrawal/reopen pairs. Record its new hash explicitly; retain the original failure and never label its unexecuted withdrawal as passed. No observer source binding or candidate source may be weakened.

## Subsequent scoped author analysis

The exact staged file was copied into a uniquely named candidate-workspace test file, analyzed alone with `flutter analyze --no-pub`, and removed after its hash was checked. Analysis passed with no issues. `author-analysis.json` binds the command, log and unchanged live/staged pins. No native retry has run. The original `stage-pins.json` remains the immutable pre-analysis handoff.
