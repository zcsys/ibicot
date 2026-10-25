import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/rechart_copy.dart';
import 'package:tideglass/rechart_estimate.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';

RechartForecast sample({bool caught = true}) => RechartForecast(
  status: RechartForecastStatus.estimated,
  horizonSeconds: 86400,
  samples: 1440,
  work: 6700,
  firstCatchUpSeconds: caught ? 1560 : null,
  breakEvenSeconds: caught ? 1560 : null,
  rebuildSeconds: 720,
  keepGainMicros: BigInt.from(100),
  resetGainMicros: BigInt.from(caught ? 200 : 90),
  nextChartTarget: BigInt.from(25),
  unlockedChartThresholds: [10],
);

void configure(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  tester.platformDispatcher.textScaleFactorTestValue = 2;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
}

Future<void> loadFonts(WidgetTester tester) async {
  await tester.runAsync(() async {
    for (final entry in {
      'Roboto': 'Roboto-Regular.ttf',
      'MaterialIcons': 'MaterialIcons-Regular.otf',
    }.entries) {
      final file = File(
        '../../.tooling/flutter/bin/cache/artifacts/material_fonts/${entry.value}',
      );
      await (FontLoader(
        entry.key,
      )..addFont(file.readAsBytes().then(ByteData.sublistView))).load();
    }
  });
}

Future<void> capture(
  WidgetTester tester,
  GlobalKey boundaryKey,
  String name,
) async {
  const output = String.fromEnvironment('TIDEGLASS_RESET_EVIDENCE');
  if (output.isEmpty) return;
  final boundary =
      boundaryKey.currentContext!.findRenderObject()! as RenderRepaintBoundary;
  await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 1);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    final file = File(
      '$output/${Presentation.pseudoEnabled ? 'pseudo' : 'english'}-$name.png',
    );
    await file.parent.create(recursive: true);
    await file.writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

void main() {
  for (final width in [320, 1024]) {
    final size = Size(width.toDouble(), width == 320 ? 720 : 768);
    for (final mode in [
      'estimated',
      'no-catch-up',
      'unavailable',
      'not-eligible',
      'loading',
    ]) {
      testWidgets('$width px 200percent real ReadingDialog $mode', (
        tester,
      ) async {
        configure(tester, size);
        await loadFonts(tester);
        final result = switch (mode) {
          'estimated' => sample(),
          'no-catch-up' => sample(caught: false),
          'not-eligible' => const RechartForecast(
            status: RechartForecastStatus.notEligible,
            horizonSeconds: 86400,
            samples: 0,
            work: 0,
          ),
          _ => null,
        };
        var confirmed = false;
        await tester.pumpWidget(
          MaterialApp(
            theme: tideglassTheme(),
            home: Scaffold(
              body: ReadingDialog(
                title: const LocalizedText('Rechart preview'),
                content: SingleChildScrollView(
                  child: RechartEstimateContent(
                    forecast: result,
                    loading: mode == 'loading',
                  ),
                ),
                actions: [
                  FilledButton(
                    key: const ValueKey('test-confirm'),
                    onPressed: () => confirmed = true,
                    child: const LocalizedText('Rechart'),
                  ),
                ],
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        expect(find.text(Presentation.text(RechartCopy.title)), findsOneWidget);
        if (result?.status == RechartForecastStatus.estimated) {
          for (final copy in [
            RechartCopy.purchases,
            RechartCopy.continuation,
            RechartCopy.objective,
            RechartCopy.snapshot,
          ]) {
            final text = find.text(Presentation.text(copy));
            await tester.ensureVisible(text);
            await tester.pumpAndSettle();
            expect(text.hitTestable(), findsOneWidget);
            expect(tester.takeException(), isNull);
          }
        }
        final button = find.byKey(const ValueKey('test-confirm'));
        await tester.ensureVisible(button);
        await tester.pumpAndSettle();
        await tester.tap(button);
        expect(confirmed, isTrue);
        expect(tester.takeException(), isNull);
      });
    }
    testWidgets(
      '$width px actual Atlas estimate, readable assumptions and Rechart actions',
      (tester) async {
        configure(tester, size);
        await loadFonts(tester);
        const engine = TideglassEngine();
        final game = GameController(
          initialState: GameState(
            counts: [100, 75, 50, 25, 10],
            walletMicros: BigInt.from(1000000000000),
            lifetimeMicros: engine.lifetimeForCharts(BigInt.from(10)),
          ),
          startTicker: false,
          clock: () => DateTime.utc(2026, 10, 21),
        );
        addTearDown(game.dispose);
        final before = game.state.toJson(), boundary = GlobalKey();
        await tester.pumpWidget(
          RepaintBoundary(
            key: boundary,
            child: TideglassApp(
              controller: game,
              initialPreferences: const ClientPreferences(
                onboardingDismissed: true,
                reduceMotion: true,
              ),
            ),
          ),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.byType(NavigationDestination).at(1));
        await tester.pumpAndSettle();
        final preview = find.byKey(const ValueKey('preview-rechart'));
        await tester.ensureVisible(preview);
        await tester.tap(preview);
        await tester.pump();
        final panel = find.byKey(const ValueKey('rechart-estimate'));
        expect(panel, findsOneWidget);
        final future = tester
            .widget<FutureBuilder<RechartForecast?>>(
              find.descendant(
                of: panel,
                matching: find.byType(FutureBuilder<RechartForecast?>),
              ),
            )
            .future!;
        // The widget created this task in Flutter's fake-async zone. Pump that
        // zone while yielding real time for the isolate; awaiting its Future
        // only inside runAsync would strand the fake-zone completion callback.
        RechartForecast? result;
        var completed = false;
        future.then((value) {
          result = value;
          completed = true;
        });
        for (var attempt = 0; attempt < 120 && !completed; attempt++) {
          await tester.runAsync(
            () => Future<void>.delayed(const Duration(milliseconds: 20)),
          );
          await tester.pump(const Duration(milliseconds: 20));
        }
        expect(completed, isTrue);
        expect(result?.status, RechartForecastStatus.estimated);
        expect(result?.breakEvenSeconds, 1560);
        await tester.pumpAndSettle();
        expect(game.state.toJson(), before);
        final lines = {
          'estimate': RechartCopy.title,
          'purchases': RechartCopy.purchases,
          'effects': RechartCopy.continuation,
          'objective': RechartCopy.objective,
          'snapshot': RechartCopy.snapshot,
        };
        for (final entry in lines.entries) {
          final text = find.text(Presentation.text(entry.value));
          await tester.ensureVisible(text);
          await tester.pumpAndSettle();
          expect(text.hitTestable(), findsOneWidget);
          expect(tester.takeException(), isNull);
          await capture(tester, boundary, '$width-${entry.key}');
        }
        final keep = find.text(Presentation.text('Keep building'));
        await tester.ensureVisible(keep);
        await tester.pumpAndSettle();
        await capture(tester, boundary, '$width-actions');
        await tester.tap(keep);
        await tester.pumpAndSettle();
        expect(game.state.toJson(), before);
        await tester.ensureVisible(preview);
        await tester.tap(preview);
        await tester.pump();
        final confirm = find.byKey(const ValueKey('confirm-rechart'));
        await tester.ensureVisible(confirm);
        await tester.pumpAndSettle();
        await tester.tap(confirm);
        await tester.pumpAndSettle();
        expect(game.state.charts, BigInt.from(10));
        expect(game.state.counts, [1, 0, 0, 0, 0]);
        expect(game.state.walletMicros, BigInt.zero);
        expect(
          game.state.lifetimeMicros,
          BigInt.parse(before['lifetime_micros'] as String),
        );
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
      },
    );
  }
}
