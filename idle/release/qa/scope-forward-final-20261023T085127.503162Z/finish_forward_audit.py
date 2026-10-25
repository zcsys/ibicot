"""Seal the read-only scope-to-implementation audit at the explicitly fixed cutoff."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, collections
R=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
C=R/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
P=R/'release/qa/scope-forward-20261023T033420.755364Z'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def write(n,v): (O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def link(path,label=None,line=None):
 p=R/path
 return f'[{label or p.name}]({p}{":"+str(line) if line else ""})'
pg=load(R/'implementation/program.json');sc=load(R/'implementation/scope_requirements.json')
progress=load(O/'audit-progress.json');works=load(O/'work-item-matrix.json');scopes=load(O/'scope-matrix.json')
assert sha(R/'implementation/program.json')=='d259ba03e1e14727ed6dd557f6bb289b35b091e2ea1acf780c903f2346eef876'
assert sha(R/'implementation/scope_requirements.json')=='b215b2cb290721c92810f693142b363586a7266512000b5cbe20ddd7eafab598'
original=load(P/'original-contracts.json');ob={x['id']:x for x in original['v1_backlog.json']['items']}
by={x['id']:x for x in pg['items']};sb={x['id']:x for x in sc['requirements']}
checks=[]
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
for row in works:
 id=row['id'];x=by[id]
 check(id+' original backlog acceptance and dependency meaning',row['original_acceptance']==ob[id]['acceptance']==x['source_acceptance'] and row['original_dependencies']==ob[id]['dependencies']==x['source_acceptance_dependencies'])
for x in original['implementation/scope_requirements.json']['requirements']:
 check(x['id']+' unchanged original requirement, source, verification and work mapping',all(x[k]==sb[x['id']][k] for k in ['id','requirement','source','verification','work_items']))
check('69 authoritative tracking items',len(pg['items'])==69)
check('23 original packages and three bootstrap artifacts accepted',sum(by[id]['status']=='accepted' for id in ob)==23 and sum(x['status']=='accepted' and x['id'].startswith('BOOT') for x in pg['items'])==3)
check('19 verified and 25 unverified scopes',collections.Counter(x['delivery_status'] for x in sc['requirements'])=={'verified':19,'not_verified':25})
check('43 original/support items unaccepted including OPS-14',sum(x['status']!='accepted' for x in pg['items'] if x['id'] in ob or x['id']=='OPS-14')==43)
check('no whole-product release claim',pg['product_release_ready'] is False)
manifest=load(C/'manifest.json');frozen=manifest['source_sha256']
sys.path.insert(0,str(R/'tool'));import verify_native
prod=verify_native.production_inputs(frozen)
check('frozen candidate has all 1190 exact source files',len(frozen)==1190 and all(sha(C/'source'/f)==v for f,v in frozen.items()))
check('all 482 production inputs match live and candidate workspace',len(prod)==482 and all(sha(R/f)==frozen[f] and sha(C/'workspace'/f)==frozen[f] for f in prod))
write('candidate-production-identity.json',{'candidate_fingerprint':manifest['source_fingerprint'],'manifest_sha256':sha(C/'manifest.json'),'frozen_file_count':len(frozen),'production_input_count':len(prod),'production_pins':{f:frozen[f] for f in sorted(prod)},'frozen_source_rehashed':True,'live_and_workspace_match':True,'new_builds_or_runtime_tests':0})
# A file hash is identity/provenance, not an assertion that every referenced old run passed.
refs=set(progress['canonical_pins'])|set(progress['evidence_anchors'].values())
for row in works+scopes:
 for key in ['source','evidence','review_evidence']:refs.update(row.get(key,[]))
refs.update([
'release/qa/client-audio-adoption-20261025T152944.392520Z/verification.json',
'release/qa/client-android-media-20261025T150454.466933Z/verification.json',
'release/qa/client-final-reverse-20261025T150454.466933Z/verification.json',
'release/qa/settings-native-final-20261025T151902.957394Z/READINESS_REVIEW.md',
'release/qa/settings-native-final-20261025T151902.957394Z/seal.json',
'release/qa/lead-settings-reproduction-20261023T084118.092567Z/verification.json',
'release/qa/lead-offline-review-20261025T151332.191712Z/REVIEW.md',
'release/native-notifications/integration-android-20261025T151708326800Z/verification.json',
'release/native-notifications/integration-android-20261025T152403718372Z/verification.json',
'docs/audio-direction-v1.md',
'release/audio/director-direction-20261025T152221.111400Z/decision.json'])
missing=[f for f in refs if not (R/f).exists()]
check('all cited sources and evidence exist',not missing)
filepins={f:sha(R/f) for f in sorted(refs) if (R/f).is_file()}
write('final-input-pins.json',filepins)
write('metadata-transition.json',{'prior_provisional_pins':load(O/'provisional-before-final/audit-progress.json')['canonical_pins'],'current_pins':progress['canonical_pins'],'authorized_note_only_delta':'M5-06 evidence/evidence_note adds explicit reviewed audio direction. Original clauses, dependencies, reviewers, counts and scope unchanged.','independent_review':'release/qa/client-audio-adoption-20261025T152944.392520Z/REVIEW.md','prior_provisional_files_preserved':'provisional-before-final/','sealed_content_settings_and_staging_packets':'unchanged; their earlier intake metadata remains historical'})
def line_map(n):
 out={}
 for i,l in enumerate((O/n).read_text().splitlines(),1):
  if l.strip().startswith('"id":'):out[json.loads(l.strip().rstrip(',')).split(':',1)[-1] if False else json.loads(l.split(':',1)[1].strip().rstrip(','))]=i
 return out
wm=line_map('work-item-matrix.json');sm=line_map('scope-matrix.json')
esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
w=['# Original 65-package forward audit','',
'This is the sealed d259ba03 program / b215b2cb scope cutoff. Every original criterion, dependency, named reviewer and scope mapping is preserved. Click an ID for its full source/evidence list and exact observed metadata. Acceptance status is authoritative metadata, not a new decision by this review. The whole release remains unready.','',
'| Package / named reviewer | Status / unmet original dependencies | Exact original acceptance | Current implementation | Required verification or disposition |',
'|---|---|---|---|---|']
for x in works:
 cells=[link(str((O/'work-item-matrix.json').relative_to(R)),x['id'],wm[x['id']])+' — '+x['title']+'; reviewer: '+x['original_reviewer'],x['program_status_observed']+'; '+(', '.join(x['unaccepted_original_dependencies']) or 'no unmet original dependency'),x['original_acceptance'],x['implementation_assessment'],x['required_verification_or_disposition']]
 w.append('| '+' | '.join(esc(c) for c in cells)+' |')
w+=['','OPS-14 is separate original-roadmap support tracking, not a 66th backlog package: actual 14-day coverage, incident evidence, handoff and Season 2 brief remain unfulfilled. Three additional program items are accepted bootstrap artifacts.']
(O/'WORK_ITEM_MATRIX.md').write_text('\n'.join(w)+'\n')
s=['# Original 44-requirement forward audit','',
'This is the sealed d259ba03 program / b215b2cb scope cutoff. Both the original requirement and its original verification clause are reproduced verbatim. Click an ID for original mappings and full source/evidence lists. Narrow verification does not establish whole-release readiness.','',
'| Scope / authoritative status | Exact requirement | Exact verification | Current implementation | Required verification or disposition |','|---|---|---|---|---|']
for x in scopes:
 cells=[link(str((O/'scope-matrix.json').relative_to(R)),x['id'],sm[x['id']])+' — '+x['delivery_status'],x['requirement'],x['verification'],x['implementation_assessment'],x['required_verification_or_disposition']]
 s.append('| '+' | '.join(esc(c) for c in cells)+' |')
(O/'SCOPE_MATRIX.md').write_text('\n'.join(s)+'\n')
readme='''# Final forward scope audit

**The current local implementation is extensively evidenced, but Tideglass v1 is not finished or release-ready.** This audit reconciles every original backlog package and scope requirement against actual source and source-bound evidence. It identifies no additional concrete local gameplay, content, art, audio, control or selected-media repair. Two bounded execution obligations remain available locally when actual Android UI can be coordinated: the four remaining notification scenarios and the staged network-disabled guest flow. The original external and time-dependent release obligations also remain unmet.

## Exact cutoff and unchanged contract

The cutoff is program `d259ba03e1e14727ed6dd557f6bb289b35b091e2ea1acf780c903f2346eef876` and scope `b215b2cb290721c92810f693142b363586a7266512000b5cbe20ddd7eafab598`. The original design, roadmap, 65 backlog acceptance clauses, dependencies, named reviewers and 44 scope criteria/mappings are preserved. This review changes no canonical file or status.

| Tracking set | Supported status at cutoff |
|---|---|
| Original 65 packages | 23 accepted, 24 in progress, 18 not started |
| Three bootstrap artifacts | All three accepted; excluded from the original 65 |
| Original-roadmap OPS-14 support | Not started; zero actual launch-support days |
| All production/support work | 43 unaccepted items, including OPS-14 |
| Original 44 scope requirements | 19 verified, 25 unverified |
| Product release | `product_release_ready: false` |

`WORK_ITEM_MATRIX.md` separates implementation from original prerequisites and required verification for all 65 packages. `SCOPE_MATRIX.md` reproduces all 44 requirements and their exact verification clauses. Each linked JSON row records actual source and evidence paths. Original metadata prose remains verbatim inside those JSON records; the human-facing assessments use readable prose.

## Current source and evidence basis

The frozen candidate is `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`. This final seal rehashes all 1,190 frozen source files and all 482 corresponding live and candidate-workspace production inputs. They match. The earlier independent forward audit's 160-file source review is bridged explicitly, with no production/runtime/content drift. Test and observation harness repairs, metadata decisions and media selections have separately versioned review packets; they are not silently treated as unchanged old evidence.

Current engineering proof comprises 28 successful host build gates, five actual native exports and the canonical 58-target native packet: 50 passes and eight expected interrupted preparations. The full 71-attempt packet retains 55 passes, eight expected interruptions and eight failures. Expected interruptions are not successful completion claims. The prior a052 build failures, old reminder failures, Android observer limitations and failed gallery attempts are retained. The successful current exports and native rows do not establish store acceptance, physical-device performance, configured commerce or human retention.

The full content/readability matrices, current source bridges, actual daily and purchase controls, bounded Rechart forecast, exact numerical/prestige fixtures, midnight collision proof, and 184 historical plus fifteen current simulation trajectories remain evidence for their specific clauses. No unchanged full matrix, native suite, export inspection or 184-trajectory suite was repeated for this seal. New work here is read-only contract, source-identity and evidence-pin verification.

## Finite local execution remainder

| Remaining action | Exact scope and present evidence | What is not yet proven |
|---|---|---|
| Four Android reminder scenarios | M3-05/S26: actual Settings and target-input controls, all five iPhone scenarios and Android default opt-out are independently supported. | Android actual denial, quiet-hour cancellation, real scheduled delivery and revocation. Two real prompt attempts timed out without a decision; both failed reports remain. User assistance is authorized, but no current timer or future outcome is assumed. |
| Actual network-disabled guest flow | S02 and the network portion of M5-07: staged reuse of natural guest start, 35 real seconds, actual purchase/save and a separate-process reload. Exact staged harness `90dbf5a3…` has independent source review, 27 pure protocol checks and clean scoped analysis. | Actual Android network disable/restore, app-path failure while the local listener remains healthy, absent default route, gameplay/save continuity and restored reachability. No native run or socket execution has occurred. |

The S02 stage admits only the owned Android emulator and exact candidate/harness/run/predecessor identities. It uses an app-to-host local challenge, independent listener health and read-only OS connectivity snapshots; no external destination or automatic radio toggle is used. A visible airplane icon alone cannot qualify the result. If the emulator retains a usable virtual path, the qualification must fail closed. The staged protocol does not establish isolated iOS disconnection, and the Mac host network must not be disabled to manufacture such evidence.

Once actual outcomes exist, append a narrow independently reviewed addendum. Do not repeat already-closed Settings, content, numerical, export or native matrices. S08 retains its earlier supported bounded recommendation, while authoritative scope status remains unverified; this audit does not self-adopt it. S42 now has concrete forward and separately authored reverse artifacts, but remains unverified until the designated lead reconciles the complete original release obligation.

## Content, art and media conclusions

M3-08's six chapters and twelve dossiers have complete goals, unlocks, rewards, budgets, copy and active/passive routes. M4-06 has complete six-chapter/ending, twelve-dossier, twelve-pattern, eighteen-archive and Season 1 data and copy, with actual read-through/control evidence. The sealed `CONTENT_READINESS.md` records 148 source checks and 77 pins. No missing local authoring item was identified. M3-08 still depends on original M2-06; M4-06 still depends on M3-08, M4-01 and M4-02. Those dependencies have not been waived.

The named client M4-07 judgment supports six restored harbor states, the fixed 36 cosmetics and client-integrated original audio using current three-target native playback evidence and independently reproduced Settings controls. M4-06 remains its original unmet prerequisite.

M5-06 now has an explicit independently reviewed director audio choice and selected actual phone, tablet and Android stills/footage. No specific residual placeholder, required cue, score, control or selected export defect was identified in the inspected components. The authored unlock cue is deliberately not emitted automatically; the reviewed direction explicitly records that choice. The original M4-07 dependency remains. These findings do not grant blanket approval to all 164 asset records, qualify physical listening/mix behavior, prove paid soundtrack fulfillment or establish store distribution approval. None of those limits is an invented missing local asset or human-only creative gate.

The selected three-platform clips are actual local capture derivatives, silent, with disclosed bitrate/source-motion limits. Android's 44 raw frames over 28.5978778 seconds do not become additional captured motion through encoding. Seasonal stills remain internal development previews. S43's eventual shipped-candidate/offer/release reconciliation remains open; local media approval is not publication.

## Original external and dependent obligations

| Resource or observation needed | Original obligations that remain |
|---|---|
| Apple/Google developer and provider accounts, products and a qualified host | Real sandbox purchase/restore/refund/ad callbacks; verified ownership and soundtrack fulfillment; configured cloud recovery, disclosure/deletion/outage drills; signed public install/update/submission and working public links. Local adapters and synthetic provider receipts do not satisfy these. |
| Named physical reference devices | Original measured startup/resume/frame p95, thermal/battery and physical device-matrix qualifications. Simulator clocks and host control tests retain their narrower meaning. |
| Genuine new testers and cohorts | At least fifteen new-player first-reset observations; measured comprehension/friction; real session/crash denominator; mature D1/D7/D30 and player welfare/pacing evidence. No bot, fixture or simulation participant is invented. |
| Real elapsed operations and assigned operators | Actual 28-day season/D30 observation, qualified load/support/reconciliation rehearsal and dated 14-day launch coverage and incident evidence. Runbooks and accelerated time are preparations. |
| Upstream gate completion and deliberate final decisions | Beta configuration/metric freeze, final release-candidate stabilization, near-submission policy checks, shipped-offer reconciliation and release approval follow their original prerequisites. These are not hidden current code defects or new scope. |

The user reported none of the external accounts, physical devices, hosting or human playtest resources. Later manual Android UI assistance changes only the local execution opportunity. Android privacy observations remain explicitly partial because actual-app socket calls timed out and storage observation was unavailable. Included SDKs and disabled/default-off providers are distinct facts; no absence-of-traffic claim follows.

## Independence, preservation and decision

This reviewer previously authored focused QA probes and a reminder ID protocol repair. The corresponding root reproductions and different-author repair approvals are linked; this audit does not self-approve those contributions. Named client reviews cover current art/media decisions. The separately authored reverse audit maps implementation back to original scope, and its later metadata/audio clarification is pinned at this same d259/b215 cutoff.

Prior provisional audit files are preserved under `provisional-before-final/`. Earlier sealed content, Settings, native and staging packets remain unchanged. Their historical source hashes are not rewritten after authorized note-only metadata adoptions. The QA report generator's initial missing-bracket construction error was corrected before final generation and is recorded; no production or runtime result changed.

**Recommendation:** retain all current canonical statuses and original dependencies. Use these matrices as the final forward audit at this cutoff, with append-only additions for subsequent Android outcomes or explicitly reviewed decisions. The local implementation is not a finished-v1 release, and no additional concrete local feature repair is recommended by this review.
'''
(O/'FORWARD_SCOPE_REVIEW.md').write_text(readme)
# Read-only table checks: every original ID appears exactly once in its table.
check('65 readable package table rows',sum(l.startswith('| [M') for l in w)==65)
check('44 readable scope table rows',sum(l.startswith('| [S') for l in s)==44)
check('all 109 readable assessments used exactly',all(x['implementation_assessment']==load(O/'readable-assessments.json')[x['id']] for x in works+scopes))
check('all source/evidence pins unchanged through sealing',all(sha(R/f)==v for f,v in filepins.items()))
verification={'utc':datetime.now(timezone.utc).isoformat(),'result':'sealed_forward_audit_not_release_acceptance','contract_generator_checks':len(progress['checks']),'all_contract_generator_checks_passed':all(c['passed'] for c in progress['checks']),'final_checks':checks,'final_check_count':len(checks),'source_evidence_file_pin_count':len(filepins),'directory_references':['services/'],'original_packages':65,'scope_requirements':44,'program_items':69,'accepted_original':23,'accepted_bootstrap':3,'unaccepted_original_and_support':43,'scope_verified':19,'scope_unverified':25,'candidate_fingerprint':manifest['source_fingerprint'],'frozen_files_rehashed':1190,'production_inputs_rehashed_live_and_workspace':482,'current_program_sha256':sha(R/'implementation/program.json'),'current_scope_sha256':sha(R/'implementation/scope_requirements.json'),'product_release_ready':False,'production_or_status_edits':[],'new_runtime_tests_or_network_device_actions':0,'later_outcomes':'append-only independently reviewed addenda'}
write('final-verification.json',verification)
files={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='final-seal.json' and '__pycache__' not in p.parts}
write('final-seal.json',{'utc':datetime.now(timezone.utc).isoformat(),'packet':str(O.relative_to(R)),'program_sha256':sha(R/'implementation/program.json'),'scope_sha256':sha(R/'implementation/scope_requirements.json'),'product_release_ready':False,'files':files})
print(json.dumps({'verification_sha256':sha(O/'final-verification.json'),'seal_sha256':sha(O/'final-seal.json'),'report_sha256':sha(O/'FORWARD_SCOPE_REVIEW.md'),'work_matrix_sha256':sha(O/'WORK_ITEM_MATRIX.md'),'scope_matrix_sha256':sha(O/'SCOPE_MATRIX.md'),'final_checks':len(checks),'evidence_files':len(filepins),'generator_checks':len(progress['checks'])},indent=2))
