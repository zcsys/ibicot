# Independent review of the gameplay reference fixtures

Reviewer: AI art/content delivery owner. Date: 16 October 2026.

**Result: no blocking findings within the bounded reference-export contract.** This review accepts the fixture-export delivery only. It does not accept a native economy, production save system, full timeline or game build.

Reviewed `implementation/tools/export_economy_fixtures.py` and `implementation/fixtures/economy_reference.json`. Ran the exporter in read-only check mode:

```text
python3 implementation/tools/export_economy_fixtures.py --check
Verified implementation/fixtures/economy_reference.json: 113 cases; 89 independent identity/invariant checks passed.
```

The check regenerated the expected data in memory, exercised the recorded identities and compared the complete serialized fixture to the committed file. It did not modify the exporter or fixture. Source hashes bind the fixture to `economy.py` and `economy.json`.

| Coverage | Cases | Review finding |
|---|---:|---|
| Individual and bulk costs | 25 + 30 | Bulk checks compare geometric pricing with summed unit purchases in bounded binary64 values. |
| Milestones | 13 | Boundaries at 25/50/75/100 and the capped multiplier are represented. |
| Integer prestige entitlement | 17 | An independent integer-power oracle represents exponent 13/20 for whole-R inputs; adjacent threshold cases are included. |
| Reset | 4 | Repeated claims, retained lifetime/time and unchanged repeat state are checked for the limited Python State. |
| Synergy output and marginal purchases | 5 + 5 | Locked/unlocked and no-target cases are recorded; independent output identity checks cover the documented coefficients. |
| Reference purchase choices | 4 | Initial, tier-unlock and milestone-adjacent reference policy choices are captured. |
| Offline envelope | 9 | Credited-time boundaries and 36-hour saturation are represented; this is not full offline replay. |
| Idealized first run | 1 | Purchase-event order, gift accounting, target earnings and no silent reset are checked. |

The exporter and fixture explicitly state the important limits: binary64 expected costs and rates do not define settlement precision; continuous tolerances cannot grant purchases or Charts; the integer oracle has whole-unit scope; and idealized immediate purchases before autobuy unlock do not represent player behavior or automation access. Full Focus/Survey/contract/bonus/day-boundary/reset-policy replay is excluded. Reset retention of Notes, discoveries, cosmetics and receipts is also excluded because those fields are absent from the reference state.

These disclosures are consistent with the code. The 113 fixtures and 89 identity checks therefore **do not masquerade as production or player tests**. B03 must still prove native arithmetic and discrete affordability, and later batches must validate full event ordering, persistence and real device behavior. Values generated from the original model are conformance inputs, not independent proof that every formula or future runtime implementation is correct.
