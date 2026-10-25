import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/game_telemetry.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' show MemoryCredentials, TestClient;

class TelemetryClient extends TestClient {
  int consentWrites = 0, revision = 0;
  bool enabled = false, offline = false;
  final events = <Map<String, dynamic>>[];
  @override
  Future<int> setTelemetryConsent(bool value) async {
    if (offline) throw const ServiceException('service_unavailable');
    consentWrites++;
    enabled = value;
    if (!value) events.clear();
    return ++revision;
  }

  @override
  Future<Map<String, dynamic>> readTelemetryConsent() async {
    if (offline) throw const ServiceException('service_unavailable');
    return {'enabled': enabled, 'revision': revision};
  }

  @override
  Future<Map<String, dynamic>> sendTelemetry({
    required int consentRevision,
    required List<Map<String, dynamic>> events,
  }) async {
    if (offline) throw const ServiceException('service_unavailable');
    if (!enabled || consentRevision != revision) {
      throw const ServiceException('consent_revision_changed', status: 403);
    }
    for (final event in events) {
      if (!this.events.any((old) => old['id'] == event['id'])) {
        this.events.add(
          Map<String, dynamic>.from(jsonDecode(jsonEncode(event))),
        );
      }
    }
    return {'accepted': events.length};
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late TelemetryClient client;
  late NativeServicesManager manager;
  late GameController game;
  late GameTelemetry telemetry;
  final epoch = DateTime.utc(2026, 10, 19);
  setUp(() async {
    client = TelemetryClient();
    manager = NativeServicesManager(
      client: client,
      credentials: MemoryCredentials(),
    );
    game = GameController(
      startTicker: false,
      clock: () => epoch,
      initialState: GameState.initial().copyWith(
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
        walletMicros: TideglassEngine.firstPrestigeMicros,
      ),
      onPersist: (_, _) async {},
    );
    telemetry = GameTelemetry(
      game: game,
      services: manager,
      platform: 'test',
      clock: () => epoch,
    );
    await manager.createAccount(cloudConsent: true);
  });
  tearDown(() {
    telemetry.dispose();
    game.dispose();
    manager.dispose();
    client.close();
  });

  test(
    'no collection before consent and no historical action backfill',
    () async {
      expect(game.rechart(), isTrue);
      await game.save();
      await telemetry.flush();
      expect(client.events, isEmpty);
      expect(telemetry.pendingEventCount, 0);
      await manager.setTelemetryConsent(true);
      await telemetry.flush();
      expect(client.consentWrites, 1);
      expect(
        client.events.where((e) => e['name'] == 'session_start').length,
        1,
      );
      expect(client.events.where((e) => e['name'] == 'rechart'), isEmpty);
      expect(jsonEncode(client.events), isNot(contains('secret-session')));
      expect(jsonEncode(client.events), isNot(contains('wallet')));
    },
  );

  test(
    'actual Rechart and save are observed once with bounded clean lifecycle',
    () async {
      await manager.setTelemetryConsent(true);
      expect(game.rechart(), isTrue);
      await game.save();
      await game.save();
      await telemetry.backgrounded();
      await telemetry.backgrounded();
      expect(client.events.where((e) => e['name'] == 'rechart').length, 1);
      expect(client.events.where((e) => e['name'] == 'save_result').length, 1);
      expect(client.events.where((e) => e['name'] == 'session_end').length, 1);
      await telemetry.returned();
      await telemetry.returned();
      expect(
        client.events.where((e) => e['name'] == 'session_start').length,
        2,
      );
      expect(
        client.consentWrites,
        1,
        reason: 'Returning never writes another opt-in.',
      );
    },
  );

  test(
    'offline withdrawal immediately clears queue and never resumes on return',
    () async {
      await manager.setTelemetryConsent(true);
      await telemetry.flush();
      client.offline = true;
      game.rechart();
      await game.save();
      expect(telemetry.pendingEventCount, greaterThan(0));
      await expectLater(
        manager.setTelemetryConsent(false),
        throwsA(isA<ServiceException>()),
      );
      expect(telemetry.pendingEventCount, 0);
      await telemetry.returned();
      expect(telemetry.pendingEventCount, 0);
      client.offline = false;
      await manager.retryTelemetryDeletion();
      await telemetry.flush();
      expect(client.events, isEmpty);
    },
  );

  test(
    'remote withdrawal is a read on return and cannot be overwritten by old local consent',
    () async {
      await manager.setTelemetryConsent(true);
      await telemetry.flush();
      await client.setTelemetryConsent(false);
      await telemetry.returned();
      expect(manager.telemetryEnabled, isFalse);
      expect(manager.telemetryConsentRevision, isNull);
      expect(client.consentWrites, 2);
      expect(client.events, isEmpty);
      game.rechart();
      await game.save();
      await telemetry.flush();
      expect(client.events, isEmpty);
    },
  );

  test(
    'a rejected old revision stays disabled across unrelated manager notifications',
    () async {
      await manager.setTelemetryConsent(true);
      await telemetry.flush();
      await client.setTelemetryConsent(false);
      game.rechart();
      await game.save();
      await telemetry.flush();
      expect(telemetry.buffer!.enabled, isFalse);
      await game.save();
      await telemetry.flush();
      expect(telemetry.buffer!.enabled, isFalse);
      expect(telemetry.pendingEventCount, 0);
      expect(client.events, isEmpty);
    },
  );

  test(
    'account replacement drops queued observations and does not inherit consent',
    () async {
      await manager.setTelemetryConsent(true);
      await telemetry.flush();
      client.offline = true;
      game.rechart();
      await game.save();
      client.identity = '00000000-0000-4000-8000-000000000002';
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'fixture',
      );
      expect(manager.telemetryConsentRevision, isNull);
      await telemetry.flush();
      expect(telemetry.pendingEventCount, 0);
      expect(telemetry.buffer!.enabled, isFalse);
    },
  );
}
