import 'package:test/test.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

class OfflineClient extends TideglassServiceClient {
  OfflineClient() : super(endpoint: Uri.parse('https://example.invalid'));
  bool unavailable = false;
  int revision = 0;
  final List<bool> consentChanges = [];
  final List<List<Map<String, dynamic>>> deliveries = [];
  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    if (unavailable) throw const ServiceException('service_unavailable');
    consentChanges.add(enabled);
    return ++revision;
  }

  @override
  Future<Map<String, dynamic>> sendTelemetry({
    required int consentRevision,
    required List<Map<String, dynamic>> events,
  }) async {
    deliveries.add(events);
    if (unavailable) throw const ServiceException('service_unavailable');
    return {'accepted': events.length};
  }
}

void main() {
  test(
    'refusal collects nothing; bounded retry retains IDs; opt-out stops offline',
    () async {
      final client = OfflineClient();
      final buffer = ConsentTelemetryBuffer(
        client,
        platform: 'test',
        build: 'test.1',
        deviceClass: 'host',
        capacity: 2,
      );
      final session = buffer.newSessionId();
      buffer.record('session_start', sessionId: session);
      expect(buffer.pendingEventCount, 0);
      await buffer.optIn();
      for (var i = 0; i < 3; i++) {
        buffer.record(
          'save_result',
          sessionId: session,
          properties: {'outcome': 'saved'},
        );
      }
      expect(buffer.pendingEventCount, 2);
      expect(buffer.droppedEventCount, 1);
      client.unavailable = true;
      await expectLater(buffer.flush(), throwsA(isA<ServiceException>()));
      final retainedIds = client.deliveries.single
          .map((event) => event['id'])
          .toList();
      client.unavailable = false;
      await buffer.flush();
      expect(
        client.deliveries.last.map((event) => event['id']).toList(),
        retainedIds,
      );
      expect(buffer.pendingEventCount, 0);
      buffer.record('session_start', sessionId: session);
      client.unavailable = true;
      await expectLater(buffer.optOut(), throwsA(isA<ServiceException>()));
      expect(buffer.enabled, false);
      expect(buffer.pendingEventCount, 0);
      expect(buffer.pendingRemoteOptOut, true);
      buffer.record('session_start', sessionId: session);
      expect(buffer.pendingEventCount, 0);
      client.unavailable = false;
      await buffer.flush();
      expect(client.consentChanges.last, false);
      expect(buffer.pendingRemoteOptOut, false);
      client.close();
    },
  );
  test(
    'expiry and unknown fields cannot become an unbounded diagnostics dump',
    () async {
      final client = OfflineClient();
      var now = DateTime.utc(2026, 10, 16);
      final buffer = ConsentTelemetryBuffer(
        client,
        platform: 'test',
        build: 'test.1',
        deviceClass: 'host',
        clock: () => now,
      );
      await buffer.optIn();
      final session = buffer.newSessionId();
      buffer.record('session_start', sessionId: session);
      now = now.add(const Duration(days: 8));
      await buffer.flush();
      expect(buffer.droppedEventCount, 1);
      expect(client.deliveries, isEmpty);
      expect(
        () => buffer.record(
          'save_result',
          sessionId: session,
          properties: {'raw_save': 'private'},
        ),
        throwsArgumentError,
      );
      client.close();
    },
  );
}
