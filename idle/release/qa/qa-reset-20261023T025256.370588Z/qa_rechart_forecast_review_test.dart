import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/number_format.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/rechart_copy.dart';
import 'package:tideglass/rechart_estimate.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';
import 'content_presentation_probe.dart';

final observations=<Map<String,Object?>>[];
Future<void> fonts(WidgetTester tester)async{
 await tester.runAsync(()async{
  for(final e in {'Roboto':'Roboto-Regular.ttf','MaterialIcons':'MaterialIcons-Regular.otf'}.entries){
   final f=File('../../.tooling/flutter/bin/cache/artifacts/material_fonts/${e.value}');
   await(FontLoader(e.key)..addFont(f.readAsBytes().then(ByteData.sublistView))).load();
  }
 });
}
Future<void> read(WidgetTester tester,ContentProbe p,String text)async{
 final display=Presentation.text(text), finder=find.text(Presentation.text(text));expect(finder,findsOneWidget);
 final rich=find.descendant(of:finder,matching:find.byType(RichText));expect(rich,findsOneWidget);
 final paragraph=tester.renderObject<RenderParagraph>(rich);expect(paragraph.text.toPlainText(),display);expect(paragraph.didExceedMaxLines,false);
 final lines=<String,Rect>{};
 for(final word in RegExp(r'\S+').allMatches(display)){
  final boxes=paragraph.getBoxesForSelection(TextSelection(baseOffset:word.start,extentOffset:word.end));expect(boxes,isNotEmpty);
  for(final box in boxes){final id='${box.top}:${box.bottom}';lines[id]=lines[id]?.expandToInclude(box.toRect())??box.toRect();}
 }
 final entries=<Map<String,Object?>>[];
 for(final line in lines.values){
  paragraph.showOnScreen(rect:line,duration:Duration.zero);await tester.pumpAndSettle();
  final r=MatrixUtils.transformRect(paragraph.getTransformTo(null),line),v=p.visible(paragraph);
  p.inside(r,v,'actual nested dialog visible glyph line');entries.add({'rect':[r.left,r.top,r.right,r.bottom],'viewport':[v.left,v.top,v.right,v.bottom]});
 }
 observations.add({'type':'text','display':display,'complete':true,'untruncated':true,'lines':entries});
}
Future<RechartForecast?> resolve(WidgetTester tester)async{
 final panel=find.byKey(const ValueKey('rechart-estimate'));
 final future=tester.widget<FutureBuilder<RechartForecast?>>(find.descendant(of:panel,matching:find.byType(FutureBuilder<RechartForecast?>))).future!;
 var done=false;RechartForecast? result;future.then((v){done=true;result=v;});
 for(var i=0;i<120&&!done;i++){await tester.runAsync(()=>Future<void>.delayed(const Duration(milliseconds:20)));await tester.pump(const Duration(milliseconds:20));}
 expect(done,true);await tester.pumpAndSettle();return result;
}
void setup(WidgetTester tester){
 addTearDown(tester.view.resetPhysicalSize);addTearDown(tester.view.resetDevicePixelRatio);addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
}
void main(){
 tearDownAll((){const output=String.fromEnvironment('QA_RESET_REPORT');if(output.isNotEmpty){File(output).writeAsStringSync('${const JsonEncoder.withIndent('  ').convert({'viewport':contentViewport,'scale':contentTextPercent,'pseudo':Presentation.pseudoEnabled,'observations':observations})}\n');}});
 testWidgets('actual reset estimate: every glyph line, exact worker and real cancel/current-state confirmation',(tester)async{
  setup(tester);await fonts(tester);const e=TideglassEngine();var now=DateTime.utc(2026,10,23);
  final g=GameController(initialState:GameState(counts:[100,75,50,25,10],walletMicros:BigInt.from(1000000000000),lifetimeMicros:e.lifetimeForCharts(BigInt.from(10))),startTicker:false,clock:()=>now);addTearDown(g.dispose);
  final p=ContentProbe(tester);await p.show(TideglassApp(controller:g,initialPreferences:const ClientPreferences(onboardingDismissed:true,reduceMotion:true)),app:true);
  await p.checkControl('atlas',find.byType(NavigationDestination).at(1),tap:true);
  final snapshot=g.state,before=jsonEncode(g.state.toJson());
  await p.checkControl('open',keyed('preview-rechart'),tap:true);final result=await resolve(tester);expect(result?.toJson(),estimateRechart(snapshot).toJson());expect(jsonEncode(g.state.toJson()),before);
  for(final text in [RechartCopy.title,RechartCopy.breakEven(durationLabel(Duration(seconds:result!.breakEvenSeconds!))),RechartCopy.definition,RechartCopy.rebuild(durationLabel(Duration(seconds:result.rebuildSeconds!))),RechartCopy.unlocked(RechartCopy.autoBuy),RechartCopy.nextUnlock(BigInt.from(25),RechartCopy.synergy),RechartCopy.assumptionsTitle,RechartCopy.purchases,RechartCopy.continuation,RechartCopy.objective,RechartCopy.snapshot]){await read(tester,p,text);}
  final panel=tester.widget<RechartEstimatePanel>(keyed('rechart-estimate'));expect(identical(panel.snapshot,snapshot),true);
  // Actual controller updates while the dialog remains open must not silently
  // replace the opening estimate or roll back earned income on cancellation.
  now=now.add(const Duration(minutes:1));g.tick();await tester.pumpAndSettle();
  expect(g.state.lifetimeMicros,greaterThan(snapshot.lifetimeMicros));expect(identical(tester.widget<RechartEstimatePanel>(keyed('rechart-estimate')).snapshot,snapshot),true);
  final beforeCancel=jsonEncode(g.state.toJson());await p.checkControl('keep',named('Keep building'),tap:true);expect(jsonEncode(g.state.toJson()),beforeCancel);
  await p.checkControl('reopen',keyed('preview-rechart'),tap:true);expect(identical(tester.widget<RechartEstimatePanel>(keyed('rechart-estimate')).snapshot,g.state),true);
  final expected=e.rechart(g.state).state;await p.checkControl('confirm',keyed('confirm-rechart'),tap:true);
  expect(g.state.counts,expected.counts);expect(g.state.charts,expected.charts);expect(g.state.walletMicros,expected.walletMicros);expect(g.state.lifetimeMicros,expected.lifetimeMicros);
  observations.add({'type':'actual-actions','controls':p.controls,'opening_unchanged':true,'snapshot_stable':true,'cancel_keeps_new_income':true,'confirm_current_state':true});expect(tester.takeException(),isNull);await tester.pumpWidget(const SizedBox.shrink());
 });
 testWidgets('actual no-catch-up and bounded-unavailable states remain readable with working choices',(tester)async{
  setup(tester);await fonts(tester);const e=TideglassEngine();
  for(final limited in [false,true]){
   final initial=GameState(counts:limited?[10001,0,0,0,0]:[100,75,50,25,10],charts:BigInt.from(10000),walletMicros:BigInt.from(1000000000000),lifetimeMicros:e.lifetimeForCharts(BigInt.from(10001)));
   final g=GameController(initialState:initial,startTicker:false,clock:()=>DateTime.utc(2026,10,23));final p=ContentProbe(tester);
   await p.show(TideglassApp(controller:g,initialPreferences:const ClientPreferences(onboardingDismissed:true,reduceMotion:true)),app:true);
   await p.checkControl('atlas',find.byType(NavigationDestination).at(1),tap:true);final before=jsonEncode(g.state.toJson());await p.checkControl('open',keyed('preview-rechart'),tap:true);
   final result=await resolve(tester);expect(result?.status,limited?RechartForecastStatus.inputLimit:RechartForecastStatus.estimated);
   await read(tester,p,limited?RechartCopy.unavailable:RechartCopy.noCatchUp);
   if(!limited){expect(result?.breakEvenSeconds,isNull);for(final text in [RechartCopy.purchases,RechartCopy.continuation,RechartCopy.objective,RechartCopy.snapshot]){await read(tester,p,text);}}
   await p.checkControl('confirm-available',keyed('confirm-rechart'));await p.checkControl('keep',named('Keep building'),tap:true);expect(jsonEncode(g.state.toJson()),before);
   observations.add({'type':limited?'unavailable':'no-catch-up','controls':p.controls,'unchanged':true});await tester.pumpWidget(const SizedBox.shrink());g.dispose();
  }
 });
}
