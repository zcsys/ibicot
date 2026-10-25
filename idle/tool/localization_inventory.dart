// Run with .tooling/flutter/bin/cache/dart-sdk/bin/dart --packages=.tooling/flutter/packages/flutter_tools/.dart_tool/package_config.json
// tool/localization_inventory.dart inventory <dart files...>
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

String reason(StringLiteral node) {
  final raw = node.stringValue ?? node.toSource();
  for (AstNode? at = node; at != null; at = at.parent) {
    if (at is Directive) return 'import_or_directive';
    if (at is InstanceCreationExpression) {
      final name = at.constructorName.type.name.lexeme;
      if (name.endsWith('Key')) return 'stable_widget_key';
      if (name.endsWith('Exception') ||
          name.endsWith('Error') ||
          name == 'RegExp') {
        return 'internal_diagnostic_or_pattern';
      }
    }
    if (at is MapLiteralEntry && at.key == node) return 'data_key';
    if (at is DartPattern) return 'business_pattern';
  }
  final parent = node.parent;
  if (parent is BinaryExpression &&
      ['==', '!='].contains(parent.operator.lexeme)) {
    return 'business_comparison';
  }
  if (parent is IndexExpression && parent.index == node) return 'data_key';
  final words = node is StringInterpolation
      ? node.elements
            .whereType<InterpolationString>()
            .map((e) => e.value)
            .join('')
      : raw;
  if (!RegExp('[A-Za-z]').hasMatch(words)) return 'numeric_or_symbol_format';
  if (RegExp(r'^[a-z][A-Za-z0-9_.:/-]*$').hasMatch(words))
    return 'identifier_or_code';
  if (RegExp(r'^[A-Za-z0-9_.:/-]+$').hasMatch(words) &&
      RegExp(r'[_.:/]').hasMatch(words)) {
    return 'machine_format';
  }
  if (words.startsWith('package:') ||
      words.endsWith('.dart') ||
      words.startsWith('assets/')) {
    return 'resource_path';
  }
  return 'english_candidate';
}

/// Read-only candidate inventory. Classification is deliberately heuristic:
/// identifiers, authored catalogues, prices, secrets and formats need manual
/// review before a completeness claim. This command never rewrites source.
void main(List<String> args) {
  if (args.isEmpty || args.first != 'inventory') {
    stderr.writeln(
      'Usage: localization_inventory.dart inventory <dart files...>',
    );
    exitCode = 64;
    return;
  }
  final inventory = <Map<String, Object?>>[];
  for (final path in args.skip(1)) {
    final source = File(path).readAsStringSync();
    final unit = parseString(content: source).unit;
    final visitor = _Strings();
    unit.accept(visitor);
    for (final node in visitor.all) {
      inventory.add({
        'file': path,
        'line': '\n'.allMatches(source.substring(0, node.offset)).length + 1,
        'classification': reason(node),
        'source': node.toSource(),
      });
    }
  }
  stdout.writeln(const JsonEncoder.withIndent('  ').convert(inventory));
}
