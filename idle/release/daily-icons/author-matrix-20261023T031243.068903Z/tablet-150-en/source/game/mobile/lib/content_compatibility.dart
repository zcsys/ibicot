import 'bundled_hashes.g.dart';

/// The only approved content migration removes chapter 3's calibration gate.
/// The economy, IDs, earned rewards, challenge fleets and seasonal rules are
/// unchanged. Unknown manifests still fail before selecting a saved branch.
const optionalCalibrationPreviousDigest =
    '708f083217d4810e8e0a23e4d6519b374ab3c986da08eb001c0dd0a762e5c19c';
bool acceptsStoryContentDigest(Object? digest) =>
    digest == null ||
    digest == bundledManifestDigest ||
    digest == optionalCalibrationPreviousDigest;

String? migratedStoryContentDigest(String? digest) =>
    digest == optionalCalibrationPreviousDigest
    ? bundledManifestDigest
    : digest;
