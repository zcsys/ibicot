import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const engine = TideglassEngine();
final million = BigInt.from(1000000);
var assertions = 0;
final results = <String, dynamic>{};
void check(bool x, String name) {
  assertions++;
  if (!x) throw StateError(name);
}

void equal(dynamic a, dynamic b, String name) =>
    check(jsonEncode(a) == jsonEncode(b), name);
Map<String, dynamic> semantic(GameState s) => s.toJson()..remove('revision');
List<dynamic> events(TransitionResult r) =>
    r.events.map((e) => e.toJson()..remove('id')).toList();
GameState accept(TransitionResult r, String name) {
  check(r.accepted, '$name: ${r.reason}');
  return r.state;
}

Map<String, dynamic> summary(GameState s) => {
      'elapsed_micros': s.elapsedMicros.toString(),
      'charts': s.charts.toString(),
      'entitlement': engine.prestigeEntitlement(s.lifetimeMicros).toString(),
      'lifetime_micros': s.lifetimeMicros.toString(),
      'wallet_micros': s.walletMicros.toString(),
      'counts': s.counts,
      'auto_buy': s.autoBuyEnabled,
      'recharts': s.rechartCount,
      'notes': s.surveyNotes.toString(),
      'semantic_sha256':
          sha256.convert(utf8.encode(jsonEncode(semantic(s)))).toString()
    };
GameState advance(GameState s, int micros, bool offline) => accept(
    engine.advance(s, Duration(microseconds: micros),
        offline: offline,
        offlineElapsedBefore: Duration(microseconds: s.elapsedMicros.toInt())),
    'advance');
GameState firstReset(bool offline) {
  var s = GameState.initial();
  check(!engine.setAutoBuy(s, true).accepted, 'initial autobuy locked');
  check(
      s.automationPlans.length == 1 &&
          !s.selectedAutomationPlan.autoResetEnabled,
      'free base / opted out initially');
  var loops = 0;
  while (s.lifetimeMicros < TideglassEngine.firstPrestigeMicros) {
    check(loops++ < 5000, 'bounded first session');
    final tier = engine.chooseAutoBuyTier(s),
        cost = engine.priceMicros(tier, s.counts[tier]);
    if (s.walletMicros >= cost) {
      s = accept(engine.buy(s, tier, 1), 'attentive policy purchase');
      continue;
    }
    final denominator = engine.outputPerSecond(s).raw * BigInt.from(400);
    BigInt wait(BigInt delta) => ceilDivide(
        delta * Fixed.scale * BigInt.from(400) - s.earningRemainder,
        denominator);
    final purchase = wait(cost - s.walletMicros),
        gate = wait(TideglassEngine.firstPrestigeMicros - s.lifetimeMicros);
    s = advance(s, (purchase < gate ? purchase : gate).toInt(), offline);
  }
  check(engine.prestigeAward(s) == BigInt.from(10), 'first earned award10');
  s = accept(engine.rechart(s), 'earned first rechart');
  s = accept(engine.setAutoBuy(s, true), 'free autobuy10');
  check(s.surveyNotes == BigInt.zero, 'base costs no Notes');
  return s;
}

GameState reach(GameState s, int target, bool offline) {
  final threshold = engine.lifetimeForCharts(BigInt.from(target));
  var chunks = 0;
  while (s.lifetimeMicros < threshold) {
    check(chunks++ < 1000, 'bounded target progress');
    final next = advance(s, 60000000, offline);
    if (next.lifetimeMicros < threshold) {
      s = next;
      continue;
    }
    var lo = 0, hi = 60000000;
    while (lo + 1 < hi) {
      final mid = (lo + hi) ~/ 2;
      if (advance(s, mid, offline).lifetimeMicros >= threshold) {
        hi = mid;
      } else {
        lo = mid;
      }
    }
    check(advance(s, hi - 1, offline).lifetimeMicros < threshold,
        'one micro before target$target');
    s = advance(s, hi, offline);
  }
  check(engine.prestigeEntitlement(s.lifetimeMicros) == BigInt.from(target),
      'first passage target$target');
  return s;
}

Map<String, dynamic> natural(bool offline) {
  final rows = <String, dynamic>{};
  var s = firstReset(false);
  rows['ten'] = summary(s);
  s = accept(engine.rechart(reach(s, 24, offline)), 'earned24');
  rows['twenty_four'] = summary(s);
  check(
      engine.synergyMultiplier(s, 3).raw == Fixed.scale &&
          engine.synergyMultiplier(s, 4).raw == Fixed.scale,
      'synergy locked24');
  s = accept(engine.rechart(reach(s, 25, offline)), 'earned25');
  rows['twenty_five'] = summary(s);
  check(engine.synergyMultiplier(s, 3).raw > Fixed.scale, 'synergy unlock25');
  s = advance(s, 600000000, offline);
  check(s.counts[3] > 0 && s.counts[4] > 0,
      'free automatic rebuild reaches target tiers');
  check(s.elapsedMicros < TideglassEngine.fullOfflineMicros,
      'trace within full-rate window');
  rows['rebuilt'] = summary(s);
  rows['final_state'] = semantic(s);
  return rows;
}

void synergy() {
  final before = GameState(
      counts: [25, 75, 10, 10, 10],
      charts: BigInt.from(24),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(25)),
      walletMicros: BigInt.from(1000000000) * million);
  for (var t = 0; t < 5; t++) {
    check(engine.synergyMultiplier(before, t).raw == Fixed.scale,
        'matrix locked24 tier$t');
  }
  final s = before.copyWith(charts: BigInt.from(25));
  for (var t = 0; t < 3; t++) {
    check(engine.synergyMultiplier(s, t).raw == Fixed.scale,
        'early target unchanged$t');
  }
  check(
      engine.synergyMultiplier(s, 3).raw ==
          Fixed.scale * BigInt.from(14) ~/ BigInt.from(10),
      'exact S4=1.4 with logs1,2');
  check(
      engine.synergyMultiplier(s, 4).raw ==
          Fixed.scale * BigInt.from(16) ~/ BigInt.from(10),
      'exact S5=1.6 with logs1,2');
  final rows = <dynamic>[];
  for (var source = 0; source < 2; source++) {
    final predicted = engine.marginalOutputPerSecond(s, source).raw,
        after = accept(engine.buy(s, source, 1), 'real low-tier purchase');
    final observed =
        engine.outputPerSecond(after).raw - engine.outputPerSecond(s).raw;
    check(predicted == observed, 'network forecast equals actual purchase');
    for (final target in [3, 4]) {
      check(
          engine.producerOutputPerSecond(after, target).raw >
              engine.producerOutputPerSecond(s, target).raw,
          'positive edge$source->$target');
    }
    rows.add({
      'source_tier': source + 1,
      'predicted_raw': predicted.toString(),
      'observed_raw': observed.toString()
    });
  }
  results['seeded_matrix'] = {
    'counts': s.counts,
    'charts': '25',
    'S4': '1.4',
    'S5': '1.6',
    'purchases': rows
  };
}

void priorities() {
  final rows = <dynamic>[];
  for (final order in [
    [1, 0, 4, 3, 2],
    [4, 3, 2, 1, 0],
    [0, 1, 2, 3, 4]
  ]) {
    var s = GameState(
        counts: [10, 10, 10, 10, 1],
        charts: BigInt.from(100),
        lifetimeMicros: engine.lifetimeForCharts(BigInt.from(100)),
        autoBuyEnabled: true);
    s = accept(
        engine.saveAutomationPlan(
            s,
            AutomationPlan(
                id: 'plan.base',
                name: 'Synthetic priority',
                purchasePolicy: 'priority',
                tierPriority: order)),
        'free priority');
    const duration = Duration(hours: 2);
    final online = engine.advance(s, duration),
        offline = engine.advance(s, duration, offline: true);
    equal(online.state.toJson(), offline.state.toJson(),
        'priority full-rate state parity');
    equal(events(online), events(offline), 'priority ordered events parity');
    check(
        online.events
                .firstWhere((e) => e.kind == 'purchase')
                .details['tier_index'] ==
            order.first,
        'actual first tier follows priority');
    var split = s, offset = 0;
    final trace = <dynamic>[];
    for (final length in [1, 9000001, 120000002, 7070999996]) {
      final step = engine.advance(split, Duration(microseconds: length),
          offline: true, offlineElapsedBefore: Duration(microseconds: offset));
      split = accept(step, 'partition');
      offset += length;
      trace.addAll(events(step));
    }
    check(offset == duration.inMicroseconds, 'exact partition');
    equal(semantic(split), semantic(online.state), 'partition economic state');
    equal(trace, events(online), 'partition ordered semantic events');
    rows.add({
      'priority': order,
      'purchase_events':
          online.events.where((e) => e.kind == 'purchase').length,
      'final': summary(online.state)
    });
  }
  results['seeded_priority_parity'] = rows;
}

void resets() {
  final p = AutomationPlan(
      id: 'plan.base',
      name: 'Synthetic reset',
      autoResetEnabled: true,
      minimumAdditionalCharts: BigInt.from(5),
      minimumRunSeconds: 600);
  final early = GameState(
      charts: BigInt.from(99),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)));
  check(!engine.saveAutomationPlan(early, p).accepted, '99 gate');
  var s = early.copyWith(charts: BigInt.from(100));
  check(engine.advance(s, const Duration(seconds: 600)).state.rechartCount == 0,
      'default opt-out');
  s = accept(engine.saveAutomationPlan(s, p), '100 opt-in');
  final before = engine.advance(s, const Duration(microseconds: 599999999));
  check(before.state.rechartCount == 0, 'time one micro short');
  final exact = engine.advance(before.state, const Duration(microseconds: 1));
  check(exact.state.rechartCount == 1 && exact.state.charts == BigInt.from(105),
      'time exact boundary');
  final full = engine.advance(s, const Duration(seconds: 600)),
      away = engine.advance(s, const Duration(seconds: 600), offline: true);
  equal(
      full.state.toJson(), away.state.toJson(), 'reset full-rate state parity');
  equal(events(full), events(away), 'reset event parity');
  equal(semantic(exact.state), semantic(full.state),
      'reset endpoint partition parity');
  final missing = s.copyWith(
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)) - BigInt.one,
      elapsedMicros: BigInt.from(600) * million);
  check(engine.advance(missing, Duration.zero).state.rechartCount == 0,
      'award one micro short blocks');
  final crossed =
      engine.advance(missing, const Duration(microseconds: 1), offline: true);
  check(
      crossed.state.rechartCount == 1 &&
          crossed.state.charts == BigInt.from(105),
      'offline award crossing');
  check(crossed.events.where((e) => e.kind == 'rechart').length == 1,
      'one reset event');
  final disabled = accept(
      engine.saveAutomationPlan(
          s, AutomationPlan(id: 'plan.base', name: 'Disabled')),
      'opt-out again');
  check(
      engine
              .advance(disabled, const Duration(seconds: 601), offline: true)
              .state
              .rechartCount ==
          0,
      'explicit offline opt-out');
  results['seeded_reset_conditions'] = {
    'minimum_run_seconds': 600,
    'minimum_additional_charts': '5',
    'time_boundary': summary(full.state),
    'award_boundary': summary(crossed.state),
    'default_opt_in': false
  };
}

Future<void> slots() async {
  var s = GameState(
      charts: BigInt.from(100),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)),
      surveyNotes: BigInt.from(250));
  final free = accept(
      engine.saveAutomationPlan(
          s.copyWith(surveyNotes: BigInt.zero),
          AutomationPlan(
              id: 'plan.base',
              name: 'Free',
              purchasePolicy: 'priority',
              tierPriority: [1, 0, 4, 3, 2])),
      'zero Note base edit');
  check(free.surveyNotes == BigInt.zero && free.extraPlanSlots == 0,
      'base is free');
  check(!engine.buyPlanSlot(s.copyWith(surveyNotes: BigInt.from(49))).accepted,
      '49 cannot pay50');
  check(
      !engine
          .buyPlanSlot(
              GameState.initial().copyWith(surveyNotes: BigInt.from(250)))
          .accepted,
      'slots gated10');
  check(
      !engine
          .saveAutomationPlan(
              s, AutomationPlan(id: 'extra', name: 'No capacity'))
          .accepted,
      'extra requires slot');
  for (var i = 1; i <= 5; i++) {
    final before = s;
    s = accept(engine.buyPlanSlot(s), 'buy slot$i');
    check(before.surveyNotes - s.surveyNotes == BigInt.from(50),
        'exact50 slot$i');
    check(
        before.walletMicros == s.walletMicros &&
            before.lifetimeMicros == s.lifetimeMicros &&
            before.charts == s.charts,
        'slot leaves earnings$i');
    s = accept(
        engine.saveAutomationPlan(
            s,
            AutomationPlan(
                id: 'plan.extra.$i',
                name: 'Synthetic extra$i',
                purchasePolicy: 'priority',
                tierPriority: [4, 3, 2, 1, 0])),
        'save extra$i');
  }
  check(s.surveyNotes == BigInt.zero && s.automationPlans.length == 6,
      'five extras250');
  check(!engine.buyPlanSlot(s.copyWith(surveyNotes: BigInt.from(50))).accepted,
      'sixth funded slot rejected');
  s = accept(engine.selectAutomationPlan(s, 'plan.extra.5'), 'selection');
  final after = accept(engine.rechart(s), 'retain plans reset');
  equal(
      after.automationPlans.map((p) => p.toJson()).toList(),
      s.automationPlans.map((p) => p.toJson()).toList(),
      'plans retained reset');
  check(
      after.extraPlanSlots == 5 &&
          after.selectedAutomationPlanId == 'plan.extra.5',
      'capacity and selection retained');
  final dir = await Directory.systemTemp
      .createTemp('tideglass-platform-clause-synthetic-');
  try {
    final digest =
        sha256.convert(File('../../economy.json').readAsBytesSync()).toString();
    SaveRepository repo() => SaveRepository(dir,
        economicVersion: economyVersion,
        economicDigest: digest,
        validatePayload: (p) =>
            GameState.fromJson(Map<String, dynamic>.from(p['core'] as Map)));
    final writer = repo();
    await writer.load();
    await writer.save(
        {'core': after.toJson(), 'preferences': <String, dynamic>{}},
        settledThrough: DateTime.utc(2026, 10, 21));
    final loaded = (await repo().load()).snapshot!,
        restored = GameState.fromJson(
            Map<String, dynamic>.from(loaded.payload['core'] as Map));
    equal(restored.toJson(), after.toJson(),
        'actual repository reopen all plan fields');
    results['seeded_saved_slots'] = {
      'notes_spent': '250',
      'free_base': true,
      'extra_slots': 5,
      'selected': restored.selectedAutomationPlanId,
      'plans': restored.automationPlans.map((p) => p.toJson()).toList(),
      'durable_reopen_equal': true,
      'synthetic_directory_deleted_after_test': true
    };
  } finally {
    await dir.delete(recursive: true);
  }
}

void receiptParity() {
  final epoch = DateTime.utc(2026, 10, 21, 12);
  var state = GameState(
      counts: [10, 10, 10, 10, 1],
      charts: BigInt.from(100),
      lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)),
      autoBuyEnabled: true);
  state = accept(
      engine.refreshContracts(state, epoch,
          accountSeed: 'platform-clause-synthetic', utcOffsetMinutes: 0),
      'synthetic calendar');
  state = accept(
      engine.saveAutomationPlan(
          state,
          AutomationPlan(
              id: 'plan.base',
              name: 'Receipt plan',
              purchasePolicy: 'priority',
              tierPriority: [4, 3, 2, 1, 0],
              autoResetEnabled: true,
              minimumAdditionalCharts: BigInt.from(5),
              minimumRunSeconds: 600)),
      'receipt priority/reset plan');
  const duration = Duration(hours: 2);
  final request = OfflineSettlementRequest(
      sequence: state.nextSettlementSequence,
      fromUtc: epoch,
      throughUtc: epoch.add(duration));
  final online = engine.advance(state, duration);
  final offline = engine.advance(state, duration,
      offline: true, offlineSettlement: request);
  check(online.accepted && offline.accepted, 'actual receipt advance accepted');
  Map<String, dynamic> projected(GameState value) {
    final json = semantic(value);
    final support = value.support.toJson();
    json['support'] = {
      for (final key in [
        'remaining_micros',
        'token_day',
        'tokens',
        'claimed_slice_ids',
        'closed_settlement_ids',
        'grant_source_ids'
      ])
        key: support[key]
    };
    return json;
  }

  equal(projected(online.state), projected(offline.state),
      'receipt changes only settlement metadata/cache, not economic policy outcomes');
  final onlineEvents = events(online);
  final awayEvents = events(offline)
      .where((e) => e['kind'] != 'offline_salvage_finalized')
      .toList();
  equal(onlineEvents, awayEvents,
      'actual receipt purchase/reset/timer sequence equal online');
  final first = engine.advance(state, const Duration(minutes: 45),
      offline: true,
      offlineSettlement: request,
      finalizeOfflineSettlement: false);
  final second = engine.advance(first.state, const Duration(minutes: 75),
      offline: true,
      offlineElapsedBefore: const Duration(minutes: 45),
      offlineSettlement: request);
  check(first.accepted && second.accepted, 'receipt partitions accepted');
  equal(semantic(second.state), semantic(offline.state),
      'entire receipt state equal after partitioned replay');
  check(
      !engine
          .advance(offline.state, Duration.zero,
              offline: true, offlineSettlement: request)
          .accepted,
      'closed actual receipt cannot replay');
  equal(GameState.fromJson(offline.state.toJson()).toJson(),
      offline.state.toJson(), 'receipt and policy JSON roundtrip');
  results['seeded_actual_offline_receipt'] = {
    'final': summary(offline.state),
    'recharts': offline.state.rechartCount,
    'purchase_events': online.events.where((e) => e.kind == 'purchase').length,
    'settlement_sequence':
        offline.state.support.lastSettlementSequence.toString(),
    'economic_projection_equal': true,
    'full_partitioned_receipt_equal': true,
    'projection_excludes_only_revision_and_receipt_cursor_cache_metadata': true
  };
}

Future<void> main(List<String> args) async {
  try {
    final initialOnline =
        engine.advance(GameState.initial(), const Duration(hours: 2));
    final initialOffline = engine
        .advance(GameState.initial(), const Duration(hours: 2), offline: true);
    equal(initialOnline.state.toJson(), initialOffline.state.toJson(),
        'pre-unlock unattended baseline parity');
    equal(initialOffline.state.counts, [1, 0, 0, 0, 0],
        'no purchases invented before free unlock');
    check(initialOffline.state.lifetimeMicros == BigInt.from(7200) * million,
        'pre-unlock baseline exact income');
    results['pre_unlock_unattended'] = {
      'duration_seconds': 7200,
      'lifetime_micros': initialOffline.state.lifetimeMicros.toString(),
      'counts': initialOffline.state.counts
    };
    final online = natural(false),
        offline = natural(true),
        repeat = natural(false);
    equal(online, offline, 'earned first-session online/offline');
    equal(online, repeat, 'earned first-session deterministic repeat');
    results['natural_first_session'] = online;
    synergy();
    priorities();
    resets();
    receiptParity();
    await slots();
    results['status'] = 'passed';
  } catch (e, st) {
    results['status'] = 'failed';
    results['error'] = e.toString();
    results['stack'] = st.toString();
    rethrow;
  } finally {
    results['assertions'] = assertions;
    results['classification'] =
        'pure production-engine traces; named boundary fixtures synthetic; not player observations';
    File(args.single).writeAsStringSync(
        '${const JsonEncoder.withIndent('  ').convert(results)}\n');
  }
}
