/// INTERNAL SYNTHETIC fixture. No device, participant, or native fatal observed.
import 'dart:convert';
import 'dart:io';

import '../lib/study_recorder.dart';

class Store implements StudyStore {
  String? value;
  @override
  Future<String?> read() async => value;
  @override
  Future<bool> compareAndSwap(String? previous, String next) async {
    if ((value == null ? null : studyDigest(value!)) != previous) return false;
    value = next;
    return true;
  }
}

Future<void> main(List<String> args) async {
  if (args.length != 1)
    throw ArgumentError('New synthetic output directory required');
  final output = Directory(args.single);
  if (output.existsSync()) throw StateError('Do not overwrite prior evidence');
  output.createSync(recursive: true);
  final store = Store();
  var now = 100;
  var id = 0;
  final config = StudyConfig(
    candidateSha256: 'a' * 64,
    economySha256: 'b' * 64,
    contentSha256: 'c' * 64,
    config: 'synthetic_native',
  );
  Future<StudyRecorder> open() => StudyRecorder.open(
    store,
    clock: () => DateTime.fromMillisecondsSinceEpoch(now * 1000, isUtc: true),
    idGenerator: () => (++id).toRadixString(16).padLeft(32, '0'),
  );
  void save(String label) =>
      File('${output.path}/$label.json').writeAsStringSync(store.value!);
  var recorder = await open();
  await recorder.enroll(
    StudyEnrollment(
      studyId: 'synthetic_native',
      protocolSha256: 'd' * 64,
      informationSha256: 'e' * 64,
      consentVersion: 'synthetic_v2',
      eligibilityEvidenceSha256: 'f' * 64,
      synthetic: true,
      platform: 'ios',
      deviceGroup: 'phone_large',
      acquisition: 'internal_test',
    ),
    config,
    eligibleFreshInstall: true,
  );
  save('legacy-before');
  final before = jsonDecode(store.value!);
  now++;
  recorder = await open();
  await recorder.beginProcess(
    config: config,
    nativeContext: StudyProcessObservation.available(
      nativePid: 123,
      platform: 'ios',
      applicationId: 'dev.tideglass.game',
      applicationVersion: '1.0.0',
      applicationBuild: '1',
      observedStartUtcMs: now * 1000,
    ),
  );
  save('migrated-available');
  final after = jsonDecode(store.value!);
  if (studyCanonical(before['registry']) != studyCanonical(after['registry']) ||
      studyCanonical(before['records'][0]) !=
          studyCanonical(after['records'][0]))
    throw StateError('Legacy bytes changed');
  now++;
  recorder = await open();
  await recorder.beginProcess(
    config: config,
    nativeContext: const StudyProcessObservation.unavailable(
      'consent_not_granted',
    ),
  );
  save('unavailable');
  await recorder.withdraw(retainMinimalRegistry: true);
  save('withdrawn');
  final pins = <String, String>{};
  for (final file in output.listSync().whereType<File>()) {
    pins[file.uri.pathSegments.last] = studyDigest(file.readAsStringSync());
  }
  File('${output.path}/manifest.json').writeAsStringSync(
    studyCanonical({
      'synthetic': true,
      'purpose': 'Pure Dart schema migration only; no native or participant observation',
      'sha256': pins,
    }),
  );
}
