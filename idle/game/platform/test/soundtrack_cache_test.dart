import 'dart:async';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_platform/soundtrack_cache.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';

void main() {
  late Directory root;
  late DateTime now;
  late SoundtrackExportCache cache;
  setUp(() async {
    root = await Directory.systemTemp.createTemp('tideglass-cache-test-');
    now = DateTime.now().toUtc();
    cache = SoundtrackExportCache(
      Directory('${root.path}/exports'),
      now: () => now,
    );
  });
  tearDown(() async {
    await root.delete(recursive: true);
  });
  Future<File> add(String id) async {
    final dir = await Directory(
      '${cache.directory.path}/soundtrack-$id',
    ).create(recursive: true);
    return File(
      '${dir.path}/${SoundtrackDelivery.filename}',
    ).writeAsString('synthetic');
  }

  test(
    'three recent shares survive and fourth download never starts',
    () async {
      for (var n = 0; n < 3; n++) {
        await cache.export((_) => add('$n'));
      }
      var called = false;
      await expectLater(
        cache.export((_) async {
          called = true;
        }),
        throwsA(isA<SoundtrackCacheException>()),
      );
      expect(called, isFalse);
      expect(await cache.directory.list().length, 3);
    },
  );
  test('expired archives removed; backward time protects them', () async {
    final old = await add('old');
    now = now.subtract(const Duration(days: 2));
    await cache.cleanExpired();
    expect(await old.exists(), isTrue);
    now = DateTime.now().toUtc().add(const Duration(hours: 25));
    await cache.cleanExpired();
    expect(await old.exists(), isFalse);
    expect(await cache.directory.list().length, 0);
  });
  test('lock covers receiving sheet and releases after failure', () async {
    final gate = Completer<void>();
    final pending = cache.export((_) => gate.future);
    await expectLater(
      cache.export((_) async {}),
      throwsA(isA<SoundtrackCacheException>()),
    );
    await Future<void>.delayed(const Duration(milliseconds: 50));
    gate.completeError(StateError('synthetic'));
    await expectLater(pending, throwsStateError);
    await cache.export((_) async {});
  });
  test('external link is never followed or deleted', () async {
    final protected = await File(
      '${root.path}/protected',
    ).writeAsString('keep');
    await cache.directory.create();
    final dir = await Directory(
      '${cache.directory.path}/soundtrack-link',
    ).create();
    await Link(
      '${dir.path}/${SoundtrackDelivery.filename}',
    ).create(protected.path);
    now = now.add(const Duration(days: 2));
    await expectLater(
      cache.cleanExpired(),
      throwsA(isA<SoundtrackCacheException>()),
    );
    expect(await protected.readAsString(), 'keep');
  });
  test('unknown files refuse cleanup before any deletion', () async {
    final old = await add('old');
    await File('${cache.directory.path}/unrecognized').writeAsString('keep');
    now = now.add(const Duration(days: 2));
    await expectLater(
      cache.cleanExpired(),
      throwsA(isA<SoundtrackCacheException>()),
    );
    expect(await old.exists(), isTrue);
  });
  test('oversized legacy archive refuses another download', () async {
    final file = await add('large');
    final handle = await file.open(mode: FileMode.write);
    await handle.truncate(SoundtrackDelivery.maximumBytes + 1);
    await handle.close();
    await expectLater(
      cache.export((_) async {
        fail('download must not start');
      }),
      throwsA(isA<SoundtrackCacheException>()),
    );
  });
  test('bounded scan refuses large inventories without deleting', () async {
    for (var i = 0; i <= SoundtrackExportCache.scanLimit; i++) {
      await add('n$i');
    }
    now = now.add(const Duration(days: 2));
    await expectLater(
      cache.cleanExpired(),
      throwsA(isA<SoundtrackCacheException>()),
    );
    expect(
      await cache.directory.list().length,
      SoundtrackExportCache.scanLimit + 1,
    );
  });
}
