# Independent service review

The lead reviewed the actual HTTP dispatch, SQLite schema/transactions,
authentication, branch selection, entitlement and daily claim boundaries, and
Dart client source. The lead did not author this service implementation.

Four additional real HTTP checks pass: cloud-disable preserves privacy export
and deletion; concurrent uploads cannot recreate a deleted account; a fresh
independent verification renews expired ownership without issuing another
receipt; nested credentials and conflicting snapshot identities cannot replace
the selected cloud save. The test fixture's imported test class also reran all
22 author cases: **26 tests passed** in this invocation. Synthetic provider
observations are confined to tests and are not store transaction evidence.

The default service fails closed for store/ad proofs. Branch data remains
opaque recovery material and never grants paid ownership. Current authorization
is account-bound and expires until reverified. Account deletion and optional
feature switches preserve local guest play. No actionable defect was found in
this bounded review. Source hashes, command, count and limits are recorded in
`director-independent-review.json`.

This does not accept the complete production service packages. Native secure
storage/UI, authentic provider adapters and notifications, signed offline paid
ownership, authenticated soundtrack delivery, staging load/timeout behavior,
backup deletion/restore, monitoring and real store/device evidence remain open.
In particular, provider verification currently occurs inside a SQLite write
transaction; configured provider timeouts and deployment load qualification
must bound its effect on unrelated service operations.
