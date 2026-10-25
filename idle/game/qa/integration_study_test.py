"""Independent synthetic QA for the offline descriptive study analyzer.
No test participants, collection, transport or empirical claims are involved.
"""
import copy, importlib.util, json, os, random, subprocess, sys, tempfile, unittest
from pathlib import Path
from decimal import Decimal, localcontext
SOURCE=Path(os.environ.get('STUDY_REVIEW_TOOL',Path(__file__).resolve().parents[2]/'tool/study_report.py')).resolve()
spec=importlib.util.spec_from_file_location('independently_reviewed_study',SOURCE)
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
DAY=86400
START=1000

def fixture(n=4,cutoff=None):
 p={'schema_version':1,'study_id':'independent_synthetic','synthetic':True,'preregistered_at':999,'enrollment_start':START,'enrollment_end':START+100,'primary_outcome':'D7','design':'descriptive_no_experiment','exclusion_rules':['staff','automation','invalid_install'],'baseline':{'candidate_sha256':'a'*64,'economy_sha256':'b'*64,'content_sha256':'c'*64,'config':'baseline_a'},'registry_population':'opt_in_study','registry_source':'Synthetic fixed registry for independent QA only.','session_definition':'Legitimate session records are distinct from interactive-harbor/activity return eligibility.','missing_data_rule':'Preserve missing installs and compute identification bounds.'}
 d={'schema_version':2,'synthetic':True,'cutoff':cutoff if cutoff is not None else START+31*DAY,'installs':[],'sessions':[]}
 for i in range(n):d['installs'].append({'id':f'synthetic_{i:08}','first_launch':START,'platform':'test','device_group':'fixture','acquisition':'organic_fixture','baseline_config':'baseline_a','exclusion':None,'observable_intervals':[[START,d['cutoff']]]})
 return p,d

def session(i,name,when,*,end=None,crashed=False,valid=True,eligible=True,config='baseline_a'):
 return {'install_id':f'synthetic_{i:08}','session_id':name,'start':when,'end':end,'crashed':crashed,'valid':valid,'return_eligible':eligible,'config':config}

class IndependentStudy(unittest.TestCase):
 def test_startup_crash_and_candidate_exposure_without_return(self):
  p,d=fixture(1);t=START+7*DAY
  d['sessions']=[session(0,'real_record_before_harbor',t,end=t+1,crashed=True,eligible=False,config='candidate_b')]
  r=study.summarize(p,d);q=r['overall']['sessions'];day7=r['overall']['retention'][1]
  self.assertEqual(q['reported_crash_sessions'],1)
  self.assertEqual(q['valid_observed_sessions'],1)
  self.assertEqual(q['unknown_outcomes'],0)
  self.assertEqual(q['completed_without_reported_crash'],0)
  self.assertEqual(day7['observed_config_change_before_window_end'],1)
  self.assertEqual(day7['observed_returns'],0)
  self.assertEqual(day7['eligible_mature_installs'],1)

 def test_record_validity_and_return_eligibility_are_both_required(self):
  p,d=fixture(1);row=session(0,'invalid',START+DAY,valid=False,eligible=True)
  d['sessions']=[row]
  with self.assertRaises(ValueError):study.summarize(p,d)
  for field in ['valid','return_eligible']:
   p,d=fixture(1);row=session(0,'missing',START+DAY);row.pop(field);d['sessions']=[row]
   with self.subTest(field=field),self.assertRaises(ValueError):study.summarize(p,d)
  p,d=fixture(1);d['sessions']=[session(0,'invalid',START+DAY,valid=False,eligible=False)]
  r=study.summarize(p,d);self.assertEqual(r['invalid_session_records'],1);self.assertEqual(r['overall']['eligible_installs'],1)

 def test_mature_boundaries_and_per_install_denominators(self):
  p,d=fixture(4)
  d['installs'][1]['first_launch']+=1;d['installs'][1]['observable_intervals'][0][0]+=1
  d['sessions']=[session(0,'lower',START+30*DAY),session(0,'repeat',START+30*DAY+1),session(2,'upper',START+31*DAY),session(3,'last',START+31*DAY-1)]
  r=study.summarize(p,d)['overall']['retention'][2]
  self.assertEqual((r['eligible_mature_installs'],r['not_yet_mature_installs'],r['observed_returns']),(3,1,2))
  d['cutoff']+=1
  for i in d['installs']:i['observable_intervals'][0][1]+=1
  r=study.summarize(p,d)['overall']['retention'][2]
  self.assertEqual((r['eligible_mature_installs'],r['observed_returns']),(4,2))

 def test_missingness_bounds_include_decliners_and_observed_sparse_returns(self):
  p,d=fixture(5)
  for i in [0,1,2]:d['installs'][i]['observable_intervals']=[]
  d['sessions']=[session(0,'known_despite_sparse',START+30*DAY)]
  d['installs'][4]['exclusion']='staff'
  r=study.summarize(p,d);x=r['overall']['retention'][2]
  self.assertEqual(r['overall']['eligible_installs'],4)
  self.assertEqual((x['observed_returns'],x['fully_observable_windows'],x['unresolved_return_status']),(1,1,2))
  self.assertEqual(x['missing_data_identification_bounds'],[.25,.75])
  self.assertEqual(x['observed_return_fraction'],.25)
  self.assertFalse(r['registry_completeness_independently_verified'])

 def test_coverage_union_matches_integer_bruteforce(self):
  rng=random.Random(712386)
  for trial in range(800):
   start=rng.randrange(0,20);end=rng.randrange(start+1,42)
   intervals=[];covered=set()
   for _ in range(rng.randrange(12)):
    a=rng.randrange(0,42);b=rng.randrange(a+1,45);intervals.append([a,b]);covered.update(range(a,b))
   rng.shuffle(intervals)
   self.assertEqual(study.covers(intervals,start,end),set(range(start,end))<=covered,msg=str(trial))

 def test_wilson_matches_independent_decimal_score_root_inversion(self):
  # Invert the score-test inequality numerically, rather than repeating the
  # analyzer's closed-form implementation.
  with localcontext() as ctx:
   ctx.prec=70;z=Decimal('1.959963984540054');z2=z*z
   for n in [1,2,10,500,10000,100000]:
    for k in sorted({0,1,n//2,n-1,n}):
     phat=Decimal(k)/n
     def criterion(q):return Decimal(n)*(phat-q)**2-z2*q*(1-q)
     if k==0:lower=Decimal(0)
     else:
      lo,hi=Decimal(0),phat
      for _ in range(240):
       mid=(lo+hi)/2
       if criterion(mid)>0:lo=mid
       else:hi=mid
      lower=(lo+hi)/2
     if k==n:upper=Decimal(1)
     else:
      lo,hi=phat,Decimal(1)
      for _ in range(240):
       mid=(lo+hi)/2
       if criterion(mid)>0:hi=mid
       else:lo=mid
      upper=(lo+hi)/2
     actual=study.wilson(k,n)
     self.assertLess(abs(Decimal(actual[0])-lower),Decimal('1e-14'))
     self.assertLess(abs(Decimal(actual[1])-upper),Decimal('1e-14'))
  self.assertIsNone(study.wilson(0,0))

 def test_session_outcomes_and_strata_do_not_hide_unknowns(self):
  p,d=fixture(4)
  for i in [0,1]:d['installs'][i]['platform']='ios'
  for i in [2,3]:d['installs'][i]['platform']='android'
  t=START+7*DAY
  d['sessions']=[session(0,'complete',t,end=t+1),session(1,'unknown',t),session(2,'crash_no_end',t,crashed=True,eligible=False),session(3,'discarded',t,valid=False,eligible=False)]
  r=study.summarize(p,d);q=r['overall']['sessions']
  self.assertEqual((q['valid_observed_sessions'],q['reported_crash_sessions'],q['completed_without_reported_crash'],q['unknown_outcomes']),(3,1,1,1))
  self.assertEqual(q['completed_fraction_lower_bound'],1/3)
  for name in ['eligible_installs']:
   self.assertEqual(sum(v[name] for v in r['exploratory_strata']['platform'].values()),r['overall'][name])
  self.assertEqual(sum(v['sessions']['valid_observed_sessions'] for v in r['exploratory_strata']['platform'].values()),3)
  self.assertEqual(r['overall']['retention'][1]['observed_returns'],2)

 def test_config_change_does_not_exclude_install_and_future_change_not_backdated(self):
  p,d=fixture(2);d['sessions']=[session(0,'changed_without_return',START+DAY,eligible=False,config='candidate_b'),session(1,'later_change',START+8*DAY,config='candidate_b')]
  r=study.summarize(p,d)['overall']['retention'][1]
  self.assertEqual(r['eligible_mature_installs'],2);self.assertEqual(r['observed_config_change_before_window_end'],1);self.assertEqual(r['observed_returns'],0)
  d['installs'][0]['baseline_config']='candidate_b'
  with self.assertRaises(ValueError):study.summarize(p,d)

 def test_primary_protocol_and_whole_window_labels(self):
  p,d=fixture(0);r=study.summarize(p,d)
  self.assertFalse(r['whole_registered_window_d30_mature']);self.assertEqual(r['primary_outcome'],'D7');self.assertEqual(r['schema_version'],2)
  d['cutoff']=p['enrollment_end']+31*DAY;r=study.summarize(p,d)
  self.assertTrue(r['whole_registered_window_d30_mature']);self.assertTrue(r['enrollment_closed']);self.assertFalse(r['release_ready'])
  p['primary_outcome']='D30'
  with self.assertRaises(ValueError):study.summarize(p,d)
  template=json.loads((SOURCE.parent.parent/'release/study/protocol-template.json').read_text())
  with self.assertRaises(ValueError):study.summarize(template,d)

 def test_json_and_cli_errors_never_echo_private_records(self):
  with tempfile.TemporaryDirectory() as folder:
   a=Path(folder)/'protocol.json';b=Path(folder)/'data.json';p,d=fixture(1);a.write_text(json.dumps(p))
   command=[sys.executable,str(SOURCE),'--protocol',str(a),'--data',str(b)]
   for invalid in ['{"secret_record":"PRIVATE_SENTINEL","secret_record":2}','{"private":"PRIVATE_SENTINEL","value":NaN}','{"schema_version":2,"synthetic":true,"cutoff":2000,"installs":["PRIVATE_SENTINEL"],"sessions":[]}']:
    b.write_text(invalid);run=subprocess.run(command,capture_output=True,text=True)
    self.assertEqual(run.returncode,2);self.assertEqual(run.stdout,'');self.assertNotIn('PRIVATE_SENTINEL',run.stderr);self.assertNotIn('Traceback',run.stderr);self.assertEqual(json.loads(run.stderr)['status'],'invalid_input')
   d['sessions']=[session(0,'private_session_identifier',START+DAY,eligible=False)]
   b.write_text(json.dumps(d));run=subprocess.run(command,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr);r=json.loads(run.stdout)
   self.assertNotIn('synthetic_00000000',run.stdout);self.assertNotIn('private_session_identifier',run.stdout);self.assertIn('inputs_sha256',r);self.assertFalse(r['release_ready'])

 def test_future_bool_and_unrecognized_record_fields_reject(self):
  mutations=[lambda p,d:d.update(cutoff=True),lambda p,d:d['installs'][0].update(first_launch=True),lambda p,d:d['installs'][0].update(exclusion='declined_telemetry'),lambda p,d:d['sessions'].append(session(0,'future',d['cutoff']+1)),lambda p,d:d['installs'][0].update(observable_intervals=[[START,d['cutoff']+1]]),lambda p,d:d['installs'][0].update(recovery_code='PRIVATE_SENTINEL'),lambda p,d:d['sessions'].append(session(0,'bool_eligible',START+DAY,eligible=1))]
  for mutate in mutations:
   p,d=fixture(1);mutate(p,d)
   with self.subTest(mutation=mutate),self.assertRaises(ValueError):study.summarize(p,d)

 def test_input_limit_and_duplicate_nested_keys(self):
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/'input.json';file.write_bytes(b' '*(study.LIMIT+1))
   with self.assertRaises(ValueError):study.load_json(file)
   file.write_text('{"outer":{"one":1,"one":2}}')
   with self.assertRaises(ValueError):study.load_json(file)

if __name__=='__main__':unittest.main(verbosity=2)
