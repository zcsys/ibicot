import 'presentation.dart';
import 'strings.dart';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'cosmetics.dart';
import 'harbor_art.dart';
import 'palette.dart';

/// Draws one appearance in the harbor's native 640×388 coordinate system.
/// Preview and equipped views call this exact renderer. No simulation input.
void drawCosmetic(Canvas canvas, Size size, String id, double phase) {
  final item = cosmeticById(id);
  canvas.save();
  canvas.clipRect(Offset.zero & size);
  canvas.scale(size.width / 640, size.height / 388);
  final brush = _Brush(canvas);
  final time = phase.isFinite ? phase % 1 : 0.0;
  switch (item.source) {
    case CosmeticSource.chapter:
      _chapter(brush, item.ordinal);
    case CosmeticSource.decoration:
      _drawEarnedDecoration(canvas, id, time);
    case CosmeticSource.freePass:
      _free(brush, item.ordinal);
    case CosmeticSource.premiumPass:
      _premium(brush, item.ordinal);
    case CosmeticSource.shop:
      _shop(brush, item.ordinal);
  }
  canvas.restore();
}

class CosmeticOverlay extends StatelessWidget {
  const CosmeticOverlay({super.key, required this.id, this.phase = 0});
  final String id;
  final double phase;
  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: ExcludeSemantics(
      child: CustomPaint(painter: _CosmeticPainter(id, phase)),
    ),
  );
}

class CosmeticPreview extends StatelessWidget {
  const CosmeticPreview({
    super.key,
    required this.id,
    this.counts = const [25, 25, 10, 10, 1],
    this.restoration = 6,
    this.phase = 0,
    this.otherDecorationId,
  });
  final String id;
  final List<int> counts;
  final int restoration;
  final double phase;
  final String? otherDecorationId;
  @override
  Widget build(BuildContext context) => Semantics(
    image: true,
    label: UiEnglish.cosmeticCosmeticByIdIdTitleHarborAppearancePreview(
      Presentation.authored((cosmeticById(id).title).toString()),
    ),
    child: ExcludeSemantics(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(22),
        child: AspectRatio(
          aspectRatio: 640 / 388,
          child: Stack(
            fit: StackFit.expand,
            children: [
              HarborArt(counts: counts, phase: phase, restoration: restoration),
              CosmeticOverlay(id: id, phase: phase),
              if (otherDecorationId != null && otherDecorationId != id)
                CosmeticOverlay(id: otherDecorationId!, phase: phase),
            ],
          ),
        ),
      ),
    ),
  );
}

class _CosmeticPainter extends CustomPainter {
  const _CosmeticPainter(this.id, this.phase);
  final String id;
  final double phase;
  @override
  void paint(Canvas canvas, Size size) => drawCosmetic(canvas, size, id, phase);
  @override
  bool shouldRepaint(covariant _CosmeticPainter old) =>
      old.id != id || old.phase != phase;
}

const _mint = TideColors.teal, _gold = TideColors.amber;
const _pale = Color(0xFFE7E6D0), _blue = Color(0xFF89B7CC);
const _ink = Color(0xFF143744), _violet = Color(0xFFB4A8D3);

class _Brush {
  _Brush(this.canvas);
  final Canvas canvas;
  void line(
    double x,
    double y,
    double xx,
    double yy,
    Color color, [
    double width = 2,
  ]) => canvas.drawLine(
    Offset(x, y),
    Offset(xx, yy),
    Paint()
      ..color = color
      ..strokeWidth = width
      ..strokeCap = StrokeCap.round,
  );
  void circle(double x, double y, double r, Color color) =>
      canvas.drawCircle(Offset(x, y), r, Paint()..color = color);
  void ring(double x, double y, double r, Color color, [double width = 2]) =>
      canvas.drawCircle(
        Offset(x, y),
        r,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = width,
      );
  void oval(
    double x,
    double y,
    double w,
    double h,
    Color color, {
    bool fill = false,
    double width = 2,
  }) => canvas.drawOval(
    Rect.fromCenter(center: Offset(x, y), width: w, height: h),
    Paint()
      ..color = color
      ..style = fill ? PaintingStyle.fill : PaintingStyle.stroke
      ..strokeWidth = width,
  );
  void box(
    double x,
    double y,
    double w,
    double h,
    Color color, [
    double radius = 0,
  ]) => canvas.drawRRect(
    RRect.fromRectAndRadius(Rect.fromLTWH(x, y, w, h), Radius.circular(radius)),
    Paint()..color = color,
  );
  void path(Path path, Color color, {bool fill = true, double width = 2}) =>
      canvas.drawPath(
        path,
        Paint()
          ..color = color
          ..style = fill ? PaintingStyle.fill : PaintingStyle.stroke
          ..strokeWidth = width
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round,
      );
  void poly(
    List<Offset> points,
    Color color, {
    bool fill = true,
    double width = 2,
  }) {
    final shape = Path()..moveTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      shape.lineTo(point.dx, point.dy);
    }
    shape.close();
    path(shape, color, fill: fill, width: width);
  }

  void star(double x, double y, double r, Color color) => poly([
    Offset(x, y - r),
    Offset(x + r * .25, y - r * .25),
    Offset(x + r, y),
    Offset(x + r * .25, y + r * .25),
    Offset(x, y + r),
    Offset(x - r * .25, y + r * .25),
    Offset(x - r, y),
    Offset(x - r * .25, y - r * .25),
  ], color);
  void lantern(double x, double y, {double scale = 1, Color color = _gold}) {
    circle(x, y, 17 * scale, color.withValues(alpha: .08));
    box(x - 7 * scale, y - 10 * scale, 14 * scale, 20 * scale, _ink, 3 * scale);
    box(x - 4 * scale, y - 7 * scale, 8 * scale, 14 * scale, color, 2 * scale);
    poly([
      Offset(x - 10 * scale, y - 10 * scale),
      Offset(x, y - 17 * scale),
      Offset(x + 10 * scale, y - 10 * scale),
    ], _pale);
    line(
      x - 8 * scale,
      y + 11 * scale,
      x + 8 * scale,
      y + 11 * scale,
      _mint,
      2 * scale,
    );
    ring(x, y - 20 * scale, 3 * scale, _gold, scale);
  }

  void wave(
    double y,
    Color color, {
    double start = 170,
    double end = 600,
    double height = 6,
  }) {
    final p = Path()..moveTo(start, y);
    for (var x = start; x < end; x += 60) {
      p.relativeQuadraticBezierTo(15, -height, 30, 0);
      p.relativeQuadraticBezierTo(15, height, 30, 0);
    }
    path(p, color, fill: false, width: 1.5);
  }
}

void _chapter(_Brush b, int id) {
  switch (id) {
    case 1:
      b.poly(const [
        Offset(153, 300),
        Offset(172, 275),
        Offset(188, 299),
      ], _blue);
      b.box(161, 268, 19, 10, _pale, 4);
      b.box(165, 259, 11, 9, _mint, 3);
      b.line(171, 260, 171, 223, _pale);
      b.poly(const [
        Offset(171, 224),
        Offset(201, 235),
        Offset(171, 244),
      ], _gold);
      b.star(183, 235, 4, _ink);
    case 2:
      b.path(
        Path()
          ..moveTo(174, 231)
          ..quadraticBezierTo(321, 288, 462, 231),
        _pale,
        fill: false,
        width: 3,
      );
      b.line(174, 244, 462, 244, _mint, 4);
      for (var i = 0; i < 13; i++) {
        final x = 174.0 + i * 24;
        b.line(x, 244, x, 231 + math.sin(i / 12 * math.pi) * 28, _pale, 1);
      }
      for (final x in [174.0, 462.0]) {
        b.line(x, 258, x, 207, _blue, 5);
        b.lantern(x, 201, scale: .7);
      }
    case 3:
      b.line(573, 294, 588, 200, _blue, 4);
      b.line(617, 294, 601, 200, _blue, 4);
      b.line(578, 202, 613, 202, _pale, 4);
      for (var i = 0; i < 5; i++) {
        final x = 581.0 + i * 7;
        b.line(x, 205, x, 222, _mint, 1);
        b.box(x - 2, 222, 4, 28 + (i % 3) * 8, _gold, 2);
      }
      b.poly(const [
        Offset(585, 196),
        Offset(595, 183),
        Offset(605, 196),
      ], _mint);
    case 4:
      for (var i = 0; i < 3; i++) {
        final x = 240.0 + i * 124;
        b.path(
          Path()
            ..moveTo(x - 29, 367)
            ..lineTo(x - 29, 343)
            ..quadraticBezierTo(x, 307, x + 29, 343)
            ..lineTo(x + 29, 367),
          _blue,
          fill: false,
          width: 5,
        );
        b.star(x, 329, 7, _gold);
        b.box(x - 34, 367, 68, 5, _mint, 2);
        b.line(x - 19, 347, x + 19, 347, _pale, 1);
      }
    case 5:
      b.poly(const [
        Offset(53, 333),
        Offset(83, 326),
        Offset(112, 333),
        Offset(83, 349),
      ], _gold);
      b.poly(const [
        Offset(54, 330),
        Offset(83, 323),
        Offset(83, 344),
        Offset(54, 339),
      ], _pale);
      b.poly(const [
        Offset(83, 323),
        Offset(111, 330),
        Offset(111, 340),
        Offset(83, 344),
      ], _blue);
      for (var i = 0; i < 3; i++) {
        b.line(60, 330.0 + i * 3, 76, 327.0 + i * 3, _ink, 1);
      }
      b.box(121, 329, 11, 14, _ink, 3);
      b.line(125, 333, 143, 306, _gold, 1.5);
      b.poly(const [
        Offset(130, 326),
        Offset(132, 310),
        Offset(148, 301),
        Offset(142, 315),
      ], _pale);
    case 6:
      for (var i = 0; i < 6; i++) {
        final x = 223.0 + i * 66, y = 106.0 + (i % 2) * 45;
        b.lantern(x, y, scale: .8);
        b.line(x, y + 10, x + 5, y + 25, _gold.withValues(alpha: .5), 1);
      }
      b.path(
        Path()
          ..moveTo(196, 152)
          ..quadraticBezierTo(376, 12, 585, 153),
        _pale.withValues(alpha: .3),
        fill: false,
        width: 1,
      );
  }
}

void _free(_Brush b, int id) {
  switch (id) {
    case 1:
      b.line(175, 302, 175, 217, _pale, 4);
      b.box(163, 300, 24, 7, _blue, 2);
      b.path(
        Path()
          ..moveTo(175, 225)
          ..quadraticBezierTo(200, 199, 212, 220),
        _mint,
        fill: false,
        width: 3,
      );
      b.line(210, 218, 210, 232, _gold, 1);
      b.lantern(210, 249, scale: 1.2);
    case 2:
      b.poly(const [
        Offset(196, 308),
        Offset(251, 308),
        Offset(239, 324),
        Offset(210, 324),
      ], _blue);
      b.path(
        Path()
          ..moveTo(205, 313)
          ..quadraticBezierTo(224, 326, 242, 313),
        _pale,
        fill: false,
        width: 3,
      );
      for (var i = 0; i < 3; i++) {
        b.path(
          Path()
            ..moveTo(168, 329.0 + i * 6)
            ..quadraticBezierTo(226, 341.0 + i * 6, 274, 328.0 + i * 6),
          _pale.withValues(alpha: .4 - i * .08),
          fill: false,
          width: 1.5,
        );
      }
      b.circle(219, 315, 4, _gold);
    case 3:
      b.line(223, 289, 223, 228, _pale, 2);
      b.poly(const [
        Offset(223, 229),
        Offset(263, 240),
        Offset(245, 249),
        Offset(223, 252),
      ], _blue);
      b.star(240, 241, 7, _gold);
      b.line(223, 252, 232, 265, _mint, 1);
    case 4:
      b.path(
        Path()
          ..moveTo(288, 271)
          ..lineTo(288, 227)
          ..quadraticBezierTo(319, 197, 351, 227)
          ..lineTo(351, 271),
        _pale,
        fill: false,
        width: 3,
      );
      for (var i = 0; i < 4; i++) {
        final x = 297.0 + i * 15;
        b.poly([
          Offset(x, 257),
          Offset(x - 7, 239),
          Offset(x, 220),
          Offset(x + 7, 239),
        ], i.isEven ? _pale : _blue);
        b.line(x, 257, x, 220, _mint, 1);
      }
      b.box(284, 271, 71, 5, _pale, 2);
    case 5:
      b.ring(404, 292, 29, _blue, 3);
      b.ring(404, 292, 35, _mint, 1);
      for (var i = 0; i < 6; i++) {
        final a = i * math.pi / 3;
        b.line(
          404,
          292,
          404 + math.cos(a) * 27,
          292 + math.sin(a) * 27,
          _pale,
          2,
        );
      }
      b.circle(404, 292, 8, _gold);
      b.wave(354, _blue, start: 339, end: 465, height: 4);
      b.wave(362, _mint.withValues(alpha: .5), start: 339, end: 465, height: 4);
    case 6:
      b.box(463, 214, 49, 47, _ink, 3);
      for (var row = 0; row < 5; row++) {
        for (var col = 0; col < 5; col++) {
          b.box(
            466 + col * 9.0,
            216 + row * 9.0,
            8,
            8,
            (row + col).isEven ? _violet : _blue,
          );
        }
      }
      b.line(460, 212, 515, 212, _gold, 4);
      for (var i = 0; i < 6; i++) {
        b.line(465.0 + i * 9, 261, 465.0 + i * 9, 274, _pale, 1);
      }
    case 7:
      b.poly(const [
        Offset(545, 275),
        Offset(556, 256),
        Offset(578, 256),
        Offset(591, 275),
      ], _blue);
      b.line(568, 259, 568, 230, _pale, 2);
      b.ring(568, 226, 12, _mint, 2);
      b.line(550, 226, 586, 226, _gold, 1);
      b.line(568, 208, 568, 244, _gold, 1);
      b.box(555, 269, 26, 5, _gold, 2);
    case 8:
      b.poly(const [
        Offset(286, 357),
        Offset(297, 341),
        Offset(314, 339),
        Offset(329, 352),
        Offset(315, 366),
        Offset(299, 369),
      ], _blue);
      b.poly(const [
        Offset(297, 341),
        Offset(314, 339),
        Offset(307, 355),
      ], _pale);
      b.star(309, 353, 7, _gold);
      b.path(
        Path()
          ..moveTo(291, 358)
          ..quadraticBezierTo(245, 389, 221, 350),
        _mint,
        fill: false,
        width: 2,
      );
      b.ring(219, 345, 5, _gold, 2);
      b.line(219, 349, 219, 364, _gold, 2);
      b.path(
        Path()
          ..moveTo(208, 357)
          ..quadraticBezierTo(219, 376, 230, 357),
        _gold,
        fill: false,
        width: 2,
      );
    case 9:
      b.line(163, 268, 163, 186, _pale, 3);
      b.line(163, 188, 347, 188, _pale, 2);
      b.poly(const [
        Offset(168, 191),
        Offset(342, 191),
        Offset(328, 220),
        Offset(256, 228),
        Offset(181, 219),
      ], _blue);
      for (var i = 0; i < 5; i++) {
        b.star(190.0 + i * 32, 204 + (i % 2) * 7.0, 6, _gold);
      }
      b.line(172, 194, 337, 194, _mint, 1);
    case 10:
      b.path(
        Path()
          ..moveTo(544, 151)
          ..cubicTo(440, 11, 252, 21, 157, 131),
        _pale.withValues(alpha: .6),
        fill: false,
        width: 2,
      );
      for (var i = 0; i < 5; i++) {
        final x = 223.0 + i * 57, y = 84.0 + math.pow(i - 2, 2) * 7;
        b.path(
          Path()
            ..moveTo(x - 8, y)
            ..quadraticBezierTo(x - 3, y - 7, x, y)
            ..quadraticBezierTo(x + 4, y - 7, x + 10, y),
          _gold,
          fill: false,
          width: 2,
        );
      }
      b.star(157, 131, 10, _mint);
  }
}

void _premium(_Brush b, int id) {
  switch (id) {
    case 1:
      b.poly(const [
        Offset(190, 307),
        Offset(253, 307),
        Offset(239, 327),
        Offset(209, 327),
      ], _violet);
      b.poly(const [
        Offset(190, 307),
        Offset(224, 315),
        Offset(209, 327),
      ], _pale);
      b.poly(const [
        Offset(224, 315),
        Offset(253, 307),
        Offset(239, 327),
      ], _mint);
      b.line(224, 315, 223, 327, _gold, 1);
      b.oval(222, 332, 72, 8, _gold, width: 1);
    case 2:
      b.poly(const [
        Offset(222, 250),
        Offset(222, 300),
        Offset(254, 300),
      ], _ink);
      b.poly(const [
        Offset(218, 264),
        Offset(197, 298),
        Offset(218, 298),
      ], _blue);
      b.poly(const [
        Offset(222, 240),
        Offset(253, 250),
        Offset(222, 258),
      ], _violet);
      const points = [
        Offset(225, 266),
        Offset(237, 282),
        Offset(229, 292),
        Offset(247, 296),
      ];
      for (var i = 1; i < points.length; i++) {
        b.line(
          points[i - 1].dx,
          points[i - 1].dy,
          points[i].dx,
          points[i].dy,
          _gold,
          1,
        );
      }
      for (final p in points) {
        b.star(p.dx, p.dy, 3, _pale);
      }
    case 3:
      for (var i = 0; i < 3; i++) {
        final x = 297.0 + i * 23;
        b.path(
          Path()
            ..moveTo(x - 10, 265)
            ..lineTo(x - 10, 239)
            ..quadraticBezierTo(x, 214, x + 10, 239)
            ..lineTo(x + 10, 265),
          _violet,
          fill: false,
          width: 3,
        );
        b.poly([
          Offset(x, 231),
          Offset(x + 5, 246),
          Offset(x, 256),
          Offset(x - 5, 246),
        ], _mint);
      }
      b.path(
        Path()
          ..moveTo(280, 266)
          ..lineTo(288, 215)
          ..quadraticBezierTo(320, 192, 353, 215)
          ..lineTo(362, 266),
        _blue,
        fill: false,
        width: 2,
      );
      b.circle(321, 204, 7, _gold);
      b.circle(325, 201, 6, _ink);
    case 4:
      b.ring(404, 290, 34, _violet, 2);
      b.ring(404, 290, 40, _gold.withValues(alpha: .4), 1);
      for (var i = 0; i < 3; i++) {
        final a = i * math.pi * 2 / 3,
            x = 404 + math.cos(a) * 34,
            y = 290 + math.sin(a) * 34;
        b.star(x, y, 7, _gold);
        b.path(
          Path()
            ..moveTo(x, y)
            ..quadraticBezierTo(x - 27, y - 38, x - 41, y - 28),
          _mint,
          fill: false,
          width: 2,
        );
      }
      b.circle(404, 290, 10, _pale);
      b.circle(404, 290, 4, _violet);
    case 5:
      b.path(
        Path()
          ..moveTo(454, 267)
          ..lineTo(454, 203)
          ..quadraticBezierTo(488, 179, 521, 203)
          ..lineTo(521, 267),
        _gold,
        fill: false,
        width: 3,
      );
      for (var i = 0; i < 3; i++) {
        final x = 461.0 + i * 20;
        b.poly([
          Offset(x, 208),
          Offset(x + 14, 208),
          Offset(x + 14, 257),
          Offset(x + 7, 267),
          Offset(x, 257),
        ], i.isEven ? _violet : _blue);
        b.star(x + 7, 225, 4, _ink);
      }
    case 6:
      b.poly(
        const [
          Offset(537, 277),
          Offset(544, 245),
          Offset(568, 230),
          Offset(594, 246),
          Offset(601, 277),
        ],
        _gold,
        fill: false,
        width: 2,
      );
      for (var i = 0; i < 4; i++) {
        final x = 538.0 + i * 16;
        b.path(
          Path()
            ..moveTo(x, 243)
            ..cubicTo(x - 14, 216, x + 22, 188, x + 6, 166),
          i.isEven
              ? _mint.withValues(alpha: .7)
              : _violet.withValues(alpha: .6),
          fill: false,
          width: 5,
        );
      }
      b.star(568, 230, 7, _pale);
    case 7:
      b.path(
        Path()
          ..moveTo(174, 368)
          ..quadraticBezierTo(366, 331, 594, 369),
        _blue,
        fill: false,
        width: 14,
      );
      for (var i = 0; i < 12; i++) {
        final x = 184.0 + i * 35, y = 367 - math.sin(i / 11 * math.pi) * 19;
        b.line(x - 5, y - 9, x + 5, y + 9, _pale, 1.5);
        if (i.isEven) {
          b.star(x, y, 4, _gold);
        }
      }
      b.line(181, 354, 181, 338, _mint, 3);
      b.lantern(181, 329, scale: .6);
    case 8:
      b.oval(366, 346, 105, 33, _mint.withValues(alpha: .25), fill: true);
      b.ring(366, 337, 32, _gold, 2);
      b.ring(366, 337, 27, _blue, 1);
      for (var i = 0; i < 8; i++) {
        final a = i * math.pi / 4;
        b.line(
          366 + math.cos(a) * 29,
          337 + math.sin(a) * 29,
          366 + math.cos(a) * 35,
          337 + math.sin(a) * 35,
          _pale,
          1,
        );
      }
      b.poly(const [
        Offset(366, 305),
        Offset(373, 337),
        Offset(366, 362),
        Offset(359, 337),
      ], _mint);
      b.poly(const [
        Offset(340, 337),
        Offset(366, 330),
        Offset(393, 337),
        Offset(366, 344),
      ], _pale);
      b.circle(366, 337, 4, _gold);
    case 9:
      const points = [
        Offset(244, 68),
        Offset(304, 116),
        Offset(375, 59),
        Offset(452, 108),
        Offset(552, 62),
      ];
      for (var i = 1; i < points.length; i++) {
        b.line(
          points[i - 1].dx,
          points[i - 1].dy,
          points[i].dx,
          points[i].dy,
          _gold.withValues(alpha: .5),
          1,
        );
      }
      for (final p in points) {
        b.lantern(p.dx, p.dy, scale: .75, color: _mint);
      }
    case 10:
      b.path(
        Path()
          ..moveTo(166, 189)
          ..cubicTo(223, 11, 520, 7, 607, 193),
        _gold.withValues(alpha: .6),
        fill: false,
        width: 2,
      );
      b.path(
        Path()
          ..moveTo(190, 175)
          ..cubicTo(280, 58, 503, 49, 589, 173),
        _blue.withValues(alpha: .55),
        fill: false,
        width: 1.5,
      );
      for (var i = 0; i < 7; i++) {
        final a = math.pi + (i / 6) * math.pi,
            x = 385 + math.cos(a) * 207,
            y = 182 + math.sin(a) * 131;
        b.ring(x, y, 7 + i % 2 * 3.0, _mint, 1.5);
        b.circle(x, y, 3, _gold);
      }
      b.star(385, 52, 15, _pale);
      b.line(385, 31, 385, 73, _gold, 1);
      b.line(364, 52, 406, 52, _gold, 1);
      b.wave(373, _gold.withValues(alpha: .4), start: 177, end: 555, height: 3);
  }
}

void _shop(_Brush b, int id) {
  switch (id) {
    case 1:
      b.box(570, 211, 38, 84, _ink, 4);
      b.box(564, 292, 50, 7, _blue, 3);
      b.poly(const [
        Offset(562, 211),
        Offset(589, 182),
        Offset(616, 211),
      ], _mint);
      b.circle(589, 228, 17, _pale);
      b.ring(589, 228, 19, _gold, 2);
      for (var i = 0; i < 12; i++) {
        final a = i * math.pi / 6;
        b.line(
          589 + math.cos(a) * 13,
          228 + math.sin(a) * 13,
          589 + math.cos(a) * 15,
          228 + math.sin(a) * 15,
          _ink,
          1,
        );
      }
      b.line(589, 228, 589, 218, _ink, 2);
      b.line(589, 228, 598, 232, _ink, 2);
      b.line(589, 248, 589, 276, _gold, 1.5);
      b.circle(589, 277, 7, _gold);
    case 2:
      for (var i = 0; i < 5; i++) {
        final x = 202.0 + i * 78, y = 348.0 + (i % 2) * 13;
        b.poly([
          Offset(x - 18, y),
          Offset(x, y - 22),
          Offset(x + 20, y),
          Offset(x + 9, y + 10),
          Offset(x - 8, y + 10),
        ], i.isEven ? _pale : _blue);
        b.line(x, y - 22, x, y + 7, _gold, 1);
        b.line(x - 17, y, x + 18, y, _ink, 1);
        b.oval(x, y + 14, 45, 5, _mint.withValues(alpha: .35), width: 1);
      }
    case 3:
      for (final x in [268.0, 586.0]) {
        b.oval(x, 369, 72, 10, _blue.withValues(alpha: .4), fill: true);
        for (var i = 0; i < 5; i++) {
          final end = x - 28 + i * 14, y = 329.0 + (i % 2) * 14;
          b.path(
            Path()
              ..moveTo(x, 368)
              ..quadraticBezierTo(end, 351, end, y),
            i.isEven ? _violet : _mint,
            fill: false,
            width: 4,
          );
          b.line(end, y + 10, end - 8, y + 2, _pale, 2);
          b.line(end, y + 17, end + 8, y + 7, _pale, 2);
          b.circle(end, y, 3, _gold);
        }
      }
    case 4:
      for (var k = 0; k < 3; k++) {
        final x = 230.0 + k * 145, y = 72.0 + (k % 2) * 49;
        for (var i = 0; i < 12; i++) {
          final a = i * math.pi / 6;
          b.line(
            x + math.cos(a) * 13,
            y + math.sin(a) * 13,
            x + math.cos(a) * 29,
            y + math.sin(a) * 29,
            i.isEven ? _gold : _mint,
            1.5,
          );
          b.circle(x + math.cos(a) * 34, y + math.sin(a) * 34, 1.6, _pale);
        }
        b.star(x, y, 6, _violet);
      }
      b.path(
        Path()
          ..moveTo(139, 330)
          ..lineTo(139, 286)
          ..quadraticBezierTo(179, 251, 215, 286)
          ..lineTo(215, 330),
        _blue,
        fill: false,
        width: 3,
      );
      for (var i = 0; i < 5; i++) {
        b.lantern(
          145 + i * 16.0,
          286 - math.sin(i / 4 * math.pi) * 16,
          scale: .45,
        );
      }
  }
}

// Reuses the six already-authored earned decoration identities and geometry.
void _drawEarnedDecoration(Canvas canvas, String? id, double phase) {
  if (id == null) return;
  final index = int.tryParse(id.split('.').last);
  final p = Paint()..strokeCap = StrokeCap.round;
  switch (index) {
    case 1:
      p
        ..color = TideColors.amber.withValues(alpha: .7)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      final line = Path()
        ..moveTo(128, 191)
        ..quadraticBezierTo(235, 235, 337, 192);
      canvas.drawPath(line, p);
      p.style = PaintingStyle.fill;
      for (var i = 0; i < 8; i++) {
        final x = 140.0 + i * 25;
        final y = 196 + math.sin(i / 7 * math.pi) * 18;
        p.color = i.isEven ? TideColors.amber : TideColors.teal;
        canvas.drawPath(
          Path()
            ..moveTo(x, y)
            ..lineTo(x + 14, y + 3)
            ..lineTo(x + 5, y + 20)
            ..close(),
          p,
        );
      }
    case 2:
      for (var i = 0; i < 7; i++) {
        final x = 170.0 + i * 60,
            y = 350.0 + math.sin(phase * math.pi * 2 + i) * 2;
        p.color = TideColors.teal.withValues(alpha: .12);
        canvas.drawCircle(Offset(x, y), 14, p);
        p.color = i.isEven ? TideColors.teal : TideColors.amber;
        canvas.drawCircle(Offset(x, y), 5, p);
        p
          ..style = PaintingStyle.stroke
          ..color = TideColors.text.withValues(alpha: .35)
          ..strokeWidth = 1;
        canvas.drawOval(
          Rect.fromCenter(center: Offset(x, y + 8), width: 24, height: 4),
          p,
        );
        p.style = PaintingStyle.fill;
      }
    case 3:
      p
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..color = TideColors.muted;
      canvas.drawPath(
        Path()
          ..moveTo(305, 267)
          ..quadraticBezierTo(361, 214, 335, 150),
        p,
      );
      p.style = PaintingStyle.fill;
      p.color = TideColors.teal;
      canvas.drawPath(
        Path()
          ..moveTo(335, 110)
          ..lineTo(355, 133)
          ..lineTo(335, 161)
          ..lineTo(316, 133)
          ..close(),
        p,
      );
      p.color = TideColors.amber;
      canvas.drawPath(
        Path()
          ..moveTo(335, 110)
          ..lineTo(355, 133)
          ..lineTo(335, 133)
          ..close(),
        p,
      );
      p
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2;
      canvas.drawPath(
        Path()
          ..moveTo(335, 161)
          ..quadraticBezierTo(312, 178, 337, 190),
        p,
      );
      p.style = PaintingStyle.fill;
    case 4:
      p
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;
      for (var i = 0; i < 5; i++) {
        p.color = TideColors.teal.withValues(alpha: .5 - i * .07);
        canvas.drawOval(
          Rect.fromCenter(
            center: const Offset(362, 347),
            width: 50.0 + i * 46,
            height: 9.0 + i * 8,
          ),
          p,
        );
      }
      p.style = PaintingStyle.fill;
    case 5:
      for (var i = 0; i < 8; i++) {
        final x = 50.0 + i * 12, y = 299.0 + (i % 3) * 5;
        p
          ..color = const Color(0xFF5CA793)
          ..strokeWidth = 2;
        canvas.drawLine(Offset(x, y), Offset(x - 4, y - 20 - i % 3 * 7), p);
        p.color = i.isEven ? TideColors.amber : TideColors.teal;
        canvas.drawCircle(Offset(x - 4, y - 20 - i % 3 * 7), 3.5, p);
      }
    case 6:
      for (var i = 0; i < 3; i++) {
        final x = 387.0 + i * 56, y = 45.0 + i * 23;
        p
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = TideColors.amber.withValues(alpha: .4);
        canvas.drawLine(Offset(x - 36, y - 12), Offset(x, y), p);
        p.style = PaintingStyle.fill;
        p.color = TideColors.amber;
        canvas.drawPath(
          Path()
            ..moveTo(x, y - 7)
            ..lineTo(x + 2, y - 2)
            ..lineTo(x + 7, y)
            ..lineTo(x + 2, y + 2)
            ..lineTo(x, y + 7)
            ..lineTo(x - 2, y + 2)
            ..lineTo(x - 7, y)
            ..lineTo(x - 2, y - 2)
            ..close(),
          p,
        );
      }
  }
}
