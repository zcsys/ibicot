# Account and cloud presentation — author handoff

2026-10-16. Implemented `game/mobile/lib/service_settings.dart` with the real `NativeServicesManager` and `TideglassServiceClient` APIs. This report records author checks, not production service acceptance.

## Behavior

- Local guest play and export remain available with the default empty service configuration. No account, upload, analytics consent, or branch replacement happens automatically.
- Creation requires explicit cloud consent. The account ID and recovery code are shown before upload; a secure, persisted acknowledgement locks uploads until the player confirms retention. Recovery never imports or uploads the guest harbor.
- Cloud listing shows actual branch/save IDs, revision, exact UTC settlement time, and the cloud generation. Upload and branch selection use the reviewed generation for compare-and-swap. A conflict cannot call local import or merge balances. Selection downloads the complete save, selects remotely, then delegates local import to the host's backup-preserving callback. An import failure after remote selection is reported distinctly.
- Recovery replacement generates and displays the new code before sending it. Current-code input and retention confirmation are required. A lost response explicitly leaves the outcome uncertain and instructs retention of both codes.
- Online session revocation differs visibly from forgetting this device's sign-in without network. Account deletion requires current recovery code and explicit confirmation; neither action invokes a gameplay mutation.
- Telemetry has separate opt-in. Refusal stops local collection immediately. Pending remote deletion remains visibly pending until a successful retry. The manager owner repaired account-scoped privacy state after cross-account review.
- Account/local export provides a bounded selectable preview and an explicit copy of the complete text. It does not claim to have saved a file. Session credentials and recovery codes are never added to gameplay exports or logs. Secret-input suggestions/autocorrect are disabled.
- Fullscreen review forms scroll at 320 logical pixels and 200% text. Controls meet the theme's 48px minimum. Service outcome text is a live region at the top, and completion scrolls to it.

## Interface

`ServiceSettings({required NativeServicesManager manager, required Future<String> Function() onExportHarbor, required Future<void> Function(String) onImportHarbor, Future<void> Function()? onRefreshEntitlements})`.

The host initializes/owns the manager and owns atomic import, preserved local backups, credentials and actual endpoint configuration. The screen never merges saves or writes account secrets to game state.

## Verification

`../../tool/flutter test test/service_settings_test.dart` — **14 passed**.

Coverage includes explicit consent/retention, secure acknowledgement across manager reload, guest preservation on recovery, successful CAS branch selection/import, CAS conflict, confirmed upload, failed import after successful cloud selection, lost recovery-rotation response, revocation versus offline forget, deletion guards, telemetry offline deletion/retry, and real returned account export.

One widget test uses an actual loopback HTTP server and the production HTTP client: only `POST /v1/accounts` is observed after explicit UI consent; the returned code is shown, the bearer token is not, and no upload occurs. All other service responses are explicitly named fixtures exercising the real manager and UI. No test substitutes store ownership.

`../../tool/flutter analyze lib/service_settings.dart test/service_settings_test.dart` — **no issues**.

## Remaining acceptance boundaries

A deployed service, device Keychain/Keystore behavior, app-store transactions, store consent screens, and end-to-end cloud restoration on physical devices are separate release gates. These checks establish client behavior and real loopback transport only. Root owns final app/bootstrap integration and independent review.
