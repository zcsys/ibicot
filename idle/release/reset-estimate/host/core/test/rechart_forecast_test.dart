import 'dart:convert';

import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';

const engine = TideglassEngine();
GameState fixture({int charts = 0, int? entitlement, BigInt? wallet}) =>
    GameState(
      counts: [100, 75, 50, 25, 10],
      charts: BigInt.from(charts),
      lifetimeMicros: engine.lifetimeForCharts(
        BigInt.from(entitlement ?? (charts == 0 ? 10 : charts + 10)),
      ),
      walletMicros: wallet ?? BigInt.from(1000000000000),
    );

// A separate fine-step oracle retains the entire account state and uses one
// second advances, rather than the estimator's reduced projection/minute step.
Map<String, Object?> oracle(GameState original, int horizon) {
  GameState prepared(GameState s) => s.copyWith(
    autoBuyEnabled: false,
    automationPlans: [AutomationPlan.base()],
    selectedAutomationPlanId: 'plan.base',
  );
  GameState buy(GameState s) {
    for (var i = 0; i < 10000; i++) {
      final tier = engine.chooseAutoBuyTier(s);
      final attempt = engine.buy(s, tier, 1);
      if (!attempt.accepted) return s;
      s = attempt.state;
    }
    throw StateError('Oracle purchase limit');
  }

  var keep = prepared(original),
      reset = engine.rechart(prepared(original)).state;
  final oldRate = engine.outputPerSecond(original).raw;
  keep = buy(keep);
  reset = buy(reset);
  int? first, rebuild = engine.outputPerSecond(reset).raw >= oldRate ? 0 : null;
  var lastBehind = 0, ahead = false;
  for (var second = 1; second <= horizon; second++) {
    keep = engine
        .advance(keep, const Duration(seconds: 1), autoBuy: false)
        .state;
    reset = engine
        .advance(reset, const Duration(seconds: 1), autoBuy: false)
        .state;
    if (second % 60 != 0) continue;
    keep = buy(keep);
    reset = buy(reset);
    if (rebuild == null && engine.outputPerSecond(reset).raw >= oldRate)
      rebuild = second;
    ahead =
        reset.lifetimeMicros > original.lifetimeMicros &&
        reset.lifetimeMicros >= keep.lifetimeMicros;
    if (ahead) {
      first ??= second;
    } else {
      lastBehind = second;
    }
  }
  return {
    'keep': keep.lifetimeMicros - original.lifetimeMicros,
    'reset': reset.lifetimeMicros - original.lifetimeMicros,
    'first': first,
    'break': ahead ? lastBehind + 60 : null,
    'rebuild': rebuild,
    'keep_charts': keep.charts,
    'reset_charts': reset.charts,
  };
}

void main() {
  test('first minute has analytic exact production and boost expiries', () {
    final s = GameState(
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(10)),
      focusRemainingMicros: BigInt.from(30000000),
      support: SupportState(remainingMicros: BigInt.from(45000000)),
    );
    final r = estimateRechart(s, horizonSeconds: 60);
    // 60 + .20*30 + .25*45 = 77.25; first Rechart has 2x power.
    expect(r.keepGainMicros, BigInt.from(77250000));
    expect(r.resetGainMicros, BigInt.from(154500000));
    expect(r.breakEvenSeconds, 60);
    expect(r.rebuildSeconds, 0);
  });

  test(
    'fine-step oracle agrees with full account state, boosts and remainder',
    () {
      var s = fixture(charts: 100, entitlement: 135).copyWith(
        earningRemainder: Fixed.scale * BigInt.from(399),
        focusCharges: 4,
        focusPhaseMicros: BigInt.from(7199000000),
        focusRemainingMicros: BigInt.from(33000000),
        support: SupportState(remainingMicros: BigInt.from(85000000)),
        automationPlans: [
          AutomationPlan(
            id: 'plan.base',
            name: 'My reset policy',
            purchasePolicy: 'priority',
            autoResetEnabled: true,
            minimumRunSeconds: 1,
          ),
        ],
        autoBuyEnabled: true,
      );
      s = engine
          .refreshContracts(
            s,
            DateTime.utc(2026, 10, 21, 23, 59),
            accountSeed: 'forecast-fixture',
          )
          .state;
      final before = jsonEncode(s.toJson());
      final expected = oracle(s, 3600),
          r = estimateRechart(s, horizonSeconds: 3600);
      expect(r.keepGainMicros, expected['keep']);
      expect(r.resetGainMicros, expected['reset']);
      expect(r.firstCatchUpSeconds, expected['first']);
      expect(r.breakEvenSeconds, expected['break']);
      expect(r.rebuildSeconds, expected['rebuild']);
      expect(expected['keep_charts'], BigInt.from(100));
      expect(expected['reset_charts'], BigInt.from(135));
      expect(jsonEncode(s.toJson()), before);
    },
  );

  test(
    'wallet loss affects keeping and rebuilding but old lifetime is not a gain',
    () {
      final poor = fixture(wallet: BigInt.zero),
          rich = fixture(wallet: BigInt.from(1000000000000000));
      final a = estimateRechart(poor, horizonSeconds: 60),
          b = estimateRechart(rich, horizonSeconds: 60);
      expect(b.keepGainMicros! > a.keepGainMicros!, isTrue);
      expect(b.resetGainMicros, a.resetGainMicros);
      expect(a.keepGainMicros! < poor.lifetimeMicros, isTrue);
      expect(b.resetGainMicros, oracle(rich, 60)['reset']);
    },
  );

  test('24h baseline fixture has reproducible exact cumulative output', () {
    final r = estimateRechart(fixture());
    expect(r.status, RechartForecastStatus.estimated);
    expect(r.samples, 1440);
    expect(r.work, 6689);
    expect(r.breakEvenSeconds, 1560);
    expect(r.rebuildSeconds, 720);
    expect(r.keepGainMicros, BigInt.parse('19394345541120000000'));
    expect(r.resetGainMicros, BigInt.parse('46589002648200000000'));
  });

  test('small late claim honestly has no catch-up in the horizon', () {
    final r = estimateRechart(fixture(charts: 10000, entitlement: 10001));
    expect(r.status, RechartForecastStatus.estimated);
    expect(r.breakEvenSeconds, isNull);
    expect(r.resetGainMicros! < r.keepGainMicros!, isTrue);
  });

  test('10,25,100 unlock thresholds and following Chart are exact', () {
    for (final row in [
      [0, 10, 10, 25],
      [10, 24, 0, 25],
      [10, 25, 25, 100],
      [25, 99, 0, 100],
      [25, 100, 100, 101],
    ]) {
      final r = estimateRechart(
        fixture(charts: row[0], entitlement: row[1]),
        horizonSeconds: 60,
      );
      expect(
        r.unlockedChartThresholds,
        row[2] == 0 ? isEmpty : contains(row[2]),
      );
      expect(r.nextChartTarget, BigInt.from(row[3]));
      expect(
        engine.prestigeEntitlement(r.nextChartLifetimeMicros!),
        BigInt.from(row[3]),
      );
      expect(
        engine.prestigeEntitlement(r.nextChartLifetimeMicros! - BigInt.one),
        lessThan(BigInt.from(row[3])),
      );
    }
  });

  test('not eligible, mismatched rules and pending replay never simulate', () {
    expect(
      estimateRechart(GameState.initial()).status,
      RechartForecastStatus.notEligible,
    );
    expect(
      estimateRechart(
        fixture().copyWith(rulesVersion: 'tideglass-economy-0.9.0'),
      ).status,
      RechartForecastStatus.unsupportedRules,
    );
    final request = OfflineSettlementRequest(
      sequence: BigInt.one,
      fromUtc: DateTime.utc(2026, 10, 21),
      throughUtc: DateTime.utc(2026, 10, 21, 0, 1),
    );
    final pending = fixture().copyWith(
      support: SupportState(
        activeSettlementId: request.identity('local'),
        activeSettlementRequest: request,
      ),
    );
    // Use the canonical account seed, not an invented receipt identity.
    final aligned = pending.copyWith(
      support: pending.support.copyWith(
        activeSettlementId: request.identity(pending.daily.accountSeed),
      ),
    );
    expect(
      estimateRechart(aligned).status,
      RechartForecastStatus.pendingSettlement,
    );
  });

  test('work and input limits never expose partial positive advice', () {
    final r = estimateRechart(fixture(), maximumWork: 1);
    expect(r.status, RechartForecastStatus.workLimit);
    expect(r.samples, 0);
    expect(r.keepGainMicros, isNull);
    expect(r.breakEvenSeconds, isNull);
    expect(
      estimateRechart(fixture().copyWith(counts: [10001, 0, 0, 0, 0])).status,
      RechartForecastStatus.inputLimit,
    );
    expect(
      estimateRechart(GameState(lifetimeMicros: BigInt.one << 4097)).status,
      RechartForecastStatus.inputLimit,
    );
    for (final horizon in [0, 59, 61, 86460]) {
      expect(
        () => estimateRechart(fixture(), horizonSeconds: horizon),
        throwsArgumentError,
      );
    }
  });
}
