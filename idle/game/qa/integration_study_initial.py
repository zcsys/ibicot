"""Counterexamples against the original D7 analysis schema. Synthetic only."""
import importlib.util,json,sys,copy
from pathlib import Path
spec=importlib.util.spec_from_file_location('study',sys.argv[1]);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
p={'schema_version':1,'study_id':'independent_synthetic','synthetic':True,'preregistered_at':0,'enrollment_start':1000,'enrollment_end':1001,'primary_outcome':'D7','design':'descriptive_no_experiment','exclusion_rules':['staff','automation','invalid_install'],'baseline':{'candidate_sha256':'a'*64,'economy_sha256':'b'*64,'content_sha256':'c'*64,'config':'baseline_a'},'registry_population':'opt_in_study','registry_source':'Synthetic fixed registry','session_definition':'A valid return includes interactive foreground harbor and foreground activity; startup crash is not return-valid.','missing_data_rule':'Preserve unknowns.'}
d={'schema_version':1,'synthetic':True,'cutoff':1000+31*s.DAY,'installs':[{'id':'synthetic_install_01','first_launch':1000,'platform':'test','device_group':'simulated','acquisition':'fixture','baseline_config':'baseline_a','exclusion':None,'observable_intervals':[[1000,1000+31*s.DAY]]}],'sessions':[{'install_id':'synthetic_install_01','session_id':'startup_crash_before_harbor','start':1000+7*s.DAY,'end':1001+7*s.DAY,'crashed':True,'valid':False,'config':'candidate_b'}]}
r=s.summarize(p,d);result={'synthetic':True,'input':d,'result':r,'findings':[]}
q=r['overall']['sessions'];ret=r['overall']['retention'][1]
if q['reported_crash_sessions']!=1:result['findings'].append({'id':'STUDY001','expected_confirmed_startup_crashes':1,'actual_reported_crash_sessions':q['reported_crash_sessions'],'reason':'Original documented valid-return criterion reused for crash record inclusion.'})
if ret['observed_config_change_before_window_end']!=1:result['findings'].append({'id':'STUDY001','expected_changed_candidate_exposure':1,'actual_reported_config_exposures':ret['observed_config_change_before_window_end'],'reason':'Attempted candidate_b startup is present but filtered from exposure.'})
print(json.dumps(result,indent=2));sys.exit(1 if result['findings'] else 0)
