import 'dart:convert';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/decoration_purchase.dart';
import 'package:tideglass_simulation/policy_run.dart';
import 'package:tideglass_simulation/supplemental_math.dart';
import 'package:tideglass_simulation/supplemental_run.dart';
import 'package:tideglass_simulation/season_isolation.dart';

void main() {
  const engine = TideglassEngine();
  final content = SimulationContent('../content', '../events/content');
  SupplementalRun run(
    NoteSinkOrder order, {
    int offset = 0,
    DateTime? start,
    String seed = 'supplement-test',
    int chunk = 4,
  }) => SupplementalRun(
    content,
    visitsPerDay: 1,
    bonus: BonusPolicy.requiredCalibrationsOnly,
    resetDecision: const ResetDecision(ResetKind.multiplierGain),
    contractPolicy: ContractPolicy.surveysOnly,
    sinkOrder: order,
    utcOffsetMinutes: offset,
    startAt: start,
    seed: seed,
    offlineChunkHours: chunk,
  );

  test(
    'reset definitions separate Chart thresholds from actual multiplier gain',
    () {
      final state = GameState(
        counts: [100, 100, 100, 100, 100],
        charts: BigInt.from(1000),
        lifetimeMicros: engine.lifetimeForCharts(BigInt.from(1020)),
        elapsedMicros: BigInt.from(3600000000),
        rechartCount: 3,
      );
      expect(
        const ResetDecision(ResetKind.fixedCharts).evaluate(state).reset,
        true,
      );
      expect(
        const ResetDecision(ResetKind.multiplierGain).evaluate(state).reset,
        false,
      );
      expect(
        const ResetDecision(
          ResetKind.fixedCharts,
          fixedCharts: 100,
        ).evaluate(state).reset,
        false,
      );
    },
  );

  test(
    'forecast uses immutable real counterpart output and a strict1percent margin',
    () {
      final r = run(NoteSinkOrder.campaignFirst);
      r.run(days: 3);
      final state = r.main;
      final before = jsonEncode(state.toJson());
      const policy = ResetDecision(ResetKind.forecast, forecastHours: 1);
      final advice = policy.evaluate(state);
      expect(advice.reason, 'fixed_horizon_new_radiance');
      final kept = engine
          .advance(state, const Duration(hours: 1), autoBuy: true)
          .state;
      final reset = engine
          .advance(
            engine.rechart(state).state,
            const Duration(hours: 1),
            autoBuy: true,
          )
          .state;
      final a = kept.lifetimeMicros - state.lifetimeMicros;
      final b = reset.lifetimeMicros - state.lifetimeMicros;
      expect(advice.evidence['retained_gain_micros'], '$a');
      expect(advice.evidence['reset_gain_micros'], '$b');
      expect(advice.reset, b * BigInt.from(100) > a * BigInt.from(101));
      expect(jsonEncode(state.toJson()), before);
    },
  );

  test('exact marginal comparison exposes low-tier cross-tier benefit', () {
    final state = GameState(
      counts: [50, 50, 50, 50, 50],
      charts: BigInt.from(25),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(25)),
    );
    final snap = marginalSnapshot(state, label: 'controlled-synergy');
    final rows = snap['rows'] as List;
    for (final row in rows.take(2)) {
      expect(
        BigInt.parse(row['cross_tier_gain_raw']),
        greaterThan(BigInt.zero),
      );
      expect(
        BigInt.parse(row['total_gain_raw']),
        BigInt.parse(row['direct_gain_raw']) +
            BigInt.parse(row['cross_tier_gain_raw']),
      );
    }
    for (final row in rows.skip(2)) {
      expect(row['cross_tier_gain_raw'], '0');
    }
    expect((snap['efficiency_ranking'] as List).toSet(), {1, 2, 3, 4, 5});
  });

  test(
    'shared decoration transition preserves unrelated economics at49/50Notes',
    () {
      final low = GameState(
        surveyNotes: BigInt.from(49),
        walletMicros: BigInt.from(11),
        lifetimeMicros: BigInt.from(11),
      );
      final denied = buyDecoration(low, {}, 'cosmetic.core.decoration.01');
      expect(denied.accepted, false);
      expect(identical(denied.main, low), true);
      final enough = low.copyWith(surveyNotes: BigInt.from(50));
      final bought = buyDecoration(enough, {}, 'cosmetic.core.decoration.01');
      expect(bought.accepted, true);
      expect(bought.main.surveyNotes, BigInt.zero);
      final expected = enough.toJson();
      final after = bought.main.toJson();
      expected.remove('survey_notes');
      after.remove('survey_notes');
      expected.remove('revision');
      after.remove('revision');
      expect(after, expected);
      expect(
        buyDecoration(
          enough,
          bought.owned,
          'cosmetic.core.decoration.01',
        ).accepted,
        false,
      );
      expect(
        buyDecoration(enough, {}, 'cosmetic.core.decoration.07').accepted,
        false,
      );
    },
  );

  test(
    'actual optional spending order can delay campaign without Note loss',
    () {
      final campaign = run(NoteSinkOrder.campaignFirst);
      final decorations = run(NoteSinkOrder.decorationsFirst);
      campaign.run(days: 30);
      decorations.run(days: 30);
      expect(
        campaign.dossiers.completed.length,
        greaterThan(decorations.dossiers.completed.length),
      );
      expect(decorations.decorations.length, 6);
      expect(decorations.main.extraPlanSlots, 5);
      expect(decorations.decorationNotesSpent, BigInt.from(300));
      expect(decorations.planNotesSpent, BigInt.from(250));
      for (final r in [campaign, decorations]) {
        expect(
          r.totalNotesSpent + r.main.surveyNotes,
          r.surveyNotesEarned + r.contractNotesEarned,
        );
        expect(
          r.purchases.map((p) => p['id']).toSet().length,
          r.purchases.length,
        );
      }
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test(
    'all1750Notes are actually spent once and full ownership is reached',
    () {
      final r = run(NoteSinkOrder.plansFirst);
      r.run(days: 90);
      expect(r.totalNotesSpent, BigInt.from(1750));
      expect(r.dossiers.owned.length, 12);
      expect(r.dossiers.completed.length, 12);
      expect(r.purchases.length, 23);
      expect(r.allSinksPurchasedSeconds, isNotNull);
      expect(r.notesSpent, BigInt.from(1200));
      expect(r.main.extraPlanSlots, 5);
      expect(r.totalNotesSpent + r.main.surveyNotes, r.surveyNotesEarned);
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test(
    'non-midnight account phase is retained and chunking conserves outcomes',
    () {
      final a = run(
        NoteSinkOrder.decorationsFirst,
        offset: -420,
        start: DateTime.utc(2026, 10, 16, 5, 30),
        chunk: 4,
      );
      final b = run(
        NoteSinkOrder.decorationsFirst,
        offset: -420,
        start: DateTime.utc(2026, 10, 16, 5, 30),
        chunk: 1,
      );
      a.run(days: 3);
      b.run(days: 3);
      expect(a.main.daily.utcOffsetMinutes, -420);
      expect(a.main.walletMicros, b.main.walletMicros);
      expect(a.main.lifetimeMicros, b.main.lifetimeMicros);
      expect(a.main.charts, b.main.charts);
      expect(a.main.counts, b.main.counts);
      expect(a.main.daily.toJson(), b.main.daily.toJson());
      expect(a.purchases, b.purchases);
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test(
    'reachable veteran and new account produce identical isolated season',
    () {
      final r = run(NoteSinkOrder.campaignFirst);
      r.run(days: 3);
      for (final offline in [false, true]) {
        final result = seasonIsolation(
          content.season,
          r.main,
          offline: offline,
        );
        expect(result['main_profiles_differ'], true);
        expect(result['paired_event_states_identical'], true);
        expect(result['main_power_injection_rejected'], true);
        final observations = result['observations'] as List;
        expect(
          observations[2]['lifetime_micros'],
          observations[3]['lifetime_micros'],
        );
        expect(
          observations[3]['lifetime_micros'],
          observations[4]['lifetime_micros'],
        );
      }
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );
}
