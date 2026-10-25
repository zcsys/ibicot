// Independent actual pushed-route probe. Run from game/mobile, with both
// presentation modes; the author matrix mounts the screen as its root route.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/calibration_pattern.dart';
import 'package:tideglass/calibration_screen.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';

void main() {
  for (final scale in [1.5, 2.0]) {
    testWidgets('actual pushed calibration title and back at $scale', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(320, 720);
      tester.view.devicePixelRatio = 1;
      tester.platformDispatcher.textScaleFactorTestValue = scale;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      final semantics = tester.ensureSemantics();
      addTearDown(semantics.dispose);
      final patterns = List.generate(
        12,
        (i) => CalibrationPattern.fromJson(
          jsonDecode(
            File(
              'assets/calibrations/calibration.${(i + 1).toString().padLeft(2, '0')}.pattern.json',
            ).readAsStringSync(),
          ) as Map<String, dynamic>,
        ),
      );
      var completions = 0;
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: FilledButton(
                  key: const ValueKey('enter-calibration'),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => CalibrationScreen(
                        patterns: patterns,
                        focusCharges: () => 1,
                        collectedIds: () => {},
                        onComplete: (_) {
                          completions++;
                          return true;
                        },
                      ),
                    ),
                  ),
                  child: const Text('Open'),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.byKey(const ValueKey('enter-calibration')));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.byType(BackButton), findsOneWidget);
      final title = find.text(
        Presentation.text(UiEnglish.calibrationConstellationCalibration),
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
      // Use the visible scroll viewport, not the whole screen behind AppBar.
      for (final key in [
        'claim-routed-calibration',
        'claim-accessible-calibration',
      ]) {
        final control = find.byKey(ValueKey(key));
        await Scrollable.ensureVisible(tester.element(control), alignment: .5);
        await tester.pumpAndSettle();
        final rect = tester.getRect(control);
        final viewport = tester.getRect(find.byType(SingleChildScrollView));
        expect(rect.top, greaterThanOrEqualTo(viewport.top - .5));
        expect(rect.bottom, lessThanOrEqualTo(viewport.bottom + .5));
        expect(control.hitTestable(), findsOneWidget);
      }
      expect(
        completions,
        0,
        reason: 'Navigation and scrolling must not spend Focus.',
      );
      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();
      expect(find.byType(CalibrationScreen), findsNothing);
      expect(find.byKey(const ValueKey('enter-calibration')), findsOneWidget);
      expect(completions, 0);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
      expect(tester.binding.transientCallbackCount, 0);
    });
  }
}
