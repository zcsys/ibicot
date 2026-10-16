// Explicit review renderer, not a golden approval test. Run from game/mobile:
// ../../tool/flutter test ../client/design/render_story_test.dart
// Captures are widget-rendered fixtures; they do not prove native-device quality.
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/harbor_art.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/story_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  testWidgets('render actual story widgets and harbor variations for review', (
    tester,
  ) async {
    final output = Directory('../../release/client-story-proof');
    await tester.runAsync(() => output.create(recursive: true));
    await tester.runAsync(() async {
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
    Future<void> capture(String name) async {
      await tester.pumpAndSettle();
      final boundary = tester.renderObject<RenderRepaintBoundary>(
        find.byKey(const ValueKey('capture')),
      );
      await tester.runAsync(() async {
        final image = await boundary.toImage();
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        await File('${output.path}/$name.png')
            .writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    }

    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1600, 1700);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        home: RepaintBoundary(
          key: const ValueKey('capture'),
          child: Scaffold(
            body: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Tideglass · Harbor restoration and decoration review',
                    style: TextStyle(fontSize: 28),
                  ),
                  const Text(
                    'Original vector art · fixture views · not native screenshots',
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 16,
                    runSpacing: 16,
                    children: [
                      for (var stage = 0; stage <= 6; stage++)
                        SizedBox(
                          width: 370,
                          child: Column(
                            children: [
                              HarborArt(
                                counts: const [25, 25, 10, 10, 1],
                                phase: 0,
                                restoration: stage,
                              ),
                              Text('Restoration $stage / 6'),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 28),
                  const Text(
                    'Six optional decorations · preview on restored harbor',
                    style: TextStyle(fontSize: 24),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 16,
                    runSpacing: 16,
                    children: [
                      for (var item = 1; item <= 6; item++)
                        SizedBox(
                          width: 490,
                          child: Column(
                            children: [
                              HarborArt(
                                counts: const [25, 25, 10, 10, 1],
                                phase: 0,
                                restoration: 6,
                                decoration:
                                    'cosmetic.core.decoration.${item.toString().padLeft(2, '0')}',
                              ),
                              Text(
                                [
                                  'Beacon pennants',
                                  'Glass buoys',
                                  'Aurora kite',
                                  'Tide rings',
                                  'Shore garden',
                                  'Returning comets',
                                ][item - 1],
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
    await capture('harbor-contact-sheet');
    final definition = catalogue.dossiers[8];
    final subject = GameController(
      initialState: GameState(surveyNotes: BigInt.from(100)),
      initialStory: StoryProgress(
        campaign: CampaignProgress(
          completed: {'chapter.01', 'chapter.02', 'chapter.03'},
        ),
        dossiers: DossierCollection(
          owned: {definition.id},
          active: ChallengeEconomy(definition).newRun(),
        ),
      ),
      catalogue: catalogue,
      clock: () => DateTime.utc(2026, 10, 16),
      startTicker: false,
    );
    addTearDown(subject.dispose);
    tester.view.physicalSize = const Size(390, 844);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: child!,
        ),
        home: RepaintBoundary(
          key: const ValueKey('capture'),
          child: StoryScreen(game: subject),
        ),
      ),
    );
    await capture('campaign-phone');
    for (var tab = 1; tab <= 3; tab++) {
      final choice = find.byKey(ValueKey('story-tab-$tab'));
      await tester.ensureVisible(choice);
      await tester.tap(choice);
      await capture(
        ['', 'passage-phone', 'archive-phone', 'decorations-phone'][tab],
      );
    }
    expect(tester.takeException(), isNull);
  });
}
