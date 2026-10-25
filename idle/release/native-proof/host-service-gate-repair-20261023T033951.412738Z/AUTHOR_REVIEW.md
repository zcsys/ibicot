# Candidate host service gate repair

Author: `/root/native_verifier`. Different-agent review and the lead’s new-candidate decision remain required. This work repairs the actual `operations-test` environment failure from candidate `a052a44053472684ae5b60ce2b4fd1e9be0fe77f518dfd2a99a80add79094d4e`. It does not repair or rewrite that failed candidate’s record.

## Change

`tool/build_native.py` keeps the independent standard-library service suite on the host Python. Operations now uses the pinned `.tooling/services-venv/bin/python`, because the suite explicitly exercises the real vault and signer layouts and imports `cryptography`. The existing candidate-captured `check_provider_environment.py` validates the exact candidate-captured provider lock **before** operations or providers execute, including when only the operations suite is present.

Missing, non-executable or mismatched environments fail the host gate. Dependent suites receive explicit `blocked` records and are never represented as executed or passed. There is no system-Python fallback, installation, dependency relaxation, skipped vault assertion or test substitution. Actual suite failures remain failures and stop native export; independent suite evidence still completes where its prerequisites are valid. The provider soundtrack fixture remains required and hashed.

The change is limited to three files: the build runner, a fixture-only update to `test_native_candidates.py` to provision its disposable discovery interpreter, and new focused `test_native_service_gate.py`. Exact before/source copies and `repair.patch` are archived here. No service implementation, service tests, dependency lock, game source, original acceptance criterion or program status changed.

## Author verification

| Check | Result | Evidence |
|---|---|---|
| Existing native candidate/verifier tests plus 11 new orchestration methods | 35 passed | `focused-regressions.log` |
| Actual base service suite from the frozen a052 workspace, using host Python | 65 passed | `real-candidate-service-gates/services-test.log` |
| Exact existing dependency lock validation in pinned services venv | All 19 package versions match | `real-candidate-service-gates/provider-environment.log` |
| Actual operations suite from the frozen a052 workspace, using qualified pinned venv | 59 passed, including the previously failing real vault/signer layout test | `real-candidate-service-gates/operations-test.log` |
| Actual provider suite from the same workspace | 36 passed | `real-candidate-service-gates/provider-test.log` |
| Final repair source pins before/after author checks | Unchanged | `author-test-source-before.json`, `author-test-source-after.json` |
| Failed a052 evidence and all 1,186 immutable source inputs | Unchanged | `integrity.json` |

The new tests use real disposable Python subprocesses to prove execution order and nested test discovery, operations-only qualification, absent/non-executable/mismatched environments, missing provider fixture, independent service/provider/operations failure handling, and suppression of native export after an operations failure. Their environment checker is an explicit tiny test stand-in; the separate actual candidate run above uses the real lock checker and real installed packages. The native export command is intercepted only in the orchestration regression; no Flutter/native command is run by this author assignment.

The first regression attempt accidentally named a parameterized fixture helper `test_file`, so unittest tried to execute it as a test. The failed source/log are preserved as `initial-service-gate-tests.py` and `.log`. Renaming that helper to `write_suite` corrected test discovery without changing production behavior or assertions. Existing build-runner lock-handle `ResourceWarning` messages remain visible in in-process test logs; they are not hidden or a claimed part of this environment repair.

## Scope and handoff

This supports M0-08/S40 reproducible-build gates and M5-04/S27/S30/S37 operations verification. It does not accept any broader original package criterion, provider integration, hosted operations, physical-device behavior, release, store or human-study gate. The original failed full host run remains failed even though its unchanged service subset now passes with the corrected orchestration.

Reviewer should inspect the exact diff, reproduce the 35 focused methods and actual operations/lock checks, and probe a fail-closed environment path. The lead then combines this with the independently reviewed calibration regression repair, declares a new candidate, and reruns the full candidate host gate before any of the five native exports. No Flutter or device lane is held by this author after handoff.
