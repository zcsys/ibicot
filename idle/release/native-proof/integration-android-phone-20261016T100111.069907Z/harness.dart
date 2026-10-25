import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

/// This is an explicitly seeded native boundary test, not natural pacing or a
/// human playtest. Identical inputs exercise real UI commands/core/disk on both OSes.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  const label = String.fromEnvironment(
    'TIDEGLASS_DEVICE_LABEL',
    defaultValue: 'native',
  );
  const scenario = String.fromEnvironment(
    'TIDEGLASS_SCENARIO',
    defaultValue: 'seeded',
  );
  if (scenario.startsWith('natural-')) {
    naturalScenario(binding, label, scenario);
    return;
  }
  const engine = TideglassEngine();
  final epoch = DateTime.utc(2026, 10, 16, 9);

  testWidgets('seeded native purchase, confirmed Rechart and durable reload', (
    tester,
  ) async {
    binding.reportData = {
      'provenance':
          'seeded deterministic fixture; no claim of real elapsed progression, store transaction or human playtest',
      'platform': Platform.operatingSystem,
      'device_label': label,
      'economy_version': economyVersion,
      'checks': <String>[],
    };
    final base = Directory(
      '${(await getApplicationSupportDirectory()).path}/native-verification',
    );
    await base.create(recursive: true);
    final directory = await base.createTemp('$label-');
    final store = SaveRepository(
      directory,
      economicVersion: economyVersion,
      economicDigest: bundledEconomyDigest,
      validatePayload: (payload) => GameState.fromJson(payload),
      now: () => epoch,
    );
    await store.load();
    Future<void> persist(GameState state, DateTime cursor) async {
      await store.save(state.toJson(), settledThrough: cursor);
    }

    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();
    Future<void> show(GameController game, String phase) async {
      await tester.pumpWidget(
        TideglassApp(
          key: ValueKey(phase),
          controller: game,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    final start = engine
        .advance(GameState.initial(), const Duration(seconds: 60))
        .state;
    final game = GameController(
      initialState: start,
      startTicker: false,
      clock: () => epoch,
      onPersist: persist,
    );
    await show(game, 'purchase-fixture');
    await tester.ensureVisible(find.byKey(const ValueKey('buy-0')));
    await tester.tap(find.byKey(const ValueKey('buy-0')));
    await tester.pumpAndSettle();
    expect(game.state.counts, [2, 0, 0, 0, 0]);
    expect(game.state.walletMicros, BigInt.from(26400000));
    expect(game.state.lifetimeMicros, BigInt.from(60000000));
    await game.save();
    await binding.takeScreenshot('$label-seeded-purchase');
    (binding.reportData!['checks'] as List<String>).add(
      'UI buy costs33.6R, retains26.4R and creates second Skiff',
    );
    await tester.pumpWidget(const SizedBox.shrink());
    game.dispose();

    final threshold = GameState(
      counts: [40, 12, 0, 0, 0],
      walletMicros: BigInt.from(1000000000),
      lifetimeMicros: TideglassEngine.firstPrestigeMicros,
    );
    final prestige = GameController(
      initialState: threshold,
      startTicker: false,
      clock: () => epoch,
      onPersist: persist,
    );
    await show(prestige, 'rechart-fixture');
    await tester.tap(find.text('Atlas'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('preview-rechart')));
    await tester.tap(find.byKey(const ValueKey('preview-rechart')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Claim 10 new Charts'), findsOneWidget);
    await binding.takeScreenshot('$label-seeded-rechart-preview');
    await tester.tap(find.text('Keep building'));
    await tester.pumpAndSettle();
    expect(prestige.state.charts, BigInt.zero);
    expect(prestige.state.counts[0], 40);
    await tester.tap(find.byKey(const ValueKey('preview-rechart')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('confirm-rechart')));
    await tester.pumpAndSettle();
    expect(prestige.state.charts, BigInt.from(10));
    expect(prestige.state.counts, [1, 0, 0, 0, 0]);
    expect(prestige.state.walletMicros, BigInt.zero);
    expect(prestige.state.lifetimeMicros, threshold.lifetimeMicros);
    await prestige.save();
    final reopened = SaveRepository(
      directory,
      economicVersion: economyVersion,
      economicDigest: bundledEconomyDigest,
      validatePayload: (payload) => GameState.fromJson(payload),
    );
    final restored = (await reopened.load()).snapshot!;
    expect(
      GameState.fromJson(restored.payload).toJson(),
      prestige.state.toJson(),
    );
    expect(restored.settledThrough, epoch);
    binding.reportData!['save_directory'] = directory.path;
    binding.reportData!['restored_core_state'] = restored.payload;
    (binding.reportData!['checks'] as List<String>).add(
      'Cancel retains fleet; confirm resets wallet/counts, awards10Charts and retains lifetime; disk reload matches exactly',
    );
    await binding.takeScreenshot('$label-seeded-rechart-complete');
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    prestige.dispose();
  });
}

void naturalScenario(
  IntegrationTestWidgetsFlutterBinding binding,
  String label,
  String scenario,
) {
  const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
  testWidgets('real elapsed first purchase and native process reload: $scenario', (
    tester,
  ) async {
    expect(runId, isNotEmpty);
    final directory = Directory(
      '${(await getApplicationSupportDirectory()).path}/native-verification/natural-$label-$runId',
    );
    final checkpoint = File('${directory.path}/native-checkpoint.json');
    final begin = DateTime.now().toUtc();
    if (scenario == 'natural-start') {
      expect(
        await directory.exists(),
        isFalse,
        reason: 'Natural first-run must start without previous progress',
      );
    } else {
      expect(await checkpoint.exists(), isTrue);
    }
    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();
    await tester.pumpWidget(
      TideglassBootstrap(key: ValueKey(scenario), directory: directory),
    );
    for (
      var attempt = 0;
      attempt < 100 && find.byType(TideglassApp).evaluate().isEmpty;
      attempt++
    ) {
      await Future<void>.delayed(const Duration(milliseconds: 100));
      await tester.pump();
    }
    expect(find.byType(TideglassApp), findsOneWidget);
    final game = tester
        .widget<TideglassApp>(find.byType(TideglassApp))
        .controller;
    final before = game.state.toJson();
    if (scenario == 'natural-start') {
      expect(game.state.counts, [1, 0, 0, 0, 0]);
      await Future<void>.delayed(const Duration(seconds: 35));
      await tester.pump();
      expect(
        DateTime.now().toUtc().difference(begin).inSeconds,
        greaterThanOrEqualTo(35),
      );
      expect(
        game.state.walletMicros,
        greaterThanOrEqualTo(BigInt.from(33600000)),
      );
      await tester.ensureVisible(find.byKey(const ValueKey('buy-0')));
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('buy-0')));
      await tester.pump();
      expect(game.state.counts, [2, 0, 0, 0, 0]);
      await game.save();
      expect(game.saveError, isNull);
      await checkpoint.writeAsString(
        jsonEncode({
          'process_id': pid,
          'core': game.state.toJson(),
          'at': DateTime.now().toUtc().toIso8601String(),
        }),
        flush: true,
      );
    } else {
      final previous =
          jsonDecode(await checkpoint.readAsString()) as Map<String, dynamic>;
      expect(
        pid,
        isNot(previous['process_id']),
        reason: 'This must be a new native process',
      );
      final saved = GameState.fromJson(
        Map<String, dynamic>.from(previous['core'] as Map),
      );
      expect(game.state.counts, saved.counts);
      expect(
        game.state.lifetimeMicros,
        greaterThanOrEqualTo(saved.lifetimeMicros),
      );
      expect(game.state.walletMicros, greaterThanOrEqualTo(saved.walletMicros));
      await tester.ensureVisible(find.byKey(const ValueKey('buy-0')));
      await tester.pump();
    }
    binding.reportData = {
      'provenance':
          'Fresh native bootstrap with real system clock and actual elapsed wait; isolated test save path; no seeded progress. Reload is a separate native OS process.',
      'platform': Platform.operatingSystem,
      'device_label': label,
      'scenario': scenario,
      'run_id': runId,
      'process_id': pid,
      'elapsed_milliseconds': DateTime.now()
          .toUtc()
          .difference(begin)
          .inMilliseconds,
      'save_directory': directory.path,
      'before_core': before,
      'after_core': game.state.toJson(),
    };
    await binding.takeScreenshot('$label-$scenario');
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
