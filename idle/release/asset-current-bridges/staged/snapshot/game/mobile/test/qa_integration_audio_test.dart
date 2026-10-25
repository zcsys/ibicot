import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/audio_bus.dart';

// The real Dart native adapter executes against a delayed method-channel
// transport. This does not claim physical codec/playback qualification.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  const channel = MethodChannel('xyz.luan/audioplayers');
  final calls = <MethodCall>[];
  late Completer<void> firstPrepared, releaseFirstSource;
  var sources = 0;
  setUp(() {
    calls.clear();
    sources = 0;
    firstPrepared = Completer<void>();
    releaseFirstSource = Completer<void>();
    messenger.setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/path_provider'),
      (_) async => '/tmp',
    );
    messenger.setMockMethodCallHandler(
      const MethodChannel('xyz.luan/audioplayers.global'),
      (_) async => null,
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
      if (call.method == 'setSourceUrl') {
        sources++;
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
        if (sources == 1) {
          firstPrepared.complete();
          await releaseFirstSource.future;
        }
      }
      if (call.method == 'getCurrentPosition') return 0;
      return null;
    });
    for (final track in TideMusic.values) {
      AudioCache.instance.loadedFiles['audio/${track.name}.m4a'] = Uri.parse(
        'file:///qa-audio/${track.name}.m4a',
      );
    }
    for (final cue in TideCue.values) {
      AudioCache.instance.loadedFiles['audio/${cue.name}.m4a'] = Uri.parse(
        'file:///qa-audio/${cue.name}.m4a',
      );
    }
  });

  test('QA: delayed old music start cannot stop a newer route track', () async {
    final driver = NativeTideAudioDriver();
    addTearDown(driver.dispose);
    await driver.initialize();
    final oldStart = driver.playMusic(TideMusic.current, .3);
    await firstPrepared.future;
    await driver.playMusic(TideMusic.harbor, .3);
    releaseFirstSource.complete();
    await oldStart;
    final playback = calls.where(
      (call) =>
          (call.arguments as Map)['playerId'] == 'tideglass.music' &&
          {'stop', 'resume'}.contains(call.method),
    );
    expect(
      playback.last.method,
      'resume',
      reason:
          'Returning to the harbor must retain the newly selected music after older preparation completes.',
    );
    await driver.dispose();
  });

  test(
    'QA: stopped old cue cannot stop a reused voice after foreground return',
    () async {
      final driver = NativeTideAudioDriver();
      addTearDown(driver.dispose);
      await driver.initialize();
      final oldCue = driver.playCue(TideCue.purchase, .3);
      await firstPrepared.future;
      await driver.stopCues();
      expect(await driver.playCue(TideCue.rechart, .3), isTrue);
      releaseFirstSource.complete();
      expect(await oldCue, isFalse);
      final playback = calls.where(
        (call) =>
            (call.arguments as Map)['playerId'] == 'tideglass.sfx.0' &&
            {'stop', 'resume'}.contains(call.method),
      );
      expect(
        playback.last.method,
        'resume',
        reason:
            'An invalidated cue must not silence the new cue using its released voice.',
      );
    },
  );
}
