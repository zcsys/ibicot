# Service data inventory and deletion boundary

This describes implemented behavior. It is not a published legal policy, completed native SDK disclosure, or evidence of a hosted service.

| Data | Purpose | Collection and retention |
|---|---|---|
| Random account UUID, hashed recovery code and hashed session tokens | Optional account authentication | Only after cloud opt-in. Recovery code and token plaintext are returned once and never logged or stored by the service. Session lifetime 30 days, up to eight devices. |
| Full checksummed gameplay snapshots and branch metadata | Explicit cloud recovery | Uploaded only by the caller. Up to 64 MiB/10,000 snapshots; no silent branch deletion. Can include optional game settings, story state, and recovery references. No client credentials belong in a snapshot; sensitive key names are rejected. |
| Provider transaction identity, verified product/state/version/authority, acknowledgement | Restore and revoke cosmetic ownership | Stored separately from gameplay. Raw proof, purchase token, advertising ID and payment/card data are not retained by this service. No real provider is configured in the local runner. |
| Daily Support source/receipt and delivered snapshot ID | Deduplicate the shared six slots | Current plus seven prior account days; explicit prune also removes expired rows from inactive accounts. No briefing content or ad-view profile is collected. |
| Defined session/progression/diagnostic events | Optional quality measurement | Separate consent required, at most 5,000/account and 90 days. Revocation deletes current events. No freeform text, wallet dump, receipt or email field. Client queue is bounded and memory-only. |
| Short-lived source-address SHA-256 hash, time bucket and count | Request abuse limits | Raw address is not stored in service tables. Hashes are pseudonymous, not anonymized; entries removed after two minutes. Proxy/server logs need a separate deployment audit. |
| Optional feature-switch audit | Operator accountability | Contains switch name, boolean and time, without account identity. |

Account export excludes credential hashes as well as raw credentials and proofs. Account deletion requires recovery confirmation and cascades through active service snapshots, claims, telemetry, sessions and purchase records. SQLite secure-delete is enabled and database/backup permissions are owner-only. These measures do not prove forensic erasure from filesystem snapshots, WAL copies, or remote backups. The production operator must provide a bounded backup-retention/erasure policy and apply deletion tombstones before restoring backups. No hosted backup exists in this task.

Deletion leaves the current local guest game intact. It does not cancel an Apple/Google store purchase. Future restoration after deletion must independently reverify store ownership and account binding; local paid flags are not retained as proof. No email, password or third-party login is required by the implemented recovery-code method. A lost code with no valid device session is not recoverable by inventing identity or copying another player's account.

Native collection must be reviewed separately: the existing purchase and advertising plugins can initialize network behavior outside this service. Until native consent/configuration checks and actual traffic inspection are complete, this inventory cannot be asserted to describe the complete application. Consent refusal and service outage must leave guest economy, local export and free briefing playable.

No analytics upload runs automatically. `ConsentTelemetryBuffer.optOut()` clears local events immediately. If the remote service cannot be reached, its `pendingRemoteOptOut` remains true and the error is reported. The native host must persist/surface that pending request and retry after reconnection; an unsuccessful request must not be displayed as completed remote deletion.
