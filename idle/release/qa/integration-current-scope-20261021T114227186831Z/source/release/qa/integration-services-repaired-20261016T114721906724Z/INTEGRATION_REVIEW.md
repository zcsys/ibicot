# Independent service, replay and commerce integration review

**The reviewed host implementation passes its bounded regression gate.** Four defect families were independently reproduced, repaired by the lead, and retested. This review does not accept finished v1, a store release, a deployed service, or unreviewed notification work.

Repaired source: `8d0fee0b1d5d36f5114764c9b72ad9820baf0337ccd7557c45d178ff82d24cb5`. The snapshot contains **285 hashed inputs**; all remain unchanged after testing. Initial source and failures are preserved separately under `integration-services-initial-20261016T113255538648Z` (`27fff44d9fda25900cb78b54e935bbd623b4a605793fbf4767e24f67eee4465c`). `snapshot.json`, `verification.json` and `evidence-index.json` give exact sources, commands, outputs and hashes.

## Results

| Pinned area | Passed | Analysis / method |
|---|---:|---|
| Core | 176 | Clean Dart analysis |
| Events / pass | 31 | Clean Dart analysis |
| Persistence | 19 | Clean Dart analysis |
| Progression | 25 | Clean Dart analysis |
| Platform HTTP / telemetry | 6 | Clean Dart analysis |
| Mobile integrated host | 199 | Clean Flutter analysis |
| Base HTTP / SQLite service | 26 unique | 48 executions: director suite imports and repeats the 22 author cases |
| Provider author suite | 8 | Response policy, real Apple SDK forged-JWS rejection and local ECDSA |
| Independent provider review | 4 | 18 policy variants; no real provider transaction |

The six Dart packages total **456 passing tests**. Python suites contribute **38 unique cases**. These counts are software checks, not participant sessions. All **19 newly written independent mobile tests** pass in the 199-test mobile run.

## Reproduced defects and repairs

| Finding | Initial failing cases | Result |
|---|---:|---|
| QA-010 — account/request/credential lifetime | 7 | A request cannot adopt a later bearer; late sign-out cannot erase recovered B; stale secure reads/writes/deletes cannot restore A over B; stale ownership work cannot clear B's valid projection. |
| QA-011 — consent and telemetry identity | 5 | Latest local and remote withdrawal wins; account changes clear old queued activity; pending remote withdrawal is account-bound and durable in the native preference layer. |
| QA-012 — stale purchase completion | 2 | Account or harbor replacement keeps stale verification retryable and prevents false current delivery/completion. Existing ownership projection already denied the wrong account/seed. |
| QA-013 — briefing sync during save | 1 | The free local token remains available; optional sync occurs only for the account/harbor that began the action, after a successful durable save. |

Original failures total 15 cases across four families. The two consent tests' await order was adjusted to allow serialized implementations while keeping the same final refusal assertions. The original versions and logs are retained, and compatible versions were also rerun against the initial source. QA changed only its tests and evidence; the lead changed production code.

## Integrated behavior inspected

- **Replay and saves:** the actual isolate worker preserves one original absence offset across main/challenge/season, publishes one complete state, and gates interaction while replaying. Independent persisted schema-3 partial continuation proves only the remaining interval is credited. A fully consumed typed request finalizes once without extra earnings. A simulated century equals the 72-hour production cap in main and season while a host UI timer runs. Prior import partition/cursor checks remain in the full regression. This is host arithmetic/fairness evidence, not a measured physical replay budget.
- **Cloud and account UI:** explicit creation/recovery/export/deletion, consent, generation-CAS branch upload/selection and whole-save import are exercised through the real UI/manager. Existing tests include actual loopback HTTP; two independent account races also use actual HTTP. Failed local import after remote selection reports that partial outcome; no branch balances are combined. No hosted or two-device cloud qualification is inferred.
- **Purchases and cosmetics:** actual localized storefront metadata flows into preview/purchase UI. Pending, retry and restore requests do not grant ownership. Premium appearances separately require earned level and current service-verified entitlement; saved claim/preference fields cannot grant paid items. Same renderer supplies preview and equipped views. All 36 contact-sheet appearances have distinct visible additions without obvious clipping. Supporter purchase remains withheld until authenticated soundtrack fulfillment exists.
- **Support and ads:** local free briefing survives service outage and checks local durability before optional account sync. Shared day/slot identity prevents repeated delivery. SDK reward callbacks only trigger a service-ledger lookup. Consent/no-fill, late loading disposal and account/seed changes are tested through controlled native adapters. The provider suite verifies exact encoded-query ECDSA and rejects changed bindings, duplicates and unsigned suffixes.
- **SDK and audio boundaries:** inspected pinned plugin source maps generic account UUIDs into StoreKit 2 app-account tokens and Android billing account IDs. This is source inspection, not a successful purchase. The iOS ambient audio-context repair is covered by an explicit host iOS override; previous stale-track and reused-voice regressions pass. It does not prove real iOS/Android decoder, headphones or background playback.

Primary provider reference checks: [Google ProductPurchaseV2](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.productsv2) and [AdMob server-side verification](https://developers.google.com/admob/android/ssv). Real locally generated ECDSA validates cryptographic handling; synthetic purchase responses are never store-success evidence. The provider defaults remain unavailable until explicitly configured.

## Scope cross-check and acceptance limits

`SCOPE_AUDIT.md` and `scope-audit.json` review all **44 scope groups in both directions**, retain all **65 original package acceptance sentences and dependencies**, and map 20 implementation areas back to scope. All four original source hashes match. Four original foundation packages retain director acceptance; three accepted bootstrap packages remain separate. No full release scope group is accepted here, and no extra producer tier, prestige system, paid economic power or public desktop/web release was introduced.

M3-10 gains independent worker/partial-replay evidence; M4-08 gains complete appearance rendering and service-backed presentation components; M5-07 gains explicit local/cloud recovery components; M5-08 gains adapter, policy/crypto and race evidence. Their original prerequisites and full native/service/store gates remain open.

**Excluded from this pin:** notification source/tests and final lifecycle wiring, the new simulation lane, and fresh native candidate instrumentation. A notification plugin dependency may be declared in the captured manifest; that does not qualify notification behavior. Native proof belongs to its own exact candidate hashes, and a repaired host source cannot inherit an earlier device pass.

The user has no developer accounts, physical test devices, hosting or human testers. Open delivery work includes authenticated soundtrack fulfillment, production provider credentials/products and encrypted token vault/deletion integration, notification and reconciliation workers, actual SDK/network/consent audits, deployment load/backup/monitoring drills, physical performance/accessibility and both stores' acceptance. No human comprehension/retention, 28-day season or 14-day launch coverage has been fabricated. Substantial local implementation remains actionable; this is a completed independent review slice, not finished v1.
