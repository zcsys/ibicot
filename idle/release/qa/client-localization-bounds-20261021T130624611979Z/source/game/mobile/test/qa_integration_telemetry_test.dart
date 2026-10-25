import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'qa_integration_services_test.dart' show identity;

class TelemetryClient extends TideglassServiceClient {
  TelemetryClient() : super(endpoint: Uri.parse('https://example.invalid'));
  final accounts = <String?>[];
  Completer<void>? optIn;
  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    if (enabled) {
      await optIn?.future;
    }
    return 1;
  }

  @override
  Future<Map<String, dynamic>> sendTelemetry({
    required int consentRevision,
    required List<Map<String, dynamic>> events,
  }) async {
    accounts.add(session?.accountId);
    return {};
  }
}

void main() {
  test(
    'QA telemetry queue cannot transfer activity to a replacement account',
    () async {
      final client = TelemetryClient()..session = identity('1');
      addTearDown(client.close);
      final buffer = ConsentTelemetryBuffer(
        client,
        platform: 'test',
        build: 'qa',
        deviceClass: 'host',
      );
      await buffer.optIn();
      buffer.record('session_start', sessionId: buffer.newSessionId());
      expect(buffer.pendingEventCount, 1);
      client.session = identity('2');
      await buffer.flush();
      expect(client.accounts, isNot(contains(identity('2').accountId)));
      expect(buffer.enabled, false);
    },
  );
  test('QA telemetry buffer honors opt-out after a delayed opt-in', () async {
    final client = TelemetryClient()
      ..session = identity('1')
      ..optIn = Completer<void>();
    addTearDown(client.close);
    final buffer = ConsentTelemetryBuffer(
      client,
      platform: 'test',
      build: 'qa',
      deviceClass: 'host',
    );
    final pending = buffer.optIn();
    final disabling = buffer.optOut();
    client.optIn!.complete();
    await Future.wait([pending, disabling]);
    expect(buffer.enabled, false);
    expect(buffer.pendingEventCount, 0);
  });
}
