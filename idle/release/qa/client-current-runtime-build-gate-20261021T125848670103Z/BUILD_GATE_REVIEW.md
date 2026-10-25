# Independent current-runtime build-gate review

Result: the explicit `current-runtime-verifier-test` host gate is correctly wired and its failure prevents native export. No source repair requested for this change.

Reviewed source pins:

- `tool/build_native.py`: `1fca5f766c6bd816f55fc0aefafe1e3dfb8e66b91e83e1dcb275d48f13cada1d`.
- `tool/test_native_candidates.py`: `7a69e129772036ee087b8e05116bb25ddb198f0ac3b5dbaf9c6fc9132cd38e35`.
- Repaired runtime verifier: `f63c8bb1f97e5e486fceb9b5831e416efae0d0f4bc73fe248079ca5e3a7cc834`.

I inspected the actual gate and its author regression. The gate explicitly discovers `test_current_runtime_verification.py` alongside, rather than through, `test_native_*.py`; runs in the frozen candidate workspace; records its command/exit status; and appends its failure before the early return preceding native export. The author's failing fixture executes a real Python subprocess and asserts empty export results and no native command.

Independent execution:

| Check | Result |
| --- | --- |
| Existing `test_native_*.py` suite | 24 passed |
| New `game/qa/review_current_runtime_build_gate.py` | 3 passed |
| Failed frozen verifier with passing live replacement | Gate failed; no export command reached; failure log retained |
| Passed frozen verifier with failing live replacement | Gate passed; export reached only the test's interception boundary; no artifact or launch success fabricated |
| Runtime-verifier discovery alongside candidate and study patterns | All three explicit commands present |

The positive export boundary returns synthetic exit 99 without executing any SDK command. Only isolated Python unittest subprocesses ran; SDK version/pub/build calls were intercepted and no Flutter, native build, simulator, emulator, device, signing or network operation was performed. The fixture verifies frozen source hashes remained unchanged. The initial independent probe compared `/var` and `/private/var` paths lexically on macOS and failed its own cwd assertion; that initial source/log remains preserved. Resolving both fixture paths repairs the probe without changing author source or weakening its candidate-isolation assertion. Final source/log hashes are in `verification-final.json`.

The Python process emits a ResourceWarning for the builder's existing process-lifetime lock handle when `main()` is invoked as an in-process test. It does not change the tested exit/gate behavior; normal CLI exit releases the descriptor. This review makes no native-execution or staged-Dart-compilation claim. The gate is selected by `--host-checks`; snapshot-only and deliberately unqualified exports remain outside this gate's claim. The conditional command discovery is compatible with older candidates that lack this suite; the current candidate includes the exact test file and this review does not claim missing-file enforcement for historical candidates.

`current-reviewed-pins.json` now preserves the initial author pin while naming the repaired runtime source and bounded pending-native status. No acceptance status or original requirement was changed by this review.
