import 'package:tideglass_core/tideglass_core.dart';
import 'strings.dart';

/// Formatting only: never feeds rounded display values into game commands.
String compactMicros(BigInt value, {bool scientific = false}) {
  final negative = value.isNegative;
  final digits = value.abs().toString();
  if (digits.length <= 9) {
    return '${negative ? '-' : ''}${formatMicros(value.abs(), decimals: 2).replaceFirst(RegExp(r'\.?0+$'), '')}';
  }
  final exponent = digits.length - 7;
  final leading = digits.substring(0, 3).padRight(3, '0');
  if (scientific || exponent >= 15) {
    return '${negative ? '-' : ''}${leading[0]}.${leading.substring(1)}e$exponent';
  }
  final group = exponent ~/ 3;
  final scale = BigInt.from(10).pow(group * 3);
  return '${negative ? '-' : ''}${formatMicros(value.abs() ~/ scale, decimals: 1)}${['', 'K', 'M', 'B', 'T'][group]}';
}

String compactFixed(Fixed value, {bool scientific = false}) => compactMicros(
  BigInt.parse(value.toDecimalString(decimals: 6).replaceAll('.', '')),
  scientific: scientific,
);
String durationLabel(Duration duration) {
  if (duration.inDays > 0) {
    return UiEnglish.durationDays(duration.inDays, duration.inHours % 24);
  }
  if (duration.inHours > 0) {
    return UiEnglish.durationHours(duration.inHours, duration.inMinutes % 60);
  }
  if (duration.inMinutes > 0) {
    return UiEnglish.durationMinutes(
      duration.inMinutes,
      duration.inSeconds % 60,
    );
  }
  return UiEnglish.durationSeconds(duration.inSeconds);
}
