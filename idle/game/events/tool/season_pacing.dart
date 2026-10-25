import 'dart:convert';
import 'dart:io';
import 'package:tideglass_events/tideglass_events.dart';

void main() {
  final definition = SeasonDefinition.fromJson(
      jsonDecode(File('content/season.01.json').readAsStringSync())
          as Map<String, dynamic>);
  final engine = SeasonEngine(definition),
      start = DateTime.utc(2026, 10, 16, 12);
  final results = <Map<String, dynamic>>[];
  for (final hours in [2, 24, 168, 336, 504, 672]) {
    for (final offline in [false, true]) {
      var state = SeasonState.initial(definition, SeasonSchedule(start), start,
          runId: 'pacing-$hours-$offline');
      state = engine.configurePolicy(state, automatic: true).state;
      state = engine
          .advanceTo(state, start.add(Duration(hours: hours)), offline: offline)
          .state;
      results.add({
        'hours': hours,
        'offline_single_absence': offline,
        'counts': state.fleet.counts,
        'lifetime_micros': state.fleet.lifetimeMicros.toString(),
        'wallet_micros': state.fleet.walletMicros.toString(),
        'output_per_second':
            engine.outputPerSecond(state).toDecimalString(decimals: 6),
        'milestones_eligible': definition.milestones
            .where((m) => state.fleet.lifetimeMicros >= m.lifetimeMicros)
            .map((m) => m.id)
            .toList()
      });
    }
  }
  print(const JsonEncoder.withIndent('  ').convert({
    'kind': 'deterministic_host_simulation_not_player_evidence',
    'rules_digest': definition.digest,
    'policy': 'bestPayback',
    'initial_state': 'one_gifted_skiff_zero_money',
    'results': results
  }));
}
