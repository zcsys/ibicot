# Native ownership and soundtrack integration

Implementation state on 19 October 2026: integrated in the real bootstrap, account service and collection UI. Author host/loopback checks pass. Independent integration and fresh native candidate checks are underway. No real store transaction, production signing identity, public service or physical-device qualification is asserted.

## Deployment contract

| Compile definition | Meaning and default |
|---|---|
| `TIDEGLASS_SERVICE_URL` | Exact HTTPS service origin; empty keeps optional services unavailable. |
| `TIDEGLASS_LOCAL_SERVICE` | Explicit loopback HTTP allowance for local development; false by default. |
| `TIDEGLASS_OWNERSHIP_PUBLIC_KEYS` | JSON object of key ID to base64 raw 32-byte Ed25519 **public** key. No private key belongs in a native build. |
| `TIDEGLASS_COMMERCE` | Enables configured native store offers; false by default. |
| `TIDEGLASS_SUPPORTER` | Allows the supporter bundle only when authenticated soundtrack capability is also available; false by default. |
| `TIDEGLASS_REWARDED_ADS` / `TIDEGLASS_REWARDED_AD_UNIT` | Separate explicit ad configuration; disabled/empty by default. |
| `TIDEGLASS_MEASUREMENT_BUILD` | Measurement build label; defaults to `development`. Freeze a meaningful release/study label before collecting evidence. |

Production bootstrap always sets `signedOwnershipRequired: true`. Missing or malformed public pins cannot fall back to unsigned HTTP ownership. Guest play and local persistence do not wait for optional network or secure-storage initialization. Test-injected managers can retain the earlier direct service-observation path; that injection is not the production configuration.

The exact client origin is the lease issuer. Configure the corresponding server signer independently using [FULFILLMENT.md](../../services/docs/FULFILLMENT.md). The four compile-configuration checks in [bootstrap-ownership-config-evidence.json](../../release/bootstrap-ownership-config-evidence.json) execute the actual bootstrap with valid, missing, malformed and default definitions. All use a public-only test pin and no real service account.

## Ownership lifetime and account changes

The current session, linked main-game seed, signed revision, expiry and elapsed-clock evidence jointly determine presentation. Game saves and saved appearance preferences never grant paid ownership. Refreshes are guarded against replacement sessions, changed seeds and newer ownership requests. A fresh online observation clears old cached grants before requesting its matching signed lease; an unavailable lease then fails closed. A primary service outage may retain only an already valid, bounded signed lease.

Startup attempts a secure restore before an optional online refresh. The bridge notifies the existing service listeners when its evidence changes. Background transitions attempt a checkpoint; later reads still charge elapsed time from the last valid anchor. Logout clears grants while preserving anti-replay high water. Confirmed account deletion erases the corresponding secure record and reports cleanup failures. These operations do not remove the local guest harbor.

Android evidence can span a process restart within the same device boot. Apple evidence is process-scoped, so cold restarts require fresh online ownership verification. Temporary missing samples hide ownership until a valid refresh. Details, required-reason privacy declarations and physical-device limitations are in [OWNERSHIP_CLOCK.md](../../game/platform/OWNERSHIP_CLOCK.md).

## Supporter offer and export

The supporter offer bundles the existing four shop appearances and soundtrack. It adds no economic value. The UI uses the native store's product title and localized price. Capability is checked when loading offers and again before purchase. A failed or stale capability response cannot present the bundle as deliverable. Owning its four appearances separately does not pretend the soundtrack is owned.

The player explicitly selects the soundtrack export action. The client captures the account/session, fetches a bounded manifest from a fixed same-origin route, streams no more than 64 MiB to a private temporary directory, and checks exact size and SHA-256 before renaming the completed file. Redirects and query credentials are rejected. Account replacement, timeout, integrity failure and write/cleanup failures report failure. A failed transfer is removed when the filesystem permits; the busy flag is released even when cleanup itself fails.

Only the verified ZIP reaches the native share/save sheet. No token or account data is placed in it. Cancellation is reported as cancellation; an unavailable platform result does not claim that a file was saved. The receiving app may continue reading after the sheet closes, so successful downloads remain in the OS cache. Prior exported copies cannot be recalled after refund or deletion. Native sheet behavior uses [share_plus](https://pub.dev/packages/share_plus); actual simulator and physical-device behavior have separate evidence gates.

## Verification boundaries

- `release/ownership-clock-mobile-integration-tests.log`: 45 combined author host checks at the recorded source state; later response-status guard and bootstrap configuration have separate evidence.
- `release/soundtrack-delivery-client-tests-v3.log`: ten real loopback HTTP/file probes, including bad integrity, redirect, account replacement, absolute JSON timeout and an actual permission-denied cleanup fault.
- `services/evidence/ownership-clock-vault-verification.json`: separate author pin for vault/cache repairs and native clock source.
- Independent review records remain under `release/qa/`; earlier source pins do not certify later changes.

The existing d85 native exports predate these integrations. Store purchase/restore/refund, provider notifications, secure storage under real device reboot/key invalidation, native SDK traffic, hosted backup deletion and operating coverage remain unmet release requirements.
