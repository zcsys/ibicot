import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/study_gate.dart';
import 'package:tideglass_platform/study_recorder.dart';

String fixtureProvision() => jsonEncode({
  'study_id': 'synthetic-study',
  'protocol_sha256': 'b' * 64,
  'candidate_sha256': 'a' * 64,
  'config': 'synthetic-config',
  'consent_version': 'fixture-1',
  'information': 'Synthetic fixture only. No participants or actual consent.',
  'contact': 'https://example.invalid/study',
  'retention': 'Synthetic temporary test files only.',
  'synthetic': true,
  'device_group': 'unclassified',
  'acquisition': 'internal_test',
});

class InteractiveFixture extends StatefulWidget {
  const InteractiveFixture({super.key});
  @override
  State<InteractiveFixture> createState() => _InteractiveFixtureState();
}

class _InteractiveFixtureState extends State<InteractiveFixture> {
  StudySession? session;
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final next = StudyScope.of(context);
    if (identical(next, session)) return;
    session = next;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && session != null) {
        unawaited(session!.capture(session!.recorder.interactiveHarbor));
      }
    });
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    home: Scaffold(
      body: ListView(
        children: [
          TextButton(onPressed: () {}, child: const Text('Fixture activity')),
          if (session != null) StudyControls(session: session!),
        ],
      ),
    ),
  );
}

void main() {
  late Directory root;
  setUp(() {
    root = Directory.systemTemp.createTempSync('tideglass-study-gate-');
  });
  tearDown(() {
    root.deleteSync(recursive: true);
  });
  Future<void> io(WidgetTester tester) async {
    for (var i = 0; i < 12; i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 40));
    }
    await tester.pumpAndSettle(const Duration(milliseconds: 50));
  }

  Future<void> tap(WidgetTester tester, String text) async {
    await tester.ensureVisible(find.text(text));
    await tester.tap(find.text(text));
    await io(tester);
  }

  Future<void> open(WidgetTester tester, {String? provision}) async {
    await tester.pumpWidget(
      StudyGate(
        provision: provision ?? fixtureProvision(),
        supportDirectory: root,
        child: const InteractiveFixture(),
      ),
    );
    await io(tester);
  }

  Future<void> enroll(WidgetTester tester) async {
    await tap(
      tester,
      'I have read the study information and voluntarily agree to this study.',
    );
    await tap(tester, 'Agree and open the harbor');
  }

  Map<String, dynamic> document() =>
      jsonDecode(File('${root.path}/tideglass-study.json').readAsStringSync());

  testWidgets('default build never creates or reads study persistence', (
    tester,
  ) async {
    await open(tester, provision: '');
    expect(find.text('Fixture activity'), findsOneWidget);
    expect(root.listSync().length, 0);
    expect(find.text('Optional study'), findsNothing);
  });
  testWidgets('declining leaves no registry, eligibility record or backfill', (
    tester,
  ) async {
    await open(tester);
    expect(root.listSync().length, 0);
    await tap(tester, 'Continue without study recording');
    await tap(tester, 'Fixture activity');
    expect(root.listSync().length, 0);
  });
  testWidgets(
    'consent persists start before harbor; interaction and withdrawal persist',
    (tester) async {
      await open(tester);
      await enroll(tester);
      expect(find.text('Fixture activity'), findsOneWidget);
      var raw = document();
      expect((raw['records'] as List).first['kind'], 'app_start');
      expect(
        (raw['records'] as List).any((r) => r['kind'] == 'harbor_interactive'),
        isTrue,
      );
      await tap(tester, 'Fixture activity');
      raw = document();
      expect(
        (raw['records'] as List).any((r) => r['kind'] == 'activity'),
        isTrue,
      );
      await tap(tester, 'Withdraw and erase local study records');
      await tap(tester, 'Withdraw and erase');
      raw = document();
      expect(raw['status'], 'withdrawn');
      expect(raw['registry'], isNull);
      expect(raw['records'], isEmpty);
      expect(
        File('${root.path}/tideglass-study-eligibility.json').existsSync(),
        isFalse,
      );
      await tester.pumpWidget(const SizedBox());
      await io(tester);
      await open(tester);
      expect(find.text('Fixture activity'), findsOneWidget);
      expect(find.text('Optional Tideglass study'), findsNothing);
      expect(document()['status'], 'withdrawn');
    },
  );
  testWidgets(
    'existing harbor cannot become a retrospectively enrolled install',
    (tester) async {
      final save = File('${root.path}/tideglass/primary.json');
      save.parent.createSync();
      save.writeAsStringSync('sentinel');
      await open(tester);
      await enroll(tester);
      expect(File('${root.path}/tideglass-study.json').existsSync(), isFalse);
      expect(save.readAsStringSync(), 'sentinel');
      await tap(tester, 'Continue without study recording');
      expect(find.text('Fixture activity'), findsOneWidget);
    },
  );
  testWidgets('corrupt registry stays intact and cannot silently reenroll', (
    tester,
  ) async {
    final file = File('${root.path}/tideglass-study.json');
    file.writeAsStringSync('broken-synthetic-record');
    await open(tester);
    expect(find.text('Agree and open the harbor'), findsNothing);
    await tap(tester, 'Continue without study recording');
    expect(file.readAsStringSync(), 'broken-synthetic-record');
  });
  testWidgets(
    'declining during a pending registry read cannot enable recording later',
    (tester) async {
      await open(tester);
      await enroll(tester);
      await tester.pumpWidget(const SizedBox());
      await io(tester);
      final file = File('${root.path}/tideglass-study.json');
      final before = file.readAsStringSync();
      final existing = await tester.runAsync(
        () => StudyRecorder.open(AtomicStudyFileStore(file.path)),
      );
      final pending = Completer<StudyRecorder>();
      await tester.pumpWidget(
        StudyGate(
          provision: fixtureProvision(),
          supportDirectory: root,
          openRecorder: (_) => pending.future,
          child: const InteractiveFixture(),
        ),
      );
      await tap(tester, 'Continue without study recording');
      pending.complete(existing!);
      await io(tester);
      await tap(tester, 'Fixture activity');
      expect(file.readAsStringSync(), before);
      expect(find.text('Optional study'), findsNothing);
    },
  );

  testWidgets('invalid provisioning cannot collect or block ordinary play', (
    tester,
  ) async {
    await open(tester, provision: '{"synthetic":true}');
    expect(find.text('Agree and open the harbor'), findsNothing);
    await tap(tester, 'Continue without study recording');
    expect(find.text('Fixture activity'), findsOneWidget);
    expect(root.listSync().length, 0);
  });
}
