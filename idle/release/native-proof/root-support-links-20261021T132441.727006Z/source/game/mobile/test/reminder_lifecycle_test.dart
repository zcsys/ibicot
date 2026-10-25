import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/reminder_lifecycle.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'notification_service_test.dart'
    show MemoryReminderStore, FixtureNotificationGateway;
import 'bootstrap_test.dart' show settleIo;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(tzdata.initializeTimeZones);
  final epoch = DateTime.utc(2026, 10, 16, 12);
  late FixtureNotificationGateway gateway;
  late NotificationService notifications;
  setUp(() async {
    gateway = FixtureNotificationGateway();
    notifications = NotificationService(
      gateway: gateway,
      store: MemoryReminderStore(),
      clock: () => epoch,
    );
    await notifications.initialize();
    await notifications.enableByPlayer();
    await notifications.updatePreferences(
      notifications.preferences.copyWith(quiet: false),
    );
  });
  tearDown(() => notifications.dispose());

  test(
    'reminders wait for a successful durable save and never mutate it',
    () async {
      final disk = Completer<void>();
      final game = GameController(
        startTicker: false,
        clock: () => epoch,
        onPersist: (_, _) => disk.future,
      );
      addTearDown(game.dispose);
      final lifecycle = ReminderLifecycle(game, notifications);
      final before = jsonEncode(game.state.toJson());
      final leaving = lifecycle.backgrounded();
      await Future<void>.delayed(Duration.zero);
      expect(gateway.delivered, isEmpty);
      disk.complete();
      await leaving;
      expect(gateway.delivered.length, 3);
      expect(jsonEncode(game.state.toJson()), before);
      expect(
        gateway.requests,
        1,
        reason: 'Only explicit opt-in requested permission.',
      );
    },
  );

  test(
    'return or controller replacement invalidates a delayed background save',
    () async {
      for (final replacement in [false, true]) {
        final disk = Completer<void>();
        final game = GameController(
          startTicker: false,
          clock: () => epoch,
          onPersist: (_, _) => disk.future,
        );
        final lifecycle = ReminderLifecycle(game, notifications);
        final leaving = lifecycle.backgrounded();
        await Future<void>.delayed(Duration.zero);
        if (replacement) {
          lifecycle.close();
        } else {
          await lifecycle.returned();
        }
        disk.complete();
        await leaving;
        expect(gateway.delivered, isEmpty);
        game.dispose();
      }
    },
  );

  test(
    'failed persistence and preview sessions never schedule a reminder',
    () async {
      for (final hasDisk in [true, false]) {
        final game = GameController(
          startTicker: false,
          clock: () => epoch,
          onPersist: hasDisk
              ? (_, _) async => throw const FileSystemException('fixture')
              : null,
        );
        final lifecycle = ReminderLifecycle(game, notifications);
        await lifecycle.backgrounded();
        expect(gateway.delivered, isEmpty);
        if (hasDisk) expect(game.saveError, isNotNull);
        game.dispose();
      }
    },
  );

  testWidgets(
    'actual app ignores inactive dialogs and cancels a true absence on return',
    (tester) async {
      final game = GameController(
        startTicker: false,
        clock: () => epoch,
        onPersist: (_, _) async {},
      );
      await tester.pumpWidget(
        TideglassApp(
          controller: game,
          notifications: notifications,
          initialPreferences: const ClientPreferences(reduceMotion: true),
        ),
      );
      await tester.pump();
      tester.binding.handleAppLifecycleStateChanged(
        AppLifecycleState.inactive,
      );
      await tester.pump();
      expect(gateway.delivered, isEmpty);
      tester.binding.handleAppLifecycleStateChanged(
        AppLifecycleState.paused,
      );
      await settleIo(tester, until: () => gateway.delivered.length == 3);
      expect(gateway.delivered.length, 3);
      tester.binding.handleAppLifecycleStateChanged(
        AppLifecycleState.resumed,
      );
      await settleIo(tester, until: () => gateway.delivered.isEmpty);
      expect(gateway.delivered, isEmpty);
      await tester.pumpWidget(const SizedBox());
      game.dispose();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'native bootstrap connects reminders without a launch permission prompt',
    (tester) async {
      final directory = Directory.systemTemp.createTempSync(
        'tideglass-reminder-host-',
      );
      final nativeFixture = FixtureNotificationGateway();
      final service = NotificationService(
        gateway: nativeFixture,
        store: MemoryReminderStore(),
      );
      await tester.pumpWidget(
        TideglassBootstrap(
          directory: directory,
          enableAudio: false,
          notifications: service,
        ),
      );
      await settleIo(
        tester,
        until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
      );
      final app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(app.notifications, same(service));
      expect(nativeFixture.initialized, 1);
      expect(nativeFixture.requests, 0);
      expect(service.preferences.enabled, isFalse);
      await tester.runAsync(app.controller.save);
      await tester.pumpWidget(const SizedBox());
      service.dispose();
      await tester.runAsync(() => directory.delete(recursive: true));
      expect(tester.takeException(), isNull);
    },
  );
}
