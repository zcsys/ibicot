import 'dart:async';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_platform/soundtrack_cache.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';

void main() {
  late Directory root;
  late SoundtrackExportCache cache;
  late DateTime now;
  setUp(() async {
    root = await Directory.systemTemp.createTemp('tideglass-qa-cache-');
    now = DateTime.utc(2030, 1, 1);
    cache = SoundtrackExportCache(Directory('${root.path}/exports'), now: () => now);
  });
  tearDown(() async => root.delete(recursive: true));
  Future<File> archive(String id, {String? filename, DateTime? modified}) async {
    final dir = await Directory('${cache.directory.path}/soundtrack-$id').create(recursive: true);
    final file = await File('${dir.path}/${filename ?? SoundtrackDelivery.filename}').writeAsString('independent fixture');
    await file.setLastModified(modified ?? now);
    return file;
  }
  Matcher code(String value) => isA<SoundtrackCacheException>().having((e) => e.code, 'code', value);

  test('exact 24h boundary retains recent files then removes expired files', () async {
    final files = <File>[];
    for (var i = 0; i < 3; i++) { files.add(await archive('$i')); }
    final stamp = (await files.first.stat()).modified.toUtc();
    now = stamp.add(SoundtrackExportCache.retention).subtract(const Duration(microseconds: 1));
    var called = false;
    await expectLater(cache.export((_) async { called = true; }), throwsA(code('recent_exports_at_capacity')));
    expect(called, isFalse);
    for (final file in files) { expect(await file.exists(), isTrue); }
    now = stamp.add(SoundtrackExportCache.retention);
    await cache.export((directory) async { called = true; expect(await directory.list().length, 0); });
    expect(called, isTrue);
    for (final file in files) { expect(await file.exists(), isFalse); }
  });

  test('fresh directory timestamp protects an archive with old file timestamp', () async {
    final file = await archive('recent', modified: DateTime.utc(1970));
    final stamp = (await file.parent.stat()).modified.toUtc();
    now = stamp.add(SoundtrackExportCache.retention).subtract(const Duration(microseconds: 1));
    await cache.cleanExpired();
    expect(await file.exists(), isTrue);
    now = stamp.add(SoundtrackExportCache.retention);
    await cache.cleanExpired();
    expect(await file.parent.exists(), isFalse);
  });

  test('global lock includes a waiting share and releases after callback failure', () async {
    final file = await archive('shared');
    final other = SoundtrackExportCache(Directory('${root.path}/other'), now: () => now);
    final entered = Completer<void>(); final release = Completer<void>();
    final pending = cache.export((_) async { entered.complete(); await release.future; throw StateError('share failed'); });
    final failed = expectLater(pending, throwsStateError);
    await entered.future;
    now = now.add(const Duration(days: 2));
    await cache.cleanExpired();
    expect(await file.exists(), isTrue, reason: 'startup maintenance must not erase a share in flight');
    var called = false;
    await expectLater(other.export((_) async { called = true; }), throwsA(code('export_in_progress')));
    expect(called, isFalse);
    release.complete(); await failed;
    await cache.cleanExpired(); expect(await file.exists(), isFalse);
    await other.export((_) async { called = true; }); expect(called, isTrue);
  });

  test('recent partial and empty reservations also consume the three slots', () async {
    now = DateTime.now().toUtc();
    await archive('part', filename: 'download.part');
    await Directory('${cache.directory.path}/soundtrack-empty').create();
    await archive('done');
    await expectLater(cache.export((_) async { fail('must not begin fourth download'); }), throwsA(code('recent_exports_at_capacity')));
    expect(await cache.directory.list().length, 3);
    now = now.add(const Duration(days: 2));
    await cache.cleanExpired(); expect(await cache.directory.list().length, 0);
  });

  test('cache root link and child directory link never delete external files', () async {
    final outside = await Directory('${root.path}/outside').create();
    final marker = await File('${outside.path}/${SoundtrackDelivery.filename}').writeAsString('retain');
    await marker.setLastModified(DateTime.utc(1970));
    await Link(cache.directory.path).create(outside.path);
    await expectLater(cache.cleanExpired(), throwsA(code('cache_not_directory')));
    expect(await marker.readAsString(), 'retain');
    await Link(cache.directory.path).delete(); await cache.directory.create();
    await Link('${cache.directory.path}/soundtrack-link').create(outside.path);
    await expectLater(cache.cleanExpired(), throwsA(code('unrecognized_cache_entries')));
    expect(await marker.readAsString(), 'retain');
    expect(await Link('${cache.directory.path}/soundtrack-link').exists(), isTrue);
  });

  test('unknown nested content aborts the whole cleanup before deletion', () async {
    final valid = await archive('old');
    final unsafe = await archive('unsafe');
    final nested = await Directory('${unsafe.parent.path}/unexpected').create();
    now = now.add(const Duration(days: 2));
    await expectLater(cache.cleanExpired(), throwsA(code('unrecognized_cache_entries')));
    expect(await valid.exists(), isTrue); expect(await unsafe.exists(), isTrue);
    await nested.delete();
    await cache.cleanExpired();
    expect(await valid.exists(), isFalse); expect(await unsafe.exists(), isFalse);
  });

  test('exact per-file limit permits reservation while an extra byte refuses', () async {
    final file = await archive('sparse');
    var handle = await file.open(mode: FileMode.write); await handle.truncate(SoundtrackDelivery.maximumBytes); await handle.close();
    await file.setLastModified(now);
    var calls = 0;
    await cache.export((_) async { calls++; }); expect(calls, 1);
    handle = await file.open(mode: FileMode.write); await handle.truncate(SoundtrackDelivery.maximumBytes + 1); await handle.close();
    await expectLater(cache.export((_) async { calls++; }), throwsA(code('oversized_cache_entry')));
    expect(calls, 1); expect(await file.length(), SoundtrackDelivery.maximumBytes + 1);
  });

  test('real createTemp download naming remains recognized on later maintenance', () async {
    now = DateTime.now().toUtc();
    late File file;
    await cache.export((directory) async {
      final actual = await directory.createTemp('soundtrack-');
      file = await File('${actual.path}/${SoundtrackDelivery.filename}').writeAsString('fixture');
    });
    await cache.cleanExpired(); expect(await file.exists(), isTrue);
    now = now.add(const Duration(days: 2));
    await cache.cleanExpired(); expect(await file.parent.exists(), isFalse);
  });
}
