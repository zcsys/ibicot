import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/notification_copy.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/notification_settings.dart';
import 'package:tideglass/palette.dart';
import 'notification_service_test.dart'
    show FixtureNotificationGateway, MemoryReminderStore;

void main() {
  Future<void> show(
    WidgetTester tester,
    NotificationService service, {
    bool pseudo = false,
  }) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: const TextScaler.linear(2)),
          child: child!,
        ),
        home: Scaffold(
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: NotificationSettings(
                service: service,
                copy: NotificationCopy(pseudo: pseudo),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, String key) async {
    final target = find.byKey(ValueKey(key));
    await tester.ensureVisible(target);
    await tester.tap(target);
    await tester.pumpAndSettle();
  }

  testWidgets(
    'large pseudo text explicit optin controls work without build-time permission',
    (tester) async {
      final gateway = FixtureNotificationGateway();
      final store = MemoryReminderStore();
      final service = NotificationService(gateway: gateway, store: store);
      addTearDown(service.dispose);
      await service.initialize();
      await show(tester, service, pseudo: true);
      expect(gateway.requests, 0);
      await tap(tester, 'reminder-enable');
      expect(gateway.requests, 1);
      expect(store.value.enabled, isTrue);
      await tap(tester, 'reminder-focus');
      expect(store.value.focus, isFalse);
      await tap(tester, 'reminder-survey');
      expect(store.value.survey, isFalse);
      await tap(tester, 'reminder-storage');
      expect(store.value.storage, isFalse);
      await tap(tester, 'reminder-quiet');
      expect(store.value.quiet, isFalse);
      await tap(tester, 'reminder-check-permission');
      expect(gateway.requests, 1);
      await tap(tester, 'reminder-device-settings');
      expect(gateway.opened, 1);
      await tap(tester, 'reminder-enable');
      expect(store.value.enabled, isFalse);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('denial remains nonblocking and preferences failure is visible', (
    tester,
  ) async {
    final gateway = FixtureNotificationGateway()
      ..current = ReminderPermission.denied;
    final store = MemoryReminderStore();
    final service = NotificationService(gateway: gateway, store: store);
    addTearDown(service.dispose);
    await service.initialize();
    await show(tester, service);
    await tap(tester, 'reminder-enable');
    expect(service.preferences.enabled, isFalse);
    expect(
      find.textContaining('Device permission is not allowed'),
      findsOneWidget,
    );
    store.failSave = true;
    await tap(tester, 'reminder-focus');
    expect(find.byKey(const ValueKey('reminder-warning')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('quiet hours can be edited with large-text time input', (
    tester,
  ) async {
    final store = MemoryReminderStore();
    final service = NotificationService(
      gateway: FixtureNotificationGateway(),
      store: store,
    );
    addTearDown(service.dispose);
    await service.initialize();
    await show(tester, service, pseudo: true);
    await tap(tester, 'reminder-quiet-start');
    await tester.enterText(
      find.byKey(const ValueKey('reminder-hour-input')),
      '21',
    );
    await tester.enterText(
      find.byKey(const ValueKey('reminder-minute-input')),
      '00',
    );
    await tap(tester, 'reminder-save-time');
    expect(store.value.quietStart, 1260);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'invalid or equal quiet hours are not saved and cancel is harmless',
    (tester) async {
      final store = MemoryReminderStore();
      final service = NotificationService(
        gateway: FixtureNotificationGateway(),
        store: store,
      );
      addTearDown(service.dispose);
      await service.initialize();
      await show(tester, service);
      await tap(tester, 'reminder-quiet-start');
      await tester.enterText(
        find.byKey(const ValueKey('reminder-hour-input')),
        '24',
      );
      await tap(tester, 'reminder-save-time');
      expect(find.text('Enter an hour from 0 to 23.'), findsOneWidget);
      expect(store.value.quietStart, 1320);
      await tap(tester, 'reminder-cancel-time');
      await tap(tester, 'reminder-quiet-start');
      await tester.enterText(
        find.byKey(const ValueKey('reminder-hour-input')),
        '08',
      );
      await tester.enterText(
        find.byKey(const ValueKey('reminder-minute-input')),
        '00',
      );
      await tap(tester, 'reminder-save-time');
      expect(store.value.quietStart, 1320);
      expect(find.byKey(const ValueKey('reminder-warning')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  test('all new copy expands deterministically and templates resolve', () {
    const normal = NotificationCopy();
    const pseudo = NotificationCopy(pseudo: true);
    for (final key in NotificationCopy.english.keys) {
      expect(pseudo.text(key).length, greaterThan(normal.text(key).length));
    }
    expect(
      normal.text('planned', {'count': 3}),
      '3 reminders currently planned.',
    );
    expect(
      normal.text('zone', {'zone': 'Europe/Istanbul'}),
      contains('Europe/Istanbul'),
    );
  });
}
