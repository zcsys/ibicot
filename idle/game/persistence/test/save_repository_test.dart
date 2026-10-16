import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:test/test.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const digest =
    '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6';
final epoch = DateTime.utc(2026, 10, 16, 12);
Map<String, dynamic> state(int amount) => {'wallet_micros': '$amount'};
void checkPayload(Map<String, dynamic> value) {
  final wallet = BigInt.tryParse(value['wallet_micros']?.toString() ?? '');
  if (wallet == null || wallet.isNegative)
    throw const FormatException('Invalid wallet');
}

void main() {
  late Directory directory;
  SaveRepository repo({CommitProbe? probe, String config = digest}) =>
      SaveRepository(
        directory,
        economicVersion: 'tideglass-economy-1.0.0',
        economicDigest: config,
        validatePayload: checkPayload,
        now: () => epoch,
        commitProbe: probe,
      );
  setUp(() async {
    directory = await Directory.systemTemp.createTemp('tideglass-save-');
  });
  tearDown(() async {
    await directory.delete(recursive: true);
  });

  test(
    'fresh install differs from corrupted save; load before writing',
    () async {
      final store = repo();
      expect(
        () => store.save(state(1), settledThrough: epoch),
        throwsStateError,
      );
      expect((await store.load()).snapshot, isNull);
      final first = await store.save(state(123), settledThrough: epoch);
      expect(first.revision, 0);
      expect(first.envelope['parent'], isNull);
      expect((await repo().load()).snapshot!.payload, state(123));
    },
  );

  test(
    'rotating snapshots retain previous generation and exact huge values',
    () async {
      final store = repo();
      await store.load();
      final huge = BigInt.from(10).pow(120).toString();
      await store.save({'wallet_micros': huge}, settledThrough: epoch);
      final second = await store.save(
        state(500),
        settledThrough: epoch.add(const Duration(hours: 2)),
      );
      expect(second.revision, 1);
      expect(second.envelope['parent']['revision'], 0);
      final firstContainer = jsonDecode(
        await File('${directory.path}/progress.0.json').readAsString(),
      );
      expect(
        firstContainer['envelope']['gameplay_state']['payload']['wallet_micros'],
        huge,
      );
      expect(
        (await store.load()).snapshot!.settledThrough,
        epoch.add(const Duration(hours: 2)),
      );
    },
  );

  for (final stage in [
    CommitStage.beforeWrite,
    CommitStage.afterFlush,
    CommitStage.afterRename,
  ]) {
    test(
      'interruption at ${stage.name} recovers one consistent committed revision',
      () async {
        final first = repo();
        await first.load();
        await first.save(state(10), settledThrough: epoch);
        final failing = repo(
          probe: (at) async {
            if (at == stage)
              throw const FileSystemException('Injected interruption');
          },
        );
        await failing.load();
        await expectLater(
          failing.save(
            state(20),
            settledThrough: epoch.add(const Duration(hours: 1)),
          ),
          throwsA(isA<FileSystemException>()),
        );
        final recovered = (await repo().load()).snapshot!;
        final committed = stage == CommitStage.afterRename;
        expect(recovered.payload, state(committed ? 20 : 10));
        expect(recovered.revision, committed ? 1 : 0);
        expect(
          recovered.settledThrough,
          committed ? epoch.add(const Duration(hours: 1)) : epoch,
        );
      },
    );
  }

  test(
    'corrupt latest snapshot recovers prior generation with a visible warning',
    () async {
      final store = repo();
      await store.load();
      await store.save(state(10), settledThrough: epoch);
      await store.save(state(20), settledThrough: epoch);
      await File('${directory.path}/progress.1.json').writeAsString('{broken');
      final recovery = await repo().load();
      expect(recovery.snapshot!.payload, state(10));
      expect(recovery.recoveredFromBackup, isTrue);
      expect(recovery.issues, isNotEmpty);
    },
  );

  test('no valid generation never silently starts a fresh game', () async {
    await File('${directory.path}/progress.0.json').writeAsString('broken');
    await expectLater(repo().load(), throwsA(isA<CorruptSaveException>()));
    expect(
      await File('${directory.path}/progress.0.json').readAsString(),
      'broken',
    );
  });

  test(
    'concurrent writers are serialized and stale progression is rejected',
    () async {
      final one = repo(), two = repo();
      await one.load();
      await two.load();
      await one.save(state(10), settledThrough: epoch);
      await expectLater(
        two.save(state(20), settledThrough: epoch),
        throwsA(isA<SaveConflictException>()),
      );
      expect((await repo().load()).snapshot!.payload, state(10));
    },
  );

  test(
    'queued writes on one repository commit in order and capture input immediately',
    () async {
      final store = repo();
      await store.load();
      final mutable = state(1);
      final first = store.save(mutable, settledThrough: epoch);
      mutable['wallet_micros'] = '-5';
      final second = store.save(state(2), settledThrough: epoch);
      expect((await first).payload, state(1));
      expect((await second).revision, 1);
      expect((await store.load()).snapshot!.payload, state(2));
    },
  );

  test(
    'export/import selects progression and preserves displaced local branch',
    () async {
      final store = repo();
      await store.load();
      final first = await store.save(state(10), settledThrough: epoch);
      final exported = await store.exportSave();
      await store.save(
        state(20),
        settledThrough: epoch.add(const Duration(hours: 3)),
      );
      final imported = await store.importSave(exported);
      expect(imported.payload, state(10));
      expect(imported.revision, 2);
      expect(imported.branchId, isNot(first.branchId));
      expect(imported.settledThrough, epoch);
      expect(imported.envelope['commerce_cache']['entries'], isEmpty);
      final recovery =
          imported.envelope['preserved_branches'][0]['recovery_reference']
              as String;
      expect(await File(recovery).exists(), isTrue);
      expect((await repo().load()).snapshot!.payload, state(10));
    },
  );

  test(
    'explicit import can recover wholly corrupt saves while preserving raw copies',
    () async {
      final store = repo();
      await store.load();
      await store.save(state(10), settledThrough: epoch);
      final exported = await store.exportSave();
      await File(
        '${directory.path}/progress.0.json',
      ).writeAsString('bad generation 0');
      await File(
        '${directory.path}/progress.1.json',
      ).writeAsString('bad generation 1');
      final replacement = repo();
      await expectLater(
        replacement.load(),
        throwsA(isA<CorruptSaveException>()),
      );
      await expectLater(
        replacement.importSave(exported),
        throwsA(isA<CorruptSaveException>()),
      );
      await replacement.importSave(exported, recoverCorrupt: true);
      expect((await repo().load()).snapshot!.payload, state(10));
      final files = await Directory(
        '${directory.path}/recovery',
      ).list(recursive: true).where((f) => f is File).toList();
      expect(files.length, 2);
    },
  );

  test(
    'altered import fails checksum before it can change local progress',
    () async {
      final store = repo();
      await store.load();
      await store.save(state(10), settledThrough: epoch);
      final container = jsonDecode(await store.exportSave());
      container['envelope']['gameplay_state']['payload']['wallet_micros'] =
          '999';
      await expectLater(
        store.importSave(jsonEncode(container)),
        throwsA(isA<CorruptSaveException>()),
      );
      expect((await store.load()).snapshot!.payload, state(10));
    },
  );

  test(
    'unknown config is rejected without settling or overwriting either generation',
    () async {
      final store = repo();
      await store.load();
      await store.save(state(10), settledThrough: epoch);
      await expectLater(
        repo(config: '0' * 64).load(),
        throwsA(isA<IncompatibleSaveException>()),
      );
      expect((await store.load()).snapshot!.payload, state(10));
    },
  );

  test(
    'a signed-in-looking display cache never survives import as purchase authority',
    () async {
      final store = repo();
      await store.load();
      await store.save(state(10), settledThrough: epoch);
      final container =
          jsonDecode(await store.exportSave()) as Map<String, dynamic>;
      container['envelope']['commerce_cache']['entries'] = [
        {
          'entitlement_id': 'premium',
          'receipt_reference': 'untrusted',
          'display_status': 'active',
        },
      ];
      Object? canonical(Object? v) {
        if (v is Map) {
          final keys = v.keys.cast<String>().toList()..sort();
          return {for (final k in keys) k: canonical(v[k])};
        }
        if (v is List) return v.map(canonical).toList();
        return v;
      }

      container['checksum'] = sha256
          .convert(utf8.encode(jsonEncode(canonical(container['envelope']))))
          .toString();
      final imported = await store.importSave(jsonEncode(container));
      expect(imported.envelope['commerce_cache']['entries'], isEmpty);
    },
  );

  test(
    'clock rollback does not erase the prior settlement timestamp',
    () async {
      final store = repo();
      await store.load();
      final future = epoch.add(const Duration(days: 1));
      await store.save(state(10), settledThrough: future);
      final loaded = (await repo().load()).snapshot!;
      expect(loaded.settledThrough, future);
      expect(DateTime.parse(loaded.envelope['written_at_utc']), epoch);
    },
  );
  test(
    'snapshot identities are unique and parent refers to prior snapshot',
    () async {
      final store = repo();
      await store.load();
      final first = await store.save(state(1), settledThrough: epoch);
      final second = await store.save(state(2), settledThrough: epoch);
      expect(second.saveId, isNot(first.saveId));
      expect(second.envelope['parent']['save_id'], first.saveId);
      expect(second.branchId, first.branchId);
      expect((await repo().load()).snapshot!.saveId, second.saveId);
    },
  );
  test('fractional settled cursor survives disk and export exactly', () async {
    final store = repo();
    await store.load();
    final cursor = epoch.add(const Duration(microseconds: 987654));
    await store.save(state(123), settledThrough: cursor);
    expect((await repo().load()).snapshot!.settledThrough, cursor);
    final imported = await store.importSave(await store.exportSave());
    expect(imported.settledThrough, cursor);
  });
  test('normal save cannot rewind a committed cursor', () async {
    final store = repo();
    await store.load();
    await store.save(state(1), settledThrough: epoch);
    await expectLater(
      store.save(
        state(2),
        settledThrough: epoch.subtract(const Duration(microseconds: 1)),
      ),
      throwsA(isA<SaveConflictException>()),
    );
    expect((await repo().load()).snapshot!.payload, state(1));
  });
}
