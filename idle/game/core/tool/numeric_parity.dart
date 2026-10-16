import 'dart:convert';
import 'dart:io';
import 'package:tideglass_core/tideglass_core.dart';

void main(List<String> args) {
  const engine = TideglassEngine();
  final watch = Stopwatch()..start();
  final rows = <Object>[];
  for (final count in [1, 10, 24, 25, 49, 50, 75, 100, 250, 600, 1200, 5000]) {
    for (final charts in [
      BigInt.zero,
      BigInt.from(10),
      BigInt.from(25),
      BigInt.from(100),
      BigInt.one << 256
    ]) {
      final state = GameState(
          counts: [count, count + 1, count + 2, count + 3, count + 4],
          charts: charts,
          lifetimeMicros: engine.lifetimeForCharts(charts));
      rows.add({
        'count': count,
        'charts': charts.toString(),
        'rate': engine.outputPerSecond(state).raw.toString(),
        'prestige': engine.prestigeMultiplier(charts).raw.toString(),
        'prices': [
          for (var tier = 0; tier < 5; tier++)
            engine.bulkPriceMicros(tier, count, 17).toString()
        ],
        'marginals': [
          for (var tier = 0; tier < 5; tier++)
            engine.marginalOutputPerSecond(state, tier).raw.toString()
        ],
      });
    }
  }
  final epoch = DateTime.utc(2026, 10, 16);
  for (final offline in [false, true]) {
    var state = GameState(
        counts: [100, 85, 70, 55, 40],
        charts: BigInt.from(250),
        walletMicros: BigInt.from(1000000000),
        lifetimeMicros: engine.lifetimeForCharts(BigInt.from(250)),
        autoBuyEnabled: true);
    state = engine
        .refreshContracts(state, epoch,
            accountSeed: 'numeric-parity', utcOffsetMinutes: 0)
        .state;
    final result =
        engine.advance(state, const Duration(hours: 26), offline: offline);
    rows.add({
      'offline': offline,
      'state': result.state.toJson(),
      'events': result.events.map((event) => event.toJson()).toList()
    });
  }
  File(args.single).writeAsStringSync(jsonEncode(rows));
  stdout.writeln(
      '62 numeric/timeline fixtures in ${watch.elapsedMilliseconds}ms');
}
