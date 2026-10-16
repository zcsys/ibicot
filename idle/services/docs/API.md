# API v1 contract

Every body is JSON with exact required/optional keys. Unknown keys, duplicate JSON keys, non-finite values, oversized requests and unrecognized event fields are rejected. Authenticated calls use `Authorization: Bearer <session token>`. Request bodies, tokens and proofs are not logged. Responses include a diagnostic `request_id`; do not send credentials when quoting it to support. Production origins must use TLS. The application rejects query strings and chunked transfer bodies; the Dart client supplies Content-Length.

| Method and path | Request | Result |
|---|---|---|
| `GET /health` | None, unauthenticated | API/storage health and actual verifier configuration flags |
| `POST /v1/accounts` | `consent_cloud: true` | `account_id`, `session_token`, `expires_at`, one-time `recovery_code`; guest progress untouched |
| `POST /v1/sessions` | `account_id`, `recovery_code` | New expiring device session; does not import progress |
| `POST /v1/sessions/revoke` | `all_devices: bool` | Current or all device credentials revoked |
| `POST /v1/account/recovery-code` | Current `recovery_code`, pre-retained `new_recovery_code` | Atomic rotation, all old sessions revoked, fresh session |
| `GET /v1/account/export` | None | Account metadata, full snapshots, ownership, claims, retained telemetry; no credential hashes/tokens/raw purchase proofs |
| `DELETE /v1/account` | `recovery_code`, `confirm_delete: true` | Live account rows and dependent data erased; local guest data and store purchases untouched |
| `GET /v1/cloud` | None | Generation, selected save ID, immutable snapshot metadata and tip markers |
| `POST /v1/cloud/snapshots` | `export_json: string`, `expected_generation: integer` | Candidate preserved; selection advances only on current generation plus direct selected parent (or first snapshot); otherwise explicit selection required |
| `GET /v1/cloud/snapshots/{save_id}` | None | Exact checksummed `export_json` belonging to this account |
| `POST /v1/cloud/select` | `save_id`, `expected_generation`, `confirm_selection: true` | Compare-and-swap selection; no snapshot is deleted or merged |
| `GET /v1/entitlements` | None | Independent current entitlement projection, linked daily seed, verification IDs and purchase lifecycle metadata |
| `POST /v1/purchases/verify` | `platform: apple or google`, opaque `proof` | Verifier-controlled pending/purchased/revoked observation; no client-supplied status or product is trusted |
| `POST /v1/support/claims` | `day_id`, `slot: 0..5`, `route: briefing or ad`; ad-only `proof` | Stable once-only claim receipt/source identity for that account/day/slot |
| `GET /v1/support/claims` | None | Current server-account-day claims and acknowledgement status |
| `POST /v1/support/acknowledge` | `receipt_id`, uploaded `save_id` | Marks delivery only when the snapshot contains the matching token source/day/slot; does not grant currency |
| `PUT /v1/telemetry/consent` | `enabled: bool` | Consent revision; false deletes retained account telemetry |
| `POST /v1/telemetry/events` | `consent_revision`, 1..100 `events` | Counts newly accepted and duplicate IDs |
| `GET /v1/features` | None | Optional-service switches only; no economic configuration controls |

`CloudIndex.snapshots` contains save ID, branch ID, revision, parent ID, settlement cursor, checksum, received time and `is_tip`. An orphan parent is allowed because local commits may outnumber cloud uploads, but cannot automatically replace an existing selection. A known parent must match its exact branch/revision and must not have a later settlement cursor than the child. Stale uploads preserve the candidate; stale **selection** returns HTTP 409. Existing save IDs are immutable and must have the same checksum on retry.

The server verifies the envelope and SHA-256 checksum, not the opaque core economy. No snapshot or local commerce-cache entry grants paid ownership. The native client must validate its own content and state schema before importing.

## Claims and commerce

Support source IDs match the core contract:

- `briefing:{seed}:{day}:{slot}`
- `ad:{seed}:{day}:{slot}:{sha256_verified_provider_transaction}`

The service day uses server UTC plus the first linked fixed account offset. Future/expired-day claims fail. No-fill, verifier failure, feature disable, or a failed request consumes a new slot. An already-granted slot returns its original receipt even when a different route is retried. A receipt is persisted before native delivery; apply it through the core's same-slot duplicate checks, save atomically, upload, then acknowledge. A lost response is recovered by requesting the same slot. Acknowledgement is a recovery/diagnostic marker; the server never replays a reward itself. Offline briefing claims remain local and must not create an extra slot when reconnected.

All configured products are cosmetic: four shop skins, `pass.01`, or the four same skins plus `soundtrack.01`. Product IDs are provisional `dev.tideglass.*` values; no price is invented. Native store localized prices remain the storefront source. Provider implementations must validate app ID, environment, account binding, product, transaction identity, signature/server API authenticity and monotonic revocation order. No provider implementation or credentials are bundled. The test-only synthetic verifiers cannot be selected by the command-line runner.

A purchased observation is committed before `Application.reconcile_acknowledgements()` performs external acknowledgement. A failed acknowledgement leaves a durable pending item and can be retried. An acknowledgement may be sent again after a lost worker response; the real store adapter must use the store's idempotent acknowledgement behavior. Pending never grants; duplicate verified observations reuse the receipt; stale observations cannot undo a newer refund. Refunds remove only the affected purchase's contributions: a second valid purchase may independently own the same cosmetic. Ownership observations expire from the authorization projection after 24 hours until reverified. Raw proofs are not retained, so a production reconciliation worker needs configured provider transaction lookup and authenticated notification integration.

No HTTP endpoint changes pass XP. Contract XP and economic Support consumption belong to one selected core branch. Store cosmetics are unioned only from independently verified live transactions, never from two gameplay snapshots.

## Telemetry

Each event contains `id` (UUID), `session_id` (UUID), `name`, `observed_at` (UTC epoch seconds), and `properties`. The service accepts observations from at most seven days ago and at most five minutes ahead. Allowed names: `session_start`, `session_end`, `session_crash`, `resume_result`, `save_result`, `rechart`, `chapter_complete`, `dossier_complete`, `contract_claim`, `service_result`.

Allowed property keys: `build`, `platform`, `device_class`, `flow`, `outcome`, `chapter`, `duration_seconds`, `schema_version`. `platform` is required and is one of `ios`, `android`, `macos`, `test`. Labels are bounded identifier strings; freeform text, email, save blobs, wallets, receipts and credentials are not event fields. Per-account storage is at most 5,000 events and 90 days, with a scheduled prune command for inactive accounts. Reusing an event UUID with different content returns 409. Consent is off by default; a stale consent revision cannot silently turn collection back on.

## Errors and bounds

Common errors: 401 `authentication_required`; 403 `telemetry_consent_required` or missing recovery confirmation; 409 `cloud_revision_conflict`, `snapshot_identity_conflict`, `account_day_identity_conflict`, `cloud_quota_reached`, `support_day_expired`; 413 body/snapshot size; 429 rate limited; 503 `verification_unavailable`, `feature_unavailable`, `storage_unavailable`. Generic failures disclose no stack or sensitive body.

Limits: 2 MiB per snapshot; 64 MiB and 10,000 snapshots per account; 30-day session expiry; eight active devices; six daily Support slots; 64 KiB provider proof; 20 identity requests or 600 ordinary requests per source-address hash/minute. Rate hashes are removed after two minutes. Quota failure preserves both local and cloud copies; no automatic history pruning erases an unresolved branch. These are operational safeguards, not paid capacity upgrades.
