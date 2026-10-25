import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/client_economic_transition.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

import '../../core/test/support/synthetic_economy.dart';

// Qualification-only old version. Production v1 registers no predecessor.
const oldEngine = SyntheticOldEconomy();
const predecessor = ClientEconomicPredecessor(
  engine: oldEngine,
  digest: syntheticOldDigest,
);
final epoch = DateTime.utc(2026, 10, 21, 12);

SaveRepository oldStore(Directory dir) => SaveRepository(
  dir,
  economicVersion: syntheticOldVersion,
  economicDigest: syntheticOldDigest,
  validatePayload: (value) => validateClientPayload(
    value,
    expectedEconomicVersion: syntheticOldVersion,
  ),
  validateSnapshot: (value, cursor) => validateClientSnapshot(
    value,
    cursor,
    expectedEconomicVersion: syntheticOldVersion,
  ),
  now: () => epoch,
);

Future<void> seedOld(Directory dir) async {
  final store = oldStore(dir);
  await store.load();
  final state = oldEngine
      .refreshContracts(
        GameState.initial(rulesVersion: syntheticOldVersion),
        epoch,
        accountSeed: 'synthetic-bootstrap-transition',
      )
      .state;
  await store.save({
    'client_schema_version': 1,
    'core': state.toJson(),
    'client_preferences': const ClientPreferences(
      reduceMotion: true,
      onboardingDismissed: true,
    ).toJson(),
  }, settledThrough: epoch);
}

Future<void> finishOpen(WidgetTester tester) async {
  for (var i = 0; i < 300; i++) {
    if (find.byType(TideglassApp).evaluate().isNotEmpty ||
        find
            .text(
              Presentation.text(
                UiEnglish.bootstrapThisHarborNeedsACompatibleGameVersion,
              ),
            )
            .evaluate()
            .isNotEmpty) {
      return;
    }
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump();
  }
  fail(
    'Bootstrap did not finish: ${tester.widgetList<Text>(find.byType(Text)).map((v) => v.data).join(" | ")}',
  );
}

Future<Map<String, String>> generations(Directory dir) async => {
  for (final entry in dir.listSync().whereType<File>())
    if (entry.path.endsWith('.json')) entry.path: await entry.readAsString(),
};

void main() {
  testWidgets(
    'real bootstrap settles old output then persists new rules exactly once',
    (tester) async {
      final dir = Directory.systemTemp.createTempSync(
        'tideglass-client-transition-',
      );
      addTearDown(() => dir.deleteSync(recursive: true));
      await tester.runAsync(() => seedOld(dir));
      var now = epoch.add(const Duration(seconds: 60));
      Future<void> open({bool withPredecessor = true}) async {
        await tester.pumpWidget(
          TideglassBootstrap(
            directory: dir,
            enableAudio: false,
            now: () => now,
            economicPredecessors: withPredecessor
                ? const [predecessor]
                : const [],
          ),
        );
        await finishOpen(tester);
        expect(find.byType(TideglassApp), findsOneWidget);
      }

      await open();
      var app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(app.controller.state.rulesVersion, economyVersion);
      expect(app.controller.state.lifetimeMicros, BigInt.from(90000000));
      expect(app.controller.state.walletMicros, BigInt.from(90000000));
      expect(app.controller.returnReport?.earnedMicros, BigInt.from(90000000));
      expect(app.initialPreferences.reduceMotion, isTrue);
      await tester.runAsync(() => app.controller.save());
      await tester.pumpWidget(const SizedBox());

      // New ordinary rules now earn 1 R/s, not the synthetic old 1.5 R/s.
      now = now.add(const Duration(seconds: 1));
      await open(withPredecessor: false);
      app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(app.controller.state.lifetimeMicros, BigInt.from(91000000));
      expect(app.controller.state.walletMicros, BigInt.from(91000000));
      await tester.runAsync(() => app.controller.save());
      await tester.pumpWidget(const SizedBox());
      await open(withPredecessor: false);
      app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(app.controller.state.lifetimeMicros, BigInt.from(91000000));
      await tester.pumpWidget(const SizedBox());
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('clock rollback adopts at the durable cursor without income', (
    tester,
  ) async {
    final dir = Directory.systemTemp.createTempSync(
      'tideglass-client-transition-rollback-',
    );
    addTearDown(() => dir.deleteSync(recursive: true));
    await tester.runAsync(() => seedOld(dir));
    final original = await tester.runAsync(() => oldStore(dir).load());
    final oldState = GameState.fromJson(
      Map<String, dynamic>.from(original!.snapshot!.payload['core']),
      expectedEconomicVersion: syntheticOldVersion,
    );
    await tester.pumpWidget(
      TideglassBootstrap(
        directory: dir,
        enableAudio: false,
        now: () => epoch.subtract(const Duration(hours: 1)),
        economicPredecessors: const [predecessor],
      ),
    );
    await finishOpen(tester);
    expect(find.byType(TideglassApp), findsOneWidget);
    final app = tester.widget<TideglassApp>(find.byType(TideglassApp));
    expect(app.controller.state.rulesVersion, economyVersion);
    expect(app.controller.state.walletMicros, oldState.walletMicros);
    expect(app.controller.state.lifetimeMicros, oldState.lifetimeMicros);
    expect(app.controller.state.elapsedMicros, oldState.elapsedMicros);
    expect(app.controller.returnReport, isNull);
    await tester.runAsync(() => app.controller.save());
    final envelope = await tester.runAsync(() async {
      final store = SaveRepository(
        dir,
        economicVersion: economyVersion,
        economicDigest: bundledEconomyDigest,
        validatePayload: validateClientPayload,
        validateSnapshot: validateClientSnapshot,
      );
      return (await store.load()).snapshot!;
    });
    expect(envelope!.settledThrough, epoch);
    await tester.pumpWidget(const SizedBox());
    expect(tester.takeException(), isNull);
  });

  for (final registerWrongDigest in [false, true]) {
    testWidgets(
      'bootstrap rejects ${registerWrongDigest ? "wrong digest" : "unregistered rules"} without rewriting generations',
      (tester) async {
        final dir = Directory.systemTemp.createTempSync(
          'tideglass-client-transition-reject-',
        );
        addTearDown(() => dir.deleteSync(recursive: true));
        await tester.runAsync(() => seedOld(dir));
        final before = await tester.runAsync(() => generations(dir));
        await tester.pumpWidget(
          TideglassBootstrap(
            directory: dir,
            enableAudio: false,
            now: () => epoch.add(const Duration(seconds: 60)),
            economicPredecessors: [
              if (registerWrongDigest)
                ClientEconomicPredecessor(engine: oldEngine, digest: 'a' * 64),
            ],
          ),
        );
        await finishOpen(tester);
        expect(find.byType(TideglassApp), findsNothing);
        expect(
          find.text(
            Presentation.text(
              UiEnglish.bootstrapThisHarborNeedsACompatibleGameVersion,
            ),
          ),
          findsOneWidget,
        );
        final after = await tester.runAsync(() => generations(dir));
        // Notification preferences are not a game generation; inspect the two
        // actual atomic snapshot files rather than unrelated local settings.
        final oldGenerations = before!.entries.where(
          (e) => e.key.contains('/progress.'),
        );
        for (final entry in oldGenerations) {
          expect(after![entry.key], entry.value);
          final envelope = (jsonDecode(entry.value) as Map)['envelope'] as Map;
          expect(
            (envelope['economic_config'] as Map)['version'],
            syntheticOldVersion,
          );
        }
        await tester.pumpWidget(const SizedBox());
        expect(tester.takeException(), isNull);
      },
    );
  }
}
