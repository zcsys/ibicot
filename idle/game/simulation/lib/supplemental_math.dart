import 'package:tideglass_core/tideglass_core.dart';

/// Experimental advice policies. These are not a shipped reset recommendation
/// or a claim of global optimality. All quantity decisions use integers.
enum ResetKind { fixedCharts, multiplierGain, forecast }

class ResetAdvice {
  const ResetAdvice(this.reset, this.reason, [this.evidence = const {}]);
  final bool reset;
  final String reason;
  final Map<String, dynamic> evidence;
  Map<String, dynamic> toJson() => {
    'reset': reset,
    'reason': reason,
    ...evidence,
  };
}

class ResetDecision {
  const ResetDecision(
    this.kind, {
    this.fixedCharts = 10,
    this.gainPercent = 20,
    this.forecastHours = 8,
  });
  final ResetKind kind;
  final int fixedCharts, gainPercent, forecastHours;
  static const engine = TideglassEngine();
  String get id => switch (kind) {
    ResetKind.fixedCharts => 'fixed-$fixedCharts-charts',
    ResetKind.multiplierGain => 'multiplier-$gainPercent-percent',
    ResetKind.forecast => 'forecast-${forecastHours}h-output-1percent-margin',
  };

  ResetAdvice evaluate(GameState state) {
    final award = engine.prestigeAward(state);
    if (award == BigInt.zero) return const ResetAdvice(false, 'no_award');
    // Common first reset keeps the tutorial/autobuy unlock comparable.
    if (state.rechartCount == 0)
      return ResetAdvice(award >= BigInt.from(10), 'shared_first_10_charts');
    if (state.elapsedMicros - state.lastRechartElapsedMicros <
        BigInt.from(600000000)) {
      return const ResetAdvice(false, 'shared_10_minute_minimum_run');
    }
    if (kind == ResetKind.fixedCharts) {
      return ResetAdvice(
        award >= BigInt.from(fixedCharts),
        'fixed_additional_charts',
        {'additional_charts': '$award'},
      );
    }
    final before = engine.prestigeMultiplier(state.charts).raw;
    final after = engine.prestigeMultiplier(state.charts + award).raw;
    if (kind == ResetKind.multiplierGain) {
      return ResetAdvice(
        after * BigInt.from(100) >= before * BigInt.from(100 + gainPercent),
        'permanent_multiplier_gain',
        {
          'before_multiplier_raw': '$before',
          'after_multiplier_raw': '$after',
          'required_gain_percent': gainPercent,
        },
      );
    }
    // Both counterfactuals start from the identical immutable state. Retained
    // boosts expire normally; no future claims/purchases of bonuses are added.
    // Production autobuy is enabled once the common first reset unlocked it.
    final rebuilt = engine.rechart(state);
    if (!rebuilt.accepted) throw StateError('Eligible rechart rejected.');
    final horizon = Duration(hours: forecastHours);
    final keep = engine.advance(state, horizon, autoBuy: true);
    final reset = engine.advance(rebuilt.state, horizon, autoBuy: true);
    if (!keep.accepted || !reset.accepted) {
      throw StateError('Counterfactual forecast exceeded its event budget.');
    }
    final keepGain = keep.state.lifetimeMicros - state.lifetimeMicros;
    final resetGain = reset.state.lifetimeMicros - state.lifetimeMicros;
    return ResetAdvice(
      resetGain * BigInt.from(100) > keepGain * BigInt.from(101),
      'fixed_horizon_new_radiance',
      {
        'horizon_hours': forecastHours,
        'retained_gain_micros': '$keepGain',
        'reset_gain_micros': '$resetGain',
        'decision_margin_percent': 1,
      },
    );
  }
}

/// An exact marginal sample of a reachable state. Source-tier externality is
/// measured by comparing target-tier output before/after that one purchase.
/// Marginals are hypotheses even when that producer is not yet affordable.
Map<String, dynamic> marginalSnapshot(
  GameState state, {
  required String label,
}) {
  const engine = TideglassEngine();
  final rows = <Map<String, dynamic>>[];
  for (var tier = 0; tier < 5; tier++) {
    final counts = state.counts.toList();
    counts[tier]++;
    final after = state.copyWith(counts: counts);
    final direct =
        engine.producerOutputPerSecond(after, tier).raw -
        engine.producerOutputPerSecond(state, tier).raw;
    final total = engine.marginalOutputPerSecond(state, tier).raw;
    final price = engine.priceMicros(tier, state.counts[tier]);
    rows.add({
      'tier': tier + 1,
      'owned': state.counts[tier],
      'unlocked': engine.isUnlocked(state, tier),
      'affordable': price <= state.walletMicros,
      'cost_micros': '$price',
      'direct_gain_raw': '$direct',
      'cross_tier_gain_raw': '${total - direct}',
      'total_gain_raw': '$total',
      'payback_seconds_ceiling': total == BigInt.zero
          ? null
          : ceilDivide(
              price * Fixed.scale,
              total * BigInt.from(1000000),
            ).toString(),
    });
  }
  final ranked = List<Map<String, dynamic>>.from(rows)
    ..sort((a, b) {
      final left =
          BigInt.parse(a['total_gain_raw']) * BigInt.parse(b['cost_micros']);
      final right =
          BigInt.parse(b['total_gain_raw']) * BigInt.parse(a['cost_micros']);
      return right.compareTo(left);
    });
  return {
    'label': label,
    'elapsed_micros': '${state.elapsedMicros}',
    'charts': '${state.charts}',
    'counts': state.counts.toList(),
    'wallet_micros': '${state.walletMicros}',
    'lifetime_micros': '${state.lifetimeMicros}',
    'output_raw': '${engine.outputPerSecond(state).raw}',
    'efficiency_ranking': ranked.map((r) => r['tier']).toList(),
    'rows': rows,
  };
}
