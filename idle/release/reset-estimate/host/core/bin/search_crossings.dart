import 'dart:convert';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';
void main(){const e=TideglassEngine();var n=0;
for(final charts in [10,25,100,1000,10000])for(final award in [1,2,10,100])for(final wallet in [0,1000000000000,1000000000000000]){
 final s=GameState(counts:[100,75,50,25,10],charts:BigInt.from(charts),walletMicros:BigInt.from(wallet),lifetimeMicros:e.lifetimeForCharts(BigInt.from(charts+award)));
 final r=estimateRechart(s);n++;
 if(r.firstCatchUpSeconds!=null&&r.firstCatchUpSeconds!=r.breakEvenSeconds){print(jsonEncode({'n':n,'charts':charts,'award':award,'wallet':wallet,'result':r.toJson()}));return;}}
 print(jsonEncode({'cases':n,'transient_found':false}));}
