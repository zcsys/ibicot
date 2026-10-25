from pathlib import Path
import json, hashlib, datetime, collections
ROOT=Path('/Users/csys/Desktop/ibicot/idle')
OUT=Path(__file__).parent
CAND=ROOT/'.tooling/build-candidates/20261023T032609.052120Z-a052a4405347'
original=json.loads((OUT/'original-contracts.json').read_text())
program=original['implementation/program.json']; scopes=original['implementation/scope_requirements.json']['requirements']; backlog=original['v1_backlog.json']['items']
items={x['id']:x for x in program['items']}; prod=[x for x in program['items'] if x['source']=='v1_backlog.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
E={}
def ev(key,label,source,proof,boundary):
 E[key]={'label':label,'source':source.split('|'),'evidence':proof.split('|'),'boundary':boundary}
ev('F','Foundation and original contract','docs/release-contract.md|docs/decisions/engine-and-number-selection.md|docs/decisions/execution-costs.md|docs/quality/V1_QUALITY_PROTOCOL.md|release/device-matrix.json','release/qa/FOUNDATION_REVIEW.md|implementation/reports/director-foundation-review.md','Accepted foundation decisions do not provide resources or a finished public release.')
ev('N','Frozen native candidate and failed host gate','tool/build_native.py|tool/verify_native.py|tool/verify_current_runtime.py|game/mobile/integration_test/platform_smoke_test.dart|game/mobile/integration_test/current_runtime_test.dart','release/native-proof/20261023T032749.977866Z/build-report.json|release/native-proof/20261023T032749.977866Z/mobile-test.log|release/native-proof/20261023T032749.977866Z/operations-test.log','a052 host gate ended 26/28, no current exports/runtime matrix. Test expectation and operations interpreter environment repairs are separate assignments.')
ev('Q','Numbers and chronology','game/core/lib/src/fixed.dart|game/core/lib/src/state.dart|game/core/lib/src/engine.dart|game/core/lib/src/daily_engine.dart|game/core/lib/src/support_engine.dart','release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json|release/qa/lead-bounded-acceptance-20261021T1148Z/DECISIONS.md','62 exact current numeric/timeline rows, 15,365 assertions; no discrete tolerance; source bridge is narrower than human pacing or all native behavior.')
ev('P','Durable local state','game/persistence/lib/tideglass_persistence.dart|game/mobile/lib/bootstrap.dart|game/mobile/lib/client_economic_transition.dart|game/mobile/lib/offline_replay.dart','release/persistence-review.md|release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md|release/qa/lead-transition-acceptance-20261021T1221Z/DECISIONS.md','208 core and 28 persistence tests with real host process kills; nested reentry/writer failures repaired. Not physical power loss.')
ev('C','Pinned configuration','game/mobile/lib/bundled_content.dart|game/mobile/lib/content_compatibility.dart|game/mobile/assets/config/manifest.json','release/qa/lead-config-acceptance-20261021T141750.104883Z/DECISIONS.md','29 packaged files and exact compatible transition; unknown versions fail closed.')
ev('U','Shell, onboarding and reset','game/mobile/lib/app.dart|game/mobile/lib/game_controller.dart|game/mobile/lib/strings.dart|game/mobile/lib/rechart_forecast_task.dart|game/core/lib/rechart_forecast.dart','release/qa/lead-client-shell-acceptance-20261021T145030.603397Z/DECISIONS.md|release/qa/qa-reset-20261023T025256.370588Z/RESET_REVIEW.md|release/qa/lead-daily-icons-20261023T031715.308630Z/REVIEW.md','Actual 320/1024 at 200% English/pseudo forecast dialog, honest two-branch assumptions, snapshot isolation/cancel/confirm; onboarding comprehension still needs people.')
ev('A','Earned automation','game/core/lib/src/daily.dart|game/core/lib/src/daily_engine.dart|game/mobile/lib/daily_panel.dart','release/qa/lead-automation-acceptance-20261021T143015.491121Z/DECISIONS.md','10/25/100 unlocks, priorities/reset boundaries, one free and five 50-Note slots, real repository plan round trips.')
ev('D','Daily timeline','game/core/lib/src/engine.dart|game/core/lib/src/daily_engine.dart|game/core/lib/src/support_engine.dart|game/mobile/lib/daily_panel.dart|game/mobile/lib/offline_replay.dart','release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md|release/qa/integration-transition-repaired-20261021T121351672733Z/TRANSITION_REVIEW.md','Shared event chronology, saved-policy replay, remainders, seeded frozen goals/rerolls and receipts; historical results retain their pins.')
ev('K','Calibration and accessible completion','game/mobile/lib/calibration_screen.dart|game/mobile/lib/calibration_pattern.dart|game/content/calibrations/calibration.01.pattern.json','release/qa/integration-accessibility-20261021T125317256764Z/CALIBRATION_REVIEW.md|release/qa/lead-calibration-scope-acceptance-20261021T130612.263921Z/DECISIONS.md','All12 actual patterns and equivalent completion independently reviewed; S09/S17 accepted, not entire accessibility scope.')
ev('R','Reminder and settings adapters','game/mobile/lib/notification_service.dart|game/mobile/lib/reminder_lifecycle.dart|game/mobile/lib/notification_settings.dart|game/mobile/lib/audio_settings.dart|game/mobile/lib/number_format.dart','release/qa/integration-reminders-initial-20261016T115431767720Z/REMINDERS_REVIEW.md','30 host tests and 384 departure conditions; native plugin calls mocked. Actual permission/delivery/revocation not demonstrated by current 58-cell harness.')
ev('S','Cloud/account/service ledger','services/tideglass_service/api.py|services/tideglass_service/storage.py|game/platform/lib/tideglass_platform.dart|game/mobile/lib/native_services.dart|game/mobile/lib/service_settings.dart','release/qa/integration-services-repaired-20261016T114721906724Z/INTEGRATION_REVIEW.md','Real local HTTP/database and adversarial tests; optional linked account and explicit branch choice implemented. Default service/provider configuration disabled.')
ev('G','Campaign and challenges','game/content/progression/campaign.json|game/progression/lib/tideglass_progression.dart|game/progression/lib/decoration_purchase.dart|game/mobile/lib/story_screen.dart|game/mobile/lib/story_state.dart','release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md|release/balance/optional-calibration-current-integration.json','Six chapters/ending, 12 isolated dossiers across3 families,18 archives; ending needs six dossiers/600 Notes, not all1,750 optional collection. Optional calibration repaired.')
ev('V','Season and pass','game/events/lib/src/season.dart|game/events/lib/src/pass.dart|game/events/content/season.01.json|game/mobile/lib/season_screen.dart','release/client-season-review.md|release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md','Isolated fleet,28-day boundary,30×500XP,30free/10premium, one selected archived pass and idempotent alternatives; virtual boundaries are not elapsed calendar observation.')
ev('T','Complete content presentation','game/mobile/lib/story_screen.dart|game/mobile/lib/season_screen.dart|implementation/content/launch_manifest.json','release/qa/lead-content-matrix-20261021T144134.921859Z/MATRIX_REVIEW.md|release/content-presentation/full-matrix-repaired-20261021T143209447416Z/verification.json','12 actual conditions,876 tests/1,644 rows; 62 content IDs plus3 daily/help flows. Later App delta bridged separately; no relabeling historical captures.')
ev('I','Harbor, producers, cosmetics','game/mobile/lib/harbor_art.dart|game/mobile/lib/producer_art.dart|game/mobile/lib/cosmetic_art.dart|game/mobile/lib/cosmetics.dart','release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md|release/qa/lead-art-scope-acceptance-20261021T124855.896748Z/DECISIONS.md','7harbors/25producers/36cosmetics normal/reduced, phone/tablet 100/150/200 English/pseudo; actual art proof is separate from file counts.')
ev('J','Final daily icons','game/mobile/lib/daily_icon_label.dart|game/mobile/lib/daily_panel.dart|game/mobile/lib/app.dart','release/qa/qa-provenance-version-20261023T031648.974649Z/M3_09_CLIENT_RECOMMENDATION.md|release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/DECISIONS.md','M3-09 accepted unchanged; text equivalents retained; locked/error branches source-inspected, not mislabeled newly rendered fault cases.')
ev('L','Font notices and licenses UI','game/mobile/lib/font_licenses.dart|game/mobile/lib/main.dart|source/art/ui/font-manifest.json','release/qa/qa-reset-20261023T025256.370588Z/FONT_NOTICE_REVIEW.md','Actual licenses reading/keyboard/target evidence with documented SDK4px tablet overlap; packaged-native inclusion still pending current export.')
ev('B','Long-horizon simulation','game/simulation/lib/policy_run.dart|game/simulation/lib/supplemental_run.dart|game/simulation/lib/supplemental_math.dart|game/simulation/bin/run_optional_calibration.dart','release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md|release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md|release/balance/optional-calibration-current-integration.json','184 corrected historical cases plus15 focused current optional-calibration cases, not a silently rerun184. Exact no-bonus/free/ad synthetic fixtures; human pacing and beta freeze not established.')
ev('Y','Real commerce adapter and fulfillment','game/mobile/lib/native_services.dart|game/mobile/lib/service_cosmetics.dart|services/tideglass_service/providers/stores.py|services/tideglass_service/providers/admob.py|services/tideglass_service/providers/notifications.py|services/tideglass_service/reconcile.py|services/tideglass_service/vault.py','release/qa/integration-native-ownership-repaired-20261019T145035575220Z/NATIVE_OWNERSHIP_REPAIRED_REVIEW.md|release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md','Production SDK/server verification paths exist; fixtures validate logic, not actual sandbox purchase/refund/ad service. Signatures/leases separated from untrusted saves.')
ev('W','Privacy and public support plumbing','game/mobile/lib/public_links.dart|game/mobile/lib/public_links_model.dart|services/tideglass_service/web_deletion.py|game/mobile/lib/ad_privacy_copy.dart|services/docs/PRIVACY.md','release/qa/client-web-deletion-20261021T134443512157Z/WEB_DELETION_REVIEW.md|release/qa/integration-ad-privacy-20261021T141749224307Z/PRIVACY_REVIEW.md|release/qa/integration-current-ui-20261021T133115456638Z/CURRENT_UI_REVIEW.md','Actual local browser and native links UI, UMP flow and lifecycle failure tests; public URLs/operator policy, real provider regions and native SDK traffic inventory remain unqualified.')
ev('O','Operations tools','services/tideglass_service/deployment.py|services/tideglass_service/alert_transport.py|services/tideglass_service/operator_cycle.py|services/tideglass_service/ops.py|services/tideglass_service/health.py|services/tideglass_service/recovery.py','release/qa/gameplay-ops-review-20261021T140405144186Z/OPERATIONS_REVIEW.md|services/evidence/deployment-20261021T140912481855Z/REPAIRED_AUTHOR_REVIEW.md','37methods+9real localHTTP/TLS scenarios,256 fixture requests; actual local alert receiver, backup/recovery/flags. Not qualified hosted staging, human acknowledgment or14days coverage.')
ev('H','Study collection and analysis','game/platform/lib/study_recorder.dart|game/mobile/lib/study_gate.dart|game/mobile/lib/study_native_context.dart|tool/study_report.py|release/study/protocol-template.json','release/qa/integration-study-20261021T102508755253Z/STUDY_REVIEW.md|release/qa/integration-study-collection-final-20261021T113037215270Z/COLLECTION_REPAIRED_REVIEW.md|release/study/README.md','Synthetic schema2 registry/missingness/crash linkage and UI collection controls; zero people, real cohort, or elapsed observation.')
ev('X','Native privacy observer/inventory','release/native-privacy/runtime_observation.py|release/native-privacy/inspect_artifacts.py|game/mobile/integration_test/current_runtime_test.dart','release/qa/native-observation-retest-20261023T032106.255153Z/REVIEW.md|release/native-privacy/observation-integration-20261023T032452.071407Z/verification.json','Repaired collector41+9+6methods; actual native observation pending. Android storage deliberately unavailable; snapshots cannot prove no traffic or wholeSDK data behavior.')
ev('Z','Release/store/coverage preparation','release/store/metadata.en-US.json|release/runbooks/LAUNCH_HANDOVER.md|release/runbooks/launch-coverage-template.json|release/season-2-brief.md|release/store/tools/export_preview.swift|release/store/tools/inspect_preview.swift','release/store/CLIENT_REVIEW.md|release/qa/client-preview-tool-20261023T032106.818906Z/PREVIEW_TOOL_REVIEW.md','Original creative exists; silent20s historical152 exporttool independently checked, not current final editorial media. Store accounts/URLs/coverage and actual launch absent.')
ev('M','Asset source/provenance bookkeeping','implementation/art/production_contract.json|implementation/content/launch_manifest.json','release/qa/qa-provenance-version-20261023T031648.974649Z/PROVENANCE_REVIEW.md|release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md|release/qa/lead-daily-art-acceptance-20261023T032547.803843Z/provenance-integration.json','164actualsource/export/provenance sets;34version records/42bindings+37existence updates preserve oldcaptures/rights/nullapproval. Canonicalasset approval remains unfinished.')
ev('AU','Original audio and soundtrack','game/mobile/lib/audio_bus.dart|game/mobile/lib/soundtrack_export.dart|game/platform/lib/soundtrack_delivery.dart|services/tideglass_service/soundtrack.py','release/qa/client-assets-current-20261023T025348.813709Z/ASSET_REVIEW.md|release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md','Original authored audio files, three ambient masters, cues and supporterZIP; native decode/playback proof is narrower than mix, interruptions and real purchased receiving-app delivery.')
ev('RF','Stale regression correction','game/mobile/test/qa_integration_simulation_test.dart|game/simulation/lib/supplemental_run.dart','release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/FINDING.md|release/qa/optional-calibration-regression-repair-20261023T033151.002932Z/repair.patch','Original optional Focus contract supports repair; zeroFocus chapter3 and actual3charges/1800s assertions retained. Proposed/root-owned, not accepted by this audit.')
# Each tuple: evidence groups; concrete implementation; required verification/disposition.
R={
'M0-01':('F','Approved release contract fixes platforms, audience, language, content, ethical rules and decision roles.','Existing accepted decision retained; public launch remains separate.'),
'M0-02':('F N Q','Portable deterministic Dart core and native Flutter stacks; exact-number choice documented.','Existing bounded engine decision retained; no store-service inference.'),
'M0-03':('S Y','Native StoreKit/Billing/UMP/ad adapters and real local cloud revision service exist.','Actual sandbox purchase/restore, ad availability and configured provider build absent; external accounts required.'),
'M0-04':('F U P','Actual purchase, reset/return and recovery screens implemented.','Existing accepted journey/prototype decision retained; human comprehension is M2-06.'),
'M0-05':('I M','Reusable harbor/producer style, complete fixed inventory and budgets exist.','Existing accepted treatment/budget; no per-asset blanket approval.'),
'M0-06':('F H','Named seven-device matrix, severity, reproducible fixtures and recruitment/evidence protocols.','Existing accepted plan; physical devices/recruitment unavailable.'),
'M0-07':('F O Z','AI roles and cost variables/resources recorded; no inherited human payroll promise.','Provider/resource/contractor arrangements and measured operating forecast not confirmed; no spending authorized.'),
'M0-08':('F N C','Pinned wrappers, immutable candidate snapshots, native export pipeline and artifact manifests.','Accepted build mechanism retained; a052 current host gate failed, so exact final artifacts must follow repairs.'),
'M1-01':('Q','BigInt micro-R, high-precision output/remainders, telescoping bulk costs and exact prestige comparison.','Existing accepted numerical clause and unchanged economic constants retained.'),
'M1-02':('Q D','Five tiers, unlocks, milestones, lifetime/award subtraction and explicit chronology are production core.','Existing accepted state-machine clause retained.'),
'M1-03':('P','Two committed generations, checksums, atomic rename, import archives, revision guards and compiled migrations.','Host fault/SIGKILL evidence covers original local clause; named acceptance decision remains. Current native lock/return execution adds target proof, not an invented prerequisite.'),
'M1-04':('C P','Validated29bundled files and immutable compatible migration registry with old-interval settlement.','Existing accepted exact schema/version criterion retained.'),
'M1-05':('U I','Actual wallet/rate/bulk controls/milestones/reset/settings at small/large layouts.','Existing accepted shell criterion retained; not full accessibility/device release gate.'),
'M1-06':('G B','Six goals/ending, challenge rules,600mandatory versus1750total Note budget, daily/pass exceptions.','Existing accepted authored progression map retained; human pacing unproven.'),
'M1-07':('I J L','Actual modular parts/layers/UI/typography/icons, plus preserved font notices.','Existing accepted slice component criterion; current native font bundling pending.'),
'M1-08':('Q P RF','Production oracle, exact boundary, corruption, rapid reset, interruption fixtures exist.','M1-03 acceptance prerequisite remains; a052 stale optional-calibration assertion must pass repaired focused/full host gate.'),
'M2-01':('Q A','Reachable10/25Chart progression, synergies, freeautobuy and samepolicy replay.','Existing accepted first-session economy; no simulated-to-human pacing conversion.'),
'M2-02':('U W','Dismissible persisted introduction; purchase/rate hints, reset losses/retentions, earnedautomation explanations; commerce separate route.','Narrow named review of existing actual guidance/skip evidence remains; 15-person comprehension belongs to M2-06, not a new prerequisite here.'),
'M2-03':('U B','Marginal network values, threshold, asynchronous bounded retain/reset forecast and readable assumptions.','Accepted after independent numerical/isolate/UI review; source has no optimum claim.'),
'M2-04':('S P','Cloud revisions preserve stale candidate branches; explicit generation-checked select and local displaced backup.','Local HTTP conflict proofs exist; original M1-03/M0-03 dependencies remain. Real deployed cross-device recovery not established.'),
'M2-05':('I','Five silhouettes, representative harbor and all milestone variants/reducedmotion in client.','Existing accepted representative presentation criterion retained.'),
'M2-06':('H U','Study instrument/collector available; no new testers enrolled.','15 genuinely new moderated sessions, pacing/nonreachers,80%comprehension and blocker resolution absent.'),
'M2-07':('N F P','Slice native harness/recovery tests and device protocol exist.','Reference physicalhardware slice report/funding decision absent; cloud prerequisite not accepted.'),
'M3-01':('Q D P','2hFocus,8hSurvey,24/72hweighted replay,expiry/day boundaries share engine.','Original mechanism has host/boundary proofs; named acceptance awaits M1-03. Current native integrated replay still pending.'),
'M3-02':('D T','Seeded identity/snapshots, one reroll, offline earning/build progress,7day21slots and uniqueclaims.','Core/content/dailyUI evidence exists; original M3-01 acceptance and exact named decision remain.'),
'M3-03':('A','Priorities and opt-in reset plans,100Chartguard,onefree/fiveNote slots persist and replay.','Existing accepted automation criterion retained.'),
'M3-04':('K D T J','Untimed12patterns, equal alternate path, Focusqueue,Surveys and fullcontract daily screens.','S09/S17 bounded proofs complete; M3-01/M3-02 dependencies plus whole-session named package decision remain.'),
'M3-05':('R U AU','Text/notation/motion/audio/input and serialized defaultoff quiet-hour reminder service implemented.','Actual iOS/Android permission/schedule/delivery/revoke flow is uncovered; hostpluginmocks/currentNoOp harness cannot close across-target criterion.'),
'M3-06':('S W Y','Link/recovery-code lifecycle, export/delete/signout, preserved selectedbranch recovery and authoritative ownership.','Local account/outage/browser evidence exists; M2-04 prerequisite and real configured lifecycle/provider ownership proof remain.'),
'M3-07':('S Y D','Service transactional purchase/support/pass receipts separated from gameplay; persistentgrant/ack/retry.','Real provider interrupted-grant proof and original M0-03/M3-06 dependencies remain.'),
'M3-08':('G T B','Six complete chapters and12goal/rule/budget dossiers, passive/active policy inputs authored.','Implementation is present; explicit original M2-06 human-study prerequisite blocks acceptance.'),
'M3-09':('I J M','25distinct producer presentations plusfinaldailyFocus/Survey/contract/automation icons/textstates.','Accepted17thoriginal package at original clause; no global asset/native gate added.'),
'M3-10':('D Q B P','1/3/6visit,absence/queue/resetday chronology and interruptedsave test/instrument paths exist.','Host numeric/cadence evidence strong; original daily/account/ledger dependencies unresolved. Preserve historical/current source bridge and remaining native proof.'),
'M4-01':('G B','Isolated dossier fleets, deterministicgoals,independentmainloop and noeconomicexport/restartmint.','Reachability/virtualstrategy cases exist; original M3-08 prerequisite requires prior humanstudy.'),
'M4-02':('V G D','Pinned28day isolatedfleet with correcteventcoefficients,start/end/archiveresume,noChartimport.','Acceleratedengine/UI evidence exists; original M4-01/M3-01 dependencies. Real28days is M6-07, not silently required here.'),
'M4-03':('V Y I','Preview/equip,storeprice/status,restore,selectedpass/freepremium/archive UI andsharedXP.','Actual localized products/restore and original ledger/event prerequisites remain; syntheticprices are not commerce qualification.'),
'M4-04':('Y S','Server-verifies provider proofs,transaction identity,grant/ack/refund/reconciliation,vault andsignedownership.','Production paths present but genuine both-store sandbox and failures require accounts/products/hosting; original dependencies retained.'),
'M4-05':('Y D W','Freebriefing andSSV adroute share6slots;privacy/no-fill/retry/signedclaim safeguards.','Host/adfixture parity complete locally; real provider consent/refusal/no-fill/callback environment absent.'),
'M4-06':('G V K T M','All6chapters/ending12dossiers12patterns18archives/fullSeason1 data/copy exists andread-throughmatrices.','Per-ID proof not justmanifestcounts; original M3-08/M4-01/M4-02 dependencies and final namedcontentdecision remain.'),
'M4-07':('I AU M L','All7harbors/fixed36cosmetics and originalauthoredscore/cues integrated.','Existing variant/artproof reused; finalize exact canonical per-ID review record/nativeimports/audio qualification without blanket humanapproval. M4-06 dependency remains.'),
'M4-08':('G V B Y T','Reachablecontent/reward commands,15000XPfreefinish,cosmetic-onlyexports and ledgerisolation.','Logic/virtual/UI evidence exists; all5original commerce/content/art dependencies remain, including realverifiedpaid delivery.'),
'M5-01':('P N','Bounded isolateworker,visibleprogress/chunking,losslesscursor/precision and memoized engine implemented.','Namedphysical60/30fps,p95startup5s/replay3s,30minutebatterythermal measurements absent; simulator speed cannot close.'),
'M5-02':('U T I K W L','Large-textEnglish/pseudo,reducedmotion,noncolor,semantics/keyboard and12pattern alternatepaths implemented.','Extensive actualhost matrices complete; namedtarget input/OS assistive flows and originalsettings/commerce/contentdeps remain. Do not repeat unchanged fullmatrix.'),
'M5-03':('W X S Y','Data inventory,accountconsent/delete/export,outage controls,UMP options andoptionalnativeobserver implemented.','Finalartifact inventory/default/refusal observation pending; observerselectedfiles/sockets is partial,Androidstorage unavailable. RealconfiguredSDK/providerdata/deployedretention remain.'),
'M5-04':('O H S','Eventschemas/studycollection,dashboards,alerts,backups/supportreceipts/featureflags implemented.','Actuallocalreceivers/load/faults complete; allrequired functions in qualifiedstaging,actualalert recipients and originalledger/purchase prerequisites remain.'),
'M5-05':('B G H','184correctedhistorical trajectories,15currentoptionalcalibrationruns,actual1750Notesinks,strategycomparison andmetrictools.','Do not relabel184ascurrent; explicit finalnumeric/contentconclusionbridge and betaconfig/metricfreeze needed after originalsM4-06/M5-04; actualhumanobservations separate.'),
'M5-06':('I AU Z M','Actualassets/audio,icon/featurecreative,rawhistoricalcapture andreviewedexporttool exist.','Currentqualifiedcapture+intentionalfinalscreenshot/videoediting/inspection pending; originalM4-07 and finalsound/presentationreview remain.'),
'M5-07':('P N F RF','Hostsave/migrationfaults,versiontransition/currentruntimeprocesskill/return harnesses implemented.','a052hostfailed/noexports; repair andnewfreeze mandatory. Fullnamedphysicalmatrix/storage/network/updateconditions absent; no known issues waived.'),
'M5-08':('Y S W','Real localHTTP faults/providerfixture retries/duplicates/crashes andownership/adrefusal tests implemented.','Actualboth-store/providerpacketloss/refund/outage cases unavailable; originalM4-04/M4-05/M5-04 dependencies remain.'),
'M6-01':('H','Preregistrationtemplate,registry/consent/export/adjudication andcohortanalysis tools exist.','No recruitment/enrollment; actualeligible baseline/config/acquisition/exclusions and originalM5-05/07/08 dependencies missing.'),
'M6-02':('H B','Wilson/coverage/maturity reporting andcampaign/welfare instruments exist.','No matureD1/D7/D30,playersatisfaction/commercialdata orshipdecision; tooloutputs are synthetic.'),
'M6-03':('B Q','Versionedregression/trace machinery andrepairedknownfindings exist.','Futureobservedcohortfindings absent; cannot markunknownresolution work done. M5-01/M6-01 prerequisite gates remain.'),
'M6-04':('U H T','LocalUI defectsrepairedwithactualglyph/control proof; studyinstruments ready.','No observednewplayeronboarding/recoveryfindings; originalM5-02/M6-01 requirements remain.'),
'M6-05':('O Y H','Stagedaccess/support/reconciliation/disable mechanisms andlocaldrills implemented.','No realopt-in testers/stagedservice/supportrecoveryobservations; originalM5-04/M6-01 remain.'),
'M6-06':('T I H','Localreadability/contentdefects fixedwithunchangedinventory.','Polishfromobservedplayerplaynotperformed; M5-06/M6-01 dependencies remain.'),
'M6-07':('V H','28day/archive logic andcalendar-awareanalysis implemented.','No real28daypass or matureD30 cohort; acceleratedtime is separate.'),
'M6-08':('V Y O P','Passarchive/continuation,receipt replay,compatible migration anddisposablerestore drill paths exist.','Combinedactualstagedseason/paidcontinuation/recovery rehearsal absent; M4-08/M6-05 dependencies remain.'),
'M7-01':('F H Z','Hardgate checklist,minorisue/runbook/seasonbrief templates exist.','Allgates/productthresholds andactualship/change decision unfulfilled; a developmentfreeze is not releasefreeze.'),
'M7-02':('N P C','Deterministic candidate/replay/tagging pipeline andcompatiblecore/config path exist.','Finalstabilization/releaseversion requiresM6-03/M7-01; a052failedhost cannot befinal.'),
'M7-03':('N Y M','Nativeproject/export/adapters/artwork exist.','Authorizedsigning/distribution/installupdateonactualtargets,licensedasset reconciliation/storeflows required; noaccounts/finaldistribution.'),
'M7-04':('O P Z','Boundeddeploy/flags/backup/reconcile/forwardrepair tools andrunbooks exist.','Actualstagingcapacity/key/backup/ownershipreplay rehearsal andM6-05/M7-01 outstanding.'),
'M7-05':('Z W T','Englishcopy/creative/help/credits/publicpagedrafts andcaptureedit tooling exist.','Exactsubmittedcandidatefinalmedia/workingURLs/offers/reviewer/supportarrangements pending; currentcaptureassigned, noinventedpublicsites.'),
'M7-06':('F N Z','Evidencepack machinery andscopeaudits exist.','Allgatelinks/acceptedminorissues/zero blockers requireM7-02/03/04; unresolvedhost failures and externalgates prohibit releaseapproval.'),
'M7-07':('Z Y W','Submissiondrafts,reviewerrequirements/identities checklist andresourceinventory exist.','Currentofficial recheck atsubmission,workingproducts/revieweraccess,actualplatformsubmission/acceptance absent.'),
'M7-08':('Z O','14daycoverage template,escalation/stopconditions andSeason2initialbrief exist.','Named datedcoverage/authority/ongoingcosts unresolved. Actual14days andfinalrecord are separateOPS-14/S38, not simulatedcoverage.')}
assert set(R)=={x['id'] for x in prod}
S={
'S01':('F N','Nativeclient/buildpipeline andresponsiveUI implemented.','Publicinstall/update/signedbothstorelaunch notdone; currenthostgate failed andphysical/accounts absent.'),
'S02':('U S T W','Guestofflinecore/optionalaccount/cachedcontent/externalEnglish+pseudo implemented.','Hostlayout/localoutageproof exists; exactcurrentnativeairplane/resume andconfiguredcloud qualification remain.'),
'S03':('Q','Exactfiveproducer baseline/geometry/unlock implemented.','Verified originalbounded numerical clause; nochange.'),
'S04':('Q U I J','Single/milestone/max purchases and25/50/75/100whole-tiertransformations implemented.','Core +actualpurchaseUI+25stage proofs exist; narrowcombinedscope decision stillopen, not missingcontrols.'),
'S05':('Q U P','Lifetime0.65minusawarded Charts,permanentpower/reset/retainedpreview implemented.','Exactcoreandnewactualdialogproof exists; complete retainedstate client/persistence acceptance review remains.'),
'S06':('A Q','10/25/100 thresholds and1+5savedplans correct.','Verifiedoriginalscope; no paidautomationlock.'),
'S07':('Q U B','Correctcross-tiermatrix/fullmarginal output/purchase andrealconditionalresetforecast.','M2-03accepted; latechoiceaudit evidence sourcebridge mustbe explicit; scope not automaticallypromoted.'),
'S08':('D P Q','Shared eventreplay with24full+48quarter andsavedpolicy.','Hostexactparity/capproof exists; original24hreplaybudget onphysicalmin unmeasured.'),
'S09':('K D','2h/cap12/20%600squeue andequalaccessiblecompletion.','Verifiedbounded originalscope; separateoverallaccessibilitygate.'),
'S10':('D T','8h/cap3/10Notes,phasecarry/automaticresume/idempotentclaim.','Hosttimeline/dailyUI evidence exists; narrowfulloriginalscope decision anddependencies unclosed.'),
'S11':('D V T','3×10Notes/250XP frozen seededcontracts,one reroll,7day21backlog andno paid/prestigeobjective.','Coreandactualfullcontentmatrixproof exists; originaltimeline/accountledger prerequisites unclosed.'),
'S12':('P','Runtimechecksummedatomicbackups/import/migration/locking implemented.','Realhostfault/SIGKILL proof exists; narrowclause acceptance separatefrom physicalmigration/storagegate.'),
'S13':('S P','Revisionpreconditions,storedforks,explicitselection,nobalanceaddition.','Localtwo-clientHTTPselection proof exists; actualconfiguredcross-device/storeownership context unqualified.'),
'S14':('Q P C','Carriedremainders/explicitorder/pinnedoldintervaltransition.','Verifiedoriginalbounded transition/numeric clause; no arbitrarymigrationclaim.'),
'S15':('G B H','Sixchapters/ending/continue reachablewithoutFocusorpaid/alloptionals; noharddate lock.','15currentvirtualruns10.5–11.17days do notestablishordinary15–30dayhumantarget; observedlaterchaptergate absent.'),
'S16':('G B T','12dossiers/3families/100Notes persistententry andisolatedreplay.','Allgoals virtualreachable andactualcontentpresented; originalhuman-prerequisite chain remains.'),
'S17':('K','12actualauthoredpatternsandidentical-valueaccessiblepath.','Verifiedoriginalscope.'),
'S18':('G B I T','18archives/six50Noteoptionaldecorations,noallcollectionending.','Actualread-through/virtualNote-spending proofs exist; per-ID/wholeclause acceptance remains.'),
'S19':('I','7harbors/25producers withnormal/reducedmotion actualintegratedart.','Verifiedoriginalscope; no globalasset/nativeclaim.'),
'S20':('V B H','28dayisolatedSeason1/coefficients/noprestige/noexports.','Acceleratednew/veteran/archiveproof exists; actuallivecalendarobservation absent.'),
'S21':('V Y T','30×500XP,10cosmetic+20fragment free,10premium,selectedarchivecontinuation.','Logic/rewardread-through proof; genuinepaidcontinuation/restore andoriginalprerequisites unfulfilled.'),
'S22':('I M V','36actualuniqueappearanceIDs12/10/10/4;supporterreuses4shopitems.','Artmatrix andzero-economicreward tables exist; exactperassetreview/entitlementfulfillment acceptance unfinished.'),
'S23':('AU R M','Originalambient/cues/independentcontrols andverifiedarchive deliverycode.','Actualdriverdecode != mix/interruption/receiving-apporrealpurchasedfulfillment; finalsoundreview/providers/physicalconditions remain.'),
'S24':('Y S','Nativeprice/preview/status/verifiedgrant/restore/refund/revoke implementations.','Bothactualstoresandbox absent; fake/syntheticadapter results neverqualifythisscope.'),
'S25':('D Y B W','Shared6slots/300equivalentseconds,speed1200×25%,boundeduniqueofflinecache,additive1.45.','Hostmath/routeparity/localfaultproof exists; realproviderrefusal/no-fill andwholetrajectory currentversionconclusions remainbounded.'),
'S26':('R U T L','Text/notation/motion/audio/largecontrols/contexthelp/quietnotifications implemented.','Concreteuncoverednativepermission/delivery/revoke path; namedtargetinput/physicalOSassistiveproof remains.'),
'S27':('W Z T','Actualhelp/recovery/credits/releasenotes/publicpagedrafts/nativeURLlauncher/browserdeletion/runbooks.','PublicURLsoperatorcontacts/policy andactualworkingreview/supportlinks absent; staleunproducedprosetoberesolvedasbookkeeping.'),
'S28':('P Y N','Atomiccore/save/claim/ownership defenses plusfaultfixtures implemented.','No newproductionintegritydefect foundbythisaudit; cannotdeclarezeroreleaseblockers withoutcurrentgate/provider/physicalproof.'),
'S29':('Q','BigIntdiscretedecisions andspecifiedcontinuousprecision/errorbudget.','Verifiedoriginalscope unchanged; exactnumericbridge retained.'),
'S30':('H N','Consentedrawsession/diagnosticlinkage/adjudication andcrashdenominator reportingimplemented.','Zeroobservedplayersessions;99.5%over10000platform/devicegroups cannot be establishedsynthetically.'),
'S31':('P N F','Progress-visiblelosslessworker andperformanceinstrumentation.','Namedphysicalp95/startup/replay/30minbatterythermal absent; nohost/emulator substitute.'),
'S32':('H U','Moderatedinstrumentandtelemetry collectionready.','15newpeople,80%explanations,medianreacherpaceplusnonreacher proportion absent.'),
'S33':('B','184historical30/90visit/reset/buy/bonus+real1750Notespend cases;15currentoptionalrepair runs.','Finalexactconclusion/sourcebridge andbetafreeze stillrequired; no broadrepeat justified merelyby UI/commentchanges.'),
'S34':('H V','Pre-registration/registry/exclusions/maturity/missingness/intervals andseasonlogic.','No realstarts/cohort/D30/28dayseason;500/10000planningtargets notpowerguarantees.'),
'S35':('H B F','Descriptivereporting/uncertainty/productdecision instruments.','No actualretention/strategy/welfare/commercialcostdecision;35/15/7 hypotheses notautomaticshipcriteria.'),
'S36':('N Y W Z','Nativeprojects/listingdrafts/providerandpublicplumbing.','Currentofficialsubmissionrecheck andsignedacceptedbuilds/products/revieweraccess requireaccounts; nopublicreviewperformed.'),
'S37':('O P Z','Monitoring/flags/backup/deletionmanifest/reconcile/forwardrepair/stoprunbooks.','Localrealdrillscomplete; actualstaging/live/alertrecipientcoverage absent. Do notaskforgenericCLIrebuild.'),
'S38':('Z','14daycoverage templateandinitialSeason2brief.','14actualdayslaunchcoverage/incidentfollowthrough/finalrecord absent; noalways-onAIassumption.'),
'S39':('W X S','Data/lifecycle/consent/refusal/export/delete/outagecodeandboundedcollector.','Exactfinalnativeartifactinventory anddefault/refusalobservations pending; Androidselectedstorageunavailable; configuredSDK/deploymentpolicy notqualified.'),
'S40':('F N C','Pinnedstack/wrappers/buildsnapshots/validateddefaults/incompatibleupdate rejection.','Currenta052host26/28failed; newcandidateafterrepairs needed. Account-dependentnativeprobe stillopen.'),
'S41':('F M','NamedAIroles/independentreview/deviceplan/costvariables maintained.','Concreteexternalresource/costarrangement absent; duplicateartiststatusfields stale,notnewassetrejection.'),
'S42':('F N Z','Original65/44traceability andfrozen evidencepackmechanisms.','17original+3bootstrapaccepted/7scopesverified; nofinalapprovedcandidate, allgates andminorissues notclosed.'),
'S43':('U T I Z','Localreadability/contentrepairs andactualcreative/captureediting tools exist.','Currentcandidatecaptures/finaleditedmedia andobservedplayerpolish remain; currentnativejob stoppedbeforeexports.'),
'S44':('G B H','Threechallengefamilies andtwoor morequantitativelyviableresetstrategies withtradeoffs.','Virtualwinningpolicychangesbyhorizon; meaningfulunderstandablechoices andwelfare requireobservedplay, notarithmetic alone.')}
assert set(S)=={x['id'] for x in scopes}
# Missing optional named aggregate references are discovered, not silently fabricated.
paths=set()
for x in E.values(): paths.update(x['source']);paths.update(x['evidence'])
missing=[p for p in sorted(paths) if not (ROOT/p).is_file()]
if missing: print('MISSING_REFERENCES',missing)
# Require source references; evidence aliases can only be repaired explicitly before finalization.
assert not missing,missing
import re,difflib
# Full human-readable evidence anchors accompany every row; original wording is untouched.
S['S33']=('B','The corrected historical 184-case simulation and 15 current optional-calibration runs jointly cover 30/90-day visit, reset, buying, bonus and actual 1,750-Note spending comparisons.','Recommend the bounded S33 simulation criterion for lead decision with S33_BRIDGE.md. No missing trajectory identified. This does not accept M5-05 beta/config/metric freeze or S44 observed-play evidence.')
R['M5-05']=('B G H','Current simulation tools and independently reviewed historical/current reports cover the required strategy and Note comparisons; see S33_BRIDGE.md.','No general 184-case rerun is warranted. Original M4-06/M5-04 dependencies and deliberate beta configuration/metric freeze remain; this audit does not accept M5-05.')
S['S07']=('Q U B','The exact synergy matrix, full marginal network preview, purchase threshold and conditional reset forecast are implemented and independently reviewed.','Recommend the unchanged S07 scope criterion: actual preview comparisons and bounded reset assumptions plus225 reachable-fleet assessments cover its exact wording. No universal optimum or human strategy preference is claimed; M5-05 and S44 remain separate.')
# Preserve full original criteria/dependencies separately from all assessment text.
checks=[]
def check(name,value):
 checks.append({'check':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
check('exactly65production',len(prod)==65)
check('exactly44scope',len(scopes)==44)
for x in backlog:
 p=items[x['id']]
 check(x['id']+' exact original acceptance',x['acceptance']==p['source_acceptance'])
 check(x['id']+' exact original dependencies',x['dependencies']==p['source_acceptance_dependencies'])
check('all original ids exactly once',len({x['id'] for x in backlog})==65 and set(R)=={x['id'] for x in backlog})
check('allscope rows exactly once',set(S)=={x['id'] for x in scopes})
for x in scopes:
 check(x['id']+' mapped only to known work',all(i in items for i in x['work_items']))
 for i in x['work_items']:check(x['id']+' '+i+' reciprocal mapping',x['id'] in items[i]['scope_ids'])
for x in prod:
 for s in x['scope_ids']:check(x['id']+' '+s+' reciprocal mapping',x['id'] in next(v for v in scopes if v['id']==s)['work_items'])
M=json.loads((ROOT/'implementation/content/launch_manifest.json').read_text());PC=json.loads((ROOT/'implementation/art/production_contract.json').read_text())
for k,n in {'chapters':6,'harbor_presentations':7,'producer_families':5,'challenges':12,'calibrations':12,'main_archive':18,'season_fragments':20,'cosmetics':36,'audio':5,'assets':164}.items():check(k+' count',len(M[k])==n)
check('pass levels500XP',M['pass']['levels']==30 and M['pass']['xp_per_level']==500)
check('free30premium10',len(M['pass']['free_rewards'])==30 and len(M['pass']['premium_rewards'])==10)
check('free10cosmetics20fragments',collections.Counter(x['reward']['kind'] for x in M['pass']['free_rewards'])=={'cosmetic':10,'archive_fragment':20})
for a in M['assets']:
 check(a['id']+' source exists',(ROOT/a['source_path']).is_file())
for a in PC['assets']:
 for key in ('source_descriptor_path','export_descriptor_path','provenance_path'):
  check(a['asset_id']+' '+key,(ROOT/a[key]).is_file())
# Source comparison for bounded simulation continuity, not a fresh run.
baseline=json.loads((ROOT/'release/balance/long-horizon-v4-policies.json').read_text());supp=json.loads((ROOT/'release/balance/supplemental-v2.json').read_text())
archive=(ROOT/'game/simulation'/supp['source_archive']).resolve()
bridges={}
for name,d in [('baseline94',baseline),('supplemental90',supp)]:
 rows=[]
 for rel,h in d['source_sha256'].items():
  live=(ROOT/'game/simulation'/rel).resolve();path=str(live.relative_to(ROOT));old=archive/path
  check(name+' historical '+path,old.is_file() and sha(old)==h)
  rows.append({'path':path,'historical_sha256':h,'current_sha256':sha(live),'equal':sha(live)==h})
  if sha(live)!=h:
   dest=OUT/'balance-diffs'/path.replace('/','__');dest.parent.mkdir(exist_ok=True)
   dest.write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),live.read_text().splitlines(True),fromfile='historical/'+path,tofile='current/'+path)))
 bridges[name]=rows
check('82positivebaselineatleast3',all(x['focus_charges_used']>=3 for x in baseline['policies'] if x['bonus_policy']!='none'))
check('90supplementalexactly3',all(x['focus_charges_used']==3 and x['bonus_policy']=='requiredCalibrationsOnly' for x in supp['trajectories']))
check('breaks onlyday10',all(x['break_starts_day'] in (None,10) for x in baseline['policies']))
current=json.loads((ROOT/'release/balance/optional-calibration-2026-10-21T105107709296Z/report.json').read_text())
zero=[x for x in current['policies'] if x['bonus_policy']=='none']
check('6zeroFocuscurrentgrid',{(x['visits_per_day'],x['horizon_days']) for x in zero}=={(v,h) for v in (1,3,6) for h in (30,90)})
check('allzeroFocusends6',all(x['chapters_completed']==6 and x['focus_charges_used']==0 and x['free_support_tokens_used']==0 for x in zero))
nb=json.loads((ROOT/'release/qa/integration-transition-repaired-20261021T121351672733Z/NUMERIC_EVIDENCE_BRIDGE.json').read_text())
for p,h in nb['core_inputs'].items():check('numericbridgecurrent '+p,sha(ROOT/p)==h)
(OUT/'balance-source-bridge.json').write_text(json.dumps({'historical_to_current':bridges,'current_zero_focus_rows':zero,'inference':'See S33_BRIDGE.md; no historical content row relabeled current.'},indent=2)+'\n')
# Scope and item records carry actual paths, evidence keys, original language, dependency blockers.
def sources(keys):return sorted({p for key in keys for p in E[key]['source']})
def evidence(keys):return sorted({p for key in keys for p in E[key]['evidence']})
rows=[]
for p in prod:
 keys,impl,remain=R[p['id']];keys=keys.split()
 rows.append({'id':p['id'],'title':p['title'],'original_acceptance':p['source_acceptance'],'original_dependencies':p['source_acceptance_dependencies'],'original_reviewer':p['reviewer'],'program_status_observed':p['status'],'scope_ids':p['scope_ids'],'implementation_assessment':impl,'required_verification_or_disposition':remain,'unaccepted_original_dependencies':[i for i in p['source_acceptance_dependencies'] if items[i]['status']!='accepted'],'source':sources(keys),'evidence':evidence(keys),'evidence_keys':keys,'release_readiness':'Not established by package implementation or this audit.'})
srows=[]
for p in scopes:
 keys,impl,remain=S[p['id']];keys=keys.split()
 srows.append({**p,'implementation_assessment':impl,'required_verification_or_disposition':remain,'source':sources(keys),'review_evidence':evidence(keys),'evidence_keys':keys,'release_readiness':'Whole product not release ready.'})
(OUT/'work-item-matrix.json').write_text(json.dumps(rows,indent=2)+'\n')
(OUT/'scope-matrix.json').write_text(json.dumps(srows,indent=2)+'\n')
(OUT/'evidence-catalogue.json').write_text(json.dumps(E,indent=2)+'\n')
# Readable matrix exact criterion + linked evidence catalogue. Detailed assessments in JSON.
def links(paths):return '<br>'.join(f'[{p}]({ROOT/p})' for p in paths)
lines=['# Evidence catalogue','', 'Every anchor identifies production source and existing bounded proof. This audit did not rerun those suites.','']
for k,v in E.items():
 lines += [f'## {k}: {v["label"]}','',v['boundary'],'','Source: '+links(v['source']),'','Evidence: '+links(v['evidence']),'']
(OUT/'EVIDENCE.md').write_text('\n'.join(lines)+'\n')
lines=['# Original 65 work packages: scope to implementation','', 'Original acceptance and prerequisite lists are preserved verbatim below. The JSON matrix adds the clause assessment and full resolved source/evidence paths. Evidence letters refer to EVIDENCE.md. Existing acceptance is reported, never changed by this audit.','', '| ID | Original acceptance | Original prerequisites | Observed status | Concrete source / evidence groups | Unaccepted prerequisites |','|---|---|---|---|---|---|']
for x in rows:lines.append('| '+' | '.join([x['id'],x['original_acceptance'],', '.join(x['original_dependencies']) or 'None',x['program_status_observed'],', '.join(f'[{k}: {E[k]["label"]}](EVIDENCE.md)' for k in x['evidence_keys']),', '.join(x['unaccepted_original_dependencies']) or 'None'])+' |')
lines += ['','Per-item implementation, verification and release-readiness fields: [work-item-matrix.json](work-item-matrix.json). Accepted bootstrap contributions are separate and do not count toward these65 original packages.']
(OUT/'WORK_ITEM_MATRIX.md').write_text('\n'.join(lines)+'\n')
lines=['# Original 44 scope requirements: scope to implementation','', 'Original requirement and required verification are preserved verbatim. JSON includes explicit implementation / remaining verification / release-readiness fields. No status changes are made.','', '| ID | Original requirement | Original verification | Observed status | Concrete source / evidence groups |','|---|---|---|---|---|']
for x in srows:lines.append('| '+' | '.join([x['id'],x['requirement'],x['verification'],x['delivery_status'],', '.join(f'[{k}: {E[k]["label"]}](EVIDENCE.md)' for k in x['evidence_keys'])])+' |')
lines += ['','Detailed findings and remaining verification: [scope-matrix.json](scope-matrix.json).']
(OUT/'SCOPE_MATRIX.md').write_text('\n'.join(lines)+'\n')
paths.update(['TIDEGLASS_DESIGN.md','V1_ROADMAP.md','V1_BACKLOG.md','v1_backlog.json','implementation/program.json','implementation/scope_requirements.json','release/qa/integration-local-remaining-20261021T131244958842Z/LOCAL_REMAINING_REVIEW.md','release/balance/long-horizon-v4-policies.json','release/balance/supplemental-v2.json','release/balance/optional-calibration-2026-10-21T105107709296Z/report.json'])
pins={p:sha(ROOT/p) for p in sorted(paths)}
(OUT/'inspected-file-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
m=json.loads((CAND/'manifest.json').read_text());dif=[]
for p,h in m['source_sha256'].items():
 check('frozen unchanged '+p,sha(CAND/'source'/p)==h)
 if sha(ROOT/p)!=h:dif.append({'path':p,'candidate_sha256':h,'live_sha256':sha(ROOT/p)})
for p in ['implementation/program.json','implementation/scope_requirements.json','v1_backlog.json']:check('authorityunchanged '+p,json.loads((ROOT/p).read_text())==original[p])
(OUT/'candidate-verification-end.json').write_text(json.dumps({'candidate_fingerprint':m['source_fingerprint'],'frozen_inputs':len(m['source_sha256']),'frozen_unchanged':True,'live_differences':dif,'note':'Only root/native-author repairs during audit, not audited candidate evidence. Review those separately before next freeze.'},indent=2)+'\n')
verification={'reviewer':'/root/qa_release','direction':'scope_to_implementation','source_candidate':m['source_fingerprint'],'checks':checks,'all_checks_passed':all(c['passed'] for c in checks),'original_packages':len(rows),'scope_requirements':len(srows),'original_accepted_observed':sum(x['program_status_observed']=='accepted' for x in rows),'scope_verified_observed':sum(x['delivery_status']=='verified' for x in srows),'inspected_files':len(pins),'source_pins_sha256':sha(OUT/'inspected-file-pins.json'),'candidate_live_differences':dif,'new_production_code_defects_found':[],'specific_local_qualification_gaps':['Actual native notification permission, scheduling, delivery and revocation','Current native fiveexports/58cells after known host repairs','Current final media editing/inspection and exact asset record reconciliation','Configured staging/full actual SDK privacy and provider qualification'], 'status_changed':False,'flutter_or_devices_run_during_scope_audit':False,'release_ready':False}
(OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps({k:v for k,v in verification.items() if k not in ['checks','candidate_live_differences']},indent=2));print('live_differences',dif)
