# Clock-protocol repair: author handoff

The staged test-only repair addresses all three mixed-clock predicates. It captures prospective same-run raw clock brackets, validates host wall/monotonic consistency, replays the hash-pinned raw model on recovery, and binds pre-kill exports through actual live → export → live observations before the actual UI tap. Permission-change death may follow command completion; its measured interval must be consistent with the actual tap → OFF observation interval and independent fresh PID/UI/reason evidence. The original native180s, save/source/permission/pending and framework gates remain intact.

Only these files are proposed for promotion after independent review:

| File | SHA-256 |
|---|---|
| `tool/reminder_restart.py` | `5de097fd817e7fb49573e3a73c44ec805182d8dc107f1c86b8546bbb81dc63d0` |
| `tool/test_reminder_restart.py` | `a26fbae8507bb8461859467d867401bb66289846b74a98e8d9783dc0b4ac82b7` |
| `tool/test_reminder_clock.py` | `11b003659a4798631d3d2a829fccd53fb588be9b8beb7185558498d750c1a2c7` |

`clock-protocol.patch` SHA-256 `4bb2599c43ca3fee6c2adfc74700e1ee7cd49f293105e30eb06d452097aa39fb` reconstructs these exact files against the preserved baseline; a disposable git-apply control passed. `verification.json` SHA-256 `9174d82701ce127801c11210ec901a77df3823fb63302c896098d4d29568bdaa` pins all author evidence. `OPERATOR_PROTOCOL.md` contains the exact fresh packet additions and measurement boundaries.

Validation: **67 host methods passed** (43 existing,24 focused clock/causal methods), with exact command and working directory in verification. Existing checkpoint/permission/recovery/log/fixture predicates are unchanged at AST level. **42 preservation/arithmetic checks** pin37 input files; the actual post-event diagnostic integer arithmetic reproduces, but it is not retroactive calibration. The rejected f8d460 packet is explicitly refused for its absent clock model and remains untouched.

The live helper, runner, Dart harness and existing test remained at baseline hashes. No live files, Flutter, device, production, metadata or scope changed. This handoff is author evidence only; QA/root review and a fresh preparation/recovery remain necessary. The old failures and all previous stage seals remain preserved.

Reproduce from `/Users/csys/Desktop/ibicot/idle`:

```sh
PYTHONPATH=release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/staged/tool:tool python3 -m unittest -v test_reminder_restart test_native_reminders test_reminder_clock
python3 release/native-notifications/revoked-clock-repair-20261025T165159.000038Z/author_verify.py
```

The second command is read-only against live/prior inputs, writes only this author folder, and is unnecessary if reviewers prefer to replay the same checks in their own independent folder. Source writes are stopped.
