import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';

import 'ad_privacy_test.dart' as author;
import 'native_services_test.dart' as fixtures;

class DeferredReadGateway extends author.PrivacyGateway {
  final read = Completer<AdPrivacySnapshot>();
  @override
  Future<AdPrivacySnapshot> readAdPrivacyState() async {
    reads++;
    return read.future;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'QA local seed change rejects a delayed device privacy observation',
    () async {
      var seed = 'original';
      final gateway = DeferredReadGateway();
      final client = author.ClaimClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: fixtures.MemoryCredentials(),
        rewarded: gateway,
        configuration: const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'configured-real-unit',
        ),
        platformOverride: 'apple',
        localAccountSeed: () => seed,
      );
      final reading = manager.refreshAdPrivacyOptions();
      await author.spin(() => gateway.reads == 1);
      seed = 'imported-harbor';
      gateway.read.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: true,
        ),
      );
      await reading;
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      expect(manager.adPrivacyBusy, false);
      expect(
        [gateway.updates, gateway.forms, gateway.consents, gateway.loads],
        [0, 0, 0, 0],
      );
      manager.dispose();
      client.close();
    },
  );

  test(
    'QA disposal rejects late privacy observation without listener callbacks',
    () async {
      final gateway = DeferredReadGateway();
      final client = author.ClaimClient();
      final manager = author.managerFor(gateway, client);
      var calls = 0;
      manager.addListener(() => calls++);
      final reading = manager.refreshAdPrivacyOptions();
      await author.spin(() => gateway.reads == 1);
      manager.dispose();
      final before = calls;
      gateway.read.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: true,
        ),
      );
      await reading;
      expect(calls, before);
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      client.close();
    },
  );

  testWidgets(
    'QA a visible options form stays exclusive beyond update timeout',
    (tester) async {
      final gateway = author.PrivacyGateway()
        ..form = Completer<AdPrivacySnapshot>();
      final client = author.ClaimClient();
      final manager = author.managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      final form = manager.showAdPrivacyOptions();
      await tester.pump();
      expect(gateway.forms, 1);
      await tester.pump(const Duration(minutes: 10));
      expect(manager.adPrivacyBusy, true);
      await manager.updateAdPrivacyOptions();
      await manager.showAdPrivacyOptions();
      expect(await manager.requestRewardedSupport(dayId: 1, slot: 0), null);
      expect(
        [
          gateway.reads,
          gateway.updates,
          gateway.forms,
          gateway.consents,
          gateway.loads,
        ],
        [1, 0, 1, 0, 0],
      );
      gateway.form!.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: false,
        ),
      );
      await form;
      expect(manager.adPrivacyBusy, false);
      manager.dispose();
      client.close();
    },
  );

  test(
    'QA completed display still rejects receipt after local harbor changes',
    () async {
      var seed = 'original';
      final gateway = author.PrivacyGateway()..ad.earned = true;
      final client = author.ClaimClient()
        ..claims = Completer<Map<String, dynamic>>();
      final manager = NativeServicesManager(
        client: client,
        credentials: fixtures.MemoryCredentials(),
        rewarded: gateway,
        configuration: const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'configured-real-unit',
        ),
        platformOverride: 'apple',
        localAccountSeed: () => seed,
      );
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await author.spin(() => client.claimReads == 1);
      seed = 'different-main-harbor';
      client.claims!.complete({
        'claims': [
          {'day_id': 1, 'slot': 0, 'receipt_id': 'synthetic-confirmed'},
        ],
      });
      expect(await request, null);
      expect(gateway.ad.disposes, 1);
      manager.dispose();
      client.close();
    },
  );

  test(
    'QA disabled, missing and SDK example identifiers make zero privacy calls',
    () async {
      for (final config in [
        const NativeServiceConfiguration(),
        const NativeServiceConfiguration(adsEnabled: true),
        const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'ca-app-pub-3940256099942544/1712485313',
        ),
      ]) {
        final gateway = author.PrivacyGateway();
        final client = author.ClaimClient();
        final manager = NativeServicesManager(
          client: client,
          credentials: fixtures.MemoryCredentials(),
          rewarded: gateway,
          configuration: config,
          platformOverride: 'apple',
        );
        await manager.initialize();
        await manager.refreshAdPrivacyOptions();
        await manager.updateAdPrivacyOptions();
        await expectLater(
          manager.showAdPrivacyOptions(),
          throwsA(isA<Exception>()),
        );
        expect(manager.adPrivacyAvailable, false);
        expect(
          [
            gateway.reads,
            gateway.updates,
            gateway.forms,
            gateway.consents,
            gateway.loads,
          ],
          [0, 0, 0, 0, 0],
        );
        manager.dispose();
        client.close();
      }
    },
  );
}
