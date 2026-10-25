import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/number_format.dart';
import 'package:tideglass_core/tideglass_core.dart';

const engine = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 16);
GameController controller({GameState? state, PersistGame? save}) =>
    GameController(
      initialState: state,
      startTicker: false,
      clock: () => epoch,
      onPersist: save,
    );
Future<void> showGame(
  WidgetTester tester,
  GameController game, {
  Size size = const Size(390, 844),
  bool largeText = false,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    TideglassApp(
      controller: game,
      initialPreferences: ClientPreferences(
        reduceMotion: true,
        onboardingDismissed: true,
        largeText: largeText,
      ),
    ),
  );
  await tester.pump();
}

void main() {
  test('number display handles micro values and huge exact integers', () {
    expect(compactMicros(BigInt.from(123450000)), '123.45');
    expect(compactMicros(BigInt.from(1234000000)), '1.2K');
    expect(compactMicros(BigInt.from(10).pow(110)), '1.00e104');
    expect(compactFixed(Fixed.integer(20)), '20');
  });
  test(
    'controller persists actual purchase and its exact settlement cursor',
    () async {
      GameState? saved;
      DateTime? boundary;
      final initial = engine
          .advance(GameState.initial(), const Duration(seconds: 60))
          .state;
      final game = controller(
        state: initial,
        save: (s, t) async {
          saved = s;
          boundary = t;
        },
      );
      expect(game.buy(0), isTrue);
      await game.save();
      expect(saved!.counts[0], 2);
      expect(boundary, epoch);
      expect(
        saved!.walletMicros,
        initial.walletMicros - engine.priceMicros(0, 1),
      );
      game.dispose();
    },
  );
  test(
    'an offline settlement is acknowledged without replay or reward grant',
    () {
      final game = GameController(
        startTicker: false,
        settledThrough: epoch,
        clock: () => epoch.add(const Duration(hours: 48)),
      );
      expect(
        game.state.walletMicros,
        BigInt.from(108000) * BigInt.from(1000000),
      );
      expect(game.returnReport!.fullRate, const Duration(hours: 24));
      expect(game.returnReport!.quarterRate, const Duration(hours: 24));
      final settled = game.state.lifetimeMicros;
      game.acknowledgeReturn();
      game.resume();
      expect(game.returnReport, isNull);
      expect(game.state.lifetimeMicros, settled);
      game.dispose();
    },
  );
  test(
    'a failed save stays visible and retry preserves the same progress',
    () async {
      var fail = true;
      final game = controller(
        save: (s, t) async {
          if (fail) throw StateError('disk full');
        },
      );
      await game.save();
      expect(game.saveError, isNotNull);
      fail = false;
      await game.save();
      expect(game.saveError, isNull);
      game.dispose();
    },
  );
  testWidgets(
    'first purchase dispatches actual core command and shows ownership',
    (tester) async {
      final game = controller(
        state: engine
            .advance(GameState.initial(), const Duration(seconds: 60))
            .state,
      );
      addTearDown(game.dispose);
      await showGame(tester, game);
      await tester.ensureVisible(find.byKey(const ValueKey('buy-0')));
      await tester.tap(find.byKey(const ValueKey('buy-0')));
      await tester.pump();
      expect(game.state.counts[0], 2);
      expect(find.textContaining('2 at work'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('locked producers explain previous-tier requirement', (
    tester,
  ) async {
    final game = controller();
    addTearDown(game.dispose);
    await showGame(tester, game);
    expect(find.text('Needs 10 Spark Skiff'), findsOneWidget);
    final buy = tester.widget<FilledButton>(
      find.byKey(const ValueKey('buy-0')),
    );
    expect(buy.onPressed, isNull);
  });
  testWidgets(
    'Rechart requires confirmation and keeps lifetime while rebuilding',
    (tester) async {
      final state = GameState(
        counts: [40, 12, 0, 0, 0],
        walletMicros: BigInt.from(1000000000),
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
      );
      final game = controller(state: state);
      addTearDown(game.dispose);
      await showGame(tester, game);
      await tester.tap(find.text('Atlas'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const ValueKey('preview-rechart')));
      await tester.tap(find.byKey(const ValueKey('preview-rechart')));
      await tester.pumpAndSettle();
      expect(find.textContaining('Claim 10 new Charts'), findsOneWidget);
      await tester.tap(find.text('Keep building'));
      await tester.pumpAndSettle();
      expect(game.state.charts, BigInt.zero);
      expect(game.state.counts[0], 40);
      await tester.tap(find.byKey(const ValueKey('preview-rechart')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('confirm-rechart')));
      await tester.pumpAndSettle();
      expect(game.state.charts, BigInt.from(10));
      expect(game.state.counts, [1, 0, 0, 0, 0]);
      expect(game.state.lifetimeMicros, state.lifetimeMicros);
      expect(game.state.walletMicros, BigInt.zero);
    },
  );
  testWidgets(
    'daily survey collection and Focus buttons use core stored rewards',
    (tester) async {
      final game = controller(
        state: engine
            .advance(GameState.initial(), const Duration(hours: 8))
            .state,
      );
      addTearDown(game.dispose);
      await showGame(tester, game);
      await tester.tap(find.text('Logbook'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const ValueKey('activate-focus')));
      await tester.tap(find.byKey(const ValueKey('activate-focus')));
      await tester.pumpAndSettle();
      for (
        var attempt = 0;
        attempt < 40 &&
            find
                .byKey(const ValueKey('claim-accessible-calibration'))
                .evaluate()
                .isEmpty;
        attempt++
      ) {
        await tester.runAsync(
          () async => Future<void>.delayed(const Duration(milliseconds: 10)),
        );
        await tester.pumpAndSettle();
      }
      await tester.ensureVisible(
        find.byKey(const ValueKey('claim-accessible-calibration')),
      );
      await tester.tap(
        find.byKey(const ValueKey('claim-accessible-calibration')),
      );
      await tester.pump();
      expect(game.state.focusCharges, 3);
      expect(game.state.focusRemainingMicros, BigInt.from(600000000));
      expect(game.state.completedCalibrationIds, {'calibration.01'});
      await tester.pageBack();
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const ValueKey('collect-surveys')));
      await tester.tap(find.byKey(const ValueKey('collect-surveys')));
      await tester.pump();
      expect(game.state.surveyNotes, BigInt.from(10));
      expect(game.state.completedSurveys, 0);
    },
  );
  test(
    'lifecycle resume credits one offline interval and no second resume',
    () {
      var now = epoch;
      final game = GameController(startTicker: false, clock: () => now);
      game.suspend();
      now = now.add(const Duration(hours: 48));
      game.resume();
      final settled = game.state.lifetimeMicros;
      expect(settled, BigInt.from(108000000000));
      game.resume();
      expect(game.state.lifetimeMicros, settled);
      game.dispose();
    },
  );
  test(
    'save queue preserves command order while an earlier write waits',
    () async {
      final blocked = Completer<void>();
      final counts = <int>[];
      var calls = 0;
      final state = engine
          .advance(GameState.initial(), const Duration(seconds: 200))
          .state;
      final game = controller(
        state: state,
        save: (s, t) async {
          if (calls++ == 0) await blocked.future;
          counts.add(s.counts[0]);
        },
      );
      expect(game.buy(0), isTrue);
      expect(game.buy(0), isTrue);
      blocked.complete();
      await game.save();
      expect(counts, [2, 3, 3]);
      game.dispose();
    },
  );
  testWidgets('visible harbor controls have labels and minimum tap targets', (
    tester,
  ) async {
    final game = controller();
    addTearDown(game.dispose);
    final semantics = tester.ensureSemantics();

    await showGame(tester, game);
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    semantics.dispose();
  });
  testWidgets('onboarding action moves the first purchase into view', (
    tester,
  ) async {
    final game = controller(
      state: engine
          .advance(GameState.initial(), const Duration(seconds: 60))
          .state,
    );
    addTearDown(game.dispose);
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      TideglassApp(
        controller: game,
        initialPreferences: const ClientPreferences(reduceMotion: true),
      ),
    );
    await tester.pump();
    final start = find.text('Let’s begin');
    await tester.ensureVisible(start);
    await tester.tap(start);
    await tester.pumpAndSettle();
    final purchase = find.byKey(const ValueKey('buy-0'));
    expect(tester.getRect(purchase).bottom, lessThan(844 - 74));
    await tester.tap(purchase);
    await tester.pump();
    expect(game.state.counts[0], 2);
  });
  testWidgets(
    'return acknowledgement closes a settled reward without another grant',
    (tester) async {
      final game = GameController(
        startTicker: false,
        settledThrough: epoch,
        clock: () => epoch.add(const Duration(hours: 48)),
      );
      addTearDown(game.dispose);
      await showGame(tester, game);
      await tester.pumpAndSettle();
      expect(find.text('The harbor kept its light.'), findsOneWidget);
      final before = game.state.lifetimeMicros;
      await tester.tap(find.text('Welcome the light'));
      await tester.pumpAndSettle();
      expect(game.returnReport, isNull);
      expect(game.state.lifetimeMicros, before);
      expect(find.text('The harbor kept its light.'), findsNothing);
    },
  );
  for (final size in [const Size(320, 640), const Size(1024, 768)]) {
    testWidgets('critical layouts fit $size at 200 percent text', (
      tester,
    ) async {
      final game = controller();
      addTearDown(game.dispose);
      tester.platformDispatcher.textScaleFactorTestValue = 2;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await showGame(tester, game, size: size);
      expect(tester.takeException(), isNull);
      await tester.tap(find.text('Atlas'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.tap(find.text('Logbook'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
