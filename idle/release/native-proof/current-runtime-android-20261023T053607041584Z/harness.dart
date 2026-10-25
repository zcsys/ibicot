// Native qualification only. All predecessor, enrollment and cache fixtures are
// synthetic. Never point this harness at the ordinary Tideglass save directory.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/client_economic_transition.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass/study_gate.dart';
import 'package:tideglass/study_native_context.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';
import 'package:tideglass_platform/soundtrack_cache.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';
import 'package:tideglass_platform/study_recorder.dart';

const scenario = String.fromEnvironment('TIDEGLASS_SCENARIO');
const label = String.fromEnvironment('TIDEGLASS_DEVICE_LABEL');
const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
const candidate = String.fromEnvironment('TIDEGLASS_CANDIDATE_FINGERPRINT');
const harness = String.fromEnvironment('TIDEGLASS_HARNESS_SHA256');
const verification = String.fromEnvironment('TIDEGLASS_VERIFICATION_ID');
const privacyObservation = bool.fromEnvironment(
  'TIDEGLASS_PRIVACY_OBSERVATION',
);
const allowedScenarios = <String>{
  'runtime-lock-exclusion',
  'runtime-save-hold-beforeWrite',
  'runtime-save-recover-beforeWrite',
  'runtime-save-hold-afterFlush',
  'runtime-save-recover-afterFlush',
  'runtime-save-hold-afterRename',
  'runtime-save-recover-afterRename',
  'runtime-transition-start',
  'runtime-transition-reopen',
  'runtime-study-default',
  'runtime-study-enroll',
  'runtime-study-restart',
  'runtime-study-crash-hold',
  'runtime-study-crash-reopen',
  'runtime-study-capacity',
  'runtime-study-storage-withdraw',
  'runtime-study-withdraw-reopen',
  'runtime-cache-grace',
};
final epoch = DateTime.utc(2026, 10, 21, 12);
late IntegrationTestWidgetsFlutterBinding binding;
bool androidSurfaceConverted = false;
final fixtureNotifications = <NotificationService>[];
Map<String, dynamic> get report => binding.reportData!;
String hashFile(File file) => sha256.convert(file.readAsBytesSync()).toString();
Map<String, dynamic> readObject(File file) =>
    Map<String, dynamic>.from(jsonDecode(file.readAsStringSync()) as Map);

void main() {
  binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  WidgetController.hitTestWarningShouldBeFatal = true;
  testWidgets('current native runtime qualification: $scenario', (
    tester,
  ) async {
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      for (final service in fixtureNotifications) {
        service.dispose();
      }
    });
    expect(allowedScenarios, contains(scenario));
    if (privacyObservation) {
      expect({
        'runtime-study-default',
        'runtime-study-enroll',
      }, contains(scenario));
    }
    expect(const String.fromEnvironment('TIDEGLASS_SERVICE_URL'), isEmpty);
    expect(const bool.fromEnvironment('TIDEGLASS_COMMERCE'), isFalse);
    expect(const bool.fromEnvironment('TIDEGLASS_REWARDED_ADS'), isFalse);
    expect(const bool.fromEnvironment('TIDEGLASS_SUPPORTER'), isFalse);
    expect(Platform.isIOS || Platform.isAndroid || Platform.isMacOS, isTrue);
    for (final value in [label, runId, verification]) {
      expect(RegExp(r'^[A-Za-z0-9_-]+$').hasMatch(value), isTrue);
    }
    for (final value in [candidate, harness]) {
      expect(RegExp(r'^[a-f0-9]{64}$').hasMatch(value), isTrue);
    }
    binding.reportData = {
      'verification_id': verification,
      'candidate_fingerprint': candidate,
      'harness_sha256': harness,
      'scenario': scenario,
      'run_id': runId,
      'device_label': label,
      'platform': Platform.operatingSystem,
      'os_version': Platform.operatingSystemVersion,
      'process_id': pid,
      'fixture_kind': 'INTERNAL SYNTHETIC QUALIFICATION ONLY',
      'checks': <String>[],
      'completed': false,
      'limitations': <String>[
        'No real participant, consent, paid transaction or receiving-app delivery.',
        'Process termination is not physical power loss or a lifecycle callback.',
        'Injected predecessor/rate/clock/bounds are qualification fixtures only.',
        'Consented production process observations do not prove release AOT fatal-report matching or a crash-free rate.',
      ],
    };
    if (scenario.startsWith('runtime-transition-') ||
        (scenario.startsWith('runtime-study-') &&
            scenario != 'runtime-study-default')) {
      await guardEmptySharedCache();
    }
    if (scenario == 'runtime-lock-exclusion') {
      await lockExclusion();
    } else if (scenario.startsWith('runtime-save-')) {
      await saveInterruption();
    } else if (scenario.startsWith('runtime-transition-')) {
      await transition(tester);
    } else if (scenario.startsWith('runtime-study-')) {
      await study(tester);
    } else if (scenario == 'runtime-cache-grace') {
      await cacheGrace();
    }
    if (privacyObservation) await privacyWindow(tester);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    report['completed'] = true;
  });
}

Future<void> privacyWindow(WidgetTester tester) async {
  // Observational test instrumentation only. This does not open a socket or
  // record a participant; the separate host collector is read-only.
  final stopwatch = Stopwatch()..start();
  final common = <String, dynamic>{
    for (final key in [
      'verification_id',
      'candidate_fingerprint',
      'harness_sha256',
      'scenario',
      'run_id',
      'device_label',
      'platform',
      'process_id',
      'fixture_directory',
    ])
      key: report[key],
    'mode': scenario == 'runtime-study-default'
        ? 'default-unprovisioned'
        : 'synthetic-consented',
    'window_id': '$verification-privacy',
    'maximum_ms': 20000,
  };
  Map<String, dynamic> checkpoint() => {
    ...common,
    'native_elapsed_us': stopwatch.elapsedMicroseconds,
    'native_utc_ms': DateTime.now().toUtc().millisecondsSinceEpoch,
  };
  final opened = checkpoint();
  // ignore: avoid_print -- atomic host checkpoint must not be debugPrint-wrapped.
  print('TIDEGLASS_PRIVACY_WINDOW_OPEN ${jsonEncode(opened)}');
  //15s intended hold with20s absolute qualification bound. No real-world
  //progression/retention inference is made from this synthetic pause.
  while (stopwatch.elapsed < const Duration(seconds: 15)) {
    await Future<void>.delayed(const Duration(milliseconds: 50));
    await tester.pump();
  }
  final closed = checkpoint();
  expect(stopwatch.elapsed, lessThanOrEqualTo(const Duration(seconds: 20)));
  // ignore: avoid_print -- same atomic host checkpoint protocol as OPEN.
  print('TIDEGLASS_PRIVACY_WINDOW_CLOSE ${jsonEncode(closed)}');
  report['privacy_observation_window'] = {'opened': opened, 'closed': closed};
  checked(
    'Bounded synthetic process observation interval completed; not a traffic absence claim.',
  );
}

void checked(String message) => (report['checks'] as List<String>).add(message);

Future<Directory> fixture(String group, {required bool fresh}) async {
  final support = await getApplicationSupportDirectory();
  final directory = Directory(
    '${support.path}/native-current-verification/$label-$runId/$group',
  );
  if (fresh) {
    expect(
      await directory.exists(),
      isFalse,
      reason: 'Use a new run ID. Never erase a previous fixture automatically.',
    );
    await directory.create(recursive: true);
  } else {
    expect(await directory.exists(), isTrue);
  }
  report['fixture_directory'] = directory.path;
  return directory;
}

Future<void> until(
  WidgetTester tester,
  bool Function() ready,
  String reason, {
  Duration timeout = const Duration(seconds: 20),
}) async {
  final elapsed = Stopwatch()..start();
  while (!ready() && elapsed.elapsed < timeout) {
    await Future<void>.delayed(const Duration(milliseconds: 20));
    await tester.pump();
  }
  expect(ready(), isTrue, reason: reason);
}

Finder text(String english) => find.text(Presentation.text(english));
Future<void> tapText(WidgetTester tester, String english) async {
  final target = text(english);
  if (target.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      target,
      250,
      scrollable: find.byType(Scrollable).last,
      maxScrolls: 30,
    );
  }
  await tester.ensureVisible(target);
  await tester.pump();
  expect(target.hitTestable(), findsOneWidget);
  await tester.tap(target.hitTestable());
  await tester.pump();
}

Future<void> screenshot(WidgetTester tester, String suffix) async {
  if (Platform.isAndroid && !androidSurfaceConverted) {
    await binding.convertFlutterSurfaceToImage();
    androidSurfaceConverted = true;
  }
  // Required by integration_test after Android surface conversion, even if UI
  // is static. A recorder exit code alone is not screenshot completion.
  await tester.pump();
  await binding
      .takeScreenshot('$label-$scenario-$suffix')
      .timeout(const Duration(seconds: 15));
}

Future<File> checkpoint(Directory directory, Map<String, Object?> data) async {
  final file = File('${directory.path}/checkpoint.json');
  await file.writeAsString(
    jsonEncode({
      'candidate_fingerprint': candidate,
      'harness_sha256': harness,
      'device_label': label,
      'run_id': runId,
      'preparation_verification_id': verification,
      'native_process_id': pid,
      ...data,
    }),
    flush: true,
  );
  report['checkpoint_sha256'] = hashFile(file);
  return file;
}

Map<String, dynamic> previousCheckpoint(Directory directory) {
  final file = File('${directory.path}/checkpoint.json');
  final value = readObject(file);
  expect(value['candidate_fingerprint'], candidate);
  expect(value['harness_sha256'], harness);
  expect(value['device_label'], label);
  expect(value['run_id'], runId);
  expect(
    value['native_process_id'],
    isNot(pid),
    reason: 'Recovery must use a different native process.',
  );
  report['preparation_verification_id'] = value['preparation_verification_id'];
  report['preparation_checkpoint_sha256'] = hashFile(file);
  report['previous_native_process_id'] = value['native_process_id'];
  return value;
}

Future<Never> holdForExternalKill(File file) async {
  report['expected_interruption'] = true;
  // Host must save this marker, exact process identity and actual kill action.
  // There is deliberately no successful framework/driver completion here.
  // The host verifier requires one unwrapped native checkpoint line. This
  // integration-only marker deliberately bypasses debugPrint throttling.
  // ignore: avoid_print
  print(
    'TIDEGLASS_RUNTIME_KILL_READY ${jsonEncode({'verification_id': verification, 'candidate_fingerprint': candidate, 'harness_sha256': harness, 'scenario': scenario, 'process_id': pid, 'checkpoint': file.path, 'checkpoint_sha256': hashFile(file)})}',
  );
  await Future<void>.delayed(const Duration(seconds: 120));
  throw StateError('Host did not perform the required native process kill.');
}

SaveRepository amountStore(String path, {CommitProbe? probe}) => SaveRepository(
  Directory(path),
  economicVersion: economyVersion,
  economicDigest: bundledEconomyDigest,
  validatePayload: (value) {
    if (value.length != 1 || value['amount'] is! int) {
      throw const FormatException('Synthetic amount fixture');
    }
  },
  commitProbe: probe,
);

@pragma('vm:entry-point')
Future<void> writerIsolate(List<Object> arguments) async {
  final parent = arguments[1] as SendPort;
  final release = ReceivePort();
  try {
    final store = amountStore(
      arguments[0] as String,
      probe: (stage) async {
        if (stage == CommitStage.beforeWrite) {
          parent.send(['locked', release.sendPort]);
          await release.first;
        }
      },
    );
    await store.load();
    await store.save({'amount': 1}, settledThrough: epoch);
    parent.send(['finished']);
  } catch (error, stack) {
    parent.send(['error', '$error\n$stack']);
  } finally {
    release.close();
  }
}

Future<void> lockExclusion() async {
  final directory = await fixture('save-lock', fresh: true);
  final seed = amountStore(directory.path);
  await seed.load();
  await seed.save({'amount': 0}, settledThrough: epoch);
  final contender = amountStore(directory.path);
  await contender.load();
  final port = ReceivePort();
  final messages = StreamIterator<dynamic>(port);
  final worker = await Isolate.spawn(writerIsolate, <Object>[
    directory.path,
    port.sendPort,
  ]);
  SendPort? release;
  try {
    expect(
      await messages.moveNext().timeout(const Duration(seconds: 10)),
      isTrue,
    );
    expect(messages.current[0], 'locked', reason: '${messages.current}');
    release = messages.current[1] as SendPort;
    final competing = contender
        .save({'amount': 2}, settledThrough: epoch)
        .then<Object>((value) => value, onError: (Object error) => error);
    final early = await competing.timeout(
      const Duration(milliseconds: 250),
      onTimeout: () => 'still_waiting',
    );
    expect(
      early,
      'still_waiting',
      reason: 'Separate isolate must not pass held flock.',
    );
    release.send(true);
    expect(
      await messages.moveNext().timeout(const Duration(seconds: 10)),
      isTrue,
    );
    expect(messages.current[0], 'finished', reason: '${messages.current}');
    expect(
      await competing.timeout(const Duration(seconds: 10)),
      isA<SaveConflictException>(),
    );
    expect((await seed.load()).snapshot!.payload, {'amount': 1});
    checked(
      'Real native FFI flock excludes a separate isolate; released writer commits and stale contender conflicts.',
    );
  } finally {
    release?.send(true);
    worker.kill(priority: Isolate.immediate);
    await messages.cancel();
    port.close();
  }
}

Future<void> saveInterruption() async {
  final stage = CommitStage.values.singleWhere(
    (s) => scenario.endsWith(s.name),
  );
  final hold = scenario.startsWith('runtime-save-hold-');
  final directory = await fixture('save-${stage.name}', fresh: hold);
  if (hold) {
    final seed = amountStore(directory.path);
    await seed.load();
    await seed.save({'amount': 0}, settledThrough: epoch);
    final store = amountStore(
      directory.path,
      probe: (at) async {
        if (at == stage) {
          final file = await checkpoint(directory, {'stage': stage.name});
          await holdForExternalKill(file);
        }
      },
    );
    await store.load();
    await store.save({'amount': 1}, settledThrough: epoch);
    fail('Kill preparation must not reach a successful commit return.');
  } else {
    expect(previousCheckpoint(directory)['stage'], stage.name);
    final store = amountStore(directory.path);
    final loaded = await store.load().timeout(const Duration(seconds: 10));
    report['recovered_stage'] = stage.name;
    report['save_loaded_amount'] = loaded.snapshot!.payload['amount'];
    expect(loaded.snapshot!.payload, {
      'amount': stage == CommitStage.afterRename ? 1 : 0,
    });
    await store
        .save({'amount': 2}, settledThrough: epoch)
        .timeout(const Duration(seconds: 10));
    expect((await amountStore(directory.path).load()).snapshot!.payload, {
      'amount': 2,
    });
    report['save_after_recovery_amount'] = 2;
    checked(
      'After externally recorded process kill at ${stage.name}, expected generation loads and OS writer lock is released.',
    );
  }
}

const syntheticVersion = 'tideglass-economy-0.0.1';
const syntheticDigest =
    '9ecd3addb659b78144ecf733239b8003ab3af516897f7e7f7ee2c810955295c6';

class SyntheticNativePredecessor extends TideglassEngine {
  const SyntheticNativePredecessor();
  @override
  String get rulesVersion => syntheticVersion;
  @override
  Fixed producerOutputPerSecond(GameState state, int tierIndex) => Fixed.raw(
    super.producerOutputPerSecond(state, tierIndex).raw *
        BigInt.from(3) ~/
        BigInt.two,
  );
}

Future<void> transition(WidgetTester tester) async {
  final start = scenario == 'runtime-transition-start';
  final directory = await fixture('transition', fresh: start);
  final gameDirectory = Directory('${directory.path}/game');
  const old = SyntheticNativePredecessor();
  if (start) {
    final store = SaveRepository(
      gameDirectory,
      economicVersion: syntheticVersion,
      economicDigest: syntheticDigest,
      validatePayload: (v) =>
          validateClientPayload(v, expectedEconomicVersion: syntheticVersion),
      validateSnapshot: (v, cursor) => validateClientSnapshot(
        v,
        cursor,
        expectedEconomicVersion: syntheticVersion,
      ),
    );
    await store.load();
    final state = old
        .refreshContracts(
          GameState.initial(rulesVersion: syntheticVersion),
          epoch,
          accountSeed: 'synthetic-native-transition',
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
  } else {
    previousCheckpoint(directory);
  }
  final now = epoch.add(Duration(seconds: start ? 60 : 61));
  Future<void> open() async {
    await tester.pumpWidget(
      TideglassBootstrap(
        directory: gameDirectory,
        notifications: isolatedNotifications(gameDirectory),
        enableAudio: false,
        now: () => now,
        economicPredecessors: start
            ? const [
                ClientEconomicPredecessor(engine: old, digest: syntheticDigest),
              ]
            : const [],
      ),
    );
    await until(
      tester,
      () => find.byType(TideglassApp).evaluate().length == 1,
      'Actual native bootstrap completes transition/reopen.',
    );
  }

  await open();
  Future<void> verifyAndSave() async {
    final app = tester.widget<TideglassApp>(find.byType(TideglassApp));
    expect(app.controller.state.rulesVersion, economyVersion);
    expect(
      app.controller.state.lifetimeMicros,
      BigInt.from(start ? 90000000 : 91000000),
    );
    expect(
      app.controller.state.walletMicros,
      BigInt.from(start ? 90000000 : 91000000),
    );
    expect(app.initialPreferences.reduceMotion, isTrue);
    await app.controller.save();
  }

  await verifyAndSave();
  if (start) {
    await checkpoint(directory, {'expected_lifetime_micros': '90000000'});
  } else {
    await tester.pumpWidget(const SizedBox.shrink());
    await open();
    await verifyAndSave();
  }
  report['lifetime_micros'] = tester
      .widget<TideglassApp>(find.byType(TideglassApp))
      .controller
      .state
      .lifetimeMicros
      .toString();
  report['default_predecessor_registration'] = !start;
  report['same_cursor_reopen_checked'] = !start;
  await screenshot(tester, 'harbor');
  checked(
    start
        ? 'Synthetic old1.5R/s settles60s to90R before production rules adoption.'
        : 'Separate-process default bootstrap without predecessor earns1newR once; same-cursor reopen stays91R.',
  );
}

String syntheticProvision() => jsonEncode({
  'study_id': 'synthetic-native-study',
  'protocol_sha256': 'b' * 64,
  'candidate_sha256': candidate,
  'config': 'synthetic_native_qualification',
  'consent_version': 'synthetic-1',
  'information':
      'INTERNAL SYNTHETIC TEST. No participant or valid research consent.',
  'contact': 'https://example.invalid/synthetic-study',
  'retention':
      'Isolated synthetic native fixture only. No recruitment or uploads.',
  'synthetic': true,
  'device_group': label.contains('tablet') ? 'tablet' : 'phone_large',
  'acquisition': 'internal_test',
});

StudySession session(WidgetTester tester) =>
    StudyScope.of(tester.element(find.byType(TideglassApp)))!;
Map<String, dynamic> studyDocument(Directory directory) =>
    readObject(File('${directory.path}/tideglass-study.json'));

Future<void> study(WidgetTester tester) async {
  final fresh = !{
    'runtime-study-restart',
    'runtime-study-crash-reopen',
    'runtime-study-withdraw-reopen',
  }.contains(scenario);
  final directory = await fixture('study', fresh: fresh);
  final support = Directory('${directory.path}/support');
  final gameDirectory = Directory('${support.path}/tideglass');
  var nativeSamples = 0;
  Future<StudyProcessObservation> sampleNative() async {
    nativeSamples++;
    return NativeStudyProcessContext.sample();
  }

  if (scenario == 'runtime-study-default') {
    var recorderOpened = false;
    await tester.pumpWidget(
      StudyGate(
        provision: '',
        supportDirectory: support,
        sampleNativeContext: sampleNative,
        openRecorder: (_) async {
          recorderOpened = true;
          throw StateError('Default study path must not read a store.');
        },
        child: const MaterialApp(home: Text('Default guest fixture')),
      ),
    );
    await tester.pump();
    expect(find.text('Default guest fixture'), findsOneWidget);
    expect(recorderOpened, isFalse);
    expect(nativeSamples, 0);
    report['native_study_samples'] = 0;
    expect(await support.exists(), isFalse);
    checked(
      'Default StudyGate bypasses recorder opening and leaves absent native study support path absent.',
    );
    if (privacyObservation) {
      await guardEmptySharedCache();
      final guestDirectory = Directory('${directory.path}/game');
      await tester.pumpWidget(
        StudyGate(
          provision: '',
          supportDirectory: support,
          sampleNativeContext: sampleNative,
          openRecorder: (_) async {
            recorderOpened = true;
            throw StateError('Default observation must not open a recorder.');
          },
          child: TideglassBootstrap(
            directory: guestDirectory,
            notifications: isolatedNotifications(guestDirectory),
            enableAudio: false,
          ),
        ),
      );
      await until(
        tester,
        () => find.byType(TideglassApp).evaluate().length == 1,
        'Default unprovisioned actual guest opens for process observation.',
      );
      expect(recorderOpened, isFalse);
      expect(nativeSamples, 0);
      expect(await support.exists(), isFalse);
      checked(
        'Optional observed guest uses production Bootstrap with isolated save and no study provision.',
      );
    }
    return;
  }
  Map<String, dynamic>? prior;
  if (!fresh) prior = previousCheckpoint(directory);
  final capacity = scenario == 'runtime-study-capacity';
  var recorderReady = false;
  await tester.pumpWidget(
    StudyGate(
      provision: syntheticProvision(),
      supportDirectory: support,
      sampleNativeContext: sampleNative,
      openRecorder: (store) async {
        final recorder = capacity
            ? await StudyRecorder.open(
                store,
                maximumRecords: 8,
                maximumBytes: 32768,
              )
            : await StudyRecorder.open(store);
        recorderReady = true;
        return recorder;
      },
      child: TideglassBootstrap(
        directory: gameDirectory,
        notifications: isolatedNotifications(gameDirectory),
        enableAudio: false,
      ),
    ),
  );
  if (fresh) {
    await until(
      tester,
      () => recorderReady,
      'Synthetic consent loads before native game bootstrap.',
    );
    expect(await gameDirectory.exists(), isFalse);
    expect(nativeSamples, 0, reason: 'No native observation before consent.');
    await screenshot(tester, 'synthetic-consent');
    await tapText(
      tester,
      'I have read the study information and voluntarily agree to this study.',
    );
    await tapText(tester, 'Agree and open the harbor');
  }
  await until(
    tester,
    () => find.byType(TideglassApp).evaluate().length == 1,
    'Actual app opens through production StudyGate.',
  );
  if (scenario == 'runtime-study-withdraw-reopen') {
    expect(prior!['withdrawn'], isTrue);
    expect(nativeSamples, 0);
    report['native_study_samples'] = 0;
    expect(StudyScope.of(tester.element(find.byType(TideglassApp))), isNull);
    final doc = studyDocument(support);
    expect(doc['registry'], isNull);
    expect(doc['records'], isEmpty);
    expect(doc['status'], 'withdrawn');
    expect(
      await File('${support.path}/tideglass-study-eligibility.json').exists(),
      isFalse,
    );
    expect(
      await File('${support.path}/tideglass-study.json.withdrawn').exists(),
      isTrue,
    );
    report['withdrawal_durable'] = true;
    checked(
      'Separate native process respects durable withdrawal tombstone; no collection session or renewed enrollment.',
    );
    return;
  }
  final current = session(tester);
  await until(
    tester,
    () => (studyDocument(support)['records'] as List).any(
      (r) =>
          r['kind'] == 'harbor_interactive' &&
          r['process_id'] == current.recorder.processId,
    ),
    'Actual app interactive event follows durable app_start.',
  );
  var doc = studyDocument(support);
  expect(doc['registry']['synthetic'], isTrue);
  expect(doc['schema_version'], 2);
  expect(nativeSamples, 1);
  final currentStart = (doc['records'] as List).singleWhere(
    (record) =>
        record['kind'] == 'app_start' &&
        record['process_id'] == current.recorder.processId,
  );
  final nativeContext = Map<String, dynamic>.from(
    currentStart['payload']['native_context'] as Map,
  );
  expect(nativeContext['status'], 'available');
  expect(nativeContext['native_pid'], pid);
  expect(nativeContext['platform'], Platform.operatingSystem);
  expect(nativeContext['application_id'], 'dev.tideglass.game');
  expect(nativeContext['application_version'], '0.1.0');
  expect(nativeContext['application_build'], '1');
  final observed = nativeContext['observed_start_utc_ms'] as int;
  final started = (currentStart['at'] as int) * 1000;
  expect((observed - started).abs(), lessThanOrEqualTo(5000));
  report['native_study_samples'] = nativeSamples;
  report['native_study_process_context'] = nativeContext;
  report['native_study_logical_process_id'] = current.recorder.processId;
  checked(
    'Production consented channel records actual PID/app/build/UTC context atomically with its logical app_start.',
  );
  expect((doc['records'] as List).first['kind'], 'app_start');
  expect(
    (doc['records'] as List).where((r) => r['kind'] == 'terminal'),
    isEmpty,
  );
  if (!fresh) {
    expect(doc['registry']['install_id'], prior!['install_id']);
    expect(doc['registry']['first_launch'], prior['first_launch']);
    expect(
      (doc['records'] as List).first['sha256'],
      prior['first_record_sha256'],
    );
    expect(current.recorder.processId, isNot(prior['study_process_id']));
    final starts = (doc['records'] as List)
        .where((r) => r['kind'] == 'app_start')
        .toList();
    expect(starts.length, (prior['app_start_count'] as int) + 1);
    expect(starts.last['payload']['reason'], 'process_restart');
    expect(
      starts.first['payload']['native_context']['native_pid'],
      prior['native_process_id'],
    );
    expect(starts.last['payload']['native_context']['native_pid'], pid);
    report['study_identity_and_chain_retained'] = true;
    report['new_study_process_recorded'] = true;
    report['invented_terminal_count'] = 0;
    checked(
      'Native process restart preserves install/first-launch/hash chain and adds distinct process_start without inventing clean exit.',
    );
  }
  Future<File> saveStudyCheckpoint() => checkpoint(directory, {
    'install_id': doc['registry']['install_id'],
    'first_launch': doc['registry']['first_launch'],
    'first_record_sha256': (doc['records'] as List).first['sha256'],
    'study_process_id': current.recorder.processId,
    'native_process_observation': nativeContext,
    'app_start_count': (doc['records'] as List)
        .where((r) => r['kind'] == 'app_start')
        .length,
  });
  if (scenario == 'runtime-study-enroll' ||
      scenario == 'runtime-study-crash-hold') {
    await current.capture(
      () => current.recorder.activity(StudyActivity.interaction),
    );
    doc = studyDocument(support);
    final file = await saveStudyCheckpoint();
    checked(
      'Synthetic opt-in UI persists first launch before real harbor interactive event and activity.',
    );
    if (scenario == 'runtime-study-crash-hold') await holdForExternalKill(file);
  }
  if (capacity || scenario == 'runtime-study-storage-withdraw') {
    final settings = find.byTooltip(Presentation.text(Copy.settings));
    await tester.tap(settings);
    await tester.pump();
    await until(
      tester,
      () => find.byType(StudyControls).evaluate().isNotEmpty,
      'Production settings expose collection status.',
    );
    if (capacity) {
      for (var i = 0; i < 12 && current.active; i++) {
        await current.capture(
          () => current.recorder.activity(StudyActivity.navigation),
        );
      }
      expect(current.recorder.exhausted, isTrue);
      doc = studyDocument(support);
      expect((doc['records'] as List).length, lessThanOrEqualTo(8));
      expect((doc['records'] as List).last['payload']['reason'], 'capacity');
      expect(
        await File('${support.path}/tideglass-study.json').length(),
        lessThanOrEqualTo(32768),
      );
      await tester.pump();
      expect(
        text(
          'Study recording has stopped. Contact the study team about missing records.',
        ),
        findsOneWidget,
      );
      report['study_capacity_records'] = (doc['records'] as List).length;
      report['study_capacity_bytes'] = await File(
        '${support.path}/tideglass-study.json',
      ).length();
      report['study_capacity_gap'] = true;
      await screenshot(tester, 'capacity-visible');
      checked(
        'Injected8record bound stops durably with capacity gap and visible production status; no silent unbounded growth.',
      );
    } else {
      // Deliberately create our own synthetic stale CAS guard. This is a real
      // native-filesystem refusal, not a full-volume/physical-disk simulation.
      final guard = File('${support.path}/tideglass-study.json.cas-guard');
      expect(await guard.exists(), isFalse);
      await guard.create(exclusive: true);
      try {
        await current.capture(
          () => current.recorder.activity(StudyActivity.navigation),
        );
        expect(current.failed, isTrue);
        expect(current.failureCode, 'stale_store_writer');
        expect(current.active, isFalse);
        await tester.pump();
        expect(
          text(
            'Study recording has stopped after an error. You can copy the available records or withdraw; contact the study team about missing records.',
          ),
          findsOneWidget,
        );
        await screenshot(tester, 'storage-failure-visible');
      } finally {
        await guard.delete(); // Only the guard created by this fixture.
      }
      await tapText(tester, 'Withdraw and erase local study records');
      await tapText(tester, 'Withdraw and erase');
      await until(
        tester,
        () => !current.erasing && current.recorder.withdrawn,
        'UI withdrawal finishes durable native erasure.',
      );
      expect(current.erasurePending, isFalse);
      expect(current.canExport, isFalse);
      doc = studyDocument(support);
      expect(doc['registry'], isNull);
      expect(doc['records'], isEmpty);
      expect(
        await File('${support.path}/tideglass-study-eligibility.json').exists(),
        isFalse,
      );
      report['storage_failure_visible'] = true;
      report['withdrawal_durable'] = true;
      await checkpoint(directory, {'withdrawn': true});
      await screenshot(tester, 'withdrawn');
      checked(
        'Synthetic native CAS refusal stops visibly; confirmed UI withdrawal erases registry/events/eligibility and persists stop marker.',
      );
    }
  }
}

Future<void> cacheGrace() async {
  // The application temporary directory is real, but only this unique subtree
  // is touched. exportSoundtrack's shared cache path is deliberately not used.
  final nativeTemp = await getTemporaryDirectory();
  final directory = Directory(
    '${nativeTemp.path}/native-current-verification/$label-$runId/cache',
  );
  expect(await directory.exists(), isFalse);
  report['fixture_directory'] = directory.path;
  var now = DateTime.now().toUtc();
  final cache = SoundtrackExportCache(directory, now: () => now);
  Future<File> add(String id) async {
    final child = await Directory('${directory.path}/soundtrack-$id')
        .create(recursive: true);
    return File('${child.path}/${SoundtrackDelivery.filename}')
        .writeAsString('SYNTHETIC CACHE RETENTION FIXTURE', flush: true);
  }

  final retained = <File>[];
  for (var i = 0; i < 3; i++) {
    retained.add(await cache.export((_) => add('$i')));
  }
  var fourthStarted = false;
  await expectLater(
    cache.export((_) async {
      fourthStarted = true;
    }),
    throwsA(
      isA<SoundtrackCacheException>().having(
        (e) => e.code,
        'code',
        'recent_exports_at_capacity',
      ),
    ),
  );
  expect(fourthStarted, isFalse);
  now = DateTime.now().toUtc().subtract(const Duration(days: 2));
  await cache.cleanExpired();
  for (final file in retained) {
    expect(await file.exists(), isTrue);
  }
  now = DateTime.now().toUtc().add(const Duration(hours: 23));
  await cache.cleanExpired();
  for (final file in retained) {
    expect(await file.readAsString(), 'SYNTHETIC CACHE RETENTION FIXTURE');
  }
  now = DateTime.now().toUtc().add(const Duration(hours: 25));
  await cache.cleanExpired();
  expect(await directory.list().length, 0);
  checked(
    'Real native files survive backward clock and23h injected grace; fourth export refuses before download;25h cleans expired files.',
  );

  now = DateTime.now().toUtc();
  final entered = Completer<void>(), released = Completer<void>();
  final held = cache.export((_) async {
    final file = await add('held');
    entered.complete();
    await released.future;
    expect(await file.readAsString(), 'SYNTHETIC CACHE RETENTION FIXTURE');
  });
  await entered.future;
  try {
    await expectLater(
      cache.export((_) async {}),
      throwsA(
        isA<SoundtrackCacheException>().having(
          (e) => e.code,
          'code',
          'export_in_progress',
        ),
      ),
    );
    now = now.add(const Duration(hours: 25));
    await cache.cleanExpired(); // Busy receiving-action must preserve file.
    expect(
      await File(
        '${directory.path}/soundtrack-held/${SoundtrackDelivery.filename}',
      ).exists(),
      isTrue,
    );
  } finally {
    released.complete();
    await held;
  }
  await cache.cleanExpired();
  expect(await directory.list().length, 0);
  final oversized = await add('oversized');
  final handle = await oversized.open(mode: FileMode.write);
  await handle.truncate(SoundtrackDelivery.maximumBytes + 1);
  await handle.close();
  var started = false;
  await expectLater(
    cache.export((_) async {
      started = true;
    }),
    throwsA(
      isA<SoundtrackCacheException>().having(
        (e) => e.code,
        'code',
        'oversized_cache_entry',
      ),
    ),
  );
  expect(started, isFalse);
  checked(
    'Held synthetic receiving-action prevents cleanup/new export; oversized native cache file blocks another download. No actual receiving app is claimed.',
  );
  report['cache_limits'] = {
    'exports': SoundtrackExportCache.maximumExports,
    'bytes': SoundtrackExportCache.maximumBytes,
    'grace_seconds': SoundtrackExportCache.retention.inSeconds,
  };
}

Future<void> guardEmptySharedCache() async {
  final temp = await getTemporaryDirectory();
  final shared = Directory('${temp.path}/tideglass-soundtrack-exports');
  final type = await FileSystemEntity.type(shared.path, followLinks: false);
  expect(
    type,
    anyOf(FileSystemEntityType.notFound, FileSystemEntityType.directory),
  );
  if (type == FileSystemEntityType.directory) {
    expect(
      await shared.list(followLinks: false).isEmpty,
      isTrue,
      reason: 'Bootstrap maintenance must never clean a pre-existing shared archive. Use an isolated test app/device.',
    );
  }
  report['shared_cache_preflight'] = 'Absent/empty before bootstrap; optional production maintenance may create an empty shared cache.';
}

// Reminder delivery is outside these tests. This fixture prevents bootstrap
// from cancelling the ordinary app's OS notification IDs during qualification.
NotificationService isolatedNotifications(Directory directory) {
  final service = NotificationService(
    gateway: QuietFixtureNotificationGateway(),
    store: FileNotificationPreferences(
      File('${directory.path}/notification_preferences.json'),
    ),
  );
  fixtureNotifications.add(service);
  return service;
}

class QuietFixtureNotificationGateway implements NotificationGateway {
  @override
  Future<void> initialize() async {}
  @override
  Future<void> cancelReminders() async {}
  @override
  Future<ReminderPermission> permission() async => ReminderPermission.denied;
  @override
  Future<ReminderPermission> requestPermission() async =>
      throw StateError('No native permission requests in this harness');
  @override
  Future<void> schedule(PlannedReminder reminder) async =>
      throw StateError('No native reminders in this harness');
  @override
  Future<String> timeZone() async => 'UTC';
  @override
  Future<void> openSettings() async =>
      throw StateError('No OS settings changes in this harness');
}
