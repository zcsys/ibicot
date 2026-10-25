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
