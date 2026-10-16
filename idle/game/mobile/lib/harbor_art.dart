import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'palette.dart';

/// Original vector artwork. The same silhouettes are used in the harbor and
/// producer cards. Animated phase changes decorative pixels, never game state.
class HarborArt extends StatelessWidget {
  const HarborArt({
    super.key,
    required this.counts,
    required this.phase,
    this.restoration = 0,
    this.decoration,
  });
  final List<int> counts;
  final double phase;
  final int restoration;
  final String? decoration;

  @override
  Widget build(BuildContext context) => Semantics(
    image: true,
    label:
        'A lighthouse watches over the ocean. $restoration of six constellations restored. ${counts.where((n) => n > 0).length} kinds of lightkeeper are at work.',
    child: ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: AspectRatio(
        aspectRatio: 1.65,
        child: CustomPaint(
          painter: _HarborPainter(counts, phase, restoration, decoration),
        ),
      ),
    ),
  );
}

class ProducerArt extends StatelessWidget {
  const ProducerArt({
    super.key,
    required this.tier,
    required this.active,
    this.size = 58,
  });
  final int tier;
  final bool active;
  final double size;
  @override
  Widget build(BuildContext context) => SizedBox.square(
    dimension: size,
    child: ExcludeSemantics(
      child: CustomPaint(painter: _ProducerPainter(tier, active)),
    ),
  );
}

class _HarborPainter extends CustomPainter {
  _HarborPainter(this.counts, this.phase, this.restoration, this.decoration);
  final List<int> counts;
  final double phase;
  final int restoration;
  final String? decoration;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 640, size.height / 388);
    final p = Paint();
    final restored = restoration.clamp(0, 6);
    final dawn = restored / 6;
    p.shader = LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [
        Color.lerp(const Color(0xFF0D273A), const Color(0xFF243F54), dawn)!,
        Color.lerp(const Color(0xFF173B4A), const Color(0xFF447172), dawn)!,
        const Color(0xFF163743),
      ],
      stops: [0, .62, 1],
    ).createShader(const Rect.fromLTWH(0, 0, 640, 388));
    canvas.drawRect(const Rect.fromLTWH(0, 0, 640, 388), p);
    p.shader = null;

    // Hand-positioned quiet star field. No random re-layout between frames.
    const stars = [
      Offset(42, 48),
      Offset(84, 89),
      Offset(137, 37),
      Offset(190, 70),
      Offset(262, 34),
      Offset(309, 86),
      Offset(354, 26),
      Offset(402, 71),
      Offset(492, 34),
      Offset(560, 89),
      Offset(598, 43),
      Offset(610, 130),
      Offset(525, 151),
      Offset(351, 137),
      Offset(214, 118),
      Offset(66, 149),
      Offset(144, 129),
      Offset(455, 125),
    ];
    for (var i = 0; i < stars.length; i++) {
      p.color = TideColors.text.withValues(alpha: .2 + (i % 3) * .14);
      canvas.drawCircle(stars[i], i % 4 == 0 ? 1.5 : .85, p);
    }
    // The crescent and a soft atmospheric halo.
    p.shader = const RadialGradient(
      colors: [Color(0x155CE8D4), Color(0x0064DCCB)],
    ).createShader(const Rect.fromLTWH(400, -30, 200, 200));
    canvas.drawCircle(const Offset(500, 70), 100, p);
    p.shader = null;
    p.color = const Color(0xFFE5DDBB);
    canvas.drawCircle(const Offset(504, 67), 21, p);
    p.color = const Color(0xFF102D3F);
    canvas.drawCircle(const Offset(512, 60), 20, p);

    final active = restored;
    const constellations = [
      [Offset(217, 64), Offset(235, 48), Offset(254, 65), Offset(234, 75)],
      [Offset(284, 35), Offset(306, 47), Offset(319, 25)],
      [Offset(325, 104), Offset(348, 79), Offset(368, 102), Offset(348, 119)],
      [Offset(389, 45), Offset(409, 28), Offset(432, 45), Offset(414, 65)],
      [Offset(410, 132), Offset(430, 108), Offset(453, 123), Offset(472, 109)],
      [Offset(550, 81), Offset(571, 61), Offset(588, 89), Offset(568, 111)],
    ];
    p
      ..color = TideColors.teal.withValues(alpha: .22)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    for (var i = 0; i < active; i++) {
      final points = constellations[i];
      for (var star = 1; star < points.length; star++) {
        canvas.drawLine(points[star - 1], points[star], p);
      }
    }
    p.style = PaintingStyle.fill;
    for (var i = 0; i < active; i++) {
      for (final point in constellations[i]) {
        p.color = TideColors.teal.withValues(alpha: .12);
        canvas.drawCircle(point, 6, p);
        p.color = TideColors.teal;
        canvas.drawCircle(point, 1.7, p);
      }
    }

    // Distant islands deliberately leave the center open for light.
    p.color = const Color(0xFF102D38);
    canvas.drawPath(
      Path()
        ..moveTo(0, 222)
        ..lineTo(0, 192)
        ..lineTo(48, 170)
        ..lineTo(76, 184)
        ..lineTo(117, 164)
        ..lineTo(153, 190)
        ..lineTo(205, 196)
        ..lineTo(251, 220)
        ..close(),
      p,
    );
    canvas.drawPath(
      Path()
        ..moveTo(435, 221)
        ..lineTo(488, 187)
        ..lineTo(518, 201)
        ..lineTo(551, 172)
        ..lineTo(592, 180)
        ..lineTo(640, 165)
        ..lineTo(640, 224)
        ..close(),
      p,
    );
    p.shader = const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [Color(0xFF194957), Color(0xFF0D2C3B)],
    ).createShader(const Rect.fromLTWH(0, 221, 640, 167));
    canvas.drawRect(const Rect.fromLTWH(0, 221, 640, 167), p);
    p.shader = null;
    p
      ..color = const Color(0xFF42707B).withValues(alpha: .45)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    canvas.drawLine(const Offset(0, 221), const Offset(640, 221), p);
    for (var row = 0; row < 10; row++) {
      final y = 236.0 + row * 15;
      final wave = Path()..moveTo(-20, y);
      for (var col = 0; col < 9; col++) {
        final x = col * 90.0 - 20;
        final sway = math.sin(phase * math.pi * 2 + row * .7) * 3;
        wave.cubicTo(x + 25, y + sway, x + 55, y - sway, x + 90, y);
      }
      p.color = Color.lerp(
        const Color(0xFF407581),
        const Color(0xFF214451),
        row / 10,
      )!.withValues(alpha: .35);
      canvas.drawPath(wave, p);
    }
    p.style = PaintingStyle.fill;
    // The lighthouse beam falls behind structures and reflects in the water.
    p.shader = const LinearGradient(
      colors: [Color(0x55F7DA97), Color(0x00F7DA97)],
    ).createShader(const Rect.fromLTWH(111, 122, 365, 95));
    canvas.drawPath(
      Path()
        ..moveTo(110, 157)
        ..lineTo(476, 113)
        ..lineTo(476, 211)
        ..close(),
      p,
    );
    p.shader = null;
    for (var i = 0; i < 6; i++) {
      p.color = TideColors.amber.withValues(alpha: .12 - i * .014);
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(
            center: Offset(109.0 + i * 2, 278.0 + i * 13),
            width: 29 + i * 8,
            height: 2,
          ),
          const Radius.circular(2),
        ),
        p,
      );
    }
    p.color = const Color(0xFF122B34);
    canvas.drawPath(
      Path()
        ..moveTo(24, 294)
        ..lineTo(49, 266)
        ..lineTo(95, 255)
        ..lineTo(134, 269)
        ..lineTo(162, 299)
        ..lineTo(129, 319)
        ..lineTo(55, 318)
        ..close(),
      p,
    );
    p.color = const Color(0xFF52646A);
    canvas.drawPath(
      Path()
        ..moveTo(44, 291)
        ..lineTo(68, 271)
        ..lineTo(104, 265)
        ..lineTo(130, 284)
        ..close(),
      p,
    );
    // Tower, pale stone side and dark teal side.
    p.color = const Color(0xFFD4D7C8);
    canvas.drawPath(
      Path()
        ..moveTo(88, 259)
        ..lineTo(96, 174)
        ..lineTo(119, 174)
        ..lineTo(131, 269)
        ..lineTo(109, 280)
        ..close(),
      p,
    );
    p.color = const Color(0xFF6E999A);
    canvas.drawPath(
      Path()
        ..moveTo(109, 181)
        ..lineTo(119, 174)
        ..lineTo(131, 269)
        ..lineTo(109, 280)
        ..close(),
      p,
    );
    p.color = const Color(0xFF244F5D);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(99, 239, 11, 31),
        const Radius.circular(6),
      ),
      p,
    );
    for (final y in [196.0, 217.0]) {
      canvas.drawRect(Rect.fromLTWH(102, y, 5, 9), p);
    }
    p.color = const Color(0xFF315A65);
    canvas.drawRect(const Rect.fromLTWH(87, 174, 44, 7), p);
    p.color = TideColors.amber;
    canvas.drawRect(const Rect.fromLTWH(97, 147, 23, 27), p);
    p.color = const Color(0xFF537B81);
    canvas.drawPath(
      Path()
        ..moveTo(88, 147)
        ..lineTo(108, 128)
        ..lineTo(131, 147)
        ..close(),
      p,
    );
    p
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..color = const Color(0xFF214451);
    canvas.drawRect(const Rect.fromLTWH(95, 147, 27, 27), p);
    canvas.drawLine(const Offset(109, 147), const Offset(109, 174), p);
    p.style = PaintingStyle.fill;
    p.color = TideColors.amber;
    canvas.drawCircle(const Offset(108, 129), 2, p);

    // The fleet spreads across a coherent harbor, with undiscovered silhouettes.
    const positions = [
      Offset(222, 310),
      Offset(320, 269),
      Offset(404, 320),
      Offset(487, 267),
      Offset(568, 316),
    ];
    for (var i = 0; i < 5; i++) {
      canvas.save();
      final bob = counts[i] > 0 ? math.sin(phase * math.pi * 2 + i) * 1.5 : 0.0;
      canvas.translate(positions[i].dx, positions[i].dy + bob);
      canvas.scale(.92);
      drawProducer(canvas, i, counts[i] > 0);
      canvas.restore();
    }
    for (var i = 0; i < restored; i++) {
      final x = 190.0 + i * 66;
      p.color = TideColors.amber.withValues(alpha: .12);
      canvas.drawCircle(Offset(x, 218), 9, p);
      p.color = TideColors.amber;
      canvas.drawCircle(Offset(x, 218), 2.2, p);
    }
    _drawDecoration(canvas, decoration, phase);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _HarborPainter old) =>
      old.phase != phase ||
      old.counts != counts ||
      old.restoration != restoration ||
      old.decoration != decoration;
}

class _ProducerPainter extends CustomPainter {
  const _ProducerPainter(this.tier, this.active);
  final int tier;
  final bool active;
  @override
  void paint(Canvas canvas, Size size) {
    canvas.translate(size.width / 2, size.height * .72);
    canvas.scale(size.width / 80);
    drawProducer(canvas, tier, active);
  }

  @override
  bool shouldRepaint(covariant _ProducerPainter old) =>
      old.tier != tier || old.active != active;
}

void drawProducer(Canvas canvas, int tier, bool active) {
  final p = Paint()
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round;
  final base = active ? const Color(0xFF477F87) : const Color(0xFF28454F);
  final light = active ? TideColors.teal : const Color(0xFF50626A);
  final warm = active ? TideColors.amber : const Color(0xFF50626A);
  if (active) {
    p.shader = RadialGradient(
      colors: [light.withValues(alpha: .15), light.withValues(alpha: 0)],
    ).createShader(const Rect.fromLTWH(-40, -55, 80, 80));
    canvas.drawCircle(const Offset(0, -15), 40, p);
    p.shader = null;
  }
  p.color = const Color(0xFF0B222C);
  canvas.drawOval(const Rect.fromLTWH(-36, 5, 72, 9), p);
  p.color = base;
  canvas.drawPath(
    Path()
      ..moveTo(-34, 0)
      ..lineTo(34, 0)
      ..lineTo(24, 10)
      ..lineTo(-23, 10)
      ..close(),
    p,
  );
  p.color = light.withValues(alpha: .65);
  canvas.drawRect(const Rect.fromLTWH(-32, -2, 64, 3), p);
  switch (tier) {
    case 0:
      p
        ..color = base
        ..strokeWidth = 3;
      canvas.drawLine(const Offset(-6, 0), const Offset(-6, -51), p);
      p.color = warm;
      canvas.drawPath(
        Path()
          ..moveTo(-2, -47)
          ..lineTo(24, -12)
          ..lineTo(-2, -12)
          ..close(),
        p,
      );
      p.color = light;
      canvas.drawPath(
        Path()
          ..moveTo(-10, -42)
          ..lineTo(-29, -10)
          ..lineTo(-10, -10)
          ..close(),
        p,
      );
      p.color = warm;
      canvas.drawCircle(const Offset(22, -5), 3, p);
    case 1:
      p
        ..color = base
        ..strokeWidth = 3;
      for (final x in [-19.0, 0.0, 19.0]) {
        canvas.drawLine(Offset(x, -3), Offset(x, -24), p);
        p.color = light;
        canvas.drawPath(
          Path()
            ..moveTo(x, -43)
            ..lineTo(x + 9, -26)
            ..lineTo(x, -18)
            ..lineTo(x - 9, -26)
            ..close(),
          p,
        );
        p.color = warm;
        canvas.drawLine(Offset(x, -40), Offset(x, -21), p);
        p.color = base;
      }
    case 2:
      p
        ..color = base
        ..strokeWidth = 4;
      canvas.drawLine(const Offset(0, -3), const Offset(0, -31), p);
      p
        ..style = PaintingStyle.stroke
        ..color = light;
      canvas.drawCircle(const Offset(0, -29), 22, p);
      p.style = PaintingStyle.fill;
      for (var i = 0; i < 8; i++) {
        final a = i * math.pi / 4;
        p
          ..color = base
          ..strokeWidth = 3;
        canvas.drawLine(
          const Offset(0, -29),
          Offset(math.cos(a) * 19, -29 + math.sin(a) * 19),
          p,
        );
      }
      p.color = warm;
      canvas.drawCircle(const Offset(0, -29), 6, p);
    case 3:
      p
        ..color = base
        ..strokeWidth = 4;
      canvas.drawLine(const Offset(-24, 0), const Offset(-24, -46), p);
      canvas.drawLine(const Offset(24, 0), const Offset(24, -46), p);
      canvas.drawLine(const Offset(-25, -43), const Offset(25, -43), p);
      for (var i = 0; i < 5; i++) {
        p
          ..color = i.isEven ? light : warm
          ..strokeWidth = 2;
        final x = -16.0 + i * 8;
        canvas.drawPath(
          Path()
            ..moveTo(x, -39)
            ..quadraticBezierTo(x - 10, -23, x, -6),
          p..style = PaintingStyle.stroke,
        );
      }
      p.style = PaintingStyle.fill;
    case 4:
      p.color = base;
      canvas.drawRect(const Rect.fromLTWH(-25, -24, 50, 24), p);
      p.color = light;
      canvas.drawArc(
        const Rect.fromLTWH(-27, -51, 54, 54),
        math.pi,
        math.pi,
        true,
        p,
      );
      p.color = base;
      canvas.drawRect(const Rect.fromLTWH(-27, -26, 54, 4), p);
      p
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = base;
      canvas.drawArc(
        const Rect.fromLTWH(-13, -51, 26, 54),
        math.pi,
        math.pi,
        false,
        p,
      );
      p.style = PaintingStyle.fill;
      p.color = warm;
      canvas.drawRect(const Rect.fromLTWH(-4, -19, 8, 19), p);
      canvas.drawCircle(const Offset(0, -53), 3, p);
  }
}

/// Six earned decorations have concrete, distinct silhouettes. They never
/// affect the simulation; selection is the only input beyond visual phase.
void _drawDecoration(Canvas canvas, String? id, double phase) {
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
