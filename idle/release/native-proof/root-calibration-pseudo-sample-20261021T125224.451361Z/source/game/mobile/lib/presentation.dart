import 'package:flutter/material.dart';

/// Build with --dart-define=TIDEGLASS_PSEUDO=true to exercise expansion in the
/// actual screens. This never changes content IDs, saved values, or game rules.
abstract final class Presentation {
  static const pseudoEnabled = bool.fromEnvironment('TIDEGLASS_PSEUDO');
  static const _plain = 'AaEeIiOoUuYy';
  static const _accented = 'ÁáÉéÍíÓóÚúÝý';

  static String text(String value, {bool pseudo = pseudoEnabled}) {
    if (!pseudo || value.isEmpty || value.startsWith('[!')) return value;
    if (RegExp(r'^[+\-−]?\d[\d.,eE+\-\sKMBT%/×]*$').hasMatch(value)) {
      return value;
    }
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
    return '[!$output ${List.filled(words, 'éxtra').join(' ')}!]';
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
    if (pseudo && !result.startsWith('[!')) result = '[!$result!]';
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

/// Confirmation copy and actions share one scroll area at large text sizes.
/// This avoids reserving an unbounded fixed title/actions region around a
/// tiny scrolling body, while preserving the familiar compact dialog normally.
class ReadingDialog extends StatelessWidget {
  const ReadingDialog({
    super.key,
    this.title,
    this.content,
    this.actions = const [],
  });
  final Widget? title, content;
  final List<Widget> actions;
  @override
  Widget build(BuildContext context) {
    if (!Presentation.pseudoEnabled &&
        MediaQuery.textScalerOf(context).scale(16) <= 22.4) {
      return AlertDialog(title: title, content: content, actions: actions);
    }
    return Dialog.fullscreen(
      child: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 680),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (title != null) ...[
                    Semantics(
                      header: true,
                      child: DefaultTextStyle(
                        style: Theme.of(context).textTheme.headlineSmall!,
                        child: title!,
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                  ?content,
                  for (final action in actions) ...[
                    const SizedBox(height: 16),
                    action,
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Secondary-screen titles wrap at large text sizes and in pseudo builds.
/// Measuring the same displayed string avoids clipping translated headings.
AppBar readingAppBar(
  BuildContext context, {
  required String title,
  Widget? leading,
}) {
  final display = Presentation.text(title);
  final scale = MediaQuery.textScalerOf(context);
  final baseStyle =
      Theme.of(context).appBarTheme.titleTextStyle ??
      Theme.of(context).textTheme.titleLarge!;
  final style = baseStyle.copyWith(
    fontFamily: baseStyle.fontFamily ?? 'Roboto',
  );
  final leadingWidth =
      leading != null || (ModalRoute.of(context)?.canPop ?? false) ? 56 : 0;
  var height = kToolbarHeight;
  if (Presentation.pseudoEnabled || scale.scale(16) > 24) {
    final painter =
        TextPainter(
          text: TextSpan(text: display, style: style),
          textDirection: Directionality.of(context),
          textScaler: scale,
        )..layout(
          maxWidth: (MediaQuery.sizeOf(context).width - 32 - leadingWidth)
              .clamp(80, 10000)
              .toDouble(),
        );
    height = (painter.height + 24).clamp(kToolbarHeight, double.infinity);
    painter.dispose();
  }
  return AppBar(
    toolbarHeight: height,
    leading: leading,
    title: Text(
      display,
      style: style,
      softWrap: true,
      overflow: TextOverflow.visible,
    ),
  );
}
