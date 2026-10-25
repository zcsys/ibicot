// Independent regression for root's cache repair. No production rules change.
import 'dart:convert';
import 'dart:io';

import 'package:tideglass_core/tideglass_core.dart' as core;
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_events/tideglass_events.dart';

import '../../release/performance/numeric-baseline-source/tideglass_core.dart'
    as old;

class BaselineRules extends old.TideglassEngine {
  const BaselineRules(this.matrix, this.immediate);
  final List<List<int>> matrix;
  final bool immediate;
  @override
  old.Fixed synergyMultiplier(old.GameState s, int t) {
    if (!immediate || t < 3) return old.Fixed.one;
    final x = old.log2Ratio(BigInt.from(25 + s.counts[0]), BigInt.from(25));
    final y = old.log2Ratio(BigInt.from(25 + s.counts[1]), BigInt.from(25));
    return old.Fixed.raw(
      old.Fixed.scale +
          (x.raw * BigInt.from(matrix[0][t - 3]) +
                  y.raw * BigInt.from(matrix[1][t - 3])) ~/
              BigInt.from(100),
    );
  }
}

class NoMemoChallenge extends ChallengeEconomy {
  const NoMemoChallenge(super.definition);
  @override
  core.Fixed outputPerSecond(core.GameState s) => core.Fixed.raw(
    List.generate(
      5,
      (i) => producerOutputPerSecond(s, i).raw,
    ).fold(BigInt.zero, (a, b) => a + b),
  );
}

var assertions = 0;
void equal(Object? a, Object? b, String label) {
  assertions++;
  if (jsonEncode(a) != jsonEncode(b)) throw StateError('$label: $a != $b');
}

Map<String, dynamic> economic(core.GameState s) => {
  'counts': s.counts,
  'wallet': '${s.walletMicros}',
  'lifetime': '${s.lifetimeMicros}',
  'elapsed': '${s.elapsedMicros}',
  'remainder': '${s.earningRemainder}',
};
Map<String, dynamic> read(String p) =>
    Map<String, dynamic>.from(jsonDecode(File(p).readAsStringSync()));
void main() {
  final definitions = [
    for (var i = 1; i <= 12; i++)
      ChallengeDefinition.fromJson(
        read(
          '../content/challenges/challenge.${i.toString().padLeft(2, '0')}.json',
        ),
      ),
  ];
  final definition = SeasonDefinition.fromJson(
    read('../events/content/season.01.json'),
  );
  final seasonEngine = SeasonEngine(definition);
  const main = core.TideglassEngine();
  const mainBefore = old.TideglassEngine();
  final start = DateTime.utc(2026, 10, 16);
  SeasonState seasonAt(core.GameState s) {
    final j = SeasonState.initial(
      definition,
      SeasonSchedule(start),
      start,
      runId: 'cache-rule-isolation',
    ).toJson();
    j['fleet'] = {
      'counts': s.counts,
      'wallet_micros': '${s.walletMicros}',
      'lifetime_micros': '${s.lifetimeMicros}',
      'elapsed_micros': '${s.elapsedMicros}',
      'earning_remainder': '${s.earningRemainder}',
    };
    return SeasonState.fromJson(j, definition);
  }

  final funcs = <BigInt Function(core.GameState)>[
    (s) => main.outputPerSecond(s).raw,
    for (final d in definitions)
      (s) => ChallengeEconomy(d).outputPerSecond(s).raw,
    (s) => seasonEngine.outputPerSecond(seasonAt(s)).raw,
  ];
  final refs = <BigInt Function(old.GameState)>[
    (s) => mainBefore.outputPerSecond(s).raw,
    for (final d in definitions)
      (s) => BaselineRules(d.matrix, d.synergyImmediate).outputPerSecond(s).raw,
    (s) => BaselineRules(definition.matrix, true).outputPerSecond(s).raw,
  ];
  // Controlled rate vectors can exceed dossier caps. The actual traces below
  // use valid reachable fleets, all rules and exact persisted-state comparison.
  for (final counts in [
    [25, 25, 25, 25, 25],
    [26, 50, 75, 100, 125],
    [100, 99, 75, 50, 25],
  ]) {
    final s = core.GameState(counts: counts),
        previous = old.GameState(counts: counts);
    for (var cycle = 0; cycle < 28; cycle++) {
      for (var index = 0; index < 14; index++) {
        final rule = (cycle + (cycle < 14 ? index : -index)) % 14;
        equal(
          '${funcs[rule](s)}',
          '${refs[rule](previous)}',
          'rate order$cycle index$index rule$rule',
        );
      }
    }
  }
  for (var i = 0; i < 1300; i++) {
    final s = core.GameState(counts: [i + 1, 1301 - i, 25, 25, 25]);
    equal(
      '${main.outputPerSecond(s).raw}',
      '${mainBefore.outputPerSecond(old.GameState.fromJson(s.toJson())).raw}',
      'main eviction churn$i',
    );
  }
  final repeated = core.GameState(counts: [25, 25, 25, 25, 25]);
  final previous = old.GameState.fromJson(repeated.toJson());
  for (var i = 13; i >= 0; i--)
    equal(
      '${funcs[i](repeated)}',
      '${refs[i](previous)}',
      'scenario after eviction$i',
    );
  final traces = <Map<String, dynamic>>[];
  for (final d in definitions) {
    for (final offline in [false, true]) {
      final production = ChallengeEconomy(d), reference = NoMemoChallenge(d);
      var actual = production.newRun().copyWith(automatic: true);
      var expected = reference.newRun().copyWith(automatic: true);
      var offset = Duration.zero;
      for (final hours in [1, 7, 16, 24, 24, 1]) {
        main.outputPerSecond(actual.fleet);
        seasonEngine.outputPerSecond(seasonAt(actual.fleet));
        final step = Duration(hours: hours);
        actual = production.advanceRun(
          actual,
          step,
          offline: offline,
          offlineElapsedBefore: offset,
        );
        expected = reference.advanceRun(
          expected,
          step,
          offline: offline,
          offlineElapsedBefore: offset,
        );
        equal(
          actual.toJson(),
          expected.toJson(),
          '${d.id} offline$offline after${offset + step}',
        );
        offset += step;
      }
      traces.add({
        'id': d.id,
        'offline': offline,
        'complete': actual.complete,
        'state': economic(actual.fleet),
      });
    }
  }
  final eventRules = ChallengeDefinition(
    id: 'challenge.12',
    family: 'synergy_priorities',
    title: 'event oracle',
    intro: '',
    completion: '',
    tierCaps: const [null, null, null, null, null],
    matrix: definition.matrix,
    synergyImmediate: true,
    automaticOnly: false,
    goalMicros: BigInt.from(10).pow(50),
  );
  for (final offline in [false, true]) {
    var event = seasonEngine
        .configurePolicy(
          SeasonState.initial(
            definition,
            SeasonSchedule(start),
            start,
            runId: 'event-reference',
          ),
          automatic: true,
        )
        .state;
    final reference = NoMemoChallenge(eventRules);
    var expected = reference.newRun().copyWith(automatic: true);
    var offset = Duration.zero;
    for (final hours in [1, 7, 16, 24, 24, 1]) {
      main.outputPerSecond(event.fleet.asCore);
      for (final d in definitions) {
        ChallengeEconomy(d).outputPerSecond(event.fleet.asCore);
      }
      final step = Duration(hours: hours);
      final result = seasonEngine.advanceTo(
        event,
        start.add(offset + step),
        offline: offline,
        offlineElapsedBefore: offset,
      );
      equal(result.accepted, true, 'event advance accepted');
      event = result.state;
      expected = reference.advanceRun(
        expected,
        step,
        offline: offline,
        offlineElapsedBefore: offset,
      );
      equal(
        economic(event.fleet.asCore),
        economic(expected.fleet),
        'event trace$offline after${offset + step}',
      );
      offset += step;
    }
    traces.add({
      'id': 'season.01',
      'offline': offline,
      'state': economic(event.fleet.asCore),
    });
  }
  print(
    jsonEncode({
      'status': 'passed',
      'assertions': assertions,
      'rate_rule_count': 14,
      'rotated_forward_reverse_orders': 28,
      'controlled_count_vectors': 3,
      'eviction_states': 1300,
      'exact_scenario_traces': traces,
      'limits': 'Host economic isolation; not native device, services or player evidence',
    }),
  );
}
