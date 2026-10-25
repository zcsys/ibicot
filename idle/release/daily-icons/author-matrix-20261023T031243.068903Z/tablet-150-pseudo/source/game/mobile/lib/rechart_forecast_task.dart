import 'dart:async';
import 'dart:isolate';

import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';

/// One preview owns one worker. Closing it or reaching the deadline kills the
/// worker; timing out a Future alone would leave expensive work running.
class RechartForecastTask {
  RechartForecastTask(
    GameState snapshot, {
    Duration timeout = const Duration(seconds: 3),
  }) {
    _port.listen((message) {
      _finish(message is RechartForecast ? message : null);
    });
    _timer = Timer(timeout, () => _finish(null));
    unawaited(
      Isolate.spawn(
            _estimate,
            [_port.sendPort, snapshot],
            onError: _port.sendPort,
            onExit: _port.sendPort,
            errorsAreFatal: true,
          )
          .then((worker) {
            if (_finished) {
              worker.kill(priority: Isolate.immediate);
            } else {
              _worker = worker;
            }
          })
          .catchError((Object _) {
            _finish(null);
          }),
    );
  }
  final _completed = Completer<RechartForecast?>();
  final _port = ReceivePort();
  Isolate? _worker;
  Timer? _timer;
  bool _finished = false;
  Future<RechartForecast?> get result => _completed.future;

  void cancel() => _finish(null);
  void _finish(RechartForecast? value) {
    if (_finished) return;
    _finished = true;
    _timer?.cancel();
    _worker?.kill(priority: Isolate.immediate);
    _port.close();
    _completed.complete(value);
  }
}

void _estimate(List<Object?> message) {
  final port = message[0] as SendPort;
  port.send(estimateRechart(message[1] as GameState));
}
