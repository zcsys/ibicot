import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/audio_bus.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/producer_art.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

/// This is an explicitly seeded native boundary test, not natural pacing or a
/// human playtest. Identical inputs exercise real UI commands/core/disk on both OSes.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  WidgetController.hitTestWarningShouldBeFatal = true;
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
  if (scenario.startsWith('session-')) {
    sessionScenario(binding, label, scenario);
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
      'verification_id': const String.fromEnvironment(
        'TIDEGLASS_VERIFICATION_ID',
      ),
      'candidate_fingerprint': const String.fromEnvironment(
        'TIDEGLASS_CANDIDATE_FINGERPRINT',
      ),
      'harness_sha256': const String.fromEnvironment(
        'TIDEGLASS_HARNESS_SHA256',
      ),
      'scenario': 'seeded',
      'run_id': const String.fromEnvironment('TIDEGLASS_RUN_ID'),
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
    await tester.ensureVisible(find.text('Your lightkeepers'));
    await tester.pumpAndSettle();
    await binding.takeScreenshot('$label-seeded-purchase');
    (binding.reportData!['checks'] as List<String>).add(
      'UI buy costs 33.6 R, retains 26.4 R and creates second Skiff',
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
      'Cancel retains fleet; confirm resets wallet/counts, awards 10 Charts and retains lifetime; disk reload matches exactly',
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
    if (find.text(Copy.returnAcknowledge).evaluate().isNotEmpty) {
      await tester.tap(find.text(Copy.returnAcknowledge));
      await tester.pump(const Duration(milliseconds: 350));
    }
    await tester.ensureVisible(find.text('Your lightkeepers'));
    await tester.pump();
    binding.reportData = {
      'provenance':
          'Fresh native bootstrap with real system clock and actual elapsed wait; isolated test save path; no seeded progress. Reload is a separate native OS process.',
      'verification_id': const String.fromEnvironment(
        'TIDEGLASS_VERIFICATION_ID',
      ),
      'candidate_fingerprint': const String.fromEnvironment(
        'TIDEGLASS_CANDIDATE_FINGERPRINT',
      ),
      'harness_sha256': const String.fromEnvironment(
        'TIDEGLASS_HARNESS_SHA256',
      ),
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

/// Deliberately seeded content/state: this proves native integration, not pace.
void sessionScenario(
  IntegrationTestWidgetsFlutterBinding binding,
  String label,
  String scenario,
) {
  const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
  testWidgets('seeded worker, cosmetics and native audio: $scenario', (
    tester,
  ) async {
    binding.reportData = {
      'verification_id': const String.fromEnvironment(
        'TIDEGLASS_VERIFICATION_ID',
      ),
      'candidate_fingerprint': const String.fromEnvironment(
        'TIDEGLASS_CANDIDATE_FINGERPRINT',
      ),
      'harness_sha256': const String.fromEnvironment(
        'TIDEGLASS_HARNESS_SHA256',
      ),
      'platform': Platform.operatingSystem,
      'device_label': label,
      'scenario': scenario,
      'run_id': runId,
      'process_id': pid,
    };
    final directory = Directory(
      '${(await getApplicationSupportDirectory()).path}/native-verification/session-$label-$runId',
    );
    final checkpoint = File('${directory.path}/session-checkpoint.json');
    final catalogue = await StoryCatalogue.load();
    DateTime? seededAt;
    if (scenario == 'session-start') {
      expect(await directory.exists(), isFalse);
      seededAt = DateTime.now().toUtc().subtract(const Duration(hours: 24));
      final seeded = GameController(
        catalogue: catalogue,
        initialState: GameState.initial().copyWith(
          surveyNotes: BigInt.from(100),
        ),
        initialStory: StoryProgress(
          campaign: CampaignProgress(completed: {'chapter.01'}),
        ),
        clock: () => seededAt!,
        startTicker: false,
      );
      final repository = SaveRepository(
        directory,
        economicVersion: economyVersion,
        economicDigest: bundledEconomyDigest,
        validatePayload: (payload) =>
            validateClientPayload(payload, catalogue: catalogue),
      );
      await repository.load();
      await repository.save({
        'client_schema_version': 2,
        'core': seeded.state.toJson(),
        'story': seeded.story.toJson(),
        'client_preferences': const ClientPreferences(
          reduceMotion: true,
          onboardingDismissed: true,
        ).toJson(),
      }, settledThrough: seededAt);
      seeded.dispose();
    } else {
      expect(await checkpoint.exists(), isTrue);
    }
    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();
    final launchWatch = Stopwatch()..start();
    await tester.pumpWidget(
      TideglassBootstrap(key: ValueKey(scenario), directory: directory),
    );
    for (
      var i = 0;
      i < 300 && find.byType(TideglassApp).evaluate().isEmpty;
      i++
    ) {
      await Future<void>.delayed(const Duration(milliseconds: 100));
      await tester.pump();
    }
    expect(find.byType(TideglassApp), findsOneWidget);
    launchWatch.stop();
    final game = tester
        .widget<TideglassApp>(find.byType(TideglassApp))
        .controller;
    game.suspend();
    final loadedCore = game.state.toJson();
    final loadedCursor = game.settledThrough;
    final checks = <String>[];
    if (scenario == 'session-start') {
      expect(
        game.returnReport!.absence,
        greaterThanOrEqualTo(const Duration(hours: 24)),
      );
      expect(
        game.state.walletMicros,
        greaterThanOrEqualTo(BigInt.from(86400000000)),
      );
      expect(game.state.walletMicros, lessThan(BigInt.from(86430000000)));
      expect(game.state.support.activeSettlementId, isNull);
      expect(game.state.support.caches, isNotEmpty);
      checks.add(
        'Native bootstrap completed seeded 24-hour worker replay and finalized salvage receipt',
      );
    } else {
      final previous =
          jsonDecode(await checkpoint.readAsString()) as Map<String, dynamic>;
      expect(pid, isNot(previous['process_id']));
      expect(game.visibleAppearance, 'cosmetic.core.chapter.01');
      expect(game.story.equippedDecoration, 'cosmetic.core.decoration.01');
      expect(game.state.surveyNotes, BigInt.from(50));
      final saved = GameState.fromJson(
        Map<String, dynamic>.from(previous['core'] as Map),
      );
      expect(game.state.walletMicros, greaterThanOrEqualTo(saved.walletMicros));
      checks.add(
        'Separate native process retained both cosmetic selections, 50 Notes and earned Radiance',
      );
    }
    if (find.text(Copy.returnAcknowledge).evaluate().isNotEmpty) {
      await tester.tap(find.text(Copy.returnAcknowledge));
      await tester.pump(const Duration(milliseconds: 350));
    }
    await tester.pumpAndSettle();
    await game.resumeWithProgress();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Logbook'));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.ensureVisible(find.byKey(const ValueKey('open-cosmetics')));
    await tester.tap(find.byKey(const ValueKey('open-cosmetics')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('cosmetic-filter-2')));
    await tester.pumpAndSettle();
    if (scenario == 'session-start') {
      await tester.ensureVisible(
        find.byKey(const ValueKey('equip-cosmetic.core.chapter.01')),
      );
      await tester.tap(
        find.byKey(const ValueKey('equip-cosmetic.core.chapter.01')),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(
        find.byKey(const ValueKey('acquire-cosmetic.core.decoration.01')),
      );
      await tester.tap(
        find.byKey(const ValueKey('acquire-cosmetic.core.decoration.01')),
      );
      await tester.pumpAndSettle();
      expect(game.state.surveyNotes, BigInt.from(50));
      expect(game.visibleAppearance, 'cosmetic.core.chapter.01');
      expect(game.story.equippedDecoration, 'cosmetic.core.decoration.01');
      checks.add(
        'Collection route equipped earned chapter appearance and spent exactly 50 Notes on coexisting decoration',
      );
    }
    await binding.takeScreenshot('$label-$scenario-collection');
    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Harbor'));
    await tester.pumpAndSettle();
    await binding.takeScreenshot('$label-$scenario-harbor');
    final audio = game.audio!;
    await audio.initialize();
    expect(audio.warning, isNull);
    for (final track in TideMusic.values) {
      await audio.startMusic(track);
      expect(audio.warning, isNull);
    }
    expect(await audio.playCue(TideCue.purchase), isTrue);
    await audio.setForeground(false);
    expect(await audio.playCue(TideCue.claim), isFalse);
    await audio.setForeground(true);
    expect(audio.warning, isNull);
    checks.add(
      'Production native audio driver initialized, switched all three tracks and respected foreground cue gating',
    );
    await game.save();
    expect(game.saveError, isNull);
    await checkpoint.writeAsString(
      jsonEncode({
        'process_id': pid,
        'core': game.state.toJson(),
        'cursor': game.settledThrough.toIso8601String(),
      }),
      flush: true,
    );
    final finalCore = game.state.toJson();
    await tester.pumpWidget(const SizedBox.shrink());
    await audio.close();

    // Decode every bundled AAC through the real OS plugin; keep this probe silent.
    final decoded = <Map<String, Object>>[];
    final probe = AudioPlayer(playerId: 'tideglass.native.codec.probe');
    await probe.setVolume(0);
    for (final name in [
      ...TideMusic.values.map((v) => v.name),
      ...TideCue.values.map((v) => v.name),
    ]) {
      await probe.setSource(AssetSource('audio/$name.m4a'));
      final duration = await probe.getDuration();
      expect(duration, isNotNull);
      expect(duration!.inMilliseconds, greaterThan(0));
      decoded.add({
        'asset': '$name.m4a',
        'duration_ms': duration.inMilliseconds,
      });
      await probe.stop();
    }
    await probe.setSource(AssetSource('audio/harbor.m4a'));
    await probe.setReleaseMode(ReleaseMode.loop);
    await probe.resume();
    await Future<void>.delayed(const Duration(milliseconds: 400));
    final position = await probe.getCurrentPosition();
    expect(probe.state, PlayerState.playing);
    expect(position!.inMilliseconds, greaterThan(0));
    await probe.pause();
    expect(probe.state, PlayerState.paused);
    await probe.dispose();
    checks.add(
      'All eleven AAC assets decoded with positive duration; native music playback clock advanced and paused',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          backgroundColor: const Color(0xFF071E2A),
          body: SafeArea(
            child: Column(
              children: [
                const Text(
                  'Native producer stages · seeded visual fixture',
                  style: TextStyle(color: Colors.white),
                ),
                Expanded(
                  child: GridView.count(
                    crossAxisCount: 5,
                    children: [
                      for (var tier = 0; tier < 5; tier++)
                        for (var stage = 0; stage < 5; stage++)
                          Column(
                            children: [
                              Expanded(
                                child: StagedProducerArt(
                                  tier: tier,
                                  count: stage * 25,
                                  size: 60,
                                ),
                              ),
                              Text(
                                '${tier + 1} / ${stage * 25}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(StagedProducerArt), findsNWidgets(25));
    await binding.takeScreenshot('$label-$scenario-producer-stages');
    expect(tester.takeException(), isNull);
    binding.reportData = {
      ...?binding.reportData,
      'verification_id': const String.fromEnvironment(
        'TIDEGLASS_VERIFICATION_ID',
      ),
      'candidate_fingerprint': const String.fromEnvironment(
        'TIDEGLASS_CANDIDATE_FINGERPRINT',
      ),
      'harness_sha256': const String.fromEnvironment(
        'TIDEGLASS_HARNESS_SHA256',
      ),
      'platform': Platform.operatingSystem,
      'device_label': label,
      'scenario': scenario,
      'run_id': runId,
      'process_id': pid,
      'provenance':
          'Seeded 24-hour absence, earned chapter and Notes. Native worker, UI, storage and audio SDK execute normally. No natural pacing, human audio appraisal or physical-device performance claim.',
      'save_directory': directory.path,
      'checks': checks,
      'launch_single_sample_ms': launchWatch.elapsedMilliseconds,
      'seeded_at': seededAt?.toIso8601String(),
      'loaded_cursor': loadedCursor.toIso8601String(),
      'loaded_core': loadedCore,
      'final_core': finalCore,
      'audio_decoded': decoded,
      'audio_clock_position_ms': position.inMilliseconds,
    };
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
