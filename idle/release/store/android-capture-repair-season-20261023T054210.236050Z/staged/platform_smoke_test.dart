import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/ownership_clock.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/soundtrack_export.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

/// Capture-only binding: retain hit-tested gestures without the live test
/// binding's painted pointer crosshair. These are still automated inputs,
/// not physical-device or human interaction evidence.
class CaptureGalleryBinding extends IntegrationTestWidgetsFlutterBinding {
  CaptureGalleryBinding() {
    shouldPropagateDevicePointerEvents = true;
  }

  int routedTestPointerEvents = 0;

  @override
  void handlePointerEventForSource(
    PointerEvent event, {
    TestBindingEventSource source = TestBindingEventSource.device,
  }) {
    if (source == TestBindingEventSource.test) routedTestPointerEvents += 1;
    // The propagated device branch forwards this same event through normal
    // framework hit testing and gesture dispatch, without recording a painted
    // test pointer. Do not invoke UI callbacks or alter event coordinates.
    super.handlePointerEventForSource(
      event,
      source: TestBindingEventSource.device,
    );
  }
}

/// This is an explicitly seeded native boundary test, not natural pacing or a
/// human playtest. Identical inputs exercise real UI commands/core/disk on both OSes.
void main() {
  const scenario = String.fromEnvironment(
    'TIDEGLASS_SCENARIO',
    defaultValue: 'seeded',
  );
  final binding = scenario == 'capture-gallery'
      ? CaptureGalleryBinding()
      : IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  WidgetController.hitTestWarningShouldBeFatal = true;
  const label = String.fromEnvironment(
    'TIDEGLASS_DEVICE_LABEL',
    defaultValue: 'native',
  );
  if (scenario.startsWith('clock-')) {
    clockScenario(binding, label, scenario);
    return;
  }
  if (scenario == 'share-cancel') {
    shareCancellationScenario(binding, label);
    return;
  }
  if (scenario == 'capture-gallery') {
    captureGalleryScenario(binding, label);
    return;
  }
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

Map<String, dynamic> nativeIdentity(String label, String scenario) => {
  'verification_id': const String.fromEnvironment('TIDEGLASS_VERIFICATION_ID'),
  'candidate_fingerprint': const String.fromEnvironment(
    'TIDEGLASS_CANDIDATE_FINGERPRINT',
  ),
  'harness_sha256': const String.fromEnvironment('TIDEGLASS_HARNESS_SHA256'),
  'platform': Platform.operatingSystem,
  'os_version': Platform.operatingSystemVersion,
  'device_label': label,
  'scenario': scenario,
  'run_id': const String.fromEnvironment('TIDEGLASS_RUN_ID'),
  'process_id': pid,
};

class NativeLifecycleProbe extends WidgetsBindingObserver {
  final states = <AppLifecycleState>[];
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) => states.add(state);
}

Future<void> waitForNativeCondition(
  WidgetTester tester,
  bool Function() condition, {
  required String reason,
  Duration timeout = const Duration(seconds: 90),
}) async {
  final watch = Stopwatch()..start();
  while (!condition() && watch.elapsed < timeout) {
    await Future<void>.delayed(const Duration(milliseconds: 200));
    await tester.pump();
  }
  expect(condition(), isTrue, reason: reason);
}

/// Clock epochs stay only in a private fixture checkpoint, never in exported
/// reports. The report contains scope, equality results and elapsed deltas.
void clockScenario(
  IntegrationTestWidgetsFlutterBinding binding,
  String label,
  String scenario,
) {
  const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
  const channel = MethodChannel('dev.tideglass/ownership_clock');
  testWidgets('actual native ownership clock: $scenario', (tester) async {
    binding.reportData = {
      ...nativeIdentity(label, scenario),
      'provenance':
          'Real native MethodChannel and OS process/lifecycle controls. No signed ownership, paid transaction, device security or reboot qualification.',
    };
    expect(runId, isNotEmpty);
    final directory = Directory(
      '${(await getApplicationSupportDirectory()).path}/native-verification/clock-$label-$runId',
    );
    final checkpoint = File('${directory.path}/clock-checkpoint.json');
    if (scenario == 'clock-start') {
      expect(await directory.exists(), isFalse);
      await directory.create(recursive: true);
    } else {
      expect(await checkpoint.exists(), isTrue);
    }
    final lifecycle = NativeLifecycleProbe();
    binding.addObserver(lifecycle);
    final bridge = OwnershipClockBridge(autoRefresh: false);
    addTearDown(() {
      bridge.dispose();
      binding.removeObserver(lifecycle);
    });
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('Native clock verification — local fixture'),
          ),
        ),
      ),
    );
    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();
    // integration_test requires a rendered frame after Android surface
    // conversion. This static fixture has no animation to supply that frame.
    await pumpNativeUi(tester);
    debugPrint('TIDEGLASS_NATIVE_CLOCK_SURFACE_READY');
    Future<Map<String, dynamic>> sample() async {
      final raw = await channel.invokeMapMethod<String, dynamic>('sample');
      expect(raw, isNotNull);
      expect(raw!['version'], 1);
      expect(raw['elapsed_us'], isA<int>());
      expect((raw['elapsed_us'] as int) >= 0, isTrue);
      expect(raw['epoch_id'], isA<String>());
      expect(raw['continuity_scope'], Platform.isAndroid ? 'boot' : 'process');
      return raw;
    }

    final first = await sample();
    await Future<void>.delayed(const Duration(milliseconds: 500));
    final second = await sample();
    expect(second['epoch_id'] == first['epoch_id'], isTrue);
    final delta = (second['elapsed_us'] as int) - (first['elapsed_us'] as int);
    expect(delta, greaterThanOrEqualTo(400000));
    expect(await bridge.refresh(), isTrue);
    expect(bridge.current, isNotNull);
    expect(bridge.current!.bootId == second['epoch_id'], isTrue);
    expect(bridge.restartContinuity, Platform.isAndroid);
    final uncertainty = bridge.current!.uncertaintyMicroseconds;
    expect(uncertainty, greaterThan(0));
    binding.reportData!.addAll({
      'continuity_scope': second['continuity_scope'],
      'same_process_epoch_stable': true,
      'native_sample_delta_us': delta,
      'bridge_uncertainty_us': uncertainty,
      'bridge_restart_continuity': bridge.restartContinuity,
    });

    if (scenario == 'clock-start') {
      var invalidations = 0;
      void observed() {
        if (bridge.current == null) invalidations++;
      }

      bridge.addListener(observed);
      final lifecycleStart = lifecycle.states.length;
      final priorInvalidations = invalidations;
      // The external runner must now send the actual app to Home and reopen it.
      // Never substitute a manually injected Flutter lifecycle notification.
      debugPrint('TIDEGLASS_NATIVE_CLOCK_BACKGROUND_READY');
      await waitForNativeCondition(tester, () {
        final observedStates = lifecycle.states.skip(lifecycleStart);
        return invalidations > priorInvalidations &&
            observedStates.contains(AppLifecycleState.paused) &&
            observedStates.contains(AppLifecycleState.resumed);
      }, reason: 'Actual OS background and foreground callbacks must arrive');
      expect(bridge.current, isNull);
      expect(await bridge.refresh(), isTrue);
      expect(bridge.current!.bootId == second['epoch_id'], isTrue);
      expect(
        bridge.current!.elapsedMicroseconds > (second['elapsed_us'] as int),
        isTrue,
      );
      bridge.removeListener(observed);
      binding.reportData!.addAll({
        'native_lifecycle_states': lifecycle.states
            .skip(lifecycleStart)
            .map((value) => value.name)
            .toList(),
        'evidence_hidden_before_foreground_refresh': true,
        'same_process_epoch_after_foreground': true,
      });
      final last = await sample();
      await checkpoint.writeAsString(
        jsonEncode({'process_id': pid, ...last}),
        flush: true,
      );
    } else {
      final previous = jsonDecode(await checkpoint.readAsString()) as Map;
      expect(pid, isNot(previous['process_id']));
      final epochSame = previous['epoch_id'] == second['epoch_id'];
      expect(epochSame, Platform.isAndroid);
      expect(
        (second['elapsed_us'] as int) > (previous['elapsed_us'] as int),
        isTrue,
      );
      binding.reportData!.addAll({
        'different_native_process': true,
        'epoch_equal_after_process_restart': epochSame,
        'restart_elapsed_delta_us':
            (second['elapsed_us'] as int) - (previous['elapsed_us'] as int),
        'restart_scope_assertion': Platform.isAndroid
            ? 'Same installation and OS boot retains opaque epoch across process restart'
            : 'Apple process restart changes epoch and cannot resume an offline ownership lease',
      });
    }
    debugPrint('TIDEGLASS_NATIVE_CLOCK_ASSERTIONS_DONE');
    await pumpNativeUi(tester);
    await binding
        .takeScreenshot('$label-$scenario')
        .timeout(const Duration(seconds: 15));
    expect(tester.takeException(), isNull);
    bridge.dispose();
    binding.removeObserver(lifecycle);
    await tester.pumpWidget(const SizedBox.shrink());
  }, timeout: const Timeout(Duration(minutes: 3)));
}

/// Test-only download substitution. The real native export function and share
/// plugin run normally; service authentication/ownership are deliberately absent.
class SyntheticArchiveServices extends NativeServicesManager {
  SyntheticArchiveServices(this.archive);
  final File archive;
  int downloads = 0;
  @override
  Future<File> downloadSoundtrack(Directory destination) async {
    downloads++;
    return archive;
  }
}

void shareCancellationScenario(
  IntegrationTestWidgetsFlutterBinding binding,
  String label,
) {
  const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
  testWidgets('native share sheet cancellation with synthetic archive', (
    tester,
  ) async {
    binding.reportData = {
      ...nativeIdentity(label, 'share-cancel'),
      'provenance':
          'Synthetic local ZIP, overridden test-only download, real production export function and native share sheet. No purchase, entitlement, network download or receiving-app delivery claim.',
    };
    expect(runId, isNotEmpty);
    final directory = Directory(
      '${(await getTemporaryDirectory()).path}/native-verification/share-$label-$runId',
    );
    expect(await directory.exists(), isFalse);
    await directory.create(recursive: true);
    final archive = File(
      '${directory.path}/tideglass-native-share-fixture.zip',
    );
    // Deterministic valid ZIP containing only a README stating this is a fixture.
    final bytes = base64Decode(
      'UEsDBBQAAAAIAAAAIVzVZQqIUwAAAGEAAAAKAAAAUkVBRE1FLnR4dA2M0QmAMAwF/zvFm8AFHEMXCPWhhZiUNord3n4dB8ft5eCp0jtMorwEv+otEOwBNx1L2obFxSgZ6lkU0vI1yxXmqM8U6YQ30KKE8p4E3/m1zCX9UEsBAhQDFAAAAAgAAAAhXNVlCohTAAAAYQAAAAoAAAAAAAAAAAAAAIABAAAAAFJFQURNRS50eHRQSwUGAAAAAAEAAQA4AAAAewAAAAAA',
    );
    await archive.writeAsBytes(bytes, flush: true);
    final manager = SyntheticArchiveServices(archive);
    addTearDown(manager.dispose);
    final completed = Completer<SoundtrackExportResult>();
    final buttonKey = GlobalKey();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: FilledButton(
              key: buttonKey,
              onPressed: () {
                final box =
                    buttonKey.currentContext!.findRenderObject() as RenderBox;
                final anchor = box.localToGlobal(Offset.zero) & box.size;
                debugPrint('TIDEGLASS_NATIVE_SHARE_READY');
                unawaited(
                  exportSoundtrack(
                    manager,
                    anchor,
                  ).then(completed.complete, onError: completed.completeError),
                );
              },
              child: const Text('Open native share sheet — synthetic ZIP'),
            ),
          ),
        ),
      ),
    );
    if (Platform.isAndroid) await binding.convertFlutterSurfaceToImage();
    await tester.tap(find.byKey(buttonKey));
    final result = await completed.future.timeout(const Duration(seconds: 120));
    expect(result, SoundtrackExportResult.cancelled);
    expect(manager.downloads, 1);
    expect(manager.session, isNull);
    expect(await archive.readAsBytes(), bytes);
    binding.reportData!.addAll({
      'native_export_result': result.name,
      'synthetic_archive_sha256': sha256.convert(bytes).toString(),
      'synthetic_archive_bytes': bytes.length,
      'download_substitution_calls': manager.downloads,
      'account_session_present': false,
      'archive_retained_after_cancel': true,
    });
    await tester.pump();
    await binding.takeScreenshot('$label-share-cancel-returned');
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  }, timeout: const Timeout(Duration(minutes: 3)));
}

/// Capture readiness requires the actual visible route, not just a fixed pump.
/// A returning route's secondary animation must finish before a new real tap.
bool captureRouteIsReady(WidgetTester tester, Finder landmark) {
  final elements = landmark.evaluate().toList();
  if (elements.length != 1) return false;
  final route = ModalRoute.of(elements.single);
  return route != null &&
      route.isCurrent &&
      route.animation?.status == AnimationStatus.completed &&
      route.secondaryAnimation?.status == AnimationStatus.dismissed &&
      landmark.hitTestable().evaluate().length == 1;
}

/// Store-material draft capture uses valid, explicitly seeded progression. The
/// UI is the production app and actual routes; no screenshot composition or
/// invented premium ownership is involved. Time during the clip is real time.
void captureGalleryScenario(
  IntegrationTestWidgetsFlutterBinding binding,
  String label,
) {
  const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
  testWidgets('seeded native screen set and real-time gameplay footage', (
    tester,
  ) async {
    expect(binding, isA<CaptureGalleryBinding>());
    final captureBinding = binding as CaptureGalleryBinding;
    expect(captureBinding.shouldPropagateDevicePointerEvents, isTrue);
    binding.reportData = {
      ...nativeIdentity(label, 'capture-gallery'),
      'provenance':
          'Seeded chapters, fleet, currencies, earned appearance and passage. Production UI and real timer/actions during the clip. No natural retention, paid ownership, human playtest or published store-material claim.',
      'audio_recorded': false,
      'pointer_dispatch':
          'Automated hit-tested UI gestures through device propagation; no painted test pointer, physical input or human-playtest claim.',
    };
    expect(runId, isNotEmpty);
    final directory = Directory(
      '${(await getApplicationSupportDirectory()).path}/native-verification/capture-$label-$runId',
    );
    expect(await directory.exists(), isFalse);
    await directory.create(recursive: true);
    final startSignal = File('${directory.path}/recording-started');
    final stopSignal = File('${directory.path}/recording-stopped.json');
    final watch = Stopwatch();
    final androidScreencaps = <Map<String, dynamic>>[];
    if (Platform.isAndroid) {
      binding.reportData!['android_screencaps'] = androidScreencaps;
    }
    final captureIdentity = {
      for (final key in [
        'verification_id', 'candidate_fingerprint', 'harness_sha256',
        'device_label', 'run_id', 'platform', 'scenario',
      ]) key: binding.reportData![key],
      'directory': directory.path,
    };
    Future<void> screenshot(String screen) async {
      if (!Platform.isAndroid) {
        await binding.takeScreenshot('$label-capture-$screen');
        return;
      }
      // The integration_test Android image-view conversion retains a frozen
      // display between screenshot acquisitions. Capture the real OS surface
      // externally; do not convert/revert it or invoke UI callbacks directly.
      final sequence = androidScreencaps.length + 1;
      final request = {
        ...captureIdentity,
        'sequence': sequence,
        'file': '$label-capture-$screen.png',
        'width': tester.view.physicalSize.width.toInt(),
        'height': tester.view.physicalSize.height.toInt(),
        'gameplay_elapsed_ms': watch.elapsedMilliseconds,
      };
      final ack = File('${directory.path}/screenshot-$sequence-ready.json');
      expect(await ack.exists(), isFalse);
      await tester.pump();
      debugPrint('TIDEGLASS_NATIVE_SCREENSHOT_READY ${jsonEncode(request)}');
      await waitForNativeCondition(
        tester, ack.existsSync,
        reason: 'The exact Android raw screenshot must be captured and acknowledged',
        timeout: const Duration(seconds: 10),
      );
      final receipt = Map<String, dynamic>.from(
        jsonDecode(await ack.readAsString()) as Map,
      );
      for (final entry in request.entries) {
        expect(receipt[entry.key], entry.value);
      }
      expect(receipt['capture_method'], 'adb exec-out screencap -p');
      expect(receipt['sha256'], matches(RegExp(r'^[a-f0-9]{64}$')));
      expect(receipt['bytes'], greaterThan(0));
      androidScreencaps.add(receipt);
    }
    final catalogue = await StoryCatalogue.load();
    final challenge = ChallengeEconomy(catalogue.dossiers.first);
    final run = challenge.newRun();
    final subject = GameController(
      catalogue: catalogue,
      initialState: GameState(
        counts: [60, 30, 10, 2, 0],
        walletMicros: BigInt.from(10000000000000),
        lifetimeMicros: BigInt.from(10000000000000000),
        charts: BigInt.from(25),
        surveyNotes: BigInt.from(200),
      ),
      initialStory: StoryProgress(
        campaign: CampaignProgress(
          completed: {'chapter.01', 'chapter.02', 'chapter.03'},
        ),
        dossiers: DossierCollection(
          owned: {run.dossierId},
          active: run.copyWith(
            fleet: challenge
                .advance(run.fleet, const Duration(seconds: 90))
                .state,
          ),
        ),
        decorations: {'cosmetic.core.decoration.01'},
        equippedDecoration: 'cosmetic.core.decoration.01',
        equippedAppearance: 'cosmetic.core.chapter.03',
      ),
    );
    var disposed = false;
    void disposeSubject() {
      if (!disposed) {
        disposed = true;
        subject.dispose();
      }
    }

    addTearDown(disposeSubject);
    await tester.pumpWidget(
      TideglassApp(
        controller: subject,
        initialPreferences: const ClientPreferences(onboardingDismissed: true),
      ),
    );
    await pumpNativeUi(tester);
    binding.reportData!.addAll({
      'seeded_core': subject.state.toJson(),
      'seeded_story': subject.story.toJson(),
      'device_physical_width': tester.view.physicalSize.width,
      'device_physical_height': tester.view.physicalSize.height,
      'device_pixel_ratio': tester.view.devicePixelRatio,
      'platform_locale': Platform.localeName,
    });
    await screenshot('main');
    debugPrint(
      'TIDEGLASS_NATIVE_CAPTURE_READY ${jsonEncode(Platform.isAndroid ? captureIdentity : {'directory': directory.path})}',
    );
    await waitForNativeCondition(
      tester,
      startSignal.existsSync,
      reason: 'The native recorder must acknowledge it started before gameplay',
      timeout: const Duration(seconds: 45),
    );
    watch.start();
    Future<void> until(Duration elapsed) async {
      while (watch.elapsed < elapsed) {
        await Future<void>.delayed(const Duration(milliseconds: 250));
        await tester.pump();
      }
    }

    Future<void> tap(Finder target) async {
      await tester.ensureVisible(target);
      await pumpNativeUi(tester);
      await tester.tap(target);
      await pumpNativeUi(tester);
    }

    await until(const Duration(seconds: 4));
    final beforeCount = subject.state.counts.first;
    await tap(find.byKey(const ValueKey('buy-0')));
    expect(subject.state.counts.first, beforeCount + 1);
    await until(const Duration(seconds: 8));
    await tap(find.text('Logbook'));
    await tap(find.byKey(const ValueKey('open-story')));
    await tester.ensureVisible(
      find.byKey(const PageStorageKey('chapter-chapter.04')),
    );
    await pumpNativeUi(tester);
    await screenshot('chapter');
    await until(const Duration(seconds: 14));
    await tap(find.byKey(const ValueKey('story-tab-1')));
    await tester.ensureVisible(find.byKey(const ValueKey('active-challenge')));
    await pumpNativeUi(tester);
    await screenshot('challenge');
    await until(const Duration(seconds: 20));
    await tester.pageBack();
    await pumpNativeUi(tester);
    final openSeason = find.byKey(const ValueKey('open-season'));
    await waitForNativeCondition(
      tester,
      () => openSeason.evaluate().length == 1,
      reason: 'The returned Logbook must expose its actual seasonal route control',
      timeout: const Duration(seconds: 4),
    );
    await tester.ensureVisible(openSeason);
    await waitForNativeCondition(
      tester,
      () => captureRouteIsReady(tester, openSeason),
      reason: 'The returning Logbook route must settle before the seasonal tap',
      timeout: const Duration(seconds: 4),
    );
    await tap(openSeason);
    final seasonScreen = find.byType(SeasonScreen);
    final seasonFleet = find.descendant(
      of: seasonScreen,
      matching: find.byKey(const ValueKey('season-tab-0')),
    );
    await waitForNativeCondition(
      tester,
      () => captureRouteIsReady(tester, seasonFleet),
      reason: 'The actual Season route and visible Fleet landmark must settle before capture',
      timeout: const Duration(seconds: 4),
    );
    expect(seasonScreen, findsOneWidget);
    expect(seasonFleet.hitTestable(), findsOneWidget);
    expect(tester.widget<ChoiceChip>(seasonFleet).selected, isTrue);
    final seasonRoute = ModalRoute.of(tester.element(seasonFleet))!;
    binding.reportData!['season_capture_landmark'] = {
      'widget': 'SeasonScreen',
      'key': 'season-tab-0',
      'selected': true,
      'route_is_current': seasonRoute.isCurrent,
      'primary_animation_status': seasonRoute.animation!.status.name,
      'secondary_animation_status': seasonRoute.secondaryAnimation!.status.name,
      'gameplay_elapsed_ms': watch.elapsedMilliseconds,
    };
    await screenshot('season');
    await until(const Duration(seconds: 25));
    expect(captureBinding.routedTestPointerEvents, greaterThan(0));
    final gameplayElapsedMs = watch.elapsedMilliseconds;
    if (Platform.isAndroid) {
      final request = {
        ...captureIdentity, 'gameplay_elapsed_ms': gameplayElapsedMs,
      };
      debugPrint('TIDEGLASS_NATIVE_CAPTURE_DONE ${jsonEncode(request)}');
      // Keep the final production screen present until the owned OS recorder
      // has stopped. This does not change the gameplay timeline or its speed.
      await waitForNativeCondition(
        tester, stopSignal.existsSync,
        reason: 'The exact Android recorder must stop before removing its UI',
        timeout: const Duration(seconds: 15),
      );
      final receipt = Map<String, dynamic>.from(
        jsonDecode(await stopSignal.readAsString()) as Map,
      );
      for (final entry in request.entries) {
        expect(receipt[entry.key], entry.value);
      }
      expect(receipt['recorder_stopped'], isTrue);
      binding.reportData!['android_screencaps'] = androidScreencaps;
      binding.reportData!['android_recording_stop'] = receipt;
    } else {
      debugPrint('TIDEGLASS_NATIVE_CAPTURE_DONE');
    }
    binding.reportData!.addAll({
      'real_gameplay_elapsed_ms': gameplayElapsedMs,
      'actual_purchase_count_delta': subject.state.counts.first - beforeCount,
      'automated_pointer_events_routed': captureBinding.routedTestPointerEvents,
      'screen_set': ['main', 'chapter', 'challenge', 'season'],
    });
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    disposeSubject();
  }, timeout: const Timeout(Duration(minutes: 3)));
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
    await Future<void>.delayed(const Duration(milliseconds: 400));
    await tester.pump();
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
    final audio = game.audio;
    await audio?.close();
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
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
    await pumpNativeUi(tester);
    if (find.text(Copy.returnAcknowledge).evaluate().isNotEmpty) {
      await tester.tap(find.text(Copy.returnAcknowledge));
      await tester.pump(const Duration(milliseconds: 350));
    }
    await pumpNativeUi(tester);
    await game.resumeWithProgress();
    await pumpNativeUi(tester);
    expect(game.returnReport, isNull);
    await tester.tap(find.text('Logbook'));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.ensureVisible(find.byKey(const ValueKey('open-cosmetics')));
    await tester.tap(find.byKey(const ValueKey('open-cosmetics')));
    await pumpNativeUi(tester);
    await tester.tap(find.byKey(const ValueKey('cosmetic-filter-2')));
    await pumpNativeUi(tester);
    if (scenario == 'session-start') {
      await tester.ensureVisible(
        find.byKey(const ValueKey('equip-cosmetic.core.chapter.01')),
      );
      await tester.tap(
        find.byKey(const ValueKey('equip-cosmetic.core.chapter.01')),
      );
      await pumpNativeUi(tester);
      await tester.ensureVisible(
        find.byKey(const ValueKey('acquire-cosmetic.core.decoration.01')),
      );
      await tester.tap(
        find.byKey(const ValueKey('acquire-cosmetic.core.decoration.01')),
      );
      await pumpNativeUi(tester);
      expect(game.state.surveyNotes, BigInt.from(50));
      expect(game.visibleAppearance, 'cosmetic.core.chapter.01');
      expect(game.story.equippedDecoration, 'cosmetic.core.decoration.01');
      checks.add(
        'Collection route equipped earned chapter appearance and spent exactly 50 Notes on coexisting decoration',
      );
    }
    await tester.ensureVisible(
      find.byKey(const ValueKey('collection-cosmetic.core.decoration.01')),
    );
    await pumpNativeUi(tester);
    await binding.takeScreenshot('$label-$scenario-collection');
    await tester.pageBack();
    await pumpNativeUi(tester);
    await tester.tap(find.text('Harbor'));
    await pumpNativeUi(tester);
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
    await audio.close();
    await tester.pumpWidget(const SizedBox.shrink());

    // Decode every bundled AAC through the real OS plugin; keep this probe silent.
    final decoded = <Map<String, Object>>[];
    final probe = AudioPlayer(playerId: 'tideglass.native.codec.probe');
    var probeDisposed = false;
    Future<void> closeProbe() async {
      if (probeDisposed) return;
      probeDisposed = true;
      await probe.dispose();
    }

    addTearDown(closeProbe);
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
    // Native playback can start after resume's platform-channel acknowledgement.
    // Assert its actual clock advances, without assuming a fixed 400ms startup.
    final playbackWait = Stopwatch()..start();
    final positions = <int?>[];
    Duration? position;
    do {
      await Future<void>.delayed(const Duration(milliseconds: 100));
      position = await probe.getCurrentPosition();
      positions.add(position?.inMilliseconds);
    } while ((position == null || position.inMilliseconds == 0) &&
        playbackWait.elapsed < const Duration(seconds: 5));
    binding.reportData!['audio_probe'] = {
      'decoded': decoded,
      'playback_wait_ms': playbackWait.elapsedMilliseconds,
      'position_samples_ms': positions,
      'state': probe.state.name,
    };
    expect(probe.state, PlayerState.playing);
    expect(position, isNotNull);
    expect(position!.inMilliseconds, greaterThan(0));
    await probe.pause();
    expect(probe.state, PlayerState.paused);
    await closeProbe();
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
    await pumpNativeUi(tester);
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

// A playing native AudioPlayer schedules position frames continuously. Wait for
// bounded rendered transitions instead of waiting for the whole engine to idle.
Future<void> pumpNativeUi(WidgetTester tester) async {
  await tester.pump();
  await Future<void>.delayed(const Duration(milliseconds: 250));
  await tester.pump(const Duration(milliseconds: 250));
}
