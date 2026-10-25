import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/notification_copy.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:timezone/data/latest.dart' as data;
import 'package:timezone/timezone.dart' as tz;

class MemoryReminderStore implements NotificationPreferenceStore {
  ReminderPreferences value = const ReminderPreferences();
  bool failSave = false, failLoad = false;
  @override
  Future<ReminderPreferences> load() async {
    if (failLoad) throw const FormatException('fixture');
    return value;
  }

  @override
  Future<void> save(ReminderPreferences value) async {
    if (failSave) throw const FileSystemException('fixture');
    this.value = value;
  }
}

class FixtureNotificationGateway implements NotificationGateway {
  int requests = 0, cancellations = 0, initialized = 0, opened = 0;
  ReminderPermission current = ReminderPermission.allowed;
  String zone = 'UTC';
  bool failSchedule = false;
  final delivered = <PlannedReminder>[];
  Completer<void>? scheduleGate;
  @override
  Future<void> initialize() async {
    initialized++;
  }

  @override
  Future<ReminderPermission> permission() async => current;
  @override
  Future<ReminderPermission> requestPermission() async {
    requests++;
    return current;
  }

  @override
  Future<void> cancelReminders() async {
    cancellations++;
    delivered.clear();
  }

  @override
  Future<void> schedule(PlannedReminder value) async {
    if (scheduleGate != null) await scheduleGate!.future;
    if (failSchedule) throw PlatformException(code: 'fixture');
    delivered.add(value);
  }

  @override
  Future<String> timeZone() async => zone;
  @override
  Future<void> openSettings() async {
    opened++;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(data.initializeTimeZones);
  const planner = ReminderPlanner();
  final baseline = DateTime.utc(2026, 10, 16, 12);
  List<PlannedReminder> plan({
    GameState? state,
    ReminderPreferences prefs = const ReminderPreferences(
      enabled: true,
      quiet: false,
    ),
    DateTime? boundary,
    DateTime? now,
    String zone = 'UTC',
  }) => planner.plan(
    state: state ?? GameState.initial(),
    settledThrough: boundary ?? baseline,
    nowUtc: now ?? boundary ?? baseline,
    preferences: prefs,
    location: reminderLocation(zone),
  );
  test('default off and exact 2h 8h 24h future transitions are readonly', () {
    final state = GameState.initial();
    final before = jsonEncode(state.toJson());
    expect(plan(prefs: const ReminderPreferences()), isEmpty);
    final result = plan(state: state);
    expect(result.map((r) => r.dueUtc.difference(baseline)), [
      const Duration(hours: 2),
      const Duration(hours: 8),
      const Duration(hours: 24),
    ]);
    expect(result.map((r) => r.kinds.single), ReminderKind.values);
    expect(jsonEncode(state.toJson()), before);
    final advanced = const TideglassEngine()
        .advance(state, const Duration(hours: 2), offline: true)
        .state;
    expect(advanced.focusCharges, state.focusCharges + 1);
    expect(
      result.last.body(const NotificationCopy()),
      contains('until 72 hours away'),
    );
  });
  test(
    'partial phases capped stores and disabled categories are respected',
    () {
      final phased = GameState(
        focusPhaseMicros: BigInt.from(3600000000),
        surveyPhaseMicros: BigInt.from(7200000000),
      );
      expect(plan(state: phased).map((r) => r.dueUtc.difference(baseline)), [
        const Duration(hours: 1),
        const Duration(hours: 6),
        const Duration(hours: 24),
      ]);
      expect(
        plan(
          state: GameState(focusCharges: 12, completedSurveys: 3),
        ).single.kinds,
        [ReminderKind.storage],
      );
      expect(
        plan(
          prefs: const ReminderPreferences(
            enabled: true,
            focus: false,
            survey: false,
            storage: false,
          ),
        ),
        isEmpty,
      );
    },
  );
  test(
    'overnight quiet hours defer and coalesce while preserving future truth',
    () {
      final at = DateTime.utc(2026, 10, 16, 20);
      final result = plan(
        boundary: at,
        prefs: const ReminderPreferences(enabled: true),
      );
      expect(result.length, 2);
      expect(result.first.dueUtc, DateTime.utc(2026, 10, 17, 8));
      expect(result.first.kinds, [ReminderKind.focus, ReminderKind.survey]);
      expect(result.last.dueUtc, DateTime.utc(2026, 10, 17, 20));
    },
  );
  test(
    'DST fall repeated hour and spring skipped hour exit quiet time correctly',
    () {
      final zone = tz.getLocation('America/New_York');
      final fall = planner.afterQuietHours(
        DateTime.utc(2026, 11, 1, 5, 30),
        const ReminderPreferences(quietStart: 60, quietEnd: 120),
        zone,
      );
      expect(fall, DateTime.utc(2026, 11, 1, 7));
      final spring = planner.afterQuietHours(
        DateTime.utc(2026, 3, 8, 6, 30),
        const ReminderPreferences(quietStart: 60, quietEnd: 180),
        zone,
      );
      expect(spring, DateTime.utc(2026, 3, 8, 7));
    },
  );
  test(
    'clock rollback stale snapshots near readiness and quiet boundaries are bounded',
    () {
      expect(plan(now: baseline.subtract(const Duration(seconds: 1))), isEmpty);
      expect(plan(now: baseline.add(const Duration(hours: 73))), isEmpty);
      final almost = GameState(focusPhaseMicros: BigInt.from(7199999999));
      expect(
        plan(state: almost).first.dueUtc,
        baseline.add(const Duration(minutes: 5)),
      );
      for (var hour = 0; hour < 24; hour++) {
        final result = plan(
          boundary: DateTime.utc(2026, 10, 16, hour),
          prefs: const ReminderPreferences(enabled: true),
        );
        expect(result.length, lessThanOrEqualTo(3));
        for (final item in result) {
          expect(item.dueUtc.hour, inInclusiveRange(8, 21));
        }
      }
      expect(
        () => plan(
          prefs: const ReminderPreferences(
            enabled: true,
            quietStart: 0,
            quietEnd: 0,
          ),
        ),
        throwsFormatException,
      );
    },
  );
  test(
    'preferences are separate bounded strict atomic files; corruption remains',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'tideglass-reminders-',
      );
      addTearDown(() => directory.delete(recursive: true));
      final file = File('${directory.path}/notification_preferences.json');
      final store = FileNotificationPreferences(file);
      expect((await store.load()).enabled, isFalse);
      await store.save(
        const ReminderPreferences(enabled: true, quietStart: 1260),
      );
      expect((await store.load()).quietStart, 1260);
      expect(await File('${file.path}.new').exists(), isFalse);
      final json = (jsonDecode(await file.readAsString()) as Map);
      expect(json.keys, isNot(contains('wallet')));
      await file.writeAsString('x' * 4097);
      await expectLater(store.load(), throwsFormatException);
      expect(await file.length(), 4097);
      expect(
        () => ReminderPreferences.fromJson({'version': 1}),
        throwsFormatException,
      );
    },
  );
  test(
    'startup never prompts; optin schedules only on absence and return cancels',
    () async {
      final gateway = FixtureNotificationGateway();
      final store = MemoryReminderStore();
      final service = NotificationService(
        gateway: gateway,
        store: store,
        clock: () => baseline,
      );
      addTearDown(service.dispose);
      await service.initialize();
      expect(gateway.requests, 0);
      expect(service.preferences.enabled, isFalse);
      await service.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: baseline,
      );
      expect(gateway.delivered, isEmpty);
      await service.onReturn();
      await service.enableByPlayer();
      expect(gateway.requests, 1);
      expect(gateway.delivered, isEmpty);
      await service.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: baseline,
      );
      expect(service.planned.length, 3);
      await service.onReturn();
      expect(gateway.delivered, isEmpty);
      expect(service.planned, isEmpty);
      expect(gateway.requests, 1);
    },
  );
  test(
    'denial revocation and clock/zone changes never request another permission or mutate game',
    () async {
      final gateway = FixtureNotificationGateway()
        ..current = ReminderPermission.denied;
      final store = MemoryReminderStore();
      final service = NotificationService(
        gateway: gateway,
        store: store,
        clock: () => baseline,
      );
      addTearDown(service.dispose);
      await service.initialize();
      await service.enableByPlayer();
      expect(service.preferences.enabled, isFalse);
      gateway.current = ReminderPermission.allowed;
      await service.enableByPlayer();
      final state = GameState.initial();
      final before = jsonEncode(state.toJson());
      await service.scheduleForAbsence(state: state, settledThrough: baseline);
      expect(gateway.delivered, isNotEmpty);
      gateway.current = ReminderPermission.denied;
      await service.onReturn();
      expect(gateway.delivered, isEmpty);
      await service.scheduleForAbsence(state: state, settledThrough: baseline);
      expect(service.planned, isEmpty);
      gateway.current = ReminderPermission.allowed;
      gateway.zone = 'bad/unknown';
      await service.scheduleForAbsence(state: state, settledThrough: baseline);
      expect(service.warningKey, 'zoneUnavailable');
      expect(service.planned, isEmpty);
      gateway.zone = 'Europe/Istanbul';
      await service.onClockChanged();
      expect(gateway.delivered, isEmpty);
      expect(service.warningKey, 'clockChanged');
      await service.scheduleForAbsence(state: state, settledThrough: baseline);
      expect(service.warningKey, isNull);
      expect(service.planned, isNotEmpty);
      expect(gateway.requests, 2);
      expect(jsonEncode(state.toJson()), before);
    },
  );
  test(
    'preference edits replan absence; failed save or schedule cancels the entire plan',
    () async {
      final gateway = FixtureNotificationGateway();
      final store = MemoryReminderStore();
      final service = NotificationService(
        gateway: gateway,
        store: store,
        clock: () => baseline,
      );
      addTearDown(service.dispose);
      await service.initialize();
      await service.enableByPlayer();
      await service.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: baseline,
      );
      await service.updatePreferences(
        service.preferences.copyWith(focus: false),
      );
      expect(service.planned.length, 2);
      gateway.failSchedule = true;
      await service.updatePreferences(
        service.preferences.copyWith(survey: false),
      );
      expect(gateway.delivered, isEmpty);
      gateway.failSchedule = false;
      store.failSave = true;
      await service.updatePreferences(
        service.preferences.copyWith(enabled: false),
      );
      expect(service.preferences.enabled, isFalse);
      expect(service.warningKey, 'preferencesUnsaved');
      expect(gateway.delivered, isEmpty);
    },
  );
  test(
    'serialized schedule followed by return cannot leave late pending notices',
    () async {
      final gateway = FixtureNotificationGateway();
      final service = NotificationService(
        gateway: gateway,
        store: MemoryReminderStore(),
        clock: () => baseline,
      );
      addTearDown(service.dispose);
      await service.initialize();
      await service.enableByPlayer();
      gateway.scheduleGate = Completer<void>();
      final pending = service.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: baseline,
      );
      await Future<void>.delayed(Duration.zero);
      final returning = service.onReturn();
      gateway.scheduleGate!.complete();
      await pending;
      await returning;
      expect(gateway.delivered, isEmpty);
      expect(service.planned, isEmpty);
    },
  );
  test(
    'Android adapter sends silent inexact one-shot requests and only3owned cancellations',
    () async {
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      AndroidFlutterLocalNotificationsPlugin.registerWith();
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      final calls = <MethodCall>[];
      const channel = MethodChannel(
        'dexterous.com/flutter/local_notifications',
      );
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            calls.add(call);
            return call.method == 'initialize' ||
                    call.method == 'areNotificationsEnabled' ||
                    call.method == 'requestNotificationsPermission'
                ? true
                : null;
          });
      addTearDown(
        () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null),
      );
      final gateway = NativeNotificationGateway(
        platform: TargetPlatform.android,
      );
      await gateway.initialize();
      expect(
        calls.any((c) => c.method == 'requestNotificationsPermission'),
        isFalse,
      );
      await gateway.requestPermission();
      await gateway.cancelReminders();
      final reminder = PlannedReminder(
        id: 77101,
        dueUtc: DateTime.now().toUtc().add(const Duration(hours: 2)),
        zoneName: 'UTC',
        kinds: [ReminderKind.focus],
      );
      await gateway.schedule(reminder);
      final schedule = calls.last.arguments as Map;
      final platform = schedule['platformSpecifics'] as Map;
      expect(platform['scheduleMode'], 'inexactAllowWhileIdle');
      expect(platform['playSound'], isFalse);
      expect(platform['enableVibration'], isFalse);
      expect(schedule['matchDateTimeComponents'], isNull);
      expect(schedule['payload'], '');
      expect(
        calls
            .where((c) => c.method == 'cancel')
            .map((c) => (c.arguments as Map)['id']),
        ReminderPlanner.ids,
      );
    },
  );
  test(
    'iOS adapter initialization requests no permissions and optin asks alert only',
    () async {
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      IOSFlutterLocalNotificationsPlugin.registerWith();
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      final calls = <MethodCall>[];
      const channel = MethodChannel(
        'dexterous.com/flutter/local_notifications',
      );
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            calls.add(call);
            return call.method == 'checkPermissions'
                ? {'isEnabled': true, 'isAlertEnabled': true}
                : true;
          });
      addTearDown(
        () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null),
      );
      final gateway = NativeNotificationGateway(platform: TargetPlatform.iOS);
      await gateway.initialize();
      final init = calls.single.arguments as Map;
      expect(init['requestAlertPermission'], isFalse);
      expect(init['requestBadgePermission'], isFalse);
      expect(init['requestSoundPermission'], isFalse);
      await gateway.requestPermission();
      final request =
          calls.firstWhere((c) => c.method == 'requestPermissions').arguments
              as Map;
      expect(request['alert'], isTrue);
      expect(request['sound'], isFalse);
      expect(request['badge'], isFalse);
    },
  );
}
