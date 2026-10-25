import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import study_adjudicate as a
import study_report

ROOT=Path(__file__).resolve().parents[1]

class RawStudyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.protocol=json.loads((ROOT/'release/study/fixtures/synthetic-protocol.json').read_text())
        self.protocol_hash=hashlib.sha256((ROOT/'release/study/fixtures/synthetic-protocol.json').read_bytes()).hexdigest()
        self.counter=0
        self.proof={'schema_version':1,'check':'no_prior_game_directory_entries','checked_at':'1970-01-01T00:01:39.000Z','study_id':self.protocol['study_id'],'candidate_sha256':'a'*64}
        self.proof_hash=self.evidence(a.canonical(self.proof).encode())
        self.entry={'study_id':self.protocol['study_id'],'install_id':self.id(),'enrolled_at':100,'first_launch':100,
          'protocol_sha256':self.protocol_hash,'information_sha256':'e'*64,'consent_version':'synthetic_v1',
          'eligibility_evidence_sha256':self.proof_hash,'synthetic':True,'platform':'test','device_group':'unclassified',
          'acquisition':'internal_test','baseline':self.protocol['baseline']}
        self.registry={'schema_version':1,'study_id':self.protocol['study_id'],'synthetic':True,'entries':[self.entry]}
        self.document={'schema_version':1,'registry':copy.deepcopy(self.entry),'records':[],'status':'active'}
        self.raw={'schema_version':1,'study_id':self.protocol['study_id'],'synthetic':True,'exports':[{'install_id':self.entry['install_id'],'raw':self.document}]}
        self.review={'schema_version':1,'study_id':self.protocol['study_id'],'synthetic':True,'cutoff':32*86400,
          'installs':[{'install_id':self.entry['install_id'],'eligibility_review':'qualified','eligibility_evidence_sha256':self.proof_hash,'exclusion':None,'coverage':[]}],
          'native_crashes':[],'terminal_reviews':[]}
        self.process=self.id();self.session=self.id();self.event('app_start',100,{'config':self.protocol['baseline'],'reason':'enrollment'})
    def id(self):self.counter+=1;return f'{self.counter:032x}'
    def evidence(self,blob):
        reference=hashlib.sha256(blob).hexdigest();(self.folder/(reference+'.evidence')).write_bytes(blob);return reference
    def event(self,kind,at,payload):
        records=self.document['records'];row={'seq':len(records),'event_id':self.id(),'at':at,'process_id':self.process,'session_id':self.session,'kind':kind,'payload':payload,'previous_sha256':records[-1]['sha256'] if records else a.digest(self.entry)}
        row['sha256']=a.digest(row);records.append(row);return row
    def run_it(self,raw=None):
        return a.adjudicate(self.protocol,self.registry,self.raw if raw is None else raw,self.review,protocol_sha256=self.protocol_hash,evidence_dir=self.folder)
    def restart(self,at,config='baseline'):
        self.process=self.id();self.session=self.id();return self.event('app_start',at,{'config':self.protocol['baseline'] if config=='baseline' else config,'reason':'process_restart'})
    def test_startup_departure_remains_unknown_in_fixed_denominator(self):
        data,audit=self.run_it();report=study_report.summarize(self.protocol,data)
        self.assertEqual(report['registered_installs'],1);self.assertEqual(report['overall']['sessions']['unknown_outcomes'],1)
        self.assertEqual(report['overall']['retention'][2]['unresolved_return_status'],1)
        self.assertEqual(data['sessions'][0]['return_eligible'],False);self.assertFalse(audit['release_ready'])
    def test_actual_external_startup_crash_link_counts_without_return(self):
        proof=self.evidence(b'SYNTHETIC native startup crash report; not real observation')
        self.review['native_crashes']=[{'install_id':self.entry['install_id'],'session_id':self.session,'process_id':self.process,'crash_at':101,'report_sha256':proof,'linkage_reviewed':True}]
        data,_=self.run_it();report=study_report.summarize(self.protocol,data)
        self.assertEqual(report['overall']['sessions']['reported_crash_sessions'],1);self.assertFalse(data['sessions'][0]['return_eligible'])
        (self.folder/(proof+'.evidence')).unlink()
        with self.assertRaises(ValueError):self.run_it()
    def test_crash_cannot_be_invented_from_missing_terminal_or_stale_process(self):
        proof=self.evidence(b'fixture')
        self.review['native_crashes']=[{'install_id':self.entry['install_id'],'session_id':self.session,'process_id':'f'*32,'crash_at':101,'report_sha256':proof,'linkage_reviewed':True}]
        with self.assertRaises(ValueError):self.run_it()
    def test_interactive_and_foreground_activity_required_for_return(self):
        self.restart(30*86400+100);self.event('harbor_interactive',30*86400+101,{})
        data,_=self.run_it();self.assertFalse(data['sessions'][-1]['return_eligible'])
        self.event('activity',30*86400+102,{'activity':'interaction'})
        data,_=self.run_it();self.assertTrue(data['sessions'][-1]['return_eligible'])
        self.assertEqual(study_report.summarize(self.protocol,data)['overall']['retention'][2]['observed_returns'],1)
    def test_background_activity_and_spurious_inactivity_boundary_rejected(self):
        self.event('harbor_interactive',101,{});self.event('background',102,{});self.event('activity',103,{'activity':'interaction'})
        with self.assertRaises(ValueError):self.run_it()
        self.document['records']=self.document['records'][:1];self.session=self.id();self.event('session_start',200,{'config':self.protocol['baseline'],'reason':'inactivity'})
        with self.assertRaises(ValueError):self.run_it()
    def test_exact_thirty_minute_boundary_and_process_restarts(self):
        self.event('harbor_interactive',101,{});self.event('activity',102,{'activity':'interaction'})
        self.session=self.id();self.event('session_start',1902,{'config':self.protocol['baseline'],'reason':'inactivity'})
        self.event('harbor_interactive',1902,{});self.event('activity',1902,{'activity':'interaction'});self.restart(1903)
        data,_=self.run_it();self.assertEqual(len(data['sessions']),3);self.assertTrue(data['sessions'][1]['return_eligible'])
    def test_missing_config_keeps_authentic_session_but_not_return(self):
        self.restart(1000,None);self.event('harbor_interactive',1001,{});self.event('activity',1002,{'activity':'interaction'})
        data,audit=self.run_it();self.assertTrue(data['sessions'][-1]['valid']);self.assertFalse(data['sessions'][-1]['return_eligible']);self.assertEqual(audit['sessions_with_incomplete_config'],1)
        self.assertEqual(study_report.summarize(self.protocol,data)['overall']['sessions']['unknown_outcomes'],2)
    def test_config_label_cannot_disguise_changed_candidate(self):
        changed=copy.deepcopy(self.protocol['baseline']);changed['candidate_sha256']='f'*64;self.restart(1000,changed)
        with self.assertRaises(ValueError):self.run_it()
        self.document['records'].pop();changed['config']='fixture_v2';self.restart(1000,changed)
        data,_=self.run_it();self.assertEqual(data['sessions'][-1]['config'],'fixture_v2')
    def test_missing_raw_export_keeps_install_and_unknown_return(self):
        self.raw['exports']=[];data,audit=self.run_it();self.assertEqual(len(data['installs']),1);self.assertEqual(data['sessions'],[]);self.assertEqual(audit['missing_raw_exports'],1)
        self.assertEqual(study_report.summarize(self.protocol,data)['overall']['retention'][2]['unresolved_return_status'],1)
    def test_explicit_coverage_evidence_is_required_and_gaps_subtracted(self):
        self.event('gap',200,{'reason':'storageFailure','from':150,'to':200})
        evidence=self.evidence(b'SYNTHETIC independent recording coverage audit')
        self.review['installs'][0]['coverage']=[{'start':100,'end':300,'evidence_sha256':evidence}]
        data,_=self.run_it();self.assertEqual(data['installs'][0]['observable_intervals'],[[100,150],[200,300]])
        (self.folder/(evidence+'.evidence')).write_text('changed')
        with self.assertRaises(ValueError):self.run_it()
    def test_terminal_without_external_adjudication_remains_unknown(self):
        event=self.event('terminal',200,{'reason':'explicitlyObservedCleanExit'})
        data,_=self.run_it();self.assertIsNone(data['sessions'][0]['end'])
        evidence=self.evidence(b'SYNTHETIC terminal observation record')
        self.review['terminal_reviews']=[{'install_id':self.entry['install_id'],'session_id':self.session,'terminal_event_sha256':event['sha256'],'evidence_sha256':evidence}]
        data,_=self.run_it();self.assertEqual(data['sessions'][0]['end'],200)
    def test_withdrawal_erasure_never_manufactures_observed_nonreturn(self):
        self.document['registry']=None;self.document['records']=[];self.document['status']='withdrawn'
        evidence=self.evidence(b'coverage');self.review['installs'][0]['coverage']=[{'start':100,'end':self.review['cutoff'],'evidence_sha256':evidence}]
        data,audit=self.run_it();self.assertEqual(data['installs'][0]['observable_intervals'],[]);self.assertEqual(audit['withdrawn_exports'],1)
        self.assertEqual(study_report.summarize(self.protocol,data)['overall']['retention'][2]['unresolved_return_status'],1)
    def test_tamper_duplicate_replay_and_unknown_private_fields_rejected(self):
        for change in ('tamper','duplicate_export','replay','private'):
            with self.subTest(change=change):
                raw=copy.deepcopy(self.raw)
                if change=='tamper':raw['exports'][0]['raw']['records'][0]['at']=101
                elif change=='duplicate_export':raw['exports'].append(copy.deepcopy(raw['exports'][0]))
                elif change=='replay':raw['exports'][0]['raw']['records'].append(copy.deepcopy(raw['exports'][0]['raw']['records'][0]))
                else:raw['exports'][0]['raw']['registry']['email']='private-sentinel'
                with self.assertRaises(ValueError):self.run_it(raw)
    def test_wrapped_local_probe_hash_and_time_binding(self):
        wrapper={'schema_version':1,'raw':self.document,'eligibility_evidence':self.proof}
        (self.folder/(self.proof_hash+'.evidence')).unlink()
        self.assertEqual(len(self.run_it(wrapper)[0]['sessions']),1)
        wrapper=copy.deepcopy(wrapper);wrapper['eligibility_evidence']['checked_at']='2030-01-01T00:00:00Z'
        with self.assertRaises(ValueError):self.run_it(wrapper)
    def test_unqualified_enrollment_cannot_silently_remove_dropout(self):
        self.review['installs'][0]['eligibility_review']='unqualified'
        with self.assertRaises(ValueError):self.run_it()
        self.review['installs']=[]
        with self.assertRaises(ValueError):self.run_it()
    def test_actual_dart_generated_fixture_round_trip(self):
        root=ROOT/'release/study/fixtures/collection-v1'
        values={name:json.loads((root/(name+'.json')).read_text()) for name in ('protocol','registry','raw','review')}
        protocol_hash=hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()
        data,audit=a.adjudicate(**values,protocol_sha256=protocol_hash,evidence_dir=root/'evidence')
        report=study_report.summarize(values['protocol'],data)
        self.assertEqual(report['registered_installs'],3)
        self.assertEqual(report['overall']['sessions']['reported_crash_sessions'],1)
        self.assertEqual(report['overall']['sessions']['completed_without_reported_crash'],1)
        self.assertEqual(report['overall']['sessions']['unknown_outcomes'],1)
        self.assertEqual(report['overall']['retention'][2]['observed_returns'],1)
        self.assertEqual(report['overall']['retention'][2]['unresolved_return_status'],2)
        self.assertEqual(audit['missing_raw_exports'],1)
        self.assertTrue(all(not row['observable_intervals'] for row in data['installs']))

    def test_cli_pins_inputs_and_omits_ids_from_stdout_failure(self):
        paths={}
        for name,value in [('protocol',self.protocol),('registry',self.registry),('raw',self.raw),('review',self.review)]:
            path=self.folder/(name+'.json');path.write_text(json.dumps(value));paths[name]=path
        # Registry hashes exact bytes, so preserve the original protocol bytes.
        paths['protocol'].write_bytes((ROOT/'release/study/fixtures/synthetic-protocol.json').read_bytes())
        command=[sys.executable,str(ROOT/'tool/study_adjudicate.py')]
        for key,value in paths.items():command+=['--'+key,str(value)]
        command+=['--evidence-dir',str(self.folder),'--output-dir',str(self.folder/'out')]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertNotIn(self.entry['install_id'],result.stdout)
        audit=json.loads((self.folder/'out/adjudication.json').read_text());self.assertEqual(len(audit['inputs_sha256']),6)
        paths['raw'].write_text('{"email":"private-sentinel"}')
        result=subprocess.run(command,text=True,capture_output=True);self.assertEqual(result.returncode,2);self.assertNotIn('private-sentinel',result.stderr);self.assertNotIn('Traceback',result.stderr)

if __name__=='__main__':unittest.main()
