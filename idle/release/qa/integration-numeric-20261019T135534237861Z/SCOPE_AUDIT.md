# Numeric scope check

Pin: `e1a7508d208f828057b35f942fd4d6b9b46853d03e5247fce585da79392003af`.

All 44 scope requirements retain reciprocal links to the 65 original production packages. Original acceptance text, dependencies and four source fingerprints match. Four prior original acceptances and three distinct bootstrap acceptances are unchanged.

| Scope → implementation | Evidence |
|---|---|
| S03: Five producer prices/outputs, tier ratio 20, growth 1.12, previous-tier unlock at 10 | Prices, all rate-key inputs, marginal outputs, cache churn, large integers and unchanged formula source verified. |
| S08: 24 hours full production plus 48 hours at quarter rate; event-driven saved-policy replay | 62 reference rows include online/offline timelines; additional 73h state/events compare exactly and 176 core regressions pass. |
| S31: 60/30fps targets, p95 startup ≤5s, 24h replay ≤3s, measured 30-minute battery/thermal usability | Bounded immutable memoization and host exactness checks only; no physical performance budget established. |

| Implementation → scope | Evidence |
|---|---|
| engine.dart _prices / cumulative-price wrapper → S03 | 2,048 FIFO entries keyed by tier,count; count>8,192 bypasses retention; arithmetic unchanged. |
| engine.dart _countLogs / _chartPower / _rates → S03, S08, S31 | 1,024/128/512 FIFO entries; immutable keys and Fixed values; Chart/rate retention <=4,096-bit Charts; output key includes five counts and Charts. |
| game/qa/integration_numeric_memo.dart → S03, S08, S31 | 8 cases / 12,195 assertions against preserved baseline plus fresh-isolate FIFO probes. |
| reproduced before/after fixtures and full core regression → S03, S08 | 62 byte-identical rows and 176 passing tests. |

M5-01 remains **in_progress**. Its original acceptance is: “Meet measured frame/startup/resume budgets on minimum devices; heavy replay is chunked and never silently drops earned time.” Dependencies remain M3-10, M4-02.

No full scope requirement or new production package is accepted. Physical-device distributions, minimum-device budgets, thermal/battery usability and full native qualification remain open. S03 is supporting regression evidence; its original package mapping is unchanged.
