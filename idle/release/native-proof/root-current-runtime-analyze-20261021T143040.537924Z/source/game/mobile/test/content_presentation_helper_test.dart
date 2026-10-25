// Author helper qualification, separate from the actual-content matrix.
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

import 'content_presentation_probe.dart';

void main() {
  testWidgets('selection whitespace overhang is not hidden visible prose', (
    tester,
  ) async {
    final p = ContentProbe(tester);
    const text =
        'A skiff returns with a single thread of Radiance. The harbor has forgotten how to hold the dawn. Set a light on the water, learn its rhythm, and draw the first new chart.';
    await p.show(
      const Scaffold(
        body: Center(
          child: ClipRect(
            child: SizedBox(
              width: 234,
              child: Text(text, style: TextStyle(fontSize: 14, height: 1.4)),
            ),
          ),
        ),
      ),
    );
    final paragraph = tester.renderObject<RenderParagraph>(
      find.descendant(of: find.text(text), matching: find.byType(RichText)),
    );
    final full = paragraph.getBoxesForSelection(
      const TextSelection(baseOffset: 0, extentOffset: text.length),
    );
    expect(
      full.any((b) => b.right > paragraph.size.width + .5),
      isTrue,
      reason: 'positive whitespace counterexample actually present',
    );
    await p.read('prose', text);
    expect(p.texts.single['all_lines_in_viewport'], isTrue);
    await tester.pumpWidget(const SizedBox.shrink());
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    tester.platformDispatcher.clearTextScaleFactorTestValue();
  });
  testWidgets('a clipped visible word still fails unchanged bounds', (
    tester,
  ) async {
    final p = ContentProbe(tester);
    await p.show(
      const Scaffold(
        body: Center(
          child: ClipRect(
            child: SizedBox(
              width: 60,
              height: 60,
              child: OverflowBox(
                maxWidth: 234,
                alignment: Alignment.centerLeft,
                child: Text('VISIBLE WORD', style: TextStyle(fontSize: 20)),
              ),
            ),
          ),
        ),
      ),
    );
    await expectLater(
      p.read('clipped', 'VISIBLE WORD'),
      throwsA(isA<TestFailure>()),
    );
    expect(p.texts, isEmpty);
    await tester.pumpWidget(const SizedBox.shrink());
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    tester.platformDispatcher.clearTextScaleFactorTestValue();
  });
  testWidgets('truncated prose cannot emit read-through evidence', (
    tester,
  ) async {
    final p = ContentProbe(tester);
    const text =
        'A long paragraph must remain available even when the viewport is small.';
    await p.show(
      const Scaffold(
        body: Center(
          child: SizedBox(
            width: 70,
            child: Text(text, maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
        ),
      ),
    );
    await expectLater(p.read('truncated', text), throwsA(isA<TestFailure>()));
    expect(p.texts, isEmpty);
    await tester.pumpWidget(const SizedBox.shrink());
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
    tester.platformDispatcher.clearTextScaleFactorTestValue();
  });
  testWidgets(
    'long paragraph reads every visible range over multiple viewports',
    (tester) async {
      final p = ContentProbe(tester),
          text = List.filled(
            50,
            'Every sentence remains available to read.',
          ).join(' ');
      await p.show(
        Scaffold(
          body: SafeArea(child: SingleChildScrollView(child: Text(text))),
        ),
      );
      await p.read('long', text);
      final observed = p.texts.single;
      expect(observed['line_boxes'] as int, greaterThan(30));
      expect((observed['selection_ranges'] as List).length, 300);
      expect(
        tester.state<ScrollableState>(find.byType(Scrollable)).position.pixels,
        greaterThan(0),
      );
      await tester.pumpWidget(const SizedBox.shrink());
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      tester.platformDispatcher.clearTextScaleFactorTestValue();
    },
  );
}
