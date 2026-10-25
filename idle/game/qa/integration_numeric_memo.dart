// Independent QA: compare the optimized engine to the preserved pre-cache
// source. This file changes no production APIs or cache implementation.
import 'dart:convert';
import 'dart:isolate';

import '../core/lib/tideglass_core.dart' as current;
import '../../release/performance/numeric-baseline-source/tideglass_core.dart'
    as baseline;

const engine = current.TideglassEngine();
const before = baseline.TideglassEngine();
var assertions = 0;
final cases = <String>[];

void equal(Object? actual, Object? expected, String label) {
  assertions++;
  if (actual != expected) {
    throw StateError('$label: $actual != $expected');
  }
}

current.GameState state(List<int> counts, {BigInt? charts}) {
  final c = charts ?? BigInt.from(25);
  return current.GameState(
    counts: counts,
    charts: c,
    lifetimeMicros: c.pow(2) * BigInt.from(10).pow(30),
  );
}

void compareRate(current.GameState s, String label) {
  final old = baseline.GameState.fromJson(s.toJson());
  equal(engine.outputPerSecond(s).raw, before.outputPerSecond(old).raw, label);
  for (var i = 0; i < 5; i++) {
    equal(
      engine.producerOutputPerSecond(s, i).raw,
      before.producerOutputPerSecond(old, i).raw,
      '$label tier$i',
    );
  }
}

Future<void> main() async {
  final watch = Stopwatch()..start();
  // 4,200 distinct cached cumulative-price keys exceed the 2,048-entry bound.
  for (var count = 1; count <= 4200; count++) {
    final tier = count % 5;
    equal(
      engine.bulkPriceMicros(tier, 0, count),
      before.bulkPriceMicros(tier, 0, count),
      'price churn $tier/$count',
    );
  }
  for (final count in [1, 25, 100, 4096, 8191, 8192, 8193, 12000]) {
    for (var tier = 0; tier < 5; tier++) {
      final total = engine.bulkPriceMicros(tier, count, 7);
      equal(total, before.bulkPriceMicros(tier, count, 7), 'price boundary');
      var pieces = BigInt.zero;
      for (var i = 0; i < 7; i++) {
        pieces += engine.priceMicros(tier, count + i);
      }
      equal(total, pieces, 'price telescoping after churn');
    }
  }
  cases.add('price_churn_4200_keys_and_retention_boundaries');

  // Every rate-key component matters. Non-rate state must remain irrelevant
  // to the unboosted cache and remain visible to the active-output wrapper.
  final base = state([50, 40, 30, 20, 10]);
  for (var tier = 0; tier < 5; tier++) {
    final counts = base.counts.toList()..[tier] += 1;
    final changed = base.copyWith(counts: counts);
    compareRate(changed, 'rate key tier$tier');
    equal(
      engine.outputPerSecond(changed).raw != engine.outputPerSecond(base).raw,
      true,
      'tier must alter output',
    );
  }
  compareRate(state(base.counts, charts: BigInt.from(26)), 'rate key charts');
  final boosted = base.copyWith(
    focusRemainingMicros: BigInt.from(1000000),
    walletMicros: BigInt.one,
    elapsedMicros: BigInt.one,
    revision: 7,
  );
  equal(
    engine.outputPerSecond(base).raw,
    engine.outputPerSecond(boosted).raw,
    'unboosted output excludes unrelated state',
  );
  equal(
    engine.activeOutputPerSecond(boosted).raw,
    before
        .activeOutputPerSecond(baseline.GameState.fromJson(boosted.toJson()))
        .raw,
    'focus not hidden by cache',
  );
  equal(
    engine.activeOutputPerSecond(boosted).raw >
        engine.outputPerSecond(base).raw,
    true,
    'active boost remains applied',
  );
  cases.add('rate_key_completeness_and_focus_wrapper');

  // Exceed rate (512), logarithm (1,024) and Chart (128) cache capacities.
  for (var i = 0; i < 1300; i++) {
    compareRate(
      state([i + 1, 4000 - i, 30, 40, 50], charts: BigInt.from(25 + i % 137)),
      'rate/log/chart churn $i',
    );
  }
  compareRate(base, 'recomputed original after churn');
  cases.add('rate_log_chart_churn_1300_states');

  // Fresh isolates make cache-capacity identity probes independent of prior
  // test ordering. Fixed objects are immutable; identity observes reuse only.
  final chartFifo = await Isolate.run(() {
    const e = current.TideglassEngine();
    final original = e.prestigeMultiplier(BigInt.from(100000));
    final hit = identical(original, e.prestigeMultiplier(BigInt.from(100000)));
    for (var i = 0; i < 127; i++) {
      e.prestigeMultiplier(BigInt.from(i));
    }
    final stillPresent = identical(
      original,
      e.prestigeMultiplier(BigInt.from(100000)),
    );
    e.prestigeMultiplier(BigInt.from(127));
    final recomputed = e.prestigeMultiplier(BigInt.from(100000));
    return [
      hit,
      stillPresent,
      !identical(original, recomputed),
      original.raw == recomputed.raw,
    ];
  });
  equal(
    chartFifo.every((v) => v),
    true,
    '128-entry Chart FIFO, hits do not refresh',
  );
  cases.add('chart_fifo_exact_eviction_in_fresh_isolate');

  final rateFifo = await Isolate.run(() {
    const e = current.TideglassEngine();
    final s = current.GameState(counts: [100000, 0, 0, 0, 0]);
    final original = e.outputPerSecond(s);
    for (var i = 1; i <= 511; i++) {
      e.outputPerSecond(current.GameState(counts: [i, 0, 0, 0, 0]));
    }
    final hit = identical(original, e.outputPerSecond(s));
    e.outputPerSecond(current.GameState(counts: [512, 0, 0, 0, 0]));
    final recomputed = e.outputPerSecond(s);
    return [
      hit,
      !identical(original, recomputed),
      original.raw == recomputed.raw,
    ];
  });
  equal(rateFifo.every((v) => v), true, '512-entry rate FIFO');
  cases.add('rate_fifo_exact_eviction_in_fresh_isolate');

  for (final bits in [256, 4095, 4096, 4097, 8192]) {
    final charts = (BigInt.one << (bits - 1)) + BigInt.from(123);
    final a = engine.prestigeMultiplier(charts);
    final b = engine.prestigeMultiplier(charts);
    equal(
      a.raw,
      before.prestigeMultiplier(charts).raw,
      'large Chart parity $bits',
    );
    equal(identical(a, b), bits <= 4096, 'Chart retention cutoff $bits');
    final s = state([1 << 40, 1 << 39, 24, 100, 250], charts: charts);
    final first = engine.outputPerSecond(s);
    final second = engine.outputPerSecond(s);
    equal(
      identical(first, second),
      bits <= 4096,
      'rate retention cutoff $bits',
    );
    compareRate(s, 'large output $bits');
  }
  cases.add('large_charts_8192_bits_counts_2pow40_and_cache_bypass');

  final serialBefore = jsonEncode(base.toJson());
  for (var i = 0; i < 5; i++) {
    equal(
      engine.marginalOutputPerSecond(base, i, quantity: 25).raw,
      before
          .marginalOutputPerSecond(
            baseline.GameState.fromJson(base.toJson()),
            i,
            quantity: 25,
          )
          .raw,
      'marginal output',
    );
  }
  equal(jsonEncode(base.toJson()), serialBefore, 'lookups do not mutate state');
  for (final offline in [false, true]) {
    final a = engine.advance(base, const Duration(hours: 73), offline: offline);
    final b = before.advance(
      baseline.GameState.fromJson(base.toJson()),
      const Duration(hours: 73),
      offline: offline,
    );
    equal(
      jsonEncode(a.state.toJson()),
      jsonEncode(b.state.toJson()),
      'timeline state',
    );
    equal(
      jsonEncode(a.events.map((e) => e.toJson()).toList()),
      jsonEncode(b.events.map((e) => e.toJson()).toList()),
      'timeline events',
    );
  }
  cases.add('serialized_state_marginals_and_73h_online_offline');

  var errors = 0;
  for (final invoke in <void Function()>[
    () => engine.priceMicros(-1, 0),
    () => engine.priceMicros(5, 0),
    () => engine.bulkPriceMicros(0, -1, 2),
    () => engine.bulkPriceMicros(0, 1, -1),
    () => engine.prestigeMultiplier(-BigInt.one),
  ]) {
    try {
      invoke();
    } on ArgumentError {
      errors++;
    }
  }
  equal(errors, 5, 'invalid inputs reject after caches populated');
  equal(engine.bulkPriceMicros(0, 1, 0), BigInt.zero, 'zero quantity');
  compareRate(base, 'valid result after failed lookups');
  cases.add('invalid_inputs_and_zero_quantity_after_cache_population');
  print(
    jsonEncode({
      'passed': cases.length,
      'assertions': assertions,
      'cases': cases,
      'elapsed_ms': watch.elapsedMilliseconds,
      'limits': 'Host deterministic probes, not physical performance or simulation balance evidence.',
    }),
  );
}
