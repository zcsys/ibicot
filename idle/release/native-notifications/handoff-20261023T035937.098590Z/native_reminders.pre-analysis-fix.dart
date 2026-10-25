// Simulator/emulator qualification only. Real plugin and OS APIs; synthetic
// isolated gameplay state. No permission-channel mocks or artificial clocks.
import 'dart:async';
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
const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked'};
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
  WidgetTester tester,
  bool Function() ready, {
  required String reason,
  int seconds = 120,
}) async {
  final watch = Stopwatch()..start();
  while (!ready() && watch.elapsed < Duration(seconds: seconds)) {
    await Future<void>.delayed(const Duration(milliseconds: 100));
    await tester.pump();
  }
  expect(ready(), isTrue, reason: reason);
}

class NativeLifecycleObservation extends WidgetsBindingObserver {
  final events = <Map<String, dynamic>>[];
  Future<void> Function(AppLifecycleState)? onChange;
  Object? error;
  Future<void> tail = Future.value();
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    events.add({'state': state.name, 'utc_ms': utcMs()});
    final callback = onChange;
    if (callback != null) {
      tail = tail.then((_) => callback(state)).catchError((Object failure) {
        error = failure;
      });
    }
  }
}

void main() {
  binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('real OS reminder qualification: $scenario', (tester) async {
    expect(Platform.isIOS || Platform.isAndroid, isTrue);
    expect(scenarios, contains(scenario));
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
          reason:
              'This scenario requires actual OS approval; inability is unqualified.',
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
        lifecycle = ReminderLifecycle(game!, service);
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
          await lifecycle!.backgrounded();
          await recordPlan(service, gateway, repository, game!);
          final due = tz.TZDateTime.from(
            service.planned.single.dueUtc,
            location,
          );
          expect(due.hour * 60 + due.minute, end);
          report['quiet_due_local_minute'] = due.hour * 60 + due.minute;
          await lifecycle!.returned();
          expect(await pending(gateway), isEmpty);
          report['return_pending_ids'] = await pending(gateway);
        } else if (scenario == 'revoked') {
          report['background_call_utc_ms'] = utcMs();
          await lifecycle!.backgrounded();
          await recordPlan(service, gateway, repository, game!);
          final baseline = observation.events.length;
          action('revoke_in_os_settings_then_return_via_app_icon');
          await service.openDeviceSettings();
          await until(
            tester,
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
          await lifecycle!.returned();
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
          observation.onChange = (state) async {
            if (state == AppLifecycleState.paused && !scheduled) {
              report['background_call_utc_ms'] = utcMs();
              await lifecycle!.backgrounded();
              await recordPlan(service, gateway, repository, game!);
              earliestReturn =
                  service.planned.single.dueUtc.millisecondsSinceEpoch;
              report['scheduled_elapsed_ms'] = watch.elapsedMilliseconds;
              scheduled = true;
              action('wait_until_due_then_return_via_app_icon', {
                'not_before_utc_ms': earliestReturn,
              });
            } else if (state == AppLifecycleState.resumed &&
                scheduled &&
                !returned) {
              report['returned_utc_ms'] = utcMs();
              report['returned_elapsed_ms'] = watch.elapsedMilliseconds;
              // Observe delivered OS records before production cancellation.
              final delivered = await gateway.plugin.getActiveNotifications();
              report['delivered_records'] = [
                for (final item in delivered)
                  if (ReminderPlanner.ids.contains(item.id))
                    {'id': item.id, 'title': item.title, 'body': item.body},
              ];
              expect(utcMs(), greaterThanOrEqualTo(earliestReturn));
              expect(
                report['delivered_records'],
                isNotEmpty,
                reason: 'A scheduled request alone is not actual delivery.',
              );
              expect(
                (report['delivered_records'] as List).any(
                  (dynamic row) =>
                      row['id'] == 77101 &&
                      row['body'] == const NotificationCopy().text('focusBody'),
                ),
                isTrue,
              );
              await lifecycle!.returned();
              expect(await pending(gateway), isEmpty);
              expect(
                (await gateway.plugin.getActiveNotifications()).where(
                  (x) => ReminderPlanner.ids.contains(x.id),
                ),
                isEmpty,
              );
              report['return_pending_ids'] = await pending(gateway);
              report['return_active_ids'] = <int>[];
              returned = true;
            }
          };
          action('background_app_now_using_os_home');
          await until(
            tester,
            () => returned || observation.error != null,
            reason:
                'Real production-minimum elapsed delivery and native return required.',
            seconds: 720,
          );
          await observation.tail;
          if (observation.error != null) throw observation.error!;
          expect(scheduled && returned, isTrue);
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

Future<void> recordPlan(
  NotificationService service,
  NativeNotificationGateway gateway,
  SaveRepository repository,
  GameController game,
) async {
  expect(service.warningKey, isNull);
  expect(service.planned.length, 1);
  expect(await pending(gateway), [77101]);
  final plan = service.planned.single;
  final saved = (await repository.load()).snapshot!;
  expect(saved.payload, game.state.toJson());
  expect(saved.settledThrough, game.settledThrough.toUtc());
  final now = utcMs();
  expect(plan.dueUtc.isAfter(DateTime.now().toUtc()), isTrue);
  report['plan'] = {
    'background_call_utc_ms': report['background_call_utc_ms'],
    'scheduled_observed_utc_ms': now,
    'due_utc_ms': plan.dueUtc.millisecondsSinceEpoch,
    'settled_through_utc_ms': game.settledThrough
        .toUtc()
        .millisecondsSinceEpoch,
    'zone': plan.zoneName,
    'ids': await pending(gateway),
    'kinds': plan.kinds.map((x) => x.name).toList(),
    'body': plan.body(const NotificationCopy()),
    'saved_payload_sha256': sha256
        .convert(utf8.encode(jsonEncode(saved.payload)))
        .toString(),
    'saved_snapshot_id': saved.saveId,
    'production_lifecycle': true,
  };
}
