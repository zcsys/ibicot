import 'dart:convert';
import 'dart:io';

import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';
import 'support/synthetic_economy.dart';

const baselineDigest =
    '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6';
const oldEngine = SyntheticOldEconomy();
const newEngine = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 21, 12);
Map<String, dynamic> payload(GameState state) => {'core': state.toJson()};
GameState decode(Map<String, dynamic> value, String version) =>
    GameState.fromJson(Map<String, dynamic>.from(value['core'] as Map),
        expectedEconomicVersion: version);
void validateAt(Map<String, dynamic> value, DateTime cursor, String version) {
  final state = decode(value, version);
  if (state.daily.utcAnchorMicros! + state.elapsedMicros !=
      BigInt.from(cursor.microsecondsSinceEpoch)) {
    throw const FormatException('State and envelope cursors differ');
  }
}

final oldConfig = EconomicConfiguration(
    version: syntheticOldVersion,
    digest: syntheticOldDigest,
    validatePayload: (value) => decode(value, syntheticOldVersion),
    validateSnapshot: (value, cursor) =>
        validateAt(value, cursor, syntheticOldVersion));
Map<String, dynamic> migrate(Map<String, dynamic> value) {
  final adopted = newEngine.adoptCompatibleState(
      decode(value, syntheticOldVersion),
      sourceRulesVersion: syntheticOldVersion);
  if (!adopted.accepted) throw StateError(adopted.reason!);
  return payload(adopted.state);
}

Future<Map<String, dynamic>> settleOld(
    SaveSnapshot source, DateTime boundary) async {
  final state = decode(source.payload, source.economicVersion);
  final advanced = oldEngine.advance(
      state, boundary.difference(source.settledThrough),
      offline: true,
      offlineSettlement: OfflineSettlementRequest(
          sequence: state.nextSettlementSequence,
          fromUtc: source.settledThrough,
          throughUtc: boundary));
  if (!advanced.accepted) throw StateError(advanced.reason!);
  return payload(advanced.state);
}

void main() {
  late Directory directory;
  SaveRepository oldRepository() => SaveRepository(directory,
      economicVersion: syntheticOldVersion,
      economicDigest: syntheticOldDigest,
      validatePayload: oldConfig.validatePayload,
      validateSnapshot: oldConfig.validateSnapshot,
      now: () => epoch);
  SaveRepository destination(
          {CommitProbe? probe,
          bool knownPredecessor = true,
          Map<String, dynamic> Function(Map<String, dynamic>)? migration}) =>
      SaveRepository(directory,
          economicVersion: economyVersion,
          economicDigest: baselineDigest,
          validatePayload: (value) => decode(value, economyVersion),
          validateSnapshot: (value, cursor) =>
              validateAt(value, cursor, economyVersion),
          compatiblePredecessors: [
            if (knownPredecessor)
              CompatibleEconomicPredecessor(
                  configuration: oldConfig,
                  migratePayload: migration ?? migrate)
          ],
          now: () => epoch,
          commitProbe: probe);
  Future<SaveSnapshot> seed() async {
    final store = oldRepository();
    await store.load();
    final initial = oldEngine
        .refreshContracts(
            GameState.initial(rulesVersion: syntheticOldVersion), epoch,
            accountSeed: 'synthetic-transition')
        .state;
    return store.save(payload(initial), settledThrough: epoch);
  }

  Future<Map<String, String>> savedFiles() async => {
        for (final file in directory.listSync().whereType<File>())
          if (file.path.endsWith('.json')) file.path: await file.readAsString()
      };
  setUp(() async {
    directory = await Directory.systemTemp.createTemp('tideglass-transition-');
  });
  tearDown(() async => directory.delete(recursive: true));

  test('default decoder and wrong engine reject unknown rules before mutation',
      () {
    final old = GameState.initial(rulesVersion: syntheticOldVersion);
    expect(() => GameState.fromJson(old.toJson()), throwsFormatException);
    expect(() => newEngine.advance(old, const Duration(seconds: 1)),
        throwsStateError);
    expect(() => newEngine.collectSurveys(old), throwsStateError);
    expect(() => newEngine.refreshContracts(old, epoch, accountSeed: 'bad'),
        throwsStateError);
    expect(
        () => newEngine.initializeReceiptCursor(old, epoch), throwsStateError);
    expect(old.lifetimeMicros, BigInt.zero);
    expect(decode(payload(old), syntheticOldVersion).toJson(), old.toJson());
  });

  test('baseline serialization identity and default rules remain unchanged',
      () {
    final base = GameState.initial();
    expect(base.rulesVersion, economyVersion);
    expect(base.toJson()['economic_version'], economyVersion);
    expect(base.toJson().containsKey('rules_version'), isFalse);
    expect(GameState.fromJson(base.toJson()).toJson(), base.toJson());
    expect(newEngine.outputPerSecond(base).raw, Fixed.scale);
    expect(newEngine.priceMicros(0, 0), BigInt.from(30000000));
  });

  test('old 3/2 rate settles once; exact fractional residue crosses boundary',
      () async {
    final source = await seed();
    final store = destination();
    await store.load();
    final boundary = epoch.add(const Duration(microseconds: 1));
    final transitioned = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: settleOld);
    final state = decode(transitioned.payload, economyVersion);
    expect(state.walletMicros, BigInt.one);
    expect(state.lifetimeMicros, BigInt.one);
    expect(state.earningRemainder, Fixed.scale * BigInt.from(200));
    expect(state.support.lastSettlementSequence, BigInt.one);
    expect(transitioned.economicVersion, economyVersion);
    expect(transitioned.economicDigest, baselineDigest);
    expect(transitioned.envelope['applied_operation_ids'], hasLength(1));
    final next =
        newEngine.advance(state, const Duration(microseconds: 1)).state;
    expect(next.walletMicros, BigInt.two);
    expect(next.earningRemainder, state.earningRemainder);
    expect(next.charts, BigInt.zero);
    final again = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: (_, __) async => throw StateError('Must not settle twice'));
    expect(again.saveId, transitioned.saveId);
    final reopened = (await destination().load()).snapshot!;
    expect(reopened.envelope, transitioned.envelope);
  });

  test('old offline cap and quarter-rate tail apply before switch', () async {
    final source = await seed();
    final store = destination();
    await store.load();
    final boundary = epoch.add(const Duration(hours: 36));
    final saved = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: settleOld);
    final state = decode(saved.payload, economyVersion);
    expect(state.lifetimeMicros, BigInt.from(145800000000));
    expect(state.focusCharges, 12);
    expect(state.completedSurveys, 3);
    final next = newEngine.advance(state, const Duration(seconds: 1)).state;
    expect(next.lifetimeMicros - state.lifetimeMicros, BigInt.from(1000000));
  });

  for (final stage in CommitStage.values) {
    test('atomic transition interruption at ${stage.name} resumes exactly once',
        () async {
      final source = await seed();
      final boundary = epoch.add(const Duration(seconds: 10));
      var calls = 0;
      Future<Map<String, dynamic>> counted(SaveSnapshot s, DateTime b) {
        calls++;
        return settleOld(s, b);
      }

      final failing = destination(probe: (at) async {
        if (at == stage)
          throw const FileSystemException('Injected interruption');
      });
      await failing.load();
      await expectLater(
          failing.transitionEconomy(
              source: source,
              boundary: boundary,
              authorizedThrough: boundary,
              settleOld: counted),
          throwsA(isA<FileSystemException>()));
      final retry = destination();
      final loaded = (await retry.load()).snapshot!;
      expect(
          loaded.economicVersion,
          stage == CommitStage.afterRename
              ? economyVersion
              : syntheticOldVersion);
      final result = await retry.transitionEconomy(
          source: source,
          boundary: boundary,
          authorizedThrough: boundary,
          settleOld: counted);
      expect(decode(result.payload, economyVersion).lifetimeMicros,
          BigInt.from(15000000));
      expect(result.revision, source.revision + 1);
      expect(calls, stage == CommitStage.afterRename ? 1 : 2);
    });
  }

  test('unknown predecessor fails closed and preserves files', () async {
    await seed();
    final before = await savedFiles();
    await expectLater(destination(knownPredecessor: false).load(),
        throwsA(isA<IncompatibleSaveException>()));
    expect(await savedFiles(), before);
  });

  test('normal save cannot skip an old interval; predecessor import rejects',
      () async {
    final source = await seed();
    final exported = await oldRepository().exportSave();
    final store = destination();
    await store.load();
    final before = await savedFiles();
    await expectLater(
        store.save(migrate(source.payload), settledThrough: epoch),
        throwsA(isA<IncompatibleSaveException>()));
    await expectLater(
        store.importSave(exported), throwsA(isA<IncompatibleSaveException>()));
    expect(await savedFiles(), before);
  });

  test('backwards or unauthorized future boundary rejects before callback',
      () async {
    final source = await seed();
    final store = destination();
    await store.load();
    var calls = 0;
    final before = await savedFiles();
    for (final boundary in [
      epoch.subtract(const Duration(microseconds: 1)),
      epoch.add(const Duration(microseconds: 1))
    ]) {
      await expectLater(
          store.transitionEconomy(
              source: source,
              boundary: boundary,
              authorizedThrough: epoch,
              settleOld: (_, __) async {
                calls++;
                return source.payload;
              }),
          throwsA(isA<SaveException>()));
    }
    expect(calls, 0);
    expect(await savedFiles(), before);
  });

  test('mismatched settlement cursor or migration cannot commit partial state',
      () async {
    final source = await seed();
    final boundary = epoch.add(const Duration(seconds: 1));
    final before = await savedFiles();
    final store = destination();
    await store.load();
    await expectLater(
        store.transitionEconomy(
            source: source,
            boundary: boundary,
            authorizedThrough: boundary,
            settleOld: (_, __) async => source.payload),
        throwsFormatException);
    final broken = destination(migration: (value) => value);
    await broken.load();
    await expectLater(
        broken.transitionEconomy(
            source: source,
            boundary: boundary,
            authorizedThrough: boundary,
            settleOld: settleOld),
        throwsFormatException);
    expect(await savedFiles(), before);
  });

  test('callback cannot reenter this repository or a second instance',
      () async {
    final source = await seed();
    final store = destination(), second = destination();
    await store.load();
    await second.load();
    final boundary = epoch.add(const Duration(seconds: 1));
    await expectLater(
        store.transitionEconomy(
            source: source,
            boundary: boundary,
            authorizedThrough: boundary,
            settleOld: (_, __) async {
              await second.load();
              return source.payload;
            }),
        throwsStateError);
    expect((await store.load()).snapshot!.saveId, source.saveId);
  });

  test('same receipt cannot suppress a different boundary or source', () async {
    final source = await seed();
    final store = destination();
    await store.load();
    final boundary = epoch.add(const Duration(seconds: 1));
    final target = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: settleOld);
    await expectLater(
        store.transitionEconomy(
            source: source,
            boundary: boundary.add(const Duration(seconds: 1)),
            authorizedThrough: boundary.add(const Duration(seconds: 1)),
            settleOld: settleOld),
        throwsA(isA<SaveConflictException>()));
    await expectLater(
        store.transitionEconomy(
            source: target,
            boundary: boundary,
            authorizedThrough: boundary,
            settleOld: settleOld),
        throwsA(isA<IncompatibleSaveException>()));
    expect((await store.load()).snapshot!.saveId, target.saveId);
  });

  test('unfinished source accumulator cannot be rebound', () {
    final initial = oldEngine
        .refreshContracts(
            GameState.initial(rulesVersion: syntheticOldVersion), epoch,
            accountSeed: 'pending')
        .state;
    final request = OfflineSettlementRequest(
        sequence: initial.nextSettlementSequence,
        fromUtc: epoch,
        throughUtc: epoch.add(const Duration(seconds: 10)));
    final partial = oldEngine
        .advance(initial, const Duration(seconds: 2),
            offline: true,
            offlineSettlement: request,
            finalizeOfflineSettlement: false)
        .state;
    final adoption = newEngine.adoptCompatibleState(partial,
        sourceRulesVersion: syntheticOldVersion);
    expect(adoption.accepted, isFalse);
    expect(adoption.state.toJson(), partial.toJson());
  });

  test(
      'transition event uses destination identity and preserves every quantity',
      () {
    final old = oldEngine
        .advance(GameState.initial(rulesVersion: syntheticOldVersion),
            const Duration(microseconds: 7))
        .state;
    final result = newEngine.adoptCompatibleState(old,
        sourceRulesVersion: syntheticOldVersion);
    final expected = old.toJson()
      ..['economic_version'] = economyVersion
      ..['revision'] = old.revision + 1;
    expect(result.state.toJson(), expected);
    expect(result.events.single.id, startsWith('$economyVersion:'));
    expect(result.events.single.details['from'], syntheticOldVersion);
    expect(jsonEncode(result.state.toJson()), jsonEncode(expected));
  });
  test('transition receipt survives later saves without rolling progress back',
      () async {
    final source = await seed();
    final store = destination();
    await store.load();
    final boundary = epoch.add(const Duration(seconds: 1));
    final switched = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: settleOld);
    final advanced = newEngine
        .advance(decode(switched.payload, economyVersion),
            const Duration(seconds: 4))
        .state;
    final latest = await store.save(payload(advanced),
        settledThrough: boundary.add(const Duration(seconds: 4)));
    final retried = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: (_, __) async => throw StateError('No replay'));
    expect(retried.saveId, latest.saveId);
    expect(decode(retried.payload, economyVersion).lifetimeMicros,
        BigInt.from(5500000));
    expect(retried.envelope['applied_operation_ids'],
        switched.envelope['applied_operation_ids']);
    final exported = await store.exportSave();
    final imported = await store.importSave(exported);
    expect(imported.envelope['applied_operation_ids'], isEmpty);
    expect(imported.branchId, isNot(source.branchId));
    await expectLater(
        store.transitionEconomy(
            source: source,
            boundary: boundary,
            authorizedThrough: boundary,
            settleOld: settleOld),
        throwsA(isA<SaveConflictException>()));
  });

  test('two queued transition attempts invoke settlement only once', () async {
    final source = await seed();
    final first = destination(), second = destination();
    await first.load();
    await second.load();
    var calls = 0;
    Future<Map<String, dynamic>> counted(SaveSnapshot s, DateTime b) async {
      calls++;
      await Future<void>.delayed(const Duration(milliseconds: 5));
      return settleOld(s, b);
    }

    final boundary = epoch.add(const Duration(seconds: 1));
    final results = await Future.wait([
      first.transitionEconomy(
          source: source,
          boundary: boundary,
          authorizedThrough: boundary,
          settleOld: counted),
      second.transitionEconomy(
          source: source,
          boundary: boundary,
          authorizedThrough: boundary,
          settleOld: counted),
    ]);
    expect(calls, 1);
    expect(results[0].saveId, results[1].saveId);
    expect((await first.load()).snapshot!.revision, source.revision + 1);
  });

  test('old runtime cannot overwrite new pinned generation', () async {
    final source = await seed();
    final old = oldRepository();
    await old.load();
    final store = destination();
    await store.load();
    final boundary = epoch.add(const Duration(seconds: 1));
    final target = await store.transitionEconomy(
        source: source,
        boundary: boundary,
        authorizedThrough: boundary,
        settleOld: settleOld);
    final before = await savedFiles();
    await expectLater(old.save(source.payload, settledThrough: epoch),
        throwsA(isA<IncompatibleSaveException>()));
    expect(await savedFiles(), before);
    expect((await store.load()).snapshot!.saveId, target.saveId);
  });

  test('symlink alias cannot bypass settlement callback reentrancy guard',
      () async {
    final source = await seed();
    final alias = Link('${directory.path}-alias');
    await alias.create(directory.path);
    try {
      final second = SaveRepository(Directory(alias.path),
          economicVersion: syntheticOldVersion,
          economicDigest: syntheticOldDigest,
          validatePayload: oldConfig.validatePayload,
          validateSnapshot: oldConfig.validateSnapshot);
      final store = destination();
      await store.load();
      final boundary = epoch.add(const Duration(seconds: 1));
      await expectLater(
          store.transitionEconomy(
              source: source,
              boundary: boundary,
              authorizedThrough: boundary,
              settleOld: (_, __) async {
                await second.load();
                return source.payload;
              }),
          throwsStateError);
      expect((await store.load()).snapshot!.saveId, source.saveId);
    } finally {
      await alias.delete();
    }
  });
  test('zero pending interval changes rules without inventing income',
      () async {
    final source = await seed();
    final store = destination();
    await store.load();
    final saved = await store.transitionEconomy(
        source: source,
        boundary: epoch,
        authorizedThrough: epoch,
        settleOld: (old, boundary) async => old.payload);
    final state = decode(saved.payload, economyVersion);
    expect(state.lifetimeMicros, BigInt.zero);
    expect(state.walletMicros, BigInt.zero);
    expect(state.elapsedMicros, BigInt.zero);
    expect(state.support.lastSettlementSequence, BigInt.zero);
    expect(saved.settledThrough, epoch);
  });
}
