import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/study_gate.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass_platform/study_recorder.dart';

String fixtureProvision({String studyId = 'synthetic-study'}) => jsonEncode({
  'study_id': studyId,
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
    theme: tideglassTheme(),
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

Finder copy(String text) => find.byWidgetPredicate(
  (widget) =>
      widget is Text &&
      (widget.data == text || widget.data == Presentation.text(text)),
  description: 'English or pseudolocalized text: $text',
);

void main() {
  late Directory root;
  setUp(() {
    root = Directory.systemTemp.createTempSync('tideglass-study-gate-');
  });
  tearDown(() {
    root.deleteSync(recursive: true);
  });
  Map<String, dynamic> document() =>
      jsonDecode(File('${root.path}/tideglass-study.json').readAsStringSync());

  String diagnostics(WidgetTester tester) {
    final fixture = tester.state<_InteractiveFixtureState>(
      find.byType(InteractiveFixture),
    );
    final session = fixture.session;
    return 'active=${session?.active} failed=${session?.failed} '
        'failureCode=${session?.failureCode} erasing=${session?.erasing} '
        'pending=${session?.erasurePending} '
        'files=${root.listSync().map((e) => e.uri.pathSegments.last).toList()}';
  }

  Future<void> io(WidgetTester tester) async {
    for (var i = 0; i < 12; i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 40));
    }
    await tester.pumpAndSettle(const Duration(milliseconds: 50));
  }

  Future<void> until(
    WidgetTester tester,
    bool Function() completed,
    String reason,
  ) async {
    for (var i = 0; i < 200 && !completed(); i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 20));
    }
    expect(completed(), isTrue, reason: '$reason ${diagnostics(tester)}');
  }

  Future<void> waitFor(WidgetTester tester, Finder target) async {
    for (var i = 0; i < 100 && target.evaluate().isEmpty; i++) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 20));
    }
    expect(target, findsOneWidget);
  }

  Future<void> tap(WidgetTester tester, String text) async {
    final target = copy(text);
    // ListView children may not be built until scrolled into view. Scrolling
    // and pumping before hit testing models a real visible tap.
    await tester.scrollUntilVisible(
      target,
      200,
      scrollable: find.byType(Scrollable).last,
      maxScrolls: 35,
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(target);
    await tester.pumpAndSettle();
    expect(target.hitTestable(), findsOneWidget);
    // Start the real filesystem work in the real async zone. A delay started
    // later cannot move an already-created fake-zone I/O chain into that zone.
    await tester.runAsync(() => tester.tap(target.hitTestable()));
    await io(tester);
    final fixture = find.byType(InteractiveFixture);
    if (fixture.evaluate().length == 1) {
      final session = tester.state<_InteractiveFixtureState>(fixture).session;
      if (session?.erasing == true) {
        await until(
          tester,
          () => !session!.erasing,
          'The initiated local erasure must settle before checking durability.',
        );
      }
    }
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

  Future<void> enroll(WidgetTester tester, {bool expectHarbor = true}) async {
    await tap(
      tester,
      'I have read the study information and voluntarily agree to this study.',
    );
    await tap(tester, 'Agree and open the harbor');
    if (expectHarbor) {
      await waitFor(tester, copy('Fixture activity'));
      await until(
        tester,
        () => (document()['records'] as List).any(
          (record) => record['kind'] == 'harbor_interactive',
        ),
        'The actual post-frame interactive observation must be durable.',
      );
    }
  }

  testWidgets('default build never creates or reads study persistence', (
    tester,
  ) async {
    await open(tester, provision: '');
    expect(copy('Fixture activity'), findsOneWidget);
    expect(root.listSync().length, 0);
    expect(copy('Optional study'), findsNothing);
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
      await waitFor(tester, copy('Fixture activity'));
      expect(copy('Fixture activity'), findsOneWidget);
      var raw = document();
      expect((raw['records'] as List).first['kind'], 'app_start');
      expect(
        (raw['records'] as List).any((r) => r['kind'] == 'harbor_interactive'),
        isTrue,
        reason: diagnostics(tester),
      );
      await tap(tester, 'Fixture activity');
      await until(
        tester,
        () =>
            (document()['records'] as List).any((r) => r['kind'] == 'activity'),
        'The actual pointer interaction must be durably recorded.',
      );
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
      expect(copy('Fixture activity'), findsOneWidget);
      expect(copy('Optional Tideglass study'), findsNothing);
      expect(document()['status'], 'withdrawn', reason: diagnostics(tester));
    },
  );
  testWidgets(
    'existing harbor cannot become a retrospectively enrolled install',
    (tester) async {
      final save = File('${root.path}/tideglass/primary.json');
      save.parent.createSync();
      save.writeAsStringSync('sentinel');
      await open(tester);
      await enroll(tester, expectHarbor: false);
      expect(File('${root.path}/tideglass-study.json').existsSync(), isFalse);
      expect(save.readAsStringSync(), 'sentinel');
      await tap(tester, 'Continue without study recording');
      expect(copy('Fixture activity'), findsOneWidget);
    },
  );
  testWidgets('corrupt registry stays intact and cannot silently reenroll', (
    tester,
  ) async {
    final file = File('${root.path}/tideglass-study.json');
    file.writeAsStringSync('broken-synthetic-record');
    await open(tester);
    expect(copy('Agree and open the harbor'), findsNothing);
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
      expect(copy('Agree and open the harbor'), findsNothing);
      expect(find.byType(CheckboxListTile), findsNothing);
      await tap(tester, 'Continue without study recording');
      pending.complete(existing!);
      await io(tester);
      await tap(tester, 'Fixture activity');
      expect(file.readAsStringSync(), before);
      expect(copy('Optional study'), findsNothing);
    },
  );

  testWidgets('invalid provisioning cannot collect or block ordinary play', (
    tester,
  ) async {
    await open(tester, provision: '{"synthetic":true}');
    expect(copy('Agree and open the harbor'), findsNothing);
    await tap(tester, 'Continue without study recording');
    expect(copy('Fixture activity'), findsOneWidget);
    expect(root.listSync().length, 0);
  });

  Future<StudyRecorder> seeded(WidgetTester tester) async {
    final provision = StudyProvision.fromJson(jsonDecode(fixtureProvision()));
    final evidence = studyCanonical({'synthetic_fixture': true});
    File(
      '${root.path}/tideglass-study-eligibility.json',
    ).writeAsStringSync(evidence);
    return (await tester.runAsync(() async {
      final recorder = await StudyRecorder.open(
        AtomicStudyFileStore('${root.path}/tideglass-study.json'),
      );
      await recorder.enroll(
        provision.enrollment(studyDigest(evidence)),
        provision.currentConfig,
        eligibleFreshInstall: true,
      );
      return recorder;
    }))!;
  }

  Future<void> pendingErasure(
    WidgetTester tester,
    StudyRecorder recorder,
  ) async {
    File('${root.path}/tideglass-study.json.cas-guard').createSync();
    await tester.runAsync(() async {
      await expectLater(recorder.withdraw(), throwsA(isA<StudyException>()));
    });
    expect(recorder.withdrawalPending, isTrue);
    expect(
      File('${root.path}/tideglass-study.json.withdrawn').existsSync(),
      isTrue,
    );
  }

  testWidgets(
    'pending withdrawal checks original study identity before controls',
    (tester) async {
      final recorder = await seeded(tester);
      await pendingErasure(tester, recorder);
      final before = File(
        '${root.path}/tideglass-study.json',
      ).readAsStringSync();
      await open(
        tester,
        provision: fixtureProvision(studyId: 'different-study'),
      );
      expect(copy('Agree and open the harbor'), findsNothing);
      expect(find.byType(StudyControls), findsNothing);
      await tap(tester, 'Continue without study recording');
      expect(copy('Fixture activity'), findsOneWidget);
      expect(find.byType(StudyControls), findsNothing);
      expect(
        File('${root.path}/tideglass-study.json').readAsStringSync(),
        before,
      );
    },
  );

  testWidgets(
    'pending withdrawal disables export across reopen and retries erasure',
    (tester) async {
      final recorder = await seeded(tester);
      await pendingErasure(tester, recorder);
      await open(tester);
      await waitFor(tester, copy('Fixture activity'));
      final session = tester
          .state<_InteractiveFixtureState>(find.byType(InteractiveFixture))
          .session!;
      expect(session.active, isFalse);
      expect(session.erasurePending, isTrue);
      expect(session.canExport, isFalse);
      await expectLater(session.exportBundle(), throwsA(isA<StudyException>()));
      final copyButton = find.ancestor(
        of: copy('Copy study records'),
        matching: find.byType(OutlinedButton),
      );
      expect(tester.widget<OutlinedButton>(copyButton).onPressed, isNull);
      File('${root.path}/tideglass-study.json.cas-guard').deleteSync();
      await tap(tester, 'Retry local erasure');
      expect(document()['status'], 'withdrawn', reason: diagnostics(tester));
      expect(document()['records'], isEmpty);
      expect(session.erasurePending, isFalse);
      expect(session.canExport, isFalse);
      expect(
        File('${root.path}/tideglass-study-eligibility.json').existsSync(),
        isFalse,
      );
    },
  );

  testWidgets(
    'eligibility cleanup failure remains retryable after tombstone and reopen',
    (tester) async {
      await open(tester);
      await enroll(tester);
      await waitFor(tester, copy('Fixture activity'));
      final eligibility = File('${root.path}/tideglass-study-eligibility.json');
      eligibility.deleteSync();
      Directory(eligibility.path).createSync();
      await tap(tester, 'Withdraw and erase local study records');
      await tap(tester, 'Withdraw and erase');
      expect(document()['status'], 'withdrawn', reason: diagnostics(tester));
      expect(copy('Retry local erasure'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
      await io(tester);
      await open(tester);
      await waitFor(tester, copy('Fixture activity'));
      final session = tester
          .state<_InteractiveFixtureState>(find.byType(InteractiveFixture))
          .session!;
      expect(session.erasurePending, isTrue);
      expect(session.canExport, isFalse);
      Directory(eligibility.path).deleteSync();
      await tap(tester, 'Retry local erasure');
      expect(session.erasurePending, isFalse);
      expect(
        copy('Study recording has stopped. Local study records were erased.'),
        findsOneWidget,
      );
      expect(document()['records'], isEmpty);
    },
  );

  testWidgets(
    'stop marker without registry permits cleanup but never enrolls or exports',
    (tester) async {
      File('${root.path}/tideglass-study.json.withdrawn').writeAsStringSync('');
      File(
        '${root.path}/tideglass-study-eligibility.json',
      ).writeAsStringSync('synthetic leftover');
      await open(tester);
      await waitFor(tester, copy('Fixture activity'));
      expect(copy('Agree and open the harbor'), findsNothing);
      expect(find.byType(StudyControls), findsNothing);
      expect(document()['status'], 'withdrawn', reason: diagnostics(tester));
      expect(document()['registry'], isNull);
      expect(document()['records'], isEmpty);
      expect(
        File('${root.path}/tideglass-study-eligibility.json').existsSync(),
        isFalse,
      );
    },
  );

  testWidgets(
    'narrow expanded enrollment and withdrawal use visible controls',
    (tester) async {
      tester.view.physicalSize = const Size(320, 1000);
      tester.view.devicePixelRatio = 1;
      tester.platformDispatcher.textScaleFactorTestValue = 2;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await open(tester);
      await enroll(tester);
      await waitFor(tester, copy('Fixture activity'));
      await tap(tester, 'Withdraw and erase local study records');
      await tap(tester, 'Withdraw and erase');
      expect(document()['status'], 'withdrawn', reason: diagnostics(tester));
      expect(tester.takeException(), isNull);
    },
  );
}
