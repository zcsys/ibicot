import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/calibration_pattern.dart';
import 'package:tideglass/calibration_screen.dart';
import 'package:tideglass/palette.dart';

List<CalibrationPattern> allPatterns() => List.generate(
  12,
  (i) => CalibrationPattern.fromJson(
    jsonDecode(
          File(
            'assets/calibrations/calibration.${(i + 1).toString().padLeft(2, '0')}.pattern.json',
          ).readAsStringSync(),
        )
        as Map<String, dynamic>,
  ),
);
List<int>? solve(CalibrationPattern pattern, List<int> path) {
  if (path.length == pattern.stars.length) {
    return path.last == pattern.end ? path : null;
  }
  for (final star in pattern.stars) {
    if (path.contains(star.key) ||
        !pattern.linked(path.last, star.key) ||
        (star.key == pattern.end && path.length != pattern.stars.length - 1)) {
      continue;
    }
    final result = solve(pattern, [...path, star.key]);
    if (result != null) return result;
  }
  return null;
}

void main() {
  for (final pattern in allPatterns()) {
    test(
      '${pattern.id} has a valid route found without reading its solution',
      () {
        final solution = solve(pattern, [pattern.start]);
        expect(solution, isNotNull);
        final route = CalibrationRoute(pattern);
        expect(route.visit(pattern.start), isFalse);
        expect(route.visit(pattern.end), isFalse);
        for (final key in solution!.skip(1)) {
          expect(route.visit(key), isTrue);
        }
        expect(route.solved, isTrue);
        expect(route.visited.toSet().length, pattern.stars.length);
        route.undo();
        expect(route.solved, isFalse);
        route.restart();
        expect(route.visited, [pattern.start]);
      },
    );
  }
  testWidgets(
    'untimed route and crew completion dispatch the identical pattern command once',
    (tester) async {
      final pattern = allPatterns().first;
      final claims = <String>[];
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: CalibrationScreen(
            patterns: [pattern],
            focusCharges: () => 2,
            collectedIds: () => {},
            onComplete: (id) {
              claims.add(id);
              return true;
            },
          ),
        ),
      );
      final solution = solve(pattern, [pattern.start])!;
      for (final key in solution.skip(1)) {
        final button = find.byKey(ValueKey('star-$key'));
        await tester.ensureVisible(button);
        await tester.tap(button);
        await tester.pump();
      }
      final routed = find.byKey(const ValueKey('claim-routed-calibration'));
      await tester.ensureVisible(routed);
      await tester.tap(routed);
      await tester.pump();
      expect(claims, [pattern.id]);
      expect(
        tester
            .widget<OutlinedButton>(
              find.byKey(const ValueKey('claim-accessible-calibration')),
            )
            .onPressed,
        isNull,
      );
      await tester.pumpWidget(const SizedBox());
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: CalibrationScreen(
            patterns: [pattern],
            focusCharges: () => 2,
            collectedIds: () => {},
            onComplete: (id) {
              claims.add(id);
              return true;
            },
          ),
        ),
      );
      final accessible = find.byKey(
        const ValueKey('claim-accessible-calibration'),
      );
      await tester.ensureVisible(accessible);
      await tester.tap(accessible);
      await tester.pump();
      expect(claims, [pattern.id, pattern.id]);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'no stored Focus prevents either route claiming but permits practice',
    (tester) async {
      var claims = 0;
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: CalibrationScreen(
            patterns: allPatterns(),
            focusCharges: () => 0,
            collectedIds: () => {},
            onComplete: (id) {
              claims++;
              return false;
            },
          ),
        ),
      );
      expect(
        tester
            .widget<OutlinedButton>(
              find.byKey(const ValueKey('claim-accessible-calibration')),
            )
            .onPressed,
        isNull,
      );
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const ValueKey('claim-routed-calibration')),
            )
            .onPressed,
        isNull,
      );
      expect(claims, 0);
      expect(tester.takeException(), isNull);
    },
  );
}
