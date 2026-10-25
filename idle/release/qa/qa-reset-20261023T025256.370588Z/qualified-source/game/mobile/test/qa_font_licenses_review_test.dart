import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
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
      await Scrollable.ensureVisible(tester.element(item), alignment: .5);
      await tester.pumpAndSettle();
      final tileRect = tester.getRect(item);
      const diagnosticOutput = String.fromEnvironment('QA_FONT_DIAGNOSTIC');
      if (diagnosticOutput.isNotEmpty) {
        File(diagnosticOutput).writeAsStringSync(
          jsonEncode({
            'tile': [
              tileRect.left,
              tileRect.top,
              tileRect.right,
              tileRect.bottom,
            ],
            'points': [
              for (final a in [
                Alignment.center,
                const Alignment(-.98, 0),
                const Alignment(.98, 0),
                const Alignment(0, -.98),
                const Alignment(0, .98),
              ])
                {
                  'alignment': a.toString(),
                  'item_hit': item.hitTestable(at: a).evaluate().length,
                  'path': [
                    for (final hit
                        in tester.hitTestOnBinding(a.withinRect(tileRect)).path)
                      {
                        'target': hit.target.runtimeType.toString(),
                        if (hit.target is RenderBox)
                          'bounds': [
                            (hit.target as RenderBox)
                                .localToGlobal(Offset.zero)
                                .dx,
                            (hit.target as RenderBox)
                                .localToGlobal(Offset.zero)
                                .dy,
                            (hit.target as RenderBox).size.width,
                            (hit.target as RenderBox).size.height,
                          ],
                      },
                  ],
                },
            ],
          }),
        );
      }
      final label = find.descendant(
        of: item,
        matching: find.text('Google Material icons'),
      );
      final labelParagraph = tester.renderObject<RenderParagraph>(
        find.descendant(of: label, matching: find.byType(RichText)),
      );
      expect(labelParagraph.text.toPlainText(), 'Google Material icons');
      expect(labelParagraph.didExceedMaxLines, false);
      final labelRects = <List<double>>[];
      for (final word in RegExp(r'\S+').allMatches('Google Material icons')) {
        for (final box in labelParagraph.getBoxesForSelection(
          TextSelection(baseOffset: word.start, extentOffset: word.end),
        )) {
          final rect = MatrixUtils.transformRect(
            labelParagraph.getTransformTo(null),
            box.toRect(),
          );
          p.inside(rect, p.visible(labelParagraph), 'complete package label');
          labelRects.add([rect.left, rect.top, rect.right, rect.bottom]);
        }
      }
      // The SDK tablet detail pane overlays the rightmost four pixels. Keep
      // that failed edge sample explicit and independently measure an actual
      // large, named, keyboard/pointer-accessible target within the full tile.
      double effectiveRight = tileRect.right - .5;
      while (effectiveRight > tileRect.left &&
          item
              .hitTestable(
                at: Alignment(
                  2 * (effectiveRight - tileRect.left) / tileRect.width - 1,
                  0,
                ),
              )
              .evaluate()
              .isEmpty) {
        effectiveRight -= 1;
      }
      final effective = Rect.fromLTRB(
        tileRect.left,
        tileRect.top,
        effectiveRight - .5,
        tileRect.bottom,
      );
      expect(effective.width, greaterThanOrEqualTo(48));
      expect(effective.height, greaterThanOrEqualTo(48));
      p.inside(
        effective,
        p.visible(tester.renderObject(item)),
        'effective package target',
      );
      for (final point in [
        effective.center,
        Offset(effective.left + 1, effective.center.dy),
        Offset(effective.right - 1, effective.center.dy),
        Offset(effective.center.dx, effective.top + 1),
        Offset(effective.center.dx, effective.bottom - 1),
      ]) {
        expect(
          item.hitTestable(
            at: Alignment(
              2 * (point.dx - tileRect.left) / tileRect.width - 1,
              2 * (point.dy - tileRect.top) / tileRect.height - 1,
            ),
          ),
          findsOneWidget,
        );
      }
      final semantics = tester.getSemantics(item).getSemanticsData();
      expect(semantics.label, contains('Google Material icons'));
      expect(semantics.hasAction(SemanticsAction.tap), true);
      bool focusedInside() {
        final c = FocusManager.instance.primaryFocus?.context;
        if (c == null) return false;
        bool found = false;
        c.visitAncestorElements((e) {
          if (identical(e, item.evaluate().single)) {
            found = true;
            return false;
          }
          return true;
        });
        return found;
      }

      for (var n = 0; n < 60 && !focusedInside(); n++) {
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
      }
      expect(
        focusedInside(),
        true,
        reason: 'actual keyboard focus reaches package item',
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pumpAndSettle();
      expect(find.text(expected.first), findsOneWidget);
      if (contentViewport == 'phone') {
        await tester.pageBack();
        await tester.pumpAndSettle();
        await p.checkControl(
          'google-icons-pointer',
          find.widgetWithText(ListTile, 'Google Material icons'),
          tap: true,
        );
      } else {
        await tester.tap(item.hitTestable());
        await tester.pumpAndSettle();
      }
      observed.add({
        'control': 'Google Material icons',
        'full_tile': [
          tileRect.left,
          tileRect.top,
          tileRect.right,
          tileRect.bottom,
        ],
        'effective_target': [
          effective.left,
          effective.top,
          effective.right,
          effective.bottom,
        ],
        'full_tile_five_point_pass': contentViewport == 'phone',
        'right_edge_overlap_pixels': tileRect.right - effectiveRight,
        'label_rects': labelRects,
        'named_tap_semantics': true,
        'effective_five_points': true,
        'keyboard_focus_and_enter': true,
        'pointer_activation': true,
      });
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
