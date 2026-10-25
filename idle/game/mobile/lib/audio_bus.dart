import 'strings.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/widgets.dart';

/// These are presentation events. Passive earnings and replay never emit cues.
enum TideCue {
  purchase,
  panel,
  claim,
  calibration,
  survey,
  unlock,
  milestone,
  rechart,
}

enum TideMusic { harbor, current, dawn }

@immutable
class AudioPreferences {
  const AudioPreferences({
    this.musicVolume = .32,
    this.sfxVolume = .55,
    this.musicMuted = false,
    this.sfxMuted = false,
    this.muted = false,
  });

  final double musicVolume, sfxVolume;
  final bool musicMuted, sfxMuted, muted;

  double get effectiveMusic => muted || musicMuted ? 0 : musicVolume;
  double get effectiveSfx => muted || sfxMuted ? 0 : sfxVolume;

  AudioPreferences copyWith({
    double? musicVolume,
    double? sfxVolume,
    bool? musicMuted,
    bool? sfxMuted,
    bool? muted,
  }) => AudioPreferences(
    musicVolume: musicVolume ?? this.musicVolume,
    sfxVolume: sfxVolume ?? this.sfxVolume,
    musicMuted: musicMuted ?? this.musicMuted,
    sfxMuted: sfxMuted ?? this.sfxMuted,
    muted: muted ?? this.muted,
  );

  Map<String, Object> toJson() => {
    'schema_version': 1,
    'music_volume': musicVolume,
    'sfx_volume': sfxVolume,
    'music_muted': musicMuted,
    'sfx_muted': sfxMuted,
    'muted': muted,
  };

  factory AudioPreferences.fromJson(Map<String, dynamic> json) {
    const fields = {
      'schema_version',
      'music_volume',
      'sfx_volume',
      'music_muted',
      'sfx_muted',
      'muted',
    };
    if (json.length != fields.length ||
        !json.keys.every(fields.contains) ||
        json['schema_version'] != 1) {
      throw const FormatException('Unsupported audio preferences.');
    }
    double volume(String key) {
      final value = json[key];
      if (value is! num || !value.isFinite || value < 0 || value > 1) {
        throw const FormatException(
          'Audio volume must be between zero and one.',
        );
      }
      return value.toDouble();
    }

    for (final key in ['music_muted', 'sfx_muted', 'muted']) {
      if (json[key] is! bool) {
        throw const FormatException('Invalid audio mute preference.');
      }
    }
    return AudioPreferences(
      musicVolume: volume('music_volume'),
      sfxVolume: volume('sfx_volume'),
      musicMuted: json['music_muted'] as bool,
      sfxMuted: json['sfx_muted'] as bool,
      muted: json['muted'] as bool,
    );
  }
}

abstract interface class AudioPreferenceStore {
  Future<AudioPreferences?> load();
  Future<void> save(AudioPreferences value);
}

/// Separate from the economic save: a preference failure cannot roll back play.
/// Writes are serialized and atomically replace one small preference file.
class FileAudioPreferenceStore implements AudioPreferenceStore {
  FileAudioPreferenceStore(this.file);
  final File file;
  Future<void> _tail = Future<void>.value();

  @override
  Future<AudioPreferences?> load() async {
    if (!await file.exists()) return null;
    if (await file.length() > 4096) {
      throw const FormatException('Audio preferences exceed their size limit.');
    }
    final value = jsonDecode(await file.readAsString());
    if (value is! Map<String, dynamic>) {
      throw const FormatException('Invalid audio preferences.');
    }
    return AudioPreferences.fromJson(value);
  }

  @override
  Future<void> save(AudioPreferences value) {
    final encoded = jsonEncode(
      AudioPreferences.fromJson(value.toJson()).toJson(),
    );
    final operation = _tail.then((_) async {
      await file.parent.create(recursive: true);
      final temporary = File('${file.path}.pending');
      await temporary.writeAsString(encoded, flush: true);
      await temporary.rename(file.path);
    });
    _tail = operation.catchError((Object _) {});
    return operation;
  }
}

abstract interface class TideAudioDriver {
  Future<void> initialize();
  Future<void> playMusic(TideMusic track, double volume);
  Future<void> stopMusic();
  Future<void> setMusicVolume(double volume);
  Future<bool> playCue(TideCue cue, double volume);
  Future<void> stopCues();
  Future<void> setSfxVolume(double volume);
  Future<void> dispose();
}

/// One streamed music player and eight bounded effect voices. Excess effects
/// are dropped, never queued. One music stream is below the two-stream budget.
class NativeTideAudioDriver implements TideAudioDriver {
  AudioPlayer? _music;
  final List<AudioPlayer> _voices = [];
  final List<bool> _busy = [];
  final List<StreamSubscription<void>> _completions = [];
  final List<int> _voiceEpoch = [];
  final List<double> _requestedVoiceVolumes = [];
  Future<void> _mixTail = Future<void>.value();
  Future<void>? _initializing;
  int _musicEpoch = 0, _cueGeneration = 0;
  TideMusic? _playingTrack;
  bool _disposed = false;
  static const maxVoices = 8;

  @override
  Future<void> initialize() => _initializing ??= _initialize();

  Future<void> _initialize() async {
    if (_disposed) return;
    await AudioPlayer.global.setAudioContext(
      AudioContext(
        android: AudioContextConfig(
          respectSilence: true,
          stayAwake: false,
          focus: AudioContextConfigFocus.mixWithOthers,
        ).buildAndroid(),
        // Ambient already mixes other audio and respects the Silent switch.
        // Adding mixWithOthers to the generic silence-respecting config is
        // rejected by the iOS adapter before a native player can be created.
        iOS: AudioContextIOS(category: AVAudioSessionCategory.ambient),
      ),
    );
    if (_disposed) return;
    _music = AudioPlayer(playerId: 'tideglass.music');
    await _music!.setReleaseMode(ReleaseMode.loop);
    for (var i = 0; i < maxVoices; i++) {
      final player = AudioPlayer(playerId: 'tideglass.sfx.$i');
      _voices.add(player);
      _busy.add(false);
      _voiceEpoch.add(0);
      _requestedVoiceVolumes.add(0);
      _completions.add(
        player.onPlayerComplete.listen((_) {
          _busy[i] = false;
          unawaited(_rebalanceVoices().catchError((Object _) {}));
        }),
      );
      await player.setReleaseMode(ReleaseMode.stop);
    }
  }

  @override
  Future<void> playMusic(TideMusic track, double volume) async {
    final epoch = ++_musicEpoch;
    await initialize();
    if (_disposed || epoch != _musicEpoch || volume <= 0) return;
    if (_playingTrack == track && _music!.state == PlayerState.playing) {
      await _music!.setVolume(volume * .5);
      return;
    }
    await _music!.stop();
    if (_disposed || epoch != _musicEpoch) return;
    _playingTrack = track;
    await _music!.setVolume(volume * .5);
    if (_disposed || epoch != _musicEpoch) return;
    await _music!.setSource(AssetSource('audio/${track.name}.m4a'));
    // A previous source preparation can finish after a newer route request.
    // It must neither resume stale audio nor stop the shared newer player.
    if (_disposed || epoch != _musicEpoch) return;
    await _music!.resume();
  }

  @override
  Future<void> stopMusic() async {
    _musicEpoch++;
    _playingTrack = null;
    await _music?.stop();
  }

  @override
  Future<void> setMusicVolume(double volume) async =>
      _music?.setVolume(volume * .5);

  @override
  Future<bool> playCue(TideCue cue, double volume) async {
    final generation = _cueGeneration;
    await initialize();
    if (_disposed || generation != _cueGeneration || volume <= 0) return false;
    final index = _busy.indexOf(false);
    if (index < 0) return false;
    _busy[index] = true;
    _requestedVoiceVolumes[index] = volume;
    final epoch = ++_voiceEpoch[index];
    try {
      await _rebalanceVoices();
      if (_disposed ||
          generation != _cueGeneration ||
          epoch != _voiceEpoch[index]) {
        return false;
      }
      await _voices[index].setSource(AssetSource('audio/${cue.name}.m4a'));
      if (_disposed ||
          generation != _cueGeneration ||
          epoch != _voiceEpoch[index]) {
        return false;
      }
      await _voices[index].resume();
      return true;
    } catch (_) {
      if (epoch == _voiceEpoch[index]) _busy[index] = false;
      rethrow;
    }
  }

  @override
  Future<void> stopCues() async {
    _cueGeneration++;
    for (var i = 0; i < _voices.length; i++) {
      _voiceEpoch[i]++;
      _busy[i] = false;
    }
    await Future.wait(_voices.map((player) => player.stop()));
  }

  @override
  Future<void> setSfxVolume(double volume) async {
    for (var i = 0; i < _requestedVoiceVolumes.length; i++) {
      _requestedVoiceVolumes[i] = volume;
    }
    await _rebalanceVoices();
  }

  Future<void> _rebalanceVoices() {
    final operation = _mixTail.then((_) async {
      if (_disposed) return;
      final active = _busy.where((busy) => busy).length.clamp(1, maxVoices);
      // Bound the worst-case coherent sum, not only each individual file.
      // Max SFX amplitude <= .9 * .568; music <= .5 * .399. Combined < .712.
      await Future.wait([
        for (var i = 0; i < _voices.length; i++)
          if (_busy[i])
            _voices[i].setVolume(_requestedVoiceVolumes[i] * .9 / active),
      ]);
    });
    _mixTail = operation.catchError((Object _) {});
    return operation;
  }

  @override
  Future<void> dispose() async {
    if (_disposed) return;
    _disposed = true;
    _musicEpoch++;
    try {
      await _initializing;
    } catch (_) {
      // Initialization can fail after allocating part of the voice pool.
      // Every allocated player still needs a best-effort native disposal.
    }
    for (final subscription in _completions) {
      await subscription.cancel();
    }
    await _mixTail;
    final players = [..._voices, ?_music];
    await Future.wait(
      players.map((player) async {
        try {
          await player.dispose();
        } catch (_) {
          // A failed native creation may also reject disposal. Continue cleaning
          // up other players instead of leaking the rest of the pool.
        }
      }),
    );
  }
}

/// Lifecycle and preference policy, independently testable from native codecs.
/// Call playCue only for an accepted, visible foreground action. Never derive
/// sounds from income deltas, replayed events, imported saves or a timer tick.
class TideAudioBus extends ChangeNotifier with WidgetsBindingObserver {
  TideAudioBus({
    required TideAudioDriver driver,
    required AudioPreferenceStore store,
    DateTime Function()? clock,
    bool observeLifecycle = true,
  }) : _driver = driver,
       _store = store,
       _clock = clock ?? DateTime.now,
       _observeLifecycle = observeLifecycle {
    if (observeLifecycle) WidgetsBinding.instance.addObserver(this);
  }

  final TideAudioDriver _driver;
  final AudioPreferenceStore _store;
  final DateTime Function() _clock;
  final bool _observeLifecycle;
  AudioPreferences preferences = const AudioPreferences();
  String? warning;
  bool _foreground = true, _closed = false;
  int _epoch = 0;
  TideMusic? _track;
  Future<void>? _initializing;
  final Map<TideCue, DateTime> _lastCue = {};
  Future<void> _preferenceTail = Future<void>.value();

  bool get foreground => _foreground;
  TideMusic? get music => _track;

  Future<void> initialize() => _initializing ??= _initialize();
  Future<void> _initialize() async {
    try {
      preferences = await _store.load() ?? const AudioPreferences();
    } catch (_) {
      // Respect uncertainty about a saved mute choice: fail quietly.
      preferences = const AudioPreferences(muted: true);
      warning = UiEnglish.audioSoundSettingsCouldNotBeReadSound;
    }
    try {
      await _driver.initialize();
    } catch (_) {
      warning = UiEnglish.audioSoundIsTemporarilyUnavailableYourHarborContinues;
    }
    if (!_closed) notifyListeners();
  }

  Future<void> setPreferences(AudioPreferences next) async {
    next = AudioPreferences.fromJson(next.toJson());
    await initialize();
    if (_closed) return;
    preferences = next;
    _epoch++;
    notifyListeners();
    final persisted = _preferenceTail.then((_) => _store.save(next));
    _preferenceTail = persisted.catchError((Object _) {});
    // Apply mute before waiting for storage; a slow disk never delays silence.
    await _safe(() async {
      await _driver.setSfxVolume(preferences.effectiveSfx);
      if (preferences.effectiveSfx == 0) await _driver.stopCues();
      if (!_foreground || preferences.effectiveMusic == 0) {
        await _driver.stopMusic();
      } else {
        await _driver.setMusicVolume(preferences.effectiveMusic);
        if (_track != null) {
          await _driver.playMusic(_track!, preferences.effectiveMusic);
        }
      }
    });
    try {
      await persisted;
    } catch (_) {
      warning = UiEnglish.audioSoundSettingsChangedForThisSessionBut;
      if (!_closed) notifyListeners();
    }
  }

  Future<void> startMusic([TideMusic track = TideMusic.harbor]) async {
    final epoch = _epoch;
    await initialize();
    if (_closed || epoch != _epoch) return;
    _track = track;
    if (_foreground && preferences.effectiveMusic > 0) {
      await _safe(() => _driver.playMusic(track, preferences.effectiveMusic));
    }
  }

  Future<bool> playCue(
    TideCue cue, {
    DateTime? occurredAt,
    bool offline = false,
  }) async {
    final epoch = _epoch;
    final created = occurredAt ?? _clock();
    if (offline || !_foreground || _closed) return false;
    await initialize();
    final age = _clock().difference(created);
    if (_closed ||
        !_foreground ||
        epoch != _epoch ||
        preferences.effectiveSfx <= 0 ||
        age.isNegative ||
        age > const Duration(milliseconds: 750)) {
      return false;
    }
    final previous = _lastCue[cue];
    if (previous != null &&
        _clock().difference(previous) < const Duration(milliseconds: 100)) {
      return false;
    }
    _lastCue[cue] = _clock();
    var played = false;
    await _safe(() async {
      played = await _driver.playCue(cue, preferences.effectiveSfx);
    });
    return played;
  }

  Future<void> setForeground(bool value) async {
    if (_closed || value == _foreground) return;
    _foreground = value;
    _epoch++;
    _lastCue.clear();
    final epoch = _epoch;
    await initialize();
    if (_closed || epoch != _epoch) return;
    await _safe(() async {
      await _driver.stopCues();
      await _driver.stopMusic();
      if (_foreground && _track != null && preferences.effectiveMusic > 0) {
        await _driver.playMusic(_track!, preferences.effectiveMusic);
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    unawaited(setForeground(state == AppLifecycleState.resumed));
  }

  Future<void> _safe(Future<void> Function() operation) async {
    try {
      await operation();
    } catch (_) {
      warning =
          UiEnglish.audioSoundIsTemporarilyUnavailableYourHarborContinues2;
      if (!_closed) notifyListeners();
    }
  }

  /// Await in shutdown tests. The ordinary widget dispose also invokes it.
  Future<void> close() async {
    if (_closed) return;
    _closed = true;
    _epoch++;
    if (_observeLifecycle) WidgetsBinding.instance.removeObserver(this);
    await _preferenceTail;
    await _safe(_driver.dispose);
  }

  @override
  void dispose() {
    unawaited(close());
    super.dispose();
  }
}
