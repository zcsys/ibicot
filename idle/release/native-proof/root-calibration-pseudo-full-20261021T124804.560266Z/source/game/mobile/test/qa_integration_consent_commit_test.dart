import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' as fixture;

class CommitGatedClient extends fixture.TestClient {
  final started = Completer<void>();
  final release = Completer<void>();
  bool remoteEnabled = false;
  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    if (enabled) {
      if (!started.isCompleted) {
        started.complete();
      }
      await release.future;
    }
    remoteEnabled = enabled;
    return enabled ? 1 : 2;
  }
}

void main() {
  test(
    'QA latest native opt-out also wins at a delayed remote commit',
    () async {
      final client = CommitGatedClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: fixture.MemoryCredentials(),
      );
      addTearDown(() {
        manager.dispose();
        client.close();
      });
      await manager.createAccount(cloudConsent: true);
      final enabling = manager.setTelemetryConsent(true);
      await client.started.future;
      final disabling = manager.setTelemetryConsent(false);
      await Future<void>.delayed(Duration.zero);
      client.release.complete();
      await Future.wait([enabling, disabling]);
      expect(manager.telemetryEnabled, false);
      expect(client.remoteEnabled, false);
    },
  );
  test(
    'QA latest buffer opt-out also wins at a delayed remote commit',
    () async {
      final client = CommitGatedClient();
      addTearDown(client.close);
      await client.createAccount(cloudConsent: true);
      final buffer = ConsentTelemetryBuffer(
        client,
        platform: 'test',
        build: 'qa',
        deviceClass: 'host',
      );
      final enabling = buffer.optIn();
      await client.started.future;
      final disabling = buffer.optOut();
      await Future<void>.delayed(Duration.zero);
      client.release.complete();
      await Future.wait([enabling, disabling]);
      expect(buffer.enabled, false);
      expect(client.remoteEnabled, false);
    },
  );
}
