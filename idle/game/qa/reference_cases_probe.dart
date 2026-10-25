import 'dart:convert';
import 'dart:io';
import 'package:tideglass_core/tideglass_core.dart';

void main(List<String> args) {
  const engine = TideglassEngine();
  final cases = jsonDecode(File(args[0]).readAsStringSync())['cases'] as Map;
  final million=BigInt.from(1000000);
  BigInt wholeMicros(num n)=>BigInt.from(n.toInt())*million;
  var checks=0;
  final failures=<String>[];
  void check(bool ok,String name){checks++;if(!ok) failures.add(name);}
  bool close(num a,num b)=> (a-b).abs()<=b.abs()*1e-8+0.0000011;
  GameState fromLegacy(Map d,{bool normalizeSyntheticLifetime=false}) {
    final charts=BigInt.from(d['charts']);
    var lifetime=wholeMicros(d['lifetime']);
    if(normalizeSyntheticLifetime && charts>BigInt.zero && lifetime<engine.lifetimeForCharts(charts)) lifetime=engine.lifetimeForCharts(charts);
    return GameState(counts:List<int>.from(d['counts']),walletMicros:wholeMicros(d['wallet']),lifetimeMicros:lifetime,charts:charts,elapsedMicros:wholeMicros(d['time']));
  }
  for(final c in cases['reset']) {
    final state=fromLegacy(c['input']), expected=c['expected'];
    final result=engine.rechart(state), target=fromLegacy(expected['state']);
    final same=result.state.counts.join(',')==target.counts.join(',') && result.state.walletMicros==target.walletMicros && result.state.lifetimeMicros==target.lifetimeMicros && result.state.charts==target.charts && result.state.elapsedMicros==target.elapsedMicros;
    check(result.accepted==expected['accepted'] && same,c['id']);
    check(result.state.charts-state.charts==BigInt.from(expected['awarded_charts']),'${c['id']}:award');
    check(!engine.rechart(result.state).accepted,'${c['id']}:repeat');
  }
  for(final c in cases['marginal_purchase']) {
    final state=fromLegacy(c['input']['state'],normalizeSyntheticLifetime:true);
    final tier=c['input']['buy_one_tier_index'] as int;
    check(close(engine.priceMicros(tier,state.counts[tier]).toDouble()/1e6,c['expected']['cost_radiance']),'${c['id']}:cost');
    check(close(double.parse(engine.marginalOutputPerSecond(state,tier).toDecimalString(decimals: 24)),c['expected']['full_delta_radiance_per_second']),'${c['id']}:network');
  }
  for(final c in cases['purchase_choice']) {
    final state=fromLegacy(c['input']);
    final tier=engine.chooseAutoBuyTier(state);
    check(tier==c['expected']['tier_index'],c['id']);
    check(close(engine.priceMicros(tier,state.counts[tier]).toDouble()/1e6,c['expected']['price_radiance']),'${c['id']}:cost');
  }
  for(final c in cases['offline_envelope']) {
    final state=engine.advance(GameState.initial(),Duration(seconds:c['input']['absence_real_seconds']),offline:true).state;
    final expected=BigInt.from((c['expected_effective_production_seconds'] as num)*1000000);
    check(state.walletMicros==expected && state.lifetimeMicros==expected,c['id']);
  }
  print(jsonEncode({'fixture_cases':22,'checks':checks,'passed':failures.isEmpty,'failures':failures,'notes':['Complements the 91 directly consumed cases in frozen core tests.','Legacy marginal fixtures have synthetic 100 Charts with zero lifetime. Probe supplies minimum supporting lifetime to satisfy production validation; all output inputs remain unchanged.','Continuous float reference comparison uses 1e-8 relative plus 1.1 micro absolute; no tolerance controls purchases, reset grants or offline accounting.']}));
  if(failures.isNotEmpty) exitCode=1;
}
