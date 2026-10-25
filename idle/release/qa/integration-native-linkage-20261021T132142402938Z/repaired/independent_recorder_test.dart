import 'dart:async';
import 'dart:convert';
import 'package:test/test.dart';
import 'promoted/game/platform/lib/study_recorder.dart';
class DelayedStore implements StudyStore {
 String? value; bool fail=false; int writes=0; Completer<void>? entered,release;
 Future<String?> read() async => value;
 Future<bool> compareAndSwap(String? expected,String next) async {
  writes++;entered?.complete();await release?.future;
  if(fail) throw StateError('synthetic write failure');
  if((value==null?null:studyDigest(value!))!=expected)return false;
  value=next;return true;
 }
 void block(){entered=Completer<void>();release=Completer<void>();}
 void unblock(){release!.complete();release=null;entered=null;}
}
void main(){
 late DelayedStore store;var clock=100,ids=1000;
 final config=StudyConfig(candidateSha256:'a'*64,economySha256:'b'*64,contentSha256:'c'*64,config:'independent');
 final enrollment=StudyEnrollment(studyId:'independent',protocolSha256:'d'*64,informationSha256:'e'*64,consentVersion:'synthetic',eligibilityEvidenceSha256:'f'*64,synthetic:true,platform:'ios',deviceGroup:'phone_large',acquisition:'internal_test');
 Future<StudyRecorder> open()=>StudyRecorder.open(store,clock:()=>DateTime.fromMillisecondsSinceEpoch(clock*1000,isUtc:true),idGenerator:()=>(++ids).toRadixString(16).padLeft(32,'0'));
 StudyProcessObservation available()=>StudyProcessObservation.available(nativePid:321,platform:'ios',applicationId:'dev.tideglass.game',applicationVersion:'1.0.0',applicationBuild:'1',observedStartUtcMs:clock*1000);
 Map<String,dynamic> doc()=>jsonDecode(store.value!);
 setUp((){store=DelayedStore();clock=100;ids=1000;});
 test('unavailable start and zero gap publish in one CAS after durable completion',()async{
  final r=await open();store.block();final pending=r.enroll(enrollment,config,eligibleFreshInstall:true,nativeContext:const StudyProcessObservation.unavailable('native_unavailable'));
  await store.entered!.future;expect(r.exportRaw(),isNull);expect(store.value,isNull);expect(store.writes,1);
  store.unblock();await pending;
  final rows=doc()['records'] as List;expect(rows.length,2);expect(rows[0]['kind'],'app_start');expect(rows[1]['payload'],{'reason':'instrumentationUnavailable','from':100,'to':100});expect(rows[0]['process_id'],rows[1]['process_id']);expect(rows[0]['session_id'],rows[1]['session_id']);expect((await open()).exportRaw(),r.exportRaw());
 });
 test('legacy prefix remains byte-identical, new consent context begins one process',()async{
  final first=await open();await first.enroll(enrollment,config,eligibleFreshInstall:true);await first.interactiveHarbor();await first.activity(StudyActivity.interaction);
  final before=doc();clock=101;final next=await open();await next.beginProcess(config:config,nativeContext:available());
  final after=doc();expect(studyCanonical(after['registry']),studyCanonical(before['registry']));expect(studyCanonical((after['records'] as List).take((before['records'] as List).length).toList()),studyCanonical(before['records']));expect(after['schema_version'],2);
  final committed=store.value;await next.beginProcess(config:config,nativeContext:available());expect(store.value,committed);
 });
 test('failed restart retains last committed identity; retry gap belongs to previous process',()async{
  var r=await open();await r.enroll(enrollment,config,eligibleFreshInstall:true,nativeContext:available());final prior=store.value,oldProcess=r.processId;clock=101;r=await open();store.fail=true;
  await expectLater(r.beginProcess(config:config,nativeContext:available()),throwsStateError);expect(store.value,prior);expect(r.processId,oldProcess);expect(r.hasPendingStorageGap,isTrue);
  store.fail=false;clock=102;await r.beginProcess(config:config,nativeContext:available());final rows=doc()['records'] as List;
  expect(rows[1]['payload'],{'reason':'storageFailure','from':100,'to':102});expect(rows[1]['process_id'],oldProcess);expect(rows[2]['kind'],'app_start');expect(rows[2]['process_id'],isNot(oldProcess));await open();
 });
 test('withdrawal immediately stops queued capture and erases all native fields',()async{
  final r=await open();await r.enroll(enrollment,config,eligibleFreshInstall:true,nativeContext:available());store.block();final active=r.interactiveHarbor();await store.entered!.future;
  final stop=r.withdraw(retainMinimalRegistry:true);expect(r.enrolled,isFalse);expect(r.withdrawalPending,isTrue);final skipped=r.activity(StudyActivity.interaction);store.unblock();await active;await stop;await skipped;
  expect(doc(),{'schema_version':1,'registry':null,'records':[],'status':'withdrawn'});expect((await open()).withdrawn,isTrue);
 });
 test('missing unavailable gap rejects on persisted reopen',()async{
  final r=await open();await r.enroll(enrollment,config,eligibleFreshInstall:true,nativeContext:const StudyProcessObservation.unavailable('not_requested'));
  final value=doc();(value['records'] as List).removeLast();store.value=studyCanonical(value);await expectLater(open(),throwsA(isA<StudyException>()));
 });
 test('fractional erased schema is rejected like Python',()async{
  for(final v in [1.0,2.0]){store.value=studyCanonical({'schema_version':v,'registry':null,'records':[],'status':'withdrawn'});await expectLater(open(),throwsA(isA<StudyException>()),reason:'schema=$v');}
 });
 test('native context is strict for version, keys, PID/time type and unavailable reason',(){
  final baseline=available().toJson();
  for(final change in [{'version':1.0},{'native_pid':321.0},{'observed_start_utc_ms':100000.0},{'extra':'secret'},{'application_build':'1\n'}]){expect(()=>StudyProcessObservation.fromJson({...baseline,...change}),throwsA(anything));}
  expect(()=>StudyProcessObservation.fromJson({'version':1,'status':'unavailable','reason':'invented'}),throwsFormatException);
 });
}
