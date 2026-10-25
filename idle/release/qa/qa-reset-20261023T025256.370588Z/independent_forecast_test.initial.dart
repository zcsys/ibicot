import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';
import '../../../game/mobile/lib/rechart_forecast_task.dart';

const engine = TideglassEngine();
final observations = <Map<String,Object?>>[];
GameState state(List<int> counts, int charts, int entitlement, {int wallet = 1000000000000, int focus = 0, int support = 0}) => GameState(counts: counts, charts: BigInt.from(charts), lifetimeMicros: engine.lifetimeForCharts(BigInt.from(entitlement)), walletMicros: BigInt.from(wallet), focusRemainingMicros: BigInt.from(focus), support: SupportState(remainingMicros: BigInt.from(support)), earningRemainder: Fixed.scale * BigInt.from(399));

// Independent selector: recompute the total before/after rate rather than
// calling chooseAutoBuyTier or marginalOutputPerSecond. Cross multiplication
// preserves exact comparisons. Highest tier wins exact efficiency ties.
GameState decide(GameState s) {
  while (true) {
    int selected = -1;
    BigInt bestGain = BigInt.zero, bestCost = BigInt.one;
    final before = engine.outputPerSecond(s).raw;
    for (var tier=0;tier<5;tier++) {
      if (tier>0 && s.counts[tier-1]<10) continue;
      final counts = s.counts.toList()..[tier]++;
      final gain = engine.outputPerSecond(s.copyWith(counts: counts)).raw-before;
      final cost = engine.priceMicros(tier,s.counts[tier]);
      if (selected<0 || gain*bestCost>=bestGain*cost) {selected=tier;bestGain=gain;bestCost=cost;}
    }
    if (s.walletMicros<bestCost) return s;
    final buy=engine.buy(s,selected,1);
    expect(buy.accepted,true);
    s=buy.state;
  }
}

Map<String,Object?> oracle(GameState input,int horizon) {
  final prepared=input.copyWith(autoBuyEnabled:false,automationPlans:[AutomationPlan.base()], selectedAutomationPlanId:'plan.base');
  var keep=decide(prepared), reset=decide(engine.rechart(prepared).state);
  final initialRate=engine.outputPerSecond(input).raw;
  int? first, rebuilt=engine.outputPerSecond(reset).raw>=initialRate?0:null;
  var lastBehind=0;
  bool ahead=false;
  for(var seconds=60;seconds<=horizon;seconds+=60){
    // Unequal sub-minute intervals cross boost/queue/calendar boundaries while
    // retaining all account state that the forecast's reduced projection omits.
    for(final part in [13000001,16999998,29000000,1000001]){
      final k=engine.advance(keep,Duration(microseconds:part),autoBuy:false);
      final r=engine.advance(reset,Duration(microseconds:part),autoBuy:false);
      expect(k.accepted,true);expect(r.accepted,true);keep=k.state;reset=r.state;
    }
    keep=decide(keep);reset=decide(reset);
    if(rebuilt==null && engine.outputPerSecond(reset).raw>=initialRate) rebuilt=seconds;
    ahead=reset.lifetimeMicros>input.lifetimeMicros && reset.lifetimeMicros>=keep.lifetimeMicros;
    if(ahead){first??=seconds;}else{lastBehind=seconds;}
  }
  return {'keep':(keep.lifetimeMicros-input.lifetimeMicros).toString(),'reset':(reset.lifetimeMicros-input.lifetimeMicros).toString(),'first':first,'break':ahead?lastBehind+60:null,'rebuild':rebuilt,'keep_charts':keep.charts.toString(),'reset_charts':reset.charts.toString()};
}
void compare(GameState s,int horizon,String name){
 final before=jsonEncode(s.toJson()); final expected=oracle(s,horizon);
 final actual=estimateRechart(s,horizonSeconds:horizon);
 expect(actual.status,RechartForecastStatus.estimated);
 expect(actual.keepGainMicros.toString(),expected['keep']);expect(actual.resetGainMicros.toString(),expected['reset']);
 expect(actual.firstCatchUpSeconds,expected['first']);expect(actual.breakEvenSeconds,expected['break']);expect(actual.rebuildSeconds,expected['rebuild']);
 expect(actual.samples,horizon~/60);expect(jsonEncode(s.toJson()),before);
 observations.add({'name':name,'oracle':expected,'actual':actual.toJson(),'input_unchanged':true});
}
void main(){
 tearDownAll((){File(Platform.environment['QA_FORECAST_RESULT']!).writeAsStringSync('${const JsonEncoder.withIndent('  ').convert(observations)}\n');});
 test('independent selector and unequal timeline oracle: unlock, milestone, boost, wallet and saved-plan cases',(){
  final cases=[
   state([1,0,0,0,0],0,10,wallet:0,focus:13000001,support:29999999),
   state([9,9,9,9,9],10,24,wallet:100000000000,focus:60000001,support:59999999),
   state([24,24,24,24,24],10,25,focus:29999999,support:60000001),
   state([49,74,99,24,49],25,100,focus:60000000,support:60000000),
   state([100,75,50,25,10],100,135).copyWith(autoBuyEnabled:true,automationPlans:[AutomationPlan(id:'plan.base',name:'Priority reset',purchasePolicy:'priority',autoResetEnabled:true,minimumRunSeconds:1)],focusCharges:11,focusPhaseMicros:BigInt.from(7199999999),completedSurveys:2,surveyPhaseMicros:BigInt.from(28799999999)),
   state([100,75,50,25,10],10000,10001,wallet:0),
  ];
  for(var i=0;i<cases.length;i++){
   final full=engine.refreshContracts(cases[i],DateTime.utc(2026,10,23,23,59,47),accountSeed:'qa-forecast-$i').state;
   compare(full,1800,'case-$i');
  }
 });
 test('full 24h independent oracle preserves exact totals and last-deficit criterion',(){compare(state([100,75,50,25,10],0,10),86400,'24h');});
 test('every advertised next unlock and post100 target is the exact earned boundary',(){
  for(final row in [[0,10],[10,24],[10,25],[25,99],[25,100],[100,107]]){
   final s=state([1,0,0,0,0],row[0],row[1],wallet:0),r=estimateRechart(state([1,0,0,0,0],row[0],row[1],wallet:0),horizonSeconds:60);
   final after=s.charts+engine.prestigeAward(s);
   final target=[10,25,100].map(BigInt.from).where((v)=>v>after).firstOrNull??after+BigInt.one;
   expect(r.nextChartTarget,target);expect(engine.prestigeEntitlement(r.nextChartLifetimeMicros!),target);expect(engine.prestigeEntitlement(r.nextChartLifetimeMicros!-BigInt.one),lessThan(target));
   expect(r.unlockedChartThresholds,[10,25,100].where((v)=>BigInt.from(v)>s.charts && BigInt.from(v)<=after).toList());
  }
 });
 test('shared work exhaustion cannot expose partial output or advice',(){
  final s=state([100,75,50,25,10],0,10);
  for(final budget in [1,4,100,1000]){
   final r=estimateRechart(s,maximumWork:budget);expect(r.status,RechartForecastStatus.workLimit);expect(r.keepGainMicros,isNull);expect(r.resetGainMicros,isNull);expect(r.breakEvenSeconds,isNull);expect(r.firstCatchUpSeconds,isNull);expect(r.rebuildSeconds,isNull);expect(r.samples,0);
  }
 });
 test('late one-chart claim and richer keep wallet do not imply guaranteed reset advantage',(){
  final low=estimateRechart(state([100,75,50,25,10],10000,10001,wallet:0));
  final high=estimateRechart(state([100,75,50,25,10],10000,10001,wallet:1000000000000000));
  expect(low.breakEvenSeconds,isNull);expect(high.breakEvenSeconds,isNull);expect(high.keepGainMicros!,greaterThan(low.keepGainMicros!));expect(high.resetGainMicros,low.resetGainMicros);
 });
 test('actual worker handles completion, immediate cancellation, deadlines and bad rules with no source mutation',()async{
  final s=state([100,75,50,25,10],0,10),before=jsonEncode(state([100,75,50,25,10],0,10).toJson());
  final real=RechartForecastTask(s);expect((await real.result)?.toJson(),estimateRechart(s).toJson());real.cancel();
  for(var i=0;i<12;i++){final task=RechartForecastTask(s);task.cancel();task.cancel();expect(await task.result,isNull);}
  final timeout=RechartForecastTask(s,timeout:Duration.zero);expect(await timeout.result,isNull);
  final unsupported=RechartForecastTask(s.copyWith(rulesVersion:'tideglass-economy-9.0.0'));expect((await unsupported.result)?.status,RechartForecastStatus.unsupportedRules);
  await Future<void>.delayed(const Duration(milliseconds:50));expect(jsonEncode(s.toJson()),before);
 });
}
