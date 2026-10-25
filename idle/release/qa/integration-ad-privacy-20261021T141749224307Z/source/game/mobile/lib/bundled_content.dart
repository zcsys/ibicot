import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'bundled_hashes.g.dart';
export 'bundled_hashes.g.dart';

/// The bundled, compiled allow-list is the safe local configuration. Remote
/// data is not applied by this loader. A digest mismatch fails before a save is
/// opened or a new rule can reinterpret progress.
Future<void> verifyBundledContent({AssetBundle? bundle}) async {
  final source = bundle ?? rootBundle;
  Future<List<int>> bytes(String path) async {
    final data = await source.load(path);
    return data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
  }

  final raw = await bytes('assets/config/manifest.json');
  if (sha256.convert(raw).toString() != bundledManifestDigest) {
    throw const FormatException(
      'Bundled content manifest does not match this application.',
    );
  }
  final manifest = Map<String, dynamic>.from(jsonDecode(utf8.decode(raw)));
  if (manifest['schema_version'] != 1 ||
      manifest['economy_version'] != economyVersion ||
      manifest['content_version'] != 'tideglass-native-content-1' ||
      manifest['files'] is! Map) {
    throw const FormatException('Unsupported bundled content configuration.');
  }
  final files = Map<String, dynamic>.from(manifest['files']);
  if (files.length != 29 ||
      files['assets/config/economy.json']?['sha256'] != bundledEconomicDigest) {
    throw const FormatException(
      'The full gameplay catalogue and pinned economy are required.',
    );
  }
  for (final entry in files.entries) {
    if (!entry.key.startsWith('assets/') || entry.key.contains('..')) {
      throw const FormatException('Invalid bundled content path.');
    }
    final descriptor = Map<String, dynamic>.from(entry.value);
    final content = await bytes(entry.key);
    if (content.length != descriptor['bytes'] ||
        sha256.convert(content).toString() != descriptor['sha256']) {
      throw FormatException('Bundled gameplay file differs: ${entry.key}');
    }
  }
  // The versioned core deliberately implements one fixed economy. Arbitrary
  // remote numeric values cannot silently override its tested settlement math.
  final economy = Map<String, dynamic>.from(
    jsonDecode(utf8.decode(await bytes('assets/config/economy.json'))),
  );
  if (economy['base_cost'] != 30 ||
      economy['base_output'] != 1 ||
      economy['tier_ratio'] != 20 ||
      economy['purchase_growth'] != 1.12 ||
      economy['prestige_exponent'] != .65 ||
      jsonEncode(economy['producer_names']) !=
          jsonEncode(TideglassEngine.producerNames)) {
    throw const FormatException(
      'Bundled economy does not match the compiled numeric rules.',
    );
  }
}
