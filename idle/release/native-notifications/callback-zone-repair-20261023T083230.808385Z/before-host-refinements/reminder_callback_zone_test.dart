// Synthetic host checks for test-observation mechanics only, never OS delivery.
import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/notification_copy.dart';

import '../integration_test/native_reminders_test.dart' as capture;

Map<String, dynamic> planObservation() => {
  'background_call_utc_ms': 1000,
  'warning_key': null,
  'planned': [
    {
      'id': 77101,
      'due_utc_ms': 301000,
      'due_utc_micros': 301000000,
      'zone': 'UTC',
      'kinds': ['focus'],
      'body': const NotificationCopy().text('focusBody'),
    },
  ],
  'pending_ids': [77101],
  'saved_payload': {'counts': [1, 0, 0, 0, 0]},
  'game_payload': {'counts': [1, 0, 0, 0, 0]},
  'saved_settled_through_utc_micros': 1000000,
  'game_settled_through_utc_micros': 1000000,
  'saved_snapshot_id': 'synthetic-host-snapshot',
  'observed_utc_ms': 1001,
  'observed_utc_micros': 1001000,
};

Map<String, dynamic> deliveryObservation() => {
  'delivery_observed_utc_ms': 301000,
  'delivered_records': [
    {'id': 77101, 'body': const NotificationCopy().text('focusBody')},
  ],
  'return_pending_ids': <int>[],
  'return_active_ids': <int>[],
};

void throwCallbackFailure() => throw StateError('synthetic callback failure');

void main() {
  test('root-zone lifecycle callbacks collect without test-zone assertions', () async {
    final observer = capture.NativeLifecycleObservation();
    final observed = <String>[];
    Zone? callbackZone;
    observer.onChange = (state) async {
      callbackZone = Zone.current;
      observed.add(state.name);
    };
    Zone.root.run(() {
      observer.didChangeAppLifecycleState(AppLifecycleState.paused);
      observer.didChangeAppLifecycleState(AppLifecycleState.resumed);
    });
    await observer.tail;
    expect(callbackZone, same(Zone.root));
    expect(observed, ['paused', 'resumed']);
    expect(observer.events.map((x) => x['state']), ['paused', 'resumed']);
    expect(observer.error, isNull);
    expect(observer.failures, isEmpty);
  });

  test('callback failures retain original stack and rethrow in test zone', () async {
    final observer = capture.NativeLifecycleObservation();
    observer.onChange = (_) async => throwCallbackFailure();
    Zone.root.run(() => observer.didChangeAppLifecycleState(AppLifecycleState.paused));
    await observer.tail;
    expect(observer.error, isA<StateError>());
    expect(observer.errorStack.toString(), contains('throwCallbackFailure'));
    expect(observer.failures.single['state'], 'paused');
    expect(observer.failures.single['error_type'], 'StateError');
    expect(observer.failures.single['stack'], contains('throwCallbackFailure'));
    Object? caught;
    StackTrace? stack;
    try {
      capture.rethrowLifecycleFailure(observer);
    } catch (error, trace) {
      caught = error;
      stack = trace;
    }
    expect(caught, same(observer.error));
    expect(stack.toString(), observer.errorStack.toString());
  });

  test('native observation polling does not need a Flutter frame', () async {
    var observed = false;
    final timer = Timer(const Duration(milliseconds: 5), () => observed = true);
    addTearDown(timer.cancel);
    await capture.until(() => observed, reason: 'actual host timer', seconds: 1);
    expect(observed, isTrue);
  });

  test('unobserved native condition still fails its finite bound', () async {
    await expectLater(
      capture.until(() => false, reason: 'deliberately absent', seconds: 0),
      throwsA(isA<TestFailure>()),
    );
  });

  test('captured scheduling snapshot validates and retains report contract', () {
    final observation = planObservation();
    final plan = capture.validateObservedReminderPlan(observation);
    expect(plan['ids'], [77101]);
    expect(plan['due_utc_ms'], 301000);
    expect(plan['scheduled_observed_utc_ms'], 1001);
    expect(plan['settled_through_utc_ms'], 1000);
    expect(plan['saved_snapshot_id'], 'synthetic-host-snapshot');
    expect(plan['saved_payload_sha256'], matches(RegExp(r'^[a-f0-9]{64}$')));
    expect(plan['body'], const NotificationCopy().text('focusBody'));
  });

  final planFailures = <String, void Function(Map<String, dynamic>)>{
    'warning': (x) => x['warning_key'] = 'synthetic.warning',
    'missing plan': (x) => x['planned'] = [],
    'multiple plans': (x) => (x['planned'] as List).add((x['planned'] as List).single),
    'missing pending request': (x) => x['pending_ids'] = [],
    'wrong pending request': (x) => x['pending_ids'] = [77102],
    'missing committed save': (x) => x['saved_snapshot_id'] = null,
    'changed committed payload': (x) => x['saved_payload'] = {'counts': [2, 0, 0, 0, 0]},
    'changed committed boundary': (x) => x['saved_settled_through_utc_micros'] = 999999,
    'due at observation': (x) => (x['planned'] as List).single['due_utc_micros'] = x['observed_utc_micros'],
    'due before observation': (x) => (x['planned'] as List).single['due_utc_micros'] = 1,
  };
  for (final entry in planFailures.entries) {
    test('observed plan still rejects ${entry.key}', () {
      final observation = planObservation();
      entry.value(observation);
      expect(() => capture.validateObservedReminderPlan(observation), throwsA(isA<TestFailure>()));
    });
  }

  test('actual delivery and post-return observations validate', () {
    capture.validateObservedReminderDelivery(deliveryObservation(), 301000);
  });
  final deliveryFailures = <String, void Function(Map<String, dynamic>)>{
    'early delivery observation': (x) => x['delivery_observed_utc_ms'] = 300999,
    'scheduled without delivered record': (x) => x['delivered_records'] = [],
    'wrong delivered identifier': (x) => (x['delivered_records'] as List).single['id'] = 77102,
    'wrong delivered body': (x) => (x['delivered_records'] as List).single['body'] = 'wrong',
    'remaining pending request': (x) => x['return_pending_ids'] = [77101],
    'remaining delivered notification': (x) => x['return_active_ids'] = [77101],
  };
  for (final entry in deliveryFailures.entries) {
    test('observed delivery still rejects ${entry.key}', () {
      final observation = deliveryObservation();
      entry.value(observation);
      expect(() => capture.validateObservedReminderDelivery(observation, 301000), throwsA(isA<TestFailure>()));
    });
  }
}
