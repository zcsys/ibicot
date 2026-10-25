import 'tideglass_core.dart';

/// A bounded counterfactual, never a command or a universal reset policy.
/// Both paths buy the best marginal-output/cost unit repeatedly at t=0 and
/// each minute, stopping when that unit is unaffordable. No later Rechart or
/// bonus activation occurs. Existing bonus queues expire through real advance.
/// The objective is ADDITIONAL lifetime production, not terminal wallet wealth.
enum RechartForecastStatus {
  estimated,
  notEligible,
  unsupportedRules,
  pendingSettlement,
  inputLimit,
  workLimit,
}

class RechartForecast {
  const RechartForecast({
    required this.status,
    required this.horizonSeconds,
    required this.samples,
    required this.work,
    this.firstCatchUpSeconds,
    this.breakEvenSeconds,
    this.rebuildSeconds,
    this.keepGainMicros,
    this.resetGainMicros,
    this.nextChartTarget,
    this.nextChartLifetimeMicros,
    this.unlockedChartThresholds = const [],
  });

  final RechartForecastStatus status;
  final int horizonSeconds, samples, work;

  /// First positive minute with reset cumulative production >= keep.
  final int? firstCatchUpSeconds;

  /// First sampled catch-up after the last sampled deficit, only if reset is
  /// still caught up at the horizon. Earlier crossings may reverse. This does
  /// not assert dominance between samples or beyond the horizon.
  final int? breakEvenSeconds;

  /// First sampled reset fleet whose unboosted output reaches the input rate.
  /// Production is earned throughout reconstruction, never set to zero.
  final int? rebuildSeconds;
  final BigInt? keepGainMicros, resetGainMicros;
  final BigInt? nextChartTarget, nextChartLifetimeMicros;
  final List<int> unlockedChartThresholds;

  Map<String, dynamic> toJson() => {
    'status': status.name,
    'policy': 'minute-best-payback-single-reset-v1',
    'horizon_seconds': horizonSeconds,
    'sample_seconds': 60,
    'samples': samples,
    'work': work,
    'first_catch_up_seconds': firstCatchUpSeconds,
    'break_even_seconds': breakEvenSeconds,
    'rebuild_seconds': rebuildSeconds,
    'keep_gain_micros': keepGainMicros?.toString(),
    'reset_gain_micros': resetGainMicros?.toString(),
    'next_chart_target': nextChartTarget?.toString(),
    'next_chart_lifetime_micros': nextChartLifetimeMicros?.toString(),
    'unlocked_chart_thresholds': unlockedChartThresholds,
  };
}

/// Cost is bounded by a 24h horizon, a 1-minute grid, input precision limits and
/// a shared work budget. Native callers additionally run this in a killable
/// isolate; a slow device may show unavailable instead of blocking rendering.
RechartForecast estimateRechart(
  GameState snapshot, {
  int horizonSeconds = 86400,
  int maximumWork = 20000,
}) {
  if (horizonSeconds < 60 ||
      horizonSeconds > 86400 ||
      horizonSeconds % 60 != 0 ||
      maximumWork < 1 ||
      maximumWork > 50000) {
    throw ArgumentError('Use a whole-minute horizon <=24h and bounded work.');
  }
  var work = 0;
  RechartForecast unavailable(RechartForecastStatus status) => RechartForecast(
    status: status,
    horizonSeconds: horizonSeconds,
    samples: 0,
    work: work,
  );
  if (snapshot.rulesVersion != economyVersion) {
    return unavailable(RechartForecastStatus.unsupportedRules);
  }
  if (snapshot.support.activeSettlementId != null) {
    return unavailable(RechartForecastStatus.pendingSettlement);
  }
  if (snapshot.counts.any((count) => count > 10000) ||
      [
        snapshot.walletMicros,
        snapshot.lifetimeMicros,
        snapshot.charts,
        snapshot.focusRemainingMicros,
        snapshot.supportRemainingMicros,
        snapshot.elapsedMicros,
      ].any((value) => value.bitLength > 4096)) {
    return unavailable(RechartForecastStatus.inputLimit);
  }
  const engine = TideglassEngine();
  final award = engine.prestigeAward(snapshot);
  if (award == BigInt.zero) {
    return unavailable(RechartForecastStatus.notEligible);
  }
  final afterCharts = snapshot.charts + award;
  final nextTarget =
      [
        10,
        25,
        100,
      ].map(BigInt.from).where((target) => target > afterCharts).firstOrNull ??
      afterCharts + BigInt.one;
  final unlocked = [10, 25, 100]
      .where(
        (target) =>
            snapshot.charts < BigInt.from(target) &&
            afterCharts >= BigInt.from(target),
      )
      .toList(growable: false);

  // A projection contains economic/timer inputs only. No account calendar,
  // receipts, claims, paid state or user automation plan is copied or written.
  // Explicit manual decisions below work even before the 10-Chart autobuyer.
  GameState project(GameState state) => GameState(
    counts: state.counts,
    walletMicros: state.walletMicros,
    lifetimeMicros: state.lifetimeMicros,
    charts: state.charts,
    earningRemainder: state.earningRemainder,
    elapsedMicros: state.elapsedMicros,
    focusCharges: state.focusCharges,
    focusPhaseMicros: state.focusPhaseMicros,
    focusRemainingMicros: state.focusRemainingMicros,
    completedSurveys: state.completedSurveys,
    surveyPhaseMicros: state.surveyPhaseMicros,
    support: SupportState(remainingMicros: state.supportRemainingMicros),
  );
  void spendWork() {
    work++;
    if (work > maximumWork) throw const _ForecastWorkLimit();
  }

  GameState buyAtDecision(GameState state) {
    while (true) {
      spendWork();
      final tier = engine.chooseAutoBuyTier(state);
      if (engine.priceMicros(tier, state.counts[tier]) > state.walletMicros) {
        return state;
      }
      final result = engine.buy(state, tier, 1);
      if (!result.accepted) throw StateError('Forecast purchase rejected.');
      state = result.state;
    }
  }

  GameState minute(GameState state) {
    spendWork();
    final advanced = engine.advance(
      state,
      const Duration(minutes: 1),
      autoBuy: false,
      maximumEvents: 32,
    );
    if (!advanced.accepted) throw StateError('Forecast interval rejected.');
    return buyAtDecision(advanced.state);
  }

  try {
    var keep = project(snapshot);
    final reset = engine.rechart(keep);
    if (!reset.accepted) throw StateError('Forecast Rechart rejected.');
    var rebuild = reset.state;
    final initialRate = engine.outputPerSecond(keep).raw;
    keep = buyAtDecision(keep);
    rebuild = buyAtDecision(rebuild);
    int? firstCatchUp, rebuildSeconds;
    var lastBehindSeconds = 0;
    if (engine.outputPerSecond(rebuild).raw >= initialRate) rebuildSeconds = 0;
    var lastAhead = false;
    for (var seconds = 60; seconds <= horizonSeconds; seconds += 60) {
      keep = minute(keep);
      rebuild = minute(rebuild);
      if (rebuildSeconds == null &&
          engine.outputPerSecond(rebuild).raw >= initialRate) {
        rebuildSeconds = seconds;
      }
      final keepGain = keep.lifetimeMicros - snapshot.lifetimeMicros;
      final resetGain = rebuild.lifetimeMicros - snapshot.lifetimeMicros;
      lastAhead = resetGain > BigInt.zero && resetGain >= keepGain;
      if (lastAhead) {
        firstCatchUp ??= seconds;
      } else {
        lastBehindSeconds = seconds;
      }
    }
    return RechartForecast(
      status: RechartForecastStatus.estimated,
      horizonSeconds: horizonSeconds,
      samples: horizonSeconds ~/ 60,
      work: work,
      firstCatchUpSeconds: firstCatchUp,
      breakEvenSeconds: lastAhead ? lastBehindSeconds + 60 : null,
      rebuildSeconds: rebuildSeconds,
      keepGainMicros: keep.lifetimeMicros - snapshot.lifetimeMicros,
      resetGainMicros: rebuild.lifetimeMicros - snapshot.lifetimeMicros,
      nextChartTarget: nextTarget,
      nextChartLifetimeMicros: engine.lifetimeForCharts(nextTarget),
      unlockedChartThresholds: List.unmodifiable(unlocked),
    );
  } on _ForecastWorkLimit {
    // Partial trajectories must never be presented as a complete estimate.
    return unavailable(RechartForecastStatus.workLimit);
  }
}

class _ForecastWorkLimit implements Exception {
  const _ForecastWorkLimit();
}
