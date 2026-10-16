import 'package:flutter/material.dart';

/// Build with --dart-define=TIDEGLASS_PSEUDO=true to exercise expansion in the
/// actual screens. This never changes content IDs, saved values, or game rules.
abstract final class Presentation {
  static const pseudoEnabled = bool.fromEnvironment('TIDEGLASS_PSEUDO');
  static const _plain = 'AaEeIiOoUuYy';
  static const _accented = 'ÁáÉéÍíÓóÚúÝý';

  static String text(String value, {bool pseudo = pseudoEnabled}) {
    if (!pseudo || value.isEmpty || value.startsWith('⟦')) return value;
    if (!RegExp('[A-Za-z]').hasMatch(value)) return value;
    final output = StringBuffer();
    for (final rune in value.runes) {
      final character = String.fromCharCode(rune);
      final index = _plain.indexOf(character);
      output.write(index < 0 ? character : _accented[index]);
    }
    // Separate words let expansion wrap naturally, instead of creating an
    // artificial unbreakable token that no real translation would require.
    final words = (value.length * .35 / 5).ceil().clamp(1, 100);
    return '⟦$output ${List.filled(words, 'éxtra').join(' ')}⟧';
  }

  /// Expand the surrounding English template before inserting protected values
  /// such as native prices, recovery codes, identifiers, and formatted numbers.
  static String template(
    String english,
    Map<String, Object?> values, {
    bool pseudo = pseudoEnabled,
  }) {
    var protected = english;
    final replacements = <String, String>{};
    for (final entry in values.entries) {
      final token = String.fromCharCode(0xe000 + replacements.length);
      protected = protected.replaceAll('{${entry.key}}', token);
      replacements[token] = '${entry.value}';
    }
    var result = text(protected, pseudo: pseudo);
    if (pseudo && !result.startsWith('⟦')) result = '⟦$result⟧';
    for (final entry in replacements.entries) {
      result = result.replaceAll(entry.key, entry.value);
    }
    return result;
  }

  /// Authored prose/names are display-only. Their underlying JSON remains exact.
  static String authored(String value) => text(value);
}

/// Const-compatible presentation boundary. Existing English constants and
/// authored catalogue prose both exercise the compile-time pseudo mode here.
/// Use ordinary SelectableText for secret/export material and Text for raw
/// native prices; template insertion protects those values in mixed labels.
class LocalizedText extends StatelessWidget {
  const LocalizedText(
    this.data, {
    super.key,
    this.style,
    this.strutStyle,
    this.textAlign,
    this.textDirection,
    this.locale,
    this.softWrap,
    this.overflow,
    this.textScaler,
    this.maxLines,
    this.semanticsLabel,
    this.textWidthBasis,
    this.textHeightBehavior,
    this.selectionColor,
  });
  final String data;
  final TextStyle? style;
  final StrutStyle? strutStyle;
  final TextAlign? textAlign;
  final TextDirection? textDirection;
  final Locale? locale;
  final bool? softWrap;
  final TextOverflow? overflow;
  final TextScaler? textScaler;
  final int? maxLines;
  final String? semanticsLabel;
  final TextWidthBasis? textWidthBasis;
  final TextHeightBehavior? textHeightBehavior;
  final Color? selectionColor;

  @override
  Widget build(BuildContext context) => Text(
    Presentation.text(data),
    style: style,
    strutStyle: strutStyle,
    textAlign: textAlign,
    textDirection: textDirection,
    locale: locale,
    softWrap: softWrap,
    overflow: overflow,
    textScaler: textScaler,
    maxLines: maxLines,
    semanticsLabel: semanticsLabel == null
        ? null
        : Presentation.text(semanticsLabel!),
    textWidthBasis: textWidthBasis,
    textHeightBehavior: textHeightBehavior,
    selectionColor: selectionColor,
  );
}
