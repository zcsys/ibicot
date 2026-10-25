"""Measurement contract probes; all participant/session data are synthetic."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('study_report',Path(__file__).with_name('study_report.py'))
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)
D = study.DAY


def fixture():
    protocol = {'schema_version':1,'study_id':'synthetic_cohort','synthetic':True,
        'preregistered_at':0,'enrollment_start':100,'enrollment_end':200,
        'primary_outcome':'D7','design':'descriptive_no_experiment',
        'exclusion_rules':['staff','automation','invalid_install'],
        'baseline':{'candidate_sha256':'a'*64,'economy_sha256':'b'*64,
                    'content_sha256':'c'*64,'config':'fixture_v1'},
        'registry_population':'opt_in_study','registry_source':'Synthetic registry; no people.',
        'session_definition':'One valid foreground start; explicit ends/crashes only.',
        'missing_data_rule':'Keep installs; report unidentified returns as bounds.'}
    data = {'schema_version':2,'synthetic':True,'cutoff':100+31*D,'installs':[], 'sessions':[]}
    for n in range(4):
        data['installs'].append({'id':f'person_{n:04}','first_launch':100,'platform':'test',
            'device_group':'fixture','acquisition':'fixture','baseline_config':'fixture_v1',
            'exclusion':None,'observable_intervals':[[100,data['cutoff']]]})
    return protocol,data


def session(person, name, start, end=None, crashed=False, valid=True, config='fixture_v1', return_eligible=None):
    return {'install_id':f'person_{person:04}','session_id':name,'start':start,
            'end':end,'crashed':crashed,'valid':valid,'config':config,
            'return_eligible':valid if return_eligible is None else return_eligible}


class StudyTests(unittest.TestCase):
    def test_half_open_return_boundaries_and_exact_maturity(self):
        p,d = fixture()
        start=100+30*D
        d['sessions']=[session(0,'at_start',start),session(1,'last_second',start+D-1),
                       session(2,'at_end',start+D),session(3,'before',start-1)]
        r=study.summarize(p,d)['overall']['retention'][2]
        self.assertEqual((r['eligible_mature_installs'],r['observed_returns']),(4,2))
        d['cutoff']-=1
        for i in d['installs']:i['observable_intervals'][0][1]-=1
        d['sessions']=d['sessions'][:2]+d['sessions'][3:]
        r=study.summarize(p,d)['overall']['retention'][2]
        self.assertEqual(r['eligible_mature_installs'],0)
        self.assertIsNone(r['observed_return_fraction'])

    def test_missingness_does_not_remove_people(self):
        p,d=fixture()
        d['installs'][0]['observable_intervals']=[]
        d['installs'][1]['observable_intervals']=[]
        d['sessions']=[session(0,'known_return',100+30*D)]
        r=study.summarize(p,d)['overall']['retention'][2]
        self.assertEqual(r['eligible_mature_installs'],4)
        self.assertEqual(r['unresolved_return_status'],1)
        self.assertEqual(r['fully_observable_windows'],2)
        self.assertEqual(r['missing_data_identification_bounds'],[.25,.5])

    def test_exclusions_and_nonreturners_have_fixed_denominator(self):
        p,d=fixture()
        d['installs'][0]['exclusion']='staff'
        d['sessions']=[session(0,'staff_return',100+30*D)]
        r=study.summarize(p,d)
        self.assertEqual(r['exclusions'],{'staff':1})
        self.assertEqual(r['overall']['retention'][2]['eligible_mature_installs'],3)
        self.assertEqual(r['overall']['retention'][2]['observed_returns'],0)
        d['installs'][1]['exclusion']='left_onboarding'
        with self.assertRaises(ValueError):study.summarize(p,d)

    def test_interval_union_and_gaps(self):
        self.assertTrue(study.covers([[5,8],[0,5],[8,12]],1,11))
        self.assertFalse(study.covers([[0,5],[6,12]],1,11))
        self.assertTrue(study.covers([[0,100],[20,30]],10,90))
        self.assertFalse(study.covers([],10,90))

    def test_config_change_is_disclosed_without_dropping_install(self):
        p,d=fixture()
        d['sessions']=[session(0,'changed',100+30*D,config='fixture_v2')]
        r=study.summarize(p,d)['overall']['retention'][2]
        self.assertEqual(r['observed_config_change_before_window_end'],1)
        self.assertEqual(r['eligible_mature_installs'],4)
        self.assertEqual(r['observed_returns'],1)
        d['installs'][0]['baseline_config']='fixture_v2'
        with self.assertRaises(ValueError):study.summarize(p,d)

    def test_explicit_crashes_unknown_ends_invalid_records(self):
        p,d=fixture()
        d['sessions']=[session(0,'complete',100,200),session(1,'unknown',100),
                       session(2,'crashed',100,200,True),session(3,'invalid',100,valid=False)]
        r=study.summarize(p,d)
        s=r['overall']['sessions']
        self.assertEqual((s['valid_observed_sessions'],s['reported_crash_sessions'],
                          s['completed_without_reported_crash'],s['unknown_outcomes']),(3,1,1,1))
        self.assertEqual(s['completed_fraction_lower_bound'],1/3)
        self.assertEqual(r['invalid_session_records'],1)
        self.assertFalse(r['release_ready'])

    def test_startup_crash_counts_without_qualifying_as_return(self):
        p,d=fixture()
        d['sessions']=[session(0,'startup_failure',100+30*D,crashed=True,
                               config='fixture_v2',return_eligible=False)]
        r=study.summarize(p,d)
        self.assertEqual(r['overall']['sessions']['reported_crash_sessions'],1)
        self.assertEqual(r['overall']['sessions']['valid_observed_sessions'],1)
        self.assertEqual(r['overall']['retention'][2]['observed_returns'],0)
        self.assertEqual(r['overall']['retention'][2]['observed_config_change_before_window_end'],1)
        d['sessions'][0]['valid']=False
        d['sessions'][0]['return_eligible']=True
        with self.assertRaises(ValueError):study.summarize(p,d)
        del d['sessions'][0]['return_eligible']
        with self.assertRaises(ValueError):study.summarize(p,d)

    def test_wilson_reference_and_degenerate_cases(self):
        lo,hi=study.wilson(50,100)
        self.assertAlmostEqual(lo,0.4038315303659956)
        self.assertAlmostEqual(hi,0.5961684696340044)
        self.assertEqual(study.wilson(0,0),None)
        self.assertAlmostEqual(study.wilson(0,10)[0],0)
        self.assertAlmostEqual(study.wilson(10,10)[1],1)
        self.assertGreater(study.wilson(0,10)[1],0)
        with self.assertRaises(ValueError):study.wilson(2,1)

    def test_empty_registry_never_means_success(self):
        p,d=fixture();d['installs']=[]
        r=study.summarize(p,d)
        self.assertIsNone(r['overall']['sessions']['completed_fraction_lower_bound'])
        self.assertIsNone(r['overall']['retention'][2]['observed_fraction_wilson_95'])
        self.assertFalse(r['release_ready'])
        self.assertEqual(r['status'],'synthetic_fixture')

    def test_bad_inputs(self):
        mutations=[lambda p,d:p.update(preregistered_at=101),
            lambda p,d:p.update(design='causal_ab'),
            lambda p,d:d.update(synthetic=False),
            lambda p,d:d['installs'].append(copy.deepcopy(d['installs'][0])),
            lambda p,d:d['installs'][0].update(first_launch=99),
            lambda p,d:d['installs'][0].update(first_launch=200),
            lambda p,d:d['installs'][0].update(observable_intervals=[[100,d['cutoff']+1]]),
            lambda p,d:d['sessions'].append(session(9,'unknown_id',100)),
            lambda p,d:d['sessions'].append(session(0,'future',d['cutoff']+1)),
            lambda p,d:d['sessions'].extend([session(0,'same',100),session(0,'same',101)]),
            lambda p,d:d['sessions'].append(session(0,'backwards',101,100)),
            lambda p,d:p['baseline'].update(candidate_sha256='not_a_hash'),
            lambda p,d:d['installs'][0].update(raw_email='private@example.test')]
        for mutate in mutations:
            p,d=fixture();mutate(p,d)
            with self.subTest(mutation=mutate),self.assertRaises(ValueError):study.summarize(p,d)

    def test_real_study_rejects_test_platform(self):
        p,d=fixture();p['synthetic']=d['synthetic']=False
        with self.assertRaises(ValueError):study.summarize(p,d)

    def test_cli_aggregate_output_and_private_failure(self):
        p,d=fixture()
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'protocol.json';b=Path(folder)/'data.json'
            a.write_text(json.dumps(p));b.write_text(json.dumps(d))
            command=[sys.executable,str(Path(__file__).with_name('study_report.py')),
                     '--protocol',str(a),'--data',str(b)]
            run=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            output=json.loads(run.stdout)
            self.assertIn('inputs_sha256',output)
            self.assertNotIn('person_0000',run.stdout)
            b.write_text('{"private@example.test": 1}')
            run=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
            self.assertNotIn('private@example.test',run.stderr)
            self.assertEqual(run.stdout,'')

    def test_duplicate_json_and_nonfinite_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json'
            for text in ['{"x":1,"x":2}','{"x":NaN}']:
                path.write_text(text)
                with self.assertRaises(ValueError):study.load_json(path)


if __name__=='__main__':unittest.main()
