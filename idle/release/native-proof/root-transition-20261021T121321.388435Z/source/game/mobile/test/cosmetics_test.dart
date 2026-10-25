import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/cosmetics.dart';
import 'package:tideglass/cosmetic_art.dart';
import 'package:tideglass/cosmetics_screen.dart';
import 'package:tideglass/palette.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'catalogue exactly matches the fixed 36 manifest identities and pass names',
    () {
      final manifest =
          jsonDecode(
                File(
                  '../../implementation/content/launch_manifest.json',
                ).readAsStringSync(),
              )
              as Map;
      expect(
        cosmeticCatalogue.map((c) => c.id).toSet(),
        (manifest['cosmetics'] as List).map((c) => c['id']).toSet(),
      );
      expect(cosmeticCatalogue.length, 36);
      expect(
        cosmeticCatalogue
            .where((c) => c.source == CosmeticSource.chapter)
            .length,
        6,
      );
      expect(
        cosmeticCatalogue
            .where((c) => c.source == CosmeticSource.decoration)
            .length,
        6,
      );
      expect(
        cosmeticCatalogue
            .where((c) => c.source == CosmeticSource.freePass)
            .length,
        10,
      );
      expect(
        cosmeticCatalogue
            .where((c) => c.source == CosmeticSource.premiumPass)
            .length,
        10,
      );
      expect(
        cosmeticCatalogue.where((c) => c.source == CosmeticSource.shop).length,
        4,
      );
      final season =
          jsonDecode(File('assets/events/season.01.json').readAsStringSync())
              as Map;
      for (final reward in season['rewards'] as List) {
        if (reward['kind'] == 'cosmetic') {
          expect(cosmeticById(reward['content_id']).title, reward['title']);
        }
      }
      expect(
        () => cosmeticCatalogue.add(cosmeticCatalogue.first),
        throwsUnsupportedError,
      );
      expect(() => cosmeticById('cosmetic.unknown'), throwsArgumentError);
    },
  );
  test(
    'all36 overlays have distinct nonempty actual rendered geometry',
    () async {
      final signatures = <String>{};
      for (final item in cosmeticCatalogue) {
        final recorder = ui.PictureRecorder();
        drawCosmetic(Canvas(recorder), const Size(640, 388), item.id, 0);
        final picture = recorder.endRecording();
        final image = await picture.toImage(640, 388);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final rgba = (await image.toByteData(
          format: ui.ImageByteFormat.rawRgba,
        ))!.buffer.asUint8List();
        var painted = 0;
        for (var i = 3; i < rgba.length; i += 4) {
          if (rgba[i] != 0) {
            painted++;
          }
        }
        expect(painted, greaterThan(200), reason: item.id);
        signatures.add(base64Encode(bytes!.buffer.asUint8List()));
        image.dispose();
        picture.dispose();
      }
      expect(signatures.length, 36);
    },
  );
  test(
    'offer metadata and displayed ownership are immutable and validated',
    () {
      final ids = {'cosmetic.shop.01'};
      final offer = CosmeticStoreOffer(
        productId: 'test.store.fixture',
        productTitle: 'Fixture product',
        localizedPrice: 'TEST 4.99',
        cosmeticIds: ids,
      );
      ids.add('cosmetic.shop.02');
      expect(offer.cosmeticIds, {'cosmetic.shop.01'});
      expect(
        () => offer.cosmeticIds.add('cosmetic.shop.03'),
        throwsUnsupportedError,
      );
      expect(
        () => CosmeticStoreOffer(
          productId: '',
          productTitle: 'Fixture',
          localizedPrice: 'TEST',
          cosmeticIds: {'cosmetic.shop.01'},
        ),
        throwsArgumentError,
      );
      expect(
        () => CosmeticsScreen(
          ownedIds: {},
          equippedId: 'cosmetic.shop.01',
          onEquip: (_) {},
        ),
        throwsArgumentError,
      );
    },
  );
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
            disableAnimations: true,
            textScaler: TextScaler.linear(large ? 2 : 1),
          ),
          child: child!,
        ),
        home: child,
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, Finder finder) async {
    await tester.ensureVisible(finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
  }

  testWidgets('owned appearances equip through callback and can be removed', (
    tester,
  ) async {
    String? equipped;
    await show(
      tester,
      StatefulBuilder(
        builder: (context, refresh) => CosmeticsScreen(
          ownedIds: {'cosmetic.core.chapter.01'},
          equippedId: equipped,
          onEquip: (id) => refresh(() => equipped = id),
        ),
      ),
    );
    await tap(
      tester,
      find.byKey(const ValueKey('equip-cosmetic.core.chapter.01')),
    );
    expect(equipped, 'cosmetic.core.chapter.01');
    await tap(tester, find.byKey(const ValueKey('remove-appearance')));
    expect(equipped, isNull);
  });
  testWidgets(
    'unavailable paid previews never synthesize a price or purchase action',
    (tester) async {
      await show(
        tester,
        CosmeticsScreen(
          ownedIds: {},
          equippedId: null,
          onEquip: (_) {},
          commerceUnavailableReason: 'Store verification is unavailable.',
        ),
        large: true,
      );
      await tap(tester, find.byKey(const ValueKey('cosmetic-filter-5')));
      expect(find.text('Tidal Clock'), findsOneWidget);
      expect(find.text('Store verification is unavailable.'), findsWidgets);
      expect(
        find.byWidgetPredicate(
          (w) =>
              w.key is ValueKey<String> &&
              (w.key as ValueKey<String>).value.startsWith('purchase-'),
        ),
        findsNothing,
      );
      expect(find.byKey(const ValueKey('restore-cosmetics')), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'localized offered purchase delegates without optimistic ownership',
    (tester) async {
      final offer = CosmeticStoreOffer(
        productId: 'test.supporter.fixture',
        productTitle: 'Fixture Supporter Bundle',
        localizedPrice: 'TEST 4.99',
        cosmeticIds: {for (var i = 1; i <= 4; i++) 'cosmetic.shop.0$i'},
      );
      CosmeticStoreOffer? received;
      var equipped = false;
      await show(
        tester,
        CosmeticsScreen(
          ownedIds: {},
          equippedId: null,
          onEquip: (_) => equipped = true,
          offers: [offer],
          onPurchase: (value) async {
            received = value;
          },
        ),
      );
      await tap(tester, find.byKey(const ValueKey('cosmetic-filter-5')));
      await tap(
        tester,
        find.byKey(
          const ValueKey('purchase-cosmetic.shop.01-test.supporter.fixture'),
        ),
      );
      expect(identical(received, offer), isTrue);
      expect(equipped, isFalse);
      expect(
        find.byKey(const ValueKey('equip-cosmetic.shop.01')),
        findsNothing,
      );
    },
  );
  testWidgets(
    'restoration delegates and does not create local paid ownership',
    (tester) async {
      var restores = 0;
      await show(
        tester,
        CosmeticsScreen(
          ownedIds: {},
          equippedId: null,
          onEquip: (_) {},
          onRestore: () async {
            restores++;
          },
        ),
      );
      await tap(tester, find.byKey(const ValueKey('cosmetic-filter-1')));
      await tap(tester, find.byKey(const ValueKey('restore-cosmetics')));
      expect(restores, 1);
      expect(find.text('0 of 36 appearances kept'), findsOneWidget);
    },
  );
  testWidgets(
    'decoration affordability and separate removal callbacks are real',
    (tester) async {
      var buys = 0, removals = 0;
      await show(
        tester,
        CosmeticsScreen(
          ownedIds: {'cosmetic.core.decoration.02'},
          equippedId: null,
          equippedDecorationId: 'cosmetic.core.decoration.02',
          onEquip: (_) {},
          onUnequipDecoration: () => removals++,
          notes: 49,
          onBuyDecoration: (_) => buys++,
        ),
      );
      await tap(tester, find.byKey(const ValueKey('cosmetic-filter-2')));
      final buy = find.byKey(
        const ValueKey('acquire-cosmetic.core.decoration.01'),
      );
      expect(tester.widget<OutlinedButton>(buy).onPressed, isNull);
      await tap(
        tester,
        find.byKey(const ValueKey('remove-collection-decoration')),
      );
      expect(removals, 1);
      expect(buys, 0);
    },
  );
  testWidgets(
    'all36 previews and their expanded view fit320px200percent text',
    (tester) async {
      await show(
        tester,
        CosmeticsScreen(ownedIds: {}, equippedId: null, onEquip: (_) {}),
        large: true,
      );
      expect(find.byType(CosmeticPreview), findsNWidgets(36));
      await tap(
        tester,
        find
            .byWidgetPredicate(
              (widget) => widget is InkWell && widget.child is ExcludeSemantics,
            )
            .first,
      );
      expect(find.text('Back to collection'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
