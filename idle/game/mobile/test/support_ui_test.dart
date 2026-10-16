import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/support_screen.dart';

void main() {
  testWidgets(
    'free briefing and boost are real shared-ledger commands at 320px large text',
    (tester) async {
      tester.view.physicalSize = const Size(320, 640);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final game = GameController(
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 16, 12),
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
          home: SupportScreen(game: game),
        ),
      );
      expect(tester.takeException(), isNull);
      final open = find.byKey(const ValueKey('open-briefing'));
      await tester.scrollUntilVisible(open, 250);
      await tester.tap(open);
      await tester.pumpAndSettle();
      final complete = find.byKey(const ValueKey('complete-briefing'));
      await tester.ensureVisible(complete);
      await tester.tap(complete);
      await tester.pumpAndSettle();
      expect(game.state.support.tokens.length, 1);
      expect(game.state.support.tokens.single.spent, isFalse);
      final boost = find.byKey(const ValueKey('use-support-boost'));
      await tester.scrollUntilVisible(boost, 250);
      await tester.tap(boost);
      await tester.pump();
      expect(game.state.support.tokens.single.spent, isTrue);
      expect(game.state.supportRemainingMicros, BigInt.from(1200000000));
      expect(
        game.useSupportBoost(game.state.support.tokens.single.id),
        isFalse,
      );
      expect(tester.takeException(), isNull);
      for (var slot = 1; slot < 6; slot++) {
        expect(game.completeCrewBriefing(slot), isTrue);
      }
      expect(game.completeCrewBriefing(6), isFalse);
      await tester.pump();
      expect(game.state.support.tokens.length, 6);
      expect(tester.takeException(), isNull);
    },
  );
}
