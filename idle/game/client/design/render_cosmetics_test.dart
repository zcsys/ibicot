// Author review/export: actual shared native Canvas geometry, seeded harbor.
// From game/mobile: ../../tool/flutter test ../client/design/render_cosmetics_test.dart
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/cosmetics.dart';
import 'package:tideglass/cosmetic_art.dart';
import 'package:tideglass/cosmetics_screen.dart';
import 'package:tideglass/palette.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    for (final entry in {
      'Roboto': 'Roboto-Regular.ttf',
      'MaterialIcons': 'MaterialIcons-Regular.otf',
    }.entries) {
      final bytes = await File(
        '../../.tooling/flutter/bin/cache/artifacts/material_fonts/${entry.value}',
      ).readAsBytes();
      await (FontLoader(
        entry.key,
      )..addFont(Future.value(ByteData.sublistView(bytes)))).load();
    }
  });
  test(
    'export36 distinct source overlays from the actual equipped renderer',
    () async {
      await Directory('../client/art/cosmetics').create(recursive: true);
      for (final item in cosmeticCatalogue) {
        final recorder = ui.PictureRecorder();
        drawCosmetic(Canvas(recorder), const Size(1280, 776), item.id, 0);
        final picture = recorder.endRecording();
        final image = await picture.toImage(1280, 776);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        await File('../client/art/cosmetics/${item.id}.overlay.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
        picture.dispose();
      }
    },
  );
  testWidgets(
    'render all36 matched full harbor previews and collection views',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(1920, 1600);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetPhysicalSize);
      Future<void> save(Finder finder, String path) async {
        await tester.pumpAndSettle();
        final boundary = tester.renderObject<RenderRepaintBoundary>(finder);
        await tester.runAsync(() async {
          await File(path).parent.create(recursive: true);
          final image = await boundary.toImage(pixelRatio: 1);
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          await File(path).writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
      }

      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: RepaintBoundary(
            key: const ValueKey('contact'),
            child: Scaffold(
              body: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'TIDEGLASS · 36 HARBOR APPEARANCES',
                      style: TextStyle(fontSize: 28),
                    ),
                    const Text(
                      'Original vector geometry · 12 core / 10 free pass / 10 premium pass / 4 shop · author review fixtures',
                      style: TextStyle(fontSize: 14),
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 16,
                      runSpacing: 12,
                      children: [
                        for (final item in cosmeticCatalogue)
                          SizedBox(
                            width: 300,
                            child: Column(
                              children: [
                                RepaintBoundary(
                                  key: ValueKey(item.id),
                                  child: CosmeticPreview(id: item.id),
                                ),
                                const SizedBox(height: 5),
                                Text(
                                  item.title,
                                  style: const TextStyle(fontSize: 14),
                                ),
                                Text(
                                  item.id,
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: TideColors.muted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
      await save(
        find.byKey(const ValueKey('contact')),
        '../../release/art/cosmetics-contact-sheet.png',
      );
      for (final item in cosmeticCatalogue) {
        await save(
          find.byKey(ValueKey(item.id)),
          '../client/art/cosmetics/${item.id}.preview.png',
        );
      }
      tester.view.physicalSize = const Size(390, 844);
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(disableAnimations: true),
            child: child!,
          ),
          home: RepaintBoundary(
            key: const ValueKey('collection'),
            child: CosmeticsScreen(
              ownedIds: {
                'cosmetic.core.chapter.01',
                'cosmetic.free_pass.01',
                'cosmetic.core.decoration.01',
              },
              equippedId: 'cosmetic.free_pass.01',
              equippedDecorationId: 'cosmetic.core.decoration.01',
              onEquip: (_) {},
              onUnequipDecoration: () {},
              notes: 100,
              onBuyDecoration: (_) {},
            ),
          ),
        ),
      );
      await save(
        find.byKey(const ValueKey('collection')),
        '../../release/art/cosmetics-collection-phone.png',
      );
      await tester.tap(find.byKey(const ValueKey('cosmetic-filter-5')));
      await save(
        find.byKey(const ValueKey('collection')),
        '../../release/art/cosmetics-shop-unavailable-phone.png',
      );
      expect(tester.takeException(), isNull);
    },
  );
}
