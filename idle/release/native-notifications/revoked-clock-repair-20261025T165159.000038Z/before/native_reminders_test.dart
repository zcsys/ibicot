// Simulator/emulator qualification only. Real plugin and OS APIs; synthetic
// isolated gameplay state. No permission-channel mocks or artificial clocks.
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass/bundled_content.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/notification_copy.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/reminder_lifecycle.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';
import 'package:timezone/timezone.dart' as tz;

const scenario = String.fromEnvironment('TIDEGLASS_SCENARIO');
const label = String.fromEnvironment('TIDEGLASS_DEVICE_LABEL');
const runId = String.fromEnvironment('TIDEGLASS_RUN_ID');
const candidate = String.fromEnvironment('TIDEGLASS_CANDIDATE_FINGERPRINT');
const harness = String.fromEnvironment('TIDEGLASS_HARNESS_SHA256');
const verification = String.fromEnvironment('TIDEGLASS_VERIFICATION_ID');
const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked',
  'revoked-prepare', 'revoked-recover'};
late IntegrationTestWidgetsFlutterBinding binding;
Map<String, dynamic> get report => binding.reportData!;
int utcMs() => DateTime.now().toUtc().millisecondsSinceEpoch;

void action(String value, [Map<String, dynamic> details = const {}]) {
  final row = <String, dynamic>{
    'verification_id': verification,
    'candidate_fingerprint': candidate,
    'harness_sha256': harness,
    'scenario': scenario,
    'run_id': runId,
    'device_label': label,
    'platform': Platform.operatingSystem,
    'process_id': pid,
    'action': value,
    'utc_ms': utcMs(),
    ...details,
  };
  (report['actions'] as List).add(row);
  // ignore: avoid_print -- one unwrapped host protocol record.
  print('TIDEGLASS_REMINDER_ACTION ${jsonEncode(row)}');
}

Future<void> until(
  bool Function() ready, {
  required String reason,
  int seconds = 120,
}) async {
  final watch = Stopwatch()..start();
  while (!ready() && watch.elapsed < Duration(seconds: seconds)) {
    await Future<void>.delayed(const Duration(milliseconds: 100));
    // OS lifecycle observations do not require a rendered frame. A live
    // tester.pump can wait indefinitely for the next frame while paused.
  }
  expect(ready(), isTrue, reason: reason);
}

class NativeLifecycleObservation extends WidgetsBindingObserver {
  final events = <Map<String, dynamic>>[];
  Future<void> Function(AppLifecycleState)? onChange;
  Object? error;
  StackTrace? errorStack;
  final failures = <Map<String, dynamic>>[];
  Future<void> tail = Future.value();
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    events.add({'state': state.name, 'utc_ms': utcMs()});
    final callback = onChange;
    if (callback != null) {
      tail = tail.then((_) => callback(state)).catchError((
        Object failure,
        StackTrace stack,
      ) {
        error ??= failure;
        errorStack ??= stack;
        failures.add({
          'state': state.name,
          'utc_ms': utcMs(),
          'error_type': failure.runtimeType.toString(),
          'error': failure.toString(),
          'stack': stack.toString(),
        });
      });
    }
  }
}

void main() {
  binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('real OS reminder qualification: $scenario', (tester) async {
    expect(Platform.isIOS || Platform.isAndroid, isTrue);
    expect(scenarios, contains(scenario));
    if (scenario.startsWith('revoked-')) expect(Platform.isAndroid, isTrue);
    for (final value in [label, runId, verification]) {
      expect(RegExp(r'^[A-Za-z0-9_-]{1,160}$').hasMatch(value), isTrue);
    }
    for (final value in [candidate, harness]) {
      expect(RegExp(r'^[a-f0-9]{64}$').hasMatch(value), isTrue);
    }
    expect(const String.fromEnvironment('TIDEGLASS_SERVICE_URL'), isEmpty);
    expect(const bool.fromEnvironment('TIDEGLASS_COMMERCE'), isFalse);
    expect(const bool.fromEnvironment('TIDEGLASS_REWARDED_ADS'), isFalse);
    expect(const bool.fromEnvironment('TIDEGLASS_SUPPORTER'), isFalse);
    binding.reportData = {
      'verification_id': verification,
      'candidate_fingerprint': candidate,
      'harness_sha256': harness,
      'scenario': scenario,
      'run_id': runId,
      'device_label': label,
      'platform': Platform.operatingSystem,
      'process_id': pid,
      'fixture_kind': 'SYNTHETIC GAMEPLAY SNAPSHOT; REAL OS NOTIFICATION API',
      'gateway': 'NativeNotificationGateway',
      'preference_store': 'FileNotificationPreferences',
      'clock': 'actual_utc_and_monotonic_stopwatch',
      'completed': false,
      'actions': <Map<String, dynamic>>[],
      'limitations': [
        'Simulator/emulator only; no physical delivery, battery or lock-screen guarantee.',
        'Seeded Focus phase is not natural player progression.',
        'OS permission UI must be operated directly; no grant/revoke bypass.',
        'API delivered records do not prove that a person saw a banner.',
      ],
    };
    final support = await getApplicationSupportDirectory();
    if (scenario == 'revoked-recover') {
      await recoverRevoked(tester, support);
      return;
    }
    final dir = Directory(
      '${support.path}/native-reminders/$label-$runId-$scenario',
    );
    expect(
      await dir.exists(),
      isFalse,
      reason: 'Use a fresh run ID; never erase evidence.',
    );
    await dir.create(recursive: true);
    report['fixture_directory'] = dir.path;
    final preferenceFile = File('${dir.path}/notification_preferences.json');
    final store = FileNotificationPreferences(preferenceFile);
    final gateway = NativeNotificationGateway();
    final service = NotificationService(gateway: gateway, store: store);
    final observation = NativeLifecycleObservation();
    WidgetsBinding.instance.addObserver(observation);
    report['lifecycle_events'] = observation.events;
    report['lifecycle_callback_failures'] = observation.failures;
    GameController? game;
    ReminderLifecycle? lifecycle;
    addTearDown(() async {
      observation.onChange = null;
      await observation.tail;
      WidgetsBinding.instance.removeObserver(observation);
      lifecycle?.close();
      game?.dispose();
      await gateway.cancelReminders();
      service.dispose();
      await tester.pumpWidget(const SizedBox.shrink());
    });
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SafeArea(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'Tideglass reminder qualification\n\nInternal synthetic state. Real OS notifications.\nFollow the evidence runner’s current action; use the app icon to return, not the notification.',
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    // Query before initialize as well as after: the real OS permission state
    // must not change merely from production initialization/default settings.
    final before = await gateway.permission();
    report['permission_before_initialize'] = before.name;
    final initEvents = observation.events.length;
    await service.initialize();
    await tester.pump();
    report['initialization_lifecycle_events'] = observation.events
        .skip(initEvents)
        .toList();
    expect(
      observation.events
          .skip(initEvents)
          .any((e) => {'inactive', 'hidden', 'paused'}.contains(e['state'])),
      isFalse,
      reason: 'Default initialization must not open a permission UI.',
    );
    expect(service.warningKey, isNull);
    expect(service.preferences.enabled, isFalse);
    expect(service.permission, before);
    expect(await preferenceFile.exists(), isFalse);
    expect(await pending(gateway), isEmpty);
    report['permission_after_initialize'] = service.permission.name;
    report['default_opted_out'] = true;
    report['default_preferences_file_absent'] = true;
    report['default_pending_ids'] = await pending(gateway);
    if (scenario != 'default') {
      action(
        scenario == 'denied'
            ? 'deny_permission_if_prompted'
            : 'allow_permission_if_prompted',
      );
      await service.enableByPlayer().timeout(const Duration(seconds: 150));
      report['permission_after_opt_in'] = service.permission.name;
      report['preferences_after_opt_in'] = (await store.load()).toJson();
      if (scenario == 'denied') {
        expect(service.permission, ReminderPermission.denied);
        expect(service.preferences.enabled, isFalse);
        expect(await pending(gateway), isEmpty);
        report['denied_pending_ids'] = await pending(gateway);
      } else {
        expect(
          service.permission,
          ReminderPermission.allowed,
          reason: 'This scenario requires actual OS approval; inability is unqualified.',
        );
        expect(service.preferences.enabled, isTrue);
        final repository = SaveRepository(
          Directory('${dir.path}/save'),
          economicVersion: economyVersion,
          economicDigest: bundledEconomicDigest,
          validatePayload: (payload) {
            GameState.fromJson(payload);
          },
        );
        await repository.load();
        game = GameController(
          initialState: GameState(
            focusPhaseMicros:
                TideglassEngine.focusCycleMicros - BigInt.from(240000000),
          ),
          startTicker: false,
          onPersist: (state, through) async {
            await repository.save(state.toJson(), settledThrough: through);
          },
        );
        lifecycle = ReminderLifecycle(game, service);
        await service.updatePreferences(
          service.preferences.copyWith(
            focus: true,
            survey: false,
            storage: false,
            quiet: false,
          ),
        );
        if (scenario == 'quiet-cancel') {
          final location = reminderLocation(await gateway.timeZone());
          final local = tz.TZDateTime.from(DateTime.now(), location);
          final start = local.hour * 60 + local.minute;
          final end = (start + 60) % 1440;
          await service.updatePreferences(
            service.preferences.copyWith(
              quiet: true,
              quietStart: start,
              quietEnd: end,
            ),
          );
          report['quiet_window'] = {
            'zone': location.name,
            'start_minute': start,
            'end_minute': end,
          };
          report['background_call_utc_ms'] = utcMs();
          await lifecycle.backgrounded();
          await recordPlan(service, gateway, repository, game);
          final due = tz.TZDateTime.from(
            service.planned.single.dueUtc,
            location,
          );
          expect(due.hour * 60 + due.minute, end);
          report['quiet_due_local_minute'] = due.hour * 60 + due.minute;
          await lifecycle.returned();
          expect(await pending(gateway), isEmpty);
          report['return_pending_ids'] = await pending(gateway);
        } else if (scenario == 'revoked-prepare') {
          report['background_call_utc_ms'] = utcMs();
          await lifecycle.backgrounded();
          await recordPlan(service, gateway, repository, game);
          report['preferences_sha256'] = await fileDigest(preferenceFile);
          final checkpoint = <String, dynamic>{
            'version': 1,
            'preparation': report,
            'files_sha256': await restartFiles(dir),
            'written_utc_ms': utcMs(),
          };
          final file = File('${dir.path}/revoke-checkpoint.json');
          expect(await file.exists(), isFalse);
          await file.writeAsString(jsonEncode(checkpoint), flush: true);
          action('revoke_in_os_settings_expect_process_death', {
            'checkpoint': file.path,
            'checkpoint_sha256': await fileDigest(file),
          });
          await service.openDeviceSettings();
          // Android may terminate this process for PERMISSION CHANGE. This
          // preparation never reports a passed/completed integration test.
          await until(() => false,
              reason: 'Actual Android permission-change termination required.',
              seconds: 180);
        } else if (scenario == 'revoked') {
          report['background_call_utc_ms'] = utcMs();
          await lifecycle.backgrounded();
          await recordPlan(service, gateway, repository, game);
          final baseline = observation.events.length;
          action('revoke_in_os_settings_then_return_via_app_icon');
          await service.openDeviceSettings();
          await until(
            () => observation.events
                .skip(baseline)
                .any((e) => e['state'] == 'resumed'),
            reason: 'Actual Settings departure and return required.',
            seconds: 180,
          );
          expect(
            observation.events
                .skip(baseline)
                .any((e) => e['state'] == 'paused' || e['state'] == 'hidden'),
            isTrue,
          );
          await lifecycle.returned();
          expect(service.permission, ReminderPermission.denied);
          expect(await pending(gateway), isEmpty);
          report['permission_after_revoke'] = service.permission.name;
          report['revoke_pending_ids'] = await pending(gateway);
          action('deny_permission_again_if_prompted');
          await service.enableByPlayer().timeout(const Duration(seconds: 150));
          expect(service.permission, ReminderPermission.denied);
          expect((await store.load()).enabled, isFalse);
          report['revoked_opt_in_stays_disabled'] = true;
        } else {
          final watch = Stopwatch()..start();
          bool scheduled = false, returned = false;
          var earliestReturn = 0;
          Map<String, dynamic>? observedPlan;
          observation.onChange = (state) async {
            // Native callbacks may arrive outside package:test's Zone. Only
            // observe/call production APIs here; matchers run in the test body.
            if (state == AppLifecycleState.paused && !scheduled) {
              report['background_call_utc_ms'] = utcMs();
              await lifecycle!.backgrounded();
              observedPlan = await observeReminderPlan(
                service,
                gateway,
                repository,
                game!,
              );
              report['plan_observation'] = observedPlan;
              report['scheduled_elapsed_ms'] = watch.elapsedMilliseconds;
              scheduled = true;
              final plans = observedPlan!['planned'] as List;
              if (plans.length == 1) {
                earliestReturn = plans.single['due_utc_ms'] as int;
                action('wait_until_due_then_return_via_app_icon', {
                  'not_before_utc_ms': earliestReturn,
                });
              }
            } else if (state == AppLifecycleState.resumed &&
                scheduled &&
                !returned) {
              report['returned_utc_ms'] = utcMs();
              report['returned_elapsed_ms'] = watch.elapsedMilliseconds;
              // Preserve actual delivered records before production cancellation.
              final delivered = await gateway.plugin.getActiveNotifications();
              report['delivered_records'] = [
                for (final item in delivered)
                  if (ReminderPlanner.ids.contains(item.id))
                    {'id': item.id, 'title': item.title, 'body': item.body},
              ];
              report['delivery_observed_utc_ms'] = utcMs();
              await lifecycle!.returned();
              report['return_pending_ids'] = await pending(gateway);
              report['return_active_ids'] = [
                for (final item
                    in await gateway.plugin.getActiveNotifications())
                  if (ReminderPlanner.ids.contains(item.id)) item.id,
              ];
              returned = true;
            }
          };
          action('background_app_now_using_os_home');
          await until(
            () => scheduled || observation.error != null,
            reason: 'An actual native pause must produce a plan observation.',
            seconds: 720,
          );
          rethrowLifecycleFailure(observation);
          expect(observedPlan, isNotNull);
          report['plan'] = validateObservedReminderPlan(observedPlan!);
          // Preserve the original total observation budget, including Home
          // operation and scheduling; neither phase restarts the real clock.
          final elapsedSeconds =
              (watch.elapsedMicroseconds / Duration.microsecondsPerSecond)
                  .ceil();
          final remainingSeconds = 720 - elapsedSeconds;
          expect(remainingSeconds, greaterThan(0));
          await until(
            () => returned || observation.error != null,
            reason: 'Real production-minimum elapsed delivery and native return required.',
            seconds: remainingSeconds,
          );
          await observation.tail;
          rethrowLifecycleFailure(observation);
          expect(scheduled && returned, isTrue);
          validateObservedReminderDelivery(report, earliestReturn);
          report['actual_background_and_return'] = true;
          observation.onChange = null;
        }
      }
    }
    report['lifecycle_events'] = observation.events;
    if (await preferenceFile.exists()) {
      report['preferences_sha256'] = sha256
          .convert(await preferenceFile.readAsBytes())
          .toString();
    }
    expect(observation.error, isNull);
    report['completed'] = true;
  }, timeout: const Timeout(Duration(minutes: 15)));
}

Future<List<int>> pending(NativeNotificationGateway gateway) async =>
    (await gateway.plugin.pendingNotificationRequests())
        .where((item) => ReminderPlanner.ids.contains(item.id))
        .map((item) => item.id)
        .toList()
      ..sort();

void rethrowLifecycleFailure(NativeLifecycleObservation observation) {
  final error = observation.error;
  if (error != null) {
    Error.throwWithStackTrace(error, observation.errorStack!);
  }
}

Future<Map<String, dynamic>> observeReminderPlan(
  NotificationService service,
  NativeNotificationGateway gateway,
  SaveRepository repository,
  GameController game,
) async {
  final warning = service.warningKey;
  final plans = List<PlannedReminder>.of(service.planned);
  final ids = await pending(gateway);
  final saved = (await repository.load()).snapshot;
  final observed = DateTime.now().toUtc();
  return {
    'background_call_utc_ms': report['background_call_utc_ms'],
    'warning_key': warning,
    'planned': [
      for (final plan in plans)
        {
          'id': plan.id,
          'due_utc_ms': plan.dueUtc.millisecondsSinceEpoch,
          'due_utc_micros': plan.dueUtc.microsecondsSinceEpoch,
          'zone': plan.zoneName,
          'kinds': plan.kinds.map((x) => x.name).toList(),
          'body': plan.body(const NotificationCopy()),
        },
    ],
    'pending_ids': ids,
    'saved_payload': saved?.payload,
    'saved_settled_through_utc_micros': saved?.settledThrough
        .toUtc()
        .microsecondsSinceEpoch,
    'saved_snapshot_id': saved?.saveId,
    'game_payload': game.state.toJson(),
    'game_settled_through_utc_micros': game.settledThrough
        .toUtc()
        .microsecondsSinceEpoch,
    'observed_utc_ms': observed.millisecondsSinceEpoch,
    'observed_utc_micros': observed.microsecondsSinceEpoch,
  };
}

Map<String, dynamic> validateObservedReminderPlan(
  Map<String, dynamic> observed,
) {
  expect(observed['warning_key'], isNull);
  final plans = observed['planned'] as List;
  expect(plans.length, 1);
  expect(observed['pending_ids'], [77101]);
  expect(observed['saved_snapshot_id'], isNotNull);
  expect(observed['saved_payload'], observed['game_payload']);
  expect(
    observed['saved_settled_through_utc_micros'],
    observed['game_settled_through_utc_micros'],
  );
  final plan = plans.single as Map;
  // Evaluate future-ness at the actual scheduling observation, not minutes
  // later when a suspended test body may first get CPU time after return.
  expect(plan['due_utc_micros'], greaterThan(observed['observed_utc_micros']));
  return {
    'background_call_utc_ms': observed['background_call_utc_ms'],
    'scheduled_observed_utc_ms': observed['observed_utc_ms'],
    'due_utc_ms': plan['due_utc_ms'],
    'settled_through_utc_ms':
        (observed['game_settled_through_utc_micros'] as int) ~/ 1000,
    'zone': plan['zone'],
    'ids': observed['pending_ids'],
    'kinds': plan['kinds'],
    'body': plan['body'],
    'saved_payload_sha256': sha256
        .convert(utf8.encode(jsonEncode(observed['saved_payload'])))
        .toString(),
    'saved_snapshot_id': observed['saved_snapshot_id'],
    'production_lifecycle': true,
  };
}

void validateObservedReminderDelivery(
  Map<String, dynamic> observed,
  int dueMs,
) {
  expect(observed['delivery_observed_utc_ms'], greaterThanOrEqualTo(dueMs));
  final delivered = observed['delivered_records'] as List;
  expect(
    delivered,
    isNotEmpty,
    reason: 'A scheduled request alone is not actual delivery.',
  );
  expect(
    delivered.any(
      (dynamic row) =>
          row['id'] == 77101 &&
          row['body'] == const NotificationCopy().text('focusBody'),
    ),
    isTrue,
  );
  expect(observed['return_pending_ids'], isEmpty);
  expect(observed['return_active_ids'], isEmpty);
}

Future<void> recordPlan(
  NotificationService service,
  NativeNotificationGateway gateway,
  SaveRepository repository,
  GameController game,
) async {
  final observed = await observeReminderPlan(
    service,
    gateway,
    repository,
    game,
  );
  report['plan_observation'] = observed;
  report['plan'] = validateObservedReminderPlan(observed);
}


Future<String> fileDigest(File file) async =>
    sha256.convert(await file.readAsBytes()).toString();

Future<Map<String, String>> restartFiles(Directory dir,
    {bool includePreferences = true}) async {
  final files = <String, String>{};
  for (final relative in [
    if (includePreferences) 'notification_preferences.json',
    'save/progress.0.json', 'save/progress.1.json',
  ]) {
    final file = File('${dir.path}/$relative');
    if (await file.exists()) files[relative] = await fileDigest(file);
  }
  expect(files.keys.where((key) => key.startsWith('save/')), isNotEmpty);
  if (includePreferences) expect(files, contains('notification_preferences.json'));
  return files;
}

Future<List<int>> activeReminderIds(NativeNotificationGateway gateway) async =>
    (await gateway.plugin.getActiveNotifications())
        .where((item) => ReminderPlanner.ids.contains(item.id))
        .map((item) => item.id!).toList()..sort();

Future<void> recoverRevoked(WidgetTester tester, Directory support) async {
  const priorId = String.fromEnvironment('TIDEGLASS_PREDECESSOR_ID');
  const checkpointDigest = String.fromEnvironment('TIDEGLASS_PREDECESSOR_CHECKPOINT');
  expect(RegExp(r'^[A-Za-z0-9_-]{1,160}$').hasMatch(priorId), isTrue);
  expect(RegExp(r'^[a-f0-9]{64}$').hasMatch(checkpointDigest), isTrue);
  final dir = Directory('${support.path}/native-reminders/$label-$runId-revoked-prepare');
  final checkpointFile = File('${dir.path}/revoke-checkpoint.json');
  expect(await dir.exists(), isTrue);
  expect(await fileDigest(checkpointFile), checkpointDigest);
  final checkpoint = (jsonDecode(await checkpointFile.readAsString()) as Map)
      .cast<String, dynamic>();
  expect(checkpoint['version'], 1);
  final prior = (checkpoint['preparation'] as Map).cast<String, dynamic>();
  for (final entry in {
    'verification_id': priorId, 'candidate_fingerprint': candidate,
    'harness_sha256': harness, 'scenario': 'revoked-prepare', 'run_id': runId,
    'device_label': label, 'platform': 'android',
  }.entries) { expect(prior[entry.key], entry.value); }
  expect(prior['completed'], isFalse);
  expect(prior['process_id'], isA<int>());
  expect(prior['process_id'], greaterThan(1));
  expect(pid, isNot(prior['process_id']));
  final hashes = (checkpoint['files_sha256'] as Map).cast<String, String>();
  expect(await restartFiles(dir), hashes);
  report.addAll({
    'fixture_directory': dir.path,
    'predecessor_verification_id': priorId,
    'predecessor_checkpoint_sha256': checkpointDigest,
    'previous_process_id': prior['process_id'],
    'recovery_files_before': await restartFiles(dir),
    'predecessor_default_opted_out': prior['default_opted_out'],
  });
  final store = FileNotificationPreferences(File('${dir.path}/notification_preferences.json'));
  expect((await store.load()).enabled, isTrue);
  final gateway = NativeNotificationGateway();
  final service = NotificationService(gateway: gateway, store: store);
  final observation = NativeLifecycleObservation();
  WidgetsBinding.instance.addObserver(observation);
  addTearDown(() async {
    WidgetsBinding.instance.removeObserver(observation);
    await gateway.cancelReminders();
    service.dispose();
    await tester.pumpWidget(const SizedBox.shrink());
  });
  await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text(
      'Tideglass reminder restart qualification. Real permission denial; retained synthetic save.'))));
  report['permission_before_initialize'] = (await gateway.permission()).name;
  // Android may already have removed an alarm/notification on revocation.
  // Record that separately from what production initialization cancels.
  report['pending_before_initialize'] = await pending(gateway);
  report['active_before_initialize'] = await activeReminderIds(gateway);
  expect(report['permission_before_initialize'], 'denied');
  final initBaseline = observation.events.length;
  await service.initialize();
  await tester.pump();
  report['initialization_lifecycle_events'] = observation.events.skip(initBaseline).toList();
  expect(observation.events.skip(initBaseline).where((row) => row['state'] != 'resumed'), isEmpty);
  expect(service.warningKey, isNull);
  expect(service.permission, ReminderPermission.denied);
  expect(service.preferences.enabled, isTrue,
      reason: 'Remembered opt-in is distinct from denied effective permission.');
  report['permission_after_initialize'] = service.permission.name;
  report['remembered_opt_in_after_initialize'] = service.preferences.enabled;
  report['pending_after_initialize'] = await pending(gateway);
  report['active_after_initialize'] = await activeReminderIds(gateway);
  expect(report['pending_after_initialize'], isEmpty);
  expect(report['active_after_initialize'], isEmpty);
  final repository = SaveRepository(Directory('${dir.path}/save'),
      economicVersion: economyVersion, economicDigest: bundledEconomicDigest,
      validatePayload: (payload) { GameState.fromJson(payload); });
  final saved = (await repository.load()).snapshot;
  expect(saved, isNotNull);
  final observed = (prior['plan_observation'] as Map).cast<String, dynamic>();
  expect(saved!.payload, observed['saved_payload']);
  expect(saved.saveId, observed['saved_snapshot_id']);
  expect(saved.settledThrough.toUtc().microsecondsSinceEpoch,
      observed['saved_settled_through_utc_micros']);
  report['restored_snapshot_id'] = saved.saveId;
  report['restored_payload_sha256'] = sha256.convert(utf8.encode(jsonEncode(saved.payload))).toString();
  report['restored_settled_through_utc_micros'] = saved.settledThrough.toUtc().microsecondsSinceEpoch;
  // Use the real scheduling path with the preserved saved state. Do not save
  // or settle it again merely to test the OS permission gate.
  await service.scheduleForAbsence(state: GameState.fromJson(saved.payload),
      settledThrough: saved.settledThrough);
  expect(service.permission, ReminderPermission.denied);
  expect(service.planned, isEmpty);
  expect(service.warningKey, isNull);
  report['denied_schedule_pending_ids'] = await pending(gateway);
  report['denied_schedule_active_ids'] = await activeReminderIds(gateway);
  expect(report['denied_schedule_pending_ids'], isEmpty);
  expect(report['denied_schedule_active_ids'], isEmpty);
  await service.onReturn();
  expect(service.warningKey, isNull);
  report['recovery_files_before_reoptin'] = await restartFiles(dir);
  expect(report['recovery_files_before_reoptin'], hashes);
  action('deny_permission_again_if_prompted');
  await service.enableByPlayer().timeout(const Duration(seconds: 150));
  expect(service.permission, ReminderPermission.denied);
  expect((await store.load()).enabled, isFalse);
  expect(service.warningKey, isNull);
  report['permission_after_reoptin'] = service.permission.name;
  report['preferences_after_reoptin'] = (await store.load()).toJson();
  report['preferences_sha256'] = await fileDigest(File('${dir.path}/notification_preferences.json'));
  report['recovery_save_files_after'] = await restartFiles(dir, includePreferences: false);
  expect(report['recovery_save_files_after'], Map<String, String>.from(hashes)
      ..remove('notification_preferences.json'));
  expect(await fileDigest(checkpointFile), checkpointDigest);
  report['return_pending_ids'] = await pending(gateway);
  report['return_active_ids'] = await activeReminderIds(gateway);
  expect(report['return_pending_ids'], isEmpty);
  expect(report['return_active_ids'], isEmpty);
  report['lifecycle_events'] = observation.events;
  report['completed'] = true;
}
