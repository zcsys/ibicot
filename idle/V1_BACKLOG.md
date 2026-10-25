# Tideglass v1 development backlog

This backlog implements the [v1 roadmap](V1_ROADMAP.md). Every item is planned work; the existing Python model is a reference, not a completed production ticket. Estimates are focused person-weeks for the primary contributor and must be refined after the vertical slice.

**Dependency semantics:** “Depends on” lists prerequisites for accepting the finished work package, not a requirement to wait until every upstream package is finished before starting. Packages span their milestone and exchange interfaces, fixtures and integrated slices at the roadmap's dated handoffs. Split them into smaller sprint tasks in M0; retain finish-to-start dependencies wherever implementation really cannot proceed. All 65 items are currently `not_started`.

| Role | Owner designation |
|---|---|
| PD | Product and economy designer |
| GE | Gameplay systems engineer |
| UI | Client and UI engineer |
| BE | Platform and services engineer |
| AR | 2D artist |
| QA | QA and release lead |

## M0 Scope and technical qualification

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M0-01 | Define the release contract | PD | 0.6 | — | Freeze audience, iOS/Android scope, English launch, six-chapter content budget, ethical constraints, device targets and decision owners. |
| M0-02 | Qualify engine and numeric approach | GE | 0.8 | M0-01 | Build the same deterministic purchase/reset case on both native targets; compare large-number candidates and record the engine decision. |
| M0-03 | Prove native service integrations | BE | 0.8 | M0-01 | Demonstrate sandbox purchase/restore, ad availability and cloud revision handling in a throwaway integration build; list SDK and account dependencies. |
| M0-04 | Prototype the player journey | UI | 1.0 | M0-01 | Clickable flows cover first purchase, Rechart preview, offline return and recovery; identify accessibility and small-screen constraints. |
| M0-05 | Set visual production budget | AR | 1.0 | M0-01 | Approve one harbor look, one producer milestone transformation, asset reuse rules and a complete asset manifest. |
| M0-06 | Create quality and device plan | QA | 1.0 | M0-01 | Name reference devices, severities, reproducible save fixtures, test recruitment plan and the release evidence checklist. |
| M0-07 | Establish delivery and operating costs | PD | 0.6 | M0-01 | Confirm six role assignments, contractors, distribution accounts, tester recruitment and service cost model; reforecast for holidays and absences. |
| M0-08 | Create reproducible builds | GE | 0.5 | M0-02 | Automated builds run on both targets, version configurations and preserve build artifacts; no production secrets enter the client. |

## M1 Production foundations

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M1-01 | Implement production number handling | GE | 1.2 | M0-02 | Define precision, comparison and rounding rules; pass bulk-buy and prestige-boundary fixtures including extreme values. |
| M1-02 | Implement the economy state machine | GE | 1.4 | M1-01 | Five producers, unlocks, milestones, lifetime ledger and Rechart run without rendering; explicit event ordering is tested. |
| M1-03 | Build crash-safe local saves | BE | 1.4 | M1-02 | Atomic saves, rolling backups, checksums, export/import and versioned migration recover from interruption without double rewards. |
| M1-04 | Version configuration and content schemas | BE | 1.0 | M0-08 | Validate configs, pin economic versions to saves and provide safe defaults; reject incompatible updates before application. |
| M1-05 | Build the playable client shell | UI | 2.5 | M0-04, M1-02 | Display wallet, output, producer purchases, milestones, resets and settings on small and large screens. |
| M1-06 | Design the full progression map | PD | 2.5 | M0-01 | Specify six chapter goals, ending, challenge entry requirements, Note source/sink budgets and daily/pass exceptions; no new prestige layer is assumed. |
| M1-07 | Produce reusable visual components | AR | 2.4 | M0-05 | Deliver modular producer parts, harbor layers, typography, icons and UI states sufficient for the slice. |
| M1-08 | Port oracle cases and failure fixtures | QA | 2.5 | M1-01, M1-02, M1-03 | Existing checks become production fixtures; add save corruption, rounding, rapid reset and interrupted-transaction cases. |

## M2 Vertical slice

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M2-01 | Complete the first-session economy | GE | 2.7 | M1-02 | Cross-tier synergies, free autobuy unlock and baseline offline replay support first session through 25 Charts with deterministic results. |
| M2-02 | Build onboarding and Rechart communication | UI | 1.4 | M1-05, M2-01 | Teach costs, production, retained progress and automation with skippable guidance; no monetization prompt interrupts onboarding. |
| M2-03 | Add purchase and reset forecasts | UI | 1.3 | M2-01 | Show marginal network output, next threshold and conditional reset estimate with readable assumptions and no claim of a universal optimum. |
| M2-04 | Implement optional cloud recovery | BE | 2.6 | M1-03, M1-04, M0-03 | Save revisions detect conflicts; divergent branches remain recoverable; never add two wallets or replay overlapping offline time. |
| M2-05 | Finish representative harbor presentation | AR | 2.7 | M1-07 | One area, all five base silhouettes and a milestone sequence establish final visual quality, including reduced-motion variants. |
| M2-06 | Run moderated first-session studies | PD | 2.6 | M2-02, M2-03, M2-05 | At least 15 new testers attempt the first reset; capture understanding, friction and pacing, then resolve the largest blockers. |
| M2-07 | Certify the vertical slice | QA | 2.7 | M2-01, M2-04, M2-05 | Replay purchase/reset/save/resume on reference hardware; publish a slice gate report and evidence for the next funding decision. |

## M3 Complete game systems

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M3-01 | Implement all real-time boundaries | GE | 1.6 | M2-01, M1-03 | 2-hour Focus, 8-hour Surveys, 24/72-hour offline envelope, bonus expiry and account-day boundaries resolve in a single event timeline. |
| M3-02 | Implement contracts and their backlog | GE | 1.2 | M3-01, M1-06 | Seeded contracts, snapshots, offline progress, rerolls and 21-slot backlog preserve claim IDs and do not duplicate rewards. |
| M3-03 | Implement player automation plans | GE | 1.3 | M2-01, M1-06 | Purchase priorities and opt-in reset conditions work identically online/offline; free base plan and Note-priced extra slots follow the blueprint. |
| M3-04 | Build calibration and daily interfaces | UI | 2.1 | M3-01, M3-02 | Untimed calibration, equal-value accessible completion, queued Focus, Surveys and contract management form a complete daily session. |
| M3-05 | Complete settings and notification controls | UI | 1.8 | M1-05, M3-01 | Text scale, number notation, motion/audio controls, input navigation and opt-in quiet-hour notifications function across targets. |
| M3-06 | Complete account lifecycle and branch recovery | BE | 2.0 | M2-04 | Guest linking, account recovery, export, deletion and divergent-save selection preserve recovery copies and purchased ownership. |
| M3-07 | Build the entitlement and claim ledger | BE | 1.9 | M0-03, M1-04, M3-06 | Unique receipts and idempotent grants separate cosmetics, Support allowance, pass XP and gameplay saves; interrupted grants resume safely. |
| M3-08 | Author chapter and challenge specifications | PD | 3.8 | M1-06, M2-06 | Six chapters and twelve challenges have objectives, unlock rules, reward budgets and completion evidence; passive and active routes are covered. |
| M3-09 | Produce producer transformations and core UI art | AR | 4.0 | M2-05 | Five producer families each have base plus four milestone presentations; daily-loop icons and status states are final. |
| M3-10 | Validate the entire daily timeline | QA | 4.1 | M3-01, M3-02, M3-03, M3-06, M3-07 | Test 1/3/6 visits, 2/8/24/48/72-hour absences, clock changes, bonus queues and reset/day-boundary collisions; report exact and approximate differences. |

## M4 Content and commerce complete

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M4-01 | Build reusable challenge scenarios | GE | 2.0 | M3-08, M3-03 | Challenge state is isolated, goals are deterministic, main automation continues and exit/restart cannot export economic rewards. |
| M4-02 | Build the seasonal event state machine | GE | 2.0 | M4-01, M3-01 | Season start/end/archive, event coefficients, pinned versions and offline transitions work; no paid or main-world power enters the event. |
| M4-03 | Build cosmetic shop and pass experience | UI | 4.0 | M3-07, M4-02 | Preview, price, ownership, restoration, selected pass and archived completion are understandable; shared XP grants only once. |
| M4-04 | Integrate production purchase handling | BE | 2.2 | M3-07, M0-03 | Validate, grant, acknowledge, restore and reconcile purchases; pending, duplicate, refunded and interrupted cases have explicit states. |
| M4-05 | Integrate optional ads and equal free rewards | BE | 1.9 | M3-07, M3-01 | Ad and briefing routes consume the same allowance; no-fill, refusal and duplicate callbacks preserve access and cannot multiply rewards. |
| M4-06 | Finish all launch content and reward tables | PD | 4.1 | M3-08, M4-01, M4-02 | Six chapters, ending, twelve challenges, twelve calibration patterns, eighteen archive entries and Season 1 have complete data and copy. |
| M4-07 | Finish launch art and cosmetics | AR | 4.1 | M3-09, M4-06 | Six harbor restoration states and the fixed 36-item cosmetic manifest are complete; commissioned audio is integrated through client work. |
| M4-08 | Verify content and monetization boundaries | QA | 4.1 | M4-03, M4-04, M4-05, M4-06, M4-07 | Every content ID and reward is reachable; full pass is completable free of paid speed; no event or cosmetic increases core power. |

## M5 Beta readiness

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M5-01 | Optimize runtime and offline replay | GE | 2.7 | M3-10, M4-02 | Meet measured frame/startup/resume budgets on minimum devices; heavy replay is chunked and never silently drops earned time. |
| M5-02 | Complete accessibility and language readiness | UI | 2.7 | M3-05, M4-03, M4-06 | Critical flows work at large text, without color/audio/motion dependencies and via target inputs; pseudolocalization has no blocking overflow. |
| M5-03 | Complete privacy and service recovery flows | BE | 1.4 | M3-06, M4-04, M4-05 | Data inventory matches SDK behavior; consent refusal, export/deletion and service-outage recovery are verified on actual builds. |
| M5-04 | Ship measurement and operating tools | BE | 1.3 | M3-07, M4-04 | Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging. |
| M5-05 | Run long-horizon economy and content audit | PD | 2.7 | M4-06, M5-04 | Simulate 30/90 days across visit and bonus policies, audit Note sinks and content pacing, freeze beta config and metric definitions. |
| M5-06 | Complete presentation and store assets | AR | 2.7 | M4-07 | Remove placeholders, integrate final sound direction, and prepare representative screenshots, icon and short footage. |
| M5-07 | Run device and migration regression | QA | 1.7 | M5-01, M5-02, M5-03 | Complete the device matrix, storage/network interruptions, upgrade migrations and install/return flows with zero open blocking issues. |
| M5-08 | Run commerce and service fault tests | QA | 1.1 | M4-04, M4-05, M5-04 | Purchase/restore/refund/ad callbacks are tested under packet loss, retries, duplicate messages, crashes and backend outages. |

## M6 Player validation

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M6-01 | Recruit and freeze the measurement cohort | PD | 1.8 | M5-05, M5-07, M5-08 | Enroll the D30 cohort during week 27; record baseline config, acquisition source, denominator and exclusions before analysis. |
| M6-02 | Evaluate retention and content outcomes | PD | 2.3 | M6-01 | Report mature D1/D7/D30 with confidence intervals, campaign progress, bonus impact, satisfaction and explicit ship/change decisions. |
| M6-03 | Resolve economy and simulation findings | GE | 3.6 | M5-01, M6-01 | Fix core bugs using replay fixtures; version any balance changes and keep affected cohorts separate. |
| M6-04 | Resolve comprehension and interaction findings | UI | 3.6 | M5-02, M6-01 | Reduce observed onboarding/recovery friction without adding pressure, hidden rewards or paid advantages. |
| M6-05 | Operate staged access and support | BE | 3.7 | M5-04, M6-01 | Exercise service load, support recovery, purchase reconciliation and feature disable controls with real opt-in testers. |
| M6-06 | Polish content from observed play | AR | 2.4 | M5-06, M6-01 | Address readability, repeated visual issues and content defects without increasing the launch asset count. |
| M6-07 | Observe real calendar progression | QA | 2.1 | M6-01 | A real 28-day pass and mature D30 cohort are observed; accelerated testing is documented separately. |
| M6-08 | Rehearse season and release recovery | QA | 2.1 | M4-08, M6-05 | Exercise season archive, paid pass continuation, save migration, purchase replay and compatible rollback/forward repair. |

## M7 Release

| ID | Deliverable | Owner | Person-weeks | Depends on | Acceptance evidence |
|---|---|---|---:|---|---|
| M7-01 | Decide readiness and freeze release scope | PD | 2.0 | M6-02, M6-07, M6-08 | Review all hard gates and product thresholds, assign accepted minor issues, and freeze the release candidate configuration. |
| M7-02 | Stabilize final game build | GE | 2.1 | M6-03, M7-01 | Fix remaining blockers, tag deterministic core/config versions and prove candidate replay compatibility. |
| M7-03 | Package native release candidates | UI | 2.1 | M6-04, M7-01 | Signing, install/update, responsive layouts, licensed assets and store-visible flows work in final distribution builds. |
| M7-04 | Prepare safe staged release | BE | 1.8 | M6-05, M7-01 | Version-compatible config rollback, feature disables, capacity, backups and entitlement replay are rehearsed and documented. |
| M7-05 | Finish store communication and support material | AR | 2.0 | M6-06, M7-01 | Screenshots, footage, credits, help visuals and release assets describe the actual shipped game and offers. |
| M7-06 | Approve the release evidence pack | QA | 1.6 | M7-02, M7-03, M7-04 | All gate evidence is linked; no blocker, save-loss, duplication or unresolved purchase-delivery issue remains. |
| M7-07 | Submit and manage platform review | QA | 1.1 | M7-05, M7-06 | Recheck current platform requirements, provide reviewer access and working products, and resolve review findings before launch. |
| M7-08 | Hand over launch operations | BE | 0.9 | M7-04, M7-06 | Document 14-day coverage, escalation, incident response and Season 2 preparation; launch authority and rollout stop conditions are explicit. |

## Capacity check

| Role | Planned focused person-weeks | Available at 70 percent of 36 weeks |
|---|---:|---:|
| Product and economy designer | 23.0 | 25.2 |
| Gameplay systems engineer | 23.1 | 25.2 |
| Client and UI engineer | 22.5 | 25.2 |
| Platform and services engineer | 22.9 | 25.2 |
| 2D artist | 21.3 | 25.2 |
| QA and release lead | 24.1 | 25.2 |
| **Total** | **136.9** | **151.2** |

This is an aggregate and milestone-level capacity check, not a proven resource-leveled schedule. The 36-week target relies on the incremental handoffs in the roadmap; interpreting all links as finish-to-start gives a 59.2-week lower bound before resource conflicts. Real start dependencies, integration windows, holidays, contractors and specialist availability must be placed on the sprint calendar in M0. A gate can move even when total capacity fits.

