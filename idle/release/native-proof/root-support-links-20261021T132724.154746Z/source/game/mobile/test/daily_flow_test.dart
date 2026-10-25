import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/daily_panel.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  const engine = TideglassEngine();
  final epoch = DateTime.utc(2026, 10, 16, 12);
  testWidgets('completed contract pays once through the actual claim control', (
    tester,
  ) async {
    var state = engine
        .refreshContracts(
          GameState.initial(),
          epoch,
          accountSeed: 'daily-flow',
          availableDiscoveryKinds: ['archive'],
        )
        .state;
    state = engine.advance(state, const Duration(minutes: 20)).state;
    state = engine.buy(state, 0, 5).state;
    state = engine
        .recordDiscovery(
          state,
          'archive',
          operationSequence: state.nextDiscoverySequence,
        )
        .state;
    final game = GameController(
      initialState: state,
      clock: () => epoch,
      startTicker: false,
    );
    addTearDown(game.dispose);
    final contract = game.state.dailyContracts.first;
    expect(engine.contractProgress(game.state, contract), contract.target);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        home: Scaffold(
          body: ListenableBuilder(
            listenable: game,
            builder: (_, _) =>
                SingleChildScrollView(child: ContractPanel(game: game)),
          ),
        ),
      ),
    );
    final claim = find.byKey(ValueKey('claim-${contract.id}'));
    await tester.ensureVisible(claim);
    await tester.tap(claim);
    await tester.pump();
    expect(game.state.surveyNotes, BigInt.from(10));
    expect(game.state.passXp, BigInt.from(250));
    expect(game.claimContract(contract.id), isFalse);
    expect(game.state.surveyNotes, BigInt.from(10));
    expect(game.state.passXp, BigInt.from(250));
  });
  testWidgets(
    'automation editor uses freeplan and respects narrowlarge-text layout',
    (tester) async {
      tester.view.physicalSize = const Size(320, 640);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final game = GameController(
        initialState: GameState(
          charts: BigInt.from(100),
          lifetimeMicros: BigInt.from(10).pow(20),
        ),
        clock: () => epoch,
        startTicker: false,
      );
      addTearDown(game.dispose);
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: const TextScaler.linear(2)),
            child: child!,
          ),
          home: AutomationScreen(game: game),
        ),
      );
      await tester.pump();
      expect(tester.takeException(), isNull);
      final save = find.text('Save and select plan');
      await tester.ensureVisible(save);
      await tester.tap(save);
      await tester.pump();
      expect(game.state.automationPlans.length, 1);
      expect(game.state.surveyNotes, BigInt.zero);
      expect(game.state.selectedAutomationPlan.autoResetEnabled, isFalse);
      expect(tester.takeException(), isNull);
    },
  );
}
