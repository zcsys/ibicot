# Independent recommendations for M1-06 and M0-08

Recommend accepting both packages at their original, narrowly stated clauses. Their original prerequisites are accepted. These recommendations do not verify S15 or S40 in full, qualify the changed economic-transition runtime natively, or establish finished-v1 release acceptance. The director decides and applies statuses; QA made no program or scope edits.

The 55 reviewed source/evidence inputs have fingerprint `3f33fbbca035bab5c6c3fef909e4b55ede762fe62521d12075994da3fe4dfcb4`. The verification record lists 824 checks, chiefly source/artifact identity checks; this number is not 824 gameplay scenarios. QA also independently reran the current 23 native-tooling unit cases successfully. No Flutter/native build was launched in this review.

## M1-06 — Design the full progression map

Original acceptance: “Specify six chapter goals, ending, challenge entry requirements, Note source/sink budgets and daily/pass exceptions; no new prestige layer is assumed.”

Original prerequisite: **M0-01**, currently accepted. No prerequisite was added, removed or substituted.

| Original clause | Actual evidence and assessment |
|---|---|
| Six chapter goals | `game/content/progression/campaign.json` defines ordered prerequisites and concrete goals: first Rechart; 25 Charts plus 25 of each early producer; 12 Surveys; one dossier from each family; 100 Charts/five Recharts/one Observatory; two dossiers from each family. All six have completion copy, cosmetic identity and harbor state. Calibration is explicitly optional after the independently reviewed correction. Satisfied as specification. |
| Ending | Chapter six has complete ending text and explicit continued play. No paid requirement or purchase of every optional Note sink is required. Satisfied. |
| Challenge entry requirements | All twelve actual dossier files require three completed chapters and a one-time 100-Note persistent unlock, with zero-cost replay. Four dossiers in each of three families define fixed starts, rule constraints, goals and no imported main power or extra prestige. Satisfied. |
| Note source/sink budgets | The original design and roadmap specify 10 Notes per Survey and per daily contract, maximum ordinary generation 30+30/day; twelve 100-Note dossiers, five 50-Note extra plans and six 50-Note decorations total 1,750. Current campaign requires six dossiers/600 Notes, leaving the rest optional. Generation arithmetic is 20 days for mandatory Surveys-only, 10 at full contracts; optional full collection is about 58.3/29.2 days before unlock/behavior constraints. Satisfied as budgets, not measured pacing. |
| Daily/pass exceptions | Design §§III.4–5 plus `game/events/README.md` and actual pass implementation specify frozen account/day difficulty, one reroll, seven retained daily sets, no compulsory prestige/ad/spending, one selected shared XP ledger, main/event alternatives consuming one slot reward, archived continuation, preserved existing XP, upcoming-pass exclusion and cosmetic-only rewards. Thirty levels ×500 XP require twenty full 750-XP days. Satisfied. |
| No new prestige layer | Main Charts remain the sole permanent prestige layer. Challenge prestige is disabled; event Rechart rejects and exports no economic resources. Satisfied. |

Prior independent optional-calibration review and corrected balance reviews provide useful implementation support, but acceptance here does not require or pretend to complete their human-pacing obligations. Fast feasible policy endings around 10.5–11.17 days are not observations of the original 15–30-day player target. Old metadata such as `authored_balance_validation_pending` accurately retains those later empirical obligations; it does not undo an actually specified progression map.

Forward mapping is **M1-06 → S15/S44**. Reverse mapping is **S15/S44 → this progression-specification contribution**, with content reachability, current complete native presentation, player comprehension, pacing and total release criteria still separately evaluated. Recommendation: **accept M1-06 only**.

## M0-08 — Create reproducible builds

Original acceptance: “Automated builds run on both targets, version configurations and preserve build artifacts; no production secrets enter the client.”

Original prerequisite: **M0-02**, currently accepted. No prerequisite was added, removed or substituted.

| Original clause | Actual evidence and assessment |
|---|---|
| Automated builds run on both targets | `tool/build_native.py` drives pinned Flutter commands for iOS simulator/unsigned device release and Android APK/AAB. Preserved candidate152 debug/release reports record successful real exports on both targets, plus macOS as a supplemental host. QA inspected the commands and final audit, rehashed all 670 frozen inputs and all five artifacts. Satisfied as an automated build capability. |
| Version configurations | Frozen manifests bind the complete source map and locks. Flutter is pinned to 3.47.7 / `abaf9c523780a608bd46686fd5e53740a07077f8`; JDK download has a fixed digest; Gradle/native platform files and package locks are captured. `--enforce-lockfile` and post-build lock comparisons are explicit. `pubspec.yaml` is 0.1.0+1; both actual iOS bundles independently report version 0.1.0/build1 and `dev.tideglass.game`. Provisional identity/version remain clearly developmental. Satisfied. |
| Preserve artifacts | Two iOS ZIPs, debug Android APK, release Android AAB and macOS ZIP all match recorded SHA-256 and sizes. Source and generated workspaces are separate, with manifests, raw logs and snapshots retained. Candidate152's existing 22 accepted runtime-cell records were rehashed; these are supporting historical records, not new runs. Satisfied. |
| No production secrets enter client | The reviewed build entry point adds no secret compile definitions or signing material; Android release signing is unset and iOS exports use `--no-codesign`. The client only configures public endpoint/ad identifiers, public verification pins and feature booleans, with optional services off by default. Server/provider code and credentials are outside Flutter asset declarations. The five actual artifacts contain none of the checked credential-container/key filenames. Source archives contain test/server material but are not client asset bundles. Satisfied for this reviewed configuration; this is not a security certification of future deployments. |

The later build-tool change includes bounded synthetic study fixtures and explicitly runs study tests under `--host-checks`; independent lead review and QA's fresh 23-case tooling run cover immutable capture, declared derivation, failed-study/no-export behavior and strict native-success classification. The host gate is an explicit CLI option, not a claim of installed CI. The preserved ResourceWarning about early-return lock-file object cleanup remains a tooling improvement, not an observed build/lock failure.

“Reproducible” here is the exact original automated-build/version/artifact criterion: same-host source/recipe/lock identity and retained actual outputs. No byte-identical rebuild or independent second-host reproduction is claimed. Candidate152 is deliberately older than the new economic-transition/FFI implementation; a new current candidate must still build and run. No signed distribution, store account, physical-device matrix or public release is implied.

Forward mapping is **M0-08 → S40**. Reverse mapping is **S40 → this build capability**, with actual current configuration compatibility, later FFI execution and broader platform feasibility still requiring their own evidence. Recommendation: **accept M0-08 only**.

The original 65 acceptance sentences, dependencies and distinct bootstrap contributions remain intact. No S15/S40 or final-release promotion follows automatically from these two package decisions.
