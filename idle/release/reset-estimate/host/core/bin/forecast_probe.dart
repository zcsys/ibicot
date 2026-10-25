import 'dart:convert';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';
void main() {
 const e=TideglassEngine();
 final rows=<Map<String,dynamic>>[];
 for(final chart in [0,10,24,25,99,100,1000]) {
 final target=chart==0?BigInt.from(10):BigInt.from(chart+10);
 final s=GameState(counts:[100,75,50,25,10], lifetimeMicros:e.lifetimeForCharts(target),walletMicros:BigInt.from(1000000000000),charts:BigInt.from(chart));
 final w=Stopwatch()..start();final r=estimateRechart(s);w.stop();
 rows.add({'charts':chart,'milliseconds':w.elapsedMilliseconds,'estimate':r.toJson()});
 }
 print(jsonEncode(rows));
}
