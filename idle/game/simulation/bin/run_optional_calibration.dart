import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_simulation/policy_run.dart';

void main() {
  final root = Directory('../..').resolveSymbolicLinksSync();
  final stamp = DateTime.now()
      .toUtc()
      .toIso8601String()
      .replaceAll(':', '')
      .replaceAll('.', '');
  final output = Directory('../../release/balance/optional-calibration-$stamp')
    ..createSync();
  final pins = <String, String>{};
  for (final path in [
    '../core/lib',
    '../progression/lib',
    '../events/lib',
    '../content',
    '../events/content',
    'lib',
    'bin',
    'test',
  ]) {
    for (final file in Directory(
      path,
    ).listSync(recursive: true).whereType<File>()) {
      if (!file.path.endsWith('.dart') && !file.path.endsWith('.json'))
        continue;
      final relative = file.resolveSymbolicLinksSync().substring(
        root.length + 1,
      );
      pins[relative] = sha256.convert(file.readAsBytesSync()).toString();
      final copy = File('${output.path}/source/$relative');
      copy.parent.createSync(recursive: true);
      file.copySync(copy.path);
    }
  }
  final rows = <Map<String, dynamic>>[];
  final content = SimulationContent('../content', '../events/content');
  void save() {
    File('${output.path}/report.json').writeAsStringSync(
      const JsonEncoder.withIndent('  ').convert({
            'status': rows.length == 15 ? 'complete' : 'running',
            'experiment':
                'Deterministic production policies after optional calibration repair; not human pacing or retention',
            'planned_cases': 15,
            'source_sha256': pins,
            'policies': rows,
            'limitations': [
              'Legacy requiredCalibrationsOnly policy uses three optional calibrations',
              'Ad receipts are synthetic parity fixtures',
              'Chapter timestamps are evaluation-boundary upper bounds',
            ],
          }) +
          '\n',
      flush: true,
    );
  }

  save();
  stdout.writeln(output.path);
  for (final visits in [1, 3, 6]) {
    for (final bonus in [
      BonusPolicy.none,
      BonusPolicy.requiredCalibrationsOnly,
      BonusPolicy.focusAndFreeSupport,
      BonusPolicy.focusAndAdSupportFixture,
    ]) {
      final run = PolicyRun(
        content,
        visitsPerDay: visits,
        bonus: bonus,
        resetPolicy: ResetPolicy.atVisits,
      );
      rows.add(run.run(days: 30)..['horizon_days'] = 30);
      save();
      stdout.writeln(
        '${rows.length}/15 $visits ${bonus.name}: chapters ${rows.last['chapters_completed']}',
      );
    }
    final run = PolicyRun(
      content,
      visitsPerDay: visits,
      bonus: BonusPolicy.none,
      resetPolicy: ResetPolicy.atVisits,
    );
    rows.add(run.run(days: 90)..['horizon_days'] = 90);
    save();
    stdout.writeln(
      '${rows.length}/15 $visits noBonus 90 days: chapters ${rows.last['chapters_completed']}',
    );
  }
  for (final entry in pins.entries) {
    if (sha256
            .convert(File('$root/${entry.key}').readAsBytesSync())
            .toString() !=
        entry.value)
      throw StateError('Source changed during run: ${entry.key}');
  }
  for (final row in rows) {
    if (row['chapters_completed'] != 6)
      throw StateError(
        'Ending not reached: ${row['visits_per_day']} / ${row['bonus_policy']}',
      );
    if (row['bonus_policy'] == 'none' &&
        (row['focus_charges_used'] != 0 ||
            row['free_support_tokens_used'] != 0))
      throw StateError('No-bonus contamination');
  }
  for (final visits in [1, 3, 6]) {
    Object? normalized(Object? value) {
      if (value is Map)
        return {
          for (final entry in value.entries)
            if (entry.key != 'bonus_policy' &&
                entry.key != 'main_serialized_bytes')
              entry.key: normalized(entry.value),
        };
      if (value is List) return value.map(normalized).toList();
      return value;
    }

    Object? comparison(String bonus) => normalized(
      rows.singleWhere(
        (r) =>
            r['visits_per_day'] == visits &&
            r['horizon_days'] == 30 &&
            r['bonus_policy'] == bonus,
      ),
    );
    if (jsonEncode(comparison('focusAndFreeSupport')) !=
        jsonEncode(comparison('focusAndAdSupportFixture')))
      throw StateError('Route parity differs');
  }
  File('${output.path}/assertions.json').writeAsStringSync(
    jsonEncode({
          'source_unchanged': true,
          'all_15_endings': true,
          'six_zero_bonus_cases': true,
          'three_free_ad_economic_summary_pairs_equal': true,
          'comparison_exclusions': ['bonus_policy', 'main_serialized_bytes'],
        }) +
        '\n',
  );
}
