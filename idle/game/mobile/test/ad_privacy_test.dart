import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
// Test uses the exact pinned SDK wire codec for consent-info request parameters.
// ignore: implementation_imports
import 'package:google_mobile_ads/src/ump/user_messaging_codec.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/service_settings.dart';

import 'native_services_test.dart' as fixtures;

class PrivacyAd implements NativeRewardedAd {
  Completer<void>? configuration;
  Completer<bool>? showing;
  bool earned = false;
  int shows = 0, disposes = 0;
  @override
  Future<void> configure({
    required String accountId,
    required int dayId,
    required int slot,
  }) async {
    await configuration?.future;
  }

  @override
  Future<bool> show() async {
    shows++;
    return showing == null ? earned : showing!.future;
  }

  @override
  Future<void> dispose() async {
    disposes++;
  }
}

class PrivacyGateway implements RewardedGateway, AdPrivacyGateway {
  int consents = 0, reads = 0, updates = 0, forms = 0, loads = 0;
  Completer<bool>? consent;
  Completer<NativeRewardedAd>? loading;
  Completer<AdPrivacySnapshot>? form, update;
  bool failRead = false, failForm = false, failUpdate = false;
  AdPrivacySnapshot state = const AdPrivacySnapshot(
    requirement: AdPrivacyRequirement.required,
    canRequestAds: true,
  );
  final ad = PrivacyAd();
  @override
  Future<bool> requestConsent() async {
    consents++;
    return consent == null ? true : consent!.future;
  }

  @override
  Future<NativeRewardedAd> load(String unitId) async {
    loads++;
    return loading == null ? ad : loading!.future;
  }

  @override
  Future<AdPrivacySnapshot> readAdPrivacyState() async {
    reads++;
    if (failRead) throw StateError('synthetic status failure');
    return state;
  }

  @override
  Future<AdPrivacySnapshot> updateAdPrivacyState() async {
    updates++;
    if (failUpdate) throw StateError('synthetic information-update failure');
    if (update != null) return update!.future;
    return state = const AdPrivacySnapshot(
      requirement: AdPrivacyRequirement.required,
      canRequestAds: true,
    );
  }

  @override
  Future<AdPrivacySnapshot> showAdPrivacyOptions() async {
    forms++;
    if (failForm) throw StateError('synthetic form failure');
    if (form != null) return form!.future;
    return state = const AdPrivacySnapshot(
      requirement: AdPrivacyRequirement.required,
      canRequestAds: false,
    );
  }
}

class ClaimClient extends fixtures.TestClient {
  int claimReads = 0;
  Completer<Map<String, dynamic>>? claims;
  @override
  Future<Map<String, dynamic>> supportClaims() async {
    claimReads++;
    return claims == null
        ? {'claims': <Map<String, dynamic>>[]}
        : claims!.future;
  }
}

NativeServicesManager managerFor(
  PrivacyGateway gateway,
  ClaimClient client, {
  bool configured = true,
}) => NativeServicesManager(
  client: configured ? client : null,
  credentials: fixtures.MemoryCredentials(),
  rewarded: gateway,
  configuration: const NativeServiceConfiguration(
    adsEnabled: true,
    rewardedAdUnitId: 'configured-real-unit',
  ),
  platformOverride: 'apple',
  localAccountSeed: () => 'same-main-seed',
);
Future<void> spin(bool Function() predicate) async {
  for (var i = 0; i < 30 && !predicate(); i++) {
    await Future<void>.delayed(Duration.zero);
  }
  expect(predicate(), isTrue);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'default guest and absent capability do not contact the ad SDK',
    () async {
      final gateway = PrivacyGateway();
      final client = ClaimClient();
      final manager = managerFor(gateway, client, configured: false);
      await manager.initialize();
      await manager.refreshAdPrivacyOptions();
      await manager.updateAdPrivacyOptions();
      expect(manager.adPrivacyAvailable, false);
      await expectLater(
        manager.showAdPrivacyOptions(),
        throwsA(isA<Exception>()),
      );
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
      final legacy = NativeServicesManager(
        client: client,
        rewarded: fixtures.TestRewarded(),
        credentials: fixtures.MemoryCredentials(),
        platformOverride: 'apple',
        configuration: const NativeServiceConfiguration(
          adsEnabled: true,
          rewardedAdUnitId: 'configured-real-unit',
        ),
      );
      expect(legacy.adPrivacyAvailable, false);
      await legacy.createAccount(cloudConsent: true);
      expect(await legacy.requestRewardedSupport(dayId: 1, slot: 0), null);
      manager.dispose();
      legacy.dispose();
      client.close();
    },
  );

  test(
    'configured initialization does not query; explicit local status works after sign-out',
    () async {
      final gateway = PrivacyGateway();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.initialize();
      expect(gateway.reads, 0);
      expect(gateway.updates, 0);
      await manager.refreshAdPrivacyOptions();
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.required);
      expect(gateway.consents, 0);
      expect(gateway.loads, 0);
      expect(gateway.forms, 0);
      expect(gateway.updates, 0);
      manager.dispose();
      client.close();
    },
  );

  test(
    'cold unknown can update information then open required options without an ad',
    () async {
      final gateway = PrivacyGateway()
        ..state = const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.unknown,
          canRequestAds: false,
        );
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.initialize();
      await manager.refreshAdPrivacyOptions();
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      expect(gateway.updates, 0);
      await manager.updateAdPrivacyOptions();
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.required);
      expect(gateway.updates, 1);
      expect(gateway.forms, 0);
      await manager.showAdPrivacyOptions();
      expect(gateway.forms, 1);
      expect(gateway.consents, 0);
      expect(gateway.loads, 0);
      manager.dispose();
      client.close();
    },
  );

  test(
    'explicit information update fails safely and retries; late account response cannot publish',
    () async {
      final gateway = PrivacyGateway()
        ..state = const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.unknown,
          canRequestAds: false,
        )
        ..failUpdate = true;
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.updateAdPrivacyOptions();
      expect(manager.adPrivacyError, 'ad_privacy_unavailable');
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      expect(manager.adPrivacyBusy, false);
      gateway.failUpdate = false;
      gateway.update = Completer<AdPrivacySnapshot>();
      final pending = manager.updateAdPrivacyOptions();
      await spin(() => gateway.updates == 2);
      await manager.createAccount(cloudConsent: true);
      gateway.update!.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: true,
        ),
      );
      await pending;
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      gateway.update = null;
      await manager.updateAdPrivacyOptions();
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.required);
      expect(manager.adPrivacyError, null);
      expect(gateway.consents, 0);
      expect(gateway.loads, 0);
      expect(gateway.forms, 0);
      manager.dispose();
      client.close();
    },
  );

  testWidgets(
    'stalled explicit information update is bounded and late success cannot publish',
    (tester) async {
      final gateway = PrivacyGateway()..update = Completer<AdPrivacySnapshot>();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      final pending = manager.updateAdPrivacyOptions();
      await tester.pump();
      expect(manager.adPrivacyBusy, true);
      await tester.pump(const Duration(seconds: 36));
      await pending;
      expect(manager.adPrivacyBusy, false);
      expect(manager.adPrivacyError, 'ad_privacy_unavailable');
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      gateway.update!.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: true,
        ),
      );
      await tester.pump();
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
      expect(gateway.consents, 0);
      expect(gateway.forms, 0);
      expect(gateway.loads, 0);
      manager.dispose();
      client.close();
    },
  );

  test(
    'privacy options invalidates delayed consent even if old consent later allows ads',
    () async {
      final gateway = PrivacyGateway()..consent = Completer<bool>();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await spin(() => gateway.consents == 1);
      await manager.showAdPrivacyOptions();
      gateway.consent!.complete(true);
      expect(await request, null);
      expect(gateway.loads, 0);
      expect(gateway.forms, 1);
      expect(client.claimReads, 0);
      manager.dispose();
      client.close();
    },
  );

  test('options invalidate loaded and configured but unshown ads', () async {
    for (final loading in [true, false]) {
      final gateway = PrivacyGateway();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      if (loading) {
        gateway.loading = Completer<NativeRewardedAd>();
      } else {
        gateway.ad.configuration = Completer<void>();
      }
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await spin(() => gateway.loads == 1);
      await manager.showAdPrivacyOptions();
      if (loading) {
        gateway.loading!.complete(gateway.ad);
        await expectLater(request, throwsA(isA<Exception>()));
      } else {
        gateway.ad.configuration!.complete();
        expect(await request, null);
      }
      expect(gateway.ad.shows, 0);
      expect(gateway.ad.disposes, 1);
      expect(client.claimReads, 0);
      manager.dispose();
      client.close();
    }
  });

  test(
    'options invalidate unfinished display and prevent new requests while form is open',
    () async {
      final gateway = PrivacyGateway()..form = Completer<AdPrivacySnapshot>();
      gateway.ad.showing = Completer<bool>();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await spin(() => gateway.ad.shows == 1);
      final options = manager.showAdPrivacyOptions();
      await spin(() => gateway.forms == 1);
      expect(await manager.requestRewardedSupport(dayId: 1, slot: 1), null);
      expect(gateway.consents, 1);
      gateway.ad.showing!.complete(true);
      expect(await request, null);
      expect(client.claimReads, 0);
      gateway.form!.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.required,
          canRequestAds: false,
        ),
      );
      await options;
      expect(gateway.ad.disposes, 1);
      manager.dispose();
      client.close();
    },
  );

  test(
    'completed display keeps its server-confirmed receipt despite later privacy change',
    () async {
      final gateway = PrivacyGateway();
      gateway.ad.earned = true;
      final client = ClaimClient()..claims = Completer<Map<String, dynamic>>();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await spin(() => client.claimReads == 1);
      await manager.showAdPrivacyOptions();
      final receipt = {
        'day_id': 1,
        'slot': 0,
        'receipt_id': 'already-server-confirmed-synthetic',
      };
      client.claims!.complete({
        'claims': [receipt],
      });
      expect(await request, receipt);
      expect(gateway.ad.disposes, 1);
      expect(gateway.forms, 1);
      expect(await manager.requestRewardedSupport(dayId: 1, slot: 1), null);
      expect(
        gateway.loads,
        1,
      ); // Refused current SDK permission never starts another ad.
      manager.dispose();
      client.close();
    },
  );

  test(
    'same-account reauthentication invalidates old request and late privacy response',
    () async {
      final gateway = PrivacyGateway()..consent = Completer<bool>();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      await manager.refreshAdPrivacyOptions();
      final request = manager.requestRewardedSupport(dayId: 1, slot: 0);
      await spin(() => gateway.consents == 1);
      gateway.form = Completer<AdPrivacySnapshot>();
      final options = manager.showAdPrivacyOptions();
      await spin(() => gateway.forms == 1);
      await manager.recoverAccount(
        accountId: client.identity,
        recoveryCode: 'fixture',
      );
      gateway.form!.complete(
        const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.notRequired,
          canRequestAds: true,
        ),
      );
      await options;
      gateway.consent!.complete(true);
      expect(await request, null);
      expect(gateway.loads, 0);
      expect(
        manager.adPrivacyRequirement,
        AdPrivacyRequirement.required,
      ); // Late response was not published.
      manager.dispose();
      client.close();
    },
  );

  test(
    'status/form errors retain an options retry and cannot load ads',
    () async {
      final gateway = PrivacyGateway();
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      await manager.refreshAdPrivacyOptions();
      gateway.failForm = true;
      await manager.showAdPrivacyOptions();
      expect(manager.adPrivacyError, 'ad_privacy_unavailable');
      expect(manager.adPrivacyRequirement, AdPrivacyRequirement.required);
      gateway.failRead = true;
      expect(await manager.requestRewardedSupport(dayId: 1, slot: 0), null);
      expect(gateway.loads, 0);
      gateway.failRead = false;
      gateway.failForm = false;
      await manager.showAdPrivacyOptions();
      expect(manager.adPrivacyError, null);
      manager.dispose();
      client.close();
    },
  );

  test(
    'unknown privacy requirement cannot authorize an ad even with a stale allowed value',
    () async {
      final gateway = PrivacyGateway()
        ..state = const AdPrivacySnapshot(
          requirement: AdPrivacyRequirement.unknown,
          canRequestAds: true,
        );
      final client = ClaimClient();
      final manager = managerFor(gateway, client);
      await manager.createAccount(cloudConsent: true);
      expect(await manager.requestRewardedSupport(dayId: 1, slot: 0), null);
      expect(gateway.loads, 0);
      expect(client.claimReads, 0);
      manager.dispose();
      client.close();
    },
  );

  test(
    'real SDK explicit update resolves cold unknown without loading consent or ads',
    () async {
      final channel = MethodChannel(
        'plugins.flutter.io/google_mobile_ads/ump',
        StandardMethodCodec(UserMessagingCodec()),
      );
      final calls = <String>[];
      var requirement = 2;
      var allowed = false;
      var formFailure = false;
      var updateFailure = false;
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            calls.add(call.method);
            if (call.method ==
                'ConsentInformation#getPrivacyOptionsRequirementStatus') {
              return requirement;
            }
            if (call.method == 'ConsentInformation#canRequestAds') {
              return allowed;
            }
            if (call.method == 'ConsentInformation#requestConsentInfoUpdate') {
              if (updateFailure) {
                throw PlatformException(
                  code: '2',
                  message: 'synthetic update failure',
                );
              }
              requirement = 1;
              allowed = true;
              return null;
            }
            if (call.method == 'UserMessagingPlatform#showPrivacyOptionsForm') {
              if (formFailure) {
                throw PlatformException(
                  code: '3',
                  message: 'synthetic form failure',
                );
              }
              allowed = false;
              return null;
            }
            throw StateError('Unexpected SDK method');
          });
      addTearDown(
        () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null),
      );
      final gateway = SdkRewardedGateway();
      expect(
        (await gateway.readAdPrivacyState()).requirement,
        AdPrivacyRequirement.unknown,
      );
      expect(calls, [
        'ConsentInformation#getPrivacyOptionsRequirementStatus',
        'ConsentInformation#canRequestAds',
      ]);
      expect(
        (await gateway.updateAdPrivacyState()).requirement,
        AdPrivacyRequirement.required,
      );
      expect(calls.skip(2), [
        'ConsentInformation#requestConsentInfoUpdate',
        'ConsentInformation#getPrivacyOptionsRequirementStatus',
        'ConsentInformation#canRequestAds',
      ]);
      expect((await gateway.showAdPrivacyOptions()).canRequestAds, false);
      formFailure = true;
      await expectLater(
        gateway.showAdPrivacyOptions(),
        throwsA(isA<Exception>()),
      );
      updateFailure = true;
      final beforeFailure = calls.length;
      await expectLater(
        gateway.updateAdPrivacyState(),
        throwsA(isA<Exception>()),
      );
      expect(calls.skip(beforeFailure), [
        'ConsentInformation#requestConsentInfoUpdate',
      ]);
      expect(calls.toSet(), {
        'ConsentInformation#getPrivacyOptionsRequirementStatus',
        'ConsentInformation#canRequestAds',
        'ConsentInformation#requestConsentInfoUpdate',
        'UserMessagingPlatform#showPrivacyOptionsForm',
      });
    },
  );

  for (final configured in [false, true]) {
    testWidgets(
      'privacy entry absent without configured ads and hidden when not required ($configured)',
      (tester) async {
        final gateway = PrivacyGateway()
          ..state = const AdPrivacySnapshot(
            requirement: AdPrivacyRequirement.notRequired,
            canRequestAds: true,
          );
        final client = ClaimClient();
        final manager = managerFor(gateway, client, configured: configured);
        await tester.pumpWidget(
          MaterialApp(
            theme: tideglassTheme(),
            home: ServiceSettings(
              manager: manager,
              onExportHarbor: () async => '{}',
              onImportHarbor: (_) async {},
            ),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('ad-privacy-options')), findsNothing);
        expect(gateway.reads, configured ? 1 : 0);
        expect(gateway.updates, 0);
        expect(gateway.consents, 0);
        expect(gateway.loads, 0);
        await tester.pumpWidget(const SizedBox.shrink());
        manager.dispose();
        client.close();
      },
    );
  }

  for (final coldStart in [false, true]) {
    testWidgets(
      'privacy options reachable at320px200percent; cold check/error/retry $coldStart',
      (tester) async {
        tester.view.physicalSize = const Size(320, 720);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final gateway = PrivacyGateway();
        if (coldStart) {
          gateway.state = const AdPrivacySnapshot(
            requirement: AdPrivacyRequirement.unknown,
            canRequestAds: false,
          );
        }
        final client = ClaimClient();
        final manager = managerFor(gateway, client);
        await tester.pumpWidget(
          MaterialApp(
            theme: tideglassTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: const TextScaler.linear(2)),
              child: child!,
            ),
            home: ServiceSettings(
              manager: manager,
              onExportHarbor: () async => '{}',
              onImportHarbor: (_) async {},
            ),
          ),
        );
        await tester.pumpAndSettle();
        final button = find.byKey(const ValueKey('ad-privacy-options'));
        final scrollable = find
            .descendant(
              of: find.byKey(const ValueKey('services-scroll')),
              matching: find.byType(Scrollable),
            )
            .first;
        Future<void> revealButton() async {
          // Error prose can move this lazy child outside the built viewport.
          // Return through real scroll gestures before locating it again.
          final position = tester.state<ScrollableState>(scrollable).position;
          for (
            var i = 0;
            i < 80 && position.pixels > position.minScrollExtent;
            i++
          ) {
            await tester.drag(scrollable, const Offset(0, 500));
            await tester.pumpAndSettle();
          }
          expect(position.pixels, position.minScrollExtent);
          await tester.scrollUntilVisible(
            button,
            200,
            scrollable: scrollable,
            maxScrolls: 80,
          );
          await tester.ensureVisible(button);
          await tester.pumpAndSettle();
          final rect = tester.getRect(button);
          final viewport = tester.getRect(scrollable);
          expect(rect.width, greaterThanOrEqualTo(48));
          expect(rect.height, greaterThanOrEqualTo(48));
          expect(rect.left, greaterThanOrEqualTo(viewport.left));
          expect(rect.right, lessThanOrEqualTo(viewport.right));
          expect(rect.top, greaterThanOrEqualTo(viewport.top));
          expect(rect.bottom, lessThanOrEqualTo(viewport.bottom));
          for (final point in [
            Alignment.center,
            const Alignment(-.8, -.8),
            const Alignment(.8, -.8),
            const Alignment(-.8, .8),
            const Alignment(.8, .8),
          ]) {
            expect(button.hitTestable(at: point), findsOneWidget);
          }
        }

        await revealButton();
        expect(gateway.updates, 0);
        if (coldStart) {
          gateway.failUpdate = true;
          await tester.tap(button);
          await tester.pumpAndSettle();
          expect(manager.adPrivacyError, 'ad_privacy_unavailable');
          expect(manager.adPrivacyRequirement, AdPrivacyRequirement.unknown);
          expect(gateway.forms, 0);
          gateway.failUpdate = false;
          await revealButton();
          await tester.tap(button);
          await tester.pumpAndSettle();
          expect(manager.adPrivacyRequirement, AdPrivacyRequirement.required);
          expect(manager.adPrivacyError, null);
          expect(gateway.updates, 2);
          expect(gateway.forms, 0);
          await revealButton();
        }
        await tester.tap(button);
        await tester.pumpAndSettle();
        expect(gateway.forms, 1);
        expect(gateway.loads, 0);
        expect(gateway.consents, 0);
        expect(tester.takeException(), null);
        await tester.pumpWidget(const SizedBox.shrink());
        manager.dispose();
        client.close();
      },
    );
  }
}
