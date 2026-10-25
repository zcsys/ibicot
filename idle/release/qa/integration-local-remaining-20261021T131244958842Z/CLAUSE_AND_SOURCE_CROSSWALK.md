# Original clause and inspected-source crosswalk

The quotations below are unchanged clauses from the frozen original contracts, not substitute acceptance criteria. A local prerequisite may be implementable while the full staging, live, human or native requirement remains open.

## Scope obligations

| ID | Requirement | Exact verification clause |
| --- | --- | --- |
| S18 | Eighteen main archive entries and six optional 50-Note decorations; no forced full collection | Content manifest, reachable unlocks and main-ending test with optional sinks unbought. |
| S20 | Season 1 Night of Returning Stars, 28-day lifecycle, isolated fleet, specified coefficients and no event prestige | New/veteran equality; main power cannot enter; no economic export; actual live/end/archive behavior observed. |
| S21 | 30 levels at 500 XP, 30 free slots with 10 cosmetics/20 fragments, 10 premium cosmetics, selected archived pass | 15,000-XP finish; single XP grant, one selected pass and paid-pass continuation after archive. |
| S22 | 36 unique cosmetics distributed 12 core, 10 free pass, 10 premium, 4 direct shop; supporter reuses shop items | Unique IDs and actual assets match each reward; no power effect or unbudgeted supporter art set. |
| S27 | Help, recovery guide, release notes, credits, privacy/support URLs and runbooks | All pages and review/support links work and match actual data and products. |
| S37 | Monitoring, support diagnostics, backups, feature disables, rollout stops and compatible forward repair | Staging and live-operation drills; never roll a newer save into an unsupported older executable. |
| S39 | Privacy, consent/refusal, account deletion/export and service outages reflect actual SDK behavior | Native network/SDK audit and lifecycle/outage tests; no policy page alone counts as implementation. |
| S41 | Budget and device/test plan adapted to AI delivery; protect scope and independent review | Execution costs and access needs named; no inherited human-week promise or unsupported tool capability claim. |
| S42 | Complete release evidence pack and approved candidate with only accepted minor issues | Evidence from exact candidate/config/content versions; release status cannot be inferred from plan coverage. |
| S43 | Polish observed content/UI issues and create accurate store/launch assets | Changed screens rechecked on targets; final screenshots/footage represent shipped product. |

## Original package clauses

| ID | Exact acceptance sentence | Original dependencies |
| --- | --- | --- |
| M3-09 | Five producer families each have base plus four milestone presentations; daily-loop icons and status states are final. | M2-05 |
| M4-06 | Six chapters, ending, twelve challenges, twelve calibration patterns, eighteen archive entries and Season 1 have complete data and copy. | M3-08, M4-01, M4-02 |
| M4-07 | Six harbor restoration states and the fixed 36-item cosmetic manifest are complete; commissioned audio is integrated through client work. | M3-09, M4-06 |
| M4-08 | Every content ID and reward is reachable; full pass is completable free of paid speed; no event or cosmetic increases core power. | M4-03, M4-04, M4-05, M4-06, M4-07 |
| M5-03 | Data inventory matches SDK behavior; consent refusal, export/deletion and service-outage recovery are verified on actual builds. | M3-06, M4-04, M4-05 |
| M5-04 | Validate economy/session events, entitlement dashboards, alerts, backups, support receipts and feature disable switches in staging. | M3-07, M4-04 |
| M5-06 | Remove placeholders, integrate final sound direction, and prepare representative screenshots, icon and short footage. | M4-07 |
| M6-05 | Exercise service load, support recovery, purchase reconciliation and feature disable controls with real opt-in testers. | M5-04, M6-01 |
| M7-04 | Version-compatible config rollback, feature disables, capacity, backups and entitlement replay are rehearsed and documented. | M6-05, M7-01 |
| M7-05 | Screenshots, footage, credits, help visuals and release assets describe the actual shipped game and offers. | M6-06, M7-01 |

## Frozen source references by action

Each link below points to the immutable copy inspected for this triage. The relative path identifies its production or evidence origin. Full hashes are in `source-sha256.json`.

### Action 1

- [game/mobile/lib/help_content.dart](source/game/mobile/lib/help_content.dart)
- [game/mobile/lib/help_screen.dart](source/game/mobile/lib/help_screen.dart)
- [game/mobile/pubspec.yaml](source/game/mobile/pubspec.yaml)
- [release/public-pages/publication.json](source/release/public-pages/publication.json)
- [release/public-pages/INDEPENDENT_REVIEW.md](source/release/public-pages/INDEPENDENT_REVIEW.md)

### Action 2

- [services/tideglass_service/__main__.py](source/services/tideglass_service/__main__.py)
- [services/tideglass_service/api.py](source/services/tideglass_service/api.py)
- [services/tideglass_service/ops.py](source/services/tideglass_service/ops.py)
- [services/README.md](source/services/README.md)
- [services/docs/OPERATIONS.md](source/services/docs/OPERATIONS.md)
- [release/runbooks/LAUNCH_HANDOVER.md](source/release/runbooks/LAUNCH_HANDOVER.md)
- [release/qa/integration-operations-final-20261021T104534667043Z/OPERATIONS_REVIEW.md](source/release/qa/integration-operations-final-20261021T104534667043Z/OPERATIONS_REVIEW.md)

### Action 3

- [implementation/art/production_contract.json](source/implementation/art/production_contract.json)
- [implementation/content/launch_manifest.json](source/implementation/content/launch_manifest.json)
- [game/mobile/test/story_ui_test.dart](source/game/mobile/test/story_ui_test.dart)
- [game/mobile/test/season_ui_test.dart](source/game/mobile/test/season_ui_test.dart)
- [game/mobile/test/daily_flow_test.dart](source/game/mobile/test/daily_flow_test.dart)
- [game/events/test/events_test.dart](source/game/events/test/events_test.dart)
- [game/mobile/lib/app.dart](source/game/mobile/lib/app.dart)
- [source/art/verification/coverage-contract.md](source/source/art/verification/coverage-contract.md)
- [release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md](source/release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md)

### Action 4

- [services/docs/PRIVACY.md](source/services/docs/PRIVACY.md)
- [game/mobile/pubspec.lock](source/game/mobile/pubspec.lock)
- [game/mobile/android/app/src/main/AndroidManifest.xml](source/game/mobile/android/app/src/main/AndroidManifest.xml)
- [game/mobile/ios/Runner/PrivacyInfo.xcprivacy](source/game/mobile/ios/Runner/PrivacyInfo.xcprivacy)
- [release/public-pages/publication.json](source/release/public-pages/publication.json)

### Action 5

- [release/store/README.md](source/release/store/README.md)
- [release/store/metadata.en-US.json](source/release/store/metadata.en-US.json)

### Action 6

- [implementation/program.json](source/implementation/program.json)
- [implementation/team/EXECUTION_CHECKPOINT.md](source/implementation/team/EXECUTION_CHECKPOINT.md)
- [services/README.md](source/services/README.md)
- [release/balance/optional-calibration-current-integration.json](source/release/balance/optional-calibration-current-integration.json)
- [release/audio/capability-and-rights.json](source/release/audio/capability-and-rights.json)

Raw candidate152 video existence was checked at `release/native-proof/integration-android-20261021T114929.560297Z/gameplay.mp4`, `release/native-proof/integration-ios-phone-20261021T112255.702927Z/gameplay.mp4` and `release/native-proof/integration-ios-tablet-20261021T115934.504362Z/gameplay.mp4`. These are existing historical artifacts, not a claim that final current-candidate footage is qualified.
