import 'dart:async';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/audio_bus.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  const channel = MethodChannel('xyz.luan/audioplayers');
  final calls = <MethodCall>[];
  final globalCalls = <MethodCall>[];
  var failInitialization = false;
  setUp(() {
    messenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/path_provider'),
      (_) async => '/tmp',
    );
    calls.clear();
    globalCalls.clear();
    failInitialization = false;
    messenger.setMockMethodCallHandler(
      const MethodChannel('xyz.luan/audioplayers.global'),
      (call) async {
        globalCalls.add(call);
        return null;
      },
    );
    messenger.setMockMethodCallHandler(
      const MethodChannel('xyz.luan/audioplayers.global/events'),
      (_) async => null,
    );
    for (final id in [
      'tideglass.music',
      for (var i = 0; i < 8; i++) 'tideglass.sfx.$i',
    ]) {
      messenger.setMockMethodCallHandler(
        MethodChannel('xyz.luan/audioplayers/events/$id'),
        (_) async => null,
      );
    }
    messenger.setMockMethodCallHandler(channel, (call) async {
      calls.add(call);
      final arguments = call.arguments as Map;
      final playerId = arguments['playerId'] as String;
      if (failInitialization &&
          call.method == 'setReleaseMode' &&
          playerId == 'tideglass.sfx.2') {
        throw PlatformException(code: 'injected_partial_setup_failure');
      }
      if (call.method == 'setSourceUrl') {
        scheduleMicrotask(() {
          messenger.handlePlatformMessage(
            'xyz.luan/audioplayers/events/$playerId',
            const StandardMethodCodec().encodeSuccessEnvelope({
              'event': 'audio.onPrepared',
              'value': true,
            }),
            (_) {},
          );
        });
      }
      if (call.method == 'getCurrentPosition') return 0;
      return null;
    });
    // Bypass real filesystem cache only; the actual AudioPlayer and native
    // method/event bridge still execute, including pool and cleanup behavior.
    for (final name in [
      ...TideCue.values.map((c) => c.name),
      ...TideMusic.values.map((c) => c.name),
    ]) {
      AudioCache.instance.loadedFiles['audio/$name.m4a'] = Uri.parse(
        'file:///test-audio/$name.m4a',
      );
    }
  });

  test(
    'iOS ambient session initializes without incompatible mix options',
    () async {
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      addTearDown(() => debugDefaultTargetPlatformOverride = null);
      final driver = NativeTideAudioDriver();
      await driver.initialize();
      final context = globalCalls.lastWhere(
        (call) => call.method == 'setAudioContext',
      );
      expect(context.arguments, {'category': 'ambient', 'options': <String>[]});
      expect(calls.where((call) => call.method == 'create').length, 9);
      await driver.dispose();
    },
  );

  test(
    'partial native setup failure disposes every allocated player',
    () async {
      failInitialization = true;
      final driver = NativeTideAudioDriver();
      await expectLater(driver.initialize(), throwsA(isA<PlatformException>()));
      await driver.dispose();
      final created = calls
          .where((c) => c.method == 'create')
          .map((c) => (c.arguments as Map)['playerId'])
          .toSet();
      final disposed = calls
          .where((c) => c.method == 'dispose')
          .map((c) => (c.arguments as Map)['playerId'])
          .toSet();
      expect(created, {
        'tideglass.music',
        'tideglass.sfx.0',
        'tideglass.sfx.1',
        'tideglass.sfx.2',
      });
      expect(disposed, created);
      await driver.dispose();
      expect(calls.where((c) => c.method == 'dispose').length, 4);
    },
  );
  test(
    'real native adapter drops ninth voice and uses one music player',
    () async {
      final driver = NativeTideAudioDriver();
      await driver.initialize();
      for (var i = 0; i < 8; i++) {
        expect(await driver.playCue(TideCue.purchase, .4), isTrue);
      }
      expect(await driver.playCue(TideCue.rechart, .5), isFalse);
      await driver.playMusic(TideMusic.harbor, .2);
      await driver.playMusic(TideMusic.current, .2);
      expect(calls.where((c) => c.method == 'create').length, 9);
      expect(
        calls
            .where(
              (c) =>
                  c.method == 'resume' &&
                  (c.arguments as Map)['playerId'].toString().startsWith(
                    'tideglass.sfx',
                  ),
            )
            .length,
        8,
      );
      final latestVolumes = <String, double>{};
      for (final call in calls.where((call) => call.method == 'setVolume')) {
        final args = call.arguments as Map;
        latestVolumes[args['playerId'] as String] = (args['volume'] as num)
            .toDouble();
      }
      final sfxTotal = latestVolumes.entries
          .where((entry) => entry.key.startsWith('tideglass.sfx'))
          .fold<double>(0, (sum, entry) => sum + entry.value);
      expect(sfxTotal, closeTo(.4 * .9, 1e-12));
      expect(latestVolumes['tideglass.music'], closeTo(.2 * .5, 1e-12));
      await driver.stopCues();
      expect(await driver.playCue(TideCue.rechart, .5), isTrue);
      await driver.dispose();
      expect(calls.where((c) => c.method == 'dispose').length, 9);
    },
  );
}
