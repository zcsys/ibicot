# Evidence catalogue

Every anchor identifies production source and existing bounded proof. This audit did not rerun those suites.

## F: Foundation and original contract

Accepted foundation decisions do not provide resources or a finished public release.

Source: [docs/release-contract.md](/Users/csys/Desktop/ibicot/idle/docs/release-contract.md)<br>[docs/decisions/engine-and-number-selection.md](/Users/csys/Desktop/ibicot/idle/docs/decisions/engine-and-number-selection.md)<br>[docs/decisions/execution-costs.md](/Users/csys/Desktop/ibicot/idle/docs/decisions/execution-costs.md)<br>[docs/quality/V1_QUALITY_PROTOCOL.md](/Users/csys/Desktop/ibicot/idle/docs/quality/V1_QUALITY_PROTOCOL.md)<br>[release/device-matrix.json](/Users/csys/Desktop/ibicot/idle/release/device-matrix.json)

Evidence: [release/qa/FOUNDATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/FOUNDATION_REVIEW.md)<br>[implementation/reports/director-foundation-review.md](/Users/csys/Desktop/ibicot/idle/implementation/reports/director-foundation-review.md)

## N: Frozen native candidate and failed host gate

a052 host gate ended 26/28, no current exports/runtime matrix. Test expectation and operations interpreter environment repairs are separate assignments.

Source: [tool/build_native.py](/Users/csys/Desktop/ibicot/idle/tool/build_native.py)<br>[tool/verify_native.py](/Users/csys/Desktop/ibicot/idle/tool/verify_native.py)<br>[tool/verify_current_runtime.py](/Users/csys/Desktop/ibicot/idle/tool/verify_current_runtime.py)<br>[game/mobile/integration_test/platform_smoke_test.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/integration_test/platform_smoke_test.dart)<br>[game/mobile/integration_test/current_runtime_test.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/integration_test/current_runtime_test.dart)

Evidence: [release/native-proof/20261023T032749.977866Z/build-report.json](/Users/csys/Desktop/ibicot/idle/release/native-proof/20261023T032749.977866Z/build-report.json)<br>[release/native-proof/20261023T032749.977866Z/mobile-test.log](/Users/csys/Desktop/ibicot/idle/release/native-proof/20261023T032749.977866Z/mobile-test.log)<br>[release/native-proof/20261023T032749.977866Z/operations-test.log](/Users/csys/Desktop/ibicot/idle/release/native-proof/20261023T032749.977866Z/operations-test.log)

## Q: Numbers and chronology

62 exact current numeric/timeline rows, 15,365 assertions; no discrete tolerance; source bridge is narrower than human pacing or all native behavior.

Source: [game/core/lib/src/fixed.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/fixed.dart)<br>[game/core/lib/src/state.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/state.dart)<br>[game/core/lib/src/engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/engine.dart)<br>[game/core/lib/src/daily_engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/daily_engine.dart)<br>[game/core/lib/src/support_engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/support_engine.dart)

Evidence: [release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json](/Users/csys/Desktop/ibicot/idle/release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json)<br>[release/qa/lead-bounded-acceptance-20261021T1148Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-bounded-acceptance-20261021T1148Z/DECISIONS.md)

## P: Durable local state

208 core and 28 persistence tests with real host process kills; nested reentry/writer failures repaired. Not physical power loss.

Source: [game/persistence/lib/tideglass_persistence.dart](/Users/csys/Desktop/ibicot/idle/game/persistence/lib/tideglass_persistence.dart)<br>[game/mobile/lib/bootstrap.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/bootstrap.dart)<br>[game/mobile/lib/client_economic_transition.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/client_economic_transition.dart)<br>[game/mobile/lib/offline_replay.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/offline_replay.dart)

Evidence: [release/persistence-review.md](/Users/csys/Desktop/ibicot/idle/release/persistence-review.md)<br>[release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md)<br>[release/qa/lead-transition-acceptance-20261021T1221Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-transition-acceptance-20261021T1221Z/DECISIONS.md)

## C: Pinned configuration

29 packaged files and exact compatible transition; unknown versions fail closed.

Source: [game/mobile/lib/bundled_content.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/bundled_content.dart)<br>[game/mobile/lib/content_compatibility.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/content_compatibility.dart)<br>[game/mobile/assets/config/manifest.json](/Users/csys/Desktop/ibicot/idle/game/mobile/assets/config/manifest.json)

Evidence: [release/qa/lead-config-acceptance-20261021T141750.104883Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-config-acceptance-20261021T141750.104883Z/DECISIONS.md)

## U: Shell, onboarding and reset

Actual 320/1024 at 200% English/pseudo forecast dialog, honest two-branch assumptions, snapshot isolation/cancel/confirm; onboarding comprehension still needs people.

Source: [game/mobile/lib/app.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/app.dart)<br>[game/mobile/lib/game_controller.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/game_controller.dart)<br>[game/mobile/lib/strings.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/strings.dart)<br>[game/mobile/lib/rechart_forecast_task.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/rechart_forecast_task.dart)<br>[game/core/lib/rechart_forecast.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/rechart_forecast.dart)

Evidence: [release/qa/lead-client-shell-acceptance-20261021T145030.603397Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-client-shell-acceptance-20261021T145030.603397Z/DECISIONS.md)<br>[release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md)<br>[release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md)

## A: Earned automation

10/25/100 unlocks, priorities/reset boundaries, one free and five 50-Note slots, real repository plan round trips.

Source: [game/core/lib/src/daily.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/daily.dart)<br>[game/core/lib/src/daily_engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/daily_engine.dart)<br>[game/mobile/lib/daily_panel.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/daily_panel.dart)

Evidence: [release/qa/lead-automation-acceptance-20261021T143015.491121Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-automation-acceptance-20261021T143015.491121Z/DECISIONS.md)

## D: Daily timeline

Shared event chronology, saved-policy replay, remainders, seeded frozen goals/rerolls and receipts; historical results retain their pins.

Source: [game/core/lib/src/engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/engine.dart)<br>[game/core/lib/src/daily_engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/daily_engine.dart)<br>[game/core/lib/src/support_engine.dart](/Users/csys/Desktop/ibicot/idle/game/core/lib/src/support_engine.dart)<br>[game/mobile/lib/daily_panel.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/daily_panel.dart)<br>[game/mobile/lib/offline_replay.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/offline_replay.dart)

Evidence: [release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md)<br>[release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md)

## K: Calibration and accessible completion

All12 actual patterns and equivalent completion independently reviewed; S09/S17 accepted, not entire accessibility scope.

Source: [game/mobile/lib/calibration_screen.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/calibration_screen.dart)<br>[game/mobile/lib/calibration_pattern.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/calibration_pattern.dart)<br>[game/content/calibrations/calibration.01.pattern.json](/Users/csys/Desktop/ibicot/idle/game/content/calibrations/calibration.01.pattern.json)

Evidence: [release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md)<br>[release/qa/lead-calibration-scope-acceptance-20261021T130612.263921Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-calibration-scope-acceptance-20261021T130612.263921Z/DECISIONS.md)

## R: Reminder and settings adapters

30 host tests and 384 departure conditions; native plugin calls mocked. Actual permission/delivery/revocation not demonstrated by current 58-cell harness.

Source: [game/mobile/lib/notification_service.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/notification_service.dart)<br>[game/mobile/lib/reminder_lifecycle.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/reminder_lifecycle.dart)<br>[game/mobile/lib/notification_settings.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/notification_settings.dart)<br>[game/mobile/lib/audio_settings.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/audio_settings.dart)<br>[game/mobile/lib/number_format.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/number_format.dart)

Evidence: [release/qa/integration-reminders-initial-20261016T115431767720Z/REMINDERS_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-reminders-initial-20261016T115431767720Z/REMINDERS_REVIEW.md)

## S: Cloud/account/service ledger

Real local HTTP/database and adversarial tests; optional linked account and explicit branch choice implemented. Default service/provider configuration disabled.

Source: [services/tideglass_service/api.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/api.py)<br>[services/tideglass_service/storage.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/storage.py)<br>[game/platform/lib/tideglass_platform.dart](/Users/csys/Desktop/ibicot/idle/game/platform/lib/tideglass_platform.dart)<br>[game/mobile/lib/native_services.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/native_services.dart)<br>[game/mobile/lib/service_settings.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/service_settings.dart)

Evidence: [release/qa/integration-services-repaired-20261016T114721906724Z/INTEGRATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-services-repaired-20261016T114721906724Z/INTEGRATION_REVIEW.md)

## G: Campaign and challenges

Six chapters/ending, 12 isolated dossiers across3 families,18 archives; ending needs six dossiers/600 Notes, not all1,750 optional collection. Optional calibration repaired.

Source: [game/content/progression/campaign.json](/Users/csys/Desktop/ibicot/idle/game/content/progression/campaign.json)<br>[game/progression/lib/tideglass_progression.dart](/Users/csys/Desktop/ibicot/idle/game/progression/lib/tideglass_progression.dart)<br>[game/progression/lib/decoration_purchase.dart](/Users/csys/Desktop/ibicot/idle/game/progression/lib/decoration_purchase.dart)<br>[game/mobile/lib/story_screen.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/story_screen.dart)<br>[game/mobile/lib/story_state.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/story_state.dart)

Evidence: [release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md)<br>[release/balance/optional-calibration-current-integration.json](/Users/csys/Desktop/ibicot/idle/release/balance/optional-calibration-current-integration.json)

## V: Season and pass

Isolated fleet,28-day boundary,30×500XP,30free/10premium, one selected archived pass and idempotent alternatives; virtual boundaries are not elapsed calendar observation.

Source: [game/events/lib/src/season.dart](/Users/csys/Desktop/ibicot/idle/game/events/lib/src/season.dart)<br>[game/events/lib/src/pass.dart](/Users/csys/Desktop/ibicot/idle/game/events/lib/src/pass.dart)<br>[game/events/content/season.01.json](/Users/csys/Desktop/ibicot/idle/game/events/content/season.01.json)<br>[game/mobile/lib/season_screen.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/season_screen.dart)

Evidence: [release/client-season-review.md](/Users/csys/Desktop/ibicot/idle/release/client-season-review.md)<br>[release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md)

## T: Complete content presentation

12 actual conditions,876 tests/1,644 rows; 62 content IDs plus3 daily/help flows. Later App delta bridged separately; no relabeling historical captures.

Source: [game/mobile/lib/story_screen.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/story_screen.dart)<br>[game/mobile/lib/season_screen.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/season_screen.dart)<br>[implementation/content/launch_manifest.json](/Users/csys/Desktop/ibicot/idle/implementation/content/launch_manifest.json)

Evidence: [release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md)<br>[release/content-presentation/full-matrix-repaired-20261021T143209447416Z/verification.json](/Users/csys/Desktop/ibicot/idle/release/content-presentation/full-matrix-repaired-20261021T143209447416Z/verification.json)

## I: Harbor, producers, cosmetics

7harbors/25producers/36cosmetics normal/reduced, phone/tablet 100/150/200 English/pseudo; actual art proof is separate from file counts.

Source: [game/mobile/lib/harbor_art.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/harbor_art.dart)<br>[game/mobile/lib/producer_art.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/producer_art.dart)<br>[game/mobile/lib/cosmetic_art.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/cosmetic_art.dart)<br>[game/mobile/lib/cosmetics.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/cosmetics.dart)

Evidence: [release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md)<br>[release/qa/lead-art-scope-acceptance-20261021T124855.896748Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-art-scope-acceptance-20261021T124855.896748Z/DECISIONS.md)

## J: Final daily icons

M3-09 accepted unchanged; text equivalents retained; locked/error branches source-inspected, not mislabeled newly rendered fault cases.

Source: [game/mobile/lib/daily_icon_label.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/daily_icon_label.dart)<br>[game/mobile/lib/daily_panel.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/daily_panel.dart)<br>[game/mobile/lib/app.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/app.dart)

Evidence: [release/qa/qa-provenance-version-20261023T031648.974649Z/M3_09_CLIENT_RECOMMENDATION.md](/Users/csys/Desktop/ibicot/idle/release/qa/qa-provenance-version-20261023T031648.974649Z/M3_09_CLIENT_RECOMMENDATION.md)<br>[release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/DECISIONS.md](/Users/csys/Desktop/ibicot/idle/release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/DECISIONS.md)

## L: Font notices and licenses UI

Actual licenses reading/keyboard/target evidence with documented SDK4px tablet overlap; packaged-native inclusion still pending current export.

Source: [game/mobile/lib/font_licenses.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/font_licenses.dart)<br>[game/mobile/lib/main.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/main.dart)<br>[source/art/ui/font-manifest.json](/Users/csys/Desktop/ibicot/idle/source/art/ui/font-manifest.json)

Evidence: [release/qa/qa-reset-20261023T025256.370588Z/FONT_NOTICE_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/qa-reset-20261023T025256.370588Z/FONT_NOTICE_REVIEW.md)

## B: Long-horizon simulation

184 corrected historical cases plus15 focused current optional-calibration cases, not a silently rerun184. Exact no-bonus/free/ad synthetic fixtures; human pacing and beta freeze not established.

Source: [game/simulation/lib/policy_run.dart](/Users/csys/Desktop/ibicot/idle/game/simulation/lib/policy_run.dart)<br>[game/simulation/lib/supplemental_run.dart](/Users/csys/Desktop/ibicot/idle/game/simulation/lib/supplemental_run.dart)<br>[game/simulation/lib/supplemental_math.dart](/Users/csys/Desktop/ibicot/idle/game/simulation/lib/supplemental_math.dart)<br>[game/simulation/bin/run_optional_calibration.dart](/Users/csys/Desktop/ibicot/idle/game/simulation/bin/run_optional_calibration.dart)

Evidence: [release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md)<br>[release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md)<br>[release/balance/optional-calibration-current-integration.json](/Users/csys/Desktop/ibicot/idle/release/balance/optional-calibration-current-integration.json)

## Y: Real commerce adapter and fulfillment

Production SDK/server verification paths exist; fixtures validate logic, not actual sandbox purchase/refund/ad service. Signatures/leases separated from untrusted saves.

Source: [game/mobile/lib/native_services.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/native_services.dart)<br>[game/mobile/lib/service_cosmetics.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/service_cosmetics.dart)<br>[services/tideglass_service/providers/stores.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/providers/stores.py)<br>[services/tideglass_service/providers/admob.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/providers/admob.py)<br>[services/tideglass_service/providers/notifications.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/providers/notifications.py)<br>[services/tideglass_service/reconcile.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/reconcile.py)<br>[services/tideglass_service/vault.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/vault.py)

Evidence: [release/qa/integration-native-ownership-repaired-20261019T145035575220Z/NATIVE_OWNERSHIP_REPAIRED_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-native-ownership-repaired-20261019T145035575220Z/NATIVE_OWNERSHIP_REPAIRED_REVIEW.md)<br>[release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md)

## W: Privacy and public support plumbing

Actual local browser and native links UI, UMP flow and lifecycle failure tests; public URLs/operator policy, real provider regions and native SDK traffic inventory remain unqualified.

Source: [game/mobile/lib/public_links.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/public_links.dart)<br>[game/mobile/lib/public_links_model.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/public_links_model.dart)<br>[services/tideglass_service/web_deletion.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/web_deletion.py)<br>[game/mobile/lib/ad_privacy_copy.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/ad_privacy_copy.dart)<br>[services/docs/PRIVACY.md](/Users/csys/Desktop/ibicot/idle/services/docs/PRIVACY.md)

Evidence: [release/qa/client-web-deletion-20261021T134443512157Z/WEB_DELETION_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/client-web-deletion-20261021T134443512157Z/WEB_DELETION_REVIEW.md)<br>[release/qa/integration-ad-privacy-20261021T141749224307Z/PRIVACY_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-ad-privacy-20261021T141749224307Z/PRIVACY_REVIEW.md)<br>[release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md)

## O: Operations tools

37methods+9real localHTTP/TLS scenarios,256 fixture requests; actual local alert receiver, backup/recovery/flags. Not qualified hosted staging, human acknowledgment or14days coverage.

Source: [services/tideglass_service/deployment.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/deployment.py)<br>[services/tideglass_service/alert_transport.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/alert_transport.py)<br>[services/tideglass_service/operator_cycle.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/operator_cycle.py)<br>[services/tideglass_service/ops.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/ops.py)<br>[services/tideglass_service/health.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/health.py)<br>[services/tideglass_service/recovery.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/recovery.py)

Evidence: [release/qa/gameplay-ops-review-20261021T140405144186Z/OPERATIONS_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/gameplay-ops-review-20261021T140405144186Z/OPERATIONS_REVIEW.md)<br>[services/evidence/deployment-20261021T140912481855Z/REPAIRED_AUTHOR_REVIEW.md](/Users/csys/Desktop/ibicot/idle/services/evidence/deployment-20261021T140912481855Z/REPAIRED_AUTHOR_REVIEW.md)

## H: Study collection and analysis

Synthetic schema2 registry/missingness/crash linkage and UI collection controls; zero people, real cohort, or elapsed observation.

Source: [game/platform/lib/study_recorder.dart](/Users/csys/Desktop/ibicot/idle/game/platform/lib/study_recorder.dart)<br>[game/mobile/lib/study_gate.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/study_gate.dart)<br>[game/mobile/lib/study_native_context.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/study_native_context.dart)<br>[tool/study_report.py](/Users/csys/Desktop/ibicot/idle/tool/study_report.py)<br>[release/study/protocol-template.json](/Users/csys/Desktop/ibicot/idle/release/study/protocol-template.json)

Evidence: [release/qa/integration-study-20261021T102508755253Z/STUDY_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-study-20261021T102508755253Z/STUDY_REVIEW.md)<br>[release/qa/integration-study-collection-final-20261021T113037215270Z/COLLECTION_REPAIRED_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-study-collection-final-20261021T113037215270Z/COLLECTION_REPAIRED_REVIEW.md)<br>[release/study/README.md](/Users/csys/Desktop/ibicot/idle/release/study/README.md)

## X: Native privacy observer/inventory

Repaired collector41+9+6methods; actual native observation pending. Android storage deliberately unavailable; snapshots cannot prove no traffic or wholeSDK data behavior.

Source: [release/native-privacy/runtime_observation.py](/Users/csys/Desktop/ibicot/idle/release/native-privacy/runtime_observation.py)<br>[release/native-privacy/inspect_artifacts.py](/Users/csys/Desktop/ibicot/idle/release/native-privacy/inspect_artifacts.py)<br>[game/mobile/integration_test/current_runtime_test.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/integration_test/current_runtime_test.dart)

Evidence: [release/qa/native-observation-retest-20261023T032106.255153Z/REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/native-observation-retest-20261023T032106.255153Z/REVIEW.md)<br>[release/native-privacy/observation-integration-20261023T032452.071407Z/verification.json](/Users/csys/Desktop/ibicot/idle/release/native-privacy/observation-integration-20261023T032452.071407Z/verification.json)

## Z: Release/store/coverage preparation

Original creative exists; silent20s historical152 exporttool independently checked, not current final editorial media. Store accounts/URLs/coverage and actual launch absent.

Source: [release/store/metadata.en-US.json](/Users/csys/Desktop/ibicot/idle/release/store/metadata.en-US.json)<br>[release/runbooks/LAUNCH_HANDOVER.md](/Users/csys/Desktop/ibicot/idle/release/runbooks/LAUNCH_HANDOVER.md)<br>[release/runbooks/launch-coverage-template.json](/Users/csys/Desktop/ibicot/idle/release/runbooks/launch-coverage-template.json)<br>[release/season-2-brief.md](/Users/csys/Desktop/ibicot/idle/release/season-2-brief.md)<br>[release/store/tools/export_preview.swift](/Users/csys/Desktop/ibicot/idle/release/store/tools/export_preview.swift)<br>[release/store/tools/inspect_preview.swift](/Users/csys/Desktop/ibicot/idle/release/store/tools/inspect_preview.swift)

Evidence: [release/store/CLIENT_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/store/CLIENT_REVIEW.md)<br>[release/qa/client-preview-tool-20261023T032106.818906Z/PREVIEW_TOOL_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/client-preview-tool-20261023T032106.818906Z/PREVIEW_TOOL_REVIEW.md)

## M: Asset source/provenance bookkeeping

164actualsource/export/provenance sets;34version records/42bindings+37existence updates preserve oldcaptures/rights/nullapproval. Canonicalasset approval remains unfinished.

Source: [implementation/art/production_contract.json](/Users/csys/Desktop/ibicot/idle/implementation/art/production_contract.json)<br>[implementation/content/launch_manifest.json](/Users/csys/Desktop/ibicot/idle/implementation/content/launch_manifest.json)

Evidence: [release/qa/qa-provenance-version-20261023T031648.974649Z/PROVENANCE_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/qa-provenance-version-20261023T031648.974649Z/PROVENANCE_REVIEW.md)<br>[release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md)<br>[release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/provenance-integration.json](/Users/csys/Desktop/ibicot/idle/release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/provenance-integration.json)

## AU: Original audio and soundtrack

Original authored audio files, three ambient masters, cues and supporterZIP; native decode/playback proof is narrower than mix, interruptions and real purchased receiving-app delivery.

Source: [game/mobile/lib/audio_bus.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/audio_bus.dart)<br>[game/mobile/lib/soundtrack_export.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/lib/soundtrack_export.dart)<br>[game/platform/lib/soundtrack_delivery.dart](/Users/csys/Desktop/ibicot/idle/game/platform/lib/soundtrack_delivery.dart)<br>[services/tideglass_service/soundtrack.py](/Users/csys/Desktop/ibicot/idle/services/tideglass_service/soundtrack.py)

Evidence: [release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md)<br>[release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md](/Users/csys/Desktop/ibicot/idle/release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md)

## RF: Stale regression correction

Original optional Focus contract supports repair; zeroFocus chapter3 and actual3charges/1800s assertions retained. Proposed/root-owned, not accepted by this audit.

Source: [game/mobile/test/qa_integration_simulation_test.dart](/Users/csys/Desktop/ibicot/idle/game/mobile/test/qa_integration_simulation_test.dart)<br>[game/simulation/lib/supplemental_run.dart](/Users/csys/Desktop/ibicot/idle/game/simulation/lib/supplemental_run.dart)

Evidence: [release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/FINDING.md](/Users/csys/Desktop/ibicot/idle/release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/FINDING.md)<br>[release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/repair.patch](/Users/csys/Desktop/ibicot/idle/release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/repair.patch)

