import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'package:test/test.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const _digest =
    '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6';
final _epoch = DateTime.utc(2026, 10, 21);
SaveRepository _repository(String path, {CommitProbe? probe}) => SaveRepository(
  Directory(path),
  economicVersion: 'tideglass-economy-1.0.0',
  economicDigest: _digest,
  validatePayload: (value) {
    if (value['amount'] is! int) throw const FormatException('amount');
  },
  commitProbe: probe,
);

Future<void> _writer(List<Object> arguments) async {
  final path = arguments[0] as String, parent = arguments[1] as SendPort;
  final release = ReceivePort();
  try {
    final store = _repository(
      path,
      probe: (stage) async {
        if (stage == CommitStage.beforeWrite) {
          parent.send(['locked', release.sendPort]);
          await release.first;
        }
      },
    );
    await store.load();
    await store.save({'amount': 1}, settledThrough: _epoch);
    parent.send(['finished']);
  } catch (error, trace) {
    parent.send(['error', '$error\n$trace']);
  } finally {
    release.close();
  }
}

void main() {
  test(
    'independent isolate cannot commit while another holds writer lock',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'tideglass-lock-',
      );
      final port = ReceivePort();
      final locked = Completer<SendPort>(), finished = Completer<void>();
      final subscription = port.listen((dynamic message) {
        if (message[0] == 'locked') locked.complete(message[1] as SendPort);
        if (message[0] == 'finished') finished.complete();
        if (message[0] == 'error')
          finished.completeError(StateError(message[1] as String));
      });
      Isolate? worker;
      SendPort? release;
      try {
        final seed = _repository(directory.path);
        await seed.load();
        await seed.save({'amount': 0}, settledThrough: _epoch);
        final contender = _repository(directory.path);
        await contender.load();
        worker = await Isolate.spawn(_writer, <Object>[
          directory.path,
          port.sendPort,
        ]);
        release = await locked.future.timeout(const Duration(seconds: 5));
        final competing = contender
            .save({'amount': 2}, settledThrough: _epoch)
            .then<Object>((value) => value, onError: (Object error) => error);
        final early = await competing.timeout(
          const Duration(milliseconds: 100),
          onTimeout: () => 'still_waiting',
        );
        release.send(true);
        await finished.future.timeout(const Duration(seconds: 5));
        final result = await competing.timeout(const Duration(seconds: 5));
        expect(
          early,
          isNot(isA<SaveSnapshot>()),
          reason:
              'A separate isolate must not commit through the held OS lock.',
        );
        expect(
          result,
          anyOf(isA<FileSystemException>(), isA<SaveConflictException>()),
        );
        expect((await seed.load()).snapshot!.payload, {'amount': 1});
      } finally {
        release?.send(true);
        worker?.kill(priority: Isolate.immediate);
        await subscription.cancel();
        port.close();
        await directory.delete(recursive: true);
      }
    },
  );
  for (final stage in [
    CommitStage.beforeWrite,
    CommitStage.afterFlush,
    CommitStage.afterRename,
  ]) {
    test(
      'terminated child at ${stage.name} releases lock without orphan recovery',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'tideglass-process-lock-',
        );
        Process? child;
        try {
          final seed = _repository(directory.path);
          await seed.load();
          await seed.save({'amount': 0}, settledThrough: _epoch);
          final contender = _repository(directory.path);
          await contender.load();
          child = await Process.start(Platform.resolvedExecutable, [
            '--packages=${File('.dart_tool/package_config.json').absolute.path}',
            'test/helpers/writer_process.dart',
            directory.path,
            stage.name,
          ]);
          final errors = child.stderr.transform(utf8.decoder).join();
          final ready = await child.stdout
              .transform(utf8.decoder)
              .transform(const LineSplitter())
              .first
              .timeout(const Duration(seconds: 10));
          expect(ready, 'LOCKED');
          final competing = contender
              .save({'amount': 2}, settledThrough: _epoch)
              .then<Object>((value) => value, onError: (Object error) => error);
          final early = await competing.timeout(
            const Duration(milliseconds: 100),
            onTimeout: () => 'still_waiting',
          );
          expect(
            early,
            'still_waiting',
            reason: 'Live child must exclude competing writer.',
          );
          expect(child.kill(ProcessSignal.sigkill), isTrue);
          await child.exitCode.timeout(const Duration(seconds: 5));
          expect(await errors, isEmpty);
          final result = await competing.timeout(const Duration(seconds: 5));
          if (stage == CommitStage.afterRename) {
            expect(result, isA<SaveConflictException>());
            expect((await seed.load()).snapshot!.payload, {'amount': 1});
          } else {
            expect(result, isA<SaveSnapshot>());
            expect((await seed.load()).snapshot!.payload, {'amount': 2});
          }
        } finally {
          child?.kill(ProcessSignal.sigkill);
          await directory.delete(recursive: true);
        }
      },
    );
  }
  test(
    'symlink or directory writer.lock is rejected before any snapshot write',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'tideglass-lock-kind-',
      );
      final outside = File('${directory.path}/unrelated.txt');
      await outside.writeAsString('preserve');
      final link = Link('${directory.path}/writer.lock');
      try {
        await link.create(outside.path);
        await expectLater(
          _repository(directory.path).load(),
          throwsA(isA<FileSystemException>()),
        );
        expect(await outside.readAsString(), 'preserve');
        await link.delete();
        await Directory(link.path).create();
        await expectLater(
          _repository(directory.path).load(),
          throwsA(isA<FileSystemException>()),
        );
        expect(
          await File('${directory.path}/progress.0.json').exists(),
          isFalse,
        );
        expect(await outside.readAsString(), 'preserve');
      } finally {
        await directory.delete(recursive: true);
      }
    },
  );
}
