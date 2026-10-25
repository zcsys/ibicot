import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:tideglass_platform/signed_entitlements.dart';

/// Device-local elapsed-time evidence. No sample or epoch leaves this device.
/// Android survives process exit in the same boot; Apple deliberately does not.
class OwnershipClockBridge extends ChangeNotifier with WidgetsBindingObserver {
  OwnershipClockBridge({
    MethodChannel channel = const MethodChannel(
      'dev.tideglass/ownership_clock',
    ),
    bool autoRefresh = true,
    this.refreshInterval = const Duration(seconds: 10),
    this.sampleValidity = const Duration(seconds: 30),
    this.requestTimeout = const Duration(seconds: 3),
    DateTime Function()? wallClock,
    int Function()? elapsedMicroseconds,
  }) : _channel = channel,
       _wallClock = wallClock ?? DateTime.now,
       _elapsedMicroseconds = elapsedMicroseconds {
    _stopwatch.start();
    WidgetsBinding.instance.addObserver(this);
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'invalidate') invalidate();
    });
    if (autoRefresh) {
      _timer = Timer.periodic(refreshInterval, (_) {
        if (_foreground && !_pending) unawaited(refresh());
      });
    }
  }

  final MethodChannel _channel;
  final Duration refreshInterval, sampleValidity, requestTimeout;
  final DateTime Function() _wallClock;
  final int Function()? _elapsedMicroseconds;
  final Stopwatch _stopwatch = Stopwatch();
  Timer? _timer;
  TrustedDeviceTime? _sample;
  DateTime? _receivedWall;
  int _receivedElapsed = 0, _generation = 0;
  bool _disposed = false, _foreground = true, _pending = false;
  bool _restartContinuity = false;
  int get _elapsed =>
      _elapsedMicroseconds?.call() ?? _stopwatch.elapsedMicroseconds;

  /// False on Apple: native process epochs never promise restart continuity.
  bool get restartContinuity => current != null && _restartContinuity;

  /// A short-lived conservative bound. A stale/missing sample hides grants;
  /// callers refresh before loading, accepting, or resuming cached ownership.
  TrustedDeviceTime? get current {
    if (_disposed || !_foreground || _sample == null) return null;
    final projected = _elapsed - _receivedElapsed;
    final wall = _wallClock().difference(_receivedWall!).inMicroseconds;
    if (projected < 0 ||
        wall < 0 ||
        projected > sampleValidity.inMicroseconds ||
        wall > sampleValidity.inMicroseconds ||
        (projected - wall).abs() > 250000) {
      return null;
    }
    return TrustedDeviceTime(
      bootId: _sample!.bootId,
      elapsedMicroseconds: _sample!.elapsedMicroseconds + projected,
      uncertaintyMicroseconds: _sample!.uncertaintyMicroseconds,
    );
  }

  Future<bool> refresh() async {
    if (_disposed || !_foreground) return false;
    final generation = ++_generation, began = _elapsed;
    _pending = true;
    try {
      final raw = await _channel
          .invokeMapMethod<String, dynamic>('sample')
          .timeout(requestTimeout);
      if (_disposed || generation != _generation || !_foreground) return false;
      final ended = _elapsed;
      if (raw == null ||
          raw['version'] != 1 ||
          raw['elapsed_us'] is! int ||
          raw['elapsed_us'] < 0 ||
          raw['epoch_id'] is! String ||
          !RegExp(
            r'^[A-Za-z0-9_.-]{8,160}$',
          ).hasMatch(raw['epoch_id'] as String) ||
          !{'boot', 'process'}.contains(raw['continuity_scope']) ||
          ended < began ||
          ended - began > requestTimeout.inMicroseconds) {
        invalidate();
        return false;
      }
      // The native sample occurs between request and response. Its value at
      // receipt is in [sample, sample + round-trip]. Upper-bound elapsed usage
      // in the lease cache prevents a slow channel from extending a grant.
      _sample = TrustedDeviceTime(
        bootId: raw['epoch_id'] as String,
        elapsedMicroseconds: raw['elapsed_us'] as int,
        uncertaintyMicroseconds: ended - began + 1,
      );
      _receivedElapsed = ended;
      _receivedWall = _wallClock();
      _restartContinuity = raw['continuity_scope'] == 'boot';
      notifyListeners();
      return true;
    } catch (_) {
      if (!_disposed && generation == _generation) invalidate();
      return false;
    } finally {
      if (generation == _generation) _pending = false;
    }
  }

  /// Invalidates pending replies as well as the current projection.
  void invalidate() {
    if (_disposed) return;
    ++_generation;
    _pending = false;
    _sample = null;
    _restartContinuity = false;
    notifyListeners();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _foreground = state == AppLifecycleState.resumed;
    invalidate();
  }

  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    ++_generation;
    _timer?.cancel();
    _channel.setMethodCallHandler(null);
    WidgetsBinding.instance.removeObserver(this);
    _stopwatch.stop();
    super.dispose();
  }
}
