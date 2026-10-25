import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/ownership_clock.dart';

void main() {
  final binding = TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('dev.tideglass/ownership_clock');
  late OwnershipClockBridge bridge;
  late DateTime wall;
  var elapsed = 0;
  Map<String, dynamic> sample([String epoch = 'qa.device.boot']) => {'version': 1,
    'elapsed_us': 1000000, 'epoch_id': epoch, 'continuity_scope': 'boot'};
  setUp(() {
    wall = DateTime.utc(2026, 10, 19); elapsed = 0;
    bridge = OwnershipClockBridge(autoRefresh: false, wallClock: () => wall,
      elapsedMicroseconds: () => elapsed);
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (_) async => sample());
  });
  tearDown(() { bridge.dispose(); binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, null); });
  test('an older failed request cannot invalidate a newer accepted sample', () async {
    final first = Completer<Map<String, dynamic>>(); var calls = 0;
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (_) async =>
      ++calls == 1 ? first.future : sample('qa.newer.boot'));
    final old = bridge.refresh(); await Future<void>.delayed(Duration.zero);
    expect(await bridge.refresh(), isTrue);
    first.completeError(PlatformException(code: 'late_fixture_failure'));
    expect(await old, isFalse); expect(bridge.current!.bootId, 'qa.newer.boot');
  });
  test('exact projection lifetime and wall divergence boundaries are conservative', () async {
    await bridge.refresh(); elapsed = 30000000; wall = wall.add(const Duration(seconds: 30));
    expect(bridge.current, isNotNull); elapsed++; wall = wall.add(const Duration(microseconds: 1));
    expect(bridge.current, isNull);
    await bridge.refresh(); wall = wall.add(const Duration(microseconds: 250000));
    expect(bridge.current, isNotNull); wall = wall.add(const Duration(microseconds: 1));
    expect(bridge.current, isNull);
  });
  test('negative local projection and backward wall evidence hide grants', () async {
    await bridge.refresh(); elapsed = -1; expect(bridge.current, isNull);
    elapsed = 0; wall = wall.subtract(const Duration(microseconds: 1));
    expect(bridge.current, isNull);
    await bridge.refresh(); expect(bridge.current, isNotNull);
  });
  test('native invalidation during a request cannot resurrect evidence afterward', () async {
    final gate = Completer<Map<String, dynamic>>();
    binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (_) => gate.future);
    final request = bridge.refresh(); await Future<void>.delayed(Duration.zero);
    final message = Completer<void>();
    binding.defaultBinaryMessenger.handlePlatformMessage(channel.name,
      const StandardMethodCodec().encodeMethodCall(const MethodCall('invalidate')), (_) => message.complete());
    await message.future; gate.complete(sample()); expect(await request, isFalse); expect(bridge.current, isNull);
  });
}
