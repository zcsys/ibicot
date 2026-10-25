import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/calibration_screen.dart';
import 'package:tideglass/cosmetics.dart';
import 'package:tideglass/cosmetics_screen.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/notification_settings.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'calibration_test.dart' show allPatterns;
import 'notification_service_test.dart'
    show FixtureNotificationGateway, MemoryReminderStore;

void main() {
  testWidgets('capture actual critical screens at 320px and 200% text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.runAsync(() async {
      // Flutter's bundled fonts are loaded explicitly in host screenshots.
      for (final entry in {
        'Roboto': 'Roboto-Regular.ttf',
        'MaterialIcons': 'MaterialIcons-Regular.otf',
      }.entries) {
        final font = File(
          '../../.tooling/flutter/bin/cache/artifacts/material_fonts/${entry.value}',
        );
        await (FontLoader(
          entry.key,
        )..addFont(font.readAsBytes().then(ByteData.sublistView))).load();
      }
    });
    final boundaryKey = GlobalKey();
    Future<void> show(Widget screen, {bool app = false}) async {
      await tester.pumpWidget(
        RepaintBoundary(
          key: boundaryKey,
          child: app
              ? screen
              : MaterialApp(
                  debugShowCheckedModeBanner: false,
                  theme: tideglassTheme(),
                  home: screen,
                ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }

    Future<void> capture(String name) async {
      final boundary =
          boundaryKey.currentContext!.findRenderObject()!
              as RenderRepaintBoundary;
      await tester.runAsync(() async {
        final image = await boundary.toImage(pixelRatio: 2);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final file = File(
          '../../release/localization-proof/${Presentation.pseudoEnabled ? 'pseudo' : 'english'}-$name.png',
        );
        await file.parent.create(recursive: true);
        await file.writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    }

    final game = GameController(
      startTicker: false,
      initialState: GameState(
        counts: [40, 12, 0, 0, 0],
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
        walletMicros: BigInt.from(1000000000),
      ),
    );
    addTearDown(game.dispose);
    await show(
      TideglassApp(
        controller: game,
        initialPreferences: const ClientPreferences(
          reduceMotion: true,
          onboardingDismissed: true,
        ),
      ),
      app: true,
    );
    await capture('harbor');
    await tester.tap(find.byType(NavigationDestination).at(1));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const ValueKey('preview-rechart')));
    await tester.tap(find.byKey(const ValueKey('preview-rechart')));
    await tester.pumpAndSettle();
    await capture('rechart');
    await show(
      CalibrationScreen(
        patterns: [allPatterns().first],
        focusCharges: () => 1,
        collectedIds: () => {},
        onComplete: (_) => true,
      ),
    );
    await capture('calibration');
    await show(
      CosmeticsScreen(
        ownedIds: {},
        equippedId: null,
        onEquip: (_) {},
        offers: [
          CosmeticStoreOffer(
            productId: 'fixture',
            productTitle: 'Store offer',
            localizedPrice: 'USD 9.99',
            cosmeticIds: {'cosmetic.shop.01'},
          ),
        ],
        onPurchase: (_) async {},
      ),
    );
    await tester.ensureVisible(find.byKey(const ValueKey('cosmetic-filter-5')));
    await tester.tap(find.byKey(const ValueKey('cosmetic-filter-5')));
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const ValueKey('purchase-cosmetic.shop.01-fixture')),
    );
    await tester.pumpAndSettle();
    await capture('store-price');
    final reminders = NotificationService(
      gateway: FixtureNotificationGateway(),
      store: MemoryReminderStore(),
    );
    addTearDown(reminders.dispose);
    await reminders.initialize();
    await show(
      Scaffold(
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: NotificationSettings(service: reminders),
        ),
      ),
    );
    await tester.ensureVisible(
      find.byKey(const ValueKey('reminder-quiet-start')),
    );
    await tester.tap(find.byKey(const ValueKey('reminder-quiet-start')));
    await tester.pumpAndSettle();
    await capture('quiet-time');
    expect(tester.takeException(), isNull);
  });
}
