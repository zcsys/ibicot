// Deterministic widget captures, not native screenshots or natural pacing.
// From game/mobile: ../../tool/flutter test ../client/design/render_season_test.dart
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
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
  testWidgets('render saved seasonal views for inspection', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final subject = GameController(
      catalogue: catalogue,
      clock: () => DateTime.utc(2026, 10, 16, 12),
      startTicker: false,
      initialState: GameState(
        daily: DailyState(passXpById: {'pass.01': BigInt.from(1500)}),
      ),
    );
    addTearDown(subject.dispose);
    Future<void> show(GameController game, String key) => tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: child!,
        ),
        home: RepaintBoundary(
          key: const ValueKey('capture'),
          child: SeasonScreen(key: ValueKey(key), game: game),
        ),
      ),
    );
    Future<void> capture(String name) async {
      await tester.pumpAndSettle();
      final boundary = tester.renderObject<RenderRepaintBoundary>(
        find.byKey(const ValueKey('capture')),
      );
      await tester.runAsync(() async {
        final directory = Directory('../../release/client-season-proof');
        await directory.create(recursive: true);
        final image = await boundary.toImage();
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        await File('${directory.path}/$name.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    }

    await show(subject, 'live');
    await capture('fleet-phone');
    await tester.tap(find.byKey(const ValueKey('season-tab-1')));
    await capture('pass-phone');
    final reward = find.text('Level 3 · Harbor Lantern');
    await tester.ensureVisible(reward);
    await tester.tap(reward);
    await tester.pumpAndSettle();
    await tester.ensureVisible(reward);
    await capture('reward-preview-phone');
    final contracts = find.byKey(const ValueKey('season-tab-2'));
    await tester.ensureVisible(contracts);
    await tester.tap(contracts);
    await capture('contracts-phone');
    final archive = GameController(
      catalogue: catalogue,
      clock: () => DateTime.utc(2026, 11, 14),
      startTicker: false,
    );
    addTearDown(archive.dispose);
    await show(archive, 'archive');
    await capture('archive-phone');
    expect(tester.takeException(), isNull);
  });
}
