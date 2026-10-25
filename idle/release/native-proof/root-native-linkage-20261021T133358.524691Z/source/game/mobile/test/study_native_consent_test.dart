// INTERNAL SYNTHETIC widget tests. Native channel/build qualification is separate.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/study_gate.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass_platform/study_recorder.dart';

String provision() => jsonEncode({
  'study_id': 'synthetic-native',
  'protocol_sha256': 'b' * 64,
  'candidate_sha256': 'a' * 64,
  'config': 'synthetic-native',
  'consent_version': 'synthetic-1',
  'information': 'Synthetic test; no participants.',
  'contact': 'https://example.invalid/study',
  'retention': 'Temporary synthetic files.',
  'synthetic': true,
  'device_group': 'unclassified',
  'acquisition': 'internal_test',
});
Finder copy(String text) => find.byWidgetPredicate(
  (widget) =>
      widget is Text &&
      (widget.data == text || widget.data == Presentation.text(text)),
);

void main() {
  late Directory directory;
  setUp(() {
    directory = Directory.systemTemp.createTempSync(
      'tideglass-native-consent-',
    );
  });
  tearDown(() {
    directory.deleteSync(recursive: true);
  });
  Map<String, dynamic> raw() => jsonDecode(
    File('${directory.path}/tideglass-study.json').readAsStringSync(),
  );
  Future<void> until(WidgetTester tester, bool Function() done) async {
    for (var i = 0; i < 200 && !done(); i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 20));
    }
    expect(done(), isTrue);
  }

  Future<void> tap(WidgetTester tester, String text) async {
    final target = copy(text);
    await tester.scrollUntilVisible(
      target,
      200,
      scrollable: find.byType(Scrollable).last,
      maxScrolls: 40,
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(target);
    expect(target.hitTestable(), findsOneWidget);
    await tester.runAsync(() => tester.tap(target.hitTestable()));
    await tester.pump();
  }

  Future<void> open(
    WidgetTester tester, {
    String? supplied,
    Future<StudyProcessObservation> Function()? sample,
  }) async {
    await tester.pumpWidget(
      StudyGate(
        provision: supplied ?? provision(),
        supportDirectory: directory,
        sampleNativeContext: sample,
        child: const MaterialApp(home: Scaffold(body: Text('Harbor fixture'))),
      ),
    );
  }

  testWidgets('default empty provision performs no native or study I/O', (
    tester,
  ) async {
    var sampled = 0, opened = 0;
    await tester.pumpWidget(
      StudyGate(
        provision: '',
        supportDirectory: directory,
        sampleNativeContext: () async {
          sampled++;
          throw StateError('must not sample');
        },
        openRecorder: (store) async {
          opened++;
          throw StateError('must not open');
        },
        child: const MaterialApp(home: Text('Harbor fixture')),
      ),
    );
    await tester.pump();
    expect(copy('Harbor fixture'), findsOneWidget);
    expect(sampled, 0);
    expect(opened, 0);
    expect(directory.listSync(), isEmpty);
  });
  testWidgets(
    'native disclosure is visible before consent and sampling waits for Agree',
    (tester) async {
      var sampled = 0;
      await open(
        tester,
        sample: () async {
          sampled++;
          return const StudyProcessObservation.unavailable(
            'unsupported_platform',
          );
        },
      );
      await until(
        tester,
        () => find.byType(CheckboxListTile).evaluate().isNotEmpty,
      );
      await tester.scrollUntilVisible(
        copy(StudyProvision.nativeLinkageInformation),
        150,
        scrollable: find.byType(Scrollable).last,
        maxScrolls: 40,
      );
      await tester.pumpAndSettle();
      expect(copy(StudyProvision.nativeLinkageInformation), findsOneWidget);
      expect(sampled, 0);
      expect(directory.listSync(), isEmpty);
      await tap(
        tester,
        'I have read the study information and voluntarily agree to this study.',
      );
      expect(sampled, 0);
      await tap(tester, 'Agree and open the harbor');
      await until(tester, () => copy('Harbor fixture').evaluate().isNotEmpty);
      expect(sampled, 1);
      expect(raw()['schema_version'], 2);
      expect(
        raw()['registry']['information_sha256'],
        studyDigest(
          StudyProvision.fromJson(jsonDecode(provision())).information,
        ),
      );
      // enroll + beginProcess emits exactly one process start, then unavailable gap.
      expect(
        (raw()['records'] as List)
            .where((row) => row['kind'] == 'app_start')
            .length,
        1,
      );
      expect((raw()['records'] as List).length, 2);
    },
  );
  testWidgets('decline never samples the native context', (tester) async {
    var sampled = 0;
    await open(
      tester,
      sample: () async {
        sampled++;
        throw StateError('must not sample');
      },
    );
    await until(
      tester,
      () => find.byType(CheckboxListTile).evaluate().isNotEmpty,
    );
    await tap(tester, 'Continue without study recording');
    await until(tester, () => copy('Harbor fixture').evaluate().isNotEmpty);
    expect(sampled, 0);
    expect(directory.listSync(), isEmpty);
  });
  testWidgets(
    'legacy consent preserves registry and old events without PID sampling',
    (tester) async {
      final configured = StudyProvision.fromJson(jsonDecode(provision()));
      final source = configured.enrollment('f' * 64);
      final legacy = StudyEnrollment(
        studyId: source.studyId,
        protocolSha256: source.protocolSha256,
        informationSha256: studyDigest(configured.legacyInformation),
        consentVersion: source.consentVersion,
        eligibilityEvidenceSha256: source.eligibilityEvidenceSha256,
        synthetic: true,
        platform: source.platform,
        deviceGroup: source.deviceGroup,
        acquisition: source.acquisition,
      );
      await tester.runAsync(() async {
        final recorder = await StudyRecorder.open(
          AtomicStudyFileStore('${directory.path}/tideglass-study.json'),
        );
        await recorder.enroll(
          legacy,
          configured.currentConfig,
          eligibleFreshInstall: true,
        );
      });
      final before = raw();
      var sampled = 0;
      await open(
        tester,
        sample: () async {
          sampled++;
          throw StateError('old consent must not sample');
        },
      );
      await until(tester, () => copy('Harbor fixture').evaluate().isNotEmpty);
      final after = raw();
      expect(sampled, 0);
      expect(after['registry'], before['registry']);
      expect(after['records'][0], before['records'][0]);
      expect(after['schema_version'], 2);
      expect(after['records'][1]['payload']['native_context'], {
        'version': 1,
        'status': 'unavailable',
        'reason': 'consent_not_granted',
      });
    },
  );
}
