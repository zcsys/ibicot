import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/service_cosmetics.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

class FixtureCredentials implements CredentialStore {
  final data = <String, String>{};
  @override
  Future<String?> read(String key) async => data[key];
  @override
  Future<void> write(String key, String value) async => data[key] = value;
  @override
  Future<void> delete(String key) async => data.remove(key);
}

class FixtureStore implements StoreGateway {
  final updates = StreamController<List<PurchaseDetails>>.broadcast();
  int buys = 0, restores = 0, completions = 0;
  final products = [
    for (var i = 1; i <= 4; i++)
      ProductDetails(
        id: 'dev.tideglass.cosmetic.0$i',
        title: 'Fixture appearance $i',
        description: 'Test-only offer',
        price: 'TEST ${i + 1},49',
        rawPrice: i + 1.49,
        currencyCode: 'TEST',
      ),
    ProductDetails(
      id: 'dev.tideglass.pass.01',
      title: 'Fixture premium pass',
      description: 'Test-only pass',
      price: 'TEST 9,99',
      rawPrice: 9.99,
      currencyCode: 'TEST',
    ),
    ProductDetails(
      id: 'dev.tideglass.supporter',
      title: 'Fixture supporter',
      description: 'Test-only supporter',
      price: 'WITHHELD 19,99',
      rawPrice: 19.99,
      currencyCode: 'TEST',
    ),
  ];
  @override
  Stream<List<PurchaseDetails>> get purchases => updates.stream;
  @override
  Future<bool> isAvailable() async => true;
  @override
  Future<ProductDetailsResponse> query(Set<String> products) async =>
      ProductDetailsResponse(productDetails: this.products, notFoundIDs: []);
  @override
  Future<bool> buy(ProductDetails product, String accountId) async {
    buys++;
    return true;
  }

  @override
  Future<void> restore(String accountId) async {
    restores++;
  }

  @override
  Future<void> complete(PurchaseDetails purchase) async {
    completions++;
  }

  void emit(PurchaseStatus status) {
    updates.add([
      PurchaseDetails(
        purchaseID: 'fixture-transaction',
        productID: 'dev.tideglass.cosmetic.01',
        verificationData: PurchaseVerificationData(
          localVerificationData: 'fixture',
          serverVerificationData: 'fixture-proof',
          source: 'test',
        ),
        transactionDate: '1000',
        status: status,
      )..pendingCompletePurchase = status == PurchaseStatus.purchased,
    ]);
  }
}

/// This is an explicit verification fixture, never production ownership proof.
class FixtureCommerceClient extends TideglassServiceClient {
  FixtureCommerceClient()
    : super(endpoint: Uri.parse('https://commerce.example.invalid'));
  Set<String> grant = {};
  bool offline = false;
  String seed = 'commerce-fixture';
  int observationAge = 0;
  int verifies = 0;
  @override
  Future<AccountCreated> createAccount({required bool cloudConsent}) async {
    session = ServiceSession(
      accountId: '10000000-0000-4000-8000-000000000001',
      token: 'fixture-secret-token',
      expiresAt: DateTime.utc(2035),
    );
    return AccountCreated(session!, 'fixture-recovery');
  }

  @override
  Future<Map<String, dynamic>> entitlements() async {
    if (offline) throw const ServiceException('service_unavailable');
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    return {
      'account_id': session!.accountId,
      'linked_account_seed': seed,
      'verified_at': now,
      'maximum_verification_age_seconds': 3600,
      'purchases': [
        {
          'product_id': 'dev.tideglass.cosmetic.01',
          'state': 'purchased',
          'verification_id': 'fixture-receipt',
          'updated': now - observationAge,
        },
      ],
      'entitlements': [
        for (final id in grant)
          {'id': id, 'verification_receipt_id': 'fixture-receipt'},
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> verifyPurchase({
    required String platform,
    required String proof,
  }) async {
    verifies++;
    return {
      ...await entitlements(),
      'delivery_state': 'granted_awaiting_acknowledgement',
    };
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  setUpAll(() async => catalogue = await StoryCatalogue.load());
  Future<
    (GameController, NativeServicesManager, FixtureCommerceClient, FixtureStore)
  >
  fixture({int xp = 0, bool signedIn = true}) async {
    final client = FixtureCommerceClient();
    final store = FixtureStore();
    late GameController game;
    final manager = NativeServicesManager(
      client: client,
      credentials: FixtureCredentials(),
      store: store,
      configuration: const NativeServiceConfiguration(commerceEnabled: true),
      platformOverride: 'apple',
      localAccountSeed: () => game.state.daily.accountSeed,
    );
    game = GameController(
      catalogue: catalogue,
      initialState: const TideglassEngine()
          .refreshContracts(
            GameState(
              daily: DailyState(passXpById: {'pass.01': BigInt.from(xp)}),
            ),
            DateTime.utc(2026, 10, 16, 12),
            accountSeed: 'commerce-fixture',
            availableDiscoveryKinds: ['archive'],
          )
          .state,
      clock: () => DateTime.utc(2026, 10, 16, 12),
      startTicker: false,
      verifiedPaidCosmetics: () => verifiedPaidCosmetics(manager, game),
    );
    await manager.initialize();
    if (signedIn) {
      await manager.createAccount(cloudConsent: true);
      await manager.acknowledgeRecoveryCode();
    }
    addTearDown(() async {
      game.dispose();
      manager.dispose();
      await store.updates.close();
    });
    return (game, manager, client, store);
  }

  Future<void> show(
    WidgetTester tester,
    Widget child, {
    bool large = false,
  }) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(
            textScaler: TextScaler.linear(large ? 2 : 1),
            disableAnimations: true,
          ),
          child: child!,
        ),
        home: child,
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, String key) async {
    final finder = find.byKey(ValueKey(key));
    await tester.ensureVisible(finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
  }

  test(
    'paid projection requires fresh bound ownership and exact earned pass levels',
    () async {
      final (game, manager, client, _) = await fixture(xp: 3000);
      expect(verifiedPaidCosmetics(manager, game), isEmpty);
      client.grant = {
        'pass.01',
        'cosmetic.shop.01',
        'soundtrack.01',
        'cosmetic.unknown',
      };
      await manager.refreshOwnership();
      expect(verifiedPaidCosmetics(manager, game), {
        'cosmetic.shop.01',
        'cosmetic.premium_pass.01',
        'cosmetic.premium_pass.02',
      });
      expect(
        () => verifiedPaidCosmetics(manager, game).add('forged'),
        throwsUnsupportedError,
      );
      expect(game.equipCosmetic('cosmetic.premium_pass.02'), isTrue);
      client.seed = 'different-harbor';
      await manager.refreshOwnership();
      expect(verifiedPaidCosmetics(manager, game), isEmpty);
      expect(game.visibleAppearance, isNull);
      expect(game.equipCosmetic('cosmetic.shop.01'), isFalse);
    },
  );
  test(
    'supporter reuses exactly four shop IDs and expired observations grant nothing',
    () async {
      final (game, manager, client, _) = await fixture(xp: 15000);
      client.grant = {
        'pass.01',
        'soundtrack.01',
        for (var i = 1; i <= 4; i++) 'cosmetic.shop.0$i',
      };
      await manager.refreshOwnership();
      expect(verifiedPaidCosmetics(manager, game).length, 14);
      client.observationAge = 3600;
      await manager.refreshOwnership();
      expect(verifiedPaidCosmetics(manager, game), isEmpty);
    },
  );
  test(
    'real returned product metadata maps to known IDs and withholds unfulfilled supporter',
    () async {
      final (_, manager, client, store) = await fixture();
      expect(cosmeticStoreOffers(manager), isEmpty);
      await manager.loadOffers();
      await manager.refreshOwnership();
      final offers = cosmeticStoreOffers(manager);
      expect(offers.length, 5);
      expect(offers.first.localizedPrice, store.products.first.price);
      expect(offers.first.cosmeticIds, {'cosmetic.shop.01'});
      expect(offers.last.cosmeticIds.length, 10);
      expect(
        offers.any((offer) => offer.productId == 'dev.tideglass.supporter'),
        isFalse,
      );
      client.offline = true;
      await expectLater(
        manager.refreshOwnership(),
        throwsA(isA<ServiceException>()),
      );
      expect(cosmeticStoreOffers(manager), isEmpty);
    },
  );
  testWidgets(
    'default unavailable store never invents prices or disables earned collection',
    (tester) async {
      final (game, _, _, _) = await fixture(signedIn: false);
      final manager = NativeServicesManager();
      addTearDown(manager.dispose);
      await show(
        tester,
        CommerceScreen(game: game, manager: manager),
        large: true,
      );
      expect(
        find.textContaining('Online services are not configured'),
        findsWidgets,
      );
      expect(find.byKey(const ValueKey('refresh-commerce')), findsNothing);
      expect(find.textContaining('TEST'), findsNothing);
      expect(
        find.byKey(const ValueKey('supporter-fulfillment-unavailable')),
        findsOneWidget,
      );
      await tap(tester, 'cosmetic-filter-2');
      expect(find.text('First Light Cairn'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'purchase request and pending store response grant nothing and hide repeat purchase',
    (tester) async {
      final (game, manager, _, store) = await fixture();
      await show(
        tester,
        CommerceScreen(game: game, manager: manager),
        large: true,
      );
      await tap(tester, 'refresh-commerce');
      await tap(tester, 'cosmetic-filter-5');
      expect(find.textContaining('TEST 2,49'), findsOneWidget);
      expect(find.textContaining('WITHHELD 19,99'), findsNothing);
      await tap(tester, 'purchase-cosmetic.shop.01-dev.tideglass.cosmetic.01');
      expect(store.buys, 1);
      expect(game.ownedCosmetics, isNot(contains('cosmetic.shop.01')));
      store.emit(PurchaseStatus.pending);
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Waiting for approval or payment'),
        findsOneWidget,
      );
      expect(
        find.byKey(
          const ValueKey('purchase-cosmetic.shop.01-dev.tideglass.cosmetic.01'),
        ),
        findsNothing,
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'failed verified delivery retries without another purchase and exposes verified appearance',
    (tester) async {
      final (game, manager, client, store) = await fixture();
      await show(tester, CommerceScreen(game: game, manager: manager));
      await tap(tester, 'refresh-commerce');
      client.offline = true;
      store.emit(PurchaseStatus.purchased);
      await tester.pumpAndSettle();
      expect(game.ownedCosmetics, isNot(contains('cosmetic.shop.01')));
      expect(
        manager.purchaseStates['dev.tideglass.cosmetic.01'],
        'delivery_needs_retry',
      );
      client.offline = false;
      client.grant = {'cosmetic.shop.01'};
      await tap(tester, 'retry-purchase-delivery');
      expect(game.ownedCosmetics, contains('cosmetic.shop.01'));
      expect(store.buys, 0);
      expect(store.completions, 1);
      await tap(tester, 'cosmetic-filter-5');
      await tap(tester, 'equip-cosmetic.shop.01');
      expect(game.visibleAppearance, 'cosmetic.shop.01');
      client.offline = true;
      await expectLater(
        manager.refreshOwnership(),
        throwsA(isA<ServiceException>()),
      );
      await tester.pumpAndSettle();
      expect(game.visibleAppearance, isNull);
    },
  );
  testWidgets(
    'restore request alone never claims completion or manufactures ownership',
    (tester) async {
      final (game, manager, _, store) = await fixture();
      await show(tester, CommerceScreen(game: game, manager: manager));
      await tap(tester, 'refresh-commerce');
      await tap(tester, 'cosmetic-filter-5');
      await tap(tester, 'restore-cosmetics');
      expect(store.restores, 1);
      expect(game.ownedCosmetics, isEmpty);
      expect(find.textContaining('Restoration requested'), findsWidgets);
      expect(find.textContaining('Restoration check complete'), findsNothing);
    },
  );
  testWidgets(
    'season projects earned verified premium and opens the real collection panel',
    (tester) async {
      final (game, manager, client, _) = await fixture(xp: 1500);
      client.grant = {'pass.01'};
      await manager.refreshOwnership();
      await show(
        tester,
        SeasonScreen(game: game, services: manager, initialTab: 1),
        large: true,
      );
      final level = find.byKey(const PageStorageKey('level-3'));
      await tester.ensureVisible(level);
      await tester.tap(level);
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Available in your harbor collection'),
        findsOneWidget,
      );
      expect(game.story.pass!.claims, isEmpty);
      await tap(tester, 'season-commerce');
      expect(
        find.byKey(const ValueKey('commerce-service-panel')),
        findsOneWidget,
      );
      client.grant = {};
      await manager.refreshOwnership();
      await tester.pumpAndSettle();
      expect(verifiedPaidCosmetics(manager, game), isEmpty);
      expect(tester.takeException(), isNull);
    },
  );
}
