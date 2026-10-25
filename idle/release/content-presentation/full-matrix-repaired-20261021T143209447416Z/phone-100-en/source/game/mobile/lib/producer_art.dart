import 'package:flutter/material.dart';
import 'producer_art_data.dart';

int producerStageForCount(int count) => (count ~/ 25).clamp(0, 4);

/// Five authored silhouettes with five actual additive construction stages.
/// Adjacent cards carry names/counts; the artwork adds no duplicate semantics.
class StagedProducerArt extends StatelessWidget {
  const StagedProducerArt({
    super.key,
    required this.tier,
    required this.count,
    this.size = 72,
    this.locked = false,
    this.selected = false,
  }) : assert(tier >= 0 && tier < 5),
       assert(size > 0);
  final int tier, count;
  final double size;
  final bool locked, selected;

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: SizedBox.square(
      dimension: size,
      child: Stack(
        children: [
          Positioned.fill(
            child: Opacity(
              opacity: locked ? .35 : 1,
              child: CustomPaint(
                painter: ProducerStagePainter(
                  tier,
                  producerStageForCount(count),
                ),
              ),
            ),
          ),
          if (selected)
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFFF4CA88), width: 2),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          if (locked)
            const Positioned(
              right: 0,
              bottom: 0,
              child: Icon(
                Icons.lock_outline,
                size: 16,
                color: Color(0xFFA1BAC3),
              ),
            ),
        ],
      ),
    ),
  );
}

class ProducerStagePainter extends CustomPainter {
  ProducerStagePainter(this.tier, this.stage)
    : assert(tier >= 0 && tier < 5),
      assert(stage >= 0 && stage < 5);
  final int tier, stage;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 100, size.height / 100);
    for (final raw in producerScenes[tier * 5 + stage]['shapes'] as List) {
      final shape = raw as Map;
      double value(String key) => (shape[key] as num).toDouble();
      void draw(Paint paint) {
        switch (shape['type']) {
          case 'circle':
            canvas.drawCircle(
              Offset(value('cx'), value('cy')),
              value('r'),
              paint,
            );
          case 'ellipse':
            canvas.drawOval(
              Rect.fromCenter(
                center: Offset(value('cx'), value('cy')),
                width: value('rx') * 2,
                height: value('ry') * 2,
              ),
              paint,
            );
          case 'rect':
            canvas.drawRRect(
              RRect.fromRectAndRadius(
                Rect.fromLTWH(
                  value('x'),
                  value('y'),
                  value('width'),
                  value('height'),
                ),
                Radius.circular(value('radius')),
              ),
              paint,
            );
          case 'line':
            canvas.drawLine(
              Offset(value('x1'), value('y1')),
              Offset(value('x2'), value('y2')),
              paint,
            );
          case 'polygon':
            final points = shape['points'] as List;
            final path = Path();
            for (var i = 0; i < points.length; i++) {
              final point = points[i] as List;
              final x = (point[0] as num).toDouble(),
                  y = (point[1] as num).toDouble();
              if (i == 0) {
                path.moveTo(x, y);
              } else {
                path.lineTo(x, y);
              }
            }
            canvas.drawPath(path..close(), paint);
        }
      }

      Color color(String source) =>
          Color(int.parse('FF${source.substring(1)}', radix: 16));
      if (shape['fill'] != 'none') {
        draw(Paint()..color = color(shape['fill'] as String));
      }
      if (shape['stroke'] != null) {
        draw(
          Paint()
            ..color = color(shape['stroke'] as String)
            ..style = PaintingStyle.stroke
            ..strokeJoin = StrokeJoin.round
            ..strokeCap = StrokeCap.round
            ..strokeWidth = value('stroke_width'),
        );
      }
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(ProducerStagePainter oldDelegate) =>
      oldDelegate.tier != tier || oldDelegate.stage != stage;
}
