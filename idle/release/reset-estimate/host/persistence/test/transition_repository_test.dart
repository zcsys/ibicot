import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:test/test.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

final epoch = DateTime.utc(2026, 10, 21);
void payloadCheck(Map<String, dynamic> payload) {
  if (payload['amount'] is! int || payload['cursor'] is! String) {
    throw const FormatException('Invalid test payload');
  }
}

void cursorCheck(Map<String, dynamic> payload, DateTime cursor) {
  if (DateTime.parse(payload['cursor'] as String) != cursor) {
    throw const FormatException('Cursor mismatch');
  }
}

EconomicConfiguration oldConfig({bool withCursor = true}) =>
    EconomicConfiguration(
      version: 'tideglass-economy-0.0.1',
      digest: '0' * 64,
      validatePayload: payloadCheck,
      validateSnapshot: withCursor ? cursorCheck : null,
    );
SaveRepository oldStore(Directory dir) => SaveRepository(
  dir,
  economicVersion: 'tideglass-economy-0.0.1',
  economicDigest: '0' * 64,
  validatePayload: payloadCheck,
  validateSnapshot: cursorCheck,
);
SaveRepository destination(
  Directory dir, {
  CommitProbe? probe,
  bool oldCursor = true,
  bool newCursor = true,
}) => SaveRepository(
  dir,
  economicVersion: 'tideglass-economy-1.0.0',
  economicDigest: '1' * 64,
  validatePayload: payloadCheck,
  validateSnapshot: newCursor ? cursorCheck : null,
  commitProbe: probe,
  compatiblePredecessors: [
    CompatibleEconomicPredecessor(
      configuration: oldConfig(withCursor: oldCursor),
      migratePayload: (p) => p,
    ),
  ],
);
Future<SaveSnapshot> seed(Directory dir) async {
  final old = oldStore(dir);
  await old.load();
  return old.save({
    'amount': 0,
    'cursor': epoch.toIso8601String(),
  }, settledThrough: epoch);
}

Future<Map<String, dynamic>> settlement(SaveSnapshot old, DateTime end) async =>
    {'amount': 1, 'cursor': end.toIso8601String()};
Object? canonical(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return {for (final key in keys) key: canonical(value[key])};
  }
  if (value is List) return value.map(canonical).toList();
  return value;
}

void main() {
  late Directory dir;
  setUp(
    () async => dir = await Directory.systemTemp.createTemp('tideglass-edge-'),
  );
  tearDown(() async => dir.delete(recursive: true));

  test('compatible edges require old and destination cursor validators', () {
    expect(() => destination(dir, oldCursor: false), throwsArgumentError);
    expect(() => destination(dir, newCursor: false), throwsArgumentError);
  });

  test(
    'receipt binds complete source envelope beyond reused identity fields',
    () async {
      final source = await seed(dir);
      final oldExport = await oldStore(dir).exportSave();
      final store = destination(dir);
      await store.load();
      final end = epoch.add(const Duration(seconds: 1));
      final committed = await store.transitionEconomy(
        source: source,
        boundary: end,
        authorizedThrough: end,
        settleOld: settlement,
      );
      final altered = jsonDecode(oldExport) as Map<String, dynamic>;
      final envelope = altered['envelope'] as Map;
      (envelope['gameplay_state'] as Map)['payload']['amount'] = 7;
      altered['checksum'] = sha256
          .convert(utf8.encode(jsonEncode(canonical(envelope))))
          .toString();
      final other = await Directory('${dir.path}/other').create();
      await File(
        '${other.path}/progress.0.json',
      ).writeAsString(jsonEncode(altered));
      final changedSource = (await oldStore(other).load()).snapshot!;
      expect(changedSource.saveId, source.saveId);
      expect(changedSource.payload, isNot(source.payload));
      await expectLater(
        store.transitionEconomy(
          source: changedSource,
          boundary: end,
          authorizedThrough: end,
          settleOld: settlement,
        ),
        throwsA(isA<SaveConflictException>()),
      );
      expect((await store.load()).snapshot!.saveId, committed.saveId);
    },
  );

  test('nested A to B callback cannot reenter ancestor A', () async {
    final bDir = await Directory('${dir.path}/b').create();
    final sourceA = await seed(dir), sourceB = await seed(bDir);
    final a = destination(dir), b = destination(bDir);
    await a.load();
    await b.load();
    final end = epoch.add(const Duration(seconds: 1));
    await expectLater(
      a
          .transitionEconomy(
            source: sourceA,
            boundary: end,
            authorizedThrough: end,
            settleOld: (_, __) async {
              await b.transitionEconomy(
                source: sourceB,
                boundary: end,
                authorizedThrough: end,
                settleOld: (_, __) async {
                  await a.load();
                  return settlement(sourceB, end);
                },
              );
              return settlement(sourceA, end);
            },
          )
          .timeout(const Duration(seconds: 3)),
      throwsStateError,
    );
    expect((await a.load()).snapshot!.saveId, sourceA.saveId);
    expect((await b.load()).snapshot!.saveId, sourceB.saveId);
  });

  test(
    'ambiguous rename retry succeeds on same repository without load',
    () async {
      final source = await seed(dir);
      var interrupt = true, calls = 0;
      final store = destination(
        dir,
        probe: (stage) async {
          if (stage == CommitStage.afterRename && interrupt) {
            interrupt = false;
            throw const FileSystemException('Injected after rename');
          }
        },
      );
      await store.load();
      final end = epoch.add(const Duration(seconds: 1));
      Future<Map<String, dynamic>> counted(SaveSnapshot old, DateTime at) {
        calls++;
        return settlement(old, at);
      }

      await expectLater(
        store.transitionEconomy(
          source: source,
          boundary: end,
          authorizedThrough: end,
          settleOld: counted,
        ),
        throwsA(isA<FileSystemException>()),
      );
      final retry = await store.transitionEconomy(
        source: source,
        boundary: end,
        authorizedThrough: end,
        settleOld: counted,
      );
      expect(calls, 1);
      expect(retry.revision, source.revision + 1);
      expect(retry.payload['amount'], 1);
    },
  );
}
