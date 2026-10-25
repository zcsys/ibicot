"""Independent adversarial qualification of the bounded art-evidence checker."""
import contextlib,copy,hashlib,importlib.util,io,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/'source/art/verification/check_matrix.py'
spec=importlib.util.spec_from_file_location('reviewed_art_checker',P);checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
PROOF=ROOT/'release/native-proof/root-art-pseudo-full-20261021T122636.246158Z'
REPORT=ROOT/'release/art/catalogue-variants/root-art-pseudo-full-20261021T122636.246158Z/matrix-results.json'
class CheckerCounterexamples(unittest.TestCase):
 def call(self,change=None):
  with tempfile.TemporaryDirectory(prefix='qa-art-checker-') as td:
   temp=pathlib.Path(td).resolve();proof=temp/'proof';proof.mkdir();report=temp/'report.json'
   data=json.loads(REPORT.read_text());metadata=json.loads((PROOF/'verification.json').read_text())
   for x in ['source','source-before.json','analyzer.log','art.log']:(proof/x).symlink_to(PROOF/x,target_is_directory=(x=='source'))
   for result in metadata['results']:
    result['command']=[f'--dart-define=TIDEGLASS_ART_REPORT_DIR={temp}' if c.startswith('--dart-define=TIDEGLASS_ART_REPORT_DIR=') else c for c in result['command']]
   if change:change(data,metadata)
   report.write_text(json.dumps(data))
   metadata['art_report_sha256']=hashlib.sha256(report.read_bytes()).hexdigest()
   (proof/'verification.json').write_text(json.dumps(metadata))
   out=io.StringIO()
   with patch.object(sys,'argv',['checker',str(report),'--proof',str(proof),'--full']),contextlib.redirect_stdout(out):code=checker.main()
   return code,json.loads(out.getvalue())
 def reject(self,change):
  code,data=self.call(change);self.assertNotEqual(code,0,msg=json.dumps(data))
 def test_control_full_proof(self):self.assertEqual(self.call()[0],0)
 def test_missing_asset_pair(self):self.reject(lambda d,p:d['rows'].pop())
 def test_duplicate_asset_pair(self):self.reject(lambda d,p:d['rows'].__setitem__(0,copy.deepcopy(d['rows'][1])))
 def test_missing_supplement(self):self.reject(lambda d,p:d['supplemental_cases'].pop())
 def test_wrong_pseudo_command(self):self.reject(lambda d,p:p['results'][-1]['command'].remove('--dart-define=TIDEGLASS_PSEUDO=true'))
 def test_failed_actual_command(self):self.reject(lambda d,p:p['results'][-1].__setitem__('exit_code',1))
 def test_reported_source_drift(self):self.reject(lambda d,p:p.__setitem__('source_differences',['game/mobile/lib/app.dart']))
 def test_filtered_separate_option(self):self.reject(lambda d,p:p['results'][-1]['command'].extend(['--name','phone-100-normal']))
 def test_filtered_attached_option(self):self.reject(lambda d,p:p['results'][-1]['command'].append('--name=phone-100-normal'))
 def test_false_producer_button_semantics(self):self.reject(lambda d,p:next(r for r in d['rows'] if r['group']=='producer').__setitem__('button_semantics_and_48px_hitbox',False))
 def test_false_cosmetic_reachability(self):self.reject(lambda d,p:next(r for r in d['rows'] if r['group']=='cosmetic').__setitem__('controls_reachable_with_48px_button_semantics',False))
 def test_failed_lifecycle_supplement(self):self.reject(lambda d,p:next(r for r in d['supplemental_cases'] if r['case']=='actual_app_animation_lifecycle').__setitem__('background_phase_stops',False))
 def test_failed_palette_supplement(self):self.reject(lambda d,p:next(r for r in d['supplemental_cases'] if r['case']=='declared_text_palette')['ratios'].__setitem__('text_on_deep',1.0))
 def test_false_canonical_promotion(self):self.reject(lambda d,p:d.__setitem__('canonical_verification_written',True))
if __name__=='__main__':unittest.main(verbosity=2)
