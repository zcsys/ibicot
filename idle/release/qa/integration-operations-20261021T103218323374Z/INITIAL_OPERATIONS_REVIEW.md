# Independent operations review — original checkpoint

The original checkpoint is **not ready to close**. Ten independent cases run against the immutable 37-file author snapshot produced seven passes and three failures. No production source was changed by the reviewer.

Source-map fingerprint: `7b3a5742947907c7025790a56fe044f2832ecf0c2ccb46608e41ddca416f19a1`. Every author-snapshot byte matched. Live production/runtime inputs also matched; only `implementation/program.json` had subsequently changed. Its live version is separately preserved as `current-program.json`; the author program remains in the isolated workspace.

## OPS001 — unsupported constraints accepted

`health.check_schema` compares `table_xinfo`, foreign keys and `index_info`; those do not cover CHECK expressions or index collations. A schema with the vault singleton `CHECK(id=1)` removed, containing an invalid `id=2` row, was accepted. A schema changing the accounts primary-key comparison to `COLLATE NOCASE` was also accepted. Both are valid SQLite files whose integrity and FK checks pass, but they are not the known supported structure the guard promises. The unchanged independent tests require refusal before restore or operator mutation. Repair must preserve recognition of the actual existing provider-generated schemas, not just the author's expected-schema fixture.

## OPS002 — future events dilute a present failure alert

The telemetry selection only requires `received >= now-window`. One hundred current save events with two failures yield a critical 2% failure rate. After adding 200 successes received tomorrow, the same checker reports 300 samples, 2 failures, 0.0066667 and **ok**. Future rows must not enter the current sample denominator. A server clock rollback can create this persisted shape without modifying event properties. The original log records the complete aggregate counterexample without account credentials.

## Passing independent behavior

A real recursive SQLite query is interrupted by the configured short budget; writes through `open_existing` are refused and source bytes remain unchanged. All six tested CLI commands reject a missing path without making its parent or a backup destination. Valid current-window endpoints and synthetic exclusion behave as documented. An actual WAL-backed backup contains the committed marker, is owner-only, and refuses to replace an existing destination.

The isolated restore applies account deletion to accounts, sessions, purchases, reconciliation, leases, encrypted provider tokens and telemetry, preserves vault key-binding history, invokes actual dispatch checks, leaves the source backup byte-identical and removes the temporary directory. Reports contain no supplied account identity, bearer/recovery secret or encrypted fixture content. An expired restore budget fails and cleans its temporary copy. Seven malformed/ambiguous deletion-manifest shapes are rejected before source mutation.

## Scope limits

These findings concern local M5-04/M6-08(service portion)/M7-04 tooling and S27/S30/S37. Runbooks contribute local preparation to M7-08/S38. No live destination, hosted recovery, actual provider transaction, delivered alert, native season/pass migration, real player denominator or elapsed support coverage was exercised. The reviewed code has no live activation flag and always leaves a successful drill ineligible for activation. All original acceptance criteria and dependencies remain unchanged.

Evidence: `source-manifest.json`, `original-independent-test.py`, `initial-independent-tests.log`, preserved author logs and subsequent independently reproduced author-suite logs.
