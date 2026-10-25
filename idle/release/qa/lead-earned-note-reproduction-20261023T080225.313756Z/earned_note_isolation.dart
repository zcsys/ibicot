import 'dart:convert';
import 'dart:io';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

var assertions = 0;
void require(bool condition, String message) {
  assertions++;
  if (!condition) throw StateError(message);
}
String snapshot(GameState state) => jsonEncode(state.toJson());

void main() {
  const core = TideglassEngine();
  var earned = GameState.initial();
  final ledger = <Map<String, Object>>[];
  for (var n = 1; n <= 10; n++) {
    earned = core.advance(earned, const Duration(hours: 8)).state;
    require(earned.completedSurveys == 1, 'one actually generated Survey');
    final before = earned;
    final collected = core.collectSurveys(earned);
    require(collected.accepted, 'actual collection accepted');
    earned = collected.state;
    require(earned.surveyNotes == BigInt.from(n * 10), 'ten Notes per Survey');
    require(earned.walletMicros == before.walletMicros &&
        earned.lifetimeMicros == before.lifetimeMicros,
        'collection cannot export money');
    require(!core.collectSurveys(earned).accepted, 'duplicate empty collection refused');
    ledger.add({'survey': n, 'notes': earned.surveyNotes.toString(),
      'elapsed_micros': earned.elapsedMicros.toString()});
  }
  final funded = snapshot(earned);
  final unlocked = CampaignProgress(completed: {'chapter.01', 'chapter.02', 'chapter.03'});
  final rows = <Map<String, Object>>[];
  final families = <String, int>{};
  for (var n = 1; n <= 12; n++) {
    final id = 'challenge.${n.toString().padLeft(2, '0')}';
    final raw = Map<String, dynamic>.from(jsonDecode(
      File('../content/challenges/$id.json').readAsStringSync()));
    final definition = ChallengeDefinition.fromJson(raw);
    families.update(definition.family, (v) => v + 1, ifAbsent: () => 1);
    require(definition.id == id, 'actual content identity');
    final underfunded = earned.copyWith(surveyNotes: BigInt.from(99));
    final refused = DossierCollection().open(underfunded, unlocked, definition);
    require(!refused.accepted && snapshot(refused.main) == snapshot(underfunded) &&
        refused.dossiers.owned.isEmpty, '99 Notes refuses without state mutation');
    final opened = DossierCollection().open(earned, unlocked, definition);
    require(opened.accepted && opened.main.surveyNotes == BigInt.zero,
        '100 actually earned Notes buys exact dossier');
    final expected = earned.toJson();
    expected['survey_notes'] = '0';
    expected['revision'] = earned.revision + 1;
    require(jsonEncode(expected) == snapshot(opened.main),
        'entry changes only Note debit and revision');
    require(opened.dossiers.owned.length == 1 && opened.dossiers.owned.contains(id),
        'ownership recorded exactly once');
    final engine = ChallengeEconomy(definition);
    final played = engine.advanceRun(opened.dossiers.active!.copyWith(automatic: true),
        const Duration(minutes: 2));
    require(played.fleet.lifetimeMicros > BigInt.zero, 'actual separate fleet earned');
    final active = opened.dossiers.withRun(played, definition);
    final beforeControl = snapshot(opened.main);
    final restarted = active.restart(definition);
    require(restarted.active!.fleet.walletMicros == BigInt.zero &&
        restarted.active!.fleet.lifetimeMicros == BigInt.zero &&
        restarted.active!.fleet.counts.join(',') == '1,0,0,0,0',
        'restart discards funded challenge economy');
    require(restarted.owned.contains(id) && snapshot(opened.main) == beforeControl,
        'restart preserves ownership and all main economic state');
    final left = active.leave();
    require(left.active == null && left.owned.contains(id) &&
        snapshot(opened.main) == beforeControl,
        'exit discards funded challenge without export');
    final decoded = DossierCollection.fromJson(left.toJson());
    final reopened = decoded.open(opened.main, unlocked, definition);
    require(reopened.accepted && snapshot(reopened.main) == beforeControl &&
        reopened.dossiers.active!.fleet.walletMicros == BigInt.zero &&
        reopened.dossiers.active!.fleet.lifetimeMicros == BigInt.zero,
        'serialized ownership reopens free with a fresh isolated fleet');
    require(snapshot(earned) == funded, 'shared funded main input remains immutable');
    rows.add({'id': id, 'family': definition.family,
      'earned_notes_before': earned.surveyNotes.toString(),
      'entry_notes_after': opened.main.surveyNotes.toString(),
      'scenario_earned_micros_discarded': played.fleet.lifetimeMicros.toString(),
      'exit_restart_reopen_isolated': true});
  }
  require(families.length == 3 && families.values.every((v) => v == 4),
      'three actual families with four dossiers each');
  stdout.writeln(jsonEncode({'passed': true, 'assertions': assertions,
    'note_source': 'ten actual eight-hour core advances and Survey collections',
    'chapter_unlock': 'explicit chapter-three fixture; no natural campaign timing claim',
    'limits': 'Pure production core/progression; no new UI/native/persistence execution; existing reachability tests not repeated.',
    'survey_ledger': ledger, 'rows': rows}));
}
