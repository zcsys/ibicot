// Original six earned decorations, retained under the same identities.
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
