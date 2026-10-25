import importlib.util,pathlib,sys,unittest
ROOT=pathlib.Path('/Users/csys/Desktop/ibicot/idle');HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tool'));name='verify_current_runtime';path=HERE/('before-verify_current_runtime.py' if '--before' in sys.argv else 'verify_current_runtime.py')
spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);v.ROOT=ROOT
suite=unittest.TestSuite()
for name,path in [('original_suite',HERE/'original-test_current_runtime_verification.py'),('probe_suite',HERE/'test_android_fixture_exit_status.py')]:
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if '--before' in sys.argv:
  if name=='probe_suite':suite.addTest(module.ProbeTests('test_directory_not_link_remote_false_status_survives_transport'))
 else:suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
