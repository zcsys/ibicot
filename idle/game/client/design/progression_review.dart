import 'dart:convert';
import 'dart:io';

import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_core/tideglass_core.dart';

Map<String, dynamic> read(String path) =>
    Map<String, dynamic>.from(jsonDecode(File(path).readAsStringSync()));
bool rejected(void Function() action) {
  try {
    action();
    return false;
  } on FormatException {
    return true;
  }
}

void main() {
  final paths = List.generate(
    12,
    (i) =>
        'game/content/challenges/challenge.${(i + 1).toString().padLeft(2, '0')}.json',
  );
  final dossiers = paths
      .map((p) => ChallengeDefinition.fromJson(read(p)))
      .toList();
  final altered = read(paths.first)..['construction_mode'] = 'unknown-mode';
  final invalid = read('game/content/progression/campaign.json');
  (invalid['chapters'] as List).first['id'] = 'chapter.invalid';
  final normal = Campaign(
    read('game/content/progression/campaign.json'),
    dossiers,
  );
  var immutable = false;
  try {
    normal.chapters.first['id'] = 'chapter.mutated';
  } on UnsupportedError {
    immutable = true;
  }
  final unlocked = CampaignProgress(
    completed: {'chapter.01', 'chapter.02', 'chapter.03'},
  );
  final poor = GameState(surveyNotes: BigInt.from(99));
  final refused = DossierCollection().open(poor, unlocked, dossiers.first);
  final paid = DossierCollection().open(
    GameState(surveyNotes: BigInt.from(150)),
    unlocked,
    dossiers.first,
  );
  final replay = paid.dossiers.leave().open(
    paid.main,
    unlocked,
    dossiers.first,
  );
  final conflict = paid.dossiers.open(paid.main, unlocked, dossiers[1]);
  var nestedImmutable = false;
  final nested = Campaign(
    read('game/content/progression/campaign.json'),
    dossiers,
  );
  try {
    (nested.chapters.first['objectives'] as List).first['value'] = 0;
  } on UnsupportedError {
    nestedImmutable = true;
  }
  final bothOwned = DossierCollection(
    owned: {dossiers[0].id, dossiers[1].id},
    active: ChallengeEconomy(dossiers[0]).newRun(),
  );
  final findings = {
    'unknown_construction_mode_rejected': rejected(
      () => ChallengeDefinition.fromJson(altered),
    ),
    'invalid_campaign_identity_rejected': rejected(
      () => Campaign(invalid, dossiers),
    ),
    'direct_progress_invalid_prefix_rejected': rejected(
      () => CampaignProgress(completed: {'chapter.06'}),
    ),
    'nested_campaign_maps_immutable': immutable,
    'nested_objective_maps_immutable': nestedImmutable,
    'insufficient_notes_leave_original_state':
        !refused.accepted &&
        identical(refused.main, poor) &&
        refused.dossiers.owned.isEmpty,
    'first_entry_spends_exactly_100_notes':
        paid.accepted &&
        paid.main.surveyNotes == BigInt.from(50) &&
        paid.dossiers.owned.contains(dossiers.first.id),
    'paid_entry_increments_core_revision': paid.main.revision == 1,
    'restart_different_active_requires_explicit_replacement': rejected(
      () => bothOwned.restart(dossiers[1]),
    ),
    'owned_replay_is_free':
        replay.accepted && replay.main.surveyNotes == paid.main.surveyNotes,
    'active_replacement_needs_confirmation':
        !conflict.accepted && identical(conflict.dossiers, paid.dossiers),
    'unearned_completion_rejected': rejected(
      () => paid.dossiers.withRun(
        paid.dossiers.active!.copyWith(complete: true),
        dossiers.first,
      ),
    ),
  };
  print(const JsonEncoder.withIndent('  ').convert(findings));
  if (findings.values.any((accepted) => !accepted)) exitCode = 1;
}
