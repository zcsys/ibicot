import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_progression/decoration_purchase.dart';
import 'package:tideglass_simulation/policy_run.dart';
import 'package:tideglass_simulation/supplemental_run.dart';
import 'package:tideglass_simulation/supplemental_math.dart';
import 'package:tideglass_simulation/season_isolation.dart';

int checks = 0;
void check(bool value, String label) {
  checks++;
  if (!value) throw StateError(label);
}

Object? canonical(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return {for (final key in keys) key: canonical(value[key])};
  }
  if (value is List) return value.map(canonical).toList();
  return value;
}

String encoded(Object? value) => jsonEncode(canonical(value));
void same(Object? a, Object? b, String label) =>
    check(encoded(a) == encoded(b), label);

void main(List<String> args) {
  final target = File(args.single);
  final baseline = jsonDecode(
    File('../../release/balance/long-horizon-v4-policies.json')
        .readAsStringSync(),
  ) as Map;
  final supplemental = jsonDecode(
    File('../../release/balance/supplemental-v2.json').readAsStringSync(),
  ) as Map;
  final content = SimulationContent('../content', '../events/content');
  final results = <Map<String, dynamic>>[];
  const engine = TideglassEngine();

  // Independent finite-difference construction: explicitly sum every changed
  // producer rather than calling the simulator's marginalSnapshot helper.
  var samples = 0;
  for (final trajectory in supplemental['trajectories']) {
    for (final sample in trajectory['marginal_samples']) {
      final state = GameState(
        counts: List<int>.from(sample['counts']),
        charts: BigInt.parse(sample['charts']),
        walletMicros: BigInt.parse(sample['wallet_micros']),
        lifetimeMicros: BigInt.parse(sample['lifetime_micros']),
      );
      final before = jsonEncode(state.toJson());
      final base = List.generate(
        5,
        (i) => engine.producerOutputPerSecond(state, i).raw,
      );
      same(
        '${base.fold(BigInt.zero, (a, b) => a + b)}',
        sample['output_raw'],
        'sample base rate',
      );
      for (final row in sample['rows']) {
        final tier = (row['tier'] as int) - 1;
        final counts = state.counts.toList();
        counts[tier]++;
        final after = state.copyWith(counts: counts);
        final changed = List.generate(
          5,
          (i) => engine.producerOutputPerSecond(after, i).raw - base[i],
        );
        final total = changed.fold(BigInt.zero, (a, b) => a + b);
        same(
          '${changed[tier]}',
          row['direct_gain_raw'],
          'direct finite difference',
        );
        same(
          '${total - changed[tier]}',
          row['cross_tier_gain_raw'],
          'external finite difference',
        );
        same('$total', row['total_gain_raw'], 'total finite difference');
        same(
          '${engine.priceMicros(tier, counts[tier] - 1)}',
          row['cost_micros'],
          'sample exact price',
        );
      }
      same(jsonEncode(state.toJson()), before, 'marginal sample immutable');
      samples++;
    }
  }

  // Boundary probes cover every real Note sink family, underflow, caps,
  // ownership replay, chapter prerequisite, and no economic side effects.
  final unlocked = GameState(
    charts: BigInt.from(10),
    lifetimeMicros: engine.lifetimeForCharts(BigInt.from(10)),
    surveyNotes: BigInt.from(1750),
  );
  var plans = unlocked;
  for (var n = 0; n < 5; n++) {
    check(
      !engine
          .buyPlanSlot(plans.copyWith(surveyNotes: BigInt.from(49)))
          .accepted,
      'plan rejects49',
    );
    final next = engine.buyPlanSlot(plans);
    check(
      next.accepted &&
          next.state.extraPlanSlots == n + 1 &&
          next.state.surveyNotes == plans.surveyNotes - BigInt.from(50),
      'exact plan purchase',
    );
    check(
      engine.outputPerSecond(plans).raw ==
          engine.outputPerSecond(next.state).raw,
      'plan no raw power',
    );
    plans = next.state;
  }
  check(!engine.buyPlanSlot(plans).accepted, 'five-plan cap');
  check(
    !engine.buyPlanSlot(unlocked.copyWith(charts: BigInt.from(9))).accepted,
    'plan Chart gate',
  );
  var decorState = plans;
  var owned = <String>{};
  for (var n = 1; n <= 6; n++) {
    final id = 'cosmetic.core.decoration.${n.toString().padLeft(2, '0')}';
    final denied = buyDecoration(
      decorState.copyWith(surveyNotes: BigInt.from(49)),
      owned,
      id,
    );
    check(
      !denied.accepted && denied.owned.length == owned.length,
      'decoration rejects49',
    );
    final purchased = buyDecoration(decorState, owned, id);
    check(
      purchased.accepted &&
          purchased.main.surveyNotes ==
              decorState.surveyNotes - BigInt.from(50),
      'decoration50',
    );
    final expect = decorState.toJson();
    expect['survey_notes'] = purchased.main.surveyNotes.toString();
    expect['revision'] = decorState.revision + 1;
    same(
      purchased.main.toJson(),
      expect,
      'decoration changes only Notes/revision',
    );
    owned = purchased.owned.toSet();
    decorState = purchased.main;
    check(
      !buyDecoration(decorState, owned, id).accepted,
      'decoration duplicate',
    );
  }
  check(
    !buyDecoration(decorState, owned, 'cosmetic.core.decoration.07').accepted,
    'unknown decoration',
  );
  var dossierMain = decorState;
  var collection = DossierCollection();
  final campaign = CampaignProgress(
    completed: {'chapter.01', 'chapter.02', 'chapter.03'},
  );
  for (final definition in content.challenges) {
    check(
      !collection.open(dossierMain, CampaignProgress(), definition).accepted,
      'dossier chapter gate',
    );
    check(
      !collection
          .open(
            dossierMain.copyWith(surveyNotes: BigInt.from(99)),
            campaign,
            definition,
          )
          .accepted,
      'dossier rejects99',
    );
    final opened = collection.open(dossierMain, campaign, definition);
    check(
      opened.accepted &&
          opened.main.surveyNotes == dossierMain.surveyNotes - BigInt.from(100),
      'dossier100',
    );
    final replay = opened.dossiers.open(opened.main, campaign, definition);
    check(
      replay.accepted && identical(replay.main, opened.main),
      'active dossier duplicate no debit',
    );
    collection = opened.dossiers.leave();
    dossierMain = opened.main;
    final reopened = collection.open(dossierMain, campaign, definition);
    check(
      reopened.accepted && reopened.main.surveyNotes == dossierMain.surveyNotes,
      'owned dossier reopenfree',
    );
    collection = reopened.dossiers.leave();
    dossierMain = reopened.main;
  }
  check(
    dossierMain.surveyNotes == BigInt.zero &&
        collection.owned.length == 12 &&
        owned.length == 6 &&
        plans.extraPlanSlots == 5,
    '1750 exact actual purchase boundary',
  );
  same(
    engine.outputPerSecond(dossierMain).raw.toString(),
    engine.outputPerSecond(unlocked).raw.toString(),
    'sink collection no raw power',
  );

  const selectedBaseline = {
    '30/1/none/atVisits/bestPayback/allReady/0',
    '30/1/requiredCalibrationsOnly/atVisits/bestPayback/allReady/0',
    '90/3/focusAndFreeSupport/hourlyAutomatic/bestPayback/allReady/0',
    '90/3/focusAndAdSupportFixture/hourlyAutomatic/bestPayback/allReady/0',
    '90/3/requiredCalibrationsOnly/atVisits/bestPayback/allReady/120',
  };
  for (final raw in baseline['policies']) {
    final row = Map<String, dynamic>.from(raw);
    if (!selectedBaseline.contains(row['case_id'])) continue;
    final run = PolicyRun(
      content,
      visitsPerDay: row['visits_per_day'],
      bonus: BonusPolicy.values.byName(row['bonus_policy']),
      resetPolicy: ResetPolicy.values.byName(row['reset_policy']),
      purchasePolicy: PurchasePolicy.values.byName(row['purchase_policy']),
      contractPolicy: ContractPolicy.values.byName(row['contract_policy']),
      seed: row['seed'],
      breakStartsDay: row['break_starts_day'],
      breakHours: row['break_hours'],
    );
    final actual = run.run(days: row['horizon_days']);
    row.remove('runtime_milliseconds');
    row.remove('horizon_days');
    final id = row.remove('case_id');
    same(actual, row, '$id exact replay');
    results.add({
      'case_id': id,
      'exact_summary_match': true,
      'canonical_sha256': sha256
          .convert(utf8.encode(encoded(actual)))
          .toString(),
    });
    stdout.writeln('PASS baseline $id');
  }
  const selectedSupplemental = {
    'reset/30/1/fixed-10-charts',
    'reset/30/3/forecast-24h-output-1percent-margin',
    'reset/90/3/fixed-10-charts',
    'reset/90/3/multiplier-20-percent',
    'notes/30/seed-a/plansFirst/pursueWithSeason',
    'notes/30/seed-c/decorationsFirst/surveysOnly',
    'notes/90/seed-b/plansFirst/pursueWithSeason',
    'notes/90/seed-c/decorationsFirst/surveysOnly',
  };
  for (final raw in supplemental['trajectories']) {
    final row = Map<String, dynamic>.from(raw);
    if (!selectedSupplemental.contains(row['case_id'])) continue;
    final id = row['reset_policy'] as String;
    final decision = id.startsWith('fixed-')
        ? ResetDecision(
            ResetKind.fixedCharts,
            fixedCharts: int.parse(id.split('-')[1]),
          )
        : id.startsWith('multiplier-')
        ? ResetDecision(
            ResetKind.multiplierGain,
            gainPercent: int.parse(id.split('-')[1]),
          )
        : ResetDecision(
            ResetKind.forecast,
            forecastHours: int.parse(id.split('-')[1].replaceAll('h', '')),
          );
    final run = SupplementalRun(
      content,
      visitsPerDay: row['visits_per_day'],
      bonus: BonusPolicy.values.byName(row['bonus_policy']),
      resetDecision: decision,
      sinkOrder: NoteSinkOrder.values.byName(row['sink_order']),
      startAt: DateTime.parse(row['start_utc']),
      utcOffsetMinutes: row['utc_offset_minutes'],
      purchasePolicy: PurchasePolicy.values.byName(row['purchase_policy']),
      contractPolicy: ContractPolicy.values.byName(row['contract_policy']),
      seed: row['seed'],
    );
    final actual = run.run(days: row['horizon_days']);
    final caseId = row.remove('case_id');
    for (final key in [
      'group',
      'horizon_days',
      'runtime_milliseconds',
      'notes_conserved',
    ]) {
      row.remove(key);
    }
    same(actual, row, '$caseId exact replay including decisions/transactions');
    if (caseId == 'reset/30/1/fixed-10-charts') {
      final before = jsonEncode(run.main.toJson());
      for (var i = 0; i < 2; i++) {
        same(
          seasonIsolation(content.season, run.main, offline: i == 1),
          supplemental['season_isolation'][i],
          'actual season paired trace',
        );
      }
      same(
        jsonEncode(run.main.toJson()),
        before,
        'season leaves reachable veteran immutable',
      );
      // Split the counterfactual on the real boost-expiry boundary, with no
      // future claims/reset. This independently checks full-horizon objective.
      final boosted = run.main.copyWith(
        focusRemainingMicros: BigInt.from(1000000),
      );
      final snapshot = jsonEncode(boosted.toJson());
      for (final hours in [1, 8, 24]) {
        final advice = ResetDecision(
          ResetKind.forecast,
          forecastHours: hours,
        ).evaluate(boosted);
        check(
          advice.reason == 'fixed_horizon_new_radiance',
          'eligible forecast',
        );
        GameState project(GameState s) => engine
            .advance(
              engine
                  .advance(s, const Duration(seconds: 1), autoBuy: true)
                  .state,
              Duration(seconds: hours * 3600 - 1),
              autoBuy: true,
            )
            .state;
        final keep = project(boosted).lifetimeMicros - boosted.lifetimeMicros;
        final reset =
            project(engine.rechart(boosted).state).lifetimeMicros -
            boosted.lifetimeMicros;
        same(
          advice.evidence['retained_gain_micros'],
          '$keep',
          'retain split expiry oracle',
        );
        same(
          advice.evidence['reset_gain_micros'],
          '$reset',
          'reset split expiry oracle',
        );
        check(
          advice.reset == (reset * BigInt.from(100) > keep * BigInt.from(101)),
          'strict1percent margin',
        );
      }
      same(
        jsonEncode(boosted.toJson()),
        snapshot,
        'counterfactual leaves starting state unchanged',
      );
    }
    results.add({
      'case_id': caseId,
      'exact_summary_match': true,
      'canonical_sha256': sha256
          .convert(utf8.encode(encoded(actual)))
          .toString(),
    });
    stdout.writeln('PASS supplemental $caseId');
  }
  check(
    results.length == selectedBaseline.length + selectedSupplemental.length,
    'allselectedexecuted',
  );
  target.writeAsStringSync(
    '${const JsonEncoder.withIndent('  ').convert({'status': 'pass', 'checks': checks, 'selected_exact_reproductions': results, 'marginal_states': samples, 'season_pairs_reproduced': 2, 'test_source_sha256': sha256.convert(File('../qa/integration_corrected_balance.dart').readAsBytesSync()).toString(), 'limits': 'Virtual engines only. No native, store, ad delivery, human pace or package acceptance.'})}\n',
  );
  stdout.writeln(
    'PASS $checks checks; ${results.length} exact full summaries; $samples marginal states',
  );
}
