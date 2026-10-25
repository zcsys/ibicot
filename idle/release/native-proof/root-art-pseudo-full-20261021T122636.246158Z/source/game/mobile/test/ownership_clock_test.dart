import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/ownership_clock.dart';

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('dev.tideglass/ownership_clock');
  late OwnershipClockBridge clock;
  late int elapsed;
  late DateTime wall;
  Map<String, dynamic> sample({
    String scope = 'boot',
    String epoch = 'android.test_epoch',
    int value = 1000000,
  }) => {
    'version': 1,
    'elapsed_us': value,
    'epoch_id': epoch,
    'continuity_scope': scope,
  };
  setUp(() {
    elapsed = 0;
    wall = DateTime.utc(2026, 10, 19);
    clock = OwnershipClockBridge(
      autoRefresh: false,
      wallClock: () => wall,
      elapsedMicroseconds: () => elapsed,
    );
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (_) async => sample(),
    );
  });
  tearDown(() {
    clock.dispose();
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null);
  });

  test(
    'real channel contract projects bounded sample with full request uncertainty',
    () async {
      binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (
        call,
      ) async {
        expect(call.method, 'sample');
        elapsed += 250000;
        wall = wall.add(const Duration(milliseconds: 250));
        return sample();
      });
      expect(await clock.refresh(), isTrue);
      expect(clock.current!.elapsedMicroseconds, 1000000);
      expect(clock.current!.uncertaintyMicroseconds, 250001);
      expect(clock.restartContinuity, isTrue);
      elapsed += 2000000;
      wall = wall.add(const Duration(seconds: 2));
      expect(clock.current!.elapsedMicroseconds, 3000000);
    },
  );

  test('Apple process clock never advertises restart continuity', () async {
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (_) async => sample(scope: 'process', epoch: 'apple.process.test'),
    );
    expect(await clock.refresh(), isTrue);
    expect(clock.current, isNotNull);
    expect(clock.restartContinuity, isFalse);
  });

  test(
    'stale samples and suspend divergence hide evidence until refresh',
    () async {
      await clock.refresh();
      elapsed += 31000000;
      wall = wall.add(const Duration(seconds: 31));
      expect(clock.current, isNull);
      await clock.refresh();
      wall = wall.add(const Duration(seconds: 2)); // A clock that missed sleep.
      expect(clock.current, isNull);
      expect(await clock.refresh(), isTrue);
      expect(clock.current, isNotNull);
    },
  );

  test(
    'lifecycle invalidates pending replies; resume requires a fresh response',
    () async {
      final pending = Completer<Map<String, dynamic>>();
      binding.defaultBinaryMessenger.setMockMethodCallHandler(
        channel,
        (_) => pending.future,
      );
      final request = clock.refresh();
      await Future<void>.delayed(Duration.zero);
      clock.didChangeAppLifecycleState(AppLifecycleState.paused);
      pending.complete(sample());
      expect(await request, isFalse);
      expect(await clock.refresh(), isFalse);
      clock.didChangeAppLifecycleState(AppLifecycleState.resumed);
      expect(clock.current, isNull);
      binding.defaultBinaryMessenger.setMockMethodCallHandler(
        channel,
        (_) async => sample(),
      );
      expect(await clock.refresh(), isTrue);
    },
  );

  test('out of order replies cannot replace fresh device key epoch', () async {
    final first = Completer<Map<String, dynamic>>();
    var calls = 0;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (_) async =>
          ++calls == 1 ? await first.future : sample(epoch: 'android.new_key'),
    );
    final old = clock.refresh();
    await Future<void>.delayed(Duration.zero);
    expect(await clock.refresh(), isTrue);
    first.complete(sample(epoch: 'android.old_key'));
    expect(await old, isFalse);
    expect(clock.current!.bootId, 'android.new_key');
  });

  test('native invalidation notification clears sample', () async {
    var notifications = 0;
    clock.addListener(() => notifications++);
    await clock.refresh();
    final completer = Completer<void>();
    binding.defaultBinaryMessenger.handlePlatformMessage(
      channel.name,
      const StandardMethodCodec().encodeMethodCall(
        const MethodCall('invalidate'),
      ),
      (_) => completer.complete(),
    );
    await completer.future;
    expect(clock.current, isNull);
    expect(notifications, 2);
  });

  test(
    'missing, invalid, late or failed native evidence never becomes trusted',
    () async {
      for (final data in [
        null,
        {...sample(), 'elapsed_us': -1},
        {...sample(), 'epoch_id': ''},
        {...sample(), 'continuity_scope': 'guessed'},
      ]) {
        binding.defaultBinaryMessenger.setMockMethodCallHandler(
          channel,
          (_) async => data,
        );
        expect(await clock.refresh(), isFalse);
        expect(clock.current, isNull);
      }
      binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (
        _,
      ) async {
        elapsed += 4000000;
        return sample();
      });
      expect(await clock.refresh(), isFalse);
      binding.defaultBinaryMessenger.setMockMethodCallHandler(
        channel,
        (_) async => throw PlatformException(code: 'clock_unavailable'),
      );
      expect(await clock.refresh(), isFalse);
    },
  );

  test('dispose invalidates in-flight response and further refresh', () async {
    final pending = Completer<Map<String, dynamic>>();
    binding.defaultBinaryMessenger.setMockMethodCallHandler(
      channel,
      (_) => pending.future,
    );
    final request = clock.refresh();
    await Future<void>.delayed(Duration.zero);
    clock.dispose();
    pending.complete(sample());
    expect(await request, isFalse);
    expect(await clock.refresh(), isFalse);
    expect(clock.current, isNull);
  });
}
