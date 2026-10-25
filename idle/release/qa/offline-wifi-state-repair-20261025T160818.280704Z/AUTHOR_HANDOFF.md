# S02 Android Wi-Fi state parser correction — staged only

The actual first attempt completed the native natural-start flow, but the host wrapper correctly failed closed on unrecognized `wifi_on=3`. It remains failed: `integration-android-offline-20261025T160235.910710Z`, report SHA `db58df8f44328ee257b34f97970133dc7ac9f96ead1a0753db9f90a337efa8c8`. No dependent reload ran. Native separately restored the actual baseline through the reviewed UI procedure and sealed its operator checkpoint `e53d301abb8c65b4cde4fd8ba02ea51a32ed346384806ad95da72103cff296e4`.

## Exact source basis

The [Android 15 r1 AOSP WifiSettingsStore source](https://android.googlesource.com/platform/packages/modules/Wifi/+/refs/tags/android-15.0.0_r1/service/java/com/android/server/wifi/WifiSettingsStore.java) defines persisted Wi-Fi values 0 disabled, 1 enabled, 2 enabled in airplane mode, and 3 disabled by airplane mode. The Android 15 symbol is `WIFI_DISABLED_APM_ON`; older AOSP calls the same value `WIFI_DISABLED_AIRPLANE_ON`. See source lines 48–57, 186–188 and 341–344. The tag-specific source is archived in `aosp/` with its URL and hash; curl used ordinary TLS verification. It describes persisted preference semantics, not standalone proof of app network unavailability.

## Minimal proposed change

Only `offline_support.py` changes: accept raw 3 solely with airplane=1, then allow raw 0 or 3 in offline rows. Raw 3 stays 3 in results. Raw 1 cannot qualify offline, raw 2 and unknown values remain rejected. Airplane=0 with raw 3 fails. Before/restored rows still require airplane=0 and an active default network.

No normalization or additional admissions: exact raw radio restoration equality, API35 identity, source binding, containment/symlink checks, native/driver completion, exact predecessor identity and checkpoint, distinct process, app socket failures, healthy bound listener, default-network absence, actual purchase/save/reload assertions, and three reconnection probes are unchanged. Runner and Dart harness are byte-identical to the independently reviewed style stage. No live files or canonical statuses changed.

## Verification and limits

All 39 focused pure methods pass: 26 existing behavioral cases and 13 additional regression methods covering actual raw receipt parsing, original rejection reproduction, synthetic start/reload with raw 3, wrong context, enabled/override/unknown states, network still active, reachable app endpoint, missing/failing listener health, missing reconnection, unchanged restoration/predecessor code, and exact source/evidence pins. The old 27th metadata-only test is preserved but deliberately excluded because its historical source-before record predates reviewed program-note changes; the new regression verifies current exact pins instead. No runtime assertion was removed.

`actual-receipt-pure-replay.json` is explicitly a counterfactual diagnostic under the staged helper: the existing 116 app samples pass its pure validator. This does not amend the old failed report, grant a successful predecessor, establish reload/restoration, or accept S02. A fresh independently reviewed start/reload pair with a new run ID remains required.

Independent reproduction (from this folder):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 run_pure_checks.py
```

Parent must review before native uses the new folder's unchanged runner/harness with the proposed helper. QA authored this test-only correction and does not independently approve its own change. No Flutter, device operation, sockets or production changes were performed in this author task.
