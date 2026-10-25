# Tideglass v1 scope audit

Reviewed on **16 October 2026** against the original blueprint, v1 roadmap and 65-item backlog. **The AI implementation program covers the agreed v1 scope; the game is not complete.** The audit checks the implementation plan and delivered development tooling. Runtime, device, store and real-player acceptance remain future work.

Two consecutive audit passes were performed. Pass 1 traced the source scope into AI-owned work and identified defects. After repairs, pass 2 checked the corrected artifacts in both directions and reran the affected checks. Separate agents reviewed the program, economy fixtures, content validator and save contract; the director integrated the fixes.

## 1 Coverage and current delivery status

| Check | Result |
|---|---|
| Original production packages | 65 of 65 preserved, including original acceptance text and acceptance dependencies |
| AI execution work | 69 items: 65 original packages, three foundation contributions and one explicit postlaunch-support item |
| Product requirement groups | 44 of 44 have work assignments, verification obligations and reciprocal mappings |
| Execution ordering | 24 batches; acyclic graph; every inherited prerequisite is in the same batch or an ancestor batch |
| Accountability | Six AI delivery roles; distinct author/reviewer for every work item; maximum four concurrent agents including director |
| Scope expansion check | No public desktop release, new producer/prestige layer, multiplayer or paid-power system added |
| Source drift | Original blueprint, roadmap, backlog and economy configuration match recorded fingerprints |
| Executed foundations | Economy exporter, content registry/checker, save contract/checker and art-production routing exist |
| Production completion | All 65 original packages remain unaccepted; postlaunch support is also unaccepted |
| Content completion | 164 registered asset packages remain explicitly unfinished; all 44 product requirements remain unverified |

The extra support item executes the roadmap's existing requirement for 14 actual days of coverage. It does not add a new product feature. The foundation items create reusable implementation inputs and validation tooling; they do not replace native production code, authored content or release evidence.

## 2 Findings and repairs

| Finding | Repair and independent recheck | Status |
|---|---|---|
| QA-01: early content acceptance depended on later support documents | Added a B14 content-gate mode; retained full release validation at B22. Initial Season 2 brief is due B21, with B23 updating it after launch. Per-asset schedule now agrees. | Closed |
| QA-02: sample targets omitted explicit preregistration and precision/power planning | Assigned preregistered primary outcome, observation window and descriptive precision to M5-05/S34 before enrollment; causal experiments additionally require MDE/power and allocation planning. Counts are not a power guarantee. | Closed |
| QA-03: internal runbooks and Season 2 brief were routed into client localization | Moved outputs into release documentation, excluded both from client packaging and replaced player text-scale variants with internal review. | Closed |
| CR-GE-01: missing authoring fields could bypass verified-content checks | Required category-specific status/specification fields and nonempty completed specifications; independent omission reproduction now rejects. | Closed |
| CR-GE-02: missing UI/fulfillment states could bypass verification | Required explicit implementation/fulfillment states and actual UI acceptance evidence; independent omission reproductions now reject. | Closed |

The slice's offline promise was also clarified: B06 implements baseline replay for systems present at that point; B08 adds the full Focus/Survey/contract/bonus timeline. This preserves the original staged scope.

Independent records: [QA scope review](implementation/reports/qa_scope_review.md), [structured QA findings](implementation/reports/qa_scope_findings.json), [gameplay cross-review](implementation/reports/gameplay_cross_review.md), and [independent economy-fixture review](implementation/reports/art_gameplay_review.md).

## 3 Executed checks

| Check | Observed result | What it proves |
|---|---|---|
| Economy reference export check | 113 conformance cases; 89 identity/invariant checks passed | Reproducible bounded reference outputs; not production precision/runtime correctness |
| Save contract validator | 43 of 43 positive/negative cases passed | Envelope structure and selected revision/operation/configuration invariants; not atomic writes/cloud recovery |
| Content registry and rejection checks | Registry valid; 33 rejection cases passed | Counts, relationships, parity/isolation and false-readiness guards |
| Program checker | All mappings/dependencies/source hashes pass; six invalid-program mutations rejected | Structural traceability and preservation of original acceptance |
| Independent economic mutations | Eleven invalid save/content changes rejected | Additional cross-review probes of parity, isolation, revisions and reward identity |
| Art production contract review | 20 structural checks passed | All 164 assets routed; all eight original artist packages represented; internal documents scheduled and packaged correctly |
| B14 content gate on actual manifest | Expected failure: 362 unfinished obligations | Planned gameplay content is not mislabeled complete |
| Full content release check on actual manifest | Expected failure: 380 unfinished obligations | Final release content/support evidence is still required |
| Program release check | Expected failure: 66 unaccepted production/support items and 44 unverified requirements | A covered plan cannot be reported as a finished v1 |

Command results are preserved in [bootstrap_validation.json](implementation/reports/bootstrap_validation.json). Counts are separate categories and must not be summed into a single claimed test-suite size. File/evidence existence checks are necessary bookkeeping; reviewers still have to assess actual behavior and evidence quality.

## 4 Forward mapping from v1 scope to AI implementation

Every row retains its source and specific verification obligation in the [requirement register](implementation/scope_requirements.json). All rows are **unverified product requirements** today, even where bootstrap tooling exists.

| Scope | Required behavior or content | Assigned work |
|---|---|---|
| S01 | iOS and Android public launch; phone and usable tablet; internal desktop only | M0-01, M0-02, M7-03 |
| S02 | Guest offline core, optional cloud, English externalized text and pseudolocalization | M1-05, M3-06, M5-02 |
| S03 | Five producer prices/outputs, tier ratio 20, growth 1.12, previous-tier unlock at 10 | M1-01, M1-02, M2-01, BOOT-CORE |
| S04 | Single, milestone and maximum purchase controls and whole-tier 2x milestones at 25/50/75/100 | M1-02, M1-05, M3-09 |
| S05 | Lifetime-based 0.65-exponent Rechart, entitlement subtraction, retained-state preview and permanent power | M1-01, M1-02, M2-02, BOOT-CORE |
| S06 | Autobuy at 10 Charts, synergies at 25, conditional resets at 100; free plan and five optional 50-Note slots | M2-01, M3-03 |
| S07 | Cross-tier synergy matrix and honest marginal-output/purchase/reset forecasts | M2-01, M2-03, M5-05 |
| S08 | 24 hours full production plus 48 hours at quarter rate; event-driven saved-policy replay | M3-01, M3-10, M5-01 |
| S09 | Focus every 2 hours, capacity 12, queued +20% ten-minute charges and equal accessible calibration | M3-01, M3-04, M5-02 |
| S10 | Automatic 8-hour Surveys, queue capacity 3, 10 Notes per completion | M3-01, M3-10 |
| S11 | Three daily contracts, 10 Notes and 250 XP each, frozen goals, rerolls and seven-day/21-slot backlog | M3-02, M3-10 |
| S12 | Atomic saves, rolling backups, export/import, migrations and interruption recovery | M1-03, M1-08, M5-07, BOOT-SAVE |
| S13 | Cloud revision conflicts preserve branches; no adding divergent wallets/lifetime/offline intervals | M2-04, M3-06 |
| S14 | Explicit event ordering, numeric remainder policy and pinned economic versions | M1-01, M1-04, M3-01, M3-10 |
| S15 | Six chapters, ending and continued play; target 15–30 calendar days without hard time lock | M1-06, M3-08, M4-06, M6-02, BOOT-CONTENT |
| S16 | Twelve challenge dossiers across three rule families, 100 Notes each | M3-08, M4-01, M4-06 |
| S17 | Twelve authored calibration patterns with equivalent accessible completion | M3-04, M4-06, M5-02 |
| S18 | Eighteen main archive entries and six optional 50-Note decorations; no forced full collection | M4-06, M4-07, M5-05 |
| S19 | One harbor with initial plus six restored presentations; 25 producer presentations | M0-05, M1-07, M2-05, M3-09, M4-07, BOOT-CONTENT |
| S20 | Season 1 Night of Returning Stars, 28-day lifecycle, isolated fleet, specified coefficients and no event prestige | M4-02, M4-06, M6-07 |
| S21 | 30 levels at 500 XP, 30 free slots with 10 cosmetics/20 fragments, 10 premium cosmetics, selected archived pass | M4-02, M4-03, M4-06, M6-08 |
| S22 | 36 unique cosmetics distributed 12 core, 10 free pass, 10 premium, 4 direct shop; supporter reuses shop items | M4-06, M4-07, M4-08, BOOT-CONTENT |
| S23 | Ambient soundtrack, interaction/milestone/Rechart cues, independent controls and supporter soundtrack delivery | M1-07, M4-07, M5-06 |
| S24 | Cosmetic previews, localized price, verified purchases, restore, pending/retry/refund/revocation handling | M4-03, M4-04, M5-08 |
| S25 | Equal ad/briefing six-token daily allowance; 300-second credits, speed/offline choice and additive buffs | M3-07, M4-05, M4-08, M5-05 |
| S26 | Settings, target input, readable numbers, contextual help and opt-in quiet-hour notifications | M3-05, M5-02 |
| S27 | Help, recovery guide, release notes, credits, privacy/support URLs and runbooks | M5-03, M5-04, M7-05, M7-07 |
| S28 | No known save-loss, duplicate grant, negative wallet or undelivered verified purchase | M1-08, M3-10, M5-07, M5-08, M7-06 |
| S29 | Numeric parity: matching integer decisions; continuous error budget initially 1e-8 outside near-zero cases | M1-01, M3-10, M5-05 |
| S30 | 99.5% crash-free sessions over 10,000 observed sessions, per platform/device and critical-flow review | M5-04, M6-05, M6-07, M7-06 |
| S31 | 60/30fps targets, p95 startup ≤5s, 24h replay ≤3s, measured 30-minute battery/thermal usability | M5-01, M5-07 |
| S32 | 15 new moderated testers and 80% comprehension target; first prestige 15–30 minutes among reachers plus non-reachers | M2-06, M2-07, M6-04 |
| S33 | 30/90-day simulations of visit/reset/buy/bonus strategies and Note scarcity | M5-05, M6-03 |
| S34 | Real D30 and 28-day season, targets 500 starts/10,000 sessions; uncertainty and baseline tracking | M6-01, M6-02, M6-07, M5-05 |
| S35 | D1/D7/D30 35/15/7% review hypotheses, strategy variety, welfare and commercial cost assessment | M6-02, M7-01 |
| S36 | Current platform review, accurate listing, sandbox tests and final store acceptance | M0-03, M7-03, M7-07 |
| S37 | Monitoring, support diagnostics, backups, feature disables, rollout stops and compatible forward repair | M5-04, M6-05, M6-08, M7-04, M7-08 |
| S38 | 14 actual days of launch coverage, incident follow-through, final v1 record and Season 2 brief | M7-08, OPS-14 |
| S39 | Privacy, consent/refusal, account deletion/export and service outages reflect actual SDK behavior | M3-06, M5-03 |
| S40 | Reproducible native builds, explicit stack/toolchain feasibility and configuration compatibility | M0-02, M0-03, M0-08, M1-04 |
| S41 | Budget and device/test plan adapted to AI delivery; protect scope and independent review | M0-01, M0-04, M0-06, M0-07 |
| S42 | Complete release evidence pack and approved candidate with only accepted minor issues | M7-01, M7-02, M7-06 |
| S43 | Polish observed content/UI issues and create accurate store/launch assets | M6-04, M6-06, M5-06, M7-05 |
| S44 | Mid/late progression adds meaningful decisions and at least two viable strategy/challenge approaches | M1-06, M3-08, M5-05, M6-02 |

## 5 Reverse mapping from work to agreed scope

All 65 original packages are assigned to named AI authors, independent reviewers and a primary execution batch in the [assignment table](implementation/team/ASSIGNMENTS.md). Their acceptance text is copied unchanged from the original backlog, with the staffing adaptation explicitly recorded for M0-07. Each has at least one scope requirement and every scope-to-work link has a matching reverse link.

| Additional work | Scope justification | Boundary preserved |
|---|---|---|
| BOOT-CORE | S03/S05: arithmetic and prestige conformance inputs | Bounded numerical reference; native engine/number system still to implement |
| BOOT-CONTENT | S15/S19/S22: fixed content inventory and asset production preparation | Stable IDs and production routing; all final assets/content still unfinished |
| BOOT-SAVE | S12: persistence contract and hostile input cases | Schema/domain checks; actual disk and cloud operations still to implement |
| OPS-14 | S38 and roadmap section 12: actual postlaunch support | Real 14-day operations, not an instant simulated task |

Within-scope allocations such as four challenges per family, three main archive entries per chapter and ten premium rewards at three-level intervals are authoring choices. They preserve the original totals and can be revised within those totals through a versioned content change. The supporter bundle reuses four shop cosmetics plus the soundtrack and adds no unbudgeted cosmetic set or power.

## 6 What still prevents a finished v1

The next implementation gates are release-decision closure and native stack qualification. Android Java/build prerequisites require repair; a production engine, working native IAP/ad/cloud adapters and target hardware remain unproven. The AI team must then build the production core, durable persistence, native client, authored campaign/challenges/season, assets, commerce and operations.

Before launch, actual native and physical-device tests must establish correctness, recovery, purchase fulfillment, accessibility and performance. Actual people must supply comprehension and retention evidence; a stable D30 cohort and 28-day season cannot be replaced by accelerated simulations. Store acceptance requires real account/configuration access, and launch support requires a real operating arrangement for 14 days. Audio production and soundtrack delivery require suitable files and rights.

These are assigned implementation and release obligations, not omissions in the program. No original production item or product requirement is accepted merely because the AI team and its implementation program have been created.
