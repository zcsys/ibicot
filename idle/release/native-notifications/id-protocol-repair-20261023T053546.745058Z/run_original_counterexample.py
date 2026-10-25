import importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.dont_write_bytecode=True
sys.path[:0]=[str(HERE/'proposed/tool'),str(ROOT/'tool')]
import test_native_reminders as checks
spec=importlib.util.spec_from_file_location('original_reminder_runner',HERE/'before/tool/verify_native_reminders.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
checks.verify=original
suite=unittest.TestSuite([checks.ReminderIdentityProtocolTests('test_generated_id_is_accepted_by_actual_unchanged_Dart_contract')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
expected=result.testsRun==1 and len(result.failures)==1 and not result.errors
(HERE/'original-counterexample.json').write_text(json.dumps({'expected_failure_observed':expected,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'original runner generated ID rejected by unchanged Dart consumer expression; native launch blocked'},indent=2)+'\n')
raise SystemExit(0 if expected else 1)
