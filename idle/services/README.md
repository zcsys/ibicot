# Tideglass optional services

This is implemented local service code, with a Dart integration package at `game/platform`. It preserves the offline guest game. No account, endpoint, telemetry upload, ad, purchase, deployment or spending is activated by importing the package.

Run from the repository root:

```sh
python3 -m services.tideglass_service --database services/local/tideglass.sqlite3 --port 8765
python3 -m unittest discover -s tests/services -v
cd game/platform
../../tool/dart test
../../tool/dart analyze
```

The runner binds only `127.0.0.1`. It uses a threaded WSGI development server. The application is a standard WSGI callable; public deployment requires an authenticated operating arrangement, a production application server, TLS, bounded request timeouts/body limits and staging qualification. The development server is not a public hosting solution. The default runner deliberately leaves store/ad verification unconfigured and fails closed with `verification_unavailable`. Optional real-provider source adapters are now supplied separately in `providers/`; see [provider setup and remaining qualification](docs/PROVIDER_ADAPTERS.md). They require explicit application credentials, trusted keys and operating configuration. Synthetic verifier classes live only in tests; no actual provider purchase/ad has been exercised.

## Implemented boundaries

| System | Working behavior | Limit still requiring integration or external evidence |
|---|---|---|
| Optional account | Explicit cloud opt-in; random 256-bit recovery code; hashed credentials; expiring/revocable device sessions; rotation; export/deletion | Native secure storage/UI are implemented; physical-device qualification, hosted TLS and security review remain |
| Cloud recovery | Full checked envelope snapshots, immutable identities, compare-and-swap selection, preserved divergent tips and detached history | Native two-device drill and staging; payload economic validity remains the native core's responsibility |
| Independent ownership | Server-side provider boundary; product allowlist; pending/purchased/revoked states; durable grant before acknowledgement; deduplicated restore | Actual Apple/Google authentication, app/product setup, signed notifications, reconciliation worker, purchase/restore/refund evidence |
| Support claims | One ledger per account/day/slot, six slots; briefing/ad share slots; no-fill leaves briefing available; persisted delivery acknowledgement | Provider verification/native bridge source is implemented; actual configured callbacks and native delivery qualification remain |
| Pass XP | Kept entirely in the selected gameplay branch; no service XP grant endpoint | Main/event shared receipts remain the core/events responsibility; never merge two branches' XP |
| Telemetry | Separate consent; strict fields; event deduplication; bounded retention and native-client buffer; refusal clears local buffer | Native instrumentation and SDK/network audit; full install cohorts, crashes and D30 are not measured by these tests |
| Operations | Consistent SQLite backup, schema forward guard, optional feature switches, privacy export, dashboard with unknown session outcomes | Hosted backup erasure/restore procedures, alert delivery, real staged rollout and operating coverage |

No work package is accepted solely by these local checks. See [API](docs/API.md), [privacy inventory](docs/PRIVACY.md), and [operations runbook](docs/OPERATIONS.md).

## Client integration

Add `tideglass_platform: {path: ../platform}` to the native package and use `TideglassServiceClient(endpoint: ...)`. HTTPS is mandatory except explicit loopback development. Requests do not follow redirects. Credentials are memory-only in this package; they must not be placed in a gameplay snapshot or ordinary preferences. Retain a new recovery code **before** requesting rotation so it remains available if the server commits but its response is lost.

Uploading `SaveRepository.exportSave()` never modifies local progress. An upload may preserve a candidate and return `selectionRequired`. Show the candidate branches before calling `selectSnapshot` with the latest generation. Download returns the original export string; only the existing explicit `SaveRepository.importSave()` path should replace local progress, which preserves the displaced local branch. Unknown content/schema versions must continue to fail in the native repository; service storage does not make an incompatible save safe to load.

A service account binds to the first uploaded main-game daily seed and fixed UTC offset. Linking a different guest seed fails with `account_day_identity_conflict`; keep the local guest recovery copy, then explicitly recover the desired cloud branch. Do not transplant balances or reset the account-day offset. Choosing an existing cloud snapshot never combines wallets, lifetime earnings, timers, XP or offline intervals.

`ServicePassEntitlementReader` checks both service-account identity and linked main-game seed. It reads independent service ownership and never accepts local paid flags. Current ownership projection requires a verifier observation no older than 24 hours. That conservative cutoff is not offline signed receipt caching; a production signed cache and native restore flow still require implementation/qualification. Service outages do not affect free gameplay, but this reader cannot authorize a new paid delivery during an outage.

`ConsentTelemetryBuffer` is explicitly flushed, never automatically started. It retains at most 256 events by default (hard maximum 1,000) and seven days; expired/evicted events increment `droppedEventCount`. It does not persist events and therefore does not support an all-install reliability claim. Opt-out stops collection immediately, clears the queue, and retries remote deletion when flushed; the host must surface/persist a pending remote deletion across process exit. A newly constructed buffer starts disabled.

## Reviewed primary references

The implementation uses SQLite transactions and its online backup API as documented by [Python](https://docs.python.org/3/library/sqlite3.html). The local runner follows the development-only boundary described in [Python's HTTP server documentation](https://docs.python.org/3/library/http.server.html). Real commerce integration must use [Apple's App Store Server API](https://developer.apple.com/documentation/appstoreserverapi) and [Google's product purchase verification API](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.productsv2/getproductpurchasev2); rewarded ads must independently validate [Google's server-side verification callbacks](https://developers.google.com/admob/android/ssv). These references are integration requirements, not evidence that the unavailable providers were exercised.
