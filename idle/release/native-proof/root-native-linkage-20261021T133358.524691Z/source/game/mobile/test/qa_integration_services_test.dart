import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/support_service_bridge.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' as fixture;
import 'support_service_bridge_test.dart' as support;

ServiceSession identity(String suffix) => ServiceSession(
  accountId: '00000000-0000-4000-8000-00000000000$suffix',
  token: 'test-session-$suffix',
  expiresAt: DateTime.utc(2030),
);

class GatedHttp extends Fake implements HttpClient {
  final inner = HttpClient();
  final opened = Completer<void>();
  final release = Completer<void>();
  @override
  Future<HttpClientRequest> openUrl(String method, Uri url) async {
    if (!opened.isCompleted) {
      opened.complete();
    }
    await release.future;
    return inner.openUrl(method, url);
  }

  @override
  void close({bool force = false}) => inner.close(force: force);
}

class ConsentClient extends fixture.TestClient {
  final optInStarted = Completer<void>();
  final releaseOptIn = Completer<void>();
  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    if (enabled) {
      optInStarted.complete();
      await releaseOptIn.future;
    }
    return enabled ? 1 : 2;
  }
}

class PurchaseClient extends fixture.TestClient {
  final verifyStarted = Completer<void>();
  final releaseVerify = Completer<void>();
  @override
  Future<Map<String, dynamic>> verifyPurchase({
    required String platform,
    required String proof,
  }) async {
    final response = await super.verifyPurchase(
      platform: platform,
      proof: proof,
    );
    verifyStarted.complete();
    await releaseVerify.future;
    return response;
  }
}

class TrackingClaims extends support.ClaimsClient {
  final syncedAccounts = <String?>[];
  @override
  Future<Map<String, dynamic>> claimSupport({
    required int dayId,
    required int slot,
    required String route,
    String? proof,
  }) async {
    syncedAccounts.add(session?.accountId);
    return super.claimSupport(
      dayId: dayId,
      slot: slot,
      route: route,
      proof: proof,
    );
  }
}

void main() {
  test(
    'QA authenticated operation never adopts a later account while opening HTTP',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final authorizations = <String?>[];
      final subscription = server.listen((request) async {
        authorizations.add(
          request.headers.value(HttpHeaders.authorizationHeader),
        );
        await request.drain<void>();
        request.response.headers.contentType = ContentType.json;
        request.response.write('{}');
        await request.response.close();
      });
      final http = GatedHttp();
      final client = TideglassServiceClient(
        endpoint: Uri.parse('http://127.0.0.1:${server.port}'),
        allowLocalDevelopment: true,
        httpClient: http,
      )..session = identity('1');
      addTearDown(() async {
        client.close();
        await subscription.cancel();
        await server.close(force: true);
      });
      final request = client.exportAccount().then<Object?>(
        (value) => value,
        onError: (Object error) => error,
      );
      await http.opened.future;
      client.session = identity('2');
      http.release.complete();
      await request;
      expect(
        authorizations,
        isNot(contains('Bearer test-session-2')),
        reason:
            'An operation begun for account 1 must use its captured credential or cancel.',
      );
    },
  );
  test(
    'QA late sign-out response cannot erase a newly recovered account',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      final revokeArrived = Completer<void>();
      final releaseRevoke = Completer<void>();
      final subscription = server.listen((request) async {
        await request.drain<void>();
        request.response.headers.contentType = ContentType.json;
        if (request.uri.path == '/v1/sessions/revoke') {
          revokeArrived.complete();
          await releaseRevoke.future;
          request.response.write('{}');
        } else {
          request.response.write(
            jsonEncode({
              'account_id': identity('2').accountId,
              'session_token': identity('2').token,
              'expires_at': DateTime.utc(2030).millisecondsSinceEpoch ~/ 1000,
            }),
          );
        }
        await request.response.close();
      });
      final client = TideglassServiceClient(
        endpoint: Uri.parse('http://127.0.0.1:${server.port}'),
        allowLocalDevelopment: true,
      )..session = identity('1');
      addTearDown(() async {
        client.close();
        await subscription.cancel();
        await server.close(force: true);
      });
      final pending = client.signOut().then<Object?>(
        (_) => null,
        onError: (Object error) => error,
      );
      await revokeArrived.future;
      await client.recoverAccount(
        accountId: identity('2').accountId,
        recoveryCode: 'test-recovery',
      );
      releaseRevoke.complete();
      await pending;
      expect(client.session?.accountId, identity('2').accountId);
    },
  );
  test('QA later opt-out wins over a delayed earlier opt-in', () async {
    final client = ConsentClient();
    final manager = NativeServicesManager(
      client: client,
      credentials: fixture.MemoryCredentials(),
    );
    addTearDown(() {
      manager.dispose();
      client.close();
    });
    await manager.createAccount(cloudConsent: true);
    final pending = manager.setTelemetryConsent(true);
    await client.optInStarted.future;
    final disabling = manager.setTelemetryConsent(false);
    client.releaseOptIn.complete();
    await Future.wait([pending, disabling]);
    expect(manager.telemetryEnabled, false);
    expect(manager.pendingTelemetryDeletion, false);
  });
  for (final changeSeed in [false, true]) {
    test(
      'QA old purchase response cannot complete after ${changeSeed ? 'harbor' : 'account'} changes',
      () async {
        final client = PurchaseClient()..grant = true;
        final store = fixture.TestStore();
        var seed = 'main.seed';
        final manager = NativeServicesManager(
          client: client,
          credentials: fixture.MemoryCredentials(),
          store: store,
          localAccountSeed: () => seed,
          platformOverride: 'apple',
          configuration: const NativeServiceConfiguration(
            commerceEnabled: true,
          ),
        );
        addTearDown(() async {
          manager.dispose();
          client.close();
          await store.updates.close();
        });
        await manager.initialize();
        await manager.createAccount(cloudConsent: true);
        final update = fixture.purchase(PurchaseStatus.purchased);
        store.updates.add([update]);
        await client.verifyStarted.future;
        if (changeSeed) {
          seed = 'different.seed';
        } else {
          client.session = identity('2');
        }
        client.releaseVerify.complete();
        await Future<void>.delayed(const Duration(milliseconds: 10));
        expect(manager.ownedEntitlementIds, isEmpty);
        expect(
          store.completes,
          0,
          reason:
              'A stale verification must remain retryable for its original account and harbor.',
        );
        expect(
          manager.purchaseStates['dev.tideglass.pass.01'],
          isNot('verified'),
        );
      },
    );
  }
  test(
    'QA local briefing never syncs to an account selected during its disk write',
    () async {
      final saveStarted = Completer<void>();
      final releaseSave = Completer<void>();
      final game = GameController(
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 16, 12),
        onPersist: (_, _) async {
          if (!saveStarted.isCompleted) {
            saveStarted.complete();
          }
          await releaseSave.future;
        },
      );
      final client = TrackingClaims()..session = identity('1');
      final manager = support.ClaimsManager(client)
        ..recoveryAcknowledged = true;
      final bridge = SupportServiceBridge(game, manager);
      addTearDown(() {
        bridge.dispose();
        manager.dispose();
        client.close();
        game.dispose();
      });
      final pending = bridge.completeBriefing(0);
      await saveStarted.future;
      client.session = identity('2');
      releaseSave.complete();
      await pending;
      expect(game.state.support.tokens.length, 1);
      expect(client.syncedAccounts, isNot(contains(identity('2').accountId)));
    },
  );
}
