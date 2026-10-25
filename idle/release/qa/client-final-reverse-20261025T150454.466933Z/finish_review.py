from pathlib import Path
import json,hashlib,datetime
R=Path('/Users/csys/Desktop/ibicot/idle');O=R/'release/qa/client-final-reverse-20261025T150454.466933Z'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda n:json.loads((O/n).read_text())
rows=load('reverse-crosswalk.json');deltas=load('delta-crosswalk.json');c=load('contract-check.json');identity=load('source-identity.json')
# Current original contract stays separate from the delivery observations.
for name,h in c['metadata_pins'].items(): assert sha(R/name)==h,(name,'metadata changed; refresh needed')
for row in rows:
 for e in row['evidence']:assert sha(R/e['path'])==e['sha256'],e['path']
for d in deltas:
 for name,h in d['input_sha256'].items():assert sha(R/name)==h,name
extra=[
'release/qa/client-android-media-20261025T150454.466933Z/REVIEW.md',
'release/qa/client-android-media-20261025T150454.466933Z/verification.json',
'release/qa/client-android-media-20261025T150454.466933Z/m5-06-note-proposal.json',
'release/qa/client-clean-phone-media-20261023T050152.295344Z/REVIEW.md',
'release/qa/client-current-media-20261023T080835.670842Z/tablet/REVIEW.md',
'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07/CLIENT_JUDGMENT.md',
'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07/verification.json',
'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07-note-proposal.json',
'release/qa/client-reverse-scope-20261023T033233.346454Z/REVERSE_SCOPE_REVIEW.md',
'release/qa/client-reverse-current-20261023T084431.965005Z/PAUSED_CHECKPOINT.md',
'release/qa/lead-reminder-callback-review-20261023T084219.566480Z/verification.json',
'implementation/tools/validate_program.py']
(O/'additional-evidence-pins.json').write_text(json.dumps({p:sha(R/p) for p in extra},indent=2)+'\n')
notes={
'finding_class':'stale evidence text only; no implementation or economic scope change recommended',
'proposals':[
{'id':'M4-07','problem':'Current note still calls M1-07 named client review and M3-09 daily icons pending; both packages are accepted.','proposal':'Use existing named client judgment, preserve in_progress and unaccepted M4-06 prerequisite.','source':'release/qa/client-reverse-current-20261023T084431.965005Z/m4-07-note-proposal.json'},
{'id':'M5-06','problem':'Current note still says only historical candidate152 raw media exists and current edited inspected exports are open. Current3b00 phone, corrected tablet and Android local selections are independently reviewed.','proposal':'Add bounded local output evidence and exact limitations; preserve in_progress, M4-07 dependency, and S23/S43 criteria.','source':'release/qa/client-android-media-20261025T150454.466933Z/m5-06-note-proposal.json'},
{'id':'store README','problem':'Creative table and final paragraph still say Android capture validation is in progress.','proposal':'Link current Android packet and independent review with three listing still candidates, internal Season,19s clip, raw44/28.5978778 low cadence, silent source/output, actual1.5504Mbps; no store acceptance.'}],
'allowed_program_fields':['evidence','evidence_note'],'status_dependency_criterion_changes_recommended':False,'metadata_modified_by_reviewer':False}
(O/'note-only-findings.json').write_text(json.dumps(notes,indent=2)+'\n')
lines=['# Final bounded implementation → original-scope audit',
'','**No unscoped game feature, changed economic rule, invented provider deployment or unsupported empirical completion was found in the inspected delivery.** The remaining corrective findings are stale evidence descriptions in M4-07, M5-06 and the store README. This audit is complete for the exact source and metadata cutoff below; it does not declare Tideglass v1 finished or accept any outstanding original work package.',
'','## Identity, method and original contract','',
'Candidate: `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`, under `.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122`. Rehashed all **1,190 frozen source files**, **482 corresponding live and candidate-workspace production inputs**, and all **29 runtime content payload hashes and byte counts**. They match. These are source identity counts, not delivered APK entries, test cases or human observations.',
'','The earlier independent reverse audit inspected the actual production systems; this resumed audit rehashes each cited source, preserves the old evidence, and explicitly inspects/maps changed ancillary tests, configuration notes and media tools. Ten frozen-source differences from a052 and eight later live harness/tool differences are listed in `source-identity.json`; none changes the current 3b00 production gameplay. The11 delta groups below account for the additional delivery. Source and current evidence hashes are in the machine-readable crosswalks; no result is silently inherited across a changed hash.',
'','The25 delivered groups cover all44 original scope requirements. Their original scope links collectively cover all65 original backlog packages. All65 original acceptance clauses/dependency arrays and all44 requirement/source/link/verification fields are preserved. There are69 program rows:65 originals,3 bootstrap artifacts and OPS-14, which explicitly tracks the original roadmap14-day support duty. The cheap program validator passes; it is a metadata consistency check, not release qualification.',
'',f"At the exact cutoff, **23 original packages are accepted,24 in progress and18 not started;19 scope records are verified and25 unverified**. Including OPS-14,43 production/support items remain unaccepted. `product_release_ready` is false. Program hash `{c['metadata_pins']['implementation/program.json']}`; scope hash `{c['metadata_pins']['implementation/scope_requirements.json']}`. `authority/` preserves the documents read at resume. Later lead note adoption is a separate append-only check; these counts are not silently updated.",
'','## Actual content and economy boundary','',
'| Inspected delivered element | Actual boundary |',
'|---|---|',
'| Main producers | Exactly5; base price30×20^tier, output20^tier, inflation28/25=1.12, preceding10 unlocks |',
'| Milestones and prestige |25/50/75/100 doubling; one Rechart, floor(10(L/10^9)^0.65) less awarded Charts;1+sqrt(P/10) power |',
'| Network |25-Chart gate; log2(1+n/25), Skiff→Loom.20/Observatory.10, Nursery→Loom.10/Observatory.25 |',
'| Automation | Free base plan at10 Charts, up to five50-Note plans, optional conditional reset at100 Charts |',
'| Offline and daily |24h full+48h quarter; Focus2h/cap12, Survey8h/cap3, three daily contracts with7-day backlog |',
'| Support | Shared six free/rewarded-ad slots,300 production seconds each; no paid allowance or whole-return doubling |',
'| Content |6chapters+ending,18archive entries,12dossiers,12calibrations,7harbor presentations,25producer presentations,164 registered assets |',
'| Season and rewards | One isolated28-day fleet; no imported main power, paid effects, Rechart or economic exports.40reward rows:20free fragments,10free cosmetics,10premium cosmetics |',
'| Cosmetics and paid catalog |36identities:12core/10free/10premium/4shop. Six nonconsumable products; supporter reuses four shop cosmetics and soundtrack |',
'','`actual-content-counts.json` records actual configuration/content tables. No added spendable premium currency, sixth producer, second prestige, paid automation/economic multiplier, loot box, public desktop release, multiplayer/guild/trade/leaderboard or shipped second season was found in the inspected schemas, product allowlist and controller paths. Precision integers, cosmetic identities and isolated scenario balances do not create new economy currencies. No claim that the prestige forecast proves a mathematical optimum is made: it remains a bounded24-hour counterfactual under an explicit purchase policy.',
'','## Delivered groups traced back to the original scope','',
'Every row in `reverse-crosswalk.json` contains exact source paths/hashes and linked original work items. A mapping means the behavior has an original purpose; it does not waive verification or accept the mapped requirement.','',
'| ID / delivered group | Original scope | Inspected boundary |','|---|---|---|']
for row in rows:
 lines.append('| '+row['id']+' — '+row['delivered_group']+' | '+', '.join(row['scope_ids'])+' | '+row['observation'].replace('|','\\|')+' |')
lines += ['','## Affected delivery since the earlier audit','','| Delta | Original scope | Why it remains within scope |','|---|---|---|']
for d in deltas:lines.append('| '+d['id']+' — '+d['delivered_delta']+' | '+', '.join(d['scope_ids'])+' | '+d['scope_boundary'].replace('|','\\|')+' |')
lines += ['','## Current evidence distinctions','',
'- **Native media:** exact3b00 iPhone, corrected iPad and Android local selections each have three full-frame still candidates and a19-second actual-gameplay preview. The Android packet independently passes native provenance, whole-image pixel/color/opacity, metadata, five actual visual frames and exact sampled source-time correspondence. All seasonal stills remain internal local previews. Android source has44frames over28.5978778seconds; holding samples for570output frames is not additional captured motion. All current clips are silent and actual measured bitrates remain below the11Mbps request. No store ingestion, natural player pacing, physical-device performance or public seasonal schedule is inferred. The M5-06 and S43 original obligations remain open.',
'- **M4-07:** the existing named client judgment supports its exact local harbor/cosmetic/audio integration clause, with different-author art/Settings evidence and actual three-target native playback clocks. It remains in progress because M4-06 is unaccepted. Broader final sound direction, physical mix/interruption and paid soundtrack fulfillment/distribution remain distinct. Do not invent an additional blanket human-only asset approval gate or an external audio purchase requirement.',
'- **Native reminders:** the dedicated new harness uses the real gateway/preferences/planner/lifecycle rather than the quiet fixture. The callback-zone repair collects raw observations and validates in the main test zone; it does not weaken due/save/pending/body/return gates or the real five-minute schedule. Its source changes have a different-author review. Actual OS prompt/permission/revoke/delivery observations are separate outcomes owned by the native verifier and independent QA; this reverse audit does not promote them merely because code or host tests exist. Unsupported or failed runs remain unqualified.',
'- **Native study and Settings:** actual storage/callback probes and the two Settings UI cases test only their documented controls and injected conditions. A healthy writer drain followed by refusal injection is not full-disk/adversarial-storage qualification. Fake audio/store host controls do not replace real native plugin evidence; native decode/clock receipts do not establish physical audibility.',
'- **Authorship:** this reviewer previously contributed daily icons and capture/reminder test tooling. Their different-author lead/QA reviews are used for approval, not self-approval. This audit independently assesses scope and the root-authored final Android media. No Flutter/native/device command or broad suite was run; no production or live metadata was changed.',
'','## Data, monetization and configuration boundaries','',
'Client service URL, study provisioning and public destinations default empty. Commerce, rewarded ads and supporter switches default false; telemetry and reminders default off. This is a source configuration fact, not a claim that every linked SDK makes zero network calls. Optional account recovery, cloud saves, signed entitlements, provider verification and operational services exist as implemented adapters; absent accounts, provider keys, host and genuine transactions remain absent.',
'','The server differs from client defaults: local SQLite cloud/purchases/ads/telemetry switches initialize to1, but unconfigured verification factories reject and telemetry consent starts0. Services require invocation and bind loopback by default. This is not a deployed service or unconditional telemetry collection. Account UUIDs, recovery/session hashes, snapshots, transaction/support ledgers and consent-bound enum telemetry support original recovery/commerce/operations obligations. Session/event bounds and deletion logic are source-backed; production backup/WAL retention, real SDK/network disclosures and actual provider deletion remain external operating qualifications.',
'','The opt-in study is a distinct bounded local collection path, with random enrollment/process identifiers and explicit consent/protocol/configuration hashes. Native PID/build/time can link deliberately supplied diagnostics; no automatic log upload, invented crash or synthetic participant denominator follows. Default, declined and withdrawn enrollment paths remain separate. Prepared studies/simulation code create zero empirical players, D30 retention observations or10,000-session production evidence.',
'','Original score/synthesis records state no incorporated samples. Existing font attribution preserves the actual supplied MaterialIcons notice despite the upstream Apache2.0/cachedCC BY4.0 wording discrepancy; this audit asserts neither relicensing nor a legal violation. Local support/privacy/deletion pages and operations runbooks are original release preparation. Prepared source/asset rights records are not public distribution approval or a published policy.',
'','## Findings and final reverse decision','',
'`note-only-findings.json` records three narrow stale-text findings. M4-07 still calls accepted M1-07/M3-09 work pending; M5-06 still says current edited/inspected exports are absent; the store README still calls Android validation in progress. Exact M4-07/M5-06 note proposals preserve statuses, clauses, dependencies and scope limits. Their correction is evidentiary housekeeping, not a new game feature or acceptance upgrade. The lead owns adoption.',
'','No corrective game-scope change is recommended. No additional human/provider approval gate is invented. The original unavailable resources and time-dependent evidence remain required: Apple/Google developer resources, physical targets, hosting/operator arrangements, human playtests/retention and launch/season observation. Local native simulator/emulator proofs, fixture outcomes and store media do not supply these resources or elapsed real-world evidence.',
'','This is the implementation→scope half of the combined audit. The separate forward review must still decide whether each original clause is fully evidenced. Scope mapping and clean source identity are not finished-release readiness.']
(O/'REVERSE_SCOPE_REVIEW.md').write_text('\n'.join(lines)+'\n')
print('Draft report written; source and exact contract pins remain unchanged. Ready to seal at stated cutoff or append lead adoption review.')
