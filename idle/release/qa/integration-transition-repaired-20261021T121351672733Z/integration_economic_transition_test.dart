import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const oldVersion = 'tideglass-economy-0.4.2';
const oldDigest = 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc';
const newDigest = '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6';
final epoch = DateTime.utc(2031, 7, 2);
class QuarterLegacy extends TideglassEngine {
  const QuarterLegacy();
  @override String get rulesVersion => oldVersion;
  @override Fixed producerOutputPerSecond(GameState state, int tier) => Fixed.raw(super.producerOutputPerSecond(state, tier).raw * BigInt.from(5) ~/ BigInt.from(4));
}
const oldEngine = QuarterLegacy();
const engine = TideglassEngine();
GameState decode(Map<String,dynamic> p, String version) => GameState.fromJson(Map<String,dynamic>.from(p['core'] as Map), expectedEconomicVersion: version);
Map<String,dynamic> pack(GameState s) => {'core':s.toJson()};
void at(Map<String,dynamic> p,DateTime cursor,String version) {
 final s=decode(p,version);
 if(s.daily.utcAnchorMicros!+s.elapsedMicros!=BigInt.from(cursor.microsecondsSinceEpoch)) throw const FormatException('QA cursor mismatch');
}
final config = EconomicConfiguration(version:oldVersion,digest:oldDigest,validatePayload:(p)=>decode(p,oldVersion),validateSnapshot:(p,c)=>at(p,c,oldVersion));
Map<String,dynamic> adopt(Map<String,dynamic> p) {
 final t=engine.adoptCompatibleState(decode(p,oldVersion),sourceRulesVersion:oldVersion);
 if(!t.accepted) throw StateError(t.reason!);
 return pack(t.state);
}
SaveRepository oldStore(Directory d) => SaveRepository(d,economicVersion:oldVersion,economicDigest:oldDigest,validatePayload:config.validatePayload,validateSnapshot:config.validateSnapshot);
SaveRepository newStore(Directory d,{CommitProbe? probe,List<CompatibleEconomicPredecessor>? predecessors}) => SaveRepository(d,economicVersion:economyVersion,economicDigest:newDigest,validatePayload:(p)=>decode(p,economyVersion),validateSnapshot:(p,c)=>at(p,c,economyVersion),commitProbe:probe,compatiblePredecessors:predecessors??[CompatibleEconomicPredecessor(configuration:config,migratePayload:adopt)]);
Future<SaveSnapshot> seed(Directory d) async {
 final r=oldStore(d); await r.load();
 final s=oldEngine.refreshContracts(GameState.initial(rulesVersion:oldVersion),epoch,accountSeed:'qa-transition').state;
 return r.save(pack(s),settledThrough:epoch);
}
Future<Map<String,dynamic>> settle(SaveSnapshot s,DateTime end) async {
 final state=decode(s.payload,oldVersion); final t=oldEngine.advance(state,end.difference(s.settledThrough),offline:true,offlineSettlement:OfflineSettlementRequest(sequence:state.nextSettlementSequence,fromUtc:s.settledThrough,throughUtc:end));
 if(!t.accepted) throw StateError(t.reason!); return pack(t.state);
}
Future<Map<String,String>> bytes(Directory d) async => {for(final f in d.listSync().whereType<File>()) if(f.path.endsWith('.json')) f.path:await f.readAsString()};
void main() {
 late Directory d;
 setUp(()async {d=await Directory.systemTemp.createTemp('qa-economic-transition-');});
 tearDown(()async {await d.delete(recursive:true);});
 test('nested A-to-B-to-A transition callbacks reject reentry instead of deadlock',()async {
  final b=Directory('${d.path}/second');await b.create();final sa=await seed(d),sb=await seed(b);final a=newStore(d),other=newStore(b);await a.load();await other.load();Object? seen;Future<LoadResult>? pendingReentry;
  final end=epoch.add(const Duration(microseconds:3));
  await a.transitionEconomy(source:sa,boundary:end,authorizedThrough:end,settleOld:(x,t)async{
   await other.transitionEconomy(source:sb,boundary:end,authorizedThrough:end,settleOld:(y,u)async{
    try {pendingReentry=a.load();await pendingReentry!.timeout(const Duration(milliseconds:180));}catch(e){seen=e;}
    return settle(y,u);
   });return settle(x,t);
  });
  try {await pendingReentry;} catch (_) {}
  expect(seen,isA<StateError>(),reason:'The complete ancestor lock set must survive nested transition zones. A timeout means reentry queued behind its own outer operation.');
 });
 test('foreign source identity rejects before settlement and preserves both branches',()async {
  final foreign=Directory('${d.path}/foreign');await foreign.create();await seed(d);final source=await seed(foreign);final r=newStore(d);await r.load();final before=await bytes(d);var calls=0;final end=epoch.add(const Duration(seconds:1));
  await expectLater(r.transitionEconomy(source:source,boundary:end,authorizedThrough:end,settleOld:(s,t)async{calls++;return settle(s,t);}),throwsA(isA<SaveConflictException>()));expect(calls,0);expect(await bytes(d),before);
 });
 test('wrong digest and duplicate compiled version edges reject before mutation',()async {
  await seed(d);final before=await bytes(d);
  final wrong=EconomicConfiguration(version:oldVersion,digest:'d'*64,validatePayload:config.validatePayload,validateSnapshot:config.validateSnapshot);
  await expectLater(newStore(d,predecessors:[CompatibleEconomicPredecessor(configuration:wrong,migratePayload:adopt)]).load(),throwsA(isA<IncompatibleSaveException>()));
  expect(()=>newStore(d,predecessors:[CompatibleEconomicPredecessor(configuration:config,migratePayload:adopt),CompatibleEconomicPredecessor(configuration:wrong,migratePayload:adopt)]),throwsArgumentError);expect(await bytes(d),before);
 });
 test('independent 5/4 microsecond arithmetic carries exact fractional residue',()async {
  final s=await seed(d);final r=newStore(d);await r.load();final end=epoch.add(const Duration(microseconds:3));final switched=await r.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:settle);
  final v=decode(switched.payload,economyVersion);expect(v.walletMicros,BigInt.from(3));expect(v.earningRemainder,Fixed.scale*BigInt.from(300));
  final after=engine.advance(v,const Duration(microseconds:11)).state;expect(after.walletMicros,BigInt.from(14));expect(after.lifetimeMicros,BigInt.from(14));expect(after.earningRemainder,v.earningRemainder);expect(after.charts,BigInt.zero);
 });
 test('queued same-path alias attempts settle old rules exactly once',()async {
  final s=await seed(d);final link=Link('${d.path}/alias');await link.create(d.path);final a=newStore(d),b=newStore(Directory(link.path));await a.load();await b.load();var calls=0;final end=epoch.add(const Duration(seconds:4));
  Future<Map<String,dynamic>> work(SaveSnapshot s,DateTime t)async{calls++;await Future<void>.delayed(const Duration(milliseconds:10));return settle(s,t);}
  final result=await Future.wait([a.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:work),b.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:work)]);
  expect(calls,1);expect(result[0].saveId,result[1].saveId);expect(decode(result[0].payload,economyVersion).walletMicros,BigInt.from(5000000));await link.delete();
 });
 for(final stage in CommitStage.values) {
  test('independent ambiguous ${stage.name} retry retains one grant after later write',()async{
   final s=await seed(d);var calls=0;final end=epoch.add(const Duration(seconds:2));final fail=newStore(d,probe:(p)async{if(p==stage)throw const FileSystemException('QA interrupted');});await fail.load();
   Future<Map<String,dynamic>> count(SaveSnapshot s,DateTime t)async{calls++;return settle(s,t);}
   await expectLater(fail.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:count),throwsA(isA<FileSystemException>()));
   final retry=newStore(d);await retry.load();final done=await retry.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:count);expect(calls,stage==CommitStage.afterRename?1:2);
   final advanced=engine.advance(decode(done.payload,economyVersion),const Duration(seconds:7)).state;final later=await retry.save(pack(advanced),settledThrough:end.add(const Duration(seconds:7)));
   final again=await retry.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:(_,__)async=>throw StateError('should not replay'));expect(again.envelope,later.envelope);expect(decode(again.payload,economyVersion).lifetimeMicros,BigInt.from(9500000));
   final exported=await retry.exportSave();final imported=await retry.importSave(exported);expect(imported.envelope['applied_operation_ids'],isEmpty);
   await expectLater(retry.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:settle),throwsA(isA<SaveConflictException>()));
  });
 }
 test('failed old cursor or destination migration leaves committed bytes unchanged',()async {
  final s=await seed(d);final r=newStore(d);await r.load();final before=await bytes(d);final end=epoch.add(const Duration(seconds:1));
  await expectLater(r.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:(s,t)async=>s.payload),throwsFormatException);
  final bad=newStore(d,predecessors:[CompatibleEconomicPredecessor(configuration:config,migratePayload:(p)=>p)]);await bad.load();await expectLater(bad.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:settle),throwsFormatException);expect(await bytes(d),before);
 });
 test('rejected backdate or unauthorized boundary invokes no callback',()async {
  final s=await seed(d);final r=newStore(d);await r.load();var calls=0;
  for(final boundary in [epoch.subtract(const Duration(microseconds:1)),epoch.add(const Duration(microseconds:1))]) {
   await expectLater(r.transitionEconomy(source:s,boundary:boundary,authorizedThrough:epoch,settleOld:(s,t)async{calls++;return settle(s,t);}),throwsA(isA<SaveConflictException>()));
  }expect(calls,0);
 });
 test('compatible edges require both old and new snapshot cursor validators',() {
  final unqualified=EconomicConfiguration(version:oldVersion,digest:oldDigest,validatePayload:config.validatePayload);
  expect(()=>newStore(d,predecessors:[CompatibleEconomicPredecessor(configuration:unqualified,migratePayload:adopt)]),throwsArgumentError);
  expect(()=>SaveRepository(d,economicVersion:economyVersion,economicDigest:newDigest,validatePayload:(p)=>decode(p,economyVersion),compatiblePredecessors:[CompatibleEconomicPredecessor(configuration:config,migratePayload:adopt)]),throwsArgumentError);
 });
 test('edited old envelope with reused identifiers cannot impersonate successful retry',()async {
  final s=await seed(d);final r=newStore(d);await r.load();final end=epoch.add(const Duration(seconds:1));final done=await r.transitionEconomy(source:s,boundary:end,authorizedThrough:end,settleOld:settle);
  final elsewhere=Directory('${d.path}/edited');await elsewhere.create();final edited=s.envelope;
  final changed=decode(s.payload,oldVersion).copyWith(walletMicros:BigInt.one,lifetimeMicros:BigInt.one);
  (edited['gameplay_state'] as Map)['payload']=pack(changed);
  Object? canonical(Object? o) {if(o is Map){final keys=o.keys.cast<String>().toList()..sort();return {for(final k in keys)k:canonical(o[k])};}if(o is List)return o.map(canonical).toList();return o;}
  final record={'format':'tideglass-checksummed-save','checksum':sha256.convert(utf8.encode(jsonEncode(canonical(edited)))).toString(),'envelope':edited};
  await File('${elsewhere.path}/progress.0.json').writeAsString(jsonEncode(record));final forged=(await oldStore(elsewhere).load()).snapshot!;
  expect(forged.saveId,s.saveId);expect(forged.payload,isNot(s.payload));
  await expectLater(r.transitionEconomy(source:forged,boundary:end,authorizedThrough:end,settleOld:(_,__)async=>throw StateError('not callable')),throwsA(isA<SaveConflictException>()));
  expect((await r.load()).snapshot!.saveId,done.saveId);
 });

}
