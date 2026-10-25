import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/game_telemetry.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'game_telemetry_test.dart' show TelemetryClient;
import 'native_services_test.dart' show MemoryCredentials;

class DelayedConsentClient extends TelemetryClient {
  bool holdReads = false, holdDelivery = false;
  final reads = <Completer<Map<String, dynamic>>>[];
  Completer<void>? delivery;
  final deliveries = <Map<String, dynamic>>[];
  @override
  Future<Map<String, dynamic>> readTelemetryConsent() {
    if (!holdReads) return super.readTelemetryConsent();
    final pending = Completer<Map<String, dynamic>>();
    reads.add(pending);
    return pending.future;
  }

  @override
  Future<Map<String, dynamic>> sendTelemetry({
    required int consentRevision,
    required List<Map<String, dynamic>> events,
  }) async {
    final captured = session!.accountId;
    final ids = events.map((e) => e['id']).toList();
    deliveries.add({
      'account': captured,
      'ids': ids,
      'revision': consentRevision,
      'events': jsonDecode(jsonEncode(events)),
    });
    if (holdDelivery) {
      delivery ??= Completer<void>();
      await delivery!.future;
      throw const ServiceException('unknown_delivery_outcome');
    }
    return super.sendTelemetry(
      consentRevision: consentRevision,
      events: events,
    );
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late DelayedConsentClient client;
  late NativeServicesManager manager;
  late MemoryCredentials credentials;
  late GameController game;
  GameTelemetry? telemetry;
  setUp(() async {
    client = DelayedConsentClient();
    credentials = MemoryCredentials();
    manager = NativeServicesManager(client: client, credentials: credentials);
    await manager.createAccount(cloudConsent: true);
    game = GameController(
      startTicker: false,
      clock: () => DateTime.utc(2026, 10, 19),
      initialState: GameState(
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
        walletMicros: TideglassEngine.firstPrestigeMicros,
      ),
      onPersist: (_, _) async {},
    );
  });
  tearDown(() {
    telemetry?.dispose();
    telemetry = null;
    game.dispose();
    manager.dispose();
    client.close();
  });
  GameTelemetry observe() => telemetry = GameTelemetry(
    game: game,
    services: manager,
    platform: 'test',
    clock: () => DateTime.utc(2026, 10, 19),
  );

  test(
    'late older consent read must not revive a newer confirmed withdrawal',
    () async {
      await manager.setTelemetryConsent(true);
      client.holdReads = true;
      final older = manager.refreshTelemetryConsent();
      final newer = manager.refreshTelemetryConsent();
      expect(client.reads.length, 2);
      client.reads[1].complete({'enabled': false, 'revision': 2});
      await newer;
      expect(manager.telemetryEnabled, isFalse);
      client.reads[0].complete({'enabled': true, 'revision': 1});
      await older;
      expect(manager.telemetryEnabled, isFalse);
      expect(manager.telemetryConsentRevision, isNull);
      final stored = jsonDecode(
        credentials.values.entries
            .singleWhere((e) => e.key.contains('.privacy.'))
            .value,
      );
      expect(stored['enabled'], isFalse);
    },
  );

  test(
    'late older consent read must not downgrade a newly confirmed revision',
    () async {
      await manager.setTelemetryConsent(true);
      client.holdReads = true;
      final older = manager.refreshTelemetryConsent(),
          newer = manager.refreshTelemetryConsent();
      client.reads[1].complete({'enabled': true, 'revision': 3});
      await newer;
      client.reads[0].complete({'enabled': true, 'revision': 1});
      await older;
      expect(manager.telemetryConsentRevision, 3);
    },
  );

  test(
    'explicit local withdrawal invalidates an in-flight remote consent read',
    () async {
      await manager.setTelemetryConsent(true);
      client.holdReads = true;
      final pending = manager.refreshTelemetryConsent();
      await manager.setTelemetryConsent(false);
      client.reads.single.complete({'enabled': true, 'revision': 1});
      await pending;
      expect(manager.telemetryEnabled, isFalse);
      expect(manager.telemetryConsentRevision, isNull);
      expect(client.consentWrites, 2);
    },
  );

  test(
    'account replacement invalidates an in-flight remote consent read',
    () async {
      await manager.setTelemetryConsent(true);
      client.holdReads = true;
      final pending = manager.refreshTelemetryConsent();
      client.identity = '00000000-0000-4000-8000-000000000002';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'fixture',
      );
      client.reads.single.complete({'enabled': true, 'revision': 1});
      await pending;
      expect(manager.telemetryConsentRevision, isNull);
      expect(manager.telemetryEnabled, isFalse);
    },
  );

  test(
    'consent granted while backgrounded starts no session until actual return',
    () async {
      final observer = observe();
      await observer.backgrounded();
      await manager.setTelemetryConsent(true);
      await observer.flush();
      expect(client.events, isEmpty);
      expect(observer.pendingEventCount, 0);
      await observer.returned();
      await observer.returned();
      expect(
        client.events.where((e) => e['name'] == 'session_start').length,
        1,
      );
      expect(client.consentWrites, 1);
    },
  );

  test(
    'late return consent refresh cannot restart a background session',
    () async {
      final observer = observe();
      await manager.setTelemetryConsent(true);
      await observer.flush();
      await observer.backgrounded();
      client.holdReads = true;
      final returned = observer.returned();
      expect(client.reads.length, 1);
      await observer.backgrounded();
      final starts = client.events
          .where((e) => e['name'] == 'session_start')
          .length;
      client.reads.single.complete({'enabled': true, 'revision': 1});
      await returned;
      expect(
        client.events.where((e) => e['name'] == 'session_start').length,
        starts,
      );
      expect(client.events.where((e) => e['name'] == 'session_end').length, 2);
    },
  );

  test(
    'unknown telemetry delivery retries identical event IDs without gameplay mutation',
    () async {
      final observer = observe();
      await manager.setTelemetryConsent(true);
      await observer.flush();
      final baseline = jsonEncode(game.state.toJson());
      client.holdDelivery = true;
      observer.resumeFinished(const Duration(seconds: 2), succeeded: true);
      await Future<void>.delayed(Duration.zero);
      expect(client.delivery, isNotNull);
      final ids = client.deliveries.last['ids'];
      client.holdDelivery = false;
      client.delivery!.complete();
      await Future<void>.delayed(Duration.zero);
      await observer.flush();
      expect(client.deliveries.last['ids'], ids);
      expect(observer.pendingEventCount, 0);
      expect(jsonEncode(game.state.toJson()), baseline);
    },
  );

  test(
    'account change during old delivery cannot clear new-account observations',
    () async {
      final observer = observe();
      await manager.setTelemetryConsent(true);
      await observer.flush();
      client.holdDelivery = true;
      observer.resumeFinished(const Duration(seconds: 2), succeeded: true);
      await Future<void>.delayed(Duration.zero);
      expect(client.delivery, isNotNull);
      client.identity = '00000000-0000-4000-8000-000000000002';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'fixture',
      );
      await manager.setTelemetryConsent(true);
      expect(observer.pendingEventCount, 1);
      client.holdDelivery = false;
      client.delivery!.complete();
      await Future<void>.delayed(Duration.zero);
      await observer.flush();
      expect(client.deliveries.last['account'], client.identity);
      final events = client.deliveries.last['events'] as List;
      expect(events.map((e) => e['name']), ['session_start']);
      expect(observer.pendingEventCount, 0);
    },
  );
}
