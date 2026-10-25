# Tideglass AI development team and execution program

The AI team owns implementation of Tideglass v1, replacing the studio roles in the earlier roadmap. Its work includes production code, assets, content, tests, native integrations and release preparation. The agreed game remains intact: this is a change to who delivers it, not a smaller web prototype or a reduction in scope.

The program contains **24 execution batches and 69 work items**: all **65 original production packages**, three executable development-foundation contributions, and an explicit item for the required 14 days of postlaunch support. Every item maps to one or more of **44 product requirements**. The [structured program](implementation/program.json) is the dispatch record; the [scope register](implementation/scope_requirements.json) records both directions of traceability. The [final scope audit](V1_SCOPE_AUDIT.md) distinguishes program coverage from game completion.

The original [blueprint](TIDEGLASS_DESIGN.md) controls economic rules and the [v1 roadmap](V1_ROADMAP.md) controls product scope and release gates. Their 36-week staffing forecast and person-week budget are historical human-team estimates, not an AI delivery promise. This program replaces those operating assumptions. Forecast AI work from accepted tasks and measured integration effort after the first slice; preserve real device, player-study, platform-review and postlaunch observation time.

## 1 The delivery team

Six delivery roles have been instantiated as agents in this session. The environment permits **four concurrent agents including the director**, so no more than three specialists work at once. Roles rotate through execution and review; six role names do not imply six simultaneous workers. The saved charters, assignments and evidence enable later sessions to resume; the agents are not an unattended background service.

| Delivery role | Session agent | Implementation responsibility |
|---|---|---|
| Director and integration owner | `/root` | Product/economy decisions, task dispatch, progression data, integration, scope and release decisions |
| Gameplay and economy engineer | `/root/gameplay_engineer` | Numbers, purchases, Rechart, synergies, timeline, automation, challenges, events and simulations |
| Client and accessibility engineer | `/root/client_content_engineer` | Native UI, onboarding, forecasts, daily flows, input, accessibility and packaging |
| Platform and services engineer | `/root/platform_engineer` | Saves, cloud, identity, entitlement verification, ads/free allowance, telemetry and operations |
| Art and content engineer | `/root/art_content_engineer` | Harbor/producer assets, animations, cosmetics, narrative, audio pipeline and asset completeness |
| QA and release engineer | `/root/qa_release_engineer` | Independent checks, fault/device coverage, content and scope audits, cohorts and release evidence |

The product owner supplies unavailable account authority, spending decisions and access to hardware or people. That is not a replacement six-person development staff. AI agents prepare and perform all work that the available tools can actually execute; native credentials, real people and elapsed time cannot be invented.

### Ownership and review

The [role registry](implementation/team/roles.json) defines code and content ownership. Gameplay owns `game/core` and `game/simulation`; client owns `game/client`; platform owns `game/persistence` and `services`; art/content owns `game/assets` and authored content; QA owns acceptance tests and release evidence. These are conceptual paths until B02 fixes the engine/module layout. The current `implementation` directory holds tooling and contracts, not a second competing game runtime.

Only one agent writes a shared interface or manifest at a time. The director accepts proposed schema changes, then consumers update against the accepted version. Parallel work uses disjoint paths; if native project files must change in several lanes, the director serializes those edits or uses isolated worktrees after checking repository setup. Do not overwrite unrelated workspace work.

Every work item has a named author and a different reviewer. QA review does not consist of an author restating their own test result: the reviewer inspects the changed artifact, reproduces relevant checks and probes an edge case. The director integrates only reviewed work and records the exact candidate/config/content versions. A director-authored change requires another agent's review too.

## 2 How tools are assigned to delivery

| Capability | Assigned use | Evidence required |
|---|---|---|
| Local file, command and patch tools | Core/client/service implementation, builds, fixtures, migrations, asset processing and repeatable checks | Actual files and command results; failures remain visible |
| Agent collaboration | Up to three disjoint implementation lanes, followed by cross-review and integration | Role, owned paths, task IDs, inputs, outputs and findings |
| Native SDKs and device tools | Real iOS/Android exports, adapters, install/update, sandbox and device measurements | Native logs and target-device results; a browser preview cannot satisfy these gates |
| Browser/native UI automation | Inspect runnable client flows, store/backend consoles when authorized, and accessibility/UI states | Screens or reproducible interactions for the actual target; do not infer unseen UI |
| Image generation and local visual inspection | Produce approved raster art variants after style qualification; inspect imports and animations | Saved sources, actual exports, provenance and in-game review; code/vector UI stays in its appropriate pipeline |
| Web research | Verify current engine/SDK documentation and platform requirements before decisions/submission | Primary-source links in the relevant decision record |
| Repository/PR tools, if a repository is selected | Reviewable branches, checks and pull requests | Identified repository, exact revision and linked checks; do not create remote infrastructure merely to host a plan |
| Local documents and data tools | Content manifests, reports, cohort analysis and release evidence | Versioned, readable artifacts tied to the accepted build |

Current inspection found local Python/Node and Xcode/Swift available. Android platform tools are present, but the Java/SDK setup is incomplete and native Android builds are unproven. No production engine has been qualified. [Platform handoff](implementation/handoffs/platform.json) contains the observed details. B02 resolves this before a native-stack commitment.

Audio delivery has its own capability gate. Image generation does not supply a finished soundtrack. The art owner must provide authored or suitably licensed audio, real playback/export tests and supporter fulfillment. If an external asset purchase is needed, present the concrete option and cost to the product owner before spending.

## 3 Dispatch and integration protocol

1. The director selects the next batch whose prior batch gates are accepted. Break its packages into small changes with an explicit acceptance condition; use the original 65-item acceptance criteria as completion requirements.
2. Read the relevant role handoff, source requirement, current interfaces and known defects. Assign an author, separate reviewer and file boundaries before edits.
3. Dispatch up to three independent tasks. Include input versions, work-item and scope IDs, required output paths, commands to run and the evidence needed. Draft interfaces may unblock parallel work within a batch; they do not satisfy final acceptance.
4. Each author implements, runs relevant checks and reports changed files, outcomes, unresolved concerns and remaining external checks. An unavailable service can have a test adapter, but the real integration gate stays open.
5. Another agent reviews the actual change and reruns/probes the important behavior. Failed checks or omitted evidence return the task to its author. Repeat only the checks affected by a repair plus the relevant integration gate.
6. The director integrates accepted slices, runs combined checks and records evidence. Mark a production item accepted only after its original prerequisites and acceptance criteria hold; scaffolding alone never closes the item.
7. Reconcile scope and content counts at every batch boundary. At release, repeat scope-to-work and work-to-scope audits independently, plus the runtime/store/human gates.

Use `not_started → in_progress → review_pending → verified → accepted`. A contract may be structurally verified while the production feature remains not started. An external dependency has an owner and a prepared deliverable; it does not justify fabricating a pass or preventing unrelated authorized local work.

Each handoff must record: work/scope IDs; author/reviewer; input versions; changed paths; actual output; checks run and exit results; exact evidence paths; migrations/config changes; unresolved failures; and the next owner. Keep project credentials in the appropriate secret store, not in fixtures, prompts or reports.

### Scheduling rule

Batch dependencies below are real acceptance gates. Original backlog dependencies remain acceptance prerequisites and are preserved verbatim in the structured program. Work inside a batch can overlap against reviewed interfaces. B04/B05, B08/B09, B12/B13 and B15/B16 provide independent lanes, subject to the four-agent limit and each task's input readiness. No concurrency multiplier is applied to the old human-week estimate.

Real elapsed constraints remain: a stable D30 cohort needs its full observation window; Season 1 needs a real 28-day cycle; store review has external timing; launch support lasts 14 actual days. An agent simulation can test economics over 90 days in advance, but cannot turn those observations into player retention evidence.

## 4 Ordered implementation batches

For each batch, the lead coordinates the named work items; their individual author/reviewer assignments are in the structured program. Outputs are target deliverables, not claims that those files already exist.

### B00 Create the execution baseline

**Lead:** Director and integration owner. **Entry gates:** source scope available. **Work:** BOOT-CORE, BOOT-CONTENT, BOOT-SAVE.

1. Freeze the source scope and register six AI delivery roles with file ownership.
2. Export reference economy fixtures, register all launch content and validate a versioned save-envelope contract in three independent lanes.
3. Cross-review these artifacts, run validators and reconcile scope in both directions. Mark only these development artifacts complete.

**Deliver:** `implementation/fixtures/economy_reference.json`, `implementation/content/launch_manifest.json`, `implementation/contracts/save-envelope.schema.json`, `implementation/reports/`.

**Accept when:** Reference exports are repeatable; content inventory is structurally complete but unfinished assets remain flagged; invalid save cases are rejected.

### B01 Lock release decisions and native candidate criteria

**Lead:** Director and integration owner. **Entry gates:** B00. **Work:** M0-01, M0-04, M0-05, M0-06, M0-07.

1. Preserve mobile-first iOS/Android scope, English launch, guest offline play and the full content inventory; replace human staffing assignments with AI role ownership.
2. Specify audience, territories, minimum OS/device matrix, numeric precision questions and provider-selection criteria; record unresolved decisions with owners.
3. Client implements reviewable first-purchase, Rechart, return and recovery flow prototypes; art owner supplies a reusable visual sample.
4. QA lists real-device scenarios and tester recruitment needs; director budgets tool usage, services, hardware, asset licensing and external testing without assuming six payroll positions.

**Deliver:** `docs/release-contract.md`, `docs/decisions/`, `game/prototypes/`, `release/device-matrix.json`.

**Accept when:** Four critical flows are reviewable; no public desktop, multiplayer or extra prestige tier enters scope; native proof criteria and remaining account/device needs are explicit.

**External input:** Product owner supplies unavailable audience/territory/budget constraints before dependent service enrollment or spending.

### B02 Qualify and pin the native production stack

**Lead:** Platform and services engineer. **Entry gates:** B01. **Work:** M0-02, M0-03, M0-08.

1. Inspect host toolchains and repair the local Android Java/build prerequisite; verify changes without altering unrelated projects.
2. Shortlist supported engines/runtimes using current official documentation. Build an actual iOS and Android purchase/reset screen with headless economic boundary.
3. Prove sandbox purchase/restore, optional ad plus free fallback and cloud revision behavior using candidate adapters. Stub demos cannot satisfy this gate.
4. Select the stack from evidence, pin engine/SDK/dependency versions and licenses, create repeatable builds and map conceptual paths to actual project modules.

**Deliver:** `docs/decisions/native-stack.md`, `game/`, `services/`, `build/`, `release/native-proof/`.

**Accept when:** Both native builds launch; sandbox integration evidence exists; reproducible headless/core test entry point runs. An unproven required adapter prevents stack lock.

**External input:** Native account/test-product configuration, signing credentials and available target devices; no real purchases required.

### B03 Implement production arithmetic and core state

**Lead:** Gameplay and economy engineer. **Entry gates:** B02. **Work:** M1-01, M1-02, M1-04.

1. Define numeric precision, currency accounting units, rounding and exact prestige boundaries before porting formulas.
2. Implement five producers, unlocks, bulk/max/milestone purchase commands, milestones, lifetime earnings and atomic Rechart transitions.
3. Version economic/content schemas and pin configurations to state; reject invalid or unsupported versions.
4. Compare bounded cases with the reference fixtures and add independent extreme-value/property checks; keep all reward logic outside presentation.

**Deliver:** `game/core/`, `game/content/economy/`, `tests/core/`, `docs/decisions/numbers-and-event-order.md`.

**Accept when:** No unaffordable purchase or repeated entitlement; reset preview agrees with transition; numeric error cannot cross a discrete award boundary.

### B04 Implement durable local state

**Lead:** Platform and services engineer. **Entry gates:** B03. **Work:** M1-03, M1-08.

1. Implement crash-safe writes, checksums, rolling recovery copies, migration and export/import against the reviewed envelope contract.
2. Commit economic actions and pending operation identities together; retry/recovery never grants a transaction twice.
3. QA injects interruption/corruption at every commit stage and ports production conformance fixtures, including rapid reset and version changes.

**Deliver:** `game/persistence/`, `tests/persistence/`, `tests/fixtures/migrations/`.

**Accept when:** Fresh, upgraded and corrupted saves recover to valid states; interrupted reward/reset histories do not duplicate or erase committed progression.

### B05 Build client shell and complete progression specifications

**Lead:** Client and accessibility engineer. **Entry gates:** B03. **Work:** M1-05, M1-06, M1-07.

1. Implement responsive harbor, producer controls, wallet/rate/retained-progress displays and settings over the core API.
2. Director authors all six chapter goals and the ending, challenge unlocks and required versus optional Note sinks.
3. Art owner delivers reusable scene/icon/type components with scales, states and reduced-motion behavior; externalize all text.

**Deliver:** `game/client/`, `game/content/progression/`, `game/assets/common/`.

**Accept when:** Playable shell on small phone and tablet; six-chapter goal specification exists; no duplicate economy arithmetic in UI.

### B06 Integrate the representative first session

**Lead:** Client and accessibility engineer. **Entry gates:** B04, B05. **Work:** M2-01, M2-02, M2-03, M2-04, M2-05.

1. Gameplay implements 10-Chart autobuy, 25-Chart synergies and baseline offline replay for the systems present in this slice only; full daily timers and bonuses arrive in B08.
2. Client teaches buying/Rechart/automation, displays marginal network output and conditional forecasts, and shows the offline return breakdown.
3. Platform adds optional account recovery with revision checks and explicit divergent-branch choice; never sum divergent wallets or offline intervals.
4. Art owner integrates a representative harbor, all five base silhouettes and one milestone sequence; exercise the whole path on both targets.

**Deliver:** `game/client/onboarding/`, `game/core/automation/`, `game/persistence/cloud/`, `game/assets/slice/`, `release/slice-builds/`.

**Accept when:** Gifted Skiff to five tiers, Rechart, autobuy, synergy, close/return and recovery is playable; forecasts disclose assumptions.

**External input:** Configured test cloud service and native targets.

### B07 Validate the slice with people and faults

**Lead:** QA and release engineer. **Entry gates:** B06. **Work:** M2-06, M2-07.

1. Director prepares a neutral moderator script and recruits at least 15 new testers through authorized channels.
2. Observe first-session completion and reset/offline understanding; report non-finishers as well as pacing among finishers.
3. QA reproduces critical misunderstandings and device/save/resume defects; assigned engineers repair and rerun affected checks.
4. Accept the slice only with evidence; use accepted task throughput to produce the first AI delivery forecast.

**Deliver:** `release/slice-study/`, `release/slice-gate.md`.

**Accept when:** At least 80% explanation target is assessed with individual failures; integrated device checks pass; no inference from bots is called human comprehension.

**External input:** Real recruited testers and their consent; agents can prepare and analyze, not impersonate participants.

### B08 Implement the full daily timeline

**Lead:** Gameplay and economy engineer. **Entry gates:** B07. **Work:** M3-01, M3-02, M3-03, M3-04, M3-05.

1. Implement Focus and Survey timers, offline full/tail envelope, bonus expiration and account-day boundaries on one ordered timeline.
2. Implement seeded contracts, frozen goals, rerolls, claim identities and 21-slot missed-day backlog.
3. Implement player purchase priorities, 100-Chart conditional reset plans, one free slot and Note-priced extras.
4. Client implements calibration with equal accessible completion, queued Focus, daily UI, text/notation/audio/motion controls and opt-in quiet-hour notifications.

**Deliver:** `game/simulation/`, `game/core/contracts/`, `game/core/plans/`, `game/client/daily/`, `game/client/settings/`.

**Accept when:** 2/8/24-hour behavior and 72-hour maximum absence envelope match the blueprint; same policy gives matching discrete outcomes online/offline.

### B09 Implement identity and claim services

**Lead:** Platform and services engineer. **Entry gates:** B06. **Work:** M3-06, M3-07.

1. Implement guest linking, account recovery/deletion/export and conflict selection with preserved recovery branches.
2. Separate trusted commercial ownership from local progression and cached display flags; introduce idempotent claim and receipt storage.
3. Specify Support allowance and pass-XP reconciliation; handle retries, offline claims and concurrent devices without duplicate grants.

**Deliver:** `services/identity/`, `services/entitlements/`, `game/persistence/claims/`, `tests/services/`.

**Accept when:** Guest economy works without login; confirmed ownership is recoverable; interrupted grants resume once; divergent progression is never silently merged.

**External input:** Chosen test backend/identity provider.

### B10 Complete the integrated alpha

**Lead:** Director and integration owner. **Entry gates:** B08, B09. **Work:** M3-08, M3-09, M3-10.

1. Finish chapter/challenge objectives, unlocks, copy requirements and rewards against passive and active routes.
2. Art owner produces all 25 producer presentations and daily UI states through the approved reusable pipeline.
3. QA runs combined visit schedules, absences, clock changes, reset/day collisions and bonus queues; engineers resolve failures.

**Deliver:** `game/content/challenges/`, `game/assets/producers/`, `release/alpha-gate.md`.

**Accept when:** Every core loop works in one build; 25 presentations are actually integrated; exact/approximate numerical differences are reported.

### B11 Implement isolated challenge and season runtimes

**Lead:** Gameplay and economy engineer. **Entry gates:** B10. **Work:** M4-01, M4-02.

1. Implement reusable constrained-fleet, synergy-priority and automation-planning scenarios with independent state.
2. Implement Season 1 lifecycle, pinned coefficients, start/end/archive transitions and one selected pass.
3. Ensure main automation continues while playing optional content; no main/paid power imports or economic exports; test exit/restart/offline boundaries.

**Deliver:** `game/core/challenges/`, `game/core/seasons/`, `tests/seasons/`.

**Accept when:** New and veteran players start equally in the event; live/archive transitions preserve legitimate progress and cannot mint economic rewards.

### B12 Produce the complete campaign and launch assets

**Lead:** Art and content engineer. **Entry gates:** B10, B11. **Work:** M4-06, M4-07.

1. Author and integrate all six chapters/ending, twelve dossiers, twelve calibration patterns, eighteen main archive entries and Season 1 copy.
2. Produce initial harbor plus six restored states, all 36 cosmetics and required UI states; maintain provenance, atlas/memory budgets and actual files.
3. Populate 30 free pass slots and ten premium cosmetics, soundtrack delivery, audio cues/volume controls and support material.
4. Validate identifiers and reward relationships, inspect actual screens and asset variants; planned placeholders never pass release mode.

**Deliver:** `game/content/`, `game/assets/`, `implementation/content/launch_manifest.json`, `release/content-evidence/`.

**Accept when:** All fixed quantities are integrated and reachable; supporter bundle reuses its specified cosmetics; none of these assets changes production.

**External input:** A licensed audio source or suitable audio-production capability if the available tools cannot deliver finished audio.

### B13 Implement cosmetic commerce and equal free rewards

**Lead:** Platform and services engineer. **Entry gates:** B09, B11. **Work:** M4-03, M4-04, M4-05.

1. Client implements previews, localized prices, ownership, restoration, pass selection and archived continuation.
2. Platform verifies native transactions, grants once, acknowledges/completes, restores and reconciles pending, duplicate, cancelled, interrupted and revoked purchases.
3. Integrate optional ads through the same six-token allowance as the free briefing; refusal/no-fill leaves the free route available.
4. Test Support buffs, queues and offline claims against the shared ledger; cosmetics and paid pass never add production power.

**Deliver:** `game/client/shop/`, `services/commerce/`, `game/platform/ads/`, `tests/commerce/`.

**Accept when:** Real sandbox purchase/restore/fault evidence on both stores; no fake receipt or stub ad adapter satisfies acceptance.

**External input:** Store sandbox products, test accounts and approved SDK configuration.

### B14 Certify complete content and commercial boundaries

**Lead:** QA and release engineer. **Entry gates:** B12, B13. **Work:** M4-08.

1. Traverse all content/reward IDs from realistic entry states and check campaign ending independently of optional completion.
2. Run accelerated complete-season and archived paid-pass paths; separately retain the later real-calendar gate.
3. Check no ad/cosmetic/event export increases core power beyond the equal free allowance. Run validate_content_manifest.py --content-gate: all gameplay content/assets must be verified; support documents and help/support UI receive final acceptance before B22.

**Deliver:** `release/content-commerce-gate.md`.

**Accept when:** All content and rewards are reachable with no placeholder; free pass completion requires no purchase; asset and reward counts match scope.

### B15 Optimize presentation and device performance

**Lead:** Client and accessibility engineer. **Entry gates:** B14. **Work:** M5-01, M5-02, M5-06.

1. Measure frame time, startup, 24-hour replay, battery and thermal behavior on the named minimum/midrange hardware.
2. Optimize/chunk long replays without discarding owed time; handle large text, color/audio/motion independence and target inputs.
3. Run pseudolocalization, integrate final audio and remove placeholders; create screenshots/icon/footage from actual builds.

**Deliver:** `release/performance/`, `release/accessibility/`, `release/store-assets/`.

**Accept when:** Roadmap performance/return budgets are measured; critical flows remain accessible; store images represent actual play.

**External input:** Physical minimum/midrange iOS and Android devices; simulators cannot establish thermal/battery results.

### B16 Verify privacy and operating services

**Lead:** Platform and services engineer. **Entry gates:** B13. **Work:** M5-03, M5-04.

1. Compare actual SDK/network behavior with data inventory, consent and deletion/export flows.
2. Implement trustworthy economy/session events, diagnostic exports, entitlement dashboards and version-compatible feature controls.
3. Exercise backups, service failure, recovery and minimal-data support tooling; preserve cached offline play.

**Deliver:** `services/ops/`, `release/privacy/`, `release/runbooks/`, `tests/telemetry/`.

**Accept when:** Declarations match actual collection; consent refusal and outages preserve promised access; metrics and alerts reflect known injected events.

**External input:** Configured staging services and product-owner decisions on required platform declarations.

### B17 Run long-horizon and release-fault regression

**Lead:** QA and release engineer. **Entry gates:** B15, B16. **Work:** M5-05, M5-07, M5-08.

1. Director/gameplay compare 30/90-day trajectories across purchase/reset/visit/bonus policies, Notes and content coverage.
2. QA runs minimum-device, storage/network interruption, migration and commerce retry/refund/ad faults.
3. Before enrollment, preregister the primary retention/satisfaction outcome, observation duration, exclusions and analysis. Specify descriptive precision; for any causal experiment separately set minimum detectable effect, power and allocation/sample calculation. Freeze beta configuration after faults are resolved; recruit before observation.

**Deliver:** `release/beta-economy-report.md`, `release/device-regression/`, `release/commerce-faults/`, `release/beta-gate.md`.

**Accept when:** No known save-loss or entitlement blocker; full trajectory bonus parity is assessed; 1,750-Note optional collection is not a hidden main-ending requirement.

### B18 Enroll the real measurement cohort

**Lead:** Director and integration owner. **Entry gates:** B17. **Work:** M6-01.

1. Prepare distribution, consent, recruitment and baseline version records; use only authorized external outreach and deployment.
2. Enroll the principal D30 cohort in a documented window; target 500 eligible starts and 10,000 sessions across the study. These planning counts do not guarantee causal power; do not run an underpowered experiment or substitute them for a power calculation.
3. Record denominator, predeclared exclusions, acquisition source and missing telemetry; start real seasonal observation.

**Deliver:** `release/cohorts/baseline.json`, `release/cohorts/enrollment-report.md`.

**Accept when:** Actual participants are enrolled and baseline is frozen; sample shortfall is reported rather than replaced with simulated users.

**External input:** Real people, enrollment funding/access and authorized test distribution.

### B19 Operate testing and correct observed defects

**Lead:** QA and release engineer. **Entry gates:** B18. **Work:** M6-03, M6-04, M6-05, M6-06, M6-07, M6-08.

1. Engineers resolve reproducible core, client and service findings; art owner fixes readability without expanding scope.
2. Operate support and staged access; rehearse season archive, paid continuation, migration, entitlement replay and compatible forward repair.
3. Observe an actual 28-day season and mature day-30 windows. A material experience change creates a separately analyzed cohort and may restart the observation requirement.

**Deliver:** `release/cohorts/observations/`, `release/recovery-drills/`, `release/fix-evidence/`.

**Accept when:** Real calendar gates mature; controlled fixes have replay evidence; final cohort is not mixed across unrecorded balance changes.

**External input:** At least the full D30 observation opportunity; physical devices and testers remain necessary.

### B20 Decide product readiness from mature evidence

**Lead:** Director and integration owner. **Entry gates:** B19. **Work:** M6-02.

1. Compute mature D1/D7/D30 with uncertainty and observability limits; compare provisional 35/15/7% review targets.
2. Assess campaign pacing, comprehension, strategy variety, bonuses, satisfaction, pressure and operating cost.
3. QA cross-checks calculations; record ship, extend or revise decision. Retention targets cannot waive correctness, ownership or fairness failures.

**Deliver:** `release/cohorts/final-analysis.md`, `release/product-decision.md`.

**Accept when:** Results are based on real eligible participants; non-finishers and missing data are visible; every required review signal has evidence.

### B21 Freeze and prove the release candidate

**Lead:** Director and integration owner. **Entry gates:** B20. **Work:** M7-01, M7-02, M7-03, M7-04, M7-05.

1. Review all hard gates, freeze candidate/config/content and list only acceptable minor issues with owners.
2. Engineers tag compatible builds, exercise signing/install/update/distribution and prepare forward-fix and feature-disable paths.
3. Art/client finish accurate store/help/credits materials; platform finishes privacy/support/operations documents and rehearses recovery. Director prepares the initial Season 2 brief before launch; all eight support-content records and help/support UI must be verified before B22.

**Deliver:** `release/candidate/`, `release/evidence-index.json`, `release/store-listings/`.

**Accept when:** Candidate passes exact-version regression; no normal-progression/accessibility/purchased-content blocker; listings match shipped build.

**External input:** Distribution signing/account access and reviewable products.

### B22 Submit and launch under explicit release authority

**Lead:** QA and release engineer. **Entry gates:** B21. **Work:** M7-06, M7-07, M7-08.

1. Run the full content --release check and independently review the evidence pack; recheck current platform rules from official sources. Program --release is the later final-completion check, after actual launch support.
2. Prepare review notes, working products/URLs and restore instructions; submit after the concrete build/listing is authorized.
3. Resolve review findings, stage rollout where supported and assign 14-day coverage/incident escalation; stop rollout if save or entitlement integrity fails.

**Deliver:** `release/submission/`, `release/launch-record.md`, `release/coverage.json`.

**Accept when:** Both stores accept the actual build; rollout is authorized and observed; account actions and postlaunch owner are explicit.

**External input:** Store review duration, account owner authority and explicit authorization for public release.

### B23 Complete launch support and v1 handoff

**Lead:** QA and release engineer. **Entry gates:** B22. **Work:** OPS-14.

1. Inspect crash/resume/save/entitlement trends daily for 14 days after actual launch using a named operating arrangement.
2. Route incidents to owning agents; reproduce, repair, independently review and release narrowly scoped fixes with appropriate authorization.
3. Close incident follow-through, record actual shipped scope/gates/minor issues and ongoing service costs; finalize the prelaunch Season 2 brief using observed issues without expanding v1.

**Deliver:** `release/postlaunch-14-day-report.md`, `release/v1-completion.md`, `release/season-2-brief.md`.

**Accept when:** Fourteen days of real operating coverage and incident evidence exist; ongoing ownership is handed off.

**External input:** Elapsed time and an active human/scheduled operating arrangement; session agents are not an always-on service.

## 5 What is already implemented

The first agent assignments produced executable development foundations:

| Contribution | Actual files | What it establishes |
|---|---|---|
| Economy conformance exporter | [Exporter](implementation/tools/export_economy_fixtures.py), [fixtures](implementation/fixtures/economy_reference.json) | Bounded reference behaviors for later native comparison, including cost/reset/synergy and first-run cases |
| Content inventory and checker | [Manifest](implementation/content/launch_manifest.json), [checker](implementation/tools/validate_content_manifest.py) | Stable content/reward/asset identities, exact scope counts and rejection of false readiness |
| Save contract and checker | [Schema](implementation/contracts/save-envelope.schema.json), [cases](implementation/fixtures/save_contract_cases.json), [checker](implementation/tools/validate_save_contract.py) | Version/revision, operation identity and offline-settlement envelope invariants; not actual disk/cloud persistence |
| Art production contract | [Production contract](implementation/art/production_contract.json) | Per-asset production order, source/export ownership, evidence and capability gates |
| Program traceability checker | [Checker](implementation/tools/validate_program.py) | Source fingerprints, all 65 original packages, dependency ancestry, independent reviewer assignments and bidirectional scope mapping |

All 65 production items remain unaccepted. The launch registry explicitly marks final assets and authored content unfinished. The next full production batch is B01, followed by B02's native stack proof. The exact current review outcomes and remaining counts are in the [scope audit](V1_SCOPE_AUDIT.md).

Run these from the `idle` directory:

```sh
python3 implementation/tools/export_economy_fixtures.py --check
python3 implementation/tools/validate_save_contract.py --config economy.json
python3 implementation/tools/validate_content_manifest.py --self-test
python3 implementation/tools/validate_program.py --self-test
```

B14 uses `validate_content_manifest.py --content-gate`: gameplay content and assets must be complete, while final support documents receive later acceptance. B22 uses its full `--release` mode after all eight support records, including the initial Season 2 brief, are ready. `validate_program.py --release` checks final work-status coverage after B23. These modes currently fail because production remains unfinished; even a later pass is an evidence-accounting gate, not a substitute for inspecting the actual native build.

## 6 Scope protection and final acceptance

Keep the five producers, six-chapter ending, twelve challenges, twelve calibration patterns, eighteen main archive entries, one complete seasonal pass, 36 cosmetics, offline/automation behavior and ethical reward contract. Preserve all 25 producer presentations, seven harbor presentations, audio/support obligations and the selected-pass archive behavior. Do not replace them with a smaller browser game or mark placeholders as shipped content.

Public desktop distribution, extra prestige layers/producers, multiplayer, trading, guilds, competitive economic leaderboards, scripting and additional minigame genres remain outside v1. The art contract may choose formats and internal reusable parts; it cannot silently add economic rewards or sell additional progression. Changes to scope or economics need a deliberate versioned decision and an updated scope audit.

The final release record must include the exact build/config/content versions; complete inventory and reachability evidence; core/offline/precision results; save migration and interruption tests; verified purchase/restore/refund paths; equal ad/free reward results; physical-device performance/accessibility results; mature player evidence; accurate store/privacy/support materials; platform acceptance; and operating ownership. Correctness, accessibility of required flows and purchase ownership cannot be waived by a better retention number.

The AI team can produce, test, review and repair these deliverables. Public submission, spending, account enrollment and distribution still use the product owner's authority at the concrete action. No public release or always-on monitoring was initiated by creating this program.
