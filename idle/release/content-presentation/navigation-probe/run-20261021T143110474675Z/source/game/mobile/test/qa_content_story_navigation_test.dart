import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';

import 'content_presentation_probe.dart';

void main() {
  testWidgets(
    'current Story route full heading and real back action at large text',
    (tester) async {
      final catalogue = await StoryCatalogue.load();
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 16),
      );
      addTearDown(game.dispose);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      final before = {
        'main': game.state.toJson(),
        'story': game.story.toJson(),
      };
      final probe = ContentProbe(tester);
      await probe.show(StoryScreen(game: game), pushed: true);
      expect(find.byType(BackButton), findsOneWidget);
      expect(tester.getSize(find.byType(AppBar)).height, 56);
      final title = named(UiEnglish.storyTheRestoration);
      expect(title, findsOneWidget);
      expect(tester.getSemantics(title).flagsCollection.isHeader, isTrue);
      expect(tester.getSemantics(title).flagsCollection.namesRoute, isTrue);
      await probe.read('route-title', UiEnglish.storyTheRestoration);
      await probe.checkControl(
        'actual-back',
        find.byType(BackButton),
        tap: true,
      );
      expect(find.text('QA route origin'), findsOneWidget);
      expect(find.byType(StoryScreen), findsNothing);
      expect({
        'main': game.state.toJson(),
        'story': game.story.toJson(),
      }, before);
    },
  );
}
