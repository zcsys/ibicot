"""Read-only original65/44 forward audit. Generates QA-owned review artifacts only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent;P=R/'release/qa/scope-forward-20261023T033420.755364Z'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=json.loads((P/'original-contracts.json').read_text())
pg=json.loads((R/'implementation/program.json').read_text());by={x['id']:x for x in pg['items']}
sc=json.loads((R/'implementation/scope_requirements.json').read_text());sb={x['id']:x for x in sc['requirements']}
works=json.loads((P/'work-item-matrix.json').read_text());scopes=json.loads((P/'scope-matrix.json').read_text())
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
check('all65originalpackages',len(works)==65 and len({x['id'] for x in works})==65)
check('all44originalscopeclauses',len(scopes)==44 and len(sb)==44)
for row in works:
 x=by[row['id']]
 check(row['id']+' exact original criterion',row['original_acceptance']==x['source_acceptance'])
 check(row['id']+' exact original dependencies',row['original_dependencies']==x['source_acceptance_dependencies'])
 check(row['id']+' exact named reviewer',row['original_reviewer']==x['reviewer'])
 check(row['id']+' exact scope mapping',row['scope_ids']==x['scope_ids'])
for row in scopes:
 x=sb[row['id']]
 check(row['id']+' exact original criterion',row['requirement']==x['requirement'] and row['verification']==x['verification'])
 check(row['id']+' exact original work mapping',row['work_items']==x['work_items'])
oldpins=json.loads((P/'inspected-file-pins.json').read_text());newpins={f:h(R/f) for f in oldpins}
deltas={f:{'prior':v,'current':newpins[f]} for f,v in oldpins.items() if v!=newpins[f]}
production_drift=[f for f in deltas if f.startswith(('game/core/lib/','game/mobile/lib/','game/progression/lib/','game/events/lib/','game/platform/lib/','game/persistence/lib/','game/content/','game/mobile/assets/','services/tideglass_service/')) or f=='economy.json']
check('no production/runtime/content drift from earlier independent forward audit',not production_drift)
# These dispositions supersede stale pending-host/export/native statements, but
# do not change any canonical status or discharge an original prerequisite.
updates={
'M0-03':'Real native sandbox purchase/restore and ad availability remain unqualified without developer/provider accounts and configured products. Existing local revision tests and SDK inventory are retained.',
'M0-07':'AI role assignment and cost/access model are documented. Actual distribution/service accounts, recruitment and sustained operating coverage are unavailable; user supplied none. Do not call planned arrangements confirmed.',
'M2-04':'Local revision/fork/recovery implementation and HTTP fault proofs exist. Original M0-03 remains unaccepted; real two-device configured recovery is the separate S13 qualification. No newly identified local code gap.',
'M2-06':'At least15 genuine new testers and observed first-reset understanding/friction/pacing remain unavailable. Bot or fixture sessions cannot substitute.',
'M2-07':'Reference-hardware slice replay/report and the original upstream gates remain unfulfilled. Simulator/emulator passes are explicitly bounded.',
'M3-05':'Actual Settings/input/motion/audio controls and current source-bound presentation evidence are complete. All5 iPhone reminder scenarios are independently supported; Android default passed, while denied/quiet-cancel/delivery/revoked actual-UI scenarios are not yet sealed. Keep in_progress until across-target notification clause is demonstrated.',
'M3-06':'Local guest/account recovery, branch export/deletion and selection paths exist. Original M2-04 remains unaccepted and configured service/verified purchased-ownership lifecycle qualification remains external.',
'M3-07':'Local idempotent receipt/allowance/XP/save partitions and interrupted-grant tests exist. Preserve original M0-03/M3-06 prerequisite chain and real provider qualification; no blanket rewrite of working local ledger is called for.',
'M3-08':'Substantive current objectives/unlocks/reward/copy/completion and active/passive routes supported by CONTENT_READINESS.md. Exact original M2-06 human-study prerequisite remains unaccepted; no missing local authoring item identified.',
'M3-10':'Exact numerical/cadence/absence/queue/source bridges plus independently reproduced midnight/Rechart collision and current native clock/replay receipts cover bounded local timeline checks. M3-06/M3-07 original prerequisites remain unaccepted. Preserve synthetic/actual-clock distinctions; no redundant whole timeline rerun identified.',
'M4-01':'All12 actual dossier goals, earned100-Note entry, main-policy continuation and exit/restart/reopen isolation have source-bound proof. Original M3-08 prerequisite remains unaccepted; no missing local isolation implementation identified.',
'M4-02':'Production season boundaries/coefficient/pinning/isolation and accelerated actual-client archive transitions have existing proof. Original M4-01 remains unaccepted. Real28-day observation remains M6-07; do not silently add that duration to this implementation clause.',
'M4-03':'Actual catalog/pass/restore UI and once-only XP logic are implemented. Configured localized store products/verified restoration and original ledger/event dependencies remain; fixture prices are not actual commerce qualification.',
'M4-04':'Purchase state machine/provider adapters and local adversarial checks exist; genuine both-store validate/grant/acknowledge/restore/reconcile/refund/interruption qualification requires absent accounts/products/hosting.',
'M4-05':'Equal free briefing/ad allowance and duplicate/no-fill/refusal logic are locally covered. Actual configured SDK/provider refusal/no-fill/callback verification remains unqualified; preserve original dependencies.',
'M4-06':'Complete named runtime data/copy and existing actual read-through/actions supported by CONTENT_READINESS.md. Original M3-08/M4-01/M4-02 dependencies remain unaccepted; no missing local content item identified.',
'M4-07':'Named client judgment supports six restored harbor states,36 cosmetics and client-integrated audio using current3target native sessions plus real Settings controls. Only original M4-06 prerequisite remains. This is not paid soundtrack, physical listening or all164 per-asset approval.',
'M4-08':'Content reachability/reward/power-isolation and free-pass logic have source-bound local proof. Original commerce/content/art prerequisite chain remains open; verified paid delivery is not inferred from fixture ownership.',
'M5-01':'Progress-visible replay chunking exists. Named physical minimum devices, measured startup/resume/frame p95 and thermal/battery budgets remain unavailable; simulator timing is not substituted.',
'M5-02':'Current large-text/pseudo/non-color/reduced-motion and actual control matrices are supported. Original M3-05/M4-03/M4-06 dependencies and named-target accessibility/release qualification remain. No unchanged broad UI matrix repeat identified.',
'M5-03':'Current export SDK/manifest/privacy/font inventory and current actual lifecycle/privacy observations exist. Android socket/storage observation remains partial, default providers are disabled, and configured provider/export/deletion/outage behavior remains unqualified. No absence-of-network-traffic claim.',
'M5-04':'Real local staging receivers/load/fault/backups/alert tooling exists. Qualified hosted staging, actual alert/support recipients and original ledger/purchase prerequisites remain unavailable.',
'M5-05':'S33 exact30/90day simulation and1750Note budget already verified via bounded current-source bridge. Original M4-06/M5-04 dependencies plus deliberate beta configuration/metric freeze remain; do not rerun184 unchanged trajectories without a concrete gap.',
'M5-06':'Local actual phone/tablet media and current Android raw gallery/export candidates exist. Named final sound/presentation/media review and original M4-07 dependency remain; no new asset budget or blanket human art approval imposed.',
'M5-07':'Current3b00 passes28host gates and all5 exports; canonical58 native targets are50passes+8expected interruptions, with historical failures retained. Remaining actual network-disabled guest flow, uncompleted reminder target cells and named physical install/update/storage matrix remain; no current a052 failure is transferred to3b00.',
'M5-08':'Actual provider/store packet-loss/retry/refund/crash/outage transaction cases require unavailable environments. Existing synthetic/local fault tests remain labeled; original dependencies unchanged.',
'M6-01':'No genuine D30 cohort enrollment/acquisition/baseline/denominator exists. Recruitment and original M5-05/M5-07/M5-08 gates remain open.',
'M6-02':'No mature observed D1/D7/D30, satisfaction or ship/change outcome. Synthetic reports are tooling checks only.',
'M6-03':'Future observed cohort bugs cannot be pre-resolved. Existing fixes remain versioned; original M5-01/M6-01 gates remain.',
'M6-04':'No genuine observed new-player friction study. Original M5-02/M6-01 gates remain; implemented onboarding is separate.',
'M6-05':'No real opt-in tester operation/support/purchase-reconciliation drill. Original staging/cohort prerequisites remain.',
'M6-06':'Observed-play polish cycle is unavailable; current local presentation repairs do not fulfill the original M5-06/M6-01 chain.',
'M6-07':'Actual28-day pass and matureD30 observation absent. Accelerated season simulations and clock fixtures are preserved separately.',
'M6-08':'Combined qualified staging/paid continuation/migration/replay/repair rehearsal and original M4-08/M6-05 prerequisites remain. Existing local atomic/archive tests are not relabeled as that rehearsal.',
'M7-01':'All hard gates/product thresholds, accepted minor issues and final release-candidate freeze remain unfulfilled. Development3b00 capture is not a ship decision.',
'M7-02':'Final stabilization and release tagging/replay signoff depend on M6-03/M7-01. Current local regression gates pass; old a052 failure is preserved, not current.',
'M7-03':'Current unsigned iOS/AAB and debug builds are actual exports. Signing, store installation/update/products and final distribution qualification require unavailable accounts/devices; no store acceptance claim.',
'M7-04':'Qualified operational rehearsal of capacity/backups/entitlements/version-compatible repair and original M6-05/M7-01 remain. Local receiver/fault drills exist.',
'M7-05':'Actual local screenshots/footage/help/credits/assets exist and media source versions are pinned. Final shipped offers/working hosted links/reviewer/support arrangements and original M6-06/M7-01 prerequisites remain; local listing candidates are not published listings.',
'M7-06':'No release approval: external correctness/commerce/physical/human/observed gates and original M7-02/M7-03/M7-04 remain. Local5exports/current58 do not imply zero open release blockers.',
'M7-07':'Current policy check and locally valid asset formats exist. Final near-submission recheck, working products/reviewer access, submission and resolution of actual review findings remain unavailable.',
'M7-08':'Runbooks and roles/cost model exist. Named actual dated14-day coverage, launch authority and rollout-stop operation remain unconfirmed; actual14day operating results are separate OPS-14/S38.'}
refs={
'current_native':'release/native-proof/execution-3b00-20261023T040612.562001Z/sealed-complete58-20261023T085820.484246Z/checkpoint.json',
'current_exports':'release/qa/current-exports-20261023T043341.519824Z/REVIEW.md',
'content':'release/qa/scope-forward-final-20261023T085127.503162Z/CONTENT_READINESS.md',
'settings':'release/qa/settings-native-20261023T081631.942859Z/SETTINGS_HOST_REVIEW.md',
'phone':'release/qa/settings-native-final-20261025T151902.957394Z/phone-review-verification.json',
'art':'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07/CLIENT_JUDGMENT.md',
'offline':'release/qa/offline-network-style-20261025T151630.301516Z/verification.json'}
# Audit references must point at existing exact evidence, not guessed names.
for k,f in list(refs.items()):
 if not (R/f).is_file():
  if k=='current_exports':refs[k]='release/qa/current-exports-20261023T043341.519824Z/EXPORT_REVIEW.md'
  check('reference exists '+k,(R/refs[k]).is_file())
for row in works:
 x=by[row['id']];row['program_status_observed']=x['status'];row['evidence']=sorted(set(row['evidence']+x.get('evidence',[])))
 row['unaccepted_original_dependencies']=[d for d in row['original_dependencies'] if by[d]['status']!='accepted']
 row['canonical_evidence_note_observed']=x.get('evidence_note','')
 if x['status']=='accepted':row['required_verification_or_disposition']='Original narrow package is accepted in authoritative program. Retain its exact criterion, dependencies and named reviewer; no broader release claim.'
 else:row['required_verification_or_disposition']=updates[row['id']]
 row['release_readiness']='Not established. Original release gates and unavailable external resources remain separate.'
 if row['id'] in ['M3-08','M4-01','M4-06']:row['evidence'].append(refs['content'])
 if row['id']=='M4-07':row['evidence'].append(refs['art'])
 if row['id']=='M3-05':row['evidence']+= [refs['settings'],refs['phone']]
 if row['id'] in ['M0-08','M1-03','M5-03','M5-07','M7-02','M7-03','M7-05']:row['evidence']+=[refs['current_native'],refs['current_exports']]
 row['audit_status']='current-source assessment; pending final remaining Android/offline outcome update'
sc_updates={
'S01':'Actual native5exports and58target engineering proof exist; public signed launch/install/update remains unqualified without distribution resources.',
'S02':'Localization and guest implementation proofs exist. Actual network-disabled guest flow remains unexecuted; staged exact natural-start/purchase/save/new-process reload with local-only socket/OS-state proof awaits actual supported UI. Fresh cloud services are explicitly separate dependencies.',
'S08':'Existing exact event-history/cap/return-budget numeric bridge and actual current replay rows support the bounded criterion. Canonical scope still not_verified; no status change by this audit or extra physical/human gate implied.',
'S13':'Local conflict/recovery/verified-ownership merge discipline exists. Actual two-device configured fork/recovery drill remains unqualified; no adding divergent wallets.',
'S15':'All6 goals and ending rules are implemented and reachable; actual fixture-driven content read-through and current passive/active engine trajectories exist. Observed later-chapter player progression is not supplied by fixtures; original observed-play chain remains open.',
'S20':'Actual engine/client live/end/archive transitions, equal new/veteran fleet and no-power-export rules have accelerated proof. Preserve original actual lifecycle observation requirement and explicit M6-07 real28-day gate; do not relabel simulated time as calendar observation.',
'S21':'15000XP threshold, all40slots, once-only shared XP and selected archive continuation have local proof. Actual verified paid ownership/continuation and linked fulfillment rehearsal remain unqualified; synthetic ownership is not real store acquisition.',
'S23':'Actual original audio files, three current native playback rows and real volume/mute controls supported. Working purchased soundtrack fulfillment plus applicable distribution/rights qualification remain open.',
'S24':'No real both-store sandbox products/transactions; fake adapters and local provider fixtures do not close this explicit requirement.',
'S25':'Core/free-ad economic parity and full trajectories are supported. Actual configured ad no-fill/refusal/callback environment remains unqualified; free access must remain available.',
'S26':'Current host large-text/reduced-motion/non-color/input/help/audio controls and5iPhone notification cases supported. Android default is separate; four actual permission/quiet/delivery/revocation cases await sealed results. No new physical study prerequisite is imposed on this implementation criterion.',
'S27':'Local page/link/deletion implementation and host tests exist; deployed URLs/reviewer/support contacts and current actual product disclosures remain unqualified.',
'S28':'Current fault/replay/native save proof exists, original failures preserved. Zero critical/major release progression/access/purchase defects is not established while commerce/release gates remain open.',
'S30':'No actual10000-session denominator/device cohort. Crash tooling/synthetic sessions are not observations.',
'S31':'Chunked progress-visible owed-work preservation implemented. Required named physical p95/device-budget evidence absent.',
'S32':'No genuine15newtester study records. Automated paths do not substitute for users.',
'S34':'Preregistered protocol/tooling exist; no full actual D30/season cohort windows and real denominator/config/acquisition/exclusion records.',
'S35':'No evidence-backed mature product launch/extend/revise decision; correctness/fairness remain hard gates.',
'S36':'Local official policy/format checks exist. Near-submission requirements, accepted signed builds/products/reviewer access require absent external resources.',
'S37':'Local backup/compatible migration/feature-disable drills exist. Qualified staging/live operational rehearsal remains unfulfilled; never downgrade newer saves.',
'S38':'No dated completed14-day operating report. Coverage/runbooks/cost plans are not actual operation.',
'S39':'Exact current SDK/manifests/native lifecycle observations exist; Android network/storage observations are explicitly partial and providers disabled. Actual configured privacy/refusal/outage/deletion behavior remains unqualified; no absence-of-traffic claim.',
'S42':'Original65/44 meanings and source/evidence versions preserved in this forward audit; reverse audit separate. Whole release not ready and planning coverage cannot imply completion.',
'S43':'Current actual changed-screen/readability evidence and phone/tablet/Android raw media exist. Final local media review and shipped candidate/offer reconciliation remain separate; no store-approved claim.',
'S44':'Simulation branch is supported by current-source bridge. Actual observed play/pacing/no-pressure evidence remains absent; ending independence in source is not human experience.'}
for row in scopes:
 x=sb[row['id']];row['delivery_status']=x['delivery_status'];row['evidence']=x.get('evidence',[]);row['canonical_verification_note_observed']=x.get('verification_note','')
 row['required_verification_or_disposition']='Exact scope criterion already verified by authoritative current decision; original linked package dependencies/release gates are separate.' if x['delivery_status']=='verified' else sc_updates[row['id']]
 row['release_readiness']='Not established by narrow scope verification.'
 if row['id'] in ['S02','S26']:row['review_evidence'] += [refs['offline'],refs['settings'],refs['phone']]
 row['audit_status']='current-source assessment; pending final remaining Android/offline outcome update'
for name,value in [('work-item-matrix.json',works),('scope-matrix.json',scopes),('scope-intake.json',sc),('program-intake.json',pg),('source-bridge.json',{'original_audit':str(P.relative_to(R)),'prior_pins':oldpins,'current_pins':newpins,'deltas':deltas,'production_drift':production_drift})]:
 (O/name).write_text(json.dumps(value,indent=2)+'\n')
report={'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'original_packages':65,'scope_requirements':44,'accepted_original':sum(by[x['id']]['status']=='accepted' for x in works),'accepted_bootstrap':sum(x['status']=='accepted' and x.get('source')!='v1_backlog.json' and x['id'].startswith('BOOT') for x in pg['items']),'scope_verified':sum(x['delivery_status']=='verified' for x in sc['requirements']),'canonical_pins':{f:h(R/f) for f in ('implementation/program.json','implementation/scope_requirements.json','v1_backlog.json','V1_ROADMAP.md','TIDEGLASS_DESIGN.md')},'new_runtime_tests':0,'new_canonical_edits':[],'pending':'Remaining Android reminders and S02 actual network UI outcome, then exact final evidence seal','evidence_anchors':refs}
(O/'audit-progress.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('checks','evidence_anchors')}))
