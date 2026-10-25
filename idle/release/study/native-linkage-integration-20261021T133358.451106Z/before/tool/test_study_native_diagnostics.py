"""Synthetic parser/binary fixtures only; no diagnostic or real-session acceptance."""
import copy
import importlib.util
import json
import io
import os
import zipfile
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

import study_native_diagnostics as n

ROOT=Path(__file__).resolve().parents[1]
# Explicit author override only. Clean candidates always exercise integrated code.
_staged=os.environ.get('TIDEGLASS_STAGED_ADJUDICATOR')
if _staged:
    spec=importlib.util.spec_from_file_location('staged_native_adjudicator',Path(_staged))
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
else:
    import study_adjudicate as decoder


def macho(identity):
    return struct.pack('<IiiIIIII',0xfeedfacf,0x100000c,0,2,1,24,0,0)+struct.pack('<II',0x1b,24)+bytes.fromhex(identity)


def elf(identity):
    description=bytes.fromhex(identity);note=struct.pack('<III',4,len(description),3)+b'GNU\0'+description
    note+=b'\0'*((-len(note))%4)
    header=bytearray(64);header[:7]=b'\x7fELF\x02\x01\x01';struct.pack_into('<Q',header,32,64);struct.pack_into('<HH',header,54,56,1)
    segment=struct.pack('<IIQQQQQQ',4,0,120,0,0,len(note),len(note),4)
    return bytes(header)+segment+note


class NativeDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.binary='123456781234123412341234567890ab'
        self.context={'version':1,'status':'available','source':'native_process_observation_v1','native_pid':123,'platform':'ios',
            'application_id':'dev.tideglass.game','application_version':'1.0.0','application_build':'1',
            'observed_start_utc_ms':100000}
        self.config={'candidate_sha256':'a'*64,'economy_sha256':'b'*64,'content_sha256':'c'*64,'config':'synthetic_native'}
        self.registry={'install_id':'1'*32,'first_launch':100,'enrolled_at':100,'synthetic':True,'platform':'ios',
            'baseline':self.config,'acquisition':'internal_test','study_id':'synthetic_native','protocol_sha256':'d'*64,
            'information_sha256':'e'*64,'consent_version':'synthetic_v2','eligibility_evidence_sha256':'f'*64,'device_group':'phone_large'}
        self.raw={'schema_version':2,'registry':self.registry,'status':'active','records':[]}
        self.event('app_start',100,{'config':self.config,'reason':'enrollment','native_context':self.context})
        self.report={'pid':123,'procLaunch':'1970-01-01T00:01:39Z','captureTime':'1970-01-01T00:01:50Z','incident':'synthetic-incident-1',
            'bundleInfo':{'CFBundleIdentifier':'dev.tideglass.game','CFBundleShortVersionString':'1.0.0','CFBundleVersion':'1'},
            'exception':{'type':'EXC_BAD_ACCESS','signal':'SIGSEGV'},'termination':{'namespace':'SIGNAL'},
            'usedImages':[{'name':'App','uuid':self.binary}]}
        self.manifest={'schema_version':1,'kind':'tideglass_native_release_manifest','candidate_sha256':'a'*64,'build_mode':'release','code_mode':'aot','binaries':[
            {'platform':'ios','application_id':'dev.tideglass.game','application_version':'1.0.0','application_build':'1',
             'binary_role':'dart_aot_app_code','binary_path':'Runner.app/Frameworks/App.framework/App','binary_name':'App','binary_id_kind':'macho_uuid','binary_id':self.binary,'binary_sha256':self.save(macho(self.binary))}]}
        self.source=self.save(b'INTERNAL SYNTHETIC independently supplied installation-evidence fixture; no real device')
        self.proof={'schema_version':1,'kind':'native_installation_provenance','install_id':'1'*32,'platform':'ios',
            'application_id':'dev.tideglass.game','application_version':'1.0.0','application_build':'1','candidate_sha256':'a'*64,
            'report_sha256':'','raw_document_sha256':'','observed_from_ms':99000,'observed_through_ms':200000,'source_evidence_sha256':[self.source]}

    def save(self,raw):
        ref=n.digest(raw);(self.folder/(ref+'.evidence')).write_bytes(raw);return ref
    def event(self,kind,at,payload,process='3'*32,session='4'*32):
        records=self.raw['records'];row={'seq':len(records),'event_id':f'{len(records)+10:032x}','at':at,'process_id':process,'session_id':session,
            'kind':kind,'payload':payload,'previous_sha256':records[-1]['sha256'] if records else decoder.digest(self.registry)}
        row['sha256']=decoder.digest(row);records.append(row);return row
    def rehash(self):
        previous=decoder.digest(self.registry)
        for i,row in enumerate(self.raw['records']):
            row['seq']=i;row['previous_sha256']=previous;row['sha256']=decoder.digest({k:v for k,v in row.items() if k!='sha256'});previous=row['sha256']
    def apple(self):return json.dumps({'bug_type':'309'}).encode()+b'\n'+json.dumps(self.report).encode()
    def package(self):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as archive:
            for row in self.manifest['binaries']:
                archive.writestr(row['binary_path'],n.evidence_bytes(self.folder,row['binary_sha256'],binary=True))
        self.manifest['artifact_sha256']=self.save(buffer.getvalue())
        build={'schema_version':1,'kind':'native_release_build_provenance',
               **{k:self.manifest[k] for k in ('candidate_sha256','artifact_sha256','build_mode','code_mode')},
               'build_log_sha256':self.save(b'SYNTHETIC release build log only; not a compiled artifact')}
        self.manifest['build_provenance_sha256']=self.save(n.canonical(build).encode())
    def run_match(self,report=None,proof_change=None,pack=True):
        if pack:self.package()
        data=self.apple() if report is None else report
        report_ref=self.save(data);manifest_ref=self.save(n.canonical(self.manifest).encode())
        proof=dict(self.proof,report_sha256=report_ref,raw_document_sha256=n.digest(n.canonical(self.raw).encode()))
        if proof_change:proof.update(proof_change)
        proof_ref=self.save(n.canonical(proof).encode())
        self.references={'report_sha256':report_ref,'manifest_sha256':manifest_ref,'provenance_sha256':proof_ref}
        sessions=decoder.decode_records(self.raw,self.registry,4000)[0]
        return n.match_diagnostic(raw_document=self.raw,sessions=sessions,report_sha256=report_ref,manifest_sha256=manifest_ref,
            provenance_sha256=proof_ref,evidence_dir=self.folder)

    def test_available_and_unavailable_context_bounds(self):
        self.assertEqual(n.observation(self.context),self.context)
        self.assertEqual(n.observation({'version':1,'status':'unavailable','reason':'consent_not_granted'})['status'],'unavailable')
        for key,value in [('version',1.0),('native_pid',True),('native_pid',0),('application_id','bad space'),('observed_start_utc_ms',-1),('application_build','x'*81)]:
            with self.subTest(key=key),self.assertRaises(ValueError):n.observation(dict(self.context,**{key:value}))
        with self.assertRaises(ValueError):n.observation(dict(self.context,email='synthetic-private'))
        with self.assertRaises(ValueError):n.observation(dict(self.context,observed_elapsed_us=5000000))

    def test_actual_binary_parser_extracts_ids_from_bytes(self):
        self.assertEqual(n.binary_ids(macho(self.binary),'macho_uuid'),{self.binary})
        self.assertEqual(n.binary_ids(elf(self.binary),'elf_build_id'),{self.binary})
        with self.assertRaises(ValueError):n.binary_ids(macho(self.binary)[:-1],'macho_uuid')
        with self.assertRaises(ValueError):n.binary_ids(b'synthetic nonbinary','elf_build_id')

    def test_apple_supported_fatal_links_exact_process_and_session(self):
        result=self.run_match();self.assertEqual(result['status'],'linked');self.assertEqual(result['process_id'],'3'*32);self.assertEqual(result['session_id'],'4'*32)

    def test_missing_launch_time_build_or_diagnostic_remains_unknown(self):
        for field in ('procLaunch','captureTime','bundleInfo','pid','usedImages'):
            report=copy.deepcopy(self.report);del report[field]
            data=json.dumps({'bug_type':'309'}).encode()+b'\n'+json.dumps(report).encode()
            with self.subTest(field=field):self.assertEqual(self.run_match(data)['status'],'unknown')
        self.assertEqual(self.run_match(b'no native diagnostic')['status'],'unknown')

    def test_simulated_kill_lifecycle_and_flutter_error_never_become_native_crash(self):
        for change in [dict(isSimulated=True),dict(exception={'type':'EXC_CRASH','signal':'SIGKILL'}),dict(termination={'namespace':'RUNNINGBOARD'})]:
            report=dict(self.report,**change);data=json.dumps({'bug_type':'309'}).encode()+b'\n'+json.dumps(report).encode()
            self.assertEqual(self.run_match(data)['status'],'unknown')
        for text in [b'AppLifecycleState.detached',b'flutter: Unhandled Exception: synthetic',b'host SIGKILL pid123']:
            self.assertEqual(self.run_match(text)['status'],'unknown')

    def test_pid_reuse_and_multiple_process_observations_rejected(self):
        observed=dict(self.context,observed_start_utc_ms=101000)
        self.event('app_start',101,{'config':self.config,'reason':'process_restart','native_context':observed},process='5'*32,session='6'*32)
        self.assertEqual(self.run_match()['reason'],'ambiguous_or_missing_process_link')
        # A genuinely later native launch excludes the first PID's old observation.
        self.report['procLaunch']='1970-01-01T00:01:40.500Z'
        result=self.run_match();self.assertEqual(result['status'],'linked');self.assertEqual(result['process_id'],'5'*32)

    def test_inactivity_session_shares_native_process_and_resolves_exact_interval(self):
        self.event('harbor_interactive',100,{})
        self.event('session_start',1900,{'config':self.config,'reason':'inactivity'},session='6'*32)
        self.event('harbor_interactive',1900,{},session='6'*32)
        self.report['captureTime']='1970-01-01T00:31:41Z';self.proof['observed_through_ms']=2000000
        result=self.run_match();self.assertEqual(result['status'],'linked');self.assertEqual(result['session_id'],'6'*32)

    def test_wrong_candidate_app_build_or_binary_bytes_cannot_link(self):
        for field,value in [('candidate_sha256','d'*64),('application_id','other.app'),('application_build','2')]:
            with self.subTest(field=field):self.assertEqual(self.run_match(proof_change={field:value})['status'],'unknown')
        self.manifest['binaries'][0]['binary_sha256']=self.save(macho('f'*32))
        self.assertEqual(self.run_match()['reason'],'binary_identity_mismatch')

    def test_independent_provenance_and_exact_raw_hash_are_required(self):
        for change in [dict(source_evidence_sha256=[]),dict(raw_document_sha256='d'*64),dict(install_id='f'*32),dict(observed_from_ms=120000)]:
            self.assertEqual(self.run_match(proof_change=change)['status'],'unknown')
        (self.folder/(self.source+'.evidence')).write_bytes(b'changed')
        self.assertEqual(self.run_match()['reason'],'changed_evidence')

    def test_boolean_review_cannot_replace_required_evidence(self):
        self.assertEqual(self.run_match(proof_change={'linkage_reviewed':True})['status'],'unknown')

    def test_clock_gap_rejects_otherwise_matching_native_report(self):
        self.event('gap',105,{'reason':'clockDiscontinuity','from':102,'to':None});self.raw['status']='exhausted'
        self.assertEqual(self.run_match()['reason'],'uncertain_observation_interval')

    def test_capacity_gap_cannot_claim_a_unique_later_session(self):
        self.event('gap',105,{'reason':'capacity','from':105,'to':None});self.raw['status']='exhausted'
        self.assertEqual(self.run_match()['reason'],'uncertain_observation_interval')

    def test_native_schema_migration_preserves_legacy_event_and_cannot_downgrade(self):
        first=self.raw['records'][0];del first['payload']['native_context'];self.raw['schema_version']=1;self.rehash();original=n.canonical(first)
        self.assertEqual(len(decoder.decode_records(self.raw,self.registry,4000)[0]),1)
        self.raw['schema_version']=2
        self.event('app_start',101,{'config':self.config,'reason':'process_restart','native_context':dict(self.context,observed_start_utc_ms=101000)},process='5'*32,session='6'*32)
        self.assertEqual(n.canonical(first),original);self.assertEqual(len(decoder.decode_records(self.raw,self.registry,4000)[0]),2)
        self.event('app_start',102,{'config':self.config,'reason':'process_restart'},process='7'*32,session='8'*32)
        with self.assertRaisesRegex(ValueError,'Legacy start'):decoder.decode_records(self.raw,self.registry,4000)

    def test_unavailable_context_requires_atomic_gap_and_remains_unknown(self):
        self.raw['records'][0]['payload']['native_context']={'version':1,'status':'unavailable','reason':'native_unavailable'};self.rehash()
        with self.assertRaisesRegex(ValueError,'atomic native'):decoder.decode_records(self.raw,self.registry,4000)
        self.event('gap',100,{'reason':'instrumentationUnavailable','from':100,'to':100})
        self.assertEqual(self.run_match()['status'],'unknown')

    def test_android_tombstone_requires_uptime_and_real_elf_identity(self):
        self.context['platform']='android';self.registry['platform']='android';self.rehash()
        self.manifest['binaries'][0].update(platform='android',binary_name='libapp.so',binary_path='base/lib/arm64-v8a/libapp.so',binary_id_kind='elf_build_id',binary_sha256=self.save(elf(self.binary)))
        self.proof['platform']='android'
        report=('Timestamp: 1970-01-01T00:01:50+00:00\nProcess uptime: 11s\n'
                'pid: 123, tid: 123, name: game  >>> dev.tideglass.game <<<\n'
                'signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0\n'
                '    #00 pc 00001 /data/app/lib/arm64/libapp.so (BuildId: '+self.binary+')\n').encode()
        self.assertEqual(self.run_match(report)['status'],'linked')
        self.assertEqual(self.run_match(report.replace(b'Process uptime: 11s\n',b''))['status'],'unknown')
        self.assertEqual(self.run_match(report.replace(b'11 (SIGSEGV)',b'9 (SIGKILL)'))['status'],'unknown')

    def test_shared_launcher_identity_across_candidates_never_links(self):
        self.report['usedImages']=[{'name':'Runner','uuid':self.binary},{'name':'Flutter','uuid':'f'*32}]
        row=self.manifest['binaries'][0]
        row.update(binary_name='Runner',binary_path='Runner.app/Runner',binary_role='launcher')
        for candidate in ['a'*64,'d'*64]:
            self.manifest['candidate_sha256']=candidate
            self.config['candidate_sha256']=candidate;self.rehash()
            result=self.run_match(proof_change={'candidate_sha256':candidate})
            self.assertEqual(result['status'],'unknown');self.assertEqual(result['reason'],'not_app_code_image')

    def test_debug_profile_or_missing_aot_provenance_never_links(self):
        for key,value in [('build_mode','debug'),('build_mode','profile'),('code_mode','jit')]:
            original=self.manifest[key];self.manifest[key]=value
            self.assertEqual(self.run_match()['reason'],'unqualified_code_mode');self.manifest[key]=original
        self.package();self.manifest['build_provenance_sha256']=self.source
        self.assertEqual(self.run_match(pack=False)['status'],'unknown')

    def test_actual_packaged_binary_and_build_provenance_are_bound(self):
        self.package()
        self.manifest['binaries'][0]['binary_sha256']=self.save(macho('e'*32))
        self.assertEqual(self.run_match(pack=False)['reason'],'packaged_binary_mismatch')
        self.package()
        provenance=n.json_document(n.evidence_bytes(self.folder,self.manifest['build_provenance_sha256']))
        provenance['candidate_sha256']='d'*64
        self.manifest['build_provenance_sha256']=self.save(n.canonical(provenance).encode())
        self.assertEqual(self.run_match(pack=False)['reason'],'build_provenance_mismatch')

    def test_full_schema2_adjudication_links_once_and_rejects_duplicate_reports(self):
        protocol=json.loads((ROOT/'release/study/fixtures/synthetic-protocol.json').read_text())
        protocol['study_id']='synthetic_native';protocol['baseline']=self.config
        protocol_hash=n.digest(n.canonical(protocol).encode())
        eligibility={'schema_version':1,'check':'no_prior_game_directory_entries','checked_at':'1970-01-01T00:01:39.000Z',
                     'study_id':protocol['study_id'],'candidate_sha256':self.config['candidate_sha256']}
        eligibility_hash=self.save(n.canonical(eligibility).encode())
        self.registry.update(protocol_sha256=protocol_hash,eligibility_evidence_sha256=eligibility_hash);self.rehash()
        self.assertEqual(self.run_match()['status'],'linked')
        fixed={'schema_version':1,'study_id':protocol['study_id'],'synthetic':True,'entries':[self.registry]}
        raw={'schema_version':1,'study_id':protocol['study_id'],'synthetic':True,'exports':[{'install_id':self.registry['install_id'],'raw':self.raw}]}
        review={'schema_version':1,'study_id':protocol['study_id'],'synthetic':True,'cutoff':32*86400,
                'installs':[{'install_id':self.registry['install_id'],'eligibility_review':'qualified',
                  'eligibility_evidence_sha256':eligibility_hash,'exclusion':None,'coverage':[]}],
                'native_crashes':[dict(install_id=self.registry['install_id'],**self.references)],'terminal_reviews':[]}
        data,audit=decoder.adjudicate(protocol,fixed,raw,review,protocol_sha256=protocol_hash,evidence_dir=self.folder)
        self.assertEqual(audit['externally_linked_crash_records'],1);self.assertTrue(data['sessions'][0]['crashed'])
        self.assertFalse(audit['release_ready']);self.assertEqual(audit['status'],'synthetic_adjudication')
        review['native_crashes']*=2
        with self.assertRaisesRegex(ValueError,'Duplicate diagnostic report'):
            decoder.adjudicate(protocol,fixed,raw,review,protocol_sha256=protocol_hash,evidence_dir=self.folder)

    def test_direct_matcher_rejects_raw_chain_changes_and_legacy_without_context(self):
        self.assertEqual(self.run_match()['status'],'linked')
        sessions=decoder.decode_records(self.raw,self.registry,4000)[0]
        self.raw['records'][0]['at']=101
        result=n.match_diagnostic(raw_document=self.raw,sessions=sessions,evidence_dir=self.folder,**self.references)
        self.assertEqual(result['reason'],'broken_raw_chain')
        self.raw['schema_version']=1
        result=n.match_diagnostic(raw_document=self.raw,sessions=sessions,evidence_dir=self.folder,**self.references)
        self.assertEqual(result['reason'],'native_context_not_recorded')

    def test_actual_dart_migration_examples_preserve_prior_chain_and_erase_context(self):
        folder=Path(os.environ.get('TIDEGLASS_NATIVE_FIXTURES',ROOT/'release/study/fixtures/native-linkage-v2'))
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertIs(manifest['synthetic'],True)
        values={}
        for name,expected in manifest['sha256'].items():
            self.assertIn(name,{'legacy-before.json','migrated-available.json','unavailable.json','withdrawn.json'})
            raw=(folder/name).read_bytes();self.assertEqual(n.digest(raw),expected);values[name]=json.loads(raw)
        before=values['legacy-before.json'];after=values['migrated-available.json']
        self.assertEqual(n.canonical(before['registry']),n.canonical(after['registry']))
        self.assertEqual(n.canonical(before['records'][0]),n.canonical(after['records'][0]))
        for name,count in [('legacy-before.json',1),('migrated-available.json',2),('unavailable.json',3)]:
            self.assertEqual(len(decoder.decode_records(values[name],before['registry'],4000)[0]),count)
        self.assertEqual(decoder.decode_records(values['withdrawn.json'],before['registry'],4000),([],[],True))
        self.assertNotIn('native_pid',n.canonical(values['withdrawn.json']))

    def test_duplicate_json_keys_and_oversize_are_rejected(self):
        data=b'{"bug_type":"309","bug_type":"309"}\n'+json.dumps(self.report).encode()
        self.assertEqual(self.run_match(data)['status'],'unknown')
        with self.assertRaises(ValueError):n.json_document(b' '*(n.MAX_REPORT+1))


if __name__=='__main__':unittest.main()
