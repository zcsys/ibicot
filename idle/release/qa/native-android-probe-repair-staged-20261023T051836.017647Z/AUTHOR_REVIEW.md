# Android fixture probe exit-status repair

The native verifier used `adb exec-out run-as … test` for boolean path checks. On the owned API35 emulator, both `false` and `test -L` against a normal directory returned host exit0 through exec-out; the same commands via adb shell returned1. The runner consequently rejected a real directory as a symlink before its intentional SIGKILL. The failed run remains failed, and its dependent recovery was not attempted. The held app was explicitly stopped afterward; this was not recorded as a successful preparation.

The staged runner changes exactly one line: boolean/path probes use `adb shell`, retaining the existing requirement for exit0/1 with empty stdout/stderr. The exact allowlisted path, each symlink/type/readability/traversal guard, bounds and `exec-out` binary transfer remain unchanged. No production code, live runner, live harness, observer or frozen candidate was changed.

Final source: `d1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847`. Original: `d849ab8feb642eb1b988f9a6d82558491b7ebef4c63768fb4fa132f49edf3804`. See repair.patch and verification.json for exact evidence pins. An initial comment-only explanation was removed to make the final diff exactly one line; that intermediate source/log remains explicitly named.

`python3 run_author_tests.py` reproduces31 archived original methods plus14 new methods. Controls cover the observed lost-false-status counterexample, raw binary fidelity, ancestor/final symlinks, missing required/optional files, wrong file/directory type, unreadability, untraversable parents, exit2, unexpected stdout/stderr, timeout, byte bounds and path escape. All45 pass. `--before` intentionally fails the key counterexample under the original runner.

`run_actual_readonly.py` read only the already stopped failed synthetic fixture: its checkpoint exactly matches the original native marker, an optional absent file is None, and traversal is refused without a command. It neither reruns nor reclassifies the failed native case. The original transport observations and explicit stop are in execution-3b00-20261023T040612.562001Z/android-fixture-probe-20261023T0517Z.

Different-author review and explicit collector binding approval remain required before promotion. This packet supplies no new native passing test, observer qualification or release acceptance.
