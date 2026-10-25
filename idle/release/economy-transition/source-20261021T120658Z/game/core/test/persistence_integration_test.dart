// Non-author integration review of the independent persistence package using
// real core state. These host tests do not prove device power-loss durability.
import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const digest =
    '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6';
final epoch = DateTime.utc(2026, 10, 16, 12);
const engine = TideglassEngine();

void main() {
  late Directory directory;
  SaveRepository repository({CommitProbe? probe, String config = digest}) =>
      SaveRepository(
        directory,
        economicVersion: economyVersion,
        economicDigest: config,
        validatePayload: (payload) =>
            GameState.fromJson(payload['core'] as Map<String, dynamic>),
        now: () => epoch,
        commitProbe: probe,
      );
  Map<String, dynamic> payload(GameState state) =>
      {'core': state.toJson(), 'preferences': <String, dynamic>{}};
  GameState restore(SaveSnapshot snapshot) =>
      GameState.fromJson(snapshot.payload['core'] as Map<String, dynamic>);
  setUp(() async => directory =
      await Directory.systemTemp.createTemp('tideglass-core-review-'));
  tearDown(() async => directory.delete(recursive: true));

  test(
      'core exact strings and numeric remainders survive production save/reload',
      () async {
    final repo = repository();
    await repo.load();
    final original = GameState(
        walletMicros: BigInt.from(10).pow(120),
        lifetimeMicros: BigInt.from(10).pow(121),
        earningRemainder: BigInt.from(123456789),
        elapsedMicros: BigInt.from(10).pow(20));
    await repo.save(payload(original), settledThrough: epoch);
    final restored = restore((await repository().load()).snapshot!);
    expect(restored.toJson(), original.toJson());
  });

  test('fractional settlement cursor cannot replay the same fraction',
      () async {
    final repo = repository();
    await repo.load();
    await repo.save(payload(GameState.initial()), settledThrough: epoch);
    const firstDuration = Duration(seconds: 10, microseconds: 123456);
    final first =
        engine.advance(GameState.initial(), firstDuration, offline: true).state;
    await repo.save(payload(first), settledThrough: epoch.add(firstDuration));
    final loaded = (await repository().load()).snapshot!;
    expect(loaded.settledThrough, epoch.add(firstDuration));
    final later = epoch.add(const Duration(seconds: 20));
    final second = engine
        .advance(restore(loaded), later.difference(loaded.settledThrough),
            offline: true)
        .state;
    expect(second.lifetimeMicros, BigInt.from(20000000));
  });

  test('normal save cannot rewind committed settlement cursor', () async {
    final repo = repository();
    await repo.load();
    final state =
        engine.advance(GameState.initial(), const Duration(seconds: 40)).state;
    final snapshot = await repo.save(payload(state),
        settledThrough: epoch.add(const Duration(seconds: 40)));
    await expectLater(repo.save(payload(state), settledThrough: epoch),
        throwsA(isA<SaveException>()));
    final after = (await repository().load()).snapshot!;
    expect(after.saveId, snapshot.saveId);
    expect(after.settledThrough, snapshot.settledThrough);
  });

  test(
      'each committed envelope has unique snapshot identity and conforms to reviewed schema',
      () async {
    final repo = repository();
    await repo.load();
    final first =
        await repo.save(payload(GameState.initial()), settledThrough: epoch);
    final second = await repo.save(
        payload(engine
            .advance(GameState.initial(), const Duration(seconds: 1))
            .state),
        settledThrough:
            epoch.add(const Duration(seconds: 1, microseconds: 123)));
    expect(second.saveId, isNot(first.saveId));
    expect(second.envelope['parent']['save_id'], first.saveId);
    final envelopeFile = File('${directory.path}/schema-review.json');
    await envelopeFile.writeAsString(jsonEncode(second.envelope));
    final result = await Process.run('python3', [
      '../../implementation/tools/validate_save_contract.py',
      '--save',
      envelopeFile.path,
      '--config',
      '../../economy.json',
    ]);
    expect(result.exitCode, 0, reason: '${result.stdout}\n${result.stderr}');
  });

  test('stale real-core writer cannot replace newer production', () async {
    final first = repository(), stale = repository();
    await first.load();
    await first.save(payload(GameState.initial()), settledThrough: epoch);
    await stale.load();
    final progressed =
        engine.advance(GameState.initial(), const Duration(seconds: 40)).state;
    await first.save(payload(progressed),
        settledThrough: epoch.add(const Duration(seconds: 40)));
    await expectLater(
        stale.save(payload(GameState.initial()), settledThrough: epoch),
        throwsA(isA<SaveConflictException>()));
    expect(restore((await repository().load()).snapshot!).lifetimeMicros,
        BigInt.from(40000000));
  });

  test('after-rename interruption reloads the settled interval exactly once',
      () async {
    final repo = repository();
    await repo.load();
    await repo.save(payload(GameState.initial()), settledThrough: epoch);
    final interrupted = repository(probe: (stage) async {
      if (stage == CommitStage.afterRename)
        throw const FileSystemException('injected after committed rename');
    });
    await interrupted.load();
    final progressed = engine
        .advance(GameState.initial(), const Duration(seconds: 40),
            offline: true)
        .state;
    await expectLater(
        interrupted.save(payload(progressed),
            settledThrough: epoch.add(const Duration(seconds: 40))),
        throwsA(isA<FileSystemException>()));
    final loaded = (await repository().load()).snapshot!;
    final unchanged = engine
        .advance(
            restore(loaded),
            epoch
                .add(const Duration(seconds: 40))
                .difference(loaded.settledThrough),
            offline: true)
        .state;
    expect(unchanged.lifetimeMicros, BigInt.from(40000000));
  });

  test(
      'explicit import chooses earlier branch and preserves displaced snapshot',
      () async {
    final repo = repository();
    await repo.load();
    final early =
        engine.advance(GameState.initial(), const Duration(seconds: 40)).state;
    await repo.save(payload(early),
        settledThrough: epoch.add(const Duration(seconds: 40)));
    final export = await repo.exportSave();
    final later = engine.advance(early, const Duration(seconds: 60)).state;
    final displaced = await repo.save(payload(later),
        settledThrough: epoch.add(const Duration(seconds: 100)));
    final selected = await repo.importSave(export);
    expect(restore(selected).walletMicros, BigInt.from(40000000));
    expect(selected.branchId, isNot(displaced.branchId));
    final recovery =
        (selected.envelope['preserved_branches'] as List).single as Map;
    expect(recovery['save_id'], displaced.saveId);
    expect(
        await File('${repo.directory.path}/${recovery['recovery_reference']}')
            .exists(),
        isTrue);
    expect(recovery['recovery_reference'], startsWith('recovery/'));
    expect(
        recovery['recovery_reference'], isNot(contains(repo.directory.path)));
  });

  test('wrong economic config cannot settle an existing core state', () async {
    final repo = repository();
    await repo.load();
    await repo.save(payload(GameState.initial()), settledThrough: epoch);
    await expectLater(repository(config: 'a' * 64).load(),
        throwsA(isA<IncompatibleSaveException>()));
    expect(restore((await repository().load()).snapshot!).toJson(),
        GameState.initial().toJson());
  });
}
