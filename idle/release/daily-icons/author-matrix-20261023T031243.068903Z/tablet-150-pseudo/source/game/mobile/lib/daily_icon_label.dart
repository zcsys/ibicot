import 'package:flutter/material.dart';

import 'palette.dart';
import 'presentation.dart';

/// A supporting daily-system icon beside its complete, readable text label.
/// Wrap lets large labels retain the full width instead of squeezing them into
/// the space beside an icon. The label supplies meaning to assistive technology.
class DailyIconLabel extends StatelessWidget {
  const DailyIconLabel({
    super.key,
    required this.icon,
    required this.label,
    this.style,
  });

  final IconData icon;
  final String label;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 4,
    crossAxisAlignment: WrapCrossAlignment.center,
    children: [
      ExcludeSemantics(child: Icon(icon, size: 20, color: TideColors.teal)),
      LocalizedText(label, style: style),
    ],
  );
}
