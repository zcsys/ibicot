import 'dart:async';
import 'dart:io';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'game_controller.dart';
import 'native_services.dart';

/// Observes explicit consent and current-session transitions only. It never
/// writes gameplay, reconstructs pre-consent history, or reports balances,
/// recovery codes, text, file paths, or device identifiers. The bounded queue
/// is memory-only; process termination can therefore leave an unknown outcome.
class GameTelemetry {
  GameTelemetry({
    required this.game,
    required this.services,
    String? platform,
    String build = const String.fromEnvironment(
      'TIDEGLASS_MEASUREMENT_BUILD',
      defaultValue: 'development',
    ),
    String deviceClass = 'unclassified',
    DateTime Function()? clock,
    this.flushInterval = const Duration(minutes: 1),
  }) : buffer = services.client == null
           ? null
           : ConsentTelemetryBuffer(
               services.client!,
               platform:
                   platform ??
                   (Platform.isIOS
                       ? 'ios'
                       : Platform.isAndroid
                       ? 'android'
                       : Platform.isMacOS
                       ? 'macos'
                       : 'test'),
               build: build,
               deviceClass: deviceClass,
               clock: clock,
             ) {
    game.addListener(_gameChanged);
    services.addListener(_consentChanged);
    _consentChanged();
  }
  final GameController game;
  final NativeServicesManager services;
  final ConsentTelemetryBuffer? buffer;
  final Duration flushInterval;
  final Stopwatch _sessionTime = Stopwatch();
  Timer? _timer;
  String? _sessionId;
  int? _generation, _revision;
  int _recharts = 0;
  Set<String> _chapters = {}, _dossiers = {}, _contracts = {};
  bool _foreground = true, _closed = false;
  bool _wasSaving = false, _saveFailed = false, _reportedSave = false;
  int get pendingEventCount => buffer?.pendingEventCount ?? 0;
  int get droppedEventCount => buffer?.droppedEventCount ?? 0;

  void _baseline() {
    _recharts = game.state.rechartCount;
    _chapters = {...game.story.campaign.completed};
    _dossiers = {...game.story.dossiers.completed};
    _contracts = game.state.dailyContracts
        .where((c) => c.claimed)
        .map((c) => c.id)
        .toSet();
    _wasSaving = game.saving;
    _saveFailed = game.saveError != null;
    _reportedSave = false;
  }

  void _syncConsent() {
    if (_closed || buffer == null) return;
    final revision = services.telemetryConsentRevision;
    final generation = services.client!.sessionGeneration;
    if (_generation != generation || _revision != revision) {
      _sessionId = null;
      _sessionTime
        ..stop()
        ..reset();
      _timer?.cancel();
      _generation = generation;
      _revision = revision;
    }
    buffer!.useConfirmedConsent(revision);
    if (!buffer!.enabled) {
      _sessionId = null;
      _timer?.cancel();
      return;
    }
    if (_foreground && _sessionId == null) {
      _baseline();
      _sessionId = buffer!.newSessionId();
      _sessionTime
        ..reset()
        ..start();
      _record('session_start', {
        'flow': 'consented_foreground',
        'schema_version': stateSchemaVersion,
      });
      _timer?.cancel();
      _timer = Timer.periodic(flushInterval, (_) => unawaited(flush()));
    }
  }

  void _consentChanged() {
    _syncConsent();
    if (_foreground && _sessionId != null) unawaited(flush());
  }

  void _record(String name, Map<String, dynamic> properties) {
    if (_sessionId == null || buffer?.enabled != true) return;
    buffer!.record(name, sessionId: _sessionId!, properties: properties);
  }

  void _gameChanged() {
    _syncConsent();
    if (_closed || _sessionId == null || game.replaying) return;
    if (game.state.rechartCount > _recharts) {
      _record('rechart', {
        'flow': 'simulation_progress',
        'outcome': 'observed',
      });
    }
    for (final id in game.story.campaign.completed.difference(_chapters)) {
      _record('chapter_complete', {
        'chapter': int.parse(id.split('.').last),
        'outcome': 'observed',
      });
    }
    for (final id in game.story.dossiers.completed.difference(_dossiers)) {
      _record('dossier_complete', {'flow': id, 'outcome': 'observed'});
    }
    final claimed = game.state.dailyContracts
        .where((c) => c.claimed)
        .map((c) => c.id)
        .toSet();
    if (claimed.difference(_contracts).isNotEmpty) {
      _record('contract_claim', {'outcome': 'observed'});
    }
    final failed = game.saveError != null;
    if (game.hasPersistence && failed && !_saveFailed) {
      _record('save_result', {'outcome': 'failed'});
    } else if (game.hasPersistence &&
        _wasSaving &&
        !game.saving &&
        !failed &&
        !_reportedSave) {
      _record('save_result', {'outcome': 'saved'});
      _reportedSave = true;
    }
    _saveFailed = failed;
    _wasSaving = game.saving;
    _recharts = game.state.rechartCount;
    _chapters = {...game.story.campaign.completed};
    _dossiers = {...game.story.dossiers.completed};
    _contracts = claimed;
  }

  Future<void> returned() async {
    if (_closed) return;
    _foreground = true;
    _syncConsent();
    try {
      await services.refreshTelemetryConsent();
    } catch (_) {
      // A service outage never blocks the foreground or restores old consent.
    }
    if (_closed || !_foreground) return;
    _syncConsent();
    await flush();
  }

  Future<void> backgrounded() async {
    if (_closed || !_foreground) return;
    _syncConsent();
    _record('session_end', {
      'flow': 'background',
      'duration_seconds': _sessionTime.elapsed.inSeconds.clamp(0, 864000),
    });
    _foreground = false;
    _sessionTime.stop();
    _sessionId = null;
    _timer?.cancel();
    await flush();
  }

  void resumeFinished(Duration duration, {required bool succeeded}) {
    _syncConsent();
    if (!_foreground || _closed) return;
    _record('resume_result', {
      'outcome': succeeded ? 'settled' : 'failed',
      'duration_seconds': duration.inSeconds.clamp(0, 864000),
    });
    unawaited(flush());
  }

  Future<void> flush() async {
    if (_closed || buffer == null) return;
    _syncConsent();
    try {
      await buffer!.flush();
    } catch (_) {
      // IDs stay queued for a bounded retry. Unknown outcomes are not success.
    }
  }

  /// Disposal is not evidence of a clean native process exit. No fabricated
  /// end/crash event is generated when a controller is replaced or killed.
  void dispose() {
    if (_closed) return;
    _closed = true;
    _timer?.cancel();
    game.removeListener(_gameChanged);
    services.removeListener(_consentChanged);
    buffer?.useConfirmedConsent(null);
  }
}
