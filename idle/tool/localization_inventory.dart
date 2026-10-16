// Run with .tooling/flutter/bin/cache/dart-sdk/bin/dart --packages=.tooling/flutter/packages/flutter_tools/.dart_tool/package_config.json
// tool/localization_inventory.dart <inventory|migrate> <dart files...>
// Analyzer parses strings and interpolation expressions; no regex edits Dart.
import 'dart:convert';
import 'dart:io';
import 'package:analyzer/dart/analysis/utilities.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:analyzer/dart/ast/visitor.dart';

class _Strings extends RecursiveAstVisitor<void> {
  final all = <StringLiteral>[];
  @override
  void visitSimpleStringLiteral(SimpleStringLiteral node) {
    if (node.parent is! AdjacentStrings) all.add(node);
    super.visitSimpleStringLiteral(node);
  }
  @override
  void visitAdjacentStrings(AdjacentStrings node) {
    all.add(node);
    super.visitAdjacentStrings(node);
  }
  @override
  void visitStringInterpolation(StringInterpolation node) {
    if (node.parent is! AdjacentStrings) all.add(node);
    super.visitStringInterpolation(node);
  }
}

class _PresentationSites extends RecursiveAstVisitor<void> {
  final expressions = <Expression>[];
  final constOffsets = <int>{};
  @override
  void visitNamedExpression(NamedExpression node) {
    final name = node.name.label.name;
    final call = node.parent?.parent;
    final type = call is InstanceCreationExpression
        ? call.constructorName.type.name.lexeme
        : call is MethodInvocation ? call.methodName.name : '';
    final label = name == 'label' && ['Semantics', 'Slider', 'NavigationDestination', 'DropdownMenuEntry'].contains(type);
    if ((label || ['tooltip', 'semanticsLabel', 'labelText', 'hintText', 'helperText', 'errorText'].contains(name)) &&
        !node.expression.toSource().startsWith('Presentation.')) {
      expressions.add(node.expression);
      for (AstNode? parent = node.parent; parent != null; parent = parent.parent) {
        if (parent is InstanceCreationExpression && parent.keyword?.lexeme == 'const') {
          constOffsets.add(parent.keyword!.offset);
        }
        if (parent is TypedLiteral && parent.constKeyword != null) {
          constOffsets.add(parent.constKeyword!.offset);
        }
      }
    }
    super.visitNamedExpression(node);
  }
}

String reason(StringLiteral node) {
  final raw = node.stringValue ?? node.toSource();
  for (AstNode? at = node; at != null; at = at.parent) {
    if (at is Directive) return 'import_or_directive';
    if (at is InstanceCreationExpression) {
      final name = at.constructorName.type.name.lexeme;
      if (name.endsWith('Key')) return 'stable_widget_key';
      if (name.endsWith('Exception') || name.endsWith('Error') || name == 'RegExp') {
        return 'internal_diagnostic_or_pattern';
      }
    }
    if (at is MapLiteralEntry && at.key == node) return 'data_key';
    if (at is Pattern) return 'business_pattern';
  }
  final parent = node.parent;
  if (parent is BinaryExpression && ['==', '!='].contains(parent.operator.lexeme)) {
    return 'business_comparison';
  }
  if (parent is IndexExpression && parent.index == node) return 'data_key';
  final words = node is StringInterpolation
      ? node.elements.whereType<InterpolationString>().map((e) => e.value).join('')
      : raw;
  if (!RegExp('[A-Za-z]').hasMatch(words)) return 'numeric_or_symbol_format';
  if (RegExp(r'^[a-z][a-z0-9_.:/-]*$').hasMatch(words)) return 'identifier_or_code';
  if (words.startsWith('package:') || words.endsWith('.dart') || words.startsWith('assets/')) {
    return 'resource_path';
  }
  return 'english_candidate';
}

String dartQuote(String value) => jsonEncode(value).replaceAll(r'$', r'\$');

void main(List<String> args) {
  final mode = args.first;
  final inventory = <Map<String, Object?>>[];
  final declarations = <String>[];
  final usedNames = <String>{};
  final catalogue = File('game/mobile/lib/strings.dart');
  final existing = catalogue.readAsStringSync();
  for (final match in RegExp(r'static (?:const|String) (\w+)').allMatches(existing)) {
    usedNames.add(match.group(1)!);
  }
  for (final path in args.skip(1)) {
    final file = File(path);
    final source = file.readAsStringSync();
    final unit = parseString(content: source, throwIfDiagnostics: false).unit;
    if (mode == 'present') {
      final sites = _PresentationSites();
      unit.accept(sites);
      final edits = <(int, int, String)>[
        for (final expression in sites.expressions)
          (expression.offset, expression.length, 'Presentation.text(${source.substring(expression.offset, expression.end)})'),
        for (final offset in sites.constOffsets) (offset, 6, ''),
      ]..sort((a, b) => b.$1.compareTo(a.$1));
      var next = source;
      for (final edit in edits) { next = next.replaceRange(edit.$1, edit.$1 + edit.$2, edit.$3); }
      file.writeAsStringSync(next);
      continue;
    }
    final visitor = _Strings();
    unit.accept(visitor);
    final selected = <StringLiteral, String>{};
    final prefix = path.split('/').last.replaceAll('.dart', '').split('_').first;
    for (final node in visitor.all) {
      final classification = reason(node);
      inventory.add({
        'file': path, 'line': '\n'.allMatches(source.substring(0, node.offset)).length + 1,
        'classification': classification, 'source': node.toSource(),
      });
      if (classification != 'english_candidate') continue;
      final words = (node.stringValue ?? node.toSource())
          .replaceAll(RegExp(r'[^A-Za-z]+'), ' ').trim().split(' ').take(7).join(' ');
      var name = prefix + words.split(' ').map((s) => s.isEmpty ? '' : s[0].toUpperCase() + s.substring(1)).join();
      if (name.length > 70) name = name.substring(0, 70);
      final base = name;
      var i = 2;
      while (usedNames.contains(name)) { name = '$base${i++}'; }
      usedNames.add(name);
      selected[node] = name;
    }
    if (mode != 'migrate') continue;
    String rewritten(int start, int end) {
      var result = source.substring(start, end);
      final nested = selected.keys.where((n) => n.offset >= start && n.end <= end).toList()
        ..sort((a, b) => a.offset.compareTo(b.offset));
      final outer = <StringLiteral>[];
      for (final node in nested) {
        if (!outer.any((p) => node.offset >= p.offset && node.end <= p.end)) outer.add(node);
      }
      for (final node in outer.reversed) {
        result = result.replaceRange(node.offset - start, node.end - start, replacement(node));
      }
      return result;
    }
    replacement = (StringLiteral node) {
      final name = selected[node]!;
      if (node.stringValue == null) {
        final template = StringBuffer();
        final arguments = <String>[];
        void append(StringLiteral literal) {
          if (literal is AdjacentStrings) {
            for (final part in literal.strings) { append(part); }
            return;
          }
          if (literal is SimpleStringLiteral) { template.write(literal.value); return; }
          for (final element in (literal as StringInterpolation).elements) {
          if (element is InterpolationString) template.write(element.value);
          if (element is InterpolationExpression) {
            final index = arguments.length;
            template.write('{value$index}');
            var expression = rewritten(element.expression.offset, element.expression.end);
            if (RegExp(r"\['(?:title|intro|completion|body|hint)'\]|\.title\b|producerNames|\.instructions\b").hasMatch(expression)) {
              expression = 'Presentation.authored(($expression).toString())';
            }
            arguments.add(expression);
          }
          }
        }
        append(node);
        if (!declarations.any((s) => s.startsWith('  static String $name('))) {
          declarations.add('  static String $name(${List.generate(arguments.length, (i) => 'Object? value$i').join(', ')}) => Presentation.template(${dartQuote(template.toString())}, {${List.generate(arguments.length, (i) => "'value$i': value$i").join(', ')}});');
        }
        return 'UiEnglish.$name(${arguments.join(', ')})';
      }
      if (!declarations.any((s) => s.startsWith('  static const $name ='))) {
        declarations.add('  static const $name = ${dartQuote(node.stringValue!)};');
      }
      return 'UiEnglish.$name';
    };
    var next = rewritten(0, source.length);
    // Constructor replacement retains existing const expressions and properties.
    next = next.replaceAll(RegExp(r'\bText\('), 'LocalizedText(');
    if (!next.contains("import 'strings.dart';")) next = "import 'strings.dart';\n$next";
    if (!next.contains("import 'presentation.dart';")) next = "import 'presentation.dart';\n$next";
    file.writeAsStringSync(next);
  }
  if (mode == 'migrate' && declarations.isNotEmpty) {
    var text = existing;
    if (!text.contains("import 'presentation.dart';")) text = "import 'presentation.dart';\n$text";
    if (!text.contains('abstract final class UiEnglish')) {
      text += '\n/// English UI catalogue. Templates preserve inserted values in pseudo builds.\nabstract final class UiEnglish {\n}\n';
    }
    final end = text.lastIndexOf('}');
    text = text.replaceRange(end, end, '${declarations.join('\n')}\n');
    catalogue.writeAsStringSync(text);
  }
  stdout.writeln(const JsonEncoder.withIndent('  ').convert(inventory));
}

late String Function(StringLiteral) replacement;
