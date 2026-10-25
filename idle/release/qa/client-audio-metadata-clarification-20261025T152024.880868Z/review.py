from pathlib import Path
import json,hashlib,datetime,difflib,re,subprocess
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path('/tmp/client_audio_metadata_folder.txt').read_text().strip();O=Path(O)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'release/qa/lead-evidence-refresh-20261025T151918.259192Z'
a=json.loads((A/'adoption.json').read_text());assert sha(A/'adoption.json')=='a8e0abb98009971b6c59451898d43486329e456c55f8f5dd08524d22ea5f6e45'
before=json.loads((A/'program-before.json').read_text());after=json.loads((R/'implementation/program.json').read_text());scope=R/'implementation/scope_requirements.json'
assert sha(A/'program-before.json')==a['program_before_sha256'];assert sha(R/'implementation/program.json')==a['program_after_sha256'];assert sha(scope)==a['scope_unchanged_sha256'];assert sha(R/'release/store/README.md')==a['readme_after_sha256']
B={x['id']:x for x in before['items']};C={x['id']:x for x in after['items']};assert B.keys()==C.keys()
assert {k:v for k,v in before.items() if k!='items'}=={k:v for k,v in after.items() if k!='items'}
expected={'M3-08','M4-06','M4-07','M5-06'};changed={};added=[]
for id in B:
 if B[id]!=C[id]:
  fields={k for k in B[id].keys()|C[id].keys() if B[id].get(k)!=C[id].get(k)};assert fields=={'evidence','evidence_note'},(id,fields)
  assert C[id]['status']=='in_progress';assert set(B[id]['evidence'])<=set(C[id]['evidence'])
  changed[id]=sorted(fields);added.extend(x for x in C[id]['evidence'] if x not in B[id]['evidence'])
assert set(changed)==expected
backlog=json.loads((R/'v1_backlog.json').read_text())['items'];assert len(backlog)==65
for x in backlog:
 assert C[x['id']]['source_acceptance']==x['acceptance'];assert C[x['id']]['source_acceptance_dependencies']==x['dependencies']
S=json.loads(scope.read_text())['requirements'];assert len(S)==44
for p in added:assert (R/p).is_file(),p
for p,h in a['evidence_sha256'].items():assert sha(R/p)==h,p
for id,path in [('M4-07','release/qa/client-reverse-current-20261023T084431.965005Z/m4-07-note-proposal.json'),('M5-06','release/qa/client-android-media-20261025T150454.466933Z/m5-06-note-proposal.json')]:
 proposal=json.loads((R/path).read_text());assert C[id]['evidence_note']==proposal['proposed_evidence_note']
readme=R/'release/store/README.md';md=readme.read_text();local=[]
for name in re.findall(r'\]\(([^)]+)\)',md):
 if '://' not in name:
  target=(readme.parent/name.split('#')[0]).resolve();assert target.is_file(),target;local.append(str(target.relative_to(R)))
result=subprocess.run(['python3','implementation/tools/validate_program.py'],cwd=R,text=True,capture_output=True)
(O/'program-validator.log').write_text(result.stdout+result.stderr);assert result.returncode==0
(O/'program-diff.json').write_text(json.dumps({'changed_items':changed,'added_evidence':added,'all_added_evidence_exists':True,'all_original_65_clauses_dependencies_preserved':True,'scope44_unchanged':True,'readme_relative_links':local,'author_pins_rehashed':True},indent=2)+'\n')
(O/'readme.diff').write_text(''.join(difflib.unified_diff((A/'store-readme-before.md').read_text().splitlines(True),md.splitlines(True),fromfile='before',tofile='current')))
# Bounded audio source check, no audio/device/native execution.
measure=json.loads((R/'release/audio/render-measurements.json').read_text());score=json.loads((R/'source/audio/score/tideglass.score.json').read_text());audio=[]
for m in measure['members']:
 for key,h in [('source_path','source_sha256'),('runtime_path','runtime_sha256')]:assert sha(R/m[key])==m[h],m[key]
 mobile=R/'game/mobile/assets'/m['flutter_asset'];assert sha(mobile)==m['runtime_sha256']
 audio.append({'id':m['id'],'source_sha256':m['source_sha256'],'runtime_sha256':m['runtime_sha256'],'mobile_sha256':sha(mobile),'decoded_duration_seconds':m['decoded_aac_measurements']['duration_seconds'],'decoded_clipped_samples':m['decoded_aac_measurements']['clipped_samples']})
assert len(audio)==11 and len(score['tracks'])==3 and len(score['cue_scores'])==8
(O/'audio-source-bridge.json').write_text(json.dumps({'runtime_members':audio,'track_palette':[{k:t[k] for k in ['id','title','bpm','mode','texture']} for t in score['tracks']],'cue_ids':list(score['cue_scores']),'third_party_samples':False,'new_listening_or_native_execution':False},indent=2)+'\n')
report='''# Bounded M5-06 sound-direction clarification

**No missing local audio-authoring or mandated client-integration deliverable was identified.** The remaining local action can be an explicit director decision adopting the existing original score, current track/cue routing and gain/lifecycle policy as the v1 authored sound direction. That is an ordinary design decision within the user's authorized AI replacement studio. The original M5-06 clause and roadmap do not require a human-only creative-direction decision or a purchased external commission.

This is a narrow source/evidence review, not a new audition, native matrix or blanket asset approval. “Integrate final sound direction” should not remain a vague implementation blocker after the director adopts a concrete existing direction. Full M5-06 stays in progress for its unchanged M4-07 dependency and other outstanding original presentation conditions. Physical audible quality, interruptions and genuine supporter fulfillment remain their separate qualifications.

## Existing concrete direction

| Element | Actual authored/integrated policy |
|---|---|
| Music palette | Three original sixteen-bar loops: harbor at60BPM in D Dorian, current at72BPM in G major/suspended second, dawn at54BPM in F Lydian/D Dorian. Felt/pad/glass mathematical instruments, restrained harmonics and room reflections; no incorporated recordings/samples. |
| Music routing | Bootstrap chooses harbor before the campaign ending and dawn after it. Opening Season selects current; returning selects harbor/dawn from current ending state. This is the exact existing routing, not an assertion that completing the ending immediately switches tracks. |
| Feedback palette | Eight authored cues exist: purchase, panel, claim, calibration, survey, unlock, milestone and rechart. Controller routes accepted purchases/milestone bucket crossings, Rechart, Surveys, calibration, claims and story/panel actions. The authored unlock cue is available but has no current controller emission; no original requirement mandates a separate unlock cue. Do not describe every authored cue as a separately triggered gameplay event. |
| Mix/control policy | Defaults music0.32/SFX0.55, music driver applies0.5gain; effects share a0.9gain budget across at most8voices. Independent persistent music/SFX/mute plus master mute. This is a bounded gain policy, not a perceptual balance judgment. |
| Timing/lifecycle | Cues require accepted visible foreground actions, suppress events older than750ms and same-cue repeats within100ms, drop excess voices without queuing, and stop on background. Foreground return restores only the selected ambient track. No offline earnings cue replay. |
| Export/integration | Eleven original48kHz/24-bit masters, matching AAC runtime exports, and the same three masters in the soundtrack package. All eleven source/runtime/mobile hashes still match the existing measurement record. Existing three-target native session proofs and independently reproduced actual Settings controls support integration. |

The source/decoded measurements already record zero clipped samples, estimated peaks/loudness and bounded loop steps. Their estimates are not certified metering or evidence of perceived clipping/clicks. Historical package fields such as `native_decode_verified:false` and `authored_pending_independent_review` describe the old author packet; newer source-bound native/component reviews supersede those particular generic pending claims without rewriting the old evidence.

The original roadmap asks for a coherent ambient score, interaction feedback, milestone/Rechart cues and independent controls. Its staffing allowance for audio was a small-studio planning assumption superseded by the user's AI-team instruction, not a requirement to procure a human composer. The later audio handoff's “Human speaker/headphone audition” is a physical perceptual qualification record, not authority to block routine local creative selection. A director can adopt the source-defined palette without claiming to have heard an unperformed playback or changing that record to passed.

## Exact next action recommended to the lead

Record a source-pinned director decision adopting this existing score/palette and current route/cue/gain/lifecycle behavior for v1, referencing the original composition, renderer, current bus/controller/app/bootstrap and current native/Settings integration evidence. No new score, cue, package, source edit, external purchase or broad rerun is justified by a concrete defect in this narrow review. If the director elects to change a creative policy, review and test that actual delta; it is not needed merely to replace an unspecified pending label.

Keep actual listening on speakers/headphones, device volume/routing/call interruption behavior, audibility/mix assessment, real paid soundtrack hosting/restore and distribution/public-release terms explicitly unqualified. A local direction decision supplies none of these observations and does not accept all of S23 or M5-06. This clarification narrows the earlier reverse report's generic “final sound direction remains open” wording to the explicit director adoption plus these distinct qualification limits; it does not alter its sealed source or metadata cutoff.
'''
(O/'SOUND_DIRECTION_CLARIFICATION.md').write_text(report)
meta='''# Independent evidence-note adoption review and reverse-audit addendum

**Pass.** Inspected the actual before/current program and README diff for `release/qa/lead-evidence-refresh-20261025T151918.259192Z`. Exactly M3-08, M4-06, M4-07 and M5-06 changed, and only their `evidence` and `evidence_note` fields. Existing evidence was retained; every added evidence file exists. All four remain in progress. All original65 acceptance clauses/dependencies, owners/reviewers, program fields and all44 scope records remain unchanged. The fresh cheap program validator passes:43 production/support items remain unaccepted and25 scope requirements unverified.

M3-08/M4-06 notes match the assigned QA's bounded complete-data/copy and reachability judgments, preserving human-study, commerce and real-season prerequisites. M4-07/M5-06 wording exactly matches the named client's proposals: local integration/media readiness is recognized without full package, physical, provider or public acceptance. The previous stale M4-07/M5-06 descriptions are corrected.

README changes are confined to the current media date, Android status in the creative rows, replacement of the obsolete pending-capture sentence and a factual Android paragraph. It links the exact independently reviewed source-bound selection and review. The1080×1920 RGB8 full-pixel conversion,19-second0.5–19.5interval,570held-frame30fps encoding,44rawframes/28.5978778seconds,1.550Mbps bitrate, silent track and internal-only Season limits agree with the sealed Android result. Native chrome is retained. Relative Markdown links resolve. No store ingestion, actual physical performance, public schedule or uploaded asset is fabricated. External specification citations were not re-browsed in this note-only check.

This append-only review advances only the metadata cutoff of `client-final-reverse-20261025T150454.466933Z`. New program hash: `17e1b8b2efc34cd20322c517faf3574b8b929d4965e34c0715ba73c50f4a3470`; unchanged scope hash: `b215b2cb290721c92810f693142b363586a7266512000b5cbe20ddd7eafab598`; README hash: `09d1f98a1c51b19c090d23070962887548678d8ce1e080a3ed7fa8ad1152ba02`. The old sealed report, hashes and three stale-text findings remain historical; these findings are now resolved by the inspected adoption. Counts remain23 original accepted,19scope verified and release readiness false.

The adjacent sound-direction clarification is a separate narrow interpretation and source review. This metadata review does not silently mark final listening, native interruption, paid fulfillment or a director adoption as performed. No production, scope or program file was edited by this reviewer, and no Flutter/device or broad test was run.
'''
(O/'METADATA_REVIEW.md').write_text(meta)
inputs={}
for p in [*A.iterdir(),R/'implementation/program.json',scope,readme,R/'v1_backlog.json',R/'V1_ROADMAP.md',R/'TIDEGLASS_DESIGN.md',R/'implementation/art/production_contract.json',R/'release/audio/IMPLEMENTATION_HANDOFF.md',R/'release/audio/playback-report.json',R/'release/audio/capability-and-rights.json',R/'release/audio/render-measurements.json',R/'source/audio/score/tideglass.score.json',R/'source/audio/CREDITS.txt',R/'tools/audio/render_score.py',R/'game/mobile/lib/audio_bus.dart',R/'game/mobile/lib/audio_settings.dart',R/'game/mobile/lib/game_controller.dart',R/'game/mobile/lib/app.dart',R/'game/mobile/lib/bootstrap.dart',R/'release/qa/client-final-reverse-20261025T150454.466933Z/verification.json',R/'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07/CLIENT_JUDGMENT.md',R/'release/qa/scope-forward-final-20261023T085127.503162Z/CONTENT_READINESS.md']:
 if p.is_file():inputs[str(p.relative_to(R))]=sha(p)
for p in added:inputs[p]=sha(R/p)
(O/'input-pins.json').write_text(json.dumps(inputs,indent=2)+'\n')
for name in ['SOUND_DIRECTION_CLARIFICATION.md','METADATA_REVIEW.md']:print(name,sha(O/name))
print('FOLDER',O)
