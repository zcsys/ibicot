import 'dart:convert';

import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';

// Executed in the staged host copy. Production mobile owns this pure worker.
import '../../mobile/lib/rechart_forecast_task.dart';

void main() {
  test('actual isolated projection matches synchronous engine and leaves source intact', () async {
    const engine = TideglassEngine();
    final state = GameState(
      counts: [100, 75, 50, 25, 10],
      walletMicros: BigInt.from(1000000000000),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(10)),
    );
    final before = jsonEncode(state.toJson());
    final task = RechartForecastTask(state);
    final result = await task.result;
    expect(result?.toJson(), estimateRechart(state).toJson());
    expect(jsonEncode(state.toJson()), before);
    task.cancel(); // Completion cleanup is idempotent.
  });
  test(
    'cancel and expired deadline resolve without a dangling worker',
    () async {
      final cancelled = RechartForecastTask(GameState.initial());
      cancelled.cancel();
      cancelled.cancel();
      expect(await cancelled.result, isNull);
      final expired = RechartForecastTask(
        GameState.initial(),
        timeout: Duration.zero,
      );
      expect(await expired.result, isNull);
      await Future<void>.delayed(const Duration(milliseconds: 30));
      expired.cancel();
    },
  );
}
