import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'native_services_test.dart' as fixture;
import 'qa_integration_services_test.dart' show identity;

class DelayedOwnershipClient extends fixture.TestClient {
  final started = Completer<void>();
  final release = Completer<void>();
  bool failOld = false;
  int calls = 0;
  @override
  Future<Map<String, dynamic>> entitlements() async {
    final response = await super.entitlements();
    if (++calls == 1) {
      started.complete();
      await release.future;
      if (failOld) {
        throw const ServiceException('service_unavailable');
      }
    }
    return response;
  }
}

void main() {
  for (final failure in [false, true]) {
    test(
      'QA stale ownership ${failure ? 'failure' : 'response'} cannot clear a newer account projection',
      () async {
        final client = DelayedOwnershipClient()
          ..grant = true
          ..failOld = failure;
        final manager = NativeServicesManager(
          client: client,
          credentials: fixture.MemoryCredentials(),
          localAccountSeed: () => 'main.seed',
        );
        addTearDown(() {
          manager.dispose();
          client.close();
        });
        await manager.createAccount(cloudConsent: true);
        final old = manager.refreshOwnership().then<Object?>(
          (_) => null,
          onError: (Object error) => error,
        );
        await client.started.future;
        client.session = identity('2');
        await manager.refreshOwnership();
        expect(manager.ownedEntitlementIds, {'pass.01'});
        client.release.complete();
        await old;
        expect(manager.ownedEntitlementIds, {'pass.01'});
      },
    );
  }
}
