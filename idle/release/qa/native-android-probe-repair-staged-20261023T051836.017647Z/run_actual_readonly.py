import importlib.util,pathlib,sys,json,hashlib
ROOT=pathlib.Path('/Users/csys/Desktop/ibicot/idle');HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tool'));spec=importlib.util.spec_from_file_location('staged_probe_runner',HERE/'verify_current_runtime.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.ROOT=ROOT
failed=ROOT/'release/native-proof/current-runtime-android-20261023T051542413435Z';context=json.loads((failed/'verification.json').read_text());marker=v.marker_from_log((failed/'run.log').read_text(),context);directory=str(pathlib.Path(marker['checkpoint']).parent)
host=v.NativeHost(context);raw=host.read_fixture(directory,'checkpoint.json',limit=65536);assert v.digest(raw)==marker['checkpoint_sha256'];v.validate_checkpoint(raw,context,marker['process_id']);(HERE/'actual-diagnostic-checkpoint.json').write_bytes(raw)
absent=host.read_fixture(directory,'support/tideglass-study.json',optional=True);assert absent is None
count=len(host.observations)
try:host.read_fixture(directory+'/../outside','checkpoint.json')
except ValueError:pass
else:raise AssertionError('Traversal accepted')
assert len(host.observations)==count
record={'scope':'Read-only diagnostic of already stopped failed fixture; no native execution, recovered test, expected-interrupted classification or acceptance claim','original_failure':str(failed/'verification.json'),'staged_runner_sha256':hashlib.sha256((HERE/'verify_current_runtime.py').read_bytes()).hexdigest(),'diagnostic_checkpoint_sha256':v.digest(raw),'checkpoint_matches_original_native_marker':True,'optional_absent_is_none':True,'traversal_refused_without_command':True,'observations':host.observations}
(HERE/'actual-readonly-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['staged_runner_sha256','checkpoint_matches_original_native_marker','optional_absent_is_none','traversal_refused_without_command']}))
