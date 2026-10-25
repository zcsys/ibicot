/// Synthetic cross-language fixture, generated through the real recorder.
import 'dart:convert';
import 'dart:io';
import 'package:tideglass_platform/study_recorder.dart';

class FixtureStore implements StudyStore {
  String? raw;
  @override
  Future<String?> read() async => raw;
  @override
  Future<bool> compareAndSwap(String? previous, String next) async {
    if ((raw == null ? null : studyDigest(raw!)) != previous) return false;
    raw = next;
    return true;
  }
}

Future<void> main(List<String> args) async {
  if (args.length != 1)
    throw const FormatException('Provide a new output directory.');
  final output = Directory(args.single);
  if (await output.exists()) throw const FormatException('Output must be new.');
  await output.create(recursive: true);
  final evidence = await Directory('${output.path}/evidence').create();
  final protocolText = await File(
    '../../release/study/fixtures/synthetic-protocol.json',
  ).readAsString();
  final protocol = jsonDecode(protocolText) as Map<String, dynamic>;
  final baseline = protocol['baseline'];
  final config = StudyConfig(
    candidateSha256: baseline['candidate_sha256'],
    economySha256: baseline['economy_sha256'],
    contentSha256: baseline['content_sha256'],
    config: baseline['config'],
  );
  final entries = <Object?>[];
  final exports = <Object?>[];
  final labels = <String, Object?>{};
  var counter = 0;
  var now = 100;
  for (final label in [
    'startup_departure',
    'interactive_return',
    'missing_stream',
  ]) {
    final store = FixtureStore();
    Future<StudyRecorder> open() => StudyRecorder.open(
      store,
      clock: () => DateTime.fromMillisecondsSinceEpoch(now * 1000, isUtc: true),
      idGenerator: () => (++counter).toRadixString(16).padLeft(32, '0'),
    );
    var recorder = await open();
    final proof = {
      'schema_version': 1,
      'check': 'no_prior_game_directory_entries',
      'checked_at': DateTime.fromMillisecondsSinceEpoch(
        now * 1000,
        isUtc: true,
      ).toIso8601String(),
      'study_id': protocol['study_id'],
      'candidate_sha256': config.candidateSha256,
    };
    final proofText = studyCanonical(proof);
    final proofHash = studyDigest(proofText);
    await File('${evidence.path}/$proofHash.evidence').writeAsString(proofText);
    await recorder.enroll(
      StudyEnrollment(
        studyId: protocol['study_id'],
        protocolSha256: studyDigest(protocolText),
        informationSha256: studyDigest(
          'SYNTHETIC fixture information. No participants.',
        ),
        consentVersion: 'synthetic_v1',
        eligibilityEvidenceSha256: proofHash,
        synthetic: true,
        platform: 'test',
        deviceGroup: 'unclassified',
        acquisition: 'internal_test',
      ),
      config,
      eligibleFreshInstall: true,
    );
    entries.add(recorder.registry);
    labels[label] = {
      'install_id': recorder.installId,
      'initial_session_id': recorder.sessionId,
      'initial_process_id': recorder.processId,
    };
    if (label == 'interactive_return') {
      now++;
      await recorder.interactiveHarbor();
      await recorder.activity(StudyActivity.interaction);
      now++;
      await recorder.terminal(StudyTerminal.explicitlyObservedCleanExit);
      now = 30 * 86400 + 102;
      recorder = await open();
      await recorder.beginProcess(config: config);
      await recorder.interactiveHarbor();
      await recorder.activity(StudyActivity.interaction);
    }
    if (label != 'missing_stream')
      exports.add({
        'schema_version': 1,
        'raw': jsonDecode(recorder.exportRaw()!),
        'eligibility_evidence': proof,
      });
    now = label == 'startup_departure' ? 101 : 103;
  }
  for (final entry in {
    'protocol.json': jsonDecode(protocolText),
    'registry.json': {
      'schema_version': 1,
      'study_id': protocol['study_id'],
      'synthetic': true,
      'entries': entries,
    },
    'raw.json': {
      'schema_version': 1,
      'study_id': protocol['study_id'],
      'synthetic': true,
      'exports': exports,
    },
    'labels.json': labels,
  }.entries) {
    await File(
      '${output.path}/${entry.key}',
    ).writeAsString(studyCanonical(entry.value));
  }
  // The registry pins the original protocol bytes, so preserve those verbatim.
  await File('${output.path}/protocol.json').writeAsString(protocolText);
  stdout.writeln('Synthetic fixture exported; zero participants observed.');
}
