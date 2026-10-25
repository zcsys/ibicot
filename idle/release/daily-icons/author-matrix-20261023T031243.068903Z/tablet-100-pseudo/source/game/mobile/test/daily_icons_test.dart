import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/daily_icon_label.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';

import 'content_presentation_probe.dart';

void main() {
  testWidgets(
    'daily icons retain complete labels, states and actual controls',
    (tester) async {
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      final now = DateTime.utc(2026, 10, 16, 12);
      const engine = TideglassEngine();
      final initial = engine
          .refreshContracts(
            GameState(
              focusCharges: 10,
              focusRemainingMicros: BigInt.from(1200000000),
              completedSurveys: 3,
            ),
            now,
            accountSeed: 'daily-icon-proof',
            availableDiscoveryKinds: ['archive'],
          )
          .state;
      final game = GameController(
        initialState: initial,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(game.dispose);
      final p = ContentProbe(tester);
      await p.show(
        TideglassApp(
          controller: game,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
        app: true,
      );
      await p.checkControl(
        'journal',
        find.byType(NavigationDestination).at(2),
        tap: true,
      );
      final before = game.state.toJson(), storyBefore = game.story.toJson();
      final expected = <String, IconData>{
        UiCopy.focusStored: Icons.auto_awesome_outlined,
        UiCopy.surveysComplete: Icons.explore_outlined,
        UiEnglish.dailyCrewContracts: Icons.assignment_outlined,
      };
      expect(find.byType(DailyIconLabel), findsNWidgets(3));
      for (final entry in expected.entries) {
        final heading = find.byWidgetPredicate(
          (widget) => widget is DailyIconLabel && widget.label == entry.key,
        );
        expect(heading, findsOneWidget);
        final icon = find.descendant(
          of: heading,
          matching: find.byIcon(entry.value),
        );
        expect(icon, findsOneWidget);
        final excluded = find
            .ancestor(of: icon, matching: find.byType(ExcludeSemantics))
            .first;
        expect(tester.widget<ExcludeSemantics>(excluded).excluding, isTrue);
        await Scrollable.ensureVisible(tester.element(icon), alignment: .5);
        await tester.pumpAndSettle();
        final rendered = tester.renderObject(icon);
        p.inside(tester.getRect(icon), p.visible(rendered), entry.key);
        await p.read(entry.key, entry.key, within: heading);
        final text = find.descendant(
          of: heading,
          matching: find.text(Presentation.text(entry.key)),
        );
        expect(
          tester.getSemantics(text).getSemanticsData().label,
          contains(Presentation.text(entry.key)),
        );
      }
      expect(game.state.toJson(), before);
      expect(game.story.toJson(), storyBefore);
      await p.read('stored-focus', '10 / 12');
      await p.read('stored-surveys', '3 / 3');
      await p.checkControl(
        'focus-route',
        find.byKey(const ValueKey('activate-focus')),
      );
      final contract = game.state.dailyContracts.first;
      await p.checkControl(
        'pending-contract',
        find.byKey(ValueKey('claim-${contract.id}')),
        enabled: false,
      );
      await p.checkControl(
        'collect-surveys',
        find.byKey(const ValueKey('collect-surveys')),
        tap: true,
      );
      expect(game.state.completedSurveys, 0);
      expect(game.state.surveyNotes, BigInt.from(30));
      expect(game.state.focusCharges, 10);
      expect(game.state.focusRemainingMicros, BigInt.from(1200000000));
      await p.read('empty-surveys', '0 / 3');
      await p.checkControl(
        'empty-survey-control',
        find.byKey(const ValueKey('collect-surveys')),
        enabled: false,
      );
      expect(game.story.toJson(), storyBefore);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
