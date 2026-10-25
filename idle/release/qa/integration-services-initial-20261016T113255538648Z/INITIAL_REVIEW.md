# Independent service integration — initial evidence

Frozen source: `27fff44d9fda25900cb78b54e935bbd623b4a605793fbf4767e24f67eee4465c` (277 files). Production source copies remain unchanged. Supplemental independent tests and their hashes are listed separately; no production files were repaired by QA.

Eight new failures across four defect families were reproduced and sent to the lead. See `findings.json` and the original JSONL logs. Two HTTP probes use a real loopback server and actual service client; purchase, consent and Support tests use explicit controlled adapters around the production manager/bridge. These are not real store or ad transactions.

The selected author regression passes **53 tests**: native services 13, service settings 14, Support bridge 9, commerce 8, replay 6, audio native adapter 3. The real local service discovery passes **48 executions / 26 unique cases** (the director suite imports and reruns the 22 author cases). Provider author tests pass 8, and four additional independent provider tests pass 18 adversarial variants covering invalid purchase shapes/proofs, full-refund mapping, cryptographically valid but wrong reward binding, duplicated signed fields and unsigned suffixes. No provider credentials or live store transactions were used.

Four independent replay checks pass: schema-3 partial settlement continues from second 100 to second 300 without replaying prior income; the same legacy accumulator preserves the original 72-hour cap over 120 hours; a fully consumed but unfinished typed interval closes with no extra income; and a century-long simulated absence yields UI timer execution while both main and seasonal income equal the 72-hour cap. This is algorithmic/host fairness evidence, not a physical timing or elapsed retention measurement.

The first replay harness revision incorrectly expected expired tokens to remain after five days and constructed a forbidden zero-length request. The second revision still passed the old cursor to that request. Original failed logs and both test revisions are retained; the third revision fixes only QA setup and all four checks pass. These three harness errors are not product findings.

Primary reference checks were against [Google ProductPurchaseV2](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.productsv2) and [AdMob server-side verification](https://developers.google.com/admob/android/ssv). Provider success responses remain controlled fixtures; locally generated ECDSA proves the verification code handles signatures and binding, not that production callbacks are configured.

Current limits: no developer accounts, physical devices, hosting or human testers. No native SDK secure-store/purchase/ad acceptance, authenticated soundtrack fulfillment, deployment/load/monitoring acceptance, real cohort data or actual season/post-launch elapsed coverage is inferred. Native candidate evidence belongs to its own exact source pin.
