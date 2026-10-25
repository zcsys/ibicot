# Initial88 simulation scope audit

Source pin `1c870326cd1d84559bf5f8e45a0896bf0741018ad27aadbf753a822720eb4212`.

All44requirements and65originalproductioncontracts retain their acceptance text, dependencies and reciprocal mappings. The four source fingerprints match. Four previously accepted original packages and three separate bootstrap packages are unchanged.

| Scope → evidence | Remaining |
|---|---|
| S07: Cross-tier synergy matrix and honest marginal-output/purchase/reset forecasts | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S08: 24 hours full production plus 48 hours at quarter rate; event-driven saved-policy replay | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S11: Three daily contracts, 10 Notes and 250 XP each, frozen goals, rerolls and seven-day/21-slot backlog | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S18: Eighteen main archive entries and six optional 50-Note decorations; no forced full collection | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S25: Equal ad/briefing six-token daily allowance; 300-second credits, speed/offline choice and additive buffs | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S29: Numeric parity: matching integer decisions; continuous error budget initially 1e-8 outside near-zero cases | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S33: 30/90-day simulations of visit/reset/buy/bonus strategies and Note scarcity | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S34: Real D30 and 28-day season, targets 500 starts/10,000 sessions; uncertainty and baseline tracking | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |
| S44: Mid/late progression adds meaningful decisions and at least two viable strategy/challenge approaches | Full requirement unverified; policy limits, QA014/SIM001 and external gates remain. |

| Implementation → scope | Evidence |
|---|---|
| PolicyRun and initial88report → S07, S18, S25, S29, S33, S34, S44 | Sample reproducibility, full matrix accounting and explicit limited policies; no beta freeze. |
| Actual replay worker comparison → S08 | 120h economic/partition parity and1h/4h chunking; final daily ledger gap separately recorded. |
| Actual controller discovery/calibration probes → S11, S18, S25 | QA014 reproduced; archive repeat available; minimum calibration policy is not zeroFocus. |
| Pass/Note accounting → S07, S29, S33 | 556 assertions over88rows; contract XP/Notes and12free/ad fixture pairs reconcile. |

Original acceptance remains:

- M3-02 (in_progress): Seeded contracts, snapshots, offline progress, rerolls and 21-slot backlog preserve claim IDs and do not duplicate rewards. Dependencies: M3-01, M1-06.
- M5-05 (in_progress): Simulate 30/90 days across visit and bonus policies, audit Note sinks and content pacing, freeze beta config and metric definitions. Dependencies: M4-06, M5-04.

No new package or beta freeze is accepted. Human cohorts, physical devices, developer accounts and hosting remain unavailable.
