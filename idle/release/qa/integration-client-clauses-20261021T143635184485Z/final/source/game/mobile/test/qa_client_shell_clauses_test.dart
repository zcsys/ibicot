import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/number_format.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';

import 'content_presentation_probe.dart';

Future<void> readNestedParagraph(
  WidgetTester tester,
  ContentProbe probe,
  String english,
) async {
  final display = Presentation.text(english);
  final text = find.text(display);
  expect(text, findsOneWidget);
  final rich = find.descendant(of: text, matching: find.byType(RichText));
  final paragraph = tester.renderObject<RenderParagraph>(rich);
  expect(paragraph.text.toPlainText(), display);
  expect(paragraph.didExceedMaxLines, false);
  final lines = <String, Rect>{};
  for (final match in RegExp(r'\S+').allMatches(display)) {
    final boxes = paragraph.getBoxesForSelection(
      TextSelection(baseOffset: match.start, extentOffset: match.end),
    );
    expect(boxes, isNotEmpty);
    for (final box in boxes) {
      final key = '${box.top}:${box.bottom}';
      lines[key] = lines[key]?.expandToInclude(box.toRect()) ?? box.toRect();
    }
  }
  expect(lines, isNotEmpty);
  for (final line in lines.values) {
    // This real render-object protocol propagates through both the inner
    // content scroll and the outer fullscreen dialog scroll.
    paragraph.showOnScreen(rect: line, duration: Duration.zero);
    await tester.pumpAndSettle();
    probe.inside(
      MatrixUtils.transformRect(paragraph.getTransformTo(null), line),
      probe.visible(paragraph),
      'nested dialog complete line',
    );
  }
}

void main() {
  testWidgets(
    'client shell wallet output milestone purchase reset and settings',
    (tester) async {
      const engine = TideglassEngine();
      final game = GameController(
        initialState: GameState(
          counts: [24, 10, 10, 10, 10],
          charts: BigInt.from(25),
          lifetimeMicros: engine.lifetimeForCharts(BigInt.from(35)),
          walletMicros: BigInt.from(1000000000000),
        ),
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 21),
      );
      addTearDown(game.dispose);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      final p = ContentProbe(tester);
      await p.show(
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
      final after = engine.buy(before, 0, 1).state;
      final oldSum = List.generate(
        5,
        (i) => engine.producerOutputPerSecond(before, i),
      ).fold(Fixed.zero, (a, b) => a + b);
      final newSum = List.generate(
        5,
        (i) => engine.producerOutputPerSecond(after, i),
      ).fold(Fixed.zero, (a, b) => a + b);
      final direct =
          engine.producerOutputPerSecond(after, 0) -
          engine.producerOutputPerSecond(before, 0);
      final network = newSum - oldSum;
      expect(network.raw, greaterThan(direct.raw));
      expect(engine.marginalOutputPerSecond(before, 0).raw, network.raw);
      await p.read(
        'wallet',
        compactMicros(before.walletMicros),
        within: keyed('wallet'),
      );
      await p.read('output', '+${compactFixed(oldSum)}');
      final producer = keyed('producer-0');
      await p.read(
        'milestone25',
        UiEnglish.appNextMilestoneLightkeepersDoubleThisTier(25),
        within: producer,
      );
      await p.read(
        'network-preview',
        UiEnglish.appRateGameEngineMarginalOutputPerSecondSTierQuantity(
          compactFixed(network),
        ),
        within: producer,
      );
      await p.checkControl('buy-real-milestone', keyed('buy-0'), tap: true);
      expect(game.state.counts[0], 25);
      expect(game.state.walletMicros, after.walletMicros);
      expect(game.state.lifetimeMicros, before.lifetimeMicros);
      expect(engine.outputPerSecond(game.state).raw - oldSum.raw, network.raw);
      await p.read(
        'milestone50',
        UiEnglish.appNextMilestoneLightkeepersDoubleThisTier(50),
        within: producer,
      );
      await p.read(
        'purchase-assumptions',
        UiCopy.forecastsAssumeAFixedFleetAnd,
      );
      await p.checkControl(
        'atlas-tab',
        find.byType(NavigationDestination).at(1),
        tap: true,
      );
      await p.read('reset-not-optimal', Copy.noPerfectReset);
      final beforeCancel = game.state.toJson();
      await p.checkControl(
        'preview-reset',
        keyed('preview-rechart'),
        tap: true,
      );
      await readNestedParagraph(tester, p, Copy.rechartKept);
      await readNestedParagraph(tester, p, Copy.rechartLost);
      await p.checkControl(
        'cancel-reset',
        named(UiCopy.keepBuilding),
        tap: true,
      );
      expect(game.state.toJson(), beforeCancel);
      await p.checkControl(
        'preview-reset-again',
        keyed('preview-rechart'),
        tap: true,
      );
      await p.checkControl(
        'confirm-reset',
        keyed('confirm-rechart'),
        tap: true,
      );
      expect(game.state.charts, BigInt.from(35));
      expect(game.state.counts, [1, 0, 0, 0, 0]);
      expect(game.state.lifetimeMicros, before.lifetimeMicros);
      expect(game.state.walletMicros, BigInt.zero);
      await p.checkControl(
        'settings',
        find.byTooltip(Presentation.text(Copy.settings)),
        tap: true,
      );
      await p.read('settings-heading', Copy.settings);
      await p.read('motion-setting', Copy.reducedMotion);
      await p.read('text-setting', Copy.largerText);
      await p.read('notation-setting', Copy.scientific);
      await p.checkControl(
        'close-settings',
        named(UiCopy.returnToTheHarbor),
        tap: true,
      );
      expect(game.state.charts, BigInt.from(35));
      expect(tester.takeException(), isNull);
    },
  );
}
