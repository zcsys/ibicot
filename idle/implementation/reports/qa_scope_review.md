# Independent QA scope review — two passes complete

Reviewer: `/root/qa_release_engineer`. Review date: 16 October 2026.

**Disposition: implementation program accepted after repairs; no unresolved scope-program finding.** Two directional passes preserve all 65 original work packages and cover all 44 scope groups. I identified and rechecked three program/handoff corrections. The gameplay reviewer independently found and rechecked two content-checker omission guards. This accepts the program and bounded bootstrap contracts, not a finished game.

## Evidence checked

I read the blueprint, v1 roadmap, original 65-item backlog, execution program, 44 scope groups, role registry, three implementation handoffs, content manifest, economy exporter and both contract validators. In pass 2 I also read the complete AI_IMPLEMENTATION_PROGRAM.md, the final art production contract, the program validator and the independent gameplay/art cross-review reports.

| Executed check | Actual result | What it establishes |
|---|---|---|
| Economy exporter, `--check` | 113 cases; 89 identity/invariant checks passed | Repeatable bounded reference fixtures |
| Content validator, `--self-test` | Plan valid; initially 21 and finally 33 rejection cases passed; 164 asset packages unfinished | Registry counts, relationships, reward parity and false-completion rejection |
| Save validator, `--config economy.json` | 43 of 43 cases passed | Versioned envelope and selected local invariants |
| Content validator, `--release` | Failed as expected: 380 unfinished/invalid obligations | Current manifest cannot be represented as finished content |
| Independent structural audit | 69 work items, 44 scope groups, 24 batches, six roles; no structural errors | IDs, reciprocal traceability, owners/reviewers, source hashes and acyclic dependencies |
| Program validator, `--self-test` | Structural audit plus six rejection cases passed | Rejects broken mapping, self-review, altered acceptance, cycles and unsupported completion claims |
| Content validator, `--content-gate` | Expected failure: 362 unfinished obligations | B14 does not accept unfinished gameplay content |
| Independent in-memory staged-content test | B14 profile passed; full release rejected 18 support/readiness obligations | Acceptance stages are separated without weakening final support requirements; no real manifest or status changed |
| Original-backlog comparison | All 65 IDs, original acceptance text and original dependencies preserved | No production work package silently removed |
| Batch prerequisite comparison | Every original cross-batch prerequisite is an ancestor of its dependent batch | No original acceptance prerequisite is ordered backward |

The structural audit checks that owners differ from their reviewers. It does not prove that future reviews will be independent or that evidence will be adequate.

## Forward audit: v1 scope to implementation

All 44 scope groups have assigned work and future acceptance. The machine-readable companion records each group and all 65 original packages individually.

| Scope groups | Coverage reviewed | Finding |
|---|---|---|
| S01–S02 | Native mobile release, guest/offline access, cloud option, language | Covered; actual native builds remain unproven |
| S03–S14 | Prices/output, purchase modes, prestige, automation, synergy, timelines, contracts, saves, precision | Covered; exact production arithmetic and full replay are future implementation |
| S15–S23 | Campaign/ending, challenges, calibration, archive, harbor/producer states, season/pass, cosmetics/audio | Quantities preserved; all 164 asset packages remain unfinished |
| S24–S27 | Commerce, equal ad/free routes, settings, help/support | Covered; QA-01 acceptance-stage conflict repaired |
| S28–S31 | Integrity, precision, stability, physical-device performance | Future evidence explicitly required; bootstrap checks do not satisfy these |
| S32–S35 | Moderated users, long simulations, real D30/season, decision thresholds | Real-human/calendar limits preserved; QA-02 preregistration detail added |
| S36–S44 | Platform acceptance, operations, 14-day support, privacy, builds, budget, evidence, polish, strategy | Covered; publication, operating arrangements and observed evidence remain real dependencies |

No campaign, challenge, pass, cosmetic, audio or native-store feature was marked delivered by a registry, schema or simulated player. All original production items are `not_started` in the audited snapshot.

## Reverse audit: implementation to legitimate scope

All 65 inherited packages belong to the original roadmap. The four additions have justified purposes:

| Added package | Legitimate purpose | Boundary |
|---|---|---|
| BOOT-CORE | Conformance fixtures for arithmetic/prestige implementation | Development enablement; not production core |
| BOOT-CONTENT | Stable IDs and validation for fixed launch inventory | Development enablement; not completed assets |
| BOOT-SAVE | Versioned envelope and adversarial contract cases | Development enablement; not durable persistence |
| OPS-14 | Executes the roadmap's already-required 14-day launch coverage | Existing release obligation made explicit |

No public desktop launch, extra producer/prestige layer, multiplayer, competitive economy, paid power or extra fully produced season was added. Four challenges per rule family, three archive entries per chapter and premium rewards every three levels are implementation allocations within the fixed counts, not additional product scope.

## Findings repaired and independently rechecked

### QA-01 — P1, closed: early content gate required later support artifacts

B14 explicitly requires the full manifest's `--release` check. That validator requires all tracked content and assets to be verified, including `support.operations_runbooks`, privacy/support materials and `support.season02_brief`. The program schedules operating-service work at B16, final support materials at B21 and Season 2 handoff work at B23, downstream of B14. B14 therefore cannot be accepted under the stated ordering.

**Correction requested:** define and implement a B14 content-complete profile that covers shipped gameplay/content/UI/commerce while deferring explicitly listed operational support artifacts. Require every prelaunch support artifact and an initial Season 2 brief at B21/B22, with the postlaunch brief updated at B23. Keep a strict full-content release check; do not weaken the final release contract or silently skip unfinished gameplay.

**Verified repair:** B14 now invokes `--content-gate`; B21 finishes all eight support records plus help/support UI and the initial Season 2 brief; B22 runs strict full-content `--release`; B23 updates the existing brief. The art asset schedule now assigns the initial brief to B21/M7-01 and director ownership. The independent staged-content mutation check passes B14 while strict release still rejects missing support/readiness evidence.

### QA-02 — P2, closed: study preregistration needed explicit acceptance

Blueprint Phase 3 §7 requires a preregistered primary retention or satisfaction metric, duration and minimum detectable effect. B17/B18 and S34/S35 specify frozen definitions, cohorts, counts and uncertainty, but do not assign the preregistration/power obligation explicitly. A target of 500 starts is not a power calculation.

**Correction requested:** attach a preregistration artifact to M5-05/S34 before B18 enrollment. For descriptive cohorts, specify the primary metric, window and planned precision/uncertainty; for any comparative experiment, specify effect size, power/sample calculation and stopping rule before enrollment. Report any underpowered comparison as such.

**Verified repair:** B17 explicitly preregisters the primary outcome, duration, exclusions and analysis, with descriptive precision and separate MDE/power/allocation for any causal experiment. S34 maps that obligation to M5-05. B18 states that 500 starts/10,000 sessions are planning targets, not power guarantees. Enrollment depends on B17.

### QA-03 — P2, closed: internal operating artifacts were routed into player localization

The art contract originally exported the operating runbooks and Season 2 development brief into `game/content/locales/en-US`, with player text-scale variants. Those are internal deliverables, not player-facing content. The corrected records export to `release/runbooks/index.md` and `release/season-2-brief.md`, set `delivery_channel: internal_release_package` and `exclude_from_client_packaging: true`, and require `internal_document_review`. Their manifest/evidence obligations remain intact. I reread the actual corrected records.

### Independent cross-review repairs

The gameplay reviewer found two completion-guard omissions: authored fields could be deleted from verified content, and UI/fulfillment fields could be deleted from verified UI/supporter records. The integration lead repaired the required fields/states/evidence guards; the non-author gameplay reviewer reproduced both failures and verified their rejection after repair. I read that report and reran the final 33-case checker. See `gameplay_cross_review.md`. The art owner separately reviewed and reran the gameplay exporter; see `art_gameplay_review.md`.

## Clarifications and limitations

- B06 now explicitly implements baseline saved-policy offline replay for the slice only. Full Focus/Survey/contract/bonus chronology belongs to B08.
- All six role bindings are populated. Four concurrent slots require role rotation; saved role records do not create background workers.
- Contract evidence is intentionally limited: save gameplay payloads are opaque; recovery references do not prove backups exist; cached ownership is untrusted. Native IAP/ad/cloud behavior is untested.
- The economy reference uses bounded binary64 amounts. Its exact integer prestige oracle covers whole-R samples; production fractional scaling and extreme-number handling remain necessary.
- Session agents are not persistent 24-hour operators. Real testers, physical devices, developer accounts, store review and 14 days of operating coverage cannot be supplied by synthetic test success.

## Second-pass conclusion

I reran the affected checks and repeated both directional comparisons. All 65 original acceptance strings and dependency lists remain unchanged; 44 scope groups and all 69 work items have reciprocal coverage; all 164 art contract IDs match the launch manifest. The four added work items remain implementation enablement or the existing postlaunch obligation. The human-readable program matches the corrected execution order. No new product scope or reduced native/human/elapsed gate was introduced.

The three BOOT items may be accepted as reviewed development foundations. All 65 original production packages and OPS-14 remain unaccepted, all 44 delivery requirements remain unverified, and all 164 asset packages remain unfinished. No native build, production save service, store transaction, real player cohort or launch coverage was certified. This distinction must survive any summary of this audit.

