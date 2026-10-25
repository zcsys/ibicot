import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/producer_art.dart';
import 'package:tideglass/producer_art_data.dart';

void main() {
  test('all 25 original scenes use the exact five thresholds', () {
    expect(producerScenes.length, 25);
    expect(producerScenes.map((s) => s['id']).toSet().length, 25);
    for (var tier = 0; tier < 5; tier++) {
      for (var stage = 0; stage < 5; stage++) {
        final scene = producerScenes[tier * 5 + stage];
        expect(scene['ownership_threshold'], [0, 25, 50, 75, 100][stage]);
        if (stage > 0) {
          expect(
            (scene['shapes'] as List).length,
            greaterThan(
              (producerScenes[tier * 5 + stage - 1]['shapes'] as List).length,
            ),
          );
        }
      }
    }
    for (final count in [0, 1, 24, 25, 49, 50, 74, 75, 99, 100, 999999]) {
      expect(producerStageForCount(count), count >= 100 ? 4 : count ~/ 25);
    }
  });
  test('every drawn primitive remains within the authored view box', () {
    for (final scene in producerScenes) {
      for (final raw in scene['shapes'] as List) {
        final shape = raw as Map;
        double n(String key) => (shape[key] as num).toDouble();
        final stroke = (shape['stroke_width'] as num? ?? 0).toDouble() / 2;
        late Rect bounds;
        switch (shape['type']) {
          case 'circle':
            bounds = Rect.fromCircle(
              center: Offset(n('cx'), n('cy')),
              radius: n('r'),
            );
          case 'ellipse':
            bounds = Rect.fromCenter(
              center: Offset(n('cx'), n('cy')),
              width: n('rx') * 2,
              height: n('ry') * 2,
            );
          case 'rect':
            bounds = Rect.fromLTWH(n('x'), n('y'), n('width'), n('height'));
          case 'line':
            bounds = Rect.fromPoints(
              Offset(n('x1'), n('y1')),
              Offset(n('x2'), n('y2')),
            );
          case 'polygon':
            final points = (shape['points'] as List)
                .map(
                  (p) => Offset(
                    (p[0] as num).toDouble(),
                    (p[1] as num).toDouble(),
                  ),
                )
                .toList();
            bounds = Rect.fromPoints(points.first, points.first);
            for (final point in points.skip(1)) {
              bounds = bounds.expandToInclude(Rect.fromPoints(point, point));
            }
        }
        bounds = bounds.inflate(stroke);
        expect(
          bounds.left,
          greaterThanOrEqualTo(0),
          reason: scene['id'] as String,
        );
        expect(
          bounds.top,
          greaterThanOrEqualTo(0),
          reason: scene['id'] as String,
        );
        expect(
          bounds.right,
          lessThanOrEqualTo(100),
          reason: scene['id'] as String,
        );
        expect(
          bounds.bottom,
          lessThanOrEqualTo(100),
          reason: scene['id'] as String,
        );
      }
    }
  });
  testWidgets('actual native renderer captures all 25 stages without errors', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1000, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.runAsync(() async {
      // A system font is used only for this host review sheet, never bundled.
      final font = File('/System/Library/Fonts/Supplemental/Arial.ttf');
      if (await font.exists()) {
        final loader = FontLoader('ReviewFont')
          ..addFont(
            font.readAsBytes().then((bytes) => ByteData.sublistView(bytes)),
          );
        await loader.load();
      }
    });
    final boundaryKey = GlobalKey();
    const names = [
      'Spark Skiff',
      'Prism Nursery',
      'Tide Dynamo',
      'Aurora Loom',
      'Dawn Observatory',
    ];
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(fontFamily: 'ReviewFont'),
        home: Scaffold(
          backgroundColor: const Color(0xFF071923),
          body: Center(
            child: RepaintBoundary(
              key: boundaryKey,
              child: ColoredBox(
                color: const Color(0xFF071923),
                child: SizedBox(
                  width: 950,
                  height: 690,
                  child: Column(
                    children: [
                      const Padding(
                        padding: EdgeInsets.all(14),
                        child: Text(
                          'TIDEGLASS · PRODUCER PRESENTATIONS',
                          style: TextStyle(color: Colors.white, fontSize: 20),
                        ),
                      ),
                      Row(
                        children: [
                          const SizedBox(width: 180),
                          for (final n in [0, 25, 50, 75, 100])
                            Expanded(
                              child: Center(
                                child: Text(
                                  '$n owned',
                                  style: const TextStyle(color: Colors.white),
                                ),
                              ),
                            ),
                        ],
                      ),
                      for (var tier = 0; tier < 5; tier++)
                        Expanded(
                          child: Row(
                            children: [
                              SizedBox(
                                width: 180,
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Text(
                                    names[tier],
                                    style: const TextStyle(
                                      color: Color(0xFFA1BAC3),
                                      fontSize: 16,
                                    ),
                                  ),
                                ),
                              ),
                              for (final n in [0, 25, 50, 75, 100])
                                Expanded(
                                  child: Center(
                                    child: StagedProducerArt(
                                      tier: tier,
                                      count: n,
                                      size: 112,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(tester.takeException(), isNull);
    final boundary =
        boundaryKey.currentContext!.findRenderObject()!
            as RenderRepaintBoundary;
    await tester.runAsync(() async {
      final image = await boundary.toImage(pixelRatio: 1.5);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final file = File('../../release/art/producer-contact-sheet.png');
      await file.parent.create(recursive: true);
      await file.writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  });
  testWidgets(
    'locked and selected retain shape at small size and high text scale',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(textScaler: TextScaler.linear(2)),
            child: const Scaffold(
              body: Row(
                children: [
                  StagedProducerArt(tier: 0, count: 0, size: 48, locked: true),
                  StagedProducerArt(
                    tier: 4,
                    count: 100,
                    size: 48,
                    selected: true,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
      expect(find.byIcon(Icons.lock_outline), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
