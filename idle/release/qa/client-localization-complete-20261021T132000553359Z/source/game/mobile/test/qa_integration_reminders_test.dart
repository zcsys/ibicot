import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/reminder_lifecycle.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:timezone/data/latest.dart' as data;
import 'package:timezone/timezone.dart' as tz;
import 'notification_service_test.dart'
    show FixtureNotificationGateway, MemoryReminderStore;

class ReviewedGateway extends FixtureNotificationGateway {
  final scheduleEntered = Completer<void>();
  int scheduleCalls = 0;
  bool failSecond = false;
  void Function()? beforeSchedule;
  @override
  Future<void> schedule(PlannedReminder value) async {
    beforeSchedule?.call();
    scheduleCalls++;
    if (!scheduleEntered.isCompleted) {
      scheduleEntered.complete();
    }
    if (failSecond && scheduleCalls == 2) {
      throw PlatformException(code: 'independent-partial-failure');
    }
    await super.schedule(value);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(data.initializeTimeZones);
  final epoch = DateTime.utc(2026, 10, 16, 12);
  late ReviewedGateway gateway;
  late MemoryReminderStore store;
  late NotificationService notices;
  var now = DateTime.utc(2026, 10, 16, 12);
  setUp(() async {
    now = epoch;
    gateway = ReviewedGateway();
    store = MemoryReminderStore();
    notices = NotificationService(
      gateway: gateway,
      store: store,
      clock: () => now,
    );
    await notices.initialize();
    await notices.enableByPlayer();
    await notices.updatePreferences(notices.preferences.copyWith(quiet: false));
  });
  tearDown(() => notices.dispose());
  test(
    'QA duplicate pauses followed by return cannot schedule a late saved snapshot',
    () async {
      final disk = Completer<void>();
      final saved = Completer<void>();
      final game = GameController(
        startTicker: false,
        clock: () => now,
        onPersist: (_, _) async {
          if (!saved.isCompleted) {
            saved.complete();
          }
          await disk.future;
        },
      );
      addTearDown(game.dispose);
      final lifecycle = ReminderLifecycle(game, notices);
      final before = jsonEncode(game.state.toJson());
      final first = lifecycle.backgrounded();
      final second = lifecycle.backgrounded();
      await saved.future;
      final returned = lifecycle.returned();
      disk.complete();
      await Future.wait([first, second, returned]);
      expect(gateway.delivered, isEmpty);
      expect(gateway.scheduleCalls, 0);
      expect(jsonEncode(game.state.toJson()), before);
      expect(gateway.requests, 1);
    },
  );
  test(
    'QA a paused app during real replay schedules only the final durable cursor',
    () async {
      final catalogue = await StoryCatalogue.load();
      DateTime? savedCursor;
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => now,
        onSessionPersist: (_, _, cursor) async {
          savedCursor = cursor;
        },
      );
      addTearDown(game.dispose);
      final lifecycle = ReminderLifecycle(game, notices);
      game.suspend();
      await game.save();
      now = epoch.add(const Duration(hours: 120));
      final replay = game.resumeWithProgress();
      expect(game.replaying, true);
      gateway.beforeSchedule = () {
        expect(game.replaying, false);
        expect(savedCursor, game.settledThrough);
      };
      final leaving = lifecycle.backgrounded();
      await Future.wait([replay, leaving]);
      expect(game.settledThrough, now);
      expect(gateway.delivered.length, 1);
      expect(gateway.delivered.single.kinds, [ReminderKind.storage]);
      expect(
        gateway.delivered.single.dueUtc,
        now.add(const Duration(hours: 24)),
      );
      final earned = game.state.lifetimeMicros;
      now = now.add(const Duration(minutes: 10));
      game.tick();
      expect(game.state.lifetimeMicros, earned);
    },
  );
  test(
    'QA duplicate returns during replay invalidate any older departure plan',
    () async {
      final catalogue = await StoryCatalogue.load();
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => now,
        onSessionPersist: (_, _, _) async {},
      );
      addTearDown(game.dispose);
      final lifecycle = ReminderLifecycle(game, notices);
      game.suspend();
      await game.save();
      now = epoch.add(const Duration(hours: 24));
      final replay = game.resumeWithProgress();
      final leaving = lifecycle.backgrounded();
      final one = lifecycle.returned();
      final two = lifecycle.returned();
      final returning = game.resumeWithProgress();
      await Future.wait([replay, leaving, one, two, returning]);
      expect(gateway.delivered, isEmpty);
      expect(gateway.scheduleCalls, 0);
      expect(game.replayError, isNull);
      expect(game.settledThrough, now);
    },
  );
  test(
    'QA opt-out behind an in-flight schedule clears native requests and persists refusal',
    () async {
      gateway.scheduleGate = Completer<void>();
      final state = GameState.initial();
      final before = jsonEncode(state.toJson());
      final scheduling = notices.scheduleForAbsence(
        state: state,
        settledThrough: epoch,
      );
      await gateway.scheduleEntered.future;
      final disabling = notices.updatePreferences(
        notices.preferences.copyWith(enabled: false),
      );
      gateway.scheduleGate!.complete();
      await Future.wait([scheduling, disabling]);
      expect(gateway.delivered, isEmpty);
      expect(notices.planned, isEmpty);
      expect(store.value.enabled, false);
      expect(notices.preferences.enabled, false);
      expect(gateway.requests, 1);
      expect(jsonEncode(state.toJson()), before);
    },
  );
  test(
    'QA a second native scheduling failure cancels the already-scheduled first notice',
    () async {
      gateway.failSecond = true;
      await notices.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: epoch,
      );
      expect(gateway.delivered, isEmpty);
      expect(notices.planned, isEmpty);
      expect(notices.warningKey, 'serviceUnavailable');
      gateway.failSecond = false;
      await notices.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: epoch,
      );
      expect(gateway.delivered.length, 3);
      expect(notices.warningKey, isNull);
    },
  );
  test(
    'QA time-zone replacement cancels prior IDs and uses the new quiet-hour zone',
    () async {
      await notices.updatePreferences(
        notices.preferences.copyWith(quiet: true),
      );
      gateway.zone = 'Europe/Istanbul';
      await notices.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: epoch,
      );
      expect(
        gateway.delivered.every((r) => r.zoneName == 'Europe/Istanbul'),
        true,
      );
      gateway.zone = 'America/New_York';
      await notices.onReturn();
      expect(gateway.delivered, isEmpty);
      await notices.scheduleForAbsence(
        state: GameState.initial(),
        settledThrough: epoch,
      );
      expect(
        gateway.delivered.every((r) => r.zoneName == 'America/New_York'),
        true,
      );
      expect(
        gateway.delivered.map((r) => r.id).toSet().length,
        gateway.delivered.length,
      );
      expect(gateway.requests, 1);
    },
  );
  test(
    'QA closing a controller preserves a legitimate committed absence plan',
    () async {
      final game = GameController(
        startTicker: false,
        clock: () => now,
        onPersist: (_, _) async {},
      );
      final lifecycle = ReminderLifecycle(game, notices);
      await lifecycle.backgrounded();
      final plan = gateway.delivered.map((r) => r.dueUtc).toList();
      lifecycle.close();
      game.dispose();
      expect(gateway.delivered.map((r) => r.dueUtc).toList(), plan);
      expect(plan.length, 3);
    },
  );
  test(
    'QA 384 multi-zone departure cases preserve readiness quiet windows and the strict horizon',
    () {
      const planner = ReminderPlanner();
      const prefs = ReminderPreferences(
        enabled: true,
        quietStart: 75,
        quietEnd: 135,
      );
      final state = GameState.initial();
      final before = jsonEncode(state.toJson());
      var cases = 0;
      for (final zone in [
        'UTC',
        'Europe/Istanbul',
        'America/New_York',
        'Australia/Lord_Howe',
      ]) {
        for (final day in [
          DateTime.utc(2026, 3, 8),
          DateTime.utc(2026, 4, 5),
          DateTime.utc(2026, 10, 4),
          DateTime.utc(2026, 11, 1),
        ]) {
          for (var hour = 0; hour < 24; hour++) {
            final boundary = day.add(Duration(hours: hour));
            final location = reminderLocation(zone);
            final result = planner.plan(
              state: state,
              settledThrough: boundary,
              nowUtc: boundary,
              preferences: prefs,
              location: location,
            );
            cases++;
            expect(result.length, lessThanOrEqualTo(3));
            expect(result.map((r) => r.id).toSet().length, result.length);
            for (final reminder in result) {
              final local = tz.TZDateTime.from(reminder.dueUtc, location);
              final minute = local.hour * 60 + local.minute;
              expect(minute < 75 || minute >= 135, true);
              expect(
                reminder.dueUtc.isBefore(
                  boundary.add(const Duration(hours: 72)),
                ),
                true,
              );
              for (final kind in reminder.kinds) {
                final hours = switch (kind) {
                  ReminderKind.focus => 2,
                  ReminderKind.survey => 8,
                  ReminderKind.storage => 24,
                };
                expect(
                  reminder.dueUtc.isBefore(
                    boundary.add(Duration(hours: hours)),
                  ),
                  false,
                );
              }
            }
          }
        }
      }
      expect(cases, 384);
      expect(jsonEncode(state.toJson()), before);
    },
  );
}
