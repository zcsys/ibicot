#!/usr/bin/env python3
"""Fail-closed native diagnostic linkage; never infers a crash from disappearance.

Inputs are independently supplied evidence. Hashes detect replacement, not forged
operator provenance. This module does not collect logs, recruit, or accept a release.
"""
from __future__ import annotations
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile

MAX_REPORT = 8 * 1024 * 1024
MAX_BINARY = 256 * 1024 * 1024
HASH = re.compile(r'^[a-f0-9]{64}$')
OPAQUE = re.compile(r'^[a-f0-9]{32}$')
TOKEN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.+-]{0,79}$')
PACKAGE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$')
REASONS = {'unsupported_platform','native_unavailable','invalid_native_context','not_requested','consent_not_granted'}


class LinkageError(ValueError):
    pass


def require(value, reason):
    if not value:
        raise LinkageError(reason)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def exact(value, keys):
    require(isinstance(value,dict) and set(value)==set(keys),'invalid_fields')


def integer(value, minimum=0, maximum=9007199254740991):
    return type(value) is int and minimum<=value<=maximum


def observation(value):
    require(isinstance(value,dict) and type(value.get('version')) is int and value['version']==1,'invalid_native_context')
    if value.get('status')=='unavailable':
        exact(value,{'version','status','reason'});require(value['reason'] in REASONS,'invalid_native_context')
        return value
    exact(value,{'version','status','source','native_pid','platform','application_id','application_version','application_build','observed_start_utc_ms'})
    require(value['status']=='available' and value['source']=='native_process_observation_v1','invalid_native_context')
    require(integer(value['native_pid'],2,2147483647) and value['platform'] in {'ios','android'},'invalid_native_context')
    require(isinstance(value['application_id'],str) and PACKAGE.fullmatch(value['application_id']),'invalid_native_context')
    require(all(isinstance(value[k],str) and TOKEN.fullmatch(value[k]) for k in ('application_version','application_build')),'invalid_native_context')
    require(integer(value['observed_start_utc_ms']),'invalid_native_context')
    require(len(canonical(value).encode())<=2048,'native_context_oversize')
    return value


def unique_object(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'duplicate_json_key');result[key]=value
    return result


def json_document(raw):
    require(0<len(raw)<=MAX_REPORT,'diagnostic_size')
    return json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _: (_ for _ in ()).throw(LinkageError('invalid_number')))


def instant(value):
    require(isinstance(value,str),'missing_native_time')
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(parsed.tzinfo is not None,'ambiguous_native_time')
    result=int(parsed.timestamp()*1000)
    require(integer(result),'invalid_native_time')
    return result


def native_id(value):
    require(isinstance(value,str),'missing_native_binary_id')
    result=value.replace('-','').lower()
    require(bool(re.fullmatch(r'[a-f0-9]{16,128}',result)),'invalid_native_binary_id')
    return result


def parse_apple(raw):
    require(0<len(raw)<=MAX_REPORT,'diagnostic_size')
    parts=raw.split(b'\n',1);require(len(parts)==2,'unsupported_apple_report')
    metadata=json_document(parts[0]);body=json_document(parts[1])
    require(isinstance(metadata,dict) and str(metadata.get('bug_type'))=='309','unsupported_apple_report')
    require(isinstance(body,dict),'unsupported_apple_report')
    simulated=body.get('isSimulated',False)
    require(simulated in (False,0,'false','0'),'simulated_not_crash')
    exception=body.get('exception',{});termination=body.get('termination',{})
    require(isinstance(exception,dict) and isinstance(termination,dict),'unsupported_exception')
    require(exception.get('type') in {'EXC_BAD_ACCESS','EXC_BAD_INSTRUCTION','EXC_ARITHMETIC','EXC_CRASH'}
            and exception.get('signal') in {'SIGSEGV','SIGBUS','SIGILL','SIGFPE','SIGABRT'},'not_supported_native_fatal')
    require(termination.get('namespace') not in {'FRONTBOARD','RUNNINGBOARD','JETSAM','SPRINGBOARD','WATCHDOG'},'os_termination_not_native_fatal')
    bundle=body.get('bundleInfo',{});require(isinstance(bundle,dict),'missing_native_build')
    require(all(isinstance(bundle.get(k),str) and bundle[k] for k in ('CFBundleIdentifier','CFBundleShortVersionString','CFBundleVersion')),'missing_native_build')
    launched=instant(body.get('procLaunch'));crashed=instant(body.get('captureTime'))
    require(launched<=crashed and integer(body.get('pid'),2,2147483647),'invalid_process_interval')
    incident=body.get('incident');require(isinstance(incident,str) and re.fullmatch(r'[A-Za-z0-9-]{8,80}',incident),'missing_incident')
    images=body.get('usedImages');require(isinstance(images,list) and len(images)<=4096,'missing_binary_images')
    binaries=[]
    for image in images:
        if isinstance(image,dict) and image.get('uuid'):
            name=image.get('name') or Path(image.get('path','')).name
            if isinstance(name,str) and name:
                binaries.append({'name':name,'id':native_id(image['uuid']),'kind':'macho_uuid'})
    require(binaries,'missing_binary_images')
    return {'platform':'ios','application_id':bundle['CFBundleIdentifier'],'application_version':bundle['CFBundleShortVersionString'],
            'application_build':bundle['CFBundleVersion'],'native_pid':body['pid'],'launch_earliest_ms':launched,'launch_latest_ms':launched,
            'crash_ms':crashed,'incident':incident,'binaries':binaries,'report_sha256':digest(raw),'classification':'native_fatal'}


def parse_android(raw):
    require(0<len(raw)<=MAX_REPORT,'diagnostic_size');text=raw.decode('utf-8')
    def one(pattern):
        matches=re.findall(pattern,text,re.M);require(len(matches)==1,'ambiguous_or_missing_native_field');return matches[0]
    pid,app=one(r'^pid:\s*(\d+),\s*tid:\s*\d+,.*>>> ([A-Za-z0-9_.-]+) <<<$')
    sig,signal_name=one(r'^signal (\d+) \((SIG[A-Z]+)\),.*$')
    require((int(sig),signal_name) in {(6,'SIGABRT'),(11,'SIGSEGV'),(7,'SIGBUS'),(4,'SIGILL'),(8,'SIGFPE')},'not_supported_native_fatal')
    stamp=one(r'^Timestamp: (.+)$');crashed=instant(stamp)
    uptime=int(one(r'^Process uptime: (\d+)s$'))
    require(0<=uptime<=366*86400,'invalid_process_uptime')
    binaries=[]
    for path,binary in re.findall(r'^\s*#\d+\s+pc\s+[a-fA-F0-9]+\s+(\S+).*\(BuildId:\s*([a-fA-F0-9]+)\)\s*$',text,re.M):
        binaries.append({'name':Path(path).name,'id':native_id(binary),'kind':'elf_build_id'})
    require(binaries,'missing_native_binary_id')
    require(integer(int(pid),2,2147483647),'invalid_native_pid')
    # Integer uptime gives a bounded one-second launch interval, never an exact
    # invented launch instant. Missing uptime remains unlinked.
    return {'platform':'android','application_id':app,'application_version':None,'application_build':None,'native_pid':int(pid),
            'launch_earliest_ms':max(0,crashed-(uptime+1)*1000),'launch_latest_ms':crashed-uptime*1000,
            'crash_ms':crashed,'incident':digest(raw),'binaries':binaries,'report_sha256':digest(raw),'classification':'native_fatal'}


def binary_ids(raw, kind):
    """Extract UUID/build-id from actual bounded binary bytes, not a manifest claim."""
    require(0<len(raw)<=MAX_BINARY,'binary_size')
    found=set()
    if kind=='macho_uuid':
        def macho(data,depth=0):
            require(depth<=1 and len(data)>=4,'unsupported_macho')
            big=struct.unpack_from('>I',data)[0]
            if big in (0xcafebabe,0xcafebabf):
                count=struct.unpack_from('>I',data,4)[0];require(0<count<=32,'invalid_fat_macho')
                width=32 if big==0xcafebabf else 20
                require(8+count*width<=len(data),'invalid_fat_macho')
                for i in range(count):
                    at=8+i*width
                    offset,size=(struct.unpack_from('>QQ',data,at+8) if width==32 else struct.unpack_from('>II',data,at+8))
                    require(size>0 and offset+size<=len(data),'invalid_macho_slice');macho(data[offset:offset+size],depth+1)
                return
            magic=struct.unpack_from('<I',data)[0];require(magic in (0xfeedface,0xfeedfacf),'unsupported_macho')
            header=32 if magic==0xfeedfacf else 28;require(len(data)>=header,'invalid_macho_header')
            count,size=struct.unpack_from('<II',data,16);require(count<=65536 and header+size<=len(data),'invalid_macho_commands')
            at=header
            for _ in range(count):
                require(at+8<=header+size,'invalid_macho_command');command,length=struct.unpack_from('<II',data,at)
                require(length>=8 and at+length<=header+size,'invalid_macho_command')
                if command==0x1b:
                    require(length==24,'invalid_macho_uuid');found.add(data[at+8:at+24].hex())
                at+=length
            require(at==header+size,'invalid_macho_commands')
        macho(raw)
    elif kind=='elf_build_id':
        require(raw[:4]==b'\x7fELF' and len(raw)>=52 and raw[5]==1,'unsupported_elf')
        bits=raw[4];require(bits in (1,2),'unsupported_elf')
        if bits==2:
            require(len(raw)>=64,'invalid_elf_header');offset=struct.unpack_from('<Q',raw,32)[0];width,count=struct.unpack_from('<HH',raw,54)
            minimum=56
        else:
            offset=struct.unpack_from('<I',raw,28)[0];width,count=struct.unpack_from('<HH',raw,42);minimum=32
        require(width>=minimum and count<=65536 and offset+width*count<=len(raw),'invalid_elf_segments')
        for i in range(count):
            at=offset+i*width
            if struct.unpack_from('<I',raw,at)[0]!=4:continue
            start=struct.unpack_from('<Q' if bits==2 else '<I',raw,at+(8 if bits==2 else 4))[0]
            size=struct.unpack_from('<Q' if bits==2 else '<I',raw,at+(32 if bits==2 else 16))[0]
            require(start+size<=len(raw),'invalid_elf_note');cursor=start
            while cursor+12<=start+size:
                names,description,note=struct.unpack_from('<III',raw,cursor);cursor+=12
                name_end=cursor+names;desc_start=(name_end+3)&~3;desc_end=desc_start+description
                require(desc_end<=start+size,'invalid_elf_note')
                if raw[cursor:name_end]==b'GNU\x00' and note==3:
                    require(8<=description<=64,'invalid_elf_build_id');found.add(raw[desc_start:desc_end].hex())
                cursor=(desc_end+3)&~3
    else:raise LinkageError('unsupported_binary_format')
    require(found,'missing_binary_identity');return found


def evidence_bytes(folder, reference, *, binary=False):
    require(isinstance(reference,str) and HASH.fullmatch(reference),'invalid_evidence_reference')
    path=Path(folder)/(reference+'.evidence')
    require(not path.is_symlink() and path.is_file(),'missing_evidence')
    require(path.stat().st_size<=(MAX_BINARY if binary else MAX_REPORT),'evidence_size')
    raw=path.read_bytes();require(digest(raw)==reference,'changed_evidence');return raw


def release_match(manifest, native, context, folder):
    exact(manifest,{'schema_version','kind','candidate_sha256','build_mode','code_mode',
                    'artifact_sha256','build_provenance_sha256','binaries'})
    require(type(manifest['schema_version']) is int and manifest['schema_version']==1 and
            manifest['kind']=='tideglass_native_release_manifest','invalid_release_manifest')
    require(manifest['build_mode']=='release' and manifest['code_mode']=='aot','unqualified_code_mode')
    require(isinstance(manifest['candidate_sha256'],str) and HASH.fullmatch(manifest['candidate_sha256']),'invalid_release_candidate')
    require(isinstance(manifest['binaries'],list) and 0<len(manifest['binaries'])<=32,'invalid_release_binaries')
    provenance=json_document(evidence_bytes(folder,manifest['build_provenance_sha256']))
    exact(provenance,{'schema_version','kind','candidate_sha256','artifact_sha256','build_mode','code_mode','build_log_sha256'})
    require(type(provenance['schema_version']) is int and provenance['schema_version']==1 and
            provenance['kind']=='native_release_build_provenance','invalid_build_provenance')
    require(all(provenance[k]==manifest[k] for k in ('candidate_sha256','artifact_sha256','build_mode','code_mode')),'build_provenance_mismatch')
    evidence_bytes(folder,provenance['build_log_sha256'])
    archive=evidence_bytes(folder,manifest['artifact_sha256'],binary=True)
    matches=[]
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        entries=package.infolist()
        require(len(entries)<=100000,'release_archive_oversize')
        for row in manifest['binaries']:
            exact(row,{'platform','application_id','application_version','application_build','binary_role','binary_path',
                       'binary_name','binary_id_kind','binary_id','binary_sha256'})
            if any(row[k]!=context[k] for k in ('platform','application_id','application_version','application_build')):continue
            if any(native[k] is not None and native[k]!=row[k] for k in ('application_version','application_build')):continue
            # A launcher/engine UUID can survive Dart-only changes. Only the
            # packaged release AOT app-code image can identify this candidate.
            require(row['binary_role']=='dart_aot_app_code','not_app_code_image')
            if row['platform']=='ios':
                require(row['binary_name']=='App' and row['binary_id_kind']=='macho_uuid' and
                        bool(re.fullmatch(r'(?:Payload/)?[A-Za-z0-9_-]+[.]app/Frameworks/App[.]framework/App',row['binary_path'])),
                        'not_app_code_image')
            else:
                require(row['platform']=='android' and row['binary_name']=='libapp.so' and row['binary_id_kind']=='elf_build_id' and
                        bool(re.fullmatch(r'(?:base/)?lib/(?:arm64-v8a|armeabi-v7a|x86_64)/libapp[.]so',row['binary_path'])),
                        'not_app_code_image')
            identity=native_id(row['binary_id'])
            if not any(image=={'name':row['binary_name'],'id':identity,'kind':row['binary_id_kind']} for image in native['binaries']):continue
            selected=[entry for entry in entries if entry.filename==row['binary_path']]
            require(len(selected)==1 and 0<selected[0].file_size<=MAX_BINARY and
                    (selected[0].external_attr>>16)&0o170000 != 0o120000,'invalid_app_code_member')
            actual=evidence_bytes(folder,row['binary_sha256'],binary=True)
            require(digest(package.read(selected[0]))==digest(actual),'packaged_binary_mismatch')
            require(identity in binary_ids(actual,row['binary_id_kind']),'binary_identity_mismatch')
            matches.append(row)
    require(len(matches)==1,'ambiguous_or_missing_release_binary')
    return matches[0]


def checked_chain(raw_document):
    """Defence in depth; full semantic decoding precedes this internal matcher."""
    require(isinstance(raw_document,dict) and type(raw_document.get('schema_version')) is int and raw_document['schema_version']==2,'native_context_not_recorded')
    require(raw_document.get('status')!='withdrawn','withdrawn_native_linkage')
    registry=raw_document.get('registry');records=raw_document.get('records')
    require(isinstance(registry,dict) and isinstance(records,list) and 0<len(records)<=100000,'invalid_raw_document')
    previous=digest(canonical(registry).encode());seen=set()
    for index,event in enumerate(records):
        require(isinstance(event,dict) and event.get('seq')==index and event.get('previous_sha256')==previous,'broken_raw_chain')
        require(event.get('event_id') not in seen,'duplicate_raw_event');seen.add(event.get('event_id'))
        claimed=event.get('sha256');core={k:v for k,v in event.items() if k!='sha256'}
        require(claimed==digest(canonical(core).encode()),'broken_raw_chain');previous=claimed


def match_diagnostic(*, raw_document, sessions, report_sha256, manifest_sha256, provenance_sha256, evidence_dir):
    """Return one supported process/session link or unknown; no boolean bypass."""
    try:
        checked_chain(raw_document)
        raw=evidence_bytes(evidence_dir,report_sha256)
        native=parse_apple(raw) if raw.lstrip().startswith(b'{') else parse_android(raw)
        manifest=json_document(evidence_bytes(evidence_dir,manifest_sha256))
        proof=json_document(evidence_bytes(evidence_dir,provenance_sha256))
        exact(proof,{'schema_version','kind','install_id','platform','application_id','application_version','application_build','candidate_sha256',
                     'report_sha256','raw_document_sha256','observed_from_ms','observed_through_ms','source_evidence_sha256'})
        require(type(proof['schema_version']) is int and proof['schema_version']==1 and proof['kind']=='native_installation_provenance','invalid_installation_provenance')
        require(proof['report_sha256']==report_sha256 and proof['raw_document_sha256']==digest(canonical(raw_document).encode()),'provenance_input_mismatch')
        registry=raw_document.get('registry');require(isinstance(registry,dict) and proof['install_id']==registry['install_id'],'installation_mismatch')
        require(integer(proof['observed_from_ms']) and integer(proof['observed_through_ms']) and proof['observed_from_ms']<=proof['observed_through_ms'],'invalid_provenance_interval')
        refs=proof['source_evidence_sha256'];require(isinstance(refs,list) and 0<len(refs)<=16 and len(set(refs))==len(refs),'missing_installation_evidence')
        require(all(ref not in {report_sha256,manifest_sha256,provenance_sha256} for ref in refs),'self_referential_provenance')
        for ref in refs:evidence_bytes(evidence_dir,ref)
        require(native['platform']==proof['platform'] and native['application_id']==proof['application_id'],'diagnostic_app_mismatch')
        require(proof['observed_from_ms']<=native['crash_ms']<=proof['observed_through_ms'],'outside_reviewed_interval')
        require(manifest['candidate_sha256']==proof['candidate_sha256'],'release_provenance_mismatch')
        processes={}
        for event in raw_document.get('records',[]):
            if event.get('kind')!='app_start':continue
            value=event.get('payload',{}).get('native_context')
            if value is None:continue
            observed=observation(value)
            if observed['status']!='available':continue
            if observed['native_pid']!=native['native_pid']:continue
            if any(observed[k]!=proof[k] for k in ('platform','application_id','application_version','application_build')):continue
            config=event['payload'].get('config')
            if not isinstance(config,dict) or config.get('candidate_sha256')!=manifest['candidate_sha256']:continue
            at=observed['observed_start_utc_ms']
            if not (native['launch_latest_ms']<=at<=native['crash_ms'] and proof['observed_from_ms']<=at<=proof['observed_through_ms']):continue
            release_match(manifest,native,observed,evidence_dir)
            require(event['process_id'] not in processes,'duplicate_process_start')
            processes[event['process_id']]=observed
        require(len(processes)==1,'ambiguous_or_missing_process_link')
        process=next(iter(processes));start=processes[process]['observed_start_utc_ms']
        for event in raw_document['records']:
            if event['kind']=='gap':
                gap=event['payload'];left=gap['from']*1000;right=gap['to']*1000 if gap['to'] is not None else native['crash_ms']+1
                require(not (left<=native['crash_ms'] and right>=start),'uncertain_observation_interval')
        eligible=[s for s in sessions if s['_process']==process and s['start']*1000<=native['crash_ms']<s.get('_next_start',proof['observed_through_ms']//1000+1)*1000 and s['_last_at']*1000<=native['crash_ms'] and s['_terminal'] is None]
        require(len(eligible)==1,'ambiguous_or_missing_session_interval')
        return {'status':'linked','classification':'native_fatal','install_id':registry['install_id'],'process_id':process,
                'session_id':eligible[0]['session_id'],'crash_at':native['crash_ms']//1000,'incident':native['incident'],
                'report_sha256':report_sha256,'manifest_sha256':manifest_sha256,'provenance_sha256':provenance_sha256}
    except (LinkageError,ValueError,TypeError,KeyError,UnicodeError,struct.error,OverflowError,OSError,zipfile.BadZipFile,RuntimeError) as error:
        return {'status':'unknown','reason':str(error) if isinstance(error,LinkageError) else 'invalid_or_unsupported_evidence','report_sha256':report_sha256}
