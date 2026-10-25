import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/font_licenses.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('bundled icon notice preserves exact pinned SDK terms and attribution', () async {
    final entries = await materialIconLicenses().toList();
    expect(entries, hasLength(1));
    expect(entries.single.packages, ['Google Material icons']);
    final text = entries.single.paragraphs.map((p) => p.text).join('\n');
    final supplied = File(
      '../../.tooling/flutter/bin/cache/artifacts/material_fonts/MaterialIcons_LICENSE.txt',
    ).readAsStringSync();
    for (final paragraph in supplied.split(RegExp(r'\n\s*\n'))) {
      final normalized = paragraph.trim().replaceAll(RegExp(r'\s+'), ' ');
      if (normalized.isNotEmpty) {
        expect(text.replaceAll(RegExp(r'\s+'), ' '), contains(normalized));
      }
    }
    expect(text, contains('Material icons by Google'));
    expect(text, contains('https://developers.google.com/fonts/docs/material_icons'));
  });

  test('startup registration is idempotent and reaches global license registry', () async {
    registerFontLicenses();
    registerFontLicenses();
    final found = await LicenseRegistry.licenses
        .where((entry) => entry.packages.contains('Google Material icons'))
        .toList();
    expect(found, hasLength(1));
  });
}
