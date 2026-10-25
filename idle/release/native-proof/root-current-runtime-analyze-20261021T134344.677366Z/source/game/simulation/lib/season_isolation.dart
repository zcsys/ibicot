import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';

/// Controlled engine isolation, not account-service or client-binding proof.
Map<String, dynamic> seasonIsolation(
  SeasonDefinition definition,
  GameState veteran, {
  required bool offline,
}) {
  final newcomer = GameState.initial();
  final beforeNew = jsonEncode(newcomer.toJson());
  final beforeOld = jsonEncode(veteran.toJson());
  final start = DateTime.utc(2026, 10, 16);
  final engine = SeasonEngine(definition);
  SeasonState fresh() => engine
      .configurePolicy(
        SeasonState.initial(
          definition,
          SeasonSchedule(start),
          start,
          runId: 'isolation-matched-run',
        ),
        automatic: true,
      )
      .state;
  var a = fresh(), b = fresh();
  final rows = <Map<String, dynamic>>[];
  for (var day = 1; day <= 30; day++) {
    final at = start.add(Duration(days: day));
    final ra = engine.advanceTo(a, at, offline: offline);
    final rb = engine.advanceTo(b, at, offline: offline);
    if (!ra.accepted || !rb.accepted)
      throw StateError('Season advance rejected');
    a = ra.state;
    b = rb.state;
    if (jsonEncode(a.toJson()) != jsonEncode(b.toJson())) {
      throw StateError('Main profile influenced isolated season state');
    }
    if ([1, 7, 28, 29, 30].contains(day)) {
      rows.add({
        'day': day,
        'phase': a.phase.name,
        'lifetime_micros': '${a.fleet.lifetimeMicros}',
        'counts': a.fleet.counts,
        'paired_state_sha256': sha256
            .convert(utf8.encode(jsonEncode(a.toJson())))
            .toString(),
      });
    }
  }
  final frozen = a.fleet.lifetimeMicros;
  a = engine.resumeArchive(a, start.add(const Duration(days: 30))).state;
  b = engine.resumeArchive(b, start.add(const Duration(days: 30))).state;
  a = engine
      .advanceTo(a, start.add(const Duration(days: 31)), offline: offline)
      .state;
  b = engine
      .advanceTo(b, start.add(const Duration(days: 31)), offline: offline)
      .state;
  if (jsonEncode(a.toJson()) != jsonEncode(b.toJson()) ||
      jsonEncode(newcomer.toJson()) != beforeNew ||
      jsonEncode(veteran.toJson()) != beforeOld ||
      a.fleet.lifetimeMicros <= frozen) {
    throw StateError('Archive isolation or main immutability failed');
  }
  var powerInjectionRejected = false;
  try {
    SeasonFleet.fromJson({...a.fleet.toJson(), 'charts': '${veteran.charts}'});
  } on FormatException {
    powerInjectionRejected = true;
  }
  if (!powerInjectionRejected) throw StateError('Season accepted main power');
  return {
    'cadence': offline ? 'daily_offline_returns' : 'continuous_online',
    'new_account_charts': '${newcomer.charts}',
    'veteran_account_charts': '${veteran.charts}',
    'veteran_lifetime_micros': '${veteran.lifetimeMicros}',
    'main_profiles_differ': beforeNew != beforeOld,
    'main_profiles_unchanged': true,
    'paired_event_states_identical': true,
    'main_power_injection_rejected': powerInjectionRejected,
    'archive_resume_day31_lifetime_micros': '${a.fleet.lifetimeMicros}',
    'observations': rows,
  };
}
