import 'dart:convert';
import 'dart:io';

import '../simulation/lib/policy_run.dart';

void main(List<String> args) {
  final content = SimulationContent('../content', '../events/content');
  final report = jsonDecode(File(args.single).readAsStringSync()) as Map;
  final cases = <PolicyRun>[
    PolicyRun(
      content,
      visitsPerDay: 1,
      bonus: BonusPolicy.none,
      resetPolicy: ResetPolicy.atVisits,
    ),
    PolicyRun(
      content,
      visitsPerDay: 3,
      bonus: BonusPolicy.requiredCalibrationsOnly,
      resetPolicy: ResetPolicy.atVisits,
    ),
    PolicyRun(
      content,
      visitsPerDay: 6,
      bonus: BonusPolicy.focusAndFreeSupport,
      resetPolicy: ResetPolicy.hourlyAutomatic,
    ),
    PolicyRun(
      content,
      visitsPerDay: 3,
      bonus: BonusPolicy.requiredCalibrationsOnly,
      resetPolicy: ResetPolicy.atVisits,
      breakStartsDay: 10,
      breakHours: 120,
    ),
  ];
  final results = <Map<String, dynamic>>[];
  for (final run in cases) {
    final days = run.breakHours == 0 ? 30 : 90;
    final actual = run.run(days: days);
    final id =
        '$days/${run.visitsPerDay}/${run.bonus.name}/${run.resetPolicy.name}/${run.purchasePolicy.name}/${run.contractPolicy.name}/${run.breakHours}';
    final recorded = (report['policies'] as List).cast<Map>().singleWhere(
      (r) => r['case_id'] == id,
    );
    for (final key in actual.keys) {
      if (jsonEncode(actual[key]) != jsonEncode(recorded[key])) {
        throw StateError('Recorded case differs: $id $key');
      }
    }
    results.add({
      'case_id': id,
      'compared_summary_fields': actual.length,
      'exact_match': true,
    });
  }
  print(
    jsonEncode({
      'reproduced_cases': results,
      'limits':
          'Fresh pinned deterministic policy reruns, not real elapsed players.',
    }),
  );
}
