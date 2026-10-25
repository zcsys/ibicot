# Actual Settings revocation packet

This is a prospective packet format, not evidence that any tap occurred. The native owner uses the already approved actual Android UI method. No permission API, appops, settings mutation, data reset or host kill substitutes for the OS permission-change kill.

Start a fresh `revoked-prepare` run with a fresh pair run ID. Follow the actual permission prompt if one appears. A previously allowed state verifies that state rather than a new prompt. The harness persists its synthetic save and checkpoint, then opens actual app notification Settings. **Wait for the runner's `REVOCATION CHECKPOINT CAPTURED` line before tapping OFF.** A raw native action line alone does not confirm the host captured the pre-kill bytes. Do not return to the app or relaunch it during preparation.

Capture the actual enabled ON switch, Tideglass label/icon, activity route and bound PID. Record UTC milliseconds immediately before and after the observed actual tap, its complete argv/exit result, then capture the OFF switch and raw screen. Preserve raw PNG/XML bytes. Do not crop, rewrite, annotate or replace them. The packet is in a separate fresh directory; the preparation report remains immutable.

`operator.json` fields are:

| Field | Required source |
|---|---|
| `verification_id`, `candidate_fingerprint`, `harness_sha256`, `scenario`, `run_id`, `device_label`, `platform` | Exact fresh preparation context; scenario is `revoked-prepare` |
| `process_id` | Exact preparation PID seen alive before the OFF action |
| `before_utc_ms` | Actual pre-action observation time |
| `action_started_utc_ms`, `action_finished_utc_ms` | Actual command start/end, enclosing the OS permission-change kill |
| `after_utc_ms` | Actual OFF observation time |
| `tap_argv` | Actual targeted `adb -s <emulator> shell input touchscreen tap <x> <y>` argv |
| `tap_exit_code` | Actual command result, must be zero |
| `files_sha256` | Exactly `before.xml`, `after.xml`, `before.png`, `after.png`, `settings-activities.txt`; hash each retained raw file |

The selected switch must be enabled, ON before, OFF after. `settings-activities.txt` must show `android.settings.APP_NOTIFICATION_SETTINGS`, launched from `dev.tideglass.game` and its bound MainActivity process. The point must lie inside the actual switch's observed bounds. A click on this switch's parent row is not silently accepted by this bounded checker; the native owner should use the observed switch position as in the previous real attempt. Raw screenshots also need independent visual review; machine hash/PNG-header checks alone do not establish their meaning.

Preparation can end with `status=os-interrupted-awaiting-ui-evidence`, `passed=false`, `errors=[]` only when exact pre-kill capture and actual fresh PID/reason/time evidence exist. Exit code zero here denotes a qualified interruption checkpoint for handoff, **not a passed integration test or completed revoked scenario**. The original five scenarios are unchanged. An absent/changed checkpoint, unexpected test assertion, unsupported kill behavior or missing expected driver disconnection stays failed. No old failed `revoked` run is eligible as a predecessor.

After independent review of the new preparation and UI packet, the native owner may run `revoked-recover` with the same candidate, device, label and pair run ID plus:

```text
--predecessor <exact-new-preparation>/verification.json
--revocation-evidence <exact-new-operator-packet>/operator.json
```

The recovery evidence directory is fresh. Standard same-package Flutter launch/build may occur with app data retained; no uninstall/reset is allowed. The runner verifies denied permission and unchanged predecessor bytes before launch, and the new PID checks again before production initialization. Recovery is an explicitly launched second process; it is not described as a same-process app-icon resume. Capture the actual new UI/process state in the native review. If a permission prompt appears during the explicit re-opt-in action, deny it through observed actual UI. If the OS denies immediately, record that outcome without claiming a prompt was shown.

The native runner preserves both compiled artifacts and source pins across each phase. A successful recovery qualifies this tested two-process path only. The separate real delivery test retains its 720-second observation bound, actual delivered-record gate and framework completion gate.
