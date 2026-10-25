import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_simulation/policy_run.dart';
import 'package:tideglass_simulation/supplemental_run.dart';
import 'package:tideglass_simulation/supplemental_math.dart';
import 'package:tideglass_simulation/season_isolation.dart';

void main(List<String> args) {
  final smoke = args.contains('--smoke');
  final resume = args.contains('--resume');
  final target = File(
    '../../release/balance/supplemental-v1${smoke ? '-smoke' : ''}.json',
  );
  if (target.existsSync() && !resume) {
    throw StateError(
      'Output exists; use --resume only with identical sources.',
    );
  }
  final content = SimulationContent('../content', '../events/content');
  final sources = <String, String>{};
  for (final path in [
    '../core/lib',
    '../events/lib',
    '../progression/lib',
    '../content',
    '../events/content',
    'lib',
    'bin',
    'test',
  ]) {
    final files =
        Directory(path)
            .listSync(recursive: true)
            .whereType<File>()
            .where((f) => f.path.endsWith('.dart') || f.path.endsWith('.json'))
            .toList()
          ..sort((a, b) => a.path.compareTo(b.path));
    for (final file in files) {
      sources[file.path] = sha256.convert(file.readAsBytesSync()).toString();
    }
  }
  for (final file in [
    File('pubspec.yaml'),
    File('pubspec.lock'),
    File('../../V1_ROADMAP.md'),
    File('../../TIDEGLASS_DESIGN.md'),
  ]) {
    sources[file.path] = sha256.convert(file.readAsBytesSync()).toString();
  }
  final digest = sha256.convert(utf8.encode(jsonEncode(sources))).toString();
  final archive = Directory(
    '../../release/balance/supplemental-source-$digest',
  );
  final workspace = Directory('../..').resolveSymbolicLinksSync();
  for (final path in sources.keys) {
    final source = File(path);
    final relative = source.resolveSymbolicLinksSync().substring(
      workspace.length + 1,
    );
    final destination = File('${archive.path}/$relative');
    destination.parent.createSync(recursive: true);
    if (destination.existsSync()) {
      if (sha256.convert(destination.readAsBytesSync()).toString() !=
          sources[path]) {
        throw StateError('Immutable source archive differs: $relative');
      }
    } else {
      source.copySync(destination.path);
    }
  }
  var sourcesUnchanged = false;
  final cases = <(String, String, int, SupplementalRun)>[];
  final resetPolicies = [
    const ResetDecision(ResetKind.fixedCharts),
    const ResetDecision(ResetKind.fixedCharts, fixedCharts: 100),
    const ResetDecision(ResetKind.multiplierGain),
    const ResetDecision(ResetKind.forecast, forecastHours: 1),
    const ResetDecision(ResetKind.forecast, forecastHours: 8),
    const ResetDecision(ResetKind.forecast, forecastHours: 24),
  ];
  final contexts = [
    ('seed-a', DateTime.utc(2026, 10, 16), 0),
    ('seed-b', DateTime.utc(2026, 10, 16, 23, 55), 180),
    ('seed-c', DateTime.utc(2026, 10, 16, 5, 30), -420),
  ];
  for (final days in smoke ? [3] : [30, 90]) {
    for (final visits in smoke ? [3] : [1, 3, 6]) {
      for (final policy in smoke ? [resetPolicies.last] : resetPolicies) {
        cases.add((
          'reset/$days/$visits/${policy.id}',
          'reset',
          days,
          SupplementalRun(
            content,
            visitsPerDay: visits,
            bonus: BonusPolicy.requiredCalibrationsOnly,
            resetDecision: policy,
          ),
        ));
      }
    }
    for (final context in smoke ? [contexts.last] : contexts) {
      for (final order
          in smoke ? [NoteSinkOrder.decorationsFirst] : NoteSinkOrder.values) {
        for (final contracts
            in smoke
                ? [ContractPolicy.surveysOnly]
                : [
                    ContractPolicy.surveysOnly,
                    ContractPolicy.oneReadyPerVisit,
                    ContractPolicy.pursueWithSeason,
                  ]) {
          cases.add((
            'notes/$days/${context.$1}/${order.name}/${contracts.name}',
            'notes',
            days,
            SupplementalRun(
              content,
              visitsPerDay: 1,
              bonus: BonusPolicy.requiredCalibrationsOnly,
              resetDecision: const ResetDecision(ResetKind.multiplierGain),
              sinkOrder: order,
              contractPolicy: contracts,
              seed: context.$1,
              startAt: context.$2,
              utcOffsetMinutes: context.$3,
            ),
          ));
        }
      }
    }
  }
  final rows = <Map<String, dynamic>>[];
  final isolation = <Map<String, dynamic>>[];
  if (resume && target.existsSync()) {
    final old = jsonDecode(target.readAsStringSync()) as Map;
    if (old['source_digest'] != digest)
      throw StateError('Source digest changed');
    rows.addAll(
      (old['trajectories'] as List).map((e) => Map<String, dynamic>.from(e)),
    );
    isolation.addAll(
      (old['season_isolation'] as List).map(
        (e) => Map<String, dynamic>.from(e),
      ),
    );
  }
  final ids = rows.map((r) => r['case_id']).toSet();
  target.parent.createSync(recursive: true);
  void save() {
    final tmp = File('${target.path}.new');
    tmp.writeAsStringSync(
      '${const JsonEncoder.withIndent('  ').convert({
        'schema_version': 1,
        'experiment_version': 'supplemental-v1',
        'generated_at_utc': DateTime.now().toUtc().toIso8601String(),
        'status': rows.length == cases.length && isolation.length == 2 && sourcesUnchanged ? 'complete' : 'running',
        'planned_trajectories': cases.length,
        'completed_trajectories': rows.length,
        'source_digest': digest,
        'source_archive': archive.path,
        'sources_unchanged_through_run': sourcesUnchanged,
        'dart_version': Platform.version,
        'source_sha256': sources,
        'method': {
          'production_engines': true,
          'economic_constants_changed': false,
          'first_session_minutes': 30,
          'later_session_minutes': 5,
          'reset_common_first_award': 10,
          'reset_common_min_run_seconds': 600,
          'reset_decisions': 'same visit/action opportunities; no automatic between-visit resets',
          'forecast': 'production-engine parallel immutable counterfactuals; automatic buying; retained boost expiry; no future bonuses, claims or resets',
          'forecast_objective': 'new Radiance over fixed horizon; reset must exceed retain by >1%',
          'note_sinks': 'real12x100 dossier entries,5x50 plan slots,6x50 shared production decoration purchases',
          'spending_order': 'strict sequential wish list; an unavailable first remaining item waits; dossier completion precedes next entry',
          'marginal_sampling': 'reachable before-visit states near day7,30,60,89; exact one-unit gain includes target-tier synergy',
          'limits': ['Virtual policies are not observed novice behavior, D30 retention or globally optimal reset advice.', 'Forecast horizons assume full-rate production for at most24h; later daily choices can invalidate the forecast.', 'Chapter, purchase and reconstruction times are upper bounds at action/evaluation boundaries.', 'Context tuples vary seed, day offset and start phase together; they test robustness, not independent causal seed effects.', 'Daily pursuing policy uses real reflection/season alternatives; it does not fabricate three completed contracts.', 'Extra plans are bought but their unused capacity does not automatically change purchase strategy.', 'Season pair checks engine separation; service, paid entitlement and UI account binding require independent coverage.', 'No human learning time, fill rates, beta readiness, release acceptance or elapsed season study is inferred.'],
        },
        'trajectories': rows,
        'season_isolation': isolation,
      })}\n',
      flush: true,
    );
    tmp.renameSync(target.path);
  }

  save();
  for (final (id, group, days, run) in cases) {
    if (ids.contains(id)) continue;
    final timer = Stopwatch()..start();
    final row = run.run(days: days)
      ..addAll({
        'case_id': id,
        'group': group,
        'horizon_days': days,
        'runtime_milliseconds': timer.elapsedMilliseconds,
      });
    if (run.totalNotesSpent + run.main.surveyNotes !=
        run.surveyNotesEarned + run.contractNotesEarned) {
      throw StateError('Note conservation failed for $id');
    }
    row['notes_conserved'] = true;
    rows.add(row);
    if (isolation.isEmpty && days >= (smoke ? 3 : 30)) {
      isolation.add(seasonIsolation(content.season, run.main, offline: false));
      isolation.add(seasonIsolation(content.season, run.main, offline: true));
    }
    save();
    stdout.writeln(
      '${rows.length}/${cases.length} $id; chapters=${row['chapters_completed']}; spent=${run.totalNotesSpent}; ${timer.elapsedMilliseconds}ms',
    );
  }
  sourcesUnchanged = sources.entries.every(
    (entry) =>
        sha256.convert(File(entry.key).readAsBytesSync()).toString() ==
        entry.value,
  );
  if (!sourcesUnchanged) throw StateError('Inputs changed during experiment');
  save();
}
