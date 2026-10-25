import 'dart:convert';
import 'dart:io';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_simulation/policy_run.dart';
import '../mobile/lib/content_compatibility.dart';
import '../mobile/lib/bundled_hashes.g.dart';

int checks = 0;
void check(bool value, String label) {
  checks++;
  if (!value) throw StateError(label);
}
Object? canonical(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return {for (final k in keys) k: canonical(value[k])};
  }
  if (value is List) return value.map(canonical).toList();
  return value;
}
String encoded(Object? value) => jsonEncode(canonical(value));
void main(List<String> args) {
  final report = jsonDecode(File(args[0]).readAsStringSync()) as Map;
  final content = SimulationContent('../content', '../events/content');
  final old = Campaign(
    Map<String, dynamic>.from(jsonDecode(File(args[1]).readAsStringSync())),
    content.challenges,
  );
  final prefix = CampaignProgress(completed: {'chapter.01', 'chapter.02'});
  ProgressFacts facts(int surveys, Set<String> calibrations) => ProgressFacts(
    main: GameState.initial(), recharts: 0, surveysCollected: surveys,
    calibrations: calibrations, completedChallenges: {},
  );
  check(old.evaluate(prefix, facts(12, {})).completed.length == 2, 'old requirement counterexample');
  check(content.campaign.evaluate(prefix, facts(11, {})).completed.length == 2, 'twelve Survey gate remains');
  check(content.campaign.evaluate(prefix, facts(12, {})).completed.length == 3, 'zero calibration chapter three');
  check(content.campaign.evaluate(prefix, facts(12, {'calibration.01'})).completed.length == 3, 'optional completion neutral');
  final main = GameState.initial();
  final before = encoded(main.toJson());
  for (var n = 0; n <= 6; n++) {
    final prior = CampaignProgress(completed: {
      for (var i = 1; i <= n; i++) 'chapter.${i.toString().padLeft(2, '0')}',
    });
    final evaluated = content.campaign.evaluate(prior, facts(0, {}));
    check(encoded(prior.toJson()) == encoded(evaluated.toJson()), 'prefix $n preserved');
    check(evaluated.cosmeticIds.length == n && evaluated.archiveIds.length == n * 3, 'unique reward projection $n');
    check(encoded(content.campaign.evaluate(evaluated, facts(0, {})).toJson()) == encoded(evaluated.toJson()), 'repeat evaluation $n');
  }
  check(before == encoded(main.toJson()), 'pure campaign no economic side effect');
  check(acceptsStoryContentDigest(optionalCalibrationPreviousDigest), 'known former digest accepted');
  check(acceptsStoryContentDigest(bundledManifestDigest), 'current digest accepted');
  check(acceptsStoryContentDigest(null), 'explicit legacy null remains');
  check(migratedStoryContentDigest(optionalCalibrationPreviousDigest) == bundledManifestDigest, 'known migration');
  check(migratedStoryContentDigest(bundledManifestDigest) == bundledManifestDigest, 'idempotent migration');
  for (final bad in [0, false, '', '0' * 64, '$optionalCalibrationPreviousDigest ', optionalCalibrationPreviousDigest.toUpperCase(), '$optionalCalibrationPreviousDigest\n']) {
    check(!acceptsStoryContentDigest(bad), 'unknown digest rejected: $bad');
  }
  final reproduced = <Map<String, dynamic>>[];
  for (final spec in [(1, 30, BonusPolicy.none), (3, 90, BonusPolicy.none), (6, 30, BonusPolicy.focusAndFreeSupport), (6, 30, BonusPolicy.focusAndAdSupportFixture)]) {
    final (visits, days, bonus) = spec;
    final actual = PolicyRun(content, visitsPerDay: visits, bonus: bonus, resetPolicy: ResetPolicy.atVisits).run(days: days)..['horizon_days'] = days;
    final expected = (report['policies'] as List).singleWhere((dynamic row) => row['visits_per_day'] == visits && row['horizon_days'] == days && row['bonus_policy'] == bonus.name);
    check(encoded(actual) == encoded(expected), 'exact entire trajectory summary $visits/$days/${bonus.name}');
    check(actual['chapters_completed'] == 6, 'complete campaign $visits/$days/${bonus.name}');
    if (bonus == BonusPolicy.none) {
      check(actual['focus_charges_used'] == 0 && actual['free_support_tokens_used'] == 0, 'literal no-bonus trajectory');
    }
    reproduced.add({'visits': visits, 'days': days, 'bonus': bonus.name, 'exact_report_match': true});
    stdout.writeln(jsonEncode({'reproduced': reproduced.last}));
  }
  File(args[2]).writeAsStringSync('${const JsonEncoder.withIndent('  ').convert({'checks': checks, 'reproduced': reproduced, 'status': 'pass', 'scope': 'pure content boundaries/digest API and production simulation; not native StoryProgress serialization'})}\n');
}
