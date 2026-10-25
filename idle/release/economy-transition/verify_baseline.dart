import 'dart:convert';
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  const engine = TideglassEngine();
  final rows = <Map<String,dynamic>>[];
  void record(String id, TransitionResult result) {
    final state = result.state;
    rows.add({'id':id,'accepted':result.accepted,'reason':result.reason,
      'state':state.toJson(),
      'events':result.events.map((e)=>e.toJson()).toList(),
      'output_raw':engine.outputPerSecond(state).raw.toString(),
      'prices':[for(var t=0;t<5;t++)engine.priceMicros(t,state.counts[t]).toString()],
      'prestige_award':engine.prestigeAward(state).toString()});
  }
  record('initial', TransitionResult(GameState.initial()));
  record('fraction', engine.advance(GameState.initial(), const Duration(microseconds:1)));
  record('offline_tail',engine.advance(GameState.initial(),const Duration(hours:36),offline:true));
  final earned=BigInt.from(10).pow(18);
  final developed=GameState(counts:[100,75,50,25,10],walletMicros:earned,
      lifetimeMicros:earned,charts:BigInt.from(100),autoBuyEnabled:true);
  record('developed',TransitionResult(developed));
  record('automated',engine.advance(developed,const Duration(seconds:3)));
  final price=engine.priceMicros(0,1);
  for(final delta in [-1,0,1]) {
    final wallet=price+BigInt.from(delta);
    record('purchase_$delta',engine.buy(GameState(walletMicros:wallet,lifetimeMicros:wallet),0,1));
  }
  record('prestige_boundary',engine.rechart(GameState(
      lifetimeMicros:TideglassEngine.firstPrestigeMicros,
      walletMicros:TideglassEngine.firstPrestigeMicros)));
  final at=DateTime.utc(2026,10,21,12);
  var daily=engine.refreshContracts(GameState.initial(),at,accountSeed:'baseline-parity').state;
  record('daily',TransitionResult(daily));
  daily=engine.advance(daily,const Duration(hours:8)).state;
  daily=engine.collectSurveys(daily).state;
  daily=engine.activateFocus(daily).state;
  daily=engine.claimSupportToken(daily,accountDay:daily.daily.dayHighWater,slot:0,
      sourceId:engine.briefingSourceId(daily,0)).state;
  daily=engine.useSupportBoost(daily,daily.support.tokens.single.id).state;
  record('bonuses',engine.advance(daily,const Duration(seconds:123,microseconds:456789)));
  print(jsonEncode(rows));
}
