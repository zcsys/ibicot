import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANDIDATE=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
spec=importlib.util.spec_from_file_location('probe_binding_observer',HERE/'runtime_observation.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)

class ProbeBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.e=Path(self.temp.name)/'evidence';self.e.mkdir()
        self.manifest=json.loads((CANDIDATE/'manifest.json').read_text())
        for name,relative in o.SOURCE_ARCHIVES.items():
            (self.e/name).write_bytes((CANDIDATE/'source'/relative).read_bytes())
        self.original=(self.e/'runner.py').read_bytes()
        self.repaired=self.original.replace(o._PROBE_BEFORE,o._PROBE_AFTER,1)
    def bind(self,platform='android'):
        return o.source_binding(CANDIDATE,self.e,self.manifest,platform=platform)
    def apply(self): (self.e/'runner.py').write_bytes(self.repaired)
    def test_original_candidate_binding_stays_exact(self):
        binding,archives=self.bind();self.assertNotIn('verification_tool_bridge',binding)
        self.assertEqual(archives['native-runner.py'],self.original)
    def test_exact_android_repair_archives_both_versions(self):
        self.apply();binding,archives=self.bind()
        self.assertEqual(binding['verification_tool_bridge']['executed_runner_sha256'],o.sha(self.repaired))
        self.assertEqual(binding['native_source_sha256']['runner.py'],o.sha(self.repaired))
        self.assertEqual(archives['native-runner.py'],self.repaired)
        self.assertEqual(archives['candidate-native-runner.py'],self.original)
        self.assertEqual(archives['completion-verifier.py'],(self.e/'verify_native.py').read_bytes())
        self.assertEqual(set(archives),{'collector.py','completion-verifier.py','native-runner.py','candidate-manifest.json','candidate-native-runner.py'})
    def test_bridge_cannot_be_used_on_ios_or_unknown_platform(self):
        self.apply()
        for platform in ['ios',None,'other']:
            with self.subTest(platform=platform),self.assertRaises(ValueError):self.bind(platform)
    def test_other_candidate_fingerprint_rejected(self):
        self.apply()
        with patch.dict(o.ANDROID_PROBE_BRIDGE,{'candidate_fingerprint':'0'*64}),self.assertRaises(ValueError):self.bind()
    def test_unknown_original_runner_hash_rejected(self):
        self.apply()
        with patch.dict(o.ANDROID_PROBE_BRIDGE,{'candidate_runner_sha256':'0'*64}),self.assertRaises(ValueError):self.bind()
    def test_extra_runner_change_rejected(self):
        self.apply();(self.e/'runner.py').write_bytes(self.repaired+b'\n')
        with self.assertRaises(ValueError):self.bind()
    def test_extra_change_rejected_even_if_executed_hash_declared(self):
        modified=self.repaired+b'\n';(self.e/'runner.py').write_bytes(modified)
        with patch.dict(o.ANDROID_PROBE_BRIDGE,{'executed_runner_sha256':o.sha(modified)}),self.assertRaisesRegex(ValueError,'additional changes'):self.bind()
    def test_harness_change_stays_forbidden(self):
        self.apply();(self.e/'harness.dart').write_bytes((self.e/'harness.dart').read_bytes()+b'\n')
        with self.assertRaises(ValueError):self.bind()
    def test_completion_verifier_change_stays_forbidden(self):
        self.apply();(self.e/'verify_native.py').write_bytes((self.e/'verify_native.py').read_bytes()+b'\n')
        with self.assertRaises(ValueError):self.bind()
    def test_missing_runner_rejected(self):
        (self.e/'runner.py').unlink()
        with self.assertRaises(OSError):self.bind()
    def test_symlink_runner_rejected(self):
        (self.e/'runner.py').unlink();(self.e/'runner.py').symlink_to(HERE/'runner-before.py')
        with self.assertRaises(OSError):self.bind()
    def test_caller_manifest_change_rejected(self):
        self.manifest=copy.deepcopy(self.manifest);self.manifest['source_fingerprint']='0'*64
        with self.assertRaisesRegex(ValueError,'manifest changed'):self.bind()
    def test_archive_bytes_revalidated_after_binding(self):
        self.apply();binding,archives=self.bind();output=Path(self.temp.name)/'observation';output.mkdir()
        for name,data in archives.items():(output/name).write_bytes(data)
        _,context=o.context_for(CANDIDATE,self.e,'emulator-5556')
        report={'collector_sha256':o.COLLECTOR_SHA256,'candidate':str(CANDIDATE),'native_evidence':str(self.e),'device':'emulator-5556','context':context,'source_binding':binding}
        self.assertEqual(o.validate_source_binding(report,output),archives['completion-verifier.py'])
        (output/'candidate-native-runner.py').write_bytes(self.original+b'\n')
        with self.assertRaisesRegex(ValueError,'archive changed'):o.validate_source_binding(report,output)
    def test_binding_metadata_cannot_omit_bridge(self):
        self.apply();binding,archives=self.bind();output=Path(self.temp.name)/'observation';output.mkdir()
        for name,data in archives.items():(output/name).write_bytes(data)
        _,context=o.context_for(CANDIDATE,self.e,'emulator-5556')
        del binding['verification_tool_bridge']
        report={'collector_sha256':o.COLLECTOR_SHA256,'candidate':str(CANDIDATE),'native_evidence':str(self.e),'device':'emulator-5556','context':context,'source_binding':binding}
        with self.assertRaisesRegex(ValueError,'binding changed'):o.validate_source_binding(report,output)

if __name__=='__main__':unittest.main(verbosity=2)
