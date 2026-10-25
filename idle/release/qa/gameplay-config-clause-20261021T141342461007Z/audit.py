"""Clause evidence identity and real isolated packaging check; not Flutter tests."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile

REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW.parents[2]
SOURCE = REVIEW/'source'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = json.loads((REVIEW/'source-manifest.json').read_text())
for path, digest in inputs.items():
    assert sha(SOURCE/path) == digest, path

backlog = {v['id']: v for v in json.loads((SOURCE/'v1_backlog.json').read_text())['items']}
program = {v['id']: v for v in json.loads((SOURCE/'implementation/program.json').read_text())['items']}
for id in ('M1-04', 'M0-08'):
    assert backlog[id]['acceptance'] == program[id]['source_acceptance']
    assert backlog[id]['dependencies'] == program[id]['source_acceptance_dependencies']
assert backlog['M1-04']['dependencies'] == ['M0-08']
assert program['M0-08']['status'] == 'accepted'

manifest_path = SOURCE/'game/mobile/assets/config/manifest.json'
manifest = json.loads(manifest_path.read_text())
generated = (SOURCE/'game/mobile/lib/bundled_hashes.g.dart').read_text()
manifest_digest = re.search(r"bundledManifestDigest = '([^']+)'", generated)[1]
economic_digest = re.search(r"bundledEconomicDigest = '([^']+)'", generated)[1]
assert sha(manifest_path) == manifest_digest
assert len(manifest['files']) == 29
for path, descriptor in manifest['files'].items():
    content = SOURCE/'game/mobile'/path
    assert content.stat().st_size == descriptor['bytes'], path
    assert sha(content) == descriptor['sha256'], path
assert sha(SOURCE/'economy.json') == economic_digest
assert sha(SOURCE/'game/mobile/assets/config/economy.json') == economic_digest
assert manifest['economy_version'] == 'tideglass-economy-1.0.0'
assert manifest['schema_version'] == 1

# Execute the real generator only in a disposable copy; no live assets rewritten.
with tempfile.TemporaryDirectory(prefix='tideglass-config-review-') as folder:
    copy = Path(folder)/'source'
    shutil.copytree(SOURCE, copy)
    child = subprocess.run([sys.executable, str(copy/'tool/package_content.py')],
                           cwd=copy, capture_output=True, text=True, timeout=10)
    (REVIEW/'packaging.log').write_text(child.stdout+child.stderr)
    assert child.returncode == 0
    for path in ('game/mobile/assets/config/manifest.json', 'game/mobile/assets/config/economy.json',
                 'game/mobile/lib/bundled_hashes.g.dart'):
        assert (copy/path).read_bytes() == (SOURCE/path).read_bytes(), path

# Reuse independent QA on author-owned transition code only when exact pins match.
qa = SOURCE/'release/qa/integration-transition-repaired-20261021T121351672733Z'
old = json.loads((qa/'snapshot.json').read_text())['files']
transition_drift = [path for path, digest in old.items() if sha(ROOT/path) != digest]
assert not transition_drift, transition_drift
qa_verification = json.loads((qa/'verification.json').read_text())
adapter = qa_verification['author_host_selected_current_source']
adapter_drift = [path for path, digest in adapter.items() if sha(ROOT/path) != digest]
assert not adapter_drift, adapter_drift

# Earlier actual Flutter bundle tests are supporting author executions only.
# Record exact selected unchanged inputs, not a false whole-current-candidate bridge.
host = SOURCE/'release/native-proof/root-current-integration-20261021T110234.004565Z'
host_map = json.loads((host/'separate-source-before.json').read_text())
selected = ['game/mobile/lib/bundled_content.dart', 'game/mobile/lib/bundled_hashes.g.dart',
            'game/mobile/lib/content_compatibility.dart', 'game/mobile/lib/story_state.dart',
            'game/mobile/test/bundled_content_test.dart']
bundle_bridge = {}
for path in selected:
    assert path in host_map
    entry = host_map[path]
    expected = entry if isinstance(entry,str) else entry['sha256']
    bundle_bridge[path] = {'same':sha(ROOT/path)==expected,'sha256':sha(ROOT/path)}
assert all(row['same'] for row in bundle_bridge.values())
for path, digest in inputs.items():
    assert sha(SOURCE/path) == digest, path
    # Program may be legitimately updated by the lead during this recommendation.
    if path != 'implementation/program.json':
        assert sha(ROOT/path) == digest, path

result = {'scope':'M1-04 exact original clause; no runtime self-review or native command',
    'source_inputs':len(inputs), 'source_map_sha256':sha(REVIEW/'source-manifest.json'),
    'original_acceptance':backlog['M1-04']['acceptance'],
    'original_dependencies':backlog['M1-04']['dependencies'],
    'accepted_prerequisite':'M0-08', 'bundled_files_verified':29,
    'manifest_digest':manifest_digest,'economic_digest':economic_digest,
    'isolated_actual_package_generator_byte_identical':True,
    'prior_different_author_transition_inputs_rehashed':len(old),
    'prior_transition_source_drift':transition_drift,
    'prior_reviewed_client_adapter_inputs_rehashed':len(adapter),
    'prior_adapter_source_drift':adapter_drift,
    'earlier_actual_bundle_test_selected_source_bridge':bundle_bridge,
    'native_commands_by_this_reviewer':0,'program_statuses_changed':False}
(REVIEW/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
