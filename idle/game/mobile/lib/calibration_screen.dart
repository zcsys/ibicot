import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'calibration_pattern.dart';
import 'palette.dart';

/// Both solve routes invoke the identical command. The caller owns Focus and
/// collectible accounting; this widget only chooses a pattern and a route.
class CalibrationScreen extends StatefulWidget {
  const CalibrationScreen({
    super.key,
    required this.patterns,
    required this.focusCharges,
    required this.collectedIds,
    required this.onComplete,
  });
  final List<CalibrationPattern> patterns;
  final int Function() focusCharges;
  final Set<String> Function() collectedIds;
  final bool Function(String patternId) onComplete;
  @override
  State<CalibrationScreen> createState() => _CalibrationScreenState();
}

class _CalibrationScreenState extends State<CalibrationScreen> {
  int selected = 0;
  late CalibrationRoute route;
  bool claimed = false;
  String? notice;
  CalibrationPattern get pattern => widget.patterns[selected];
  @override
  void initState() {
    super.initState();
    route = CalibrationRoute(pattern);
  }

  void choose(int index) => setState(() {
    selected = index;
    route = CalibrationRoute(pattern);
    claimed = false;
    notice = null;
  });
  void claim() {
    if (claimed) return;
    final accepted = widget.onComplete(pattern.id);
    setState(() {
      claimed = accepted;
      notice = accepted
          ? UiEnglish.calibrationPatternCollectedTenMinutesOfFocusAdded
          : UiEnglish.calibrationNoFocusChargeIsAvailableYetYour;
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const LocalizedText(UiEnglish.calibrationConstellationCalibration),
    ),
    body: SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const LocalizedText(
                  UiEnglish.calibrationAQuieterWayToBrightenTheSky,
                  style: TextStyle(color: TideColors.muted),
                ),
                const SizedBox(height: 20),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (var i = 0; i < widget.patterns.length; i++)
                      ChoiceChip(
                        label: LocalizedText('${i + 1}'),
                        tooltip: Presentation.text(widget.patterns[i].title),
                        selected: i == selected,
                        onSelected: (_) => choose(i),
                        avatar:
                            widget.collectedIds().contains(
                              widget.patterns[i].id,
                            )
                            ? const Icon(Icons.check, size: 16)
                            : null,
                      ),
                  ],
                ),
                const SizedBox(height: 22),
                LocalizedText(
                  pattern.title,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                LocalizedText(
                  pattern.intro,
                  style: const TextStyle(color: TideColors.muted),
                ),
                const SizedBox(height: 14),
                LocalizedText(pattern.instructions),
                const SizedBox(height: 20),
                Semantics(
                  image: true,
                  label: Presentation.text(
                    UiEnglish.calibrationPatternTitleRouteVisitedLengthOfPattern(
                      Presentation.authored((pattern.title).toString()),
                      route.visited.length,
                      pattern.stars.length,
                      pattern.star(route.visited.last).label,
                    ),
                  ),
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: CustomPaint(
                      painter: _SkyPainter(pattern, route.visited),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                LocalizedText(
                  route.solved
                      ? UiEnglish.calibrationTheConstellationIsAligned
                      : route.nextStars.isEmpty
                      ? UiEnglish.calibrationThisRouteHasNoNextStarUndo
                      : UiEnglish.calibrationChooseTheNextConnectedStar,
                  style: const TextStyle(color: TideColors.amber),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    for (final star in route.nextStars)
                      OutlinedButton(
                        key: ValueKey('star-${star.key}'),
                        onPressed: claimed
                            ? null
                            : () => setState(() => route.visit(star.key)),
                        child: LocalizedText(star.label),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 12,
                  children: [
                    TextButton.icon(
                      onPressed: route.visited.length > 1 && !claimed
                          ? () => setState(route.undo)
                          : null,
                      icon: const Icon(Icons.undo),
                      label: const LocalizedText(UiEnglish.calibrationUndo),
                    ),
                    TextButton.icon(
                      onPressed: claimed ? null : () => setState(route.restart),
                      icon: const Icon(Icons.refresh),
                      label: const LocalizedText(UiEnglish.calibrationRestart),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                FilledButton(
                  key: const ValueKey('claim-routed-calibration'),
                  onPressed:
                      route.solved && !claimed && widget.focusCharges() > 0
                      ? claim
                      : null,
                  child: LocalizedText(
                    claimed
                        ? UiEnglish.calibrationConstellationCollected
                        : UiEnglish.calibrationCollectPatternFocus,
                  ),
                ),
                if (notice != null) ...[
                  const SizedBox(height: 12),
                  Semantics(
                    liveRegion: true,
                    child: LocalizedText(
                      notice!,
                      style: const TextStyle(color: TideColors.teal),
                    ),
                  ),
                ],
                const SizedBox(height: 24),
                const Divider(),
                const SizedBox(height: 24),
                LocalizedText(
                  UiEnglish.calibrationLetTheCrewHelp,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                LocalizedText(
                  pattern.accessibleDescription,
                  style: const TextStyle(color: TideColors.muted),
                ),
                const SizedBox(height: 14),
                OutlinedButton(
                  key: const ValueKey('claim-accessible-calibration'),
                  onPressed: !claimed && widget.focusCharges() > 0
                      ? claim
                      : null,
                  child: LocalizedText(pattern.accessibleLabel),
                ),
                const SizedBox(height: 8),
                LocalizedText(
                  UiEnglish.calibrationWidgetFocusChargesFocusChargesAvailableNoTimer(
                    widget.focusCharges(),
                  ),
                  style: const TextStyle(color: TideColors.muted, fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class _SkyPainter extends CustomPainter {
  const _SkyPainter(this.pattern, this.visited);
  final CalibrationPattern pattern;
  final List<int> visited;
  @override
  void paint(Canvas canvas, Size size) {
    final inset = 28.0;
    Offset position(int key) {
      final s = pattern.star(key);
      return Offset(
        inset + s.x * (size.width - inset * 2),
        inset + s.y * (size.height - inset * 2),
      );
    }

    final paint = Paint()..color = TideColors.panel;
    canvas.drawRRect(
      RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(20)),
      paint,
    );
    paint
      ..color = TideColors.line
      ..strokeWidth = 1.5;
    for (final edge in pattern.edges) {
      canvas.drawLine(position(edge.$1), position(edge.$2), paint);
    }
    paint
      ..color = TideColors.teal
      ..strokeWidth = 3;
    for (var i = 1; i < visited.length; i++) {
      canvas.drawLine(position(visited[i - 1]), position(visited[i]), paint);
    }
    for (final star in pattern.stars) {
      final point = position(star.key), selected = visited.contains(star.key);
      paint.color = selected ? TideColors.teal : TideColors.raised;
      canvas.drawCircle(point, 12, paint);
      paint
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..color = star.key == pattern.start || star.key == pattern.end
            ? TideColors.amber
            : TideColors.muted;
      canvas.drawCircle(point, 12, paint);
      paint.style = PaintingStyle.fill;
      final title = TextPainter(
        text: TextSpan(
          text: star.label,
          style: const TextStyle(color: TideColors.text, fontSize: 11),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      title.paint(canvas, point + Offset(-title.width / 2, 17));
      if (star.key == pattern.start || star.key == pattern.end) {
        final role = TextPainter(
          text: TextSpan(
            text: star.key == pattern.start
                ? UiEnglish.calibrationSTART
                : UiEnglish.calibrationFINISH,
            style: const TextStyle(
              color: TideColors.amber,
              fontSize: 9,
              letterSpacing: 1,
            ),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        role.paint(canvas, point + Offset(-role.width / 2, -26));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SkyPainter old) =>
      old.pattern != pattern || old.visited.toString() != visited.toString();
}
