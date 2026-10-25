// Focused S04 integration evidence: genuine mode/button gestures, independently
// summed rational prices and unboosted output. Seeded host UI, not player pacing.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/number_format.dart';
import 'package:tideglass/producer_art.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';

import 'content_presentation_probe.dart';

BigInt cumulativeOracle(int tier, int count) {
  if (count == 0) return BigInt.zero;
  final base = BigInt.from(30000000) * BigInt.from(20).pow(tier);
  var numerator = base;
  var denominator = BigInt.one;
  for (var purchase = 1; purchase < count; purchase++) {
    numerator =
        numerator * BigInt.from(25) + base * BigInt.from(28).pow(purchase);
    denominator *= BigInt.from(25);
  }
  return (numerator + denominator - BigInt.one) ~/ denominator;
}

BigInt priceOracle(int tier, int owned, int quantity) =>
    cumulativeOracle(tier, owned + quantity) - cumulativeOracle(tier, owned);

BigInt outputOracle(List<int> counts) {
  var total = BigInt.zero;
  for (var tier = 0; tier < 5; tier++) {
    final stage = (counts[tier] ~/ 25).clamp(0, 4);
    total +=
        BigInt.from(counts[tier]) *
        BigInt.from(20).pow(tier) *
        BigInt.from(2).pow(stage);
  }
  return total * Fixed.scale;
}

void main() {
  WidgetController.hitTestWarningShouldBeFatal = true;
  Future<void> verify(
    WidgetTester tester, {
    required PurchaseMode mode,
    required int tier,
    required int owned,
    required int expectedQuantity,
    required BigInt wallet,
    bool disabled = false,
  }) async {
    final counts = List<int>.filled(5, 23)..[tier] = owned;
    final initial = GameState(
      counts: counts,
      walletMicros: wallet,
      lifetimeMicros: BigInt.from(10).pow(18),
    );
    final game = GameController(
      initialState: initial,
      startTicker: false,
      clock: () => DateTime.utc(2026, 10, 23),
    );
    addTearDown(game.dispose);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    final probe = ContentProbe(tester);
    await probe.show(
      TideglassApp(
        controller: game,
        initialPreferences: const ClientPreferences(
          reduceMotion: true,
          onboardingDismissed: true,
        ),
      ),
      app: true,
    );
    final before = game.state;
    final completeBefore = before.toJson();
    // A single purchase is selected through its real control too, after first
    // selecting another mode. No controller mode setter or callback is invoked.
    if (mode == PurchaseMode.single) {
      await probe.checkControl(
        'select-max-first',
        named(UiCopy.buyMax),
        tap: true,
      );
    }
    final label = switch (mode) {
      PurchaseMode.single => UiCopy.buy,
      PurchaseMode.milestone => UiEnglish.appMilestone,
      PurchaseMode.maximum => UiCopy.buyMax,
    };
    await probe.checkControl('select-$mode', named(label), tap: true);
    expect(game.purchaseMode, mode);
    expect(game.state.toJson(), completeBefore);
    expect(game.engine.outputPerSecond(before).raw, outputOracle(counts));
    final button = keyed('buy-$tier');
    final producer = keyed('producer-$tier');
    final price = priceOracle(tier, owned, expectedQuantity);
    await probe.read('purchase-price', compactMicros(price), within: producer);
    if (disabled) {
      await probe.checkControl('unaffordable', button, enabled: false);
      expect(tester.widget<FilledButton>(button).onPressed, isNull);
      await tester.tap(button);
      await tester.pumpAndSettle();
      expect(game.state.toJson(), completeBefore);
    } else {
      await probe.read(
        'purchase-quantity',
        UiEnglish.appBuildQuantity(expectedQuantity),
        within: producer,
      );
      await probe.checkControl('actual-purchase', button, tap: true);
      final afterCounts = counts.toList()..[tier] += expectedQuantity;
      expect(game.state.counts, afterCounts);
      expect(game.state.walletMicros, wallet - price);
      expect(game.state.walletMicros.isNegative, isFalse);
      expect(game.state.lifetimeMicros, before.lifetimeMicros);
      expect(game.state.charts, before.charts);
      expect(game.state.surveyNotes, before.surveyNotes);
      expect(
        game.engine.outputPerSecond(game.state).raw,
        outputOracle(afterCounts),
      );
      final art = tester.widget<StagedProducerArt>(
        find.descendant(of: producer, matching: find.byType(StagedProducerArt)),
      );
      expect(art.tier, tier);
      expect(art.count, owned + expectedQuantity);
      final paints = tester.widgetList<CustomPaint>(
        find.descendant(of: producer, matching: find.byType(CustomPaint)),
      );
      final painter = paints
          .map((p) => p.painter)
          .whereType<ProducerStagePainter>()
          .single;
      expect(painter.stage, ((owned + expectedQuantity) ~/ 25).clamp(0, 4));
      if (mode == PurchaseMode.maximum) {
        expect(
          game.state.walletMicros,
          lessThan(priceOracle(tier, owned + expectedQuantity, 1)),
        );
        expect(tester.widget<FilledButton>(button).onPressed, isNull);
        final exhausted = game.state.toJson();
        await tester.tap(button);
        await tester.pumpAndSettle();
        expect(game.state.toJson(), exhausted);
      }
    }
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  }

  testWidgets('single UI purchase crosses 25 at exact price', (tester) async {
    await verify(
      tester,
      mode: PurchaseMode.single,
      tier: 0,
      owned: 24,
      expectedQuantity: 1,
      wallet: priceOracle(0, 24, 1),
    );
  });
  testWidgets('single UI rejects one micro below the price', (tester) async {
    await verify(
      tester,
      mode: PurchaseMode.single,
      tier: 0,
      owned: 24,
      expectedQuantity: 1,
      wallet: priceOracle(0, 24, 1) - BigInt.one,
      disabled: true,
    );
  });
  for (final milestone in [25, 50, 75, 100]) {
    testWidgets('milestone UI buys exactly to $milestone', (tester) async {
      await verify(
        tester,
        mode: PurchaseMode.milestone,
        tier: 0,
        owned: milestone - 2,
        expectedQuantity: 2,
        wallet: priceOracle(0, milestone - 2, 2),
      );
    });
  }
  for (var tier = 0; tier < 5; tier++) {
    for (final short in [false, true]) {
      testWidgets(
        'max UI tier $tier with ${short ? 'one-micro-short' : 'exact'} budget',
        (tester) async {
          await verify(
            tester,
            mode: PurchaseMode.maximum,
            tier: tier,
            owned: 23,
            expectedQuantity: short ? 2 : 3,
            wallet:
                priceOracle(tier, 23, 3) - (short ? BigInt.one : BigInt.zero),
          );
        },
      );
    }
  }
}
