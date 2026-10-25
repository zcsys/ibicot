# Local commerce fulfillment and signed ownership

These are executable local integrations, separate from the earlier frozen base report. They do not claim actual Apple/Google transactions, hosted operation, physical secure storage, native sharing, or store approval. The default service remains unconfigured for commerce, signing and downloads. No production credential or private signing key is included.

## Configuration and execution

Install the pinned optional provider dependencies in an isolated environment using `services/requirements-providers.lock`. The existing local development environment is `.tooling/services-venv`.

Run the local service with `.tooling/services-venv/bin/python -m services.tideglass_service --database /absolute/service.sqlite3 --config /absolute/service.json --port 8765`. It binds loopback only. Omit `--config` to retain the original standard-library service with unconfigured providers. `create_runtime(database, config_path)` returns the base `application`, configured `wsgi` wrapper and `vault` for a future TLS application server.

The JSON configuration and secret files must be owner-only regular files, owned by the executing user; symlinks and group/world permissions are rejected. Paths inside configuration must be absolute. Sections are optional, exact-key validated and never loaded from ambient credentials:

| Section | Required fields | Optional fields |
|---|---|---|
| Root | `version: 1` | `google`, `apple`, `admob`, `ownership`, `soundtrack` |
| `google` | `credentials_file`, `package_name`, `allow_test_purchases` boolean, `vault_key_file` | `push_audience`, `push_service_account` together |
| `apple` | `signing_key_file`, `key_id`, `issuer_id`, `bundle_id`, `root_certificate_files` array, `environment` (`Sandbox` or `Production`) | `app_apple_id` (required by Apple's verifier for Production) |
| `admob` | `callback_ad_unit_ids` array | None |
| `ownership` | `private_key_file`, `issuer` | `ttl_seconds` (1–86400), `allow_local_development` |
| `soundtrack` | `archive_file`, `sha256` | None |

Provider/application/region identifiers, trusted Apple roots, Google push subscription identity and store products require the operator's actual accounts. Configure real AdMob callback identifiers separately from the native SDK's full ad-unit ID. Never enable purchase presentation simply because a local fixture test passed.

`ownership.issuer` is the exact client service origin without trailing slash. HTTPS is required; an explicit development flag permits HTTP only for `127.0.0.1`, `localhost` or `::1`. Dart verification has the corresponding `allowLocalDevelopment` opt-in. The client public key map is pinned independently; the service does not supply a trust-on-first-use key endpoint.

## Token vault and recovery

A vault key file has `version: 1`, `active_key_id` and a `keys` object mapping key IDs to base64-encoded **distinct 32-byte** AES keys. No example usable key is supplied. Keep keys separately from database backups and application source.

`provider_tokens` stores opaque SHA-256 transaction identities, account UUIDs, key IDs, random 96-bit nonces and AES-256-GCM ciphertext. Associated data binds the format, account, transaction and key ID. A database uniqueness constraint rejects nonce collisions for a key ID. Google verifier token persistence participates in the same SQLite transaction as the verified purchase ledger, so a failed commit cannot leave a partial grant. Lookup always requires the owning account. Account deletion cascades through token rows and reconciliation/lease state; export never includes plaintext tokens or keys.

Rotation is explicit: prepare an owner-only replacement key file containing the old and new key material, select a new active key ID, then run `.tooling/services-venv/bin/python -m services.tideglass_service.ops --database /absolute/service.sqlite3 rotate-vault --key-file /absolute/new-keyring.json`. All ciphertext and the active key epoch change in one transaction. A before-commit failure retains the old state; after-commit response loss can be resolved by reopening with the new keyring. Old running writers reject the changed epoch. Stop/reconfigure the service to use the replacement keyring. Preserve retired keys for retained encrypted backups; do not delete them until those backups are securely expired. A restored old database requires its matching retained key(s), followed by explicit rotation. Missing or wrong keys fail closed without replacing stored ciphertext.

Backup erasure and deletion replay across an operator-restored historical backup remain operating obligations. A backup made before an account deletion still contains that account's encrypted data. This implementation does not claim to erase disconnected/offsite copies or automatically replay an external deletion log.

## Provider notifications and reconciliation

| Route/command | Trust and behavior |
|---|---|
| POST `/providers/apple/notifications` | Official Apple SDK verifies the signed notification and nested transaction. A known transaction is re-read through the App Store Server API before changing ownership. Signed test notifications grant nothing. |
| POST `/providers/google/notifications` | Google OIDC JWT signature, expiry, audience, issuer, verified email and configured push service-account identity are checked. Package binding is checked. The notification is a refresh trigger; its declared purchase state is never trusted. |
| GET `/providers/admob/callback` | Existing ECDSA verifier checks the original encoded query and independently commits the shared Support slot. |
| `python -m services.tideglass_service --database … --config … --reconcile --limit 100` | One bounded real-provider reconciliation batch. Refreshes pending/purchased/revoked rows, retries Google acknowledgement only after a durable grant, and records bounded failure backoff. No synthetic success fallback. |

Notification bodies are bounded to 256 KiB. Unknown or deleted transactions never recreate accounts or ownership. Google tokens are resolved from the protected vault. Fresh reads and acknowledgement preflight check current account/product/state/refund eligibility. A lost acknowledgement response is safe: the next provider read recognizes an already acknowledged purchase. Reconciliation has durable 60-second work leases, 60-second pending retries, six-hour settled refreshes, and exponential failure backoff capped at one hour. Run it periodically through the future operating environment; the application does not silently launch a scheduler. Summary counts exclude raw proofs, tokens and account identifiers.

Apple does not offer Google's server acknowledgement operation. Native StoreKit completion follows a verified durable grant. The worker reports `native_completion_pending`; it does not assert completion. A production completion-observation/reporting mechanism and real device drills remain open.

## Authenticated soundtrack delivery

All three routes require a bearer session in the **Authorization header**. Query credentials and redirects are unsupported.

| Route | Result |
|---|---|
| GET `/v1/commerce/capabilities` | `soundtrack_delivery_ready` and `ownership_lease_available`; no key or filesystem paths. Readiness checks a safely opened unchanged archive and feature switch before presenting a supporter offer. It does not require paid ownership. |
| GET `/v1/soundtrack/manifest` | Requires a current independently verified `soundtrack.01` entitlement. Returns `asset_id`, fixed `filename`, `content_type`, `bytes`, `sha256`, fixed same-origin `download_path`. |
| GET `/v1/soundtrack/download` | Same entitlement requirement. Streams at most 64 KiB per chunk with a 64 MiB archive bound, explicit length/hash and `private, no-store`. No ranges. |

The actual archive is `release/downloads/tideglass-original-soundtrack.zip`: **52,699,186 bytes**, SHA-256 **`620d671ae8817239f89802a9bead7cb584f1e44326aedd4d352ec69fb1f8de3a`**. Audio provenance remains in `release/audio/`. Startup checks the configured hash; each open rejects symlinks, unexpected file identity/size/time or shared-write permissions. Missing/changed assets fail unavailable. Publish assets immutably; changing them requires a new configured instance. The client must verify the received hash and length before exposing the downloaded file. An authorized in-flight transfer is not recalled by a later refund, and previously downloaded personal copies cannot be remotely erased.

## Signed leases and Dart secure cache

GET `/v1/entitlements/lease` returns `lease: {key_id, payload, signature}`. Payload and signature are unpadded base64url. Ed25519 signs the **exact decoded payload bytes**, not a client reserialization. The payload contains exactly:

| Field | Constraint |
|---|---|
| `v`, `issuer` | Version 1; pinned exact service origin |
| `account_id`, `linked_account_seed` | Current authenticated account and first linked main-game seed |
| `issued_at`, `expires_at` | UTC seconds; positive interval, at most 86,400 seconds; also capped by the earliest included entitlement's remaining provider freshness |
| `revision`, `lease_id` | Monotonic account issuance revision; unique lease identifier |
| `entitlements` | Only the four shop cosmetics, `pass.01`, `soundtrack.01`; never wallet/XP modifiers |

Signing key file fields are `version: 1`, `key_id`, `private_key` (base64 raw 32-byte Ed25519 private key). Rotate using independently distributed client public-key pins; retain old public verification keys for at most the accepted lease lifetime. A signed empty lease advances the same revision and revokes cached ownership. Server clock rollback pauses issuance; future-dated purchase observations cannot mint authority. Already issued offline leases cannot learn about a subsequent refund until refresh; the maximum exposure is their bounded remaining lifetime.

`game/platform/lib/signed_entitlements.dart` exposes `SignedOwnershipVerifier` and `SecureOwnershipLeaseCache`. Supply secure read/write callbacks backed by device-only Keychain/Keystore, the configured public-key map, and current account/main seed. Call `accept` on a fresh server lease, `load` on startup, `checkpoint` before backgrounding and `clear` on logout or online revocation. `currentEntitlementIds` and `remaining` enforce account/seed, wall-clock rollback, monotonic expiry and optional native elapsed-clock evidence on every read. Persisting a new/empty lease must succeed before access is exposed. High-water revisions remain after clearing to reject replay.

A `TrustedDeviceTime` value requires a native elapsed clock that includes sleep and a `bootId` that identifies **this device and this boot**. Storage must be excluded from backups and migration; a copied boot counter is not a device identity. A changed boot or decreasing native elapsed clock invalidates restored grants. Without that trusted evidence, signed offline grants work within the current process only; reopening requires a fresh online lease. Secure wall-clock high water alone cannot prove elapsed time while the process was dead. No native clock bridge or physical-device guarantee is claimed by this package's tests.

## Evidence and remaining release gates

`services/evidence/fulfillment-author-verification.json` records source hashes, exact commands, test outputs and archive identity. Tests exercise real local HTTP/SQLite, AES-GCM/Ed25519/RSA/ECDSA primitives, fault paths, provider response contracts, Python-to-Dart signature compatibility and bounded archive delivery. Provider responses/signing identities are explicit test fixtures; no real store purchase, refund or ad was performed.

Still required: independent review; actual store/app/product/provider credentials and notifications; TLS hosting and request/process/concurrency limits; periodic reconciliation and alerts; secret distribution/rotation/retained-backup erasure drills; native account-bound boot evidence and device secure-storage tests; store pending/restore/refund/reinstall tests; native download/share qualification; Apple completion reporting; live-operation and store-release approval gates.

Primary implementation references: [AES-GCM](https://cryptography.io/en/stable/hazmat/primitives/aead/), [Ed25519](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/), [Dart cryptography](https://pub.dev/packages/cryptography), [Google authenticated push](https://docs.cloud.google.com/pubsub/docs/authenticate-push-subscriptions), [Google RTDN](https://developer.android.com/google/play/billing/rtdn-reference), [Apple's official server library](https://github.com/apple/app-store-server-library-python).

## Key identity binding and legacy recovery (QA016)

Each vault key ID now has a persistent domain-separated HMAC-SHA256 commitment to its AES key material. It contains no account identity or raw key. Empty vaults retain these configuration commitments after account/token deletion. Startup rejects changed material under a known ID; every write and rotation rechecks the binding. Rotation also rejects a stale operator instance after another rotation changed the active epoch.

A database from before this binding table can upgrade automatically only when every token ciphertext for a previously unknown key ID authenticates with the configured key. One valid row is insufficient. Failure preserves the prior database transaction. Back up the database and keys before any upgrade or rotation.

An old active epoch with no remaining ciphertext cannot prove which key material was original. Ordinary startup and same-ID rotation therefore fail closed. Recover by explicitly rotating to a **new key ID and new key material** with the existing `rotate-vault` operator command; its old unverifiable ID is permanently retired. A new ring containing only the new key suffices when there are no encrypted rows. Preserve the original database and old key file for any older backups; never overwrite an ID with replacement material. A backup containing old token rows still requires its matching old key. No AES key is supplied or generated by this repository as production configuration.
