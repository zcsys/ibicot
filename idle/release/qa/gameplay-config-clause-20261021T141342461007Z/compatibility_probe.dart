import 'dart:convert';
import 'source/game/mobile/lib/content_compatibility.dart';
import 'source/game/mobile/lib/bundled_hashes.g.dart';

void main() {
  var assertions = 0;
  void check(bool value) {
    assertions++;
    if (!value) throw StateError('Compatibility assertion $assertions failed');
  }
  for (final value in [null, bundledManifestDigest, optionalCalibrationPreviousDigest]) {
    check(acceptsStoryContentDigest(value));
    final migrated = migratedStoryContentDigest(value);
    check(migrated == (value == optionalCalibrationPreviousDigest ? bundledManifestDigest : value));
    check(migratedStoryContentDigest(migrated) == migrated);
  }
  for (final value in <Object>[
    '', '0' * 64, 'f' * 64, 1, true, {}, [],
    '$bundledManifestDigest ', ' $optionalCalibrationPreviousDigest',
    bundledManifestDigest.toUpperCase(), optionalCalibrationPreviousDigest.toUpperCase(),
    '${optionalCalibrationPreviousDigest}x',
  ]) {
    check(!acceptsStoryContentDigest(value));
  }
  print(jsonEncode({'independent_assertions': assertions, 'passed': true,
    'scope': 'pure content compatibility only; economic transition covered by different-author QA'}));
}
