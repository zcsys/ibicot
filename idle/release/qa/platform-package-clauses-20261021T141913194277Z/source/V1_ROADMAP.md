# Tideglass v1 development roadmap

Tideglass v1 is a complete, releasable single-player game: a coherent campaign with an ending, an optional continuing economy, a dependable daily loop, a finished first season, recoverable progress, and functioning cosmetic commerce. The production plan is **36 weeks with six dedicated core roles, plus four weeks of contingency and 14 days of launch support**. The user confirmed a small team of five to six people; the six-person case is the scheduling baseline.

This roadmap builds on [the economic blueprint](TIDEGLASS_DESIGN.md). The detailed [65-item backlog](V1_BACKLOG.md) and [structured backlog](v1_backlog.json) supply owners, dependencies, estimates and acceptance evidence. All production tickets are not started. Existing research and Python experiments are inputs to development, not a shipped foundation.

## 1 Release contract and planning assumptions

| Dimension | v1 baseline |
|---|---|
| Public launch platforms | iOS and Android, phone-first with usable tablet layouts |
| Shared desktop build | Internal development, automation and playtesting; public desktop distribution is a later release |
| Presentation | 2D harbor, animated producers, readable economic panels; no 3D world or free-placement construction system |
| Play model | Single-player, playable locally without a mandatory account; optional cloud recovery |
| Online dependencies | New purchases, ads, cloud sync and fresh event manifests require connectivity; the core economy and cached content remain playable |
| Launch language | English, with all text externalized and pseudolocalization tested; extra translations are a separately staffed decision |
| Commercial model | Optional rewarded ads with an equal free route, fixed cosmetic offers and a cosmetic seasonal pass |
| Content goal | A campaign intended to remain meaningful over roughly 15–30 calendar days of ordinary play, followed by optional mastery and collection |
| Schedule basis | Six full-time roles, relevant experience, funded specialist support and no major engine rewrite |
| Calendar basis | Relative weeks are authoritative; illustrative dates assume work starts Monday 19 October 2026 |

The content duration is a playtest target, not a hard calendar lock. Skilled or highly active players may finish earlier. v1 does not depend on an endless content treadmill to feel complete.

**Finished means a player can install, learn, build all five producer tiers, Rechart, automate, leave and return, recover a save, complete the main restoration, play optional challenges, finish or revisit the first seasonal pass, and keep playing without a placeholder or a promised future system blocking progress.** Commercial purchases must be deliverable and restorable. The live team must be able to diagnose problems and stop a harmful rollout.

If only five dedicated people are available, retain explicit QA/release coverage and reforecast approximately 42–48 production weeks before contingency. This is a planning range, not a linear staffing guarantee. Do not preserve a six-person date by silently assigning two full-time jobs to one person.

## 2 What exists and what remains

| Existing artifact | Useful evidence | Remaining production work |
|---|---|---|
| `economy.json` | Exact baseline economic parameters | Schema validation, economic versioning and content integration |
| `economy.py` | Purchases, milestones, prestige, synergies and restricted timing experiments | Production arithmetic, event chronology, complete automation and real-time systems |
| `validate.py` | 203 passing reference checks; independent one-hour comparison | Native runtime fixtures, property tests, crash recovery, integration and device coverage |
| First-run simulations | Approximately 16.75 minutes to initial prestige under the reference policy | Human comprehension and population pacing |
| Blueprint | Sources, formulas and proposed product rules | Client, assets, campaign, services, purchases, ads, analytics, operations and release |

The Python implementation remains the comparison model. Port its behavior into the production core; do not embed the exploratory script in the client or mistake its float arithmetic for an arbitrary-range currency ledger.

## 3 Scope of a complete v1

### Core systems

| System | Required shipped behavior |
|---|---|
| Construction | Five producers; single, milestone and maximum purchases; cost, output and marginal network value displayed |
| Milestones | Whole-tier multipliers at 25, 50, 75 and 100 ownership; matching presentation |
| Rechart | Lifetime entitlement minus previously awarded Charts; accurate reset preview and retained-progress list |
| Automation | Free basic autobuying at 10 Charts; synergies at 25; opt-in conditional reset plans at 100; one free base plan and Note-priced extra slots |
| Forecasts | Next purchase and prestige estimates with assumptions; no claim of universal optimality |
| Offline progress | Complete simulation of saved policies and timer boundaries, using the blueprint's 24-hour full-rate and 48-hour quarter-rate tail |
| Daily systems | Focus, Surveys, seeded contracts, rerolls, seven-day backlog and optional notifications |
| Active activity | Untimed calibration, queued Focus and an equal-value accessible completion |
| Persistence | Atomic local saves, backups, export/import, migration, optional cloud recovery and explicit conflict handling |
| Seasonal play | Isolated event state, shared contract-XP ledger, cosmetic-only exports, archived completion and one selected pass at a time |
| Commerce | Cosmetic preview, localized store price, purchase status, verified delivery, restore and refund/revocation handling |
| Settings and help | Text scale, motion/audio controls, number notation, target input support, contextual explanations, recovery and support entry points |

The existing economic constants remain the initial baseline: tier step 20, purchase growth 1.12, prestige exponent 0.65, permanent power `1 + sqrt(P/10)`, and the documented synergy matrix. Changes require versioned simulations and a written reason; the roadmap does not introduce another prestige currency.

### Launch content inventory

These quantities are proposed v1 scope commitments to ratify in M0, not content already created by the blueprint.

| Content | Quantity and completion standard |
|---|---|
| Main harbor | One environment, the initial unlit presentation and six restored presentations |
| Campaign | Six chapters with explicit objectives, an ending and a clear invitation to continue |
| Producers | Five families, each with a base and four milestone presentations: 25 presentations in total, built from reusable parts |
| Challenge dossiers | Twelve authored challenges across three rule families: constrained fleets, changed synergy priorities and automation planning |
| Calibration | Twelve authored patterns with non-reflex completion options |
| Main archive | Eighteen short entries tied to restoration and discovery |
| First season | Night of Returning Stars, 28-day live presentation, isolated fleet, finished start/end/archive flow |
| Pass | 30 levels at 500 XP; 30 free reward slots containing ten cosmetics and twenty short archive fragments; ten additional premium cosmetics at selected milestones |
| Visual cosmetics | 36 unique items: twelve earned through core play, ten free-pass items, ten premium-pass items and four direct-shop items |
| Audio | A coherent ambient score, interaction feedback, milestone/Rechart cues and independent volume controls; soundtrack delivery for the supporter offer |
| Support content | Help, recovery guide, release notes, credits, privacy/support pages and operational runbooks |

The supporter collection bundles existing shop cosmetics and the soundtrack rather than adding an unbudgeted asset set. Rewards have no production multipliers. Additional text fragments are narrative rewards, not another currency.

Suggested campaign beats are: first light and Rechart; network synergies; daily planning and the archive; challenge experimentation; automation mastery; complete restoration. The first two can fit an initial session. Later goals must add decisions and narrative progress, not simply increase an earnings threshold. M1 specifies unlocks and M5 tests their 30-day distribution. The ending does not require buying every optional Note sink or finishing a paid pass.

### Scope reserved for later releases

Public desktop/Steam distribution, additional prestige layers, more producer tiers, multiplayer, trading, guilds, competitive economic leaderboards, user scripting, user-generated content, additional minigame genres and further languages are outside the baseline. A Season 2 brief and operating plan are required at launch; a second fully produced season is not included in v1's asset budget.

## 4 Team and capacity

| Role | Accountable work | Planned focused person-weeks |
|---|---|---:|
| Product and economy designer | Scope, economy, progression, content, player studies and product decisions | 23.0 |
| Gameplay systems engineer | Numbers, economy, simulation, automation and challenges | 23.1 |
| Client and UI engineer | Native client, interaction, accessibility, input and release packaging | 22.5 |
| Platform and services engineer | Saves, accounts, entitlements, SDKs, telemetry and operations | 22.9 |
| 2D artist | Harbor, producers, interface art, cosmetics and store creative | 21.3 |
| QA and release lead | Test evidence, devices, failures, cohorts, certification and submission | 24.1 |
| **Total** | **65 production work packages** | **136.9** |

Six people over 36 weeks provide 216 gross person-weeks. At 70% focused delivery availability, the working envelope is 151.2 person-weeks, leaving 14.3 within that envelope for estimation error and unassigned integration work. The remaining gross capacity covers reviews, planning, communication, leave and interruptions. The four calendar weeks of contingency are separate and must be funded if used.

The backlog fits the 70% capacity envelope for each role within each milestone. Its entries are multiweek work packages with incremental handoffs, not indivisible tasks. Listed dependencies are prerequisites for accepting the completed package; downstream work can start against an agreed interface, content manifest or test fixture while implementation continues. QA prepares cases early and verifies each delivered slice.

This distinction is essential to the estimate. Treating every listed dependency as strictly finish-to-start produces a lower bound of approximately 59.2 weeks even before resource conflicts. The 36-week target therefore requires the handoffs below. It is not a fully resource-leveled commitment: M0 must split packages into sprint tasks and check sequencing, vacations and cross-role reviews. If those handoffs are infeasible, reforecast rather than hiding the delay in the four-week reserve. QA is the tightest role and should not absorb production art or account administration.

Budget additional specialist support rather than assuming the six roles supply every discipline: approximately four focused person-weeks of UX support early, three of audio across slice/content production, and two of editorial/language QA before beta. Obtain separate privacy/security/platform advice where needed. These are planning allowances, not vendor quotations.

The cash budget should use actual loaded role costs for the staffed calendar, plus specialists, hardware, developer accounts, services, recruitment and contingency. The 136.9 focused effort estimate is not the payroll budget. M0 produces the cost model; no acquisition or revenue return is assumed.

## 5 Milestones and dependency order

| Milestone | Weeks | Illustrative dates | Result required to advance |
|---|---|---|---|
| M0 Scope and technical qualification | 1–2 | 19 Oct–1 Nov 2026 | Approved scope, native feasibility, owners and build path |
| M1 Production foundations | 3–6 | 2–29 Nov 2026 | Deterministic economy, durable local state and a playable shell |
| M2 Vertical slice | 7–10 | 30 Nov–27 Dec 2026 | A representative first session through prestige and synergies on devices |
| M3 Complete game systems | 11–16 | 28 Dec 2026–7 Feb 2027 | Every core loop works in an integrated alpha |
| M4 Content and commerce complete | 17–22 | 8 Feb–21 Mar 2027 | Entire campaign, season, cosmetics and purchase paths are implemented |
| M5 Beta readiness | 23–26 | 22 Mar–18 Apr 2027 | Stable, instrumented and recoverable distribution builds |
| M6 Player validation | 27–32 | 19 Apr–30 May 2027 | Mature D30 evidence, a real seasonal cycle and resolved major findings |
| M7 Release | 33–36 | 31 May–27 Jun 2027 | Platform acceptance, launch gates passed and controlled public rollout |
| Contingency | Up to 4 weeks | Through 25 Jul 2027 if needed | Reserved for gate failures and external review delays |
| Launch support | 14 days after actual launch | Depends on launch | Stable operations, incident follow-through and next-content handoff |

This yields a provisional June–July 2027 launch window if work begins on the illustrative date. It is not a public release commitment. Holiday coverage and platform review variability must be reflected when the schedule is staffed.

The controlling dependency chain is **native feasibility → number/state model → durable save and offline simulation → representative player experience → full systems/content/commerce → stable measurement build → real 30-day observation → release acceptance**. Art, services and content proceed alongside the core, but each milestone is accepted on an integrated build.

### Required handoffs within milestones

| Milestone | Early handoff that unlocks parallel work | Integrated checkpoint and acceptance |
|---|---|---|
| M0 | Day 1 scope draft and flow priorities permit probes and prototypes; resolve native choice during week 2 | Native qualification precedes final build setup; accept scope and feasibility at the end of week 2 |
| M1 | Week 3 state/number interfaces, sample saves and UI fixtures; week 4 first purchase/reset path | Week 5 integrates persistence and shell; week 6 resolves boundary and recovery defects |
| M2 | Week 7 first-reset build and presentation components; week 8 representative onboarding and return flow | Week 9 moderated studies; week 10 addresses findings and accepts the complete slice |
| M3 | Week 11 timer/claim contracts; weeks 12–14 add daily systems and account flows in testable increments | Weeks 15–16 exercise combined histories and resolve alpha blockers |
| M4 | Week 17 locks reward/asset identifiers and interface contracts; weeks 18–20 deliver challenges, pass, content and transactions incrementally | Weeks 21–22 finish integration, exhaustive reward coverage and content acceptance |
| M5 | Week 23 starts from the complete M4 build; telemetry definitions and recruitment materials are ready by week 24 | Weeks 25–26 finish faults, device regression and beta configuration freeze |
| M6 | Week 27 enrolls the principal cohort; fixes and support run alongside observation | Week 32 accepts mature D30 and the seasonal-cycle report; a material experience change may require a later cohort |
| M7 | Early week 33 readiness decision unlocks candidate preparation; freeze candidate by the end of week 34 | Submit by week 35 where feasible; review, rollout and release acceptance occupy the remainder and contingency if necessary |

The initial interfaces and draft manifests unlock work; the final producer packages still have to pass their acceptance criteria before consumers can be accepted. In particular, preparing tests early does not count as passing them. M0 must allocate effort between preparation, integration and correction so the final checkpoint has real capacity.

### M0 Scope and technical qualification

Close the decisions that can invalidate later work. Select a supported production engine only after a short native export, purchase/restore and ad-integration probe; preserve the headless economy boundary whichever engine wins. Record the numeric representation and large-number comparison strategy. Set the minimum hardware/OS test matrix, screen/input assumptions, launch territories, audience classification, account method and SDK inventory.

Prototype four flows: first purchase, Rechart, offline return and save recovery. Approve one representative visual treatment and a reusable asset strategy. Set the budget, role assignments, contractor bookings, tester recruitment and the source of each release requirement.

**Exit:** both native targets can run a representative build, native service risks have an owner and evidence, all work packages are scheduled, and scope fits available people. If native feasibility fails, resolve the engine/platform choice now rather than carrying the uncertainty into content production.

### M1 Production foundations

Implement the economy as a deterministic state machine independent of rendering. Cover prices, batch purchases, milestones, lifetime accounting and reset entitlement. Specify precision and rounding before writing UI purchase logic. Define versioned state/configuration formats, atomic persistence, backups and migrations. Deliver a plain but playable shell.

The designer authors the six-chapter map, challenge rule families, Note spending opportunities and remaining daily/pass edge cases. QA converts the reference model into fixtures and adds faults that were absent from the Python experiment.

**Exit:** repeatable input histories produce the same discrete outcomes; boundary cases cannot create free Charts or purchases; interruptions recover to a valid state. Test failure is a foundation issue, not something to hide with a display fix.

### M2 Vertical slice

Deliver a polished representative journey: gifted Skiff → five producers → first Rechart → autobuying → synergy explanation → close/return → recovered progress. Include readable forecasts, one production-quality harbor presentation, sound direction and the save/conflict experience.

Run moderated first-session studies with at least 15 genuinely new testers. Observe whether they can explain the purchase rate, reset tradeoff and retained progress without prompting. Separate comprehension observations from the idealized 16.75-minute simulation result.

**Exit:** players can navigate the loop, the production art is affordable to extend, and the client/save/simulation design is viable on reference devices. Target at least 80% correct explanation of the reset and offline rules in this small qualitative sample; investigate every critical misunderstanding. This is a learning gate, not a statistically powered retention claim.

### M3 Complete game systems

Implement all real-time systems: Focus, Surveys, bonus queues, contracts/backlog, account-day boundaries, automation plans and opt-in notifications. Complete account recovery and entitlement/claim storage before real commerce is integrated. All controls and accessibility settings must function, even while some final art is still in production.

The alpha includes the entire daily session and meaningful progression through the system unlocks. Author all campaign/challenge goals, text needs and reward tables. Finish the 25 producer presentations using the agreed modular asset approach.

**Exit:** no central system is still represented only by a mockup; time, reset, claim and save boundaries have combined tests. The same policy yields matching discrete results online and offline, and one daily collection can retain the stated Focus and Survey generation.

### M4 Content and commerce complete

Build challenge scenarios and the isolated seasonal state machine. Populate all six campaign chapters, ending, twelve challenges, twelve calibrations, eighteen main archive entries and the first pass. Complete shop previews, saved ownership, pass selection and archive continuation.

Integrate verified purchase delivery, restoration, reconciliation and failure states. Integrate optional ads only through the same Support-token ledger as the free route. Finish the launch cosmetic manifest and harbor restoration presentations.

**Exit:** the game can be completed from a fresh profile and the entire first season is traversable with accelerated test time. Every reward and product has a manifest entry, fulfillment path and test. The economy receives no value from cosmetics or event exports. Accelerated season coverage does not replace M6's real-time observation.

### M5 Beta readiness

Optimize runtime, offline processing, loading and thermal behavior on the named hardware. Finish large-text layouts, input navigation, help and English text; run pseudolocalization to expose future expansion problems. Audit real SDK network/data behavior against declarations and consent flows.

Run 30/90-day simulations across purchasing, reset, visit-frequency and bonus policies. Audit Note scarcity and collection duration. Make event and contract content changes before the measurement build is frozen. Validate telemetry, support tools, backups, alerting and feature-disable controls.

**Exit:** distribution builds meet technical beta gates; instrumentation is trustworthy; there are no open save-loss or purchase-delivery blockers. Recruit testers before M6 so a lack of participants does not silently consume the observation window.

### M6 Player validation

Use six calendar weeks for closed testing and a controlled soft launch. Enroll the principal D30 cohort during week 27 so its final day-30 outcomes mature by the end of week 32. Keep the baseline configuration recorded; if a material rebalance changes experience, analyze the affected cohort separately and extend the gate when necessary.

Aim for at least 500 eligible new-player starts and 10,000 observed sessions across the study window. These are planning sample targets subject to recruitment funding. If recruitment falls short, state the remaining uncertainty and extend observation rather than inventing confidence. Do not divide a small cohort into numerous underpowered tests.

Follow a real 28-day pass, ending/archive transitions, missed-day recovery and paid-pass continuation. Audit full progression trajectories with and without optional bonuses: the blueprint's nominal 3.75% steady-state bonus budget is not a bound on compounded advantage.

**Exit:** D30 is actually mature, technical gates hold, major player-friction findings are resolved, and the product owner has an evidence-backed ship/change decision. A month-long synthetic simulation cannot satisfy this gate.

### M7 Release

Freeze content and economic versions, produce the release candidate and complete install/update/store tests. Recheck platform requirements close to submission, submit complete listings and reviewer instructions, and address review findings. Prepare support, monitoring and escalation coverage before opening access.

Roll out in controlled steps where platform controls permit. Observe crashes, startup/resume failures, save conflicts and entitlement delivery at each step. Disable an affected optional feature or pause rollout when necessary. Compatible configuration rollback is allowed; an older executable must not read a newer save unless explicitly supported. Prefer a forward repair when saves have migrated.

**Exit:** the public build is accepted, the release evidence pack is complete, no blocking issue remains, and the team can support the live product. Keep 14 days of named coverage after the actual launch date; this requirement moves with launch.

## 6 Architecture and state contracts

| Boundary | Production responsibility | Important dependency |
|---|---|---|
| Economy core | Pure state transitions, number operations, purchases, resets, milestones and network output | Chosen precision and validated configuration |
| Timeline simulator | Online/offline advancement, affordability events, real timers and automatic actions | Economy state and explicit event ordering |
| Client presentation | Input, display, accessibility, animation and forecasts | Reads the core; never duplicates reward arithmetic |
| Local persistence | Atomic saves, backups, migrations, export/import and pending transaction receipts | Versioned state and idempotent transitions |
| Cloud recovery | Account identity, revisions, conflict detection and branch selection | Local durability and recoverable snapshots |
| Entitlements | Verified cosmetic ownership, pass ownership and purchase transaction lifecycle | Native stores and backend reconciliation |
| Content/configuration | Chapters, challenges, assets, reward tables and season manifests | Schema checks and version compatibility |
| Operations | Telemetry, diagnostics, feature controls, support and service health | Minimal data collection and validated events |

Use one event timeline. Advance earnings over the interval before a boundary using the applicable state and configuration, resolve expirations/completions and their receipts at the boundary, then apply player commands. Document tie ordering for reset, bonus expiry, survey completion and daily rollover. Carry fractional timer progress and numerical remainders instead of rounding every UI frame.

Pin the economic version used to settle an offline interval. A downloaded rebalance applies only after the previous interval is settled and the version transition is committed. A remote manifest supplies validated data, not arbitrary executable code. Keep last-known-good content available when services are down.

Treat cloud sync as recovery of a single progression branch. Concurrent devices can fork saves while offline; they cannot be assumed to form a mergeable currency ledger. Detect the conflict, preserve both branches, and let the player select the retained progression. Merge only independently verified cosmetic entitlements and properly deduplicated receipts. Never add wallets, lifetime earnings or offline intervals from divergent branches.

Use revision preconditions to prevent overwriting changed cloud state. This is a general architectural requirement; Unity's [write-lock documentation](https://docs.unity.com/en-us/cloud-save/concepts/write-locks) describes one implementation if that service is selected, not a mandated provider.

The local game does not need competitive anti-cheat. Offline wall-clock manipulation cannot be made perfectly tamper-proof without an online authority. Use monotonic session timing, persisted settlement times and optional server anchors to prevent accidental duplicates; secure commercial ownership on the service side. Do not punish legitimate clock/time-zone changes or pretend a device signature proves elapsed real time.

## 7 Economy and content validation workstream

| Experiment | Required comparison | Decision it informs |
|---|---|---|
| First run | Reference policy, naive affordable purchases and observed novice play | First-session pacing and explanation |
| Repeat prestige | Fixed thresholds, multiplier goals and forecast-based policies | Reconstruction burden and useful reset advice |
| Low-tier relevance | Marginal purchases across sampled mid/late states | Whether synergies genuinely produce recurring choices |
| Offline parity | Same initial state and policy, online versus offline across boundary events | Accuracy and trust |
| Visit cadence | 1, 3 and 6 visits/day under matched policies | Whether storage and queues support daily play |
| Optional bonuses | Full 30/90-day trajectories with no bonuses, free-route bonuses and ad-route bonuses | Compounded advantage and route parity |
| Notes | Surveys only, partial contracts and all contracts; mandatory versus optional sinks | Whether the campaign or collection develops a bottleneck |
| Season | New and veteran accounts at identical event start state | Isolation from account age and spending |
| Content coverage | Each chapter/challenge goal reached from realistic entry states | Dead ends, dominant strategies and empty late-game periods |

The full Note collection budget deserves explicit review. Twelve 100-Note dossiers, five 50-Note extra plans and six 50-Note decorations total 1,750 Notes. At 60 Notes/day from all Surveys and contracts that is about 29.2 days of generation; Surveys alone provide 30/day, or about 58.3 days. This arithmetic excludes unlock timing and actual spending choices. Keep optional completion distinct from the main ending and do not make every purchase mandatory for a 30-day campaign.

Retain 2/8/24-hour cycles, the prestige exponent range and the ethical reward contract during tuning unless a deliberate design revision is approved. When a change improves one cohort but harms another, document that tradeoff rather than optimizing only the most active players.

## 8 Acceptance gates for release

### Hard technical and completion gates

The numeric targets below are proposed internal requirements. They are not quoted platform thresholds or industry benchmarks. M0 fixes hardware and measurement conditions; M5 verifies feasibility and any change is recorded.

| Gate | Required evidence |
|---|---|
| Complete experience | All six chapters, ending, twelve challenges and first-season reward paths are reachable; no required placeholder or inaccessible reward |
| Economic integrity | No known negative-wallet, duplicate claim, repeated-entitlement or reset-mint defect; boundary fixtures agree on discrete purchases and Charts |
| Online/offline parity | Same integer outcomes at boundaries; continuous amounts within the explicitly chosen numeric error budget, initially relative error at most 1e-8 outside near-zero cases |
| Low-value precision | M1 defines the smallest accounted unit and absolute error budget; no tolerance permits an otherwise unaffordable purchase or extra Chart |
| Save recovery | Interruption tests at every transaction boundary and seeded corruption/migration cases recover; unresolved real data-loss incidents block launch |
| Commerce | Purchase, pending state, cancellation, restore, duplicate callback, refund/revocation and disconnected delivery tested on both stores; no known undelivered verified entitlement |
| Reward parity | Ad and briefing routes have the same allowance and value; no-fill/refusal does not block the free route |
| Stability | At least 99.5% crash-free sessions over 10,000 observed sessions, reported by platform/device group; no open crash on a critical flow |
| Frame performance | Target 60 fps on reference midrange hardware and 30 fps on the declared minimum tier; report p95 frame time during the heaviest shipped scene |
| Startup | p95 cold start to usable harbor at most 5 seconds on the declared minimum device in a defined test condition |
| Return processing | p95 24-hour replay at most 3 seconds for supported baseline policies; stress policies must show progress and chunk work without losing owed production |
| Battery and thermal behavior | No required background busy loop; measured 30-minute sessions remain usable without sustained thermal collapse on minimum devices |
| Accessibility | Critical flows work with large text, reduced motion and non-color cues; equivalent-value calibration completion is discoverable |
| Platform readiness | Final metadata, products, privacy disclosures, ratings, support URLs and reviewer access match the shipped build |
| Operations | Recovery/disable/rollout drills pass; support and 14-day coverage have named owners |

There must be zero open release-blocking defects. Major defects affecting normal progression, accessibility of a required flow or purchased content also block release. Minor cosmetic issues can be accepted with an owner and a repair date.

### Product decision gates

| Signal | Proposed review threshold or question |
|---|---|
| Onboarding | At least 80% of moderated testers can explain reset losses/retentions and offline behavior; inspect failures individually |
| Initial pacing | Median first-prestige eligibility among players who reach it in an observed first-session study is 15–30 minutes; separately report the proportion who never reach it |
| Retention hypotheses | Provisional targets D1 ≥35%, D7 ≥15%, D30 ≥7%; report uncertainty and cohort composition rather than claiming universal benchmarks |
| Campaign | Real players reach later chapters without a hidden mandatory purchase, constant check-ins or an unexplained earnings wall |
| Strategy | At least two understandable policies or challenge approaches offer meaningful tradeoffs; one globally obvious action should not consume the whole game |
| Player welfare | Interviews and surveys do not reveal systematic pressure to wake up, watch ads or buy power to keep up |
| Commercial feasibility | Measure cosmetic conversion, ad participation and service/support cost; do not assume paid acquisition is profitable before evidence exists |

Define Dn as the fraction of all eligible first-launch installs that have a valid return session in the corresponding 24-hour age window. Exclude staff, automation and known invalid installs using rules fixed before analysis; do not remove players merely because they left during onboarding. Report the telemetry-observable population and any missing-data limitations. Mature cohorts only: a player must have had the full observation opportunity before entering a D30 result.

The provisional retention targets trigger review, not an automatic claim that the product is viable. Hard correctness, ownership and fairness gates cannot be traded for a stronger retention number. Product sign-off records whether to launch, extend observation or revise the experience.

## 9 Platform and service work that cannot be left to submission week

| Requirement area | Scheduled work | Source to verify again before launch |
|---|---|---|
| Complete and accurate submission | Remove placeholders, make products reviewable, supply working URLs and reviewer access in M5/M7 | [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) |
| Guest play and account lifecycle | Design optional account use and in-app deletion with recovery consequences in M0/M3 | [Apple privacy and sign-in requirements](https://developer.apple.com/app-store/review/guidelines/#privacy) |
| Google purchase lifecycle | Verify a purchase, grant only after completion, reconcile missed callbacks, and acknowledge processed purchases in M0/M4/M5 | [Google Play Billing integration](https://developer.android.com/google/play/billing/integrate) |
| Native purchase testing | Exercise native sandbox flows and restoration before external testing | [Apple purchase sandbox](https://developer.apple.com/documentation/storekit/testing-in-app-purchases-with-sandbox) |
| External Apple testing | Prepare distribution, review access and test builds before M6 | [TestFlight](https://developer.apple.com/testflight/) |
| Android field quality | Compare own telemetry with platform quality reporting during M6/M7 | [Android vitals](https://developer.android.com/google/play/vitals) |

These are dependencies to verify, not a legal compliance certification. Audience, launch territories, SDK behavior and store requirements can change. Assign an owner in M0 and review them again during beta and immediately before submission. Never hard-code today's submission version requirements into a nine-month promise.

## 10 Main risks and responses

| Risk | Early indicator | Owner | Planned response |
|---|---|---|---|
| Early economy works but later content is empty | Simulations or testers repeat the same choice for days | Product designer | Author chapters/challenges in M1; validate 30/90 days before beta; extend content work if the ending lacks substance |
| Offline approximation changes outcomes | Different purchase/reset counts across equivalent histories | Gameplay engineer | Shared event core, explicit precision rules and boundary fixtures before more features |
| Save conflicts lose or duplicate progress | Overlapping devices/claims fail recovery tests | Services engineer | Preserve branches, revision preconditions, receipts and manual recovery tools |
| SDK or engine choice blocks native features | Purchase/restore/ad proof fails | Services engineer | Resolve in M0; select supported adapters before committing to content production |
| Art scope exceeds one artist | Milestone presentations require unique full redraws | Artist | Modular visual system, locked manifest and funded external support if needed |
| Note economy forces excessive daily work | Required goals exceed realistic passive supply | Product designer | Separate required and optional sinks, inspect Surveys-only progression, retune entry costs with evidence |
| Bonuses dominate through compounding | Full trajectories diverge far beyond intended experience | Product designer | Test shared allowance paths; reduce or reshape optional rewards without selling parity |
| Recruitment or D30 maturity is missing | Stable cohort cannot start in week 27 | QA/release lead | Recruit earlier, use contingency, and defer the decision until the cohort matures |
| QA becomes the release bottleneck | Growing unverified device/migration queue | QA/release lead | Protect QA capacity, automate repeatable cases and add targeted device-test help |
| Live content is not sustainable | Season 2 requires an entirely new production pipeline | Product designer | Reuse challenge framework, prepare next-season brief and budget an ongoing team |
| Store review or external accounts delay launch | Incomplete products, access or review findings | QA/release lead | Complete integrations early; reserve contingency; do not announce a fixed date before evidence |

If time slips, first defer already-excluded platforms/languages and additional content requests. Within the baseline, a deliberate prelaunch scope revision may reduce cosmetic variety or challenge count while preserving the complete campaign and three challenge families, but it must update the manifest, backlog and product validation. Do not silently sell fewer pass rewards than advertised. Do not cut save recovery, offline correctness, purchase fulfillment, accessibility of required flows or the equal free reward route.

## 11 Delivery rhythm and first two weeks

Use two-week sprints with a weekly integrated device build. Keep one major active package per specialist. A ticket is done only when its acceptance evidence exists, its effects on saves/telemetry are understood, relevant tests pass, and UI/content changes are checked in the integrated build. Feature flags isolate incomplete work; they do not excuse shipping hidden unfinished products.

At each gate, record scope completed, evidence, unresolved risks, actual effort and the new forecast. Re-estimate after the vertical slice using actual throughput. Freeze new features at M4; later work addresses evidence, performance, correctness and release readiness.

| Week | Concrete first actions | Output |
|---|---|---|
| 1 | Confirm scope/roles, inspect the reference model, prototype four critical flows, start engine/native-service probes, select test hardware | Release contract, decision log, initial content manifest, prototype and qualification results |
| 2 | Finish native qualification, lock number/state boundaries, establish builds and test evidence, book specialists and testers, level the backlog onto sprints | M0 gate report, production architecture, cost/capacity forecast and ready M1 tickets |

No development should begin by expanding the producer list or adding a second prestige layer. The first build should demonstrate a correctly persisted purchase, reset and return on a real target device.

## 12 Launch handoff and the v1 completion record

Before release, assemble a single evidence pack containing the approved build/config versions, content manifest, known issues, test results, cohort report, store status, purchase/restore evidence, recovery/rollout runbooks and named coverage. Provide support with a safe diagnostic export and transaction identifiers; support actions must not mint the same compensation twice.

During the first 14 days, inspect crash/resume/save/entitlement trends daily, handle verified incidents, and ship narrowly scoped repairs. Keep an available forward-fix build path. Do not rebalance the core merely because early spending is below a target, and do not interpret two weeks of launch activity as mature D30 data.

The final v1 record should state what shipped, which quality and product gates passed, any accepted minor issues, and who owns ongoing service/content costs. Prepare the next season's brief, but protect time for stability and measured improvements before adding new permanent systems.
