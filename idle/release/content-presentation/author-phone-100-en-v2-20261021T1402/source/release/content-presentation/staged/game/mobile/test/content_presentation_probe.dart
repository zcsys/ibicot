// Staged author helper. This measures production render objects, not a mirror UI.
import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';

const contentViewport = String.fromEnvironment(
  'TIDEGLASS_TEST_VIEWPORT',
  defaultValue: 'phone',
);
const contentTextPercent = int.fromEnvironment(
  'TIDEGLASS_TEST_TEXT_PERCENT',
  defaultValue: 100,
);
const contentReportPath = String.fromEnvironment('TIDEGLASS_CONTENT_REPORT');
String digest(Object? value) =>
    sha256.convert(utf8.encode(jsonEncode(value))).toString();
Finder named(String value) => find.text(Presentation.text(value));
Finder keyed(String value) => find.byKey(ValueKey(value));

class ContentProbe {
  ContentProbe(this.tester);
  final WidgetTester tester;
  final List<Map<String, Object?>> texts = [], controls = [];
  static final List<Map<String, Object?>> rows = [];

  Future<void> show(
    Widget child, {
    bool app = false,
    bool pushed = false,
  }) async {
    expect([100, 150, 200], contains(contentTextPercent));
    expect(['phone', 'tablet'], contains(contentViewport));
    tester.view.physicalSize = contentViewport == 'phone'
        ? const Size(320, 720)
        : const Size(1024, 768);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue =
        contentTextPercent / 100;
    final nav = GlobalKey<NavigatorState>();
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpWidget(
      app
          ? child
          : MaterialApp(
              navigatorKey: nav,
              theme: tideglassTheme(),
              builder: (context, child) => MediaQuery(
                data: MediaQuery.of(context).copyWith(disableAnimations: true),
                child: child!,
              ),
              home: pushed
                  ? const Scaffold(body: Text('QA route origin'))
                  : child,
            ),
    );
    if (pushed) {
      nav.currentState!.push(MaterialPageRoute<void>(builder: (_) => child));
    }
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Rect visible(RenderObject object) {
    var result =
        Offset.zero & (tester.view.physicalSize / tester.view.devicePixelRatio);
    var child = object;
    for (
      RenderObject? parent = child.parent;
      parent != null;
      parent = child.parent
    ) {
      final clip = parent.describeApproximatePaintClip(child);
      if (clip != null) {
        result = result.intersect(
          MatrixUtils.transformRect(parent.getTransformTo(null), clip),
        );
      }
      if (parent is RenderAbstractViewport) {
        result = result.intersect(
          MatrixUtils.transformRect(
            parent.getTransformTo(null),
            parent.paintBounds,
          ),
        );
      }
      child = parent;
    }
    return result;
  }

  void inside(Rect rect, Rect viewport, String reason) {
    expect(viewport.isEmpty, isFalse, reason: reason);
    expect(rect.left, greaterThanOrEqualTo(viewport.left - .5), reason: reason);
    expect(rect.right, lessThanOrEqualTo(viewport.right + .5), reason: reason);
    expect(rect.top, greaterThanOrEqualTo(viewport.top - .5), reason: reason);
    expect(
      rect.bottom,
      lessThanOrEqualTo(viewport.bottom + .5),
      reason: reason,
    );
  }

  // Every rendered line box is actually brought into the intersected viewport.
  // A multi-screen paragraph is never certified by ensureVisible on its top.
  Future<void> read(
    String field,
    String english, {
    Finder? within,
    Finder? exact,
  }) async {
    final displayed = Presentation.text(english);
    final text =
        exact ??
        (within == null
            ? find.text(displayed)
            : find.descendant(of: within, matching: find.text(displayed)));
    expect(text, findsOneWidget, reason: field);
    final rich = find.descendant(of: text, matching: find.byType(RichText));
    expect(rich, findsOneWidget, reason: '$field rendered paragraph');
    final paragraph = tester.renderObject<RenderParagraph>(rich);
    expect(
      paragraph.text.toPlainText(),
      displayed,
      reason: '$field complete text',
    );
    expect(
      paragraph.didExceedMaxLines,
      isFalse,
      reason: '$field not truncated',
    );
    final boxes = paragraph.getBoxesForSelection(
      TextSelection(baseOffset: 0, extentOffset: displayed.length),
    );
    expect(boxes, isNotEmpty, reason: '$field has rendered lines');
    final observations = <Map<String, Object?>>[];
    for (final line in boxes) {
      final local = line.toRect();
      final scrollable = Scrollable.maybeOf(tester.element(text));
      if (scrollable != null) {
        final viewport = RenderAbstractViewport.of(paragraph);
        final target = viewport
            .getOffsetToReveal(paragraph, .5, rect: local)
            .offset;
        final position = scrollable.position;
        position.jumpTo(
          target.clamp(position.minScrollExtent, position.maxScrollExtent),
        );
        await tester.pumpAndSettle();
      }
      final global = MatrixUtils.transformRect(
        paragraph.getTransformTo(null),
        local,
      );
      inside(
        global,
        visible(paragraph),
        '$field line ${observations.length}: $english; local=$local; paragraph=${paragraph.size}; global=$global',
      );
      final view = visible(paragraph);
      observations.add({
        'rect': [global.left, global.top, global.right, global.bottom],
        'viewport': [view.left, view.top, view.right, view.bottom],
      });
    }
    expect(tester.takeException(), isNull);
    texts.add({
      'field': field,
      'english': english,
      'display': displayed,
      'english_sha256': digest(english),
      'display_sha256': digest(displayed),
      'code_units': displayed.length,
      'line_boxes': boxes.length,
      'observed_line_boxes': observations,
      'complete_text': true,
      'untruncated': true,
      'all_lines_in_viewport': true,
    });
  }

  Finder control(Finder finder) {
    expect(finder, findsOneWidget);
    final element = finder.evaluate().single;
    if (element.widget is BackButton) {
      return find
          .descendant(of: finder, matching: find.byType(IconButton))
          .first;
    }
    if (element.widget is ExpansionTile) {
      return find.descendant(of: finder, matching: find.byType(ListTile)).first;
    }
    bool action(Widget w) =>
        w is ButtonStyleButton ||
        w is IconButton ||
        w is ListTile ||
        w is NavigationDestination;
    if (action(element.widget)) return finder;
    Element? candidate;
    element.visitAncestorElements((e) {
      if (!action(e.widget)) return true;
      candidate = e;
      return false;
    });
    expect(candidate, isNotNull, reason: '$finder has actual control');
    return find.byElementPredicate((e) => identical(e, candidate));
  }

  Future<void> checkControl(
    String id,
    Finder finder, {
    bool enabled = true,
    bool tap = false,
  }) async {
    if (find.byType(SnackBar).evaluate().isNotEmpty) {
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    }
    final action = control(finder);
    await Scrollable.ensureVisible(tester.element(action), alignment: .5);
    await tester.pumpAndSettle();
    final rect = tester.getRect(action),
        viewport = visible(tester.renderObject(action));
    expect(rect.width, greaterThanOrEqualTo(48), reason: id);
    expect(rect.height, greaterThanOrEqualTo(48), reason: id);
    inside(rect, viewport, id);
    final semantics = tester.getSemantics(action).getSemanticsData();
    expect(
      '${semantics.label} ${semantics.tooltip}'.trim(),
      isNotEmpty,
      reason: '$id accessible name',
    );
    expect(
      semantics.hasAction(SemanticsAction.tap),
      enabled,
      reason: '$id enabled semantics',
    );
    final points = [
      Alignment.center,
      const Alignment(-.98, 0),
      const Alignment(.98, 0),
      const Alignment(0, -.98),
      const Alignment(0, .98),
    ];
    if (enabled) {
      for (final point in points) {
        expect(
          action.hitTestable(at: point),
          findsOneWidget,
          reason: '$id $point',
        );
      }
    }
    controls.add({
      'id': id,
      'enabled': enabled,
      'rect': [rect.left, rect.top, rect.right, rect.bottom],
      'viewport': [
        viewport.left,
        viewport.top,
        viewport.right,
        viewport.bottom,
      ],
      'minimum_48': true,
      'whole_control_visible': true,
      'semantic_name': '${semantics.label} ${semantics.tooltip}'.trim(),
      'semantic_tap': semantics.hasAction(SemanticsAction.tap),
      'hit_points': enabled ? 5 : 0,
      'callback_invoked': tap,
    });
    if (tap) {
      expect(enabled, isTrue);
      await tester.tap(action.hitTestable());
      await tester.pumpAndSettle();
    }
    expect(tester.takeException(), isNull);
  }

  Future<void> expand(String id, Finder tile, {required bool expanded}) async {
    await checkControl(id, tile);
    final header = control(tile);
    final isExpanded = ExpansibleController.of(tester.element(header))
        .isExpanded;
    if (isExpanded != expanded) {
      await checkControl('$id-toggle', tile, tap: true);
    }
  }

  void row(
    String id,
    String state,
    String route,
    String fixture,
    Map<String, Object?> assertions, {
    required Object before,
    required Object after,
  }) {
    expect(texts, isNotEmpty, reason: '$id/$state must read actual copy');
    expect(
      assertions.values.every((v) => v == true),
      isTrue,
      reason: '$id/$state assertions',
    );
    rows.add({
      'id': id,
      'state': state,
      'route': route,
      'fixture': fixture,
      'condition': {
        'viewport': contentViewport,
        'text_percent': contentTextPercent,
        'pseudo': Presentation.pseudoEnabled,
      },
      'texts': List.of(texts),
      'controls': List.of(controls),
      'assertions': assertions,
      'before': before,
      'after': after,
      'before_sha256': digest(before),
      'after_sha256': digest(after),
    });
    texts.clear();
    controls.clear();
    if (contentReportPath.isNotEmpty) {
      File(contentReportPath).writeAsStringSync(
        jsonEncode({
          'schema_version': 1,
          'kind': 'production_widget_content_observations',
          'complete': false,
          'rows': rows,
        }),
      );
    }
  }
}
