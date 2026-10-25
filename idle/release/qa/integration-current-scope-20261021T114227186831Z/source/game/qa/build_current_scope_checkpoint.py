"""Create a dated semantic44/65 QA checkpoint without altering source acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,difflib,collections
from current_scope_judgments import ROWS,PACKAGES
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'release/qa'/('integration-current-scope-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();src=out/'source'
 req=json.loads((ROOT/'implementation/scope_requirements.json').read_text())['requirements'];back=json.loads((ROOT/'v1_backlog.json').read_text())['items'];program=json.loads((ROOT/'implementation/program.json').read_text()); pb={x['id']:x for x in program['items']}
 assert set(ROWS)=={x['id'] for x in req} and len(req)==44
 assert set(PACKAGES)=={x['id'] for x in back} and len(back)==65
 for x in back:
  assert pb[x['id']]['source_acceptance']==x['acceptance'],x['id']
  assert pb[x['id']]['source_acceptance_dependencies']==x['dependencies'],x['id']
 E={
 'numeric':'release/qa/integration-numeric-20261019T135534237861Z/NUMERIC_REVIEW.md',
 'crossengine':'release/qa/integration-crossengine-20261019T143516578781Z/CROSS_ENGINE_REVIEW.md',
 'integration':'release/qa/integration-final-20261016T105843545492Z/INTEGRATION_REVIEW.md',
 'm002':'release/qa/integration-initial-20261016T104939468348Z/M0-02_REVIEW.md',
 'balance':'release/qa/integration-balance-20261019T145921108068Z/BALANCE_REVIEW.md',
 'calibration':'release/qa/integration-optional-calibration-20261021T110210355242Z/OPTIONAL_CALIBRATION_REVIEW.md',
 'services':'release/qa/integration-services-repaired-20261016T114721906724Z/INTEGRATION_REVIEW.md',
 'fulfillment':'release/qa/integration-fulfillment-repaired-20261019T143906718168Z/FULFILLMENT_REPAIRED_REVIEW.md',
 'ownership':'release/qa/integration-native-ownership-repaired-20261019T145035575220Z/NATIVE_OWNERSHIP_REPAIRED_REVIEW.md',
 'reminders':'release/qa/integration-reminders-initial-20261016T115431767720Z/REMINDERS_REVIEW.md',
 'telemetry':'release/qa/integration-telemetry-repaired-20261019T141639166170Z/TELEMETRY_REVIEW.md',
 'study':'release/qa/integration-study-20261021T102508755253Z/STUDY_REVIEW.md',
 'collection':'release/qa/integration-study-collection-final-20261021T113037215270Z/COLLECTION_REPAIRED_REVIEW.md',
 'study_ui':'release/qa/integration-study-ui-final-20261021T114011830149Z/STUDY_UI_REVIEW.md',
 'ops':'release/qa/integration-operations-final-20261021T104534667043Z/OPERATIONS_REVIEW.md',
 'inventory':'release/qa/integration-inventory-20261021T104607526377Z/INVENTORY_REVIEW.md',
 'registration':'release/qa/integration-registration-20261021T111626112740Z/REGISTRATION_REVIEW.md',
 'entry':'release/qa/integration-entry-gates-20261021T113426797640Z/ENTRY_GATE_REVIEW.md',
 'cache':'release/qa/integration-cache-20261021T105558701110Z/CACHE_REVIEW.md',
 'help':'release/qa/integration-help-repaired-20261021T101942186162Z/HELP_REPAIRED_REVIEW.md',
 'producer':'release/art/producer-independent-review.md',
 'localization':'release/localization-author-review.md',
 'persistence':'release/persistence-review.md',
 'store':'release/store/CLIENT_REVIEW.md',
 'native':'release/native-proof/platform-handoff.md',
 'program':'implementation/program.json',
 'quality':'docs/quality/V1_QUALITY_PROTOCOL.md'}
 # New final UI result supersedes only previous draft statements about active failures.
 overrides={
 'S02':('Finish current complete pseudo/layout gate; final study UI13English/12pseudo passes a separate pin. Prove ordinary guest flow with all optional endpoints absent on the final candidate.'),
 'S26':('Complete all changed screens/critical actions at100/150/200%,phone/tablet,pseudo,non-color states,static motion and keyboard/semantics. Final study UI has a passing narrow pin,not native delivery proof.'),
 'S28':('Complete final composed-candidate regressions and open issue disposition. STUDY005 final UI host repair passes; a broad zero-major statement still needs exact candidate scope and current fault evidence.'),
 'S30':('Study UI durable-start/withdrawal/retry source and13English/12pseudo host cases now pass. Qualify actual native integration/crash linkage including pre-Dart gaps,collector capacity,registry handling and unknown outcomes; operational telemetry alone is not a crash-free denominator.'),
 'S39':('Study UI host/source boundary now passes. Native storage/network behavior and public policy pages from actual SDK inventory remain; permissions/backup and cross-app clipboard/export limits need current-candidate audit.')}
 rows=[]
 for q in req:
  c,proof,local,external,keys=ROWS[q['id']]
  if q['id'] in overrides:local=overrides[q['id']];keys=keys+['study_ui']
  rows.append({**q,'checkpoint_classification':c,'concrete_local_evidence':proof,'remaining_local_work_or_verification':local,'external_gate':external,'evidence_paths':[E[k] for k in keys],'new_delivery_status_proposed':None,'package_acceptance_unchanged':True})
 packages=[]
 for b in back:
  note=PACKAGES[b['id']]
  note=note.replace('Study UI still under regression;','Study UI now has a passing narrow host pin;').replace('changed-study integration regression still pending','final composed candidate qualification still pending')
  packages.append({'id':b['id'],'title':b['title'],'original_acceptance':b['acceptance'],'original_dependencies':b['dependencies'],'program_status':pb[b['id']]['status'],'scope_ids':[q['id'] for q in req if b['id'] in q['work_items']],'criterion_assessment':note,'accepted_by_this_audit':False})
 # Exact numeric evidence bridge: current core is the repaired independently reviewed core.
 numeric=json.loads((ROOT/'release/qa/integration-numeric-20261019T135534237861Z/snapshot.json').read_text());cross=json.loads((ROOT/'release/qa/integration-crossengine-20261019T143516578781Z/snapshot.json').read_text());bal=json.loads((ROOT/'release/qa/integration-balance-20261019T145921108068Z/snapshot.json').read_text())
 core={p:h for p,h in bal['files'].items() if p.startswith('game/core/lib/')};assert len(core)==8
 assert all(sha(ROOT/p)==h for p,h in core.items())
 assert core['game/core/lib/src/engine.dart']==cross['files']['game/core/lib/src/engine.dart']
 old=Path(numeric['workspace'])/'game/core/lib/src/engine.dart';new=ROOT/'game/core/lib/src/engine.dart';assert sha(old)==numeric['files']['game/core/lib/src/engine.dart']
 diff=''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='numeric99a5',tofile='currenta87e4'))
 (out/'numeric-bridge.patch').write_text(diff)
 math={'current_core_sha256':core,'all8_core_files_match_corrected_balance_review':True,'engine_matches_independent_crossengine_review':True,'old_numeric_engine_sha256':sha(old),'current_engine_sha256':sha(new),'bridge':'The old main-only62row/176test/12195assertion numeric evidence is retained only for base formulas. QA018 independently reproduces the old derived-engine failure and validates the exact current runtimeType guard with3170assertions/26traces. Corrected184case review uses current8corefiles. Original cache-era88/v2/v3/supplemental-v1 results remain invalidated.','bounded_verification_eligible_for_director_consideration':['S03 reference conformance and discrete-purchase boundaries','S29 core number policy/exact decision parity'],'partial_eligible_only':['S05 exact prestige/retention arithmetic; latest whole-client preview/candidate remains separately qualified','S07 mathematical synergy/marginal/forecast clauses; observed strategy remains separate'],'no_status_changes':True}
 (out/'NUMERIC_EVIDENCE_BRIDGE.json').write_text(json.dumps(math,indent=2)+'\n')
 sources=set(E.values())|set(core)|{'TIDEGLASS_DESIGN.md','V1_ROADMAP.md','economy.json','v1_backlog.json','implementation/scope_requirements.json','implementation/program.json','implementation/art/production_contract.json','implementation/content/launch_manifest.json','docs/quality/PLAYER_STUDY_PROTOCOL.md','release/art/style-qualification.json','release/art/import-qualification.json','release/audio/capability-and-rights.json','release/study/UI_AUTHOR_HANDOFF.md','release/study/ui-author-handoff.json','release/native-proof/root-study-final-20261021T113721.329611Z/verification.json','game/qa/current_scope_judgments.py','game/qa/build_current_scope_checkpoint.py'}
 for package in ['mobile','persistence','platform','progression','events']:
  sources.update(str(p.relative_to(ROOT)) for p in (ROOT/'game'/package/'lib').rglob('*.dart'))
 for p in ['game/mobile/pubspec.yaml','game/mobile/pubspec.lock','game/mobile/lib/content_compatibility.dart','game/mobile/test/qa_integration_study_start_test.dart','game/mobile/test/study_gate_test.dart','game/platform/test/study_recorder_test.dart','game/content/progression/campaign.json','services/tideglass_service/health.py','services/docs/OPERATIONS.md','tool/study_report.py','tool/study_adjudicate.py']:
  sources.add(p)
 # Reports remain exact bounded evidence, not automatic current-candidate certification.
 for key in E.values():
  parent=(ROOT/key).parent
  for n in ['verification.json','snapshot.json','scope-audit.json']:
   if (parent/n).is_file():sources.add(str((parent/n).relative_to(ROOT)))
 hashes={}
 for p in sorted(sources):
  target=src/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target);hashes[p]=sha(target)
 fp=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 counts=dict(collections.Counter(r['checkpoint_classification'] for r in rows))
 audit={'format':'semantic-scope-checkpoint-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/qa_integration','status':'dated_component_checkpoint_not_release_acceptance','source_fingerprint':fp,'input_count':len(hashes),'source_sha256':hashes,'classification_meaning':'Primary label identifies the dominant evidence condition; each row also gives actual proven local clauses,remaining local action and external conditions. Proven local component does not accept linked packages.','classification_counts':counts,'scope_count':44,'original_package_count':65,'scope_to_implementation':rows,'original_packages_to_criteria_and_scope':packages,'evidence_to_scope':[{'path':p,'scope_ids':[x['id'] for x in rows if p in x['evidence_paths']]} for p in sorted(E.values())],'original_acceptance_and_dependencies_unchanged':True,'original_accepted':[p['id'] for p in packages if p['program_status']=='accepted'],'bootstrap_accepted_separately':[x['id'] for x in program['items'] if x['id'].startswith('BOOT') and x['status']=='accepted'],'additional_calendar_item':'OPS-14 remains additional actual operating coverage,not a replacement for any65originalcriteria','unrequested_product_scope_found':[],'product_release_ready':False,'new_packages_accepted':[],'scope_status_mutations':[],'native_boundary':'Oldd85 handoff is historical. Candidate152 current matrix is still running. Final study/cache/optional-campaign changes have separate component proofs and require a new integrated candidate.','known_current_host_study_result':'FinalUIbc019a English13,pseudo12,analysisclean;STUDY005 originalfailure retained; doesnotinheritcandidate152nativeproof.','remaining_priority_local_work':['All-ID/state actual-widget variant/semantic/palette/animation verification with canonical perasset records','Public privacy/support page content and approved-data/SDK/offer linkage','Supported economic-version interval transition fixture/implementation forS14','Complete native collector/crash linkage and capacity/registry qualification before anyreal study','Final current candidate/fullhost/pseudo/native/upgrade/return/sourcepack','Actual final screenshots/short footage and exact enabled-offer alignment','Staging operational configuration,alert destinations/recovery/forward-repair rehearsal when resourceavailable'],'external_resources':'User confirms no developer accounts,physicaldevices,hosting or humanplaytesters. These do not excuse the listed local work.'}
 (out/'scope-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 lines=['# Current Tideglass scope checkpoint','',f"Independent dated component review: {audit['recorded_at_utc']}. **All44 explicit verification obligations and all65 original production acceptance criteria are assessed below. This is not a finished-v1 or release approval.**",'',f"The{len(hashes)} source/evidence inputs are frozen at `{fp}`. Every original criterion/dependency is byte-semantically unchanged. Four original foundation approvals remain separate from three BOOT preparation approvals. No statuses were edited.",'','Primary classification counts: '+', '.join(f'{k}: {v}' for k,v in counts.items())+'. Each row can also contain other clause types; labels are not all-or-nothing product grades.','',
'## Current conclusions','',
'Core mathematical obligations S03 and S29 have a current-source evidence bridge eligible for director consideration at their exact verification scope. All8core library files match corrected balance review; the99a5→a87e4 derived-engine cache repair has its own independent failure/repaired proof. See NUMERIC_EVIDENCE_BRIDGE.json and numeric-bridge.patch. Old cache-era scenario results remain invalidated. S05/S07 mathematical clauses are locally supported; their broader client/observed obligations remain separately stated. No linked package is accepted by this audit.',
'', 'The study core65-case review and final UI13English/12pseudo host run are now passing on their separate exact pins. STUDY005 startup-order failure and earlier failed attempts remain preserved. These changes are outside candidate152. The oldd85 native handoff is historical; current native execution is still in progress. Neither native report can qualify later source by implication.',
'', 'Meaningful local work remains: all-ID/state presentation checks and canonical asset evidence; local public privacy/support content; explicit old/new economic interval transition; native study/crash linkage and collection capacity qualification; final composed candidate/upgrade checks; accurate final screenshots/footage; and configured operational rehearsals. Missing accounts/devices/hosting/people are separate external gates, not a reason to rename these local gaps as external.',
'', '##44 explicit verification obligations','']
 for row in rows:
  lines += [f"### {row['id']} — {row['checkpoint_classification']}",'',f"**Original requirement:** {row['requirement']}",f"**Exact verification obligation:** {row['verification']}",'',f"**Proven local clauses:** {row['concrete_local_evidence']}",'',f"**Remaining local action/evidence:** {row['remaining_local_work_or_verification']}",'',f"**External condition:** {row['external_gate']}",'', '**Evidence:** '+', '.join(f'[{Path(p).name}]({ROOT/p})' for p in row['evidence_paths']), '','Original work items: '+', '.join(row['work_items'])+'.','']
 lines+=['##65 original production packages: reverse criterion audit','', 'Each criterion below is copied verbatim from v1_backlog.json; dependencies exactly match the execution program. Component progress is not substituted for upstream acceptance.','']
 for p in packages:
  lines += [f"### {p['id']} — {p['title']}",'',f"**Original acceptance:** {p['original_acceptance']}",'',f"**Dependencies:** {', '.join(p['original_dependencies']) or 'none'}. **Current program status:** {p['program_status']}. **Mapped scope:** {', '.join(p['scope_ids']) or 'original criterion retained; no substitute'}.",'',p['criterion_assessment'],'']
 lines+=['##Evidence-to-scope reverse mapping','','| Delivered/reviewed artifact | Original obligations served |','|---|---|']
 for e in audit['evidence_to_scope']:lines.append(f"| `{e['path']}` | {', '.join(e['scope_ids'])} |")
 lines+=['','No added producer/prestige layer,multiplayer,power sale or public desktop/web substitution was identified. QA tools,synthetic fixtures,internalmacOS and optional study preparation support original requirements; they are not extra shipped content. OPS-14 preserves actual calendar coverage. None of this checkpoint fabricates store acceptance,physical targets,participants,realD30/season or14operatingdays.','']
 (out/'CURRENT_SCOPE_CHECKPOINT.md').write_text('\n'.join(lines))
 drift=[p for p,h in hashes.items() if sha(ROOT/p)!=h];(out/'closure.json').write_text(json.dumps({'source_fingerprint':fp,'live_drift_at_closure':drift,'scope_rows':len(rows),'criteria_rows':len(packages),'all_original_dependencies_and_acceptance_preserved':True,'release_ready':False},indent=2)+'\n')
 idx={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};(out/'evidence-index.json').write_text(json.dumps(idx,indent=2)+'\n')
 (ROOT/'game/qa/current_scope_checkpoint.json').write_text(json.dumps({'evidence':str(out)},indent=2)+'\n')
 print(out);print(fp,len(hashes),counts,drift)
if __name__=='__main__':main()
