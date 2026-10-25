import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'package:test/test.dart';
import 'package:tideglass_platform/study_recorder.dart';

class DelayedReads {
  final release = Completer<void>();
  final both = Completer<void>();
  var count = 0;
}

class BarrierFileStore extends AtomicStudyFileStore {
  BarrierFileStore(super.path, this.reads);
  final DelayedReads reads;
  @override
  Future<String?> read() async {
    final actual = await super.read();
    if (++reads.count == 2) reads.both.complete();
    await reads.release.future;
    return actual;
  }
}

class MemoryStore implements StudyStore {
  String? value;
  @override Future<String?> read() async => value;
  @override Future<bool> compareAndSwap(String? old, String next) async {
    if ((value == null ? null : studyDigest(value!)) != old) return false;
    value = next;
    return true;
  }
}

class IsolateBarrierStore extends AtomicStudyFileStore {
  IsolateBarrierStore(super.path, this.signal, this.release);
  final String signal, release;
  @override Future<String?> read() async {
    final data = await super.read();
    await File(signal).writeAsString('read');
    while (!await File(release).exists()) {
      await Future<void>.delayed(const Duration(milliseconds: 2));
    }
    return data;
  }
}

void main() {
  test('real file CAS permits only one simultaneous same-process writer', () async {
    final dir = await Directory.systemTemp.createTemp('tideglass-qa-study-cas-');
    addTearDown(() => dir.delete(recursive: true));
    final path = '${dir.path}/study.json';
    await File(path).writeAsString('original', flush: true);
    final reads = DelayedReads();
    final a = BarrierFileStore(path, reads);
    final b = BarrierFileStore(path, reads);
    final expected = studyDigest('original');
    final first = a.compareAndSwap(expected, 'first');
    final second = b.compareAndSwap(expected, 'second');
    await Future.any([reads.both.future, Future<void>.delayed(const Duration(milliseconds: 250))]);
    reads.release.complete();
    final results = await Future.wait([first, second]);
    expect(results.where((x) => x).length, 1, reason: 'both stores read the same generation; exactly one must commit');
    expect(await File(path).readAsString(), anyOf('first', 'second'));
  });

  test('reserved unknown-config label cannot be registered as exact config', () {
    expect(() => StudyConfig(candidateSha256: 'a' * 64, economySha256: 'b' * 64, contentSha256: 'c' * 64, config: 'unqualified_config'), throwsA(isA<StudyException>()));
  });

  test('real file CAS is atomic across two isolates in the same process', () async {
    final dir = await Directory.systemTemp.createTemp('tideglass-qa-study-isolates-');
    addTearDown(() => dir.delete(recursive: true));
    final path = '${dir.path}/study.json';
    final signalA = '${dir.path}/a', signalB = '${dir.path}/b', release = '${dir.path}/release';
    await File(path).writeAsString('original', flush: true);
    final first = Isolate.run(() => IsolateBarrierStore(path, signalA, release).compareAndSwap(studyDigest('original'), 'first'));
    final second = Isolate.run(() => IsolateBarrierStore(path, signalB, release).compareAndSwap(studyDigest('original'), 'second'));
    final watch = Stopwatch()..start();
    while ((!await File(signalA).exists() || !await File(signalB).exists()) && watch.elapsed < const Duration(seconds: 1)) {
      await Future<void>.delayed(const Duration(milliseconds: 2));
    }
    await File(release).writeAsString('release');
    final results = await Future.wait([first, second]);
    expect(results.where((x) => x).length, 1);
  });

  test('equivalent path spellings share the same CAS exclusion', () async {
    final dir = await Directory.systemTemp.createTemp('tideglass-qa-study-alias-');
    addTearDown(() => dir.delete(recursive: true));
    final path = '${dir.path}/study.json';
    await File(path).writeAsString('original', flush: true);
    final reads = DelayedReads();
    final first = BarrierFileStore(path, reads).compareAndSwap(studyDigest('original'), 'first');
    final second = BarrierFileStore('${dir.path}/./study.json', reads).compareAndSwap(studyDigest('original'), 'second');
    await Future.any([reads.both.future, Future<void>.delayed(const Duration(milliseconds: 250))]);
    reads.release.complete();
    final results = await Future.wait([first, second]);
    expect(results.where((x) => x).length, 1);
  });

  test('actual foreground activity at exact inactivity boundary splits once', () async {
    final store = MemoryStore();
    var now = 100, id = 0;
    final recorder = await StudyRecorder.open(store, clock: () => DateTime.fromMillisecondsSinceEpoch(now * 1000, isUtc: true), idGenerator: () => (++id).toRadixString(16).padLeft(32, '0'));
    await recorder.enroll(StudyEnrollment(studyId: 'qa', protocolSha256: 'd' * 64, informationSha256: 'e' * 64, consentVersion: 'qa', eligibilityEvidenceSha256: 'f' * 64, synthetic: true, platform: 'test', deviceGroup: 'unclassified', acquisition: 'internal_test'), StudyConfig(candidateSha256: 'a' * 64, economySha256: 'b' * 64, contentSha256: 'c' * 64, config: 'qa'), eligibleFreshInstall: true);
    await recorder.interactiveHarbor(); await recorder.activity(StudyActivity.interaction);
    final original = recorder.sessionId;
    now = 1899; await recorder.foreground();
    expect(recorder.sessionId, original);
    now = 1900; await recorder.activity(StudyActivity.interaction);
    final next = recorder.sessionId;
    expect(next, isNot(original));
    await recorder.interactiveHarbor(); await recorder.foreground();
    expect(recorder.sessionId, next);
    final rows = (jsonDecode(store.value!)['records'] as List).cast<Map>();
    expect(rows.where((x) => x['kind'] == 'session_start').length, 1);
    expect(rows.sublist(rows.indexWhere((x) => x['kind'] == 'session_start')).map((x) => x['kind']), ['session_start', 'harbor_interactive', 'activity', 'foreground']);
  });
}
