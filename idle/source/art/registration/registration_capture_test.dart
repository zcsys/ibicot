import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/harbor_art.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/story_state.dart';

// Host-only export harness. Production renders these exact widgets directly;
// generated PNGs are registration/review exports, not substitutes for native QA.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const root = '../..'; // Execute from game/mobile, through the shared lane.
  final captures = <Map<String, Object?>>[];

  test('export exact current HelpContent values without re-parsing Dart', () {
    final topics = {
      'asset.support.help': [HelpTopic.play, HelpTopic.rechart, HelpTopic.away, HelpTopic.notes],
      'asset.support.recovery_guide': [HelpTopic.recovery],
      'asset.support.release_notes': [HelpTopic.releaseNotes],
      'asset.support.credits': [HelpTopic.credits],
    };
    final values = <String, Object?>{};
    for (final entry in topics.entries) {
      values[entry.key] = {
        'schema_version': 1,
        'asset_id': entry.key,
        'locale': 'en-US',
        'runtime_source': 'game/mobile/lib/help_content.dart',
        'runtime_selector': entry.value.map((t) => 'HelpTopic.${t.name}').toList(),
        'handbook_title': HelpCopy.title,
        'handbook_intro': HelpCopy.intro,
        'development_notice': HelpCopy.developmentNotice,
        'articles': [
          for (final topic in entry.value)
            {
              'topic': topic.name,
              'title': HelpContent.article(topic).title,
              'summary': HelpContent.article(topic).summary,
              'sections': [
                for (final section in HelpContent.article(topic).sections)
                  {'id': section.id, 'title': section.title, 'paragraphs': section.paragraphs},
              ],
              'actions': [
                for (final action in HelpContent.article(topic).actions)
                  {'id': action.name, 'label': HelpCopy.action(action)},
              ],
            },
        ],
      };
    }
    final out = File('$root/source/art/registration/help-runtime-extract.json');
    out.parent.createSync(recursive: true);
    out.writeAsStringSync('${const JsonEncoder.withIndent('  ').convert(values)}\n');
    expect(values.length, 4);
  });

  Future<void> loadFonts(WidgetTester tester) async {
    await tester.runAsync(() async {
      for (final entry in {'Roboto': 'Roboto-Regular.ttf', 'MaterialIcons': 'MaterialIcons-Regular.otf'}.entries) {
        final file = File('$root/.tooling/flutter/bin/cache/artifacts/material_fonts/${entry.value}');
        await (FontLoader(entry.key)..addFont(file.readAsBytes().then(ByteData.sublistView))).load();
      }
    });
  }

  Future<List<int>> capture(WidgetTester tester, GlobalKey key, String path, Map<String, Object?> inputs) async {
    final boundary = key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
    late List<int> bytes;
    await tester.runAsync(() async {
      final image = await boundary.toImage(pixelRatio: 1);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      bytes = data!.buffer.asUint8List();
      final file = File('$root/$path');
      await file.parent.create(recursive: true);
      await file.writeAsBytes(bytes);
      captures.add({'path': path, 'width': image.width, 'height': image.height, 'inputs': inputs, 'renderer': 'Flutter host widget test', 'native_device_acceptance': false});
      image.dispose();
    });
    return bytes;
  }

  testWidgets('export all seven actual harbor restoration states and bounded viewport samples', (tester) async {
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await loadFonts(tester);
    final signatures = <String>{};
    const counts = [1, 1, 1, 1, 1];
    for (var restoration = 0; restoration <= 6; restoration++) {
      final id = restoration == 0 ? 'harbor.unlit' : 'harbor.restored.${restoration.toString().padLeft(2, '0')}';
      for (final variant in [
        {'name': 'default', 'width': 640.0, 'height': 388.0, 'phase': 0.25, 'reducedMotion': false},
        {'name': 'reduced-motion', 'width': 640.0, 'height': 388.0, 'phase': 0.0, 'reducedMotion': true},
        {'name': 'small-phone', 'width': 320.0, 'height': 194.0, 'phase': 0.0, 'reducedMotion': true},
        {'name': 'tablet', 'width': 1024.0, 'height': 621.0, 'phase': 0.0, 'reducedMotion': true},
      ]) {
        tester.view.physicalSize = Size(variant['width']! as double, variant['height']! as double);
        final key = GlobalKey();
        await tester.pumpWidget(MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: tideglassTheme(),
          builder: (context, child) => MediaQuery(data: MediaQuery.of(context).copyWith(disableAnimations: variant['reducedMotion']! as bool, textScaler: TextScaler.noScaling), child: child!),
          home: RepaintBoundary(key: key, child: HarborArt(counts: counts, phase: variant['phase']! as double, restoration: restoration)),
        ));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull, reason: '$id ${variant['name']}');
        final bytes = await capture(tester, key, 'game/assets/harbor/exports/$id.${variant['name']}.png', {
          'asset_id': 'asset.$id', 'restoration': restoration, 'counts': counts, 'decoration': null, 'phase': variant['phase'], 'reduced_motion': variant['reducedMotion'], 'text_scale': 1, 'viewport': [variant['width'], variant['height']],
        });
        if (variant['name'] == 'reduced-motion') signatures.add(base64Encode(bytes));
      }
    }
    expect(signatures.length, 7, reason: 'All seven authored restoration states have distinct actual pixels at fixed fleet/phase.');
  });

  testWidgets('export actual seasonal fleet and pass presentation with synthetic local state', (tester) async {
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await loadFonts(tester);
    final catalogue = await StoryCatalogue.load();
    final now = DateTime.utc(2026, 10, 21, 12);
    final game = GameController(catalogue: catalogue, clock: () => now, startTicker: false);
    addTearDown(game.dispose);
    for (final variant in [
      {'name': 'fleet-small-phone', 'width': 320.0, 'height': 720.0, 'textScale': 1.0, 'tab': 0},
      {'name': 'fleet-small-phone-large-text', 'width': 320.0, 'height': 720.0, 'textScale': 2.0, 'tab': 0},
      {'name': 'fleet-tablet', 'width': 1024.0, 'height': 768.0, 'textScale': 1.0, 'tab': 0},
      {'name': 'pass-preview', 'width': 640.0, 'height': 900.0, 'textScale': 1.0, 'tab': 1},
    ]) {
      tester.view.physicalSize = Size(variant['width']! as double, variant['height']! as double);
      final key = GlobalKey();
      await tester.pumpWidget(MaterialApp(
        key: UniqueKey(),
        debugShowCheckedModeBanner: false,
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(data: MediaQuery.of(context).copyWith(disableAnimations: true, textScaler: TextScaler.linear(variant['textScale']! as double)), child: child!),
        home: RepaintBoundary(key: key, child: SeasonScreen(game: game, initialTab: variant['tab']! as int)),
      ));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull, reason: variant['name']! as String);
      await capture(tester, key, 'game/assets/season_presentation/exports/season.01.${variant['name']}.png', {
        'asset_id': 'asset.season.01.presentation', 'synthetic_now_utc': now.toIso8601String(), 'season_phase': game.story.season!.phase.name, 'counts': game.story.season!.fleet.counts, 'claimed_milestones': game.story.season!.claimedMilestones.length, 'text_scale': variant['textScale'], 'reduced_motion': true, 'phase': 0, 'tab': variant['tab'], 'viewport': [variant['width'], variant['height']], 'paid_ownership': false,
      });
    }
    // A small exact-render thumbnail from the same runtime harbor composition.
    // Its catalog use is not yet implemented or claimed accepted.
    tester.view.physicalSize = const Size(256, 155);
    final thumb = GlobalKey();
    await tester.pumpWidget(MaterialApp(home: RepaintBoundary(key: thumb, child: HarborArt(counts: game.story.season!.fleet.counts, phase: 0, restoration: game.story.season!.claimedMilestones.length))));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await capture(tester, thumb, 'game/assets/season_presentation/exports/season.01.thumbnail.png', {'asset_id': 'asset.season.01.presentation', 'component': 'SeasonScreen HarborArt', 'counts': game.story.season!.fleet.counts, 'restoration': game.story.season!.claimedMilestones.length, 'phase': 0, 'text_scale': 1, 'reduced_motion': true, 'viewport': [256, 155], 'runtime_thumbnail_route': null});
    final out = File('$root/source/art/registration/capture-manifest.json');
    await tester.runAsync(() async {
      await out.writeAsString('${const JsonEncoder.withIndent('  ').convert({'schema_version': 1, 'purpose': 'Bounded host exports from actual current widgets; not device/native/physical or complete contract acceptance', 'captures': captures})}\n');
    });
    expect(captures.length, 33);
  });
}
