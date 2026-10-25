from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,plistlib,gzip,subprocess,re,struct,difflib,datetime
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent
C=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122';AUTHOR=ROOT/'release/native-proof/execution-3b00-20261023T040612.562001Z'
reports=[ROOT/'release/native-proof/20261023T040548.338966Z/build-report.json',ROOT/'release/native-proof/20261023T041555.017412Z/build-report.json']
H=lambda b:hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
read=lambda p:json.loads(p.read_text());pins={};checks=[];commands=[]
def pin(p):pins[str(p)]=sha(p);return p
def ck(name,v):
 checks.append({'name':name,'pass':bool(v)})
 if not v:raise AssertionError(name)
def run(name,argv,expected=0):
 r=subprocess.run(argv,capture_output=True,timeout=60);(OUT/(name+'.stdout')).write_bytes(r.stdout);(OUT/(name+'.stderr')).write_bytes(r.stderr);commands.append({'name':name,'argv':argv,'exit_code':r.returncode,'stdout_sha256':H(r.stdout),'stderr_sha256':H(r.stderr)});ck('command '+name,r.returncode==expected);return r.stdout.decode(errors='replace'),r.stderr.decode(errors='replace')
def cmap(font):
 # Read only standard OpenType table bounds and Unicode cmap4/12; no rendering claim.
 u16=lambda o:struct.unpack_from('>H',font,o)[0];u32=lambda o:struct.unpack_from('>I',font,o)[0]
 n=u16(4);tables={}
 for i in range(n):
  tag,checksum,off,length=struct.unpack_from('>4sIII',font,12+16*i);ck('font table bounds '+tag.decode(),off+length<=len(font));tables[tag]=(off,length)
 off=tables[b'cmap'][0];codes={}
 for i in range(u16(off+2)):
  platform,encoding,relative=struct.unpack_from('>HHI',font,off+4+8*i);sub=off+relative;fmt=u16(sub)
  if platform not in [0,3]:continue
  if fmt==12:
   for j in range(u32(sub+12)):
    start,end,gid=struct.unpack_from('>III',font,sub+16+12*j)
    for code in range(start,end+1):
     if gid+code-start:codes[code]=gid+code-start
  elif fmt==4:
   seg=u16(sub+6)//2;ends=sub+14;starts=ends+2*seg+2;deltas=starts+2*seg;ranges=deltas+2*seg
   for j in range(seg):
    start,end=u16(starts+2*j),u16(ends+2*j);delta=u16(deltas+2*j);offset=u16(ranges+2*j)
    for code in range(start,min(end,65534)+1):
     addr=ranges+2*j+offset+2*(code-start)
     gid=(code+delta)&65535 if offset==0 else u16(addr)
     if offset and gid:gid=(gid+delta)&65535
     if gid:codes[code]=gid
 count=u16(tables[b'maxp'][0]+4)
 ck('font glyph indices in range',all(x<count for x in codes.values()))
 return {'glyph_count':count,'unicode_codepoints':len(codes)},codes
manifest=read(pin(C/'manifest.json'));fingerprint=manifest['source_fingerprint'];ck('canonical source fingerprint',H(json.dumps(manifest['source_sha256'],sort_keys=True,separators=(',',':')).encode())==fingerprint)
for f,h in manifest['source_sha256'].items():ck('frozen source '+f,sha(C/'source'/f)==h)
source_count=len(manifest['source_sha256']);workspace_differences={};lockrows=[]
for workspace in ['workspace','workspace-release']:
 changed=[]
 for f,h in manifest['source_sha256'].items():
  p=C/workspace/f
  if not p.is_file() or sha(p)!=h:changed.append(f)
  if f.endswith(('pubspec.lock','Podfile.lock','gradle.lockfile','Package.resolved')):
   ck('frozen dependency lock '+workspace+'/'+f,p.is_file() and sha(p)==h);lockrows.append({'workspace':workspace,'file':f,'sha256':h})
 workspace_differences[workspace]=changed
allowed='game/mobile/android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java'
ck('debug workspace captured inputs unchanged',workspace_differences['workspace']==[])
ck('release only generated Android registrant differs',workspace_differences['workspace-release']==[allowed])
a=(C/'source'/allowed).read_text();b=(C/'workspace-release'/allowed).read_text();deleted='''    try {
      flutterEngine.getPlugins().add(new dev.flutter.plugins.integration_test.IntegrationTestPlugin());
    } catch (Exception e) {
      Log.e(TAG, "Error registering plugin integration_test, dev.flutter.plugins.integration_test.IntegrationTestPlugin", e);
    }
''';ck('SDK difference only removes integration_test plugin',a.replace(deleted,'')==b);(OUT/'generated-registrant.diff').write_text('\n'.join(difflib.unified_diff(a.splitlines(),b.splitlines()))+'\n');ck('live registrant retains frozen production bytes',sha(ROOT/allowed)==manifest['source_sha256'][allowed])
inv=read(pin(AUTHOR/'artifact-inventory/inventory.json'));fonts=read(pin(AUTHOR/'packaged-font-evidence/verification.json'))
ck('inventory exact candidate',inv['candidate_fingerprint']==fingerprint and inv['candidate_manifest_sha256']==sha(C/'manifest.json'));ck('font evidence exact candidate',fonts['candidate_fingerprint']==fingerprint and fonts['manifest_sha256']==sha(C/'manifest.json'))
for f in ['artifact-inventory/collector.py','inspect_font_exports.py','android-ready-observation.json','ios-release-signature.json','android-release-signature.json']:pin(AUTHOR/f)
for f in ['v1_backlog.json','implementation/program.json','implementation/scope_requirements.json','release/store/android-target-api-check-20261023.json','release/native-privacy/README.md','release/native-privacy/inspect_artifacts.py','.tooling/bundletool/download.json']:pin(ROOT/f)
for f in ['game/mobile/lib/bootstrap.dart','game/mobile/lib/native_services.dart','game/mobile/lib/font_licenses.dart','game/mobile/lib/main.dart','game/mobile/pubspec.yaml','game/mobile/android/app/build.gradle.kts','game/mobile/ios/Runner/PrivacyInfo.xcprivacy','game/mobile/assets/licenses/MaterialIcons_LICENSE.txt']:
 pin(ROOT/f);ck('live relevant source agrees with candidate '+f,sha(ROOT/f)==manifest['source_sha256'][f])
license_bytes=(C/'source/game/mobile/assets/licenses/MaterialIcons_LICENSE.txt').read_bytes();sdk_path=pin(ROOT/'.tooling/flutter/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf');sdkfont=sdk_path.read_bytes();sdkstats,sdkcodes=cmap(sdkfont);iconssource=pin(ROOT/'.tooling/flutter/packages/flutter/lib/src/material/icons.dart').read_text();critical={name:int(re.search(r'static const IconData '+name+r' = IconData\(\s*(0x[0-9a-f]+)',iconssource).group(1),16) for name in ['auto_awesome_outlined','explore_outlined','assignment_outlined','check_circle_outline','water_outlined']}
artifacts=[];all_privacy=[];member_count=0;release_fonts=[];metadata_anomalies=[]
for rp in reports:
 report=read(pin(rp));ck('report exact source '+report['mode'],report['candidate_fingerprint']==fingerprint and report['source_snapshot_unchanged'] and report['dependency_locks_unchanged']);ck('report runner pin '+report['mode'],sha(C/'source/tool/build_native.py')==report['runner_sha256'])
 ck('default build no provider defines '+report['mode'],not any('dart-define' in part for r in report['results'].values() for part in r['command']))
 for platform,r in report['results'].items():
  label=platform+'-'+report['mode'];p=pin(ROOT/r['artifact']);ck(label+' successful export record',r['exit_code']==0 and r['build_succeeded']);ck(label+' artifact hash/size',sha(p)==r['artifact_sha256'] and p.stat().st_size==r['artifact_bytes'])
  declared=next(x for x in inv['artifacts'] if x['platform']==platform and x['mode']==report['mode']);fontrow=next(x for x in fonts['artifacts'] if x['platform']==platform and x['mode']==report['mode']);ck(label+' inventory/report/font binding',declared['artifact_sha256']==fontrow['artifact_sha256']==r['artifact_sha256'] and declared['build_report_sha256']==sha(rp))
  row={'label':label,'artifact':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'member_inventory_count':len(declared['members']),'privacy':[]}
  with zipfile.ZipFile(p) as z:
   ck(label+' all zip members CRC/decompression',z.testzip() is None);names=z.namelist();ck(label+' unique names',len(names)==len(set(names)));ck(label+' safe archive paths',all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names))
   for m in declared['members']:
    data=z.read(m['member']);ck(label+' inventory actual member '+m['member'],H(data)==m['sha256'] and len(data)==m['bytes']);raw=AUTHOR/'artifact-inventory'/m['raw_copy'];ck(label+' archived raw member '+m['member'],raw.read_bytes()==data);member_count+=1
    if 'plist' in m:ck(label+' actual parsed plist '+m['member'],plistlib.loads(data)==m['plist'])
    else:ck(label+' actual decoded property '+m['member'],data.decode()==m['text'])
    if m['member'].endswith('/PrivacyInfo.xcprivacy'):
     e={'label':label,'member':m['member'],'sha256':H(data),'plist':plistlib.loads(data)};all_privacy.append(e);row['privacy'].append(m['member'])
    if m['member'].endswith('UserMessagingPlatform.framework/Info.plist') and platform=='ios':
     metadata_anomalies.append({'label':label,'member':m['member'],'MinimumOSVersion':m['plist'].get('MinimumOSVersion')})
   row['fonts']=[]
   for kind,suffix in [('license','/assets/licenses/MaterialIcons_LICENSE.txt'),('font','/fonts/MaterialIcons-Regular.otf'),('notices','/NOTICES.Z')]:
    matching=[n for n in names if n.endswith(suffix) and not n.startswith('__MACOSX/')];ck(label+' single '+kind,len(matching)==1);name=matching[0];data=z.read(name);prior=next(x for x in fontrow['members'] if x['kind']==kind);ck(label+' exact author '+kind,H(data)==prior['sha256']);entry={'kind':kind,'member':name,'bytes':len(data),'sha256':H(data)}
    if kind=='license':ck(label+' explicit full license exact',data==license_bytes);(OUT/(label+'-MaterialIcons_LICENSE.txt')).write_bytes(data)
    if kind=='font':
     stats,codes=cmap(data);entry.update(stats);entry['equals_full_sdk_font']=data==sdkfont;entry['critical_codepoints']={k:hex(v) for k,v in critical.items()};ck(label+' critical daily/nav glyphs included',all(v in codes for v in critical.values()));ck(label+' codepoints subset of original',set(codes)<=set(sdkcodes));(OUT/(label+'-MaterialIcons-Regular.otf')).write_bytes(data)
     if report['mode']=='release':release_fonts.append(data);ck(label+' is a real font subset',data!=sdkfont and stats['glyph_count']<sdkstats['glyph_count'])
     else:ck(label+' full pinned debug font',data==sdkfont)
    if kind=='notices':
     text=gzip.decompress(data);entry['decoded_sha256']=H(text);entry['mentions_material_icons']='Material Icons' in text.decode();entry['mentions_apache']='Apache License' in text.decode();ck(label+' decoded notice author pin',H(text)==prior['decoded_sha256']);(OUT/(label+'-NOTICES.txt')).write_bytes(text)
    row['fonts'].append(entry)
   if platform=='ios':
    info=plistlib.loads(z.read('Runner.app/Info.plist'));row['app_info']=info
    privacy=plistlib.loads(z.read('Runner.app/PrivacyInfo.xcprivacy'));ck(label+' exact app privacy semantics',privacy==plistlib.loads((C/'source/game/mobile/ios/Runner/PrivacyInfo.xcprivacy').read_bytes()))
    if report['mode']=='release':
     row['root_signature_members']=[n for n in names if n.startswith('Runner.app/_CodeSignature/') or n=='Runner.app/embedded.mobileprovision'];ck('release iOS no root signing/provision',not row['root_signature_members']);exe=OUT/'ios-release-Runner';exe.write_bytes(z.read('Runner.app/Runner'));exe.chmod(0o700);stdout,stderr=run('ios-release-codesign',['/usr/bin/codesign','-d','--verbose=4',str(exe)],1);ck('release actual executable unsigned','not signed at all' in stdout+stderr)
     ump=OUT/'ios-release-UserMessagingPlatform';ump.write_bytes(z.read('Runner.app/Frameworks/UserMessagingPlatform.framework/UserMessagingPlatform'));run('ios-release-ump-build-version',['/usr/bin/otool','-l',str(ump)])
   if platform=='android' and report['mode']=='release':
    row['signature_members']=[n for n in names if n.startswith('META-INF/') and n.upper().endswith(('.RSA','.DSA','.EC','.SF'))];ck('release AAB no signature entries',not row['signature_members']);jarsigner=ROOT/'.tooling/java/jdk-17.0.20.1+1/Contents/Home/bin/jarsigner';stdout,_=run('android-release-jarsigner',[str(pin(jarsigner)),'-verify',str(p)]);ck('release AAB verifier says unsigned','jar is unsigned.' in stdout)
  artifacts.append(row)
ck('exact five exports',len(artifacts)==5);ck('same iOS/Android release subset',release_fonts[0]==release_fonts[1])
# Independently decode actual public-target Android archive bytes with pinned read-only tools.
aapt=pin(ROOT/'.tooling/android-sdk/build-tools/36.0.0/aapt2');bundle=pin(ROOT/'.tooling/bundletool/bundletool-all-1.18.3.jar');java=pin(ROOT/'.tooling/java/jdk-17.0.20.1+1/Contents/Home/bin/java');ck('decoder pins match author',sha(aapt)==inv['tools']['aapt2_sha256'] and sha(bundle)==inv['tools']['bundletool_sha256']);ck('bundletool official recorded digest',sha(bundle)==read(ROOT/'.tooling/bundletool/download.json')['sha256'])
for mode in ['debug','release']:
 a=next(x for x in inv['artifacts'] if x['platform']=='android' and x['mode']==mode);cmd=a['manifest_command']['argv'];stdout,stderr=run('android-'+mode+'-manifest',cmd);ck('independent manifest output matches '+mode,H(stdout.encode())==a['manifest_command']['stdout_sha256'])
 if mode=='debug':
  text,_=run('android-debug-permissions',a['permissions_command']['argv']);ck('independent permissions match author',H(text.encode())==a['permissions_command']['stdout_sha256'])
 else:
  import xml.etree.ElementTree as ET
  xml=ET.fromstring(stdout);ns='{http://schemas.android.com/apk/res/android}';sdk=xml.find('uses-sdk');permissions=[x.attrib[ns+'name'] for x in xml if x.tag.startswith('uses-permission')];app=xml.find('application');components=[{'kind':x.tag,'attributes':dict(x.attrib),'metadata':[dict(y.attrib) for y in x.findall('meta-data')]} for x in app if x.tag in ['provider','service','receiver','activity','meta-data']];summary={'package':xml.get('package'),'version_code':xml.get(ns+'versionCode'),'version_name':xml.get(ns+'versionName'),'sdk':[dict(x.attrib) for x in xml.findall('uses-sdk')],'permissions':[dict(x.attrib) for x in xml if x.tag.startswith('uses-permission')],'application_attributes':dict(app.attrib),'components':components};ck('independent Android manifest parser matches author',summary==a['manifest_summary']);ck('actual API36 and Android10 floor',sdk.attrib[ns+'targetSdkVersion']=='36' and sdk.attrib[ns+'minSdkVersion']=='29');(OUT/'android-release-manifest-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  ck('SDK advertising/billing permissions retained',{'com.google.android.gms.permission.AD_ID','android.permission.ACCESS_ADSERVICES_AD_ID','com.android.vending.BILLING'}<=set(permissions));ck('SDK startup provider retained',any(x['attributes'].get(ns+'name')=='com.google.android.gms.ads.MobileAdsInitProvider' for x in components))
policy=read(ROOT/'release/store/android-target-api-check-20261023.json');ck('root target policy inventory exact',policy['artifact_inventory_sha256']==sha(AUTHOR/'artifact-inventory/inventory.json') and policy['candidate_fingerprint']==fingerprint)
ready=read(AUTHOR/'android-ready-observation.json');ck('recorded runtime only API35',next(x['output'].strip() for x in ready if x['command'][-1]=='ro.build.version.sdk')=='35')
for f,h in manifest['source_sha256'].items():ck('frozen source after '+f,sha(C/'source'/f)==h)
for p,h in pins.items():ck('inspected file unchanged '+p,sha(Path(p))==h)
(OUT/'apple-privacy-manifests.json').write_text(json.dumps(all_privacy,indent=2)+'\n');(OUT/'artifact-results.json').write_text(json.dumps(artifacts,indent=2)+'\n');(OUT/'source-lock-binding.json').write_text(json.dumps({'candidate':fingerprint,'source_files':source_count,'workspace_differences':workspace_differences,'locks':lockrows,'allowed_generated_delta':'Only release integration_test plugin registration omitted; live source unchanged'},indent=2)+'\n');(OUT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(OUT/'inspected-file-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(OUT/'verification.json').write_text(json.dumps({'candidate':fingerprint,'checks':checks,'all_passed':True,'five_exports':True,'inventory_members_reproduced':member_count,'source_files':source_count,'public_target_release_signed':False,'product_runtime_or_traffic_observed_by_reviewer':False,'new_flutter_device_ui_commands':False,'package_or_scope_acceptance':False,'sdk_metadata_observations':metadata_anomalies},indent=2)+'\n');print(json.dumps({'checks':len(checks),'source_files':source_count,'members':member_count,'artifacts':len(artifacts),'metadata_observations':metadata_anomalies,'verification_sha256':sha(OUT/'verification.json')},indent=2))
