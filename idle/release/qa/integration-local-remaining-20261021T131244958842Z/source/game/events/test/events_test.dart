import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';

final source = jsonDecode(File('content/season.01.json').readAsStringSync())
    as Map<String, dynamic>;
final definition = SeasonDefinition.fromJson(source);
final engine = SeasonEngine(definition);
final passEngine = PassEngine([definition]);
const core = TideglassEngine();
final start = DateTime.utc(2026, 10, 16, 12);
BigInt r(int n) => BigInt.from(n) * BigInt.from(1000000);
SeasonState fresh({DateTime? now, String id = 'run-one'}) =>
    SeasonState.initial(definition, SeasonSchedule(start), now ?? start,
        runId: id);
GameState mainState({int xp = 0}) {
  final state = core
      .refreshContracts(GameState.initial(), start, accountSeed: 'events-test')
      .state;
  return state.copyWith(
      daily: state.daily.copyWith(passXpById: {'pass.01': BigInt.from(xp)}));
}

Map<String, dynamic> clone(Map<String, dynamic> value) =>
    jsonDecode(jsonEncode(value)) as Map<String, dynamic>;

class FixtureEntitlements implements VerifiedPassEntitlementReader {
  final String? account, pass;
  final bool owned;
  FixtureEntitlements({this.owned = true, this.account, this.pass});
  @override
  Future<VerifiedPassEntitlement?> read(
          {required String accountId, required String passId}) async =>
      owned
          ? VerifiedPassEntitlement(
              accountId: account ?? accountId,
              passId: pass ?? passId,
              verificationReceiptId: 'test-adapter-receipt',
              authority: 'TEST ONLY')
          : null;
}

void main() {
  group('authored catalogue and isolation', () {
    test('exact40reward IDs agree with original reviewed launch manifest', () {
      final manifest = jsonDecode(
          File('../../implementation/content/launch_manifest.json')
              .readAsStringSync()) as Map;
      final original = [
        ...manifest['pass']['free_rewards'],
        ...manifest['pass']['premium_rewards']
      ];
      expect(definition.rewards.length, 40);
      for (final record in original) {
        final reward = definition.reward(record['id'] as String);
        expect(reward.level, record['level']);
        expect(reward.kind, record['reward']['kind']);
        expect(reward.contentId, record['reward']['content_id']);
        expect(reward.body, isNotEmpty);
      }
      expect(
          definition.rewards.where((r) => r.kind == 'archive_fragment').length,
          20);
      expect(definition.rewards.where((r) => r.track == 'premium').length, 10);
    });
    test('unsafe matrix effects and omitted reward content reject', () {
      for (final mutation in <void Function(Map<String, dynamic>)>[
        (v) => v['main_power_import'] = true,
        (v) => v['paid_effects'] = true,
        (v) => v['rechart_enabled'] = true,
        (v) => v['synergy_percent_matrix'] = [
              [20, 10],
              [10, 25]
            ],
        (v) => v['rewards'].removeLast(),
        (v) => v['rewards'][0]['body'] = '',
        (v) => v['rewards'][0]['economic_effects'] = ['charts'],
        (v) => v['economic_exports'] = ['radiance']
      ]) {
        final changed = clone(source);
        mutation(changed);
        expect(() => SeasonDefinition.fromJson(changed), throwsFormatException);
      }
    });
    test('definition and save parameters are pinned through content changes',
        () {
      final changed = clone(source);
      changed['copy']['live'] = 'A revised public description.';
      final replacement = SeasonDefinition.fromJson(changed);
      expect(replacement.digest, isNot(definition.digest));
      expect(() => SeasonState.fromJson(fresh().toJson(), replacement),
          throwsFormatException);
      expect(
          () => PassState.fromJson(
              PassState.initial([definition]).toJson(), [replacement]),
          throwsFormatException);
    });
    test('fleet parser cannot import main state power, ownership or receipts',
        () {
      for (final key in [
        'charts',
        'support',
        'daily',
        'focus_charges',
        'focus_remaining_micros',
        'survey_notes',
        'automation_plans',
        'premium_owned',
        'paid_multiplier'
      ]) {
        final json = clone(fresh().toJson());
        json['fleet'][key] = 1;
        expect(
            () => SeasonState.fromJson(json, definition), throwsFormatException,
            reason: key);
      }
      final forged = clone(fresh().toJson());
      forged['base_economy_version'] = 'unknown';
      expect(() => SeasonState.fromJson(forged, definition),
          throwsFormatException);
    });
    test('event matrix immediately yields1.35and1.30 at25source buildings', () {
      final json = clone(fresh().toJson());
      json['fleet']['counts'] = [25, 25, 0, 1, 1];
      final state = SeasonState.fromJson(json, definition);
      expect(engine.synergyMultiplier(state, 3).toDecimalString(), '1.35');
      expect(engine.synergyMultiplier(state, 4).toDecimalString(), '1.30');
      expect(engine.outputPerSecond(state).toDecimalString(), '219850.00');
      expect(engine.priceMicros(fresh(), 0), core.priceMicros(0, 1));
      expect(engine.rechart(state).accepted, isFalse);
    });
    test('starting fleet gifts no wallet or lifetime and offers no paid input',
        () {
      expect(fresh().fleet.counts, [1, 0, 0, 0, 0]);
      expect(fresh().fleet.walletMicros, BigInt.zero);
      expect(fresh().fleet.lifetimeMicros, BigInt.zero);
      expect(engine.outputPerSecond(fresh()).toDecimalString(), '1.00');
    });
  });
  group('season calendar and simulation', () {
    test(
        'startand28dayend use half-open live interval and archive automatically',
        () {
      var state = fresh(now: start.subtract(const Duration(seconds: 1)));
      expect(state.phase, SeasonPhase.upcoming);
      expect(engine.purchase(state, 0, 1).accepted, isFalse);
      final result =
          engine.advanceTo(state, start.add(const Duration(days: 29)));
      state = result.state;
      expect(state.phase, SeasonPhase.archived);
      expect(state.archiveActive, isFalse);
      expect(state.fleet.lifetimeMicros, r(28 * 86400));
      expect(result.events.map((e) => e.kind),
          ['season_started', 'season_archived']);
      expect(
          result.events.last.atUtcMicros,
          BigInt.from(
              start.add(const Duration(days: 28)).microsecondsSinceEpoch));
    });
    test('no activity before the exact start or on exact archive instant', () {
      final upcoming = fresh(now: start.subtract(const Duration(hours: 1)));
      final atStart = engine.advanceTo(upcoming, start).state;
      expect(atStart.phase, SeasonPhase.live);
      expect(atStart.fleet.lifetimeMicros, BigInt.zero);
      final atEnd =
          engine.advanceTo(atStart, start.add(const Duration(days: 28))).state;
      final later =
          engine.advanceTo(atEnd, start.add(const Duration(days: 40))).state;
      expect(later.fleet.toJson(), atEnd.fleet.toJson());
      expect(engine.purchase(later, 0, 1).accepted, isFalse);
    });
    test('archive resumes existing progress and skips the paused gap', () {
      var state =
          engine.advanceTo(fresh(), start.add(const Duration(days: 29))).state;
      final before = state.fleet.lifetimeMicros;
      state = engine
          .resumeArchive(state, start.add(const Duration(days: 40)))
          .state;
      expect(state.fleet.lifetimeMicros, before);
      expect(state.archiveActive, isTrue);
      state = engine
          .advanceTo(state, start.add(const Duration(days: 40, minutes: 5)))
          .state;
      expect(state.fleet.lifetimeMicros, before + r(300));
      state = engine
          .pauseArchive(state, start.add(const Duration(days: 40, minutes: 5)))
          .state;
      final paused = state.fleet.toJson();
      state =
          engine.advanceTo(state, start.add(const Duration(days: 45))).state;
      expect(state.fleet.toJson(), paused);
    });
    test(
        'late profile starts archived atfixedinitialstate without imagined live income',
        () {
      var state = fresh(now: start.add(const Duration(days: 40)));
      expect(state.phase, SeasonPhase.archived);
      expect(state.fleet.lifetimeMicros, BigInt.zero);
      state = engine
          .resumeArchive(state, start.add(const Duration(days: 40)))
          .state;
      state = engine
          .advanceTo(state, start.add(const Duration(days: 40, seconds: 1)))
          .state;
      expect(state.fleet.lifetimeMicros, r(1));
    });
    test('absolute cursor rejects replay and rollback after reload', () {
      final state = engine
          .advanceTo(fresh(), start.add(const Duration(minutes: 5)))
          .state;
      final loaded = SeasonState.fromJson(clone(state.toJson()), definition);
      for (final now in [start, start.add(const Duration(minutes: 5))]) {
        final repeated = engine.advanceTo(loaded, now);
        expect(repeated.accepted, isFalse);
        expect(repeated.state.toJson(), state.toJson());
      }
    });
    test('offline tail and cutoff use36effectivehours over72hours', () {
      final state = engine
          .advanceTo(fresh(), start.add(const Duration(days: 7)), offline: true)
          .state;
      expect(state.fleet.lifetimeMicros, r(129600));
      expect(state.fleet.toJson().keys.toSet(), {
        'counts',
        'wallet_micros',
        'lifetime_micros',
        'elapsed_micros',
        'earning_remainder'
      });
    });
    test('offline absence before season start consumes its own envelope time',
        () {
      final state = fresh(now: start.subtract(const Duration(hours: 23)));
      final after = engine
          .advanceTo(state, start.add(const Duration(hours: 2)), offline: true)
          .state;
      expect(after.fleet.lifetimeMicros, r(4500)); //1hfull+1hquarter
    });
    test('saved automatic policy is identical online/offline through24hours',
        () {
      final state = engine.configurePolicy(fresh(), automatic: true).state;
      final online =
          engine.advanceTo(state, start.add(const Duration(hours: 24))).state;
      final offline = engine
          .advanceTo(state, start.add(const Duration(hours: 24)), offline: true)
          .state;
      expect(offline.toJson(), online.toJson());
      expect(online.fleet.counts[4], greaterThan(0));
    });
    test(
        'carried-offset chunks cross both rate boundaries and save reload identically',
        () {
      final state = engine.configurePolicy(fresh(), automatic: true).state;
      final full = engine
          .advanceTo(state, start.add(const Duration(hours: 80)), offline: true)
          .state;
      var split = engine
          .advanceTo(state, start.add(const Duration(hours: 30)), offline: true)
          .state;
      split = SeasonState.fromJson(clone(split.toJson()), definition);
      split = engine
          .advanceTo(split, start.add(const Duration(hours: 80)),
              offline: true, offlineElapsedBefore: const Duration(hours: 30))
          .state;
      expect(split.toJson(), full.toJson());
    });
    test('main policy can advance alongside event without exported power', () {
      final main = mainState();
      final before = main.toJson();
      final season = engine
          .advanceTo(fresh(), start.add(const Duration(seconds: 40)))
          .state;
      expect(main.toJson(), before);
      final mainAfter = core.advance(main, const Duration(seconds: 40)).state;
      expect(mainAfter.walletMicros, r(40));
      expect(season.fleet.walletMicros, r(40));
      final bought = engine.purchase(season, 0, 1).state;
      expect(mainAfter.walletMicros, r(40));
      expect(bought.fleet.counts[0], 2);
    });
    test(
        'personal milestones export only unique badges and never economic state',
        () {
      final state = engine
          .advanceTo(engine.configurePolicy(fresh(), automatic: true).state,
              start.add(const Duration(hours: 2)))
          .state;
      final claim =
          engine.claimMilestone(state, definition.milestones.first.id);
      expect(claim.accepted, isTrue);
      expect(claim.state.fleet.toJson(), state.fleet.toJson());
      expect(engine.badgeIds(claim.state), {'badge.season01.first_signal'});
      expect(
          engine
              .claimMilestone(claim.state, definition.milestones.first.id)
              .accepted,
          isFalse);
      expect(
          engine.claimMilestone(state, definition.milestones.last.id).accepted,
          isFalse);
    });
  });
  group('single XP authority and reward delivery', () {
    test('level thresholds are500XP and cap at30 withnoXPcopy inPassState', () {
      for (final pair in [
        [0, 0],
        [499, 0],
        [500, 1],
        [14999, 29],
        [15000, 30],
        [999999, 30]
      ]) expect(passEngine.level(mainState(xp: pair[0]), 'pass.01'), pair[1]);
      expect(PassState.initial([definition]).toJson().keys.toSet(),
          {'schema_version', 'definition_digests', 'claims', 'alternatives'});
    });
    test('all30free slots claim once and leave main economy andXPunchanged',
        () {
      final main = mainState(xp: 15000);
      var pass = PassState.initial([definition]);
      final before = main.toJson();
      for (final reward in definition.rewards.where((r) => r.track == 'free')) {
        final claim =
            passEngine.claimFreeReward(main, pass, 'pass.01', reward.id);
        expect(claim.accepted, isTrue);
        expect(claim.main.toJson(), before);
        pass = claim.pass;
        expect(
            passEngine
                .claimFreeReward(main, pass, 'pass.01', reward.id)
                .accepted,
            isFalse);
      }
      expect(passEngine.cosmeticIds(pass).length, 10);
      expect(passEngine.fragmentIds(pass).length, 20);
      expect(
          passEngine
              .claimFreeReward(mainState(xp: 499),
                  PassState.initial([definition]), 'pass.01', 'pass.01.free.01')
              .accepted,
          isFalse);
    });
    test('premium requiresaccountandpassmatchedverifiedadapter andneveraddsXP',
        () async {
      final main = mainState(xp: 15000);
      var pass = PassState.initial([definition]);
      for (final reader in [
        FixtureEntitlements(owned: false),
        FixtureEntitlements(account: 'other'),
        FixtureEntitlements(pass: 'pass.99')
      ]) {
        expect(
            (await passEngine.claimPremiumReward(
                    main, pass, 'pass.01', 'pass.01.premium.03',
                    entitlementReader: reader))
                .accepted,
            isFalse);
      }
      for (final reward
          in definition.rewards.where((r) => r.track == 'premium')) {
        final result = await passEngine.claimPremiumReward(
            main, pass, 'pass.01', reward.id,
            entitlementReader: FixtureEntitlements());
        expect(result.accepted, isTrue);
        expect(result.main.toJson(), main.toJson());
        expect(result.rewardReceipt!.entitlementVerificationReceiptId,
            'test-adapter-receipt');
        pass = result.pass;
      }
      expect(passEngine.cosmeticIds(pass), isEmpty);
      expect(
          (await passEngine.verifiedCosmeticIds(main, pass,
                  entitlementReader: FixtureEntitlements()))
              .length,
          10);
      expect(
          (await passEngine.claimPremiumReward(
                  main, pass, 'pass.01', 'pass.01.premium.03',
                  entitlementReader: FixtureEntitlements()))
              .accepted,
          isFalse);
      expect(
          passEngine
              .claimFreeReward(main, pass, 'pass.01', 'pass.01.premium.06')
              .accepted,
          isFalse);
    });
    test(
        'forged or missing paid claim receipts cannot override independent ownership',
        () async {
      final main = mainState(xp: 15000);
      final json = PassState.initial([definition]).toJson();
      json['claims'] = {
        'pass.01.premium.03': {
          'account_id': 'events-test',
          'pass_id': 'pass.01',
          'reward_id': 'pass.01.premium.03',
          'receipt_id': 'pass:events-test:pass.01.premium.03',
          'entitlement_verification_receipt_id': 'forged-local-string',
        }
      };
      final forged = PassState.fromJson(json, [definition]);
      expect(passEngine.cosmeticIds(forged), isEmpty);
      expect(
          await passEngine.verifiedCosmeticIds(main, forged,
              entitlementReader: FixtureEntitlements(owned: false)),
          isEmpty);
      expect(
          await passEngine.verifiedCosmeticIds(main, forged,
              entitlementReader: FixtureEntitlements(account: 'wrong')),
          isEmpty);
      final missing = PassState.initial([definition]);
      expect(
          (await passEngine.verifiedCosmeticIds(main, missing,
                  entitlementReader: FixtureEntitlements()))
              .length,
          10);
      expect(
          (await passEngine.verifiedCosmeticIds(mainState(xp: 1499), missing,
              entitlementReader: FixtureEntitlements())),
          isEmpty);
    });
    test(
        'eventprogressbeforeassignment excluded, then exactsingle daily receipt grants',
        () {
      final main = mainState();
      var pass = PassState.initial([definition]);
      var season = engine
          .advanceTo(fresh(), start.add(const Duration(hours: 1)),
              offline: true)
          .state;
      final id = main.dailyContracts.first.id;
      pass = passEngine.bindEventAlternative(main, pass, id, season).pass;
      expect(pass.alternatives[id]!.baselineMicros, r(3600));
      expect(
          passEngine
              .claimDaily(main, pass, id, alternativeSeason: season)
              .accepted,
          isFalse);
      season = engine
          .advanceTo(season, start.add(const Duration(hours: 1, minutes: 10)),
              offline: true)
          .state;
      final claimed =
          passEngine.claimDaily(main, pass, id, alternativeSeason: season);
      expect(claimed.accepted, isTrue);
      expect(claimed.main.passXp, BigInt.from(250));
      expect(claimed.main.surveyNotes, BigInt.from(10));
      expect(claimed.main.lifetimeMicros, main.lifetimeMicros);
      expect(claimed.events.single.details['receipt_id'], 'claim:$id');
      expect(core.claimContract(claimed.main, id).accepted, isFalse);
      expect(
          passEngine
              .claimDaily(claimed.main, claimed.pass, id,
                  alternativeSeason: season)
              .accepted,
          isFalse);
    });
    test('binding cannot move targets andwrongrunorunassignedID cannotclaim',
        () {
      final main = mainState();
      final pass = PassState.initial([definition]);
      final id = main.dailyContracts.first.id;
      var bound = passEngine.bindEventAlternative(main, pass, id, fresh()).pass;
      final other = engine
          .advanceTo(
              fresh(id: 'wrong-run'), start.add(const Duration(hours: 1)))
          .state;
      expect(
          passEngine
              .claimDaily(main, bound, id, alternativeSeason: other)
              .accepted,
          isFalse);
      expect(
          passEngine
              .claimDaily(main, bound, main.dailyContracts.last.id,
                  alternativeSeason: other)
              .accepted,
          isFalse);
      final later =
          engine.advanceTo(fresh(), start.add(const Duration(hours: 1))).state;
      expect(passEngine.bindEventAlternative(main, bound, id, later).accepted,
          isFalse);
      expect(bound.alternatives[id]!.targetMicros, r(600));
    });
    test('nativecompletionbeforeeventclaim prevents doubleXP', () {
      var main = mainState();
      final id = main.dailyContracts.first.id;
      final pass = passEngine
          .bindEventAlternative(
              main, PassState.initial([definition]), id, fresh())
          .pass;
      final c = main.dailyContracts.first;
      main = main.copyWith(
          lifetimeMicros: c.target + main.lifetimeMicros,
          lifetimePurchasedCount: c.target + main.lifetimePurchasedCount);
      final claimed = core.claimContract(main, id);
      expect(claimed.accepted, isTrue);
      final season =
          engine.advanceTo(fresh(), start.add(const Duration(hours: 1))).state;
      final duplicate = passEngine.claimDaily(claimed.state, pass, id,
          alternativeSeason: season);
      expect(duplicate.accepted, isFalse);
      expect(duplicate.main.passXp, BigInt.from(250));
    });
    test('contract expiry and native reroll invalidateboundalternative', () {
      var main = mainState();
      final id = main.dailyContracts.first.id;
      final pass = passEngine
          .bindEventAlternative(
              main, PassState.initial([definition]), id, fresh())
          .pass;
      final season =
          engine.advanceTo(fresh(), start.add(const Duration(hours: 1))).state;
      final rerolled = core.rerollContract(main, id).state;
      expect(
          passEngine
              .claimDaily(rerolled, pass, id, alternativeSeason: season)
              .accepted,
          isFalse);
      main =
          core.refreshContracts(main, start.add(const Duration(days: 8))).state;
      expect(
          passEngine
              .claimDaily(main, pass, id, alternativeSeason: season)
              .accepted,
          isFalse);
    });
    test(
        'reroll permits fresh binding and excludes every pre-rebinding event earning',
        () {
      var main = mainState();
      var pass = PassState.initial([definition]);
      final id = main.dailyContracts.first.id;
      pass = passEngine.bindEventAlternative(main, pass, id, fresh()).pass;
      var season =
          engine.advanceTo(fresh(), start.add(const Duration(hours: 1))).state;
      main = core.rerollContract(main, id).state;
      expect(
          passEngine.pruneAlternatives(main, pass).pass.alternatives, isEmpty);
      final rebound = passEngine.bindEventAlternative(main, pass, id, season);
      expect(rebound.accepted, isTrue);
      pass = rebound.pass;
      expect(pass.alternatives[id]!.baselineMicros, r(3600));
      expect(
          passEngine
              .claimDaily(main, pass, id, alternativeSeason: season)
              .accepted,
          isFalse);
      expect(passEngine.bindEventAlternative(main, pass, id, season).accepted,
          isFalse);
      season = engine
          .advanceTo(season, start.add(const Duration(hours: 1, minutes: 10)))
          .state;
      final claim =
          passEngine.claimDaily(main, pass, id, alternativeSeason: season);
      expect(claim.accepted, isTrue);
      expect(claim.main.passXp, BigInt.from(250));
      expect(core.claimContract(claim.main, id).accepted, isFalse);
    });
    test('threeeventalternatives yield750XPnotextraXPand20days finishfree', () {
      var main = mainState();
      var pass = PassState.initial([definition]);
      var season = fresh();
      for (var day = 0; day < 20; day++) {
        final today = start.add(Duration(days: day));
        main = core.refreshContracts(main, today).state;
        season = engine.advanceTo(season, today).state;
        final current = main.dailyContracts
            .where((c) => c.accountDay == main.daily.dayHighWater)
            .toList();
        expect(current.length, 3);
        for (final c in current)
          pass = passEngine.bindEventAlternative(main, pass, c.id, season).pass;
        season = engine
            .advanceTo(season, today.add(const Duration(minutes: 10)))
            .state;
        for (final c in current) {
          final result = passEngine.claimDaily(main, pass, c.id,
              alternativeSeason: season);
          expect(result.accepted, isTrue);
          main = result.main;
          pass = result.pass;
        }
        expect(main.passXp, BigInt.from((day + 1) * 750));
      }
      expect(passEngine.level(main, 'pass.01'), 30);
      expect(main.passXp, BigInt.from(15000));
      expect(main.lifetimeMicros, BigInt.zero);
    });
    test('one selected archived pass receivesXPwhileother totalsremainintact',
        () {
      final second = clone(source);
      second['id'] = 'season.02';
      second['pass_id'] = 'pass.02';
      second['rules_version'] = 'season.02.fixture';
      for (final reward in second['rewards'])
        reward['id'] =
            (reward['id'] as String).replaceFirst('pass.01', 'pass.02');
      final next = SeasonDefinition.fromJson(second);
      final multi = PassEngine([definition, next]);
      var pass = PassState.initial([definition, next]);
      var main = mainState();
      final upcoming = SeasonState.initial(
          next, SeasonSchedule(start.add(const Duration(days: 1))), start,
          runId: 'future');
      expect(multi.selectPass(main, pass, upcoming).accepted, isFalse);
      final live = SeasonState.initial(next, SeasonSchedule(start), start,
          runId: 'second');
      main = multi.selectPass(main, pass, live).main;
      expect(main.daily.selectedPassId, 'pass.02');
      final archived = engine
          .resumeArchive(fresh(now: start.add(const Duration(days: 29))),
              start.add(const Duration(days: 29)))
          .state;
      main = multi.selectPass(main, pass, archived).main;
      expect(main.daily.selectedPassId, 'pass.01');
      final id = main.dailyContracts.first.id;
      pass = multi.bindEventAlternative(main, pass, id, archived).pass;
      final progressed = engine
          .advanceTo(archived, start.add(const Duration(days: 29, minutes: 10)))
          .state;
      main =
          multi.claimDaily(main, pass, id, alternativeSeason: progressed).main;
      expect(main.daily.passXpById['pass.01'], BigInt.from(250));
      expect(main.daily.passXpById['pass.02'], BigInt.zero);
    });
  });
}
