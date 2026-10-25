import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/daily_panel.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const engine=TideglassEngine();
final epoch=DateTime.utc(2026,10,16,12);
GameState dailyState()=>engine.refreshContracts(GameState.initial(),epoch,accountSeed:'qa-fixed',utcOffsetMinutes:0,availableDiscoveryKinds:['archive']).state;
void main() {
  test('clock rollback reload must not delay the next actual account-day boundary',(){
    var now=epoch.subtract(const Duration(days:1));
    final original=dailyState();
    final game=GameController(initialState:original,settledThrough:epoch,clock:()=>now,startTicker:false);
    addTearDown(game.dispose);
    expect(game.state.daily.dayHighWater,original.daily.dayHighWater);
    now=DateTime.utc(2026,10,17);
    game.tick();
    expect(game.state.daily.dayHighWater,original.daily.dayHighWater+1,
      reason:'A preserved future settlement cursor must also preserve the calendar anchor; once real time catches up, next midnight is due.');
    expect(game.state.dailyContracts.length,6);
  });
  test('real repository reload preserves exactly one daily claim',() async {
    final directory=Directory.systemTemp.createTempSync('tideglass-qa-daily-');
    addTearDown(()=>directory.deleteSync(recursive:true));
    SaveRepository repo()=>SaveRepository(directory,economicVersion:economyVersion,economicDigest:'9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',validatePayload:(p)=>GameState.fromJson(Map<String,dynamic>.from(p['core'])));
    var state=engine.advance(dailyState(),const Duration(minutes:20)).state;
    state=engine.buy(state,0,5).state;
    state=engine.recordDiscovery(state,'archive',operationId:'qa-read').state;
    final repository=repo();await repository.load();
    final game=GameController(initialState:state,clock:()=>epoch,startTicker:false,onPersist:(s,t)=>repository.save({'core':s.toJson()},settledThrough:t));
    final contract=game.state.dailyContracts.firstWhere((c)=>engine.contractProgress(game.state,c)==c.target);
    expect(game.claimContract(contract.id),isTrue);
    await game.save();
    final saved=(await repo().load()).snapshot!;
    game.dispose();
    final restored=GameController(initialState:GameState.fromJson(Map<String,dynamic>.from(saved.payload['core'])),settledThrough:saved.settledThrough,clock:()=>epoch,startTicker:false);
    addTearDown(restored.dispose);
    expect(restored.state.surveyNotes,BigInt.from(10));expect(restored.state.passXp,BigInt.from(250));
    expect(restored.claimContract(contract.id),isFalse);
    expect(restored.state.surveyNotes,BigInt.from(10));expect(restored.state.passXp,BigInt.from(250));
  });
  test('long offline return caps backlog and stale command cannot claim expired contract',(){
    var now=epoch;
    final original=dailyState();
    final oldId=original.dailyContracts.first.id;
    final game=GameController(initialState:original,clock:()=>now,startTicker:false);
    addTearDown(game.dispose);
    game.suspend();now=epoch.add(const Duration(days:90));game.resume();
    expect(game.state.dailyContracts.length,21);
    expect(game.state.dailyContracts.every((c)=>c.accountDay>=game.state.daily.dayHighWater-6),isTrue);
    final beforeNotes=game.state.surveyNotes,beforeXp=game.state.passXp;
    expect(game.claimContract(oldId),isFalse);
    expect(game.state.surveyNotes,beforeNotes);expect(game.state.passXp,beforeXp);
    final ids=game.state.dailyContracts.map((c)=>c.id).toSet();
    game.suspend();game.resume();expect(game.state.dailyContracts.map((c)=>c.id).toSet(),ids);
  });
  testWidgets('saving a valid imported automation plan without edits preserves exact run duration',(tester) async {
    final plan=AutomationPlan(id:'plan.base',name:'Ninety seconds',autoResetEnabled:true,minimumRunSeconds:90);
    final game=GameController(initialState:GameState(charts:BigInt.from(100),lifetimeMicros:BigInt.from(10).pow(20),automationPlans:[plan]),clock:()=>epoch,startTicker:false);
    addTearDown(game.dispose);
    await tester.pumpWidget(MaterialApp(theme:tideglassTheme(),home:AutomationScreen(game:game)));
    final save=find.text('Save and select plan');await tester.ensureVisible(save);await tester.tap(save);await tester.pump();
    expect(game.state.selectedAutomationPlan.minimumRunSeconds,90,
      reason:'Opening and saving without edits must not silently change an already supported exact-second plan.');
  });
  testWidgets('320px 200percent daily claim and reroll controls stay laid out',(tester) async {
    tester.view.physicalSize=const Size(320,640);tester.view.devicePixelRatio=1;addTearDown(tester.view.resetPhysicalSize);addTearDown(tester.view.resetDevicePixelRatio);
    final game=GameController(initialState:dailyState(),clock:()=>epoch,startTicker:false);addTearDown(game.dispose);
    await tester.pumpWidget(MaterialApp(theme:tideglassTheme(),builder:(context,child)=>MediaQuery(data:MediaQuery.of(context).copyWith(textScaler:const TextScaler.linear(2)),child:child!),home:Scaffold(body:SingleChildScrollView(child:ContractPanel(game:game)))));
    expect(tester.takeException(),isNull);
    final reroll=find.text('Reroll once').first;await tester.ensureVisible(reroll);await tester.tap(reroll);await tester.pump();
    expect(game.state.dailyContracts.where((c)=>c.rerolled).length,1);expect(tester.takeException(),isNull);
  });
}
