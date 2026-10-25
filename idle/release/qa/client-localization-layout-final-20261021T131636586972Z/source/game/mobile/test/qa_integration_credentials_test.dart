import 'dart:async';
import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'native_services_test.dart' as fixture;
import 'qa_integration_services_test.dart' show identity;

class DelayedCredentials extends fixture.MemoryCredentials {
  String? blocked;
  bool used = false;
  final entered = Completer<void>();
  final release = Completer<void>();
  Future<void> delay(String operation, String key) async {
    if (operation == blocked && key.endsWith('.session') && !used) {
      used = true;
      entered.complete();
      await release.future;
    }
  }

  @override
  Future<String?> read(String key) async {
    final value = await super.read(key);
    await delay('read', key);
    return value;
  }

  @override
  Future<void> write(String key, String value) async {
    await delay('write', key);
    await super.write(key, value);
  }

  @override
  Future<void> delete(String key) async {
    await delay('delete', key);
    await super.delete(key);
  }

  String? get savedAccount {
    final raw = values.entries
        .where((e) => e.key.endsWith('.session'))
        .firstOrNull
        ?.value;
    return raw == null
        ? null
        : (jsonDecode(raw) as Map)['account_id'] as String;
  }
}

void main() {
  test(
    'QA delayed secure initialization cannot replace a recovered newer account',
    () async {
      final storage = DelayedCredentials();
      final first = fixture.TestClient();
      final original = NativeServicesManager(
        client: first,
        credentials: storage,
      );
      await original.createAccount(cloudConsent: true);
      original.dispose();
      first.close();
      storage.blocked = 'read';
      final client = fixture.TestClient()..identity = identity('2').accountId;
      final manager = NativeServicesManager(
        client: client,
        credentials: storage,
      );
      addTearDown(() {
        manager.dispose();
        client.close();
      });
      final initializing = manager.initialize();
      await storage.entered.future;
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'test',
      );
      storage.release.complete();
      await initializing;
      expect(manager.session?.accountId, identity('2').accountId);
      expect(storage.savedAccount, identity('2').accountId);
      expect(manager.recoveryAcknowledged, true);
    },
  );
  test(
    'QA delayed secure logout deletion cannot erase a newer recovery',
    () async {
      final storage = DelayedCredentials();
      final client = fixture.TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: storage,
      );
      addTearDown(() {
        manager.dispose();
        client.close();
      });
      await manager.createAccount(cloudConsent: true);
      storage.blocked = 'delete';
      final logout = manager.signOut(localOnly: true);
      await storage.entered.future;
      client.identity = identity('2').accountId;
      final recovering = manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'test',
      );
      await Future<void>.delayed(Duration.zero);
      storage.release.complete();
      await Future.wait([logout, recovering]);
      expect(manager.session?.accountId, identity('2').accountId);
      expect(storage.savedAccount, identity('2').accountId);
      expect(manager.recoveryAcknowledged, true);
    },
  );
  test(
    'QA delayed secure old-login write cannot overwrite a newer recovery',
    () async {
      final storage = DelayedCredentials()..blocked = 'write';
      final client = fixture.TestClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: storage,
      );
      addTearDown(() {
        manager.dispose();
        client.close();
      });
      final creating = manager.createAccount(cloudConsent: true);
      await storage.entered.future;
      client.identity = identity('2').accountId;
      final recovering = manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'test',
      );
      await Future<void>.delayed(Duration.zero);
      storage.release.complete();
      await Future.wait([creating, recovering]);
      expect(manager.session?.accountId, identity('2').accountId);
      expect(storage.savedAccount, identity('2').accountId);
      expect(manager.recoveryAcknowledged, true);
    },
  );
}
