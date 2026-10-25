import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_simulation/policy_run.dart';

void main(List<String> arguments) {
  final quick = arguments.contains('--quick');
  final resume = arguments.contains('--resume');
  final content = SimulationContent('../content', '../events/content');
  final sources = <String, String>{};
  for (final directory in [
    '../core/lib',
    '../events/lib',
    '../progression/lib',
    '../content',
    '../events/content',
    'lib',
    'bin',
    'test',
  ]) {
    if (!Directory(directory).existsSync()) continue;
    final files =
        Directory(directory)
            .listSync(recursive: true)
            .whereType<File>()
            .where((f) => f.path.endsWith('.dart') || f.path.endsWith('.json'))
            .toList()
          ..sort((a, b) => a.path.compareTo(b.path));
    for (final file in files) {
      sources[file.path] = sha256.convert(file.readAsBytesSync()).toString();
    }
  }
  final sourceDigest = sha256
      .convert(utf8.encode(jsonEncode(sources)))
      .toString();
  final cases = <(String, int, PolicyRun)>[];
  void add(
    int days,
    int visits,
    BonusPolicy bonus,
    ResetPolicy reset, {
    PurchasePolicy purchase = PurchasePolicy.bestPayback,
    ContractPolicy contracts = ContractPolicy.allReady,
    int? breakDay,
    int breakHours = 0,
  }) {
    final id =
        '$days/$visits/${bonus.name}/${reset.name}/${purchase.name}/${contracts.name}/$breakHours';
    cases.add((
      id,
      days,
      PolicyRun(
        content,
        visitsPerDay: visits,
        bonus: bonus,
        resetPolicy: reset,
        purchasePolicy: purchase,
        contractPolicy: contracts,
        breakStartsDay: breakDay,
        breakHours: breakHours,
      ),
    ));
  }

  for (final days in quick ? [3] : [30, 90]) {
    for (final visits in quick ? [1] : [1, 3, 6]) {
      for (final bonus
          in quick
              ? [BonusPolicy.requiredCalibrationsOnly]
              : BonusPolicy.values) {
        for (final reset
            in quick ? [ResetPolicy.atVisits] : ResetPolicy.values) {
          add(days, visits, bonus, reset);
        }
      }
      if (!quick) {
        for (final purchase in [
          PurchasePolicy.lowestTierFirst,
          PurchasePolicy.highestTierFirst,
        ]) {
          add(
            days,
            visits,
            BonusPolicy.requiredCalibrationsOnly,
            ResetPolicy.atVisits,
            purchase: purchase,
          );
        }
        for (final contracts in [
          ContractPolicy.surveysOnly,
          ContractPolicy.oneReadyPerVisit,
          ContractPolicy.pursueWithSeason,
        ]) {
          add(
            days,
            visits,
            BonusPolicy.requiredCalibrationsOnly,
            ResetPolicy.atVisits,
            contracts: contracts,
          );
        }
      }
    }
  }
  if (!quick) {
    for (final hours in [24, 48, 72, 120]) {
      add(
        90,
        3,
        BonusPolicy.requiredCalibrationsOnly,
        ResetPolicy.atVisits,
        breakDay: 10,
        breakHours: hours,
      );
    }
  }
  final target = File(
    '../../release/balance/${quick ? 'smoke' : 'long-horizon'}-v4-policies.json',
  );
  final rows = <Map<String, dynamic>>[];
  if (resume && target.existsSync()) {
    final old = jsonDecode(target.readAsStringSync()) as Map;
    if (old['source_digest'] != sourceDigest) {
      throw StateError(
        'Refusing to combine policies from different source inputs.',
      );
    }
    rows.addAll(
      (old['policies'] as List).map((e) => Map<String, dynamic>.from(e)),
    );
  }
  final completed = rows.map((r) => r['case_id']).toSet();
  final watch = Stopwatch()..start();
  target.parent.createSync(recursive: true);
  void save() {
    final temporary = File('${target.path}.new');
    temporary.writeAsStringSync(
      const JsonEncoder.withIndent('  ').convert({
            'generated_at_utc': DateTime.now().toUtc().toIso8601String(),
            'current_invocation_milliseconds': watch.elapsedMilliseconds,
            'status': rows.length == cases.length ? 'complete' : 'running',
            'planned_cases': cases.length,
            'completed_cases': rows.length,
            'experiment':
                'Exact production-engine virtual policies, not observed players',
            'first_session_minutes': 30,
            'subsequent_session_minutes': 5,
            'manual_pre_automation_decision_seconds': 5,
            'seed': 'policy-audit-01',
            'paid_power': false,
            'limitations': [
              'Reproducible policies are not a proof of optimal play or measured retention.',
              'Chapter timestamps are upper bounds at evaluation boundaries, not sub-event completion times.',
              'The none policy uses no Focus or Support; all campaign goals remain eligible.',
              'The legacy-named requiredCalibrationsOnly policy voluntarily completes three accessible calibrations; it is not zero-Focus and they are no longer required.',
              'Ad-route receipts are synthetic deterministic fixtures of successful delivery, not provider verification or observed fill. Their only purpose is economic route parity.',
              'Dossier automation and best-payback choices are selected without human learning time.',
              'Only retained ready daily contracts can be claimed; allReady does not manufacture three completions per day.',
              'The ordinary policy reads one unread archive per action window. The pursueWithSeason policy also reflects on an existing archive for unfinished archive goals and explicitly binds/claims real seasonal alternatives for other unfinished goals. It does not fabricate instant completions.',
              'Only one pass is selected; its archive is explicitly resumed at a later visit.',
              'All 12 dossier sinks are attempted. Five optional plan slots and six decorations are a separate 550-Note budget, not purchased.',
              'No human session count, D30 retention, real ad completion or elapsed seasonal observation is inferred.',
            ],
            'source_digest': sourceDigest,
            'source_sha256': sources,
            'policies': rows,
          }) +
          '\n',
      flush: true,
    );
    temporary.renameSync(target.path);
  }

  save();
  for (final (id, days, run) in cases) {
    if (completed.contains(id)) continue;
    final timer = Stopwatch()..start();
    final row = run.run(days: days)
      ..['horizon_days'] = days
      ..['case_id'] = id
      ..['runtime_milliseconds'] = timer.elapsedMilliseconds;
    rows.add(row);
    save();
    stdout.writeln(
      '${rows.length}/${cases.length} $id: chapters ${row['chapters_completed']}, Notes ${row['notes_earned']} (${timer.elapsedMilliseconds}ms)',
    );
  }
}
