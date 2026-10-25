import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/font_licenses.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';
import 'content_presentation_probe.dart';
import 'qa_rechart_forecast_review_test.dart' as reset_probe;

final observed = <Map<String, Object?>>[];
Future<void> readRaw(
  WidgetTester tester,
  ContentProbe p,
  String display,
) async {
  final finder = find.text(display);
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      240,
      scrollable: find.byType(Scrollable).last,
      maxScrolls: 300,
    );
    await tester.pumpAndSettle();
  }
  expect(finder, findsOneWidget);
  final rich = find.descendant(of: finder, matching: find.byType(RichText));
  expect(rich, findsOneWidget);
  final paragraph = tester.renderObject<RenderParagraph>(rich);
  expect(paragraph.text.toPlainText(), display);
  expect(paragraph.didExceedMaxLines, false);
  final lines = <String, Rect>{};
  for (final word in RegExp(r'\S+').allMatches(display)) {
    final boxes = paragraph.getBoxesForSelection(
      TextSelection(baseOffset: word.start, extentOffset: word.end),
    );
    expect(boxes, isNotEmpty);
    for (final box in boxes) {
      final id = '${box.top}:${box.bottom}';
      lines[id] = lines[id]?.expandToInclude(box.toRect()) ?? box.toRect();
    }
  }
  final rects = <Map<String, Object?>>[];
  for (final line in lines.values) {
    paragraph.showOnScreen(rect: line, duration: Duration.zero);
    await tester.pumpAndSettle();
    final r = MatrixUtils.transformRect(paragraph.getTransformTo(null), line),
        v = p.visible(paragraph);
    p.inside(r, v, 'bundled legal notice glyph');
    rects.add({
      'rect': [r.left, r.top, r.right, r.bottom],
      'viewport': [v.left, v.top, v.right, v.bottom],
    });
  }
  observed.add({
    'text': display,
    'complete': true,
    'untruncated': true,
    'lines': rects,
  });
}

void main() {
  testWidgets(
    'real Settings Help Credits route exposes every bundled icon notice paragraph',
    (tester) async {
      reset_probe.setup(tester);
      await reset_probe.fonts(tester);
      registerFontLicenses();
      registerFontLicenses();
      final entries = await materialIconLicenses().toList();
      expect(entries, hasLength(1));
      final expected = entries.single.paragraphs.map((p) => p.text).toList();
      final registry = await LicenseRegistry.licenses
          .where((v) => v.packages.contains('Google Material icons'))
          .toList();
      expect(registry, hasLength(1));
      final g = GameController(
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 23),
      );
      addTearDown(g.dispose);
      final p = ContentProbe(tester);
      await p.show(
        TideglassApp(
          controller: g,
          initialPreferences: const ClientPreferences(
            onboardingDismissed: true,
            reduceMotion: true,
          ),
        ),
        app: true,
      );
      final before = jsonEncode(g.state.toJson());
      await p.checkControl(
        'settings',
        find.byTooltip(Presentation.text(Copy.settings)),
        tap: true,
      );
      await p.checkControl('help', named(HelpCopy.title), tap: true);
      await p.checkControl('credits', keyed('help-topic-credits'), tap: true);
      await p.checkControl(
        'licenses',
        keyed('help-action-licenses'),
        tap: true,
      );
      expect(find.byType(LicensePage), findsOneWidget);
      await tester.pumpAndSettle();
      for (
        var i = 0;
        i < 30 && find.text('Google Material icons').evaluate().isEmpty;
        i++
      ) {
        await tester.drag(find.byType(ListView).first, const Offset(0, -300));
        await tester.pumpAndSettle();
      }
      final item = find.widgetWithText(ListTile, 'Google Material icons');
      expect(item, findsOneWidget);
      await p.checkControl('google-icons', item, tap: true);
      await tester.pumpAndSettle();
      for (final paragraph in expected) {
        await readRaw(tester, p, paragraph);
      }
      expect(jsonEncode(g.state.toJson()), before);
      expect(tester.takeException(), isNull);
      const output = String.fromEnvironment('QA_FONT_REPORT');
      if (output.isNotEmpty) {
        File(output).writeAsStringSync(
          '${const JsonEncoder.withIndent('  ').convert({'viewport': contentViewport, 'scale': contentTextPercent, 'pseudo': Presentation.pseudoEnabled, 'paragraphs': observed, 'controls': p.controls, 'ledger_unchanged': true, 'single_registered_entry': true})}\n',
        );
      }
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
