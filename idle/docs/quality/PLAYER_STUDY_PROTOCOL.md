# Tideglass player validation protocol

Version 1, 16 October 2026. Status: prepared, **no participants recruited or observed**. User reports no tester access. This protocol protects the original M2/M6 gates; the AI team is not a substitute population. Director signs the enrollment version before any recruitment or data collection. A material change to onboarding, rewards, economics or seasons creates a new cohort/config label and may require new observation.

## Recruitment and consent

Director owns recruitment and any authorized spend; QA owns moderation and analysis. Proposed channels are an authorized adult playtest panel, opt-in game communities, and volunteer referrals outside the development team. These are options for later approval, not outreach already sent. Do not contact people or buy recruitment without authorization. Recruit first-time Tideglass players, English readers, age 18+, across iOS/Android and idle-game familiarity; recruit deliberately for large-text/reduced-motion/screen-reader needs rather than excluding them. The adult study is not evidence about younger players.

Before enrollment, provide a short plain-language information sheet covering the purpose, duration, what is recorded, voluntary withdrawal, contact, deletion process and data retention. Record consent separately from gameplay data. Collect pseudonymous participant/install IDs and necessary device/version facts; do not record passwords, payment details or unrelated device content. Recording is optional and requires separate consent. Compensation, if later funded, is fixed for time and never tied to reaching a milestone, watching ads or making purchases. Use store sandbox accounts for commerce tasks. A declined optional recording or ad does not disqualify the participant.

The current project has no approved hosted study database or published contact endpoint. Those must exist and be checked before enrollment. Raw study data is restricted to authorized study staff; public reports use aggregates and redacted excerpts. Freeze the specific retention/deletion period and consent wording with the actual operating setup before collecting data; this document does not invent a legal policy or claim legal review.

## Moderated first-session study: 15 new players

Schedule one 45–60 minute session per participant. At least 6 participants use each native platform; the remaining 3 balance device/access needs. Do not let staff or prior Tideglass testers satisfy the 15-person denominator. Recruit backups for scheduling, but never replace a player because their result is inconvenient. Log all consented starts, failures, withdrawals and missing observations.

1. Show the consented candidate on a fresh guest save, explain that the product is being tested, and ask the participant to play naturally. Do not explain the economy before baseline observation.
2. Observe first purchase, next-tier discovery and the player's chosen strategy. Record time from first interactive harbor, help requests, misclicks and blockers. Moderator intervention is time-stamped; report assisted and unassisted results separately.
3. Allow up to 45 minutes of natural play for first-prestige eligibility. Record eligibility time and commit time separately. Report median eligibility among reachers, the full reacher count, and every non-reacher/withdrawal; do not call accelerated or seeded runs natural pacing.
4. Ask open questions before showing answers: “What would you lose by Recharting?”, “What would stay?”, “What changes after Recharting?”, “What would happen if you returned after two days?” Score against the rubric below; avoid leading prompts.
5. After natural pacing measurement, a separate labelled seeded scenario may demonstrate offline return, recovery, calibration's accessible route and automation. It supports task comprehension and access findings, never first-session timing.
6. Ask about clarity, meaningful choices and whether the experience pressures check-ins, ads, purchases or sleep interruption. Record concrete examples. End with a debrief and withdrawal/contact information.

| Rubric item | Required understanding |
|---|---|
| Reset losses | Current wallet and purchased producer fleet reset |
| Reset retention | Charts/permanent power and lifetime progress remain; the starting Skiff returns |
| Offline rule | A saved fleet continues earning; first 24 h full, next 48 h quarter, no production beyond 72 h; no requirement to check every 2 h |
| Agency | Rechart is a choice; temporary bonuses are optional; accessible calibration has equal value |

Primary comprehension endpoint: participant correctly explains reset losses, retention and offline rule without corrective prompting. Freeze scoring examples before first session; a second non-moderator independently scores anonymized responses. Record disagreements before resolution. The target is at least 12/15 (80%), with failures reviewed individually; this small sample is descriptive and does not establish an 80% population rate. The agency response and accessibility task performance are secondary qualitative outcomes, with no dismissal of serious defects because aggregate comprehension passes.

The timing target is a median 15–30 minutes among natural reachers plus the complete non-reacher fraction. A seeded Rechart cannot fulfill this gate. Zero major required-flow accessibility failures remains a hard requirement independent of the comprehension fraction.

## Main longitudinal cohort

Preregister before enrollment: candidate/config/content and acquisition sources; eligibility/exclusions; primary endpoint and duration; session definition; telemetry consent/observability; data cutoff; missing-data handling; subgroup reporting; analysis version. Planning target: 500 eligible first-launch installs and 10,000 real sessions. Continue observation until each D30 denominator member has its full window. The season requires 28 actual elapsed days, including close/archive and missed-day/paid-pass continuation cases. Faster simulated clocks are separate engineering results.

Primary descriptive endpoint: D7 return rate on the preregistered candidate cohort. Secondary: D1/D30, campaign/season progression, strategy choices, return processing, crashes, welfare and voluntary commercial participation. This is an observational baseline, not a causal claim about a feature.

Define first launch as the earliest valid persisted app-start for an eligible install, before harbor loading or onboarding; startup failures and onboarding departures remain in the denominator. Natural gameplay pacing starts at the first interactive harbor and reports startup failures separately. A valid return session contains an interactive foreground harbor and a foreground activity event; exclude repeated background pings. Session starts after 30 minutes of inactivity or process restart; retain a stable session ID so retries deduplicate. Freeze implementation details before enrollment and validate telemetry against local event logs. Dn uses the half-open install-age window `[24n, 24(n+1))` hours. Use all eligible installs with full observation opportunity, including people who left during onboarding. Staff, automation and proven invalid installs are excluded by fixed rules, not by low engagement. Report opt-out/unobservable installs and missing telemetry separately; telemetry-observed retention cannot be described as all-player retention without qualification.

Crash-free sessions require a real observed denominator and validated crash/session linkage. Report counts and intervals overall and by native platform/device group, review every critical-flow crash, and retain opt-out/missing-data limitations. 100 simulated sessions repeated 100 times do not satisfy 10,000 sessions. Quantify first-session non-reachers and censored follow-up; do not silently discard them.

## Precision and optional experiments

Use 95% Wilson intervals for descriptive proportions. At exactly 500 observable mature installs, rates near the provisional hypotheses would have these approximate intervals (planning calculation, not observed performance):

| Rate hypothesis | Approximate 95% interval at n=500 |
|---|---|
| D1 .35 | .3095–.3928 |
| D7 .15 | .1214–.1840 |
| D30 .07 | .0508–.0958 |

The 500-start target does not guarantee causal power. No A/B experiment is currently authorized or preregistered. If one is proposed, specify one primary outcome, randomization unit, two-sided alpha, target power, baseline rate, smallest useful effect, allocation, attrition allowance and stopping rule before assignment. For rough two-arm planning with 250 per arm, alpha .05 and 80% power, the null-variance normal approximation yields absolute detectable differences of about .1195 at p=.35, .0895 at p=.15, and .0639 at p=.07. These are illustrative MDE approximations, not a promise; compute the actual design's power under the proposed alternative, including clustering/multiple comparisons and expected missingness. Do not repeatedly inspect and stop when a result becomes favorable.

A release review uses the 35/15/7% retention hypotheses to choose launch, extend observation or revise. Correctness, ownership, access and free/ad fairness cannot be waived for high retention. Record low check-in feasibility, late-chapter walls and at least two understandable strategy approaches. Commercial reports use observed conversion/participation and actual service/support costs, without inventing profitable acquisition.

## Instruments and output

`release/qa/study-instrument.json` defines the empty record schema and required report fields. No synthetic participant rows are shipped as observations. Deliver redacted session records, score agreement, all denominators, timing distributions, uncertainty, cohort/version/acquisition breakdown, known missingness, welfare findings and the director's explicit launch/extend/revise decision. QA independently checks the analysis against raw consented records and verifies full elapsed windows.
