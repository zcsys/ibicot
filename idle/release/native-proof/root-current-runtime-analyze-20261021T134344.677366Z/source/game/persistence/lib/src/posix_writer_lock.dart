import 'dart:ffi';
import 'dart:io';
import 'package:ffi/ffi.dart';

/// The Dart FileLock uses process-scoped POSIX record locks on these systems;
/// a separate Dart isolate can acquire that lock and overwrite an active writer.
/// flock instead locks each separately opened file description. Cooperating
/// isolates/processes cannot enter together; process exit releases the kernel
/// lock. Never unlink the stable lock file while any writer may be active.
class PosixWriterLock {
  PosixWriterLock._(this._fd);
  final int _fd;
  bool _released = false;

  static Future<PosixWriterLock> acquire(
    String path, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    if (!(Platform.isIOS ||
        Platform.isMacOS ||
        Platform.isAndroid ||
        Platform.isLinux)) {
      throw UnsupportedError(
        'Durable writer exclusion requires supported POSIX flock.',
      );
    }
    // Create through Dart first: open below passes only its two fixed arguments
    // and avoids a variadic mode_t ABI mismatch on Apple ARM64.
    final existing = await FileSystemEntity.type(path, followLinks: false);
    if (existing != FileSystemEntityType.notFound &&
        existing != FileSystemEntityType.file) {
      throw FileSystemException(
        'Writer lock must be a regular file, not a link',
        path,
      );
    }
    await File(path).create();
    if (await FileSystemEntity.type(path, followLinks: false) !=
            FileSystemEntityType.file ||
        ((await FileStat.stat(path)).mode & 0xf000) != 0x8000) {
      throw FileSystemException('Writer lock must be a regular file', path);
    }
    final name = path.toNativeUtf8();
    int fd;
    try {
      // O_RDWR=2. O_CLOEXEC prevents children from retaining this descriptor.
      final closeOnExec = (Platform.isIOS || Platform.isMacOS)
          ? 0x01000000
          : 0x00080000;
      final noFollow = (Platform.isIOS || Platform.isMacOS) ? 0x100 : 0x20000;
      fd = _api.open(name, 2 | closeOnExec | noFollow);
      if (fd < 0) {
        throw FileSystemException(
          'Cannot open writer lock',
          path,
          OSError('POSIX open failed', _api.errno().value),
        );
      }
    } finally {
      calloc.free(name);
    }
    final watch = Stopwatch()..start();
    var delayMs = 2;
    try {
      while (_api.flock(fd, 2 | 4) != 0) {
        // LOCK_EX | LOCK_NB
        final code = _api.errno().value;
        final wouldBlock = (Platform.isIOS || Platform.isMacOS) ? 35 : 11;
        if (code != wouldBlock && code != 4) {
          // EINTR
          throw FileSystemException(
            'Cannot acquire writer lock',
            path,
            OSError('POSIX flock failed', code),
          );
        }
        if (watch.elapsed >= timeout) {
          throw FileSystemException(
            'Timed out waiting for the active writer',
            path,
          );
        }
        // The OS call never blocks the UI isolate; waiting yields to its loop.
        await Future<void>.delayed(Duration(milliseconds: delayMs));
        if (delayMs < 32) delayMs *= 2;
      }
      return PosixWriterLock._(fd);
    } catch (_) {
      _api.close(fd);
      rethrow;
    }
  }

  void release() {
    if (_released) return;
    _released = true;
    // Closing also releases the lock if unlock is interrupted. Do not retry
    // close(EINTR): the OS may already have reused that numeric descriptor.
    _api.flock(_fd, 8); // LOCK_UN
    _api.close(_fd);
  }
}

final _api = _PosixApi();

class _PosixApi {
  _PosixApi()
    : library = Platform.isAndroid
          ? DynamicLibrary.open('libc.so')
          : Platform.isLinux
          ? DynamicLibrary.open('libc.so.6')
          : DynamicLibrary.process();
  final DynamicLibrary library;
  late final open = library
      .lookupFunction<
        Int32 Function(Pointer<Utf8>, Int32),
        int Function(Pointer<Utf8>, int)
      >('open', isLeaf: true);
  late final flock = library
      .lookupFunction<Int32 Function(Int32, Int32), int Function(int, int)>(
        'flock',
        isLeaf: true,
      );
  late final close = library
      .lookupFunction<Int32 Function(Int32), int Function(int)>(
        'close',
        isLeaf: true,
      );
  late final errno = library
      .lookupFunction<Pointer<Int32> Function(), Pointer<Int32> Function()>(
        (Platform.isIOS || Platform.isMacOS)
            ? '__error'
            : Platform.isAndroid
            ? '__errno'
            : '__errno_location',
        isLeaf: true,
      );
}
