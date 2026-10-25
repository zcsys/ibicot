import 'dart:convert';
import 'dart:io';

import '../core/lib/tideglass_core.dart';
import '../mobile/lib/help_content.dart';

void main(List<String> args) {
  var checks = 0;
  void check(bool value, String label) {
    checks++;
    if (!value) throw StateError(label);
  }

  void immutable(void Function() mutation, String label) {
    var denied = false;
    try {
      mutation();
    } on UnsupportedError {
      denied = true;
    }
    check(denied, label);
  }

  final ids = <String>{};
  check(
    HelpContent.articles.length == HelpTopic.values.length,
    'all topic coverage',
  );
  check(
    HelpContent.articles.map((a) => a.topic).toSet().length ==
        HelpTopic.values.length,
    'topic uniqueness',
  );
  immutable(() => HelpContent.articles.clear(), 'immutable catalogue');
  for (final article in HelpContent.articles) {
    check(
      article.title.isNotEmpty &&
          article.summary.isNotEmpty &&
          article.sections.isNotEmpty,
      'nonempty article',
    );
    check(
      article.actions.toSet().length == article.actions.length,
      'unique actions',
    );
    immutable(() => article.sections.clear(), 'immutable sections');
    immutable(() => article.actions.clear(), 'immutable actions');
    for (final section in article.sections) {
      check(ids.add(section.id), 'stable unique section');
      check(
        section.title.isNotEmpty &&
            section.paragraphs.isNotEmpty &&
            section.paragraphs.every((p) => p.isNotEmpty),
        'nonempty copy',
      );
      immutable(() => section.paragraphs.clear(), 'immutable paragraphs');
    }
  }
  const engine = TideglassEngine();
  final initial = GameState.initial();
  check(initial.counts[0] == 1, 'gifted skiff');
  check(
    TideglassEngine.firstPrestigeMicros == BigInt.from(10).pow(15),
    'first billion Radiance',
  );
  for (final n in [25, 50, 75, 100]) {
    check(
      engine.milestoneMultiplier(n) == engine.milestoneMultiplier(n - 1) * 2,
      'whole tier double',
    );
  }
  final offline = engine
      .advance(
        initial,
        const Duration(hours: 96),
        offline: true,
        autoBuy: false,
      )
      .state;
  check(
    offline.lifetimeMicros - initial.lifetimeMicros ==
        BigInt.from((24 * 3600 + 48 * 3600 ~/ 4) * 1000000),
    'one absence diminishing cap',
  );
  check(
    offline.focusCharges == 12 && offline.completedSurveys == 3,
    'stored capacities',
  );
  final collected = engine.collectSurveys(offline);
  check(
    collected.accepted &&
        collected.state.surveyNotes - offline.surveyNotes == BigInt.from(30),
    'three surveys ten Notes',
  );
  check(
    TideglassEngine.focusCycleMicros == BigInt.from(7200000000),
    'two hour focus',
  );
  check(
    TideglassEngine.surveyCycleMicros == BigInt.from(28800000000),
    'eight hour survey',
  );
  final utc = DateTime.utc(2026, 10, 21);
  var daily = engine
      .refreshContracts(
        initial,
        utc,
        accountSeed: 'independent-help-clock',
        utcOffsetMinutes: 180,
        availableDiscoveryKinds: ['archive'],
      )
      .state;
  final originalDay = daily.daily.dayHighWater;
  for (var slot = 0; slot < 6; slot++) {
    final result = engine.claimSupportToken(
      daily,
      accountDay: originalDay,
      slot: slot,
      sourceId: engine.briefingSourceId(daily, slot),
      route: 'briefing',
    );
    check(result.accepted, 'current day grant');
    daily = result.state;
  }
  check(
    !engine.refreshContracts(daily, utc, utcOffsetMinutes: 0).accepted,
    'fixed offset rejects travel reassignment',
  );
  final forward = engine.refreshContracts(
    daily,
    utc.add(const Duration(days: 1)),
    availableDiscoveryKinds: ['archive'],
  );
  check(
    forward.accepted && forward.state.daily.dayHighWater == originalDay + 1,
    'caller UTC forward accepted',
  );
  check(
    forward.state.elapsedMicros == daily.elapsedMicros,
    'clock forward need not imply independently measured elapsed',
  );
  var future = forward.state;
  var grants = 0;
  for (var slot = 0; slot < 6; slot++) {
    final result = engine.claimSupportToken(
      future,
      accountDay: future.daily.dayHighWater,
      slot: slot,
      sourceId: engine.briefingSourceId(future, slot),
      route: 'briefing',
    );
    check(result.accepted, 'forward-day free slot is grantable');
    future = result.state;
    grants++;
  }
  final backward = engine.refreshContracts(
    future,
    utc,
    availableDiscoveryKinds: ['archive'],
  );
  check(
    backward.accepted && backward.state.daily.dayHighWater == originalDay + 1,
    'high water rejects rollback',
  );
  final copy = HelpContent.articles
      .expand((a) => a.sections)
      .expand((s) => s.paragraphs)
      .join(' ');
  check(
    !copy.contains('clock change does not create extra days of rewards') &&
        !copy.contains('changing the device clock is not a reward mechanic') &&
        copy.contains('turning the clock back does not replay an earlier day'),
    'help qualifies clock behavior',
  );
  final result = {
    'status': 'behavior_probes_passed_copy_corrected',
    'checks': checks,
    'topic_count': HelpContent.articles.length,
    'section_count': ids.length,
    'copy_finding': 'HELP001 repaired in copy; forward-clock behavior remains explicitly unverified.',
    'forward_utc_observation': {
      'original_account_day': originalDay,
      'future_account_day': future.daily.dayHighWater,
      'elapsed_before': '${daily.elapsedMicros}',
      'elapsed_after': '${future.elapsedMicros}',
      'next_day_free_slots_granted': grants,
    },
    'limits': 'Pure content/core evidence. No Flutter, native clocks, store/provider or physical screen-reader run.',
  };
  File(args.single).writeAsStringSync(
    '${const JsonEncoder.withIndent('  ').convert(result)}\n',
  );
  stdout.writeln(jsonEncode(result));
}
