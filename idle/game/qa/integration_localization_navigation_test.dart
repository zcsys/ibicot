// Independent real Navigator routes, distinct from root-mounted author matrices.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/help_screen.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/public_links.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';

void main() {
  late StoryCatalogue catalogue;
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  for (final scale in [1.5, 2.0]) {
    for (final name in ['help', 'season']) {
      testWidgets('pushed $name route keeps full title and back at $scale', (
        tester,
      ) async {
        tester.view.physicalSize = const Size(320, 720);
        tester.view.devicePixelRatio = 1;
        tester.platformDispatcher.textScaleFactorTestValue = scale;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
        final game = GameController(
          catalogue: catalogue,
          clock: () => DateTime.utc(2026, 10, 16, 12),
          startTicker: false,
        );
        addTearDown(game.dispose);
        final before = jsonEncode({
          'main': game.state.toJson(),
          'story': game.story.toJson(),
        });
        var links = 0;
        final screen = name == 'help'
            ? HelpScreen(
                publicLinks: PublicLinksConfig(),
                publicPageLauncher: (_) async {
                  links++;
                  return true;
                },
              )
            : SeasonScreen(game: game);
        await tester.pumpWidget(
          MaterialApp(
            theme: tideglassTheme(),
            home: Builder(
              builder: (context) => Scaffold(
                body: Center(
                  child: FilledButton(
                    key: const ValueKey('qa-open'),
                    onPressed: () => Navigator.of(context)
                        .push(MaterialPageRoute<void>(builder: (_) => screen)),
                    child: const Text('Open'),
                  ),
                ),
              ),
            ),
          ),
        );
        await tester.tap(find.byKey(const ValueKey('qa-open')));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        expect(find.byType(BackButton), findsOneWidget);
        final title = find.text(
          Presentation.text(
            name == 'help' ? HelpCopy.title : UiEnglish.seasonReturningStars,
          ),
        );
        expect(title, findsOneWidget);
        if (scale > 1.5) {
          final heading = find.ancestor(
            of: title,
            matching: find.byWidgetPredicate(
              (w) =>
                  w is Semantics &&
                  w.properties.header == true &&
                  w.properties.namesRoute == true,
            ),
          );
          expect(heading, findsOneWidget);
          expect(tester.getSemantics(heading).flagsCollection.isHeader, isTrue);
          expect(tester.widget<Text>(title).maxLines, isNull);
          expect(
            find.ancestor(
              of: title,
              matching: find.byType(SingleChildScrollView),
            ),
            findsOneWidget,
          );
          expect(tester.getSize(find.byType(AppBar)).height, kToolbarHeight);
        }
        Future<void> tapVisible(Finder control) async {
          await Scrollable.ensureVisible(
            tester.element(control),
            alignment: .5,
          );
          await tester.pumpAndSettle();
          final rect = tester.getRect(control),
              viewport = tester.getRect(
                find.byType(SingleChildScrollView).last,
              );
          expect(rect.width, greaterThanOrEqualTo(48));
          expect(rect.height, greaterThanOrEqualTo(48));
          expect(rect.top, greaterThanOrEqualTo(viewport.top - .5));
          expect(rect.bottom, lessThanOrEqualTo(viewport.bottom + .5));
          expect(rect.left, greaterThanOrEqualTo(viewport.left - .5));
          expect(rect.right, lessThanOrEqualTo(viewport.right + .5));
          for (final point in [
            Alignment.center,
            const Alignment(-.98, 0),
            const Alignment(.98, 0),
            const Alignment(0, -.98),
            const Alignment(0, .98),
          ]) {
            expect(control.hitTestable(at: point), findsOneWidget);
          }
          await tester.tap(control);
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        }

        if (name == 'help') {
          await tapVisible(find.byKey(const ValueKey('help-topic-recovery')));
          expect(
            find.byKey(const ValueKey('help-scroll-recovery')),
            findsOneWidget,
          );
          if (scale > 1.5) {
            final recovery = find.byKey(const ValueKey('help-scroll-heading'));
            expect(
              tester
                  .widget<Text>(
                    find.descendant(of: recovery, matching: find.byType(Text)),
                  )
                  .maxLines,
              isNull,
            );
          }
          await tester.tap(find.byType(BackButton));
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('help-scroll-index')),
            findsOneWidget,
          );
        } else {
          await tapVisible(find.byKey(const ValueKey('season-tab-1')));
          expect(find.byKey(const PageStorageKey('level-1')), findsOneWidget);
        }
        await tester.tap(find.byType(BackButton));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('qa-open')), findsOneWidget);
        expect(
          jsonEncode({
            'main': game.state.toJson(),
            'story': game.story.toJson(),
          }),
          before,
        );
        expect(links, 0);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox());
        await tester.pumpAndSettle();
        expect(tester.binding.transientCallbackCount, 0);
      });
    }
  }
}
