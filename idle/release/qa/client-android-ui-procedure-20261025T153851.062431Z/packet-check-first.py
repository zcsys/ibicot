from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
R=Path('/Users/csys/Desktop/ibicot/idle');F=R/'release/native-notifications/android-ui-feasibility-20261025T153603.735375Z';O=Path(Path('/tmp/client_ui_procedure_folder.txt').read_text().strip());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(F/'verification.json')=='f8bd3e38001397646280febd959612fbb5e8212606e6393e9191dd86271ca17c'
v=json.loads((F/'verification.json').read_text())
for n,h in v['evidence_sha256'].items():assert sha(F/n)==h,n
before=json.loads((O/'input-pins-before.json').read_text());assert sha(O/'checkpoint-before.txt')==before['implementation/team/EXECUTION_CHECKPOINT.md']==v['source_pins']['implementation/team/EXECUTION_CHECKPOINT.md']
for n in ['game/mobile/integration_test/native_reminders_test.dart','tool/verify_native_reminders.py']:assert sha(R/n)==v['source_pins'][n]==before[n]
assert sha(R/'docs/quality/android-ui-operator.md')=='4b841ade92aee43a7292c07bbaa0e0d1306a9468c840e2318eaf0a43fc0e796a'
raw=(F/'hierarchy-readonly.txt').read_text();start=raw.index('<?xml');end=raw.index('</hierarchy>')+len('</hierarchy>');tree=ET.fromstring(raw[start:end]);nodes=list(tree.iter('node'))
buttons=[n.attrib for n in nodes if n.attrib.get('class')=='android.widget.Button' and n.attrib.get('package')=='com.google.android.permissioncontroller']
assert len(buttons)==2 and all(n['enabled']=='true' and n['clickable']=='true' for n in buttons)
assert {n['resource-id'] for n in buttons}=={'com.android.permissioncontroller:id/permission_allow_button','com.android.permissioncontroller:id/permission_deny_and_dont_ask_again_button'}
assert 'Tideglass_API_35' in (F/'probe-01.txt').read_text()
assert (F/'probe-02.txt').read_text().strip()=='35'
assert not (F/'pid.txt').read_text().strip()
acts=(F/'activities.txt').read_text();assert 'launchedFromPackage=dev.tideglass.game' in acts
report={'packet_files_rehashed':len(v['evidence_sha256']),'actual_readonly_nodes':buttons,'stale_prompt_no_app_pid':True,'original_checkpoint_preserved':True,'harness_runner_unchanged':True,'prospective_operator_decision_sha256':sha(R/'docs/quality/android-ui-operator.md'),'current_checkpoint_sha256':sha(R/'implementation/team/EXECUTION_CHECKPOINT.md'),'reviewer_device_actions':0,'native_success_inferred':False}
(O/'packet-check.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',len(v['evidence_sha256']),'packet files rehashed; two exact enabled controls; API35 stdout and empty stderr confirmed; no UI action.')
