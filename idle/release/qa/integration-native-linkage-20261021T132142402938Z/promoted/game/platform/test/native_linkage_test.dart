import 'dart:convert';

import 'package:test/test.dart';

import '../lib/study_recorder.dart';

class Memory implements StudyStore {
  String? value;
  int writes = 0;
  bool fail = false;
  @override
  Future<String?> read() async => value;
  @override
  Future<bool> compareAndSwap(String? expectedSha256, String next) async {
    if (fail) throw const StudyException('synthetic_failure');
    if ((value == null ? null : studyDigest(value!)) != expectedSha256)
      return false;
    value = next;
    writes++;
    return true;
  }
}

void main() {
  late Memory store;
  var now = 100, ids = 0;
  final config = StudyConfig(
    candidateSha256: 'a' * 64,
    economySha256: 'b' * 64,
    contentSha256: 'c' * 64,
    config: 'synthetic_native',
  );
  final enrollment = StudyEnrollment(
    studyId: 'synthetic_native',
    protocolSha256: 'd' * 64,
    informationSha256: 'e' * 64,
    consentVersion: 'synthetic_v2',
    eligibilityEvidenceSha256: 'f' * 64,
    synthetic: true,
    platform: 'ios',
    deviceGroup: 'phone_large',
    acquisition: 'internal_test',
  );
  Future<StudyRecorder> open({int bound = 4096}) => StudyRecorder.open(
    store,
    clock: () => DateTime.fromMillisecondsSinceEpoch(now * 1000, isUtc: true),
    idGenerator: () => (++ids).toRadixString(16).padLeft(32, '0'),
    maximumRecords: bound,
  );
  StudyProcessObservation observation() => StudyProcessObservation.available(
    nativePid: 123,
    platform: 'ios',
    applicationId: 'dev.tideglass.game',
    applicationVersion: '1.0.0',
    applicationBuild: '1',
    observedStartUtcMs: now * 1000,
  );
  Map<String, dynamic> document() => jsonDecode(store.value!);
  setUp(() {
    store = Memory();
    now = 100;
    ids = 0;
  });

  test('no enrollment means no linkage writes or process', () async {
    final recorder = await open();
    await recorder.beginProcess(config: config, nativeContext: observation());
    expect(store.writes, 0);
    expect(recorder.processId, isNull);
  });
  test('available context and original startup commit atomically', () async {
    final recorder = await open();
    await recorder.enroll(
      enrollment,
      config,
      eligibleFreshInstall: true,
      nativeContext: observation(),
    );
    expect(store.writes, 1);
    expect(document()['schema_version'], 2);
    expect(document()['records'].length, 1);
    expect(
      document()['records'][0]['payload']['native_context']['native_pid'],
      123,
    );
    expect((await open()).processId, recorder.processId);
  });
  test(
    'unavailable context and gap are one commit with no invented crash',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: const StudyProcessObservation.unavailable(
          'native_unavailable',
        ),
      );
      expect(store.writes, 1);
      expect(document()['records'].length, 2);
      expect(document()['records'][1]['payload'], {
        'reason': 'instrumentationUnavailable',
        'from': 100,
        'to': 100,
      });
      await open();
    },
  );
  test('legacy migration retains every registry/event byte and hash', () async {
    final old = await open();
    await old.enroll(enrollment, config, eligibleFreshInstall: true);
    final before = document();
    expect(before['schema_version'], 1);
    now++;
    final resumed = await open();
    await resumed.beginProcess(config: config, nativeContext: observation());
    final after = document();
    expect(after['schema_version'], 2);
    expect(
      studyCanonical(after['registry']),
      studyCanonical(before['registry']),
    );
    expect(
      studyCanonical(after['records'][0]),
      studyCanonical(before['records'][0]),
    );
    expect(
      after['records'][1]['previous_sha256'],
      before['records'][0]['sha256'],
    );
    await open();
  });
  test('schema2 restart cannot silently omit native availability', () async {
    final recorder = await open();
    await recorder.enroll(
      enrollment,
      config,
      eligibleFreshInstall: true,
      nativeContext: observation(),
    );
    now++;
    final resumed = await open();
    await resumed.beginProcess(config: config);
    expect(
      document()['records'][1]['payload']['native_context']['status'],
      'unavailable',
    );
    expect(document()['records'].length, 3);
    await open();
  });
  test(
    'inactivity shares process and does not duplicate process observation',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      await recorder.interactiveHarbor();
      final process = recorder.processId;
      now += 1800;
      await recorder.activity(StudyActivity.interaction);
      expect(recorder.processId, process);
      final records = document()['records'] as List;
      expect(records.where((e) => e['kind'] == 'session_start').length, 1);
      expect(
        records
            .where((e) => (e['payload'] as Map).containsKey('native_context'))
            .length,
        1,
      );
      await open();
    },
  );
  test('withdrawal erases native identity even with legacy minimal retention option', () async {
    final recorder = await open();
    await recorder.enroll(
      enrollment,
      config,
      eligibleFreshInstall: true,
      nativeContext: observation(),
    );
    await recorder.withdraw(retainMinimalRegistry: true);
    expect(document()['registry'], isNull);
    expect(document()['records'], isEmpty);
    expect(store.value, isNot(contains('native_pid')));
    await open();
  });
  test('failed atomic start cannot publish new durable identity', () async {
    final recorder = await open();
    store.fail = true;
    await expectLater(
      recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      ),
      throwsA(isA<StudyException>()),
    );
    expect(store.value, isNull);
    expect(recorder.enrolled, isFalse);
  });
  test(
    'enroll then beginProcess is a no-op without an unavailable gap',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      final exact = store.value;
      await recorder.beginProcess(config: config);
      expect(store.value, exact);
      expect(store.writes, 1);
    },
  );
  test(
    'restart platform mismatch cannot write or create a new identity',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      final exact = store.value;
      now++;
      final resumed = await open();
      final wrong = StudyProcessObservation.fromJson({
        ...observation().toJson(),
        'platform': 'android',
      });
      await expectLater(
        resumed.beginProcess(config: config, nativeContext: wrong),
        throwsA(isA<StudyException>()),
      );
      expect(store.value, exact);
      expect(resumed.processId, recorder.processId);
    },
  );
  test(
    'capacity at process start keeps the last committed process and decodes',
    () async {
      final recorder = await open(bound: 8);
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      await recorder.interactiveHarbor();
      for (var i = 0; i < 4; i++) {
        now++;
        await recorder.activity(StudyActivity.interaction);
      }
      expect(document()['records'].length, 6);
      final process = recorder.processId;
      now++;
      final resumed = await open(bound: 8);
      await resumed.beginProcess(config: config, nativeContext: observation());
      expect(resumed.exhausted, isTrue);
      expect(resumed.processId, process);
      expect(document()['records'].last['payload']['reason'], 'capacity');
      expect((await open(bound: 8)).exhausted, isTrue);
    },
  );
  test(
    'backward clock during restart retains the old committed process',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      now--;
      final resumed = await open();
      await expectLater(
        resumed.beginProcess(config: config, nativeContext: observation()),
        throwsA(isA<StudyException>()),
      );
      expect(resumed.processId, recorder.processId);
      expect((await open()).exhausted, isTrue);
    },
  );
  test(
    'failed restart retry writes the storage gap under the committed process',
    () async {
      final recorder = await open();
      await recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: observation(),
      );
      final committed = store.value;
      now++;
      final resumed = await open();
      store.fail = true;
      await expectLater(
        resumed.beginProcess(config: config, nativeContext: observation()),
        throwsA(isA<StudyException>()),
      );
      expect(store.value, committed);
      store.fail = false;
      now++;
      await resumed.beginProcess(config: config, nativeContext: observation());
      expect(document()['records'][1]['kind'], 'gap');
      expect(document()['records'][1]['process_id'], recorder.processId);
      expect(document()['records'][2]['kind'], 'app_start');
      await open();
    },
  );
  test('native bounds and hidden fields are rejected', () {
    final raw = observation().toJson();
    expect(
      () => StudyProcessObservation.fromJson({
        ...raw,
        'observed_elapsed_us': 5000000,
      }),
      throwsA(isA<FormatException>()),
    );
    expect(
      () => StudyProcessObservation.fromJson({...raw, 'version': 1.0}),
      throwsA(isA<FormatException>()),
    );
    expect(
      () => StudyProcessObservation.fromJson({
        ...raw,
        'private_email': 'synthetic',
      }),
      throwsA(isA<FormatException>()),
    );
    expect(
      () => StudyProcessObservation.fromJson({...raw, 'native_pid': 0}),
      throwsA(isA<FormatException>()),
    );
    expect(
      () =>
          const StudyProcessObservation.unavailable('unbounded-private-error')
              .toJson(),
      throwsA(isA<FormatException>()),
    );
  });
  test('stale timestamp cannot be attached to a later logical start', () async {
    final recorder = await open();
    final stale = observation();
    now += 10;
    await expectLater(
      recorder.enroll(
        enrollment,
        config,
        eligibleFreshInstall: true,
        nativeContext: stale,
      ),
      throwsA(isA<StudyException>()),
    );
    expect(store.value, isNull);
  });
}
