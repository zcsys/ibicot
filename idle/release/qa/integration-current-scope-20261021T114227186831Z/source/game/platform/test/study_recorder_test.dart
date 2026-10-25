import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_platform/study_recorder.dart';

class MemoryStore implements StudyStore {
  String? value;
  bool fail = false, loseResponse = false;
  int writes = 0;
  @override
  Future<String?> read() async => value;
  @override
  Future<bool> compareAndSwap(String? expectedSha256, String next) async {
    if (fail) throw const StudyException('fixture_write_failure');
    if ((value == null ? null : studyDigest(value!)) != expectedSha256)
      return false;
    value = next;
    writes++;
    if (loseResponse) throw const StudyException('fixture_response_loss');
    return true;
  }
}

void main() {
  late MemoryStore store;
  late int now, counter;
  late StudyRecorder recorder;
  final config = StudyConfig(
    candidateSha256: 'a' * 64,
    economySha256: 'b' * 64,
    contentSha256: 'c' * 64,
    config: 'fixture_v1',
  );
  final enrollment = StudyEnrollment(
    studyId: 'synthetic_cohort',
    protocolSha256: 'd' * 64,
    informationSha256: 'e' * 64,
    consentVersion: 'synthetic_v1',
    eligibilityEvidenceSha256: 'f' * 64,
    synthetic: true,
    platform: 'test',
    deviceGroup: 'unclassified',
    acquisition: 'internal_test',
  );
  Future<StudyRecorder> open({int limit = 4096}) => StudyRecorder.open(
    store,
    clock: () => DateTime.fromMillisecondsSinceEpoch(now * 1000, isUtc: true),
    idGenerator: () => (++counter).toRadixString(16).padLeft(32, '0'),
    maximumRecords: limit,
  );
  List<Map<String, dynamic>> records() =>
      (jsonDecode(store.value!)['records'] as List)
          .cast<Map<String, dynamic>>();
  Future<void> enroll() =>
      recorder.enroll(enrollment, config, eligibleFreshInstall: true);
  setUp(() async {
    store = MemoryStore();
    now = 100;
    counter = 0;
    recorder = await open();
  });
  test('off by default and retrospective enrollment refused', () async {
    await recorder.beginProcess(config: config);
    await recorder.interactiveHarbor();
    await recorder.activity(StudyActivity.interaction);
    expect(store.writes, 0);
    expect(recorder.exportRaw(), isNull);
    await expectLater(
      recorder.enroll(enrollment, config, eligibleFreshInstall: false),
      throwsA(isA<StudyException>()),
    );
    expect(store.value, isNull);
  });
  test(
    'atomic registry first startup and idempotent same process start',
    () async {
      await enroll();
      expect(store.writes, 1);
      expect(recorder.registry!['first_launch'], 100);
      expect(records().single['kind'], 'app_start');
      await recorder.beginProcess(config: config);
      expect(records().length, 1);
      await expectLater(enroll(), throwsA(isA<StudyException>()));
      expect((await open()).installId, recorder.installId);
    },
  );
  test('restart retains startup departure without invented terminal', () async {
    await enroll();
    final first = recorder.sessionId;
    now++;
    recorder = await open();
    await recorder.beginProcess(config: config);
    expect(recorder.sessionId, isNot(first));
    expect(records().map((e) => e['kind']), ['app_start', 'app_start']);
    expect(recorder.registry!['first_launch'], 100);
  });
  test(
    'short resume reuses session and exact inactivity boundary splits once',
    () async {
      await enroll();
      await recorder.interactiveHarbor();
      final first = recorder.sessionId;
      now = 101;
      await recorder.background();
      now = 1899;
      await recorder.foreground();
      expect(recorder.sessionId, first);
      now = 1900;
      await recorder.foreground();
      final second = recorder.sessionId;
      expect(second, isNot(first));
      await recorder.activity(StudyActivity.interaction);
      expect(records().where((e) => e['kind'] == 'activity'), isEmpty);
      await recorder.interactiveHarbor();
      await recorder.activity(StudyActivity.interaction);
      expect(recorder.sessionId, second);
      expect(records().where((e) => e['kind'] == 'session_start').length, 1);
      expect(records().where((e) => e['kind'] == 'terminal'), isEmpty);
    },
  );
  test('background pings cannot create activity', () async {
    await enroll();
    await recorder.activity(StudyActivity.interaction);
    expect(records().length, 1);
    await recorder.interactiveHarbor();
    await recorder.background();
    await recorder.activity(StudyActivity.interaction);
    expect(records().where((e) => e['kind'] == 'activity'), isEmpty);
  });
  test('missing config keeps startup record', () async {
    await enroll();
    now++;
    recorder = await open();
    await recorder.beginProcess(config: null);
    expect(records().last['payload']['config'], isNull);
    expect(records().last['kind'], 'app_start');
  });
  test('write failure preserves old data then records explicit gap', () async {
    await enroll();
    final before = store.value;
    store.fail = true;
    now++;
    await expectLater(
      recorder.interactiveHarbor(),
      throwsA(isA<StudyException>()),
    );
    expect(store.value, before);
    expect(recorder.hasPendingStorageGap, true);
    store.fail = false;
    now++;
    await recorder.interactiveHarbor();
    expect(records().where((e) => e['kind'] == 'gap').single['payload'], {
      'reason': 'storageFailure',
      'from': 100,
      'to': 102,
    });
    expect(recorder.hasPendingStorageGap, false);
  });
  test(
    'lost write response reopens durable state without completion',
    () async {
      await enroll();
      store.loseResponse = true;
      now++;
      await expectLater(
        recorder.interactiveHarbor(),
        throwsA(isA<StudyException>()),
      );
      store.loseResponse = false;
      recorder = await open();
      now++;
      await recorder.beginProcess(config: config);
      expect(records().where((e) => e['kind'] == 'app_start').length, 2);
      expect(records().where((e) => e['kind'] == 'terminal'), isEmpty);
    },
  );
  test('capacity retains registry and emits an open observation gap', () async {
    recorder = await open(limit: 8);
    await enroll();
    for (var i = 0; i < 20; i++) {
      now++;
      await recorder.foreground();
    }
    expect(recorder.exhausted, true);
    expect(records().length, 7);
    expect(records().last['payload']['reason'], 'capacity');
    expect(records().first['at'], 100);
    await recorder.withdraw();
    expect(recorder.withdrawn, true);
  });
  test('clock rollback stops and preserves original first launch', () async {
    await enroll();
    now = 99;
    await expectLater(
      recorder.interactiveHarbor(),
      throwsA(isA<StudyException>()),
    );
    expect(recorder.exhausted, true);
    expect(records().last['payload']['reason'], 'clockDiscontinuity');
    expect(recorder.registry!['first_launch'], 100);
  });
  test(
    'default withdrawal erases identifiers and prevents reenrollment',
    () async {
      await enroll();
      final id = recorder.installId;
      await recorder.withdraw();
      expect(recorder.installId, isNull);
      expect(store.value, isNot(contains(id!)));
      expect(jsonDecode(store.value!)['records'], isEmpty);
      recorder = await open();
      await recorder.beginProcess(config: config);
      expect(recorder.withdrawn, true);
      await expectLater(enroll(), throwsA(isA<StudyException>()));
    },
  );
  test('explicit minimal retention deletes behavioral history', () async {
    await enroll();
    await recorder.interactiveHarbor();
    await recorder.activity(StudyActivity.rechart);
    now++;
    await recorder.withdraw(retainMinimalRegistry: true);
    expect(records().map((e) => e['kind']), ['app_start', 'gap', 'withdrawal']);
    expect((await open()).withdrawn, true);
  });
  test(
    'full erasure after minimal withdrawal removes retained identifiers',
    () async {
      await enroll();
      await recorder.activity(StudyActivity.interaction);
      final original = recorder.installId!;
      await recorder.withdraw(retainMinimalRegistry: true);
      expect(store.value, contains(original));
      recorder = await open();
      await recorder.withdraw();
      expect(recorder.withdrawn, true);
      expect(recorder.installId, isNull);
      expect(store.value, isNot(contains(original)));
      expect(jsonDecode(store.value!)['records'], isEmpty);
      final writes = store.writes;
      await recorder.withdraw();
      await recorder.withdraw(retainMinimalRegistry: true);
      expect(store.writes, writes);
    },
  );
  test(
    'tamper duplicate keys and unknown fields fail without replacement',
    () async {
      await enroll();
      final original = store.value!;
      for (final damaged in [
        original.replaceFirst('app_start', 'harbor_interactive'),
        original.replaceFirst(
          '"schema_version":1',
          '"schema_version":1,"schema_version":1',
        ),
        original.replaceFirst(
          '"status":"active"',
          '"status":"active","email":"private"',
        ),
      ]) {
        store.value = damaged;
        await expectLater(open(), throwsA(isA<StudyException>()));
        expect(store.value, damaged);
      }
    },
  );
  test('stale writer cannot overwrite newer events', () async {
    await enroll();
    final stale = await open();
    now++;
    await recorder.interactiveHarbor();
    final before = store.value;
    await expectLater(
      stale.beginProcess(config: config),
      throwsA(isA<StudyException>()),
    );
    expect(store.value, before);
  });
  test(
    'failed erasure leaves durable stop intent and can be retried after reopen',
    () async {
      final dir = await Directory.systemTemp.createTemp(
        'study-withdraw-retry-',
      );
      addTearDown(() => dir.delete(recursive: true));
      final path = '${dir.path}/study.json';
      final disk = AtomicStudyFileStore(path);
      var collector = await StudyRecorder.open(disk);
      await collector.enroll(enrollment, config, eligibleFreshInstall: true);
      final before = await disk.read();
      final guard = File('$path.cas-guard');
      await guard.writeAsString('held by another writer');
      await expectLater(collector.withdraw(), throwsA(isA<StudyException>()));
      expect(collector.enrolled, false);
      expect(collector.withdrawalPending, true);
      expect(await File('$path.withdrawn').readAsString(), 'stop');
      expect(await disk.read(), before);
      expect(await guard.readAsString(), 'held by another writer');
      collector = await StudyRecorder.open(disk);
      expect(collector.enrolled, false);
      expect(collector.withdrawalPending, true);
      await collector.beginProcess(config: config);
      await collector.interactiveHarbor();
      await collector.activity(StudyActivity.interaction);
      expect(await disk.read(), before);
      await guard.delete(); // Qualified test removes its own known guard only.
      expect(await disk.compareAndSwap(studyDigest(before!), before), false);
      await collector.withdraw();
      expect(collector.withdrawn, true);
      expect(collector.withdrawalPending, false);
      expect((await StudyRecorder.open(disk)).withdrawn, true);
      expect(
        await disk.read(),
        studyCanonical({
          'schema_version': 1,
          'registry': null,
          'records': [],
          'status': 'withdrawn',
        }),
      );
    },
  );
  test(
    'partial withdrawal marker stops enrollment and survives reopen',
    () async {
      final dir = await Directory.systemTemp.createTemp('study-partial-stop-');
      addTearDown(() => dir.delete(recursive: true));
      final path = '${dir.path}/study.json';
      await File('$path.withdrawn').writeAsString('');
      final disk = AtomicStudyFileStore(path);
      final collector = await StudyRecorder.open(disk);
      expect(collector.withdrawalPending, true);
      await expectLater(
        collector.enroll(enrollment, config, eligibleFreshInstall: true),
        throwsA(isA<StudyException>()),
      );
      expect(await disk.read(), null);
      await collector.withdraw();
      expect((await StudyRecorder.open(disk)).withdrawn, true);
    },
  );
  test('CAS refusal or write failure releases only its own guard', () async {
    final dir = await Directory.systemTemp.createTemp('study-guard-cleanup-');
    addTearDown(() => dir.delete(recursive: true));
    final path = '${dir.path}/study.json';
    final disk = AtomicStudyFileStore(path);
    await File(path).writeAsString('original');
    expect(await disk.compareAndSwap('wrong', 'new'), false);
    expect(await File('$path.cas-guard').exists(), false);
    await Directory('$path.withdrawn').create();
    await expectLater(
      disk.compareAndSwap(studyDigest('original'), 'new'),
      throwsA(isA<StudyException>()),
    );
    expect(await File('$path.cas-guard').exists(), false);
    expect(await disk.read(), 'original');
    await Directory('$path.withdrawn').delete();
    expect(await disk.compareAndSwap(studyDigest('original'), 'new'), true);
    expect(await File('$path.cas-guard').exists(), false);
  });
  test(
    'unsafe guard or withdrawal marker never modifies linked files',
    () async {
      final dir = await Directory.systemTemp.createTemp('study-guard-links-');
      addTearDown(() => dir.delete(recursive: true));
      final path = '${dir.path}/study.json';
      final outside = File('${dir.path}/outside');
      await outside.writeAsString('preserve');
      final disk = AtomicStudyFileStore(path);
      final guard = Link('$path.cas-guard');
      await guard.create(outside.path);
      await expectLater(
        disk.compareAndSwap(null, 'new'),
        throwsA(isA<StudyException>()),
      );
      expect(await outside.readAsString(), 'preserve');
      expect(await guard.exists(), true);
      await guard.delete();
      await Link('$path.withdrawn').create(outside.path);
      await expectLater(
        disk.requestWithdrawal(),
        throwsA(isA<StudyException>()),
      );
      await expectLater(
        StudyRecorder.open(disk),
        throwsA(isA<StudyException>()),
      );
      expect(await outside.readAsString(), 'preserve');
      expect(await File(path).exists(), false);
    },
  );
  test(
    'withdrawal marker refuses active and malformed replacement records',
    () async {
      final dir = await Directory.systemTemp.createTemp('study-stop-cas-');
      addTearDown(() => dir.delete(recursive: true));
      final path = '${dir.path}/study.json';
      final disk = AtomicStudyFileStore(path);
      final collector = await StudyRecorder.open(disk);
      await collector.enroll(enrollment, config, eligibleFreshInstall: true);
      final before = (await disk.read())!;
      await disk.requestWithdrawal();
      for (final next in [
        before,
        '{"status":"withdrawn"}',
        '{"schema_version":1,"registry":null,"records":[],"status":"withdrawn","email":"hidden"}',
      ]) {
        expect(await disk.compareAndSwap(studyDigest(before), next), false);
        expect(await disk.read(), before);
      }
      await collector.withdraw(retainMinimalRegistry: true);
      final reopened = await StudyRecorder.open(disk);
      expect(reopened.withdrawn, true);
      expect(reopened.installId, collector.installId);
    },
  );
  test('atomic real file and symlink size corruption checks', () async {
    final dir = await Directory.systemTemp.createTemp('study-store-');
    addTearDown(() => dir.delete(recursive: true));
    final path = '${dir.path}/study.json';
    final disk = AtomicStudyFileStore(path);
    expect(await disk.read(), isNull);
    expect(await dir.list().length, 0);
    final collector = await StudyRecorder.open(disk);
    await collector.enroll(enrollment, config, eligibleFreshInstall: true);
    expect(
      (await StudyRecorder.open(disk)).registry!['first_launch'],
      isA<int>(),
    );
    final link = '${dir.path}/link';
    await Link(link).create(path);
    await expectLater(
      AtomicStudyFileStore(link).read(),
      throwsA(isA<StudyException>()),
    );
    await expectLater(
      AtomicStudyFileStore(path, maximumBytes: 10).read(),
      throwsA(isA<StudyException>()),
    );
    await File(path).writeAsString('{bad', flush: true);
    await expectLater(StudyRecorder.open(disk), throwsA(isA<StudyException>()));
    expect(await File(path).readAsString(), '{bad');
  });
}
