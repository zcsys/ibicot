import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/audio_bus.dart';

class MemoryAudioStore implements AudioPreferenceStore {
  AudioPreferences? value;
  bool corrupt = false, failSave = false;
  Completer<void>? hold;
  @override
  Future<AudioPreferences?> load() async {
    if (corrupt) throw const FormatException('corrupt');
    return value;
  }

  @override
  Future<void> save(AudioPreferences next) async {
    if (hold != null) await hold!.future;
    if (failSave) throw const FileSystemException('full');
    value = next;
  }
}

class FakeAudioDriver implements TideAudioDriver {
  final cues = <TideCue>[];
  final tracks = <TideMusic>[];
  Completer<void>? initializing;
  int stopCueCount = 0, stopMusicCount = 0, disposed = 0;
  double musicVolume = 0, sfxVolume = 0;
  bool broken = false;
  @override
  Future<void> initialize() async {
    if (initializing != null) await initializing!.future;
  }

  @override
  Future<bool> playCue(TideCue cue, double volume) async {
    if (broken) throw StateError('codec');
    cues.add(cue);
    sfxVolume = volume;
    return true;
  }

  @override
  Future<void> playMusic(TideMusic track, double volume) async {
    tracks.add(track);
    musicVolume = volume;
  }

  @override
  Future<void> stopMusic() async {
    stopMusicCount++;
  }

  @override
  Future<void> setMusicVolume(double volume) async {
    musicVolume = volume;
  }

  @override
  Future<void> stopCues() async {
    stopCueCount++;
  }

  @override
  Future<void> setSfxVolume(double volume) async {
    sfxVolume = volume;
  }

  @override
  Future<void> dispose() async {
    disposed++;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late MemoryAudioStore store;
  late FakeAudioDriver driver;
  late TideAudioBus audio;
  var now = DateTime.utc(2026, 10, 16);
  setUp(() {
    now = DateTime.utc(2026, 10, 16);
    store = MemoryAudioStore();
    driver = FakeAudioDriver();
    audio = TideAudioBus(
      driver: driver,
      store: store,
      clock: () => now,
      observeLifecycle: false,
    );
  });
  tearDown(() async {
    await audio.close();
    audio.dispose();
  });

  test('separate volumes and mutes survive a cold reload', () async {
    await audio.setPreferences(
      const AudioPreferences(musicVolume: .2, sfxVolume: .8, musicMuted: true),
    );
    expect(store.value!.musicMuted, isTrue);
    final reloaded = TideAudioBus(
      driver: FakeAudioDriver(),
      store: store,
      observeLifecycle: false,
    );
    await reloaded.initialize();
    expect(reloaded.preferences.musicVolume, .2);
    expect(reloaded.preferences.effectiveMusic, 0);
    expect(reloaded.preferences.effectiveSfx, .8);
    await reloaded.close();
    reloaded.dispose();
  });
  test('mute stops voices before a slow preference write finishes', () async {
    await audio.initialize();
    await audio.playCue(TideCue.claim);
    store.hold = Completer<void>();
    final pending = audio.setPreferences(
      audio.preferences.copyWith(muted: true),
    );
    await Future<void>.delayed(Duration.zero);
    expect(driver.stopCueCount, 1);
    expect(driver.stopMusicCount, 1);
    expect(await audio.playCue(TideCue.rechart), isFalse);
    store.hold!.complete();
    await pending;
  });
  test('offline, stale and future events never become audible', () async {
    expect(await audio.playCue(TideCue.milestone, offline: true), isFalse);
    expect(
      await audio.playCue(
        TideCue.claim,
        occurredAt: now.subtract(const Duration(seconds: 1)),
      ),
      isFalse,
    );
    expect(
      await audio.playCue(
        TideCue.purchase,
        occurredAt: now.add(const Duration(seconds: 1)),
      ),
      isFalse,
    );
    expect(driver.cues, isEmpty);
  });
  test('background clears cues and resumes only selected music', () async {
    await audio.startMusic(TideMusic.dawn);
    await audio.playCue(TideCue.calibration);
    await audio.setForeground(false);
    for (var i = 0; i < 50; i++) {
      await audio.playCue(TideCue.purchase);
    }
    await audio.setForeground(true);
    expect(driver.cues, [TideCue.calibration]);
    expect(driver.tracks, [TideMusic.dawn, TideMusic.dawn]);
    expect(driver.stopCueCount, 2);
  });
  test('background during initialization cancels the waiting cue', () async {
    driver.initializing = Completer<void>();
    final cue = audio.playCue(TideCue.claim);
    final background = audio.setForeground(false);
    driver.initializing!.complete();
    expect(await cue, isFalse);
    await background;
    await audio.setForeground(true);
    expect(driver.cues, isEmpty);
  });
  test('per-action debounce drops repetitions without replay queue', () async {
    expect(await audio.playCue(TideCue.purchase), isTrue);
    expect(await audio.playCue(TideCue.purchase), isFalse);
    expect(await audio.playCue(TideCue.claim), isTrue);
    now = now.add(const Duration(milliseconds: 101));
    expect(await audio.playCue(TideCue.purchase), isTrue);
    expect(driver.cues.length, 3);
  });
  test(
    'corrupt preference preserves uncertain mute by failing quietly',
    () async {
      store.corrupt = true;
      await audio.initialize();
      expect(audio.preferences.muted, isTrue);
      expect(audio.warning, contains('could not be read'));
      expect(await audio.playCue(TideCue.claim), isFalse);
      expect(store.value, isNull);
    },
  );
  test('disk write failure does not undo current mute choice', () async {
    store.failSave = true;
    await audio.setPreferences(const AudioPreferences(muted: true));
    expect(audio.preferences.muted, isTrue);
    expect(audio.warning, contains('could not be saved'));
  });
  test(
    'codec failure reports unavailable without throwing into play',
    () async {
      driver.broken = true;
      expect(await audio.playCue(TideCue.claim), isFalse);
      expect(audio.warning, contains('temporarily unavailable'));
    },
  );
  test('closure is idempotent and drops all later events', () async {
    await audio.close();
    await audio.close();
    expect(driver.disposed, 1);
    expect(await audio.playCue(TideCue.claim), isFalse);
  });
  test('preference parser rejects invalid, extra and non-finite values', () {
    for (final invalid in [-.1, 1.1, double.nan, double.infinity, '1']) {
      expect(
        () => AudioPreferences.fromJson({
          ...const AudioPreferences().toJson(),
          'music_volume': invalid,
        }),
        throwsFormatException,
      );
    }
    expect(
      () => AudioPreferences.fromJson({
        ...const AudioPreferences().toJson(),
        'extra': true,
      }),
      throwsFormatException,
    );
  });
  test(
    'real atomic file store retains final choice after queued writes',
    () async {
      final dir = await Directory.systemTemp.createTemp('tideglass-audio-');
      try {
        final disk = FileAudioPreferenceStore(File('${dir.path}/sound.json'));
        await Future.wait([
          disk.save(const AudioPreferences(musicVolume: .1)),
          disk.save(const AudioPreferences(musicVolume: .8, muted: true)),
        ]);
        final loaded = await disk.load();
        expect(loaded!.musicVolume, .8);
        expect(loaded.muted, isTrue);
        expect(await File('${dir.path}/sound.json.pending').exists(), isFalse);
      } finally {
        await dir.delete(recursive: true);
      }
    },
  );
}
