import 'dart:convert';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';

const engine = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 16, 12);
final million = BigInt.from(1000000);
BigInt r(int amount) => BigInt.from(amount) * million;

GameState assigned(
        {GameState? state,
        String seed = 'account-A',
        List<String> discoveries = const ['calibration', 'archive']}) =>
    engine
        .refreshContracts(state ?? GameState.initial(), epoch,
            accountSeed: seed,
            utcOffsetMinutes: 180,
            availableDiscoveryKinds: discoveries)
        .state;

Map<String, dynamic> withoutRevision(GameState state) =>
    state.toJson()..remove('revision');

void main() {
  group('state migration and history', () {
    test(
        'v1 quantities and timers upgrade explicitly without resetting progress',
        () {
      final source = GameState(
              counts: [10, 1, 0, 0, 0],
              charts: BigInt.from(10),
              lifetimeMicros: r(1000000000),
              walletMicros: r(5),
              surveyNotes: BigInt.from(30),
              elapsedMicros: r(1000),
              focusCharges: 2,
              focusRemainingMicros: r(30))
          .toJson();
      for (final key in [
        'daily',
        'support',
        'lifetime_purchased_count',
        'rechart_count',
        'last_rechart_elapsed_micros',
        'surveys_collected_total',
        'completed_calibration_ids',
        'extra_plan_slots',
        'automation_plans',
        'selected_automation_plan_id'
      ]) {
        source.remove(key);
      }
      source['schema_version'] = 1;
      source['event_order_version'] = 1;
      final upgraded = GameState.fromJson(source);
      expect(upgraded.walletMicros, r(5));
      expect(upgraded.lifetimeMicros, r(1000000000));
      expect(upgraded.charts, BigInt.from(10));
      expect(upgraded.focusCharges, 2);
      expect(upgraded.focusRemainingMicros, r(30));
      expect(upgraded.rechartCount,
          1); // Historical lower bound, not invented exact history.
      expect(upgraded.lifetimePurchasedCount, BigInt.from(10));
      expect(upgraded.surveysCollectedTotal, BigInt.from(3));
      expect(upgraded.daily.initialized, isFalse);
      expect(GameState.fromJson(upgraded.toJson()).toJson(), upgraded.toJson());
    });
    test('purchases resets and surveys update persistent statistics once', () {
      var state = GameState(
          walletMicros: r(1000),
          lifetimeMicros: r(1000000000),
          completedSurveys: 3);
      state = engine.buy(state, 0, 3).state;
      expect(state.lifetimePurchasedCount, BigInt.from(3));
      state = engine.collectSurveys(state).state;
      expect(state.surveysCollectedTotal, BigInt.from(3));
      expect(engine.collectSurveys(state).accepted, isFalse);
      state = engine.rechart(state).state;
      expect(state.rechartCount, 1);
      expect(state.surveysCollectedTotal, BigInt.from(3));
      expect(state.lifetimePurchasedCount, BigInt.from(3));
      expect(GameState.fromJson(state.toJson()).toJson(), state.toJson());
    });
  });

  group('seeded contracts and real calendar', () {
    test(
        'new account receives only current three slots; seed/reload do not reroll',
        () {
      final state = assigned();
      expect(state.dailyContracts.length, 3);
      final again = engine.refreshContracts(
          GameState.fromJson(state.toJson()), epoch,
          availableDiscoveryKinds: ['calibration', 'archive']).state;
      expect(again.dailyContracts.map((c) => c.toJson()).toList(),
          state.dailyContracts.map((c) => c.toJson()).toList());
      expect(assigned().daily.toJson(), state.daily.toJson());
      expect(state.dailyContracts.map((c) => c.id).toSet().length, 3);
    });
    test('frozen target formulas match exact blueprint and survive purchases',
        () {
      final state = assigned(discoveries: []);
      for (final contract in state.dailyContracts) {
        if (contract.kind == 'restore') {
          expect(contract.target, r(600));
        } else {
          expect(contract.kind, 'build');
          expect(contract.target, BigInt.from(5));
        }
      }
      final earned = engine.advance(state, const Duration(minutes: 30)).state;
      final purchased = engine.buyMax(earned, 0).state;
      expect(purchased.dailyContracts.map((c) => c.target).toList(),
          state.dailyContracts.map((c) => c.target).toList());
      expect(purchased.dailyContracts.map((c) => c.rateSnapshotRaw).toList(),
          state.dailyContracts.map((c) => c.rateSnapshotRaw).toList());
    });
    test('offline progress counts only contracts that were already assigned',
        () {
      final state = assigned(discoveries: []);
      final after = engine
          .advance(state, const Duration(minutes: 10), offline: true)
          .state;
      for (final contract
          in after.dailyContracts.where((c) => c.kind == 'restore')) {
        expect(engine.contractProgress(after, contract), contract.target);
      }
    });
    test(
        'one week backlog materializes at return snapshot without retroactive earnings',
        () {
      final state = assigned(discoveries: []);
      final advanced =
          engine.advance(state, const Duration(days: 8), offline: true).state;
      expect(advanced.dailyContracts, isEmpty); // Initial day is expired.
      final returned = engine.refreshContracts(
          advanced, epoch.add(const Duration(days: 8)),
          availableDiscoveryKinds: []).state;
      expect(returned.dailyContracts.length, 21);
      expect(
          returned.dailyContracts.map((c) => c.accountDay).toSet().length, 7);
      for (final contract in returned.dailyContracts) {
        expect(engine.contractProgress(returned, contract), BigInt.zero);
        expect(contract.lifetimeBaselineMicros, returned.lifetimeMicros);
      }
      final reloaded = engine.refreshContracts(
          GameState.fromJson(returned.toJson()),
          epoch.add(const Duration(days: 8)),
          availableDiscoveryKinds: []).state;
      expect(reloaded.dailyContracts.map((c) => c.id).toList(),
          returned.dailyContracts.map((c) => c.id).toList());
    });
    test('clock rollback and timezone changes cannot grant a second daily set',
        () {
      final state = assigned();
      final future = engine
          .refreshContracts(state, epoch.add(const Duration(days: 2)))
          .state;
      final rollback = engine
          .refreshContracts(future, epoch.subtract(const Duration(days: 2)))
          .state;
      expect(rollback.daily.dayHighWater, future.daily.dayHighWater);
      expect(rollback.dailyContracts.map((c) => c.id).toList(),
          future.dailyContracts.map((c) => c.id).toList());
      expect(
          engine
              .refreshContracts(state, epoch, utcOffsetMinutes: -180)
              .accepted,
          isFalse);
      expect(
          engine
              .refreshContracts(state, epoch, accountSeed: 'another-account')
              .accepted,
          isFalse);
    });
    test(
        'online day rollover assigns at boundary while offline slots wait for return',
        () {
      final start = DateTime.utc(2026, 10, 16, 23, 59, 59);
      final state = engine
          .refreshContracts(GameState.initial(), start,
              accountSeed: 'boundary', utcOffsetMinutes: 0)
          .state;
      final online = engine.advance(state, const Duration(seconds: 2)).state;
      final offline = engine
          .advance(state, const Duration(seconds: 2), offline: true)
          .state;
      expect(online.dailyContracts.length, 6);
      expect(offline.dailyContracts.length, 3);
      expect(online.lifetimeMicros, offline.lifetimeMicros);
      final newContracts = online.dailyContracts
          .where((c) => c.accountDay == online.daily.dayHighWater);
      expect(
          newContracts.every((c) => c.lifetimeBaselineMicros == r(1)), isTrue);
    });
    test('one reroll changes family while keeping original difficulty snapshot',
        () {
      final state = assigned();
      final original = state.dailyContracts.first;
      final progressed =
          engine.advance(state, const Duration(minutes: 10)).state;
      final rerolled = engine.rerollContract(progressed, original.id);
      expect(rerolled.accepted, isTrue);
      final next = rerolled.state.dailyContracts.first;
      expect(next.id, original.id);
      expect(next.kind, isNot(original.kind));
      expect(next.rateSnapshotRaw, original.rateSnapshotRaw);
      expect(next.cheapestPriceSnapshotMicros,
          original.cheapestPriceSnapshotMicros);
      expect(engine.contractProgress(rerolled.state, next), BigInt.zero);
      expect(
          engine.rerollContract(rerolled.state, original.id).accepted, isFalse);
    });
    test('Note and XP claim commits once and is not Radiance income', () {
      var state = assigned(state: GameState(focusCharges: 1));
      state = engine.advance(state, const Duration(minutes: 20)).state;
      state = engine.buyMax(state, 0).state;
      state = engine
          .recordDiscovery(state, 'calibration',
              operationSequence: state.nextDiscoverySequence)
          .state;
      state = engine
          .recordDiscovery(state, 'archive',
              operationSequence: state.nextDiscoverySequence)
          .state;
      final lifetime = state.lifetimeMicros;
      for (final contract in state.dailyContracts.toList()) {
        expect(engine.contractProgress(state, contract), contract.target);
        final claimed = engine.claimContract(state, contract.id);
        expect(claimed.accepted, isTrue);
        state = GameState.fromJson(
            jsonDecode(jsonEncode(claimed.state.toJson()))
                as Map<String, dynamic>);
        expect(engine.claimContract(state, contract.id).accepted, isFalse);
        expect(engine.rerollContract(state, contract.id).accepted, isFalse);
      }
      expect(state.passXp, BigInt.from(750));
      expect(state.surveyNotes, BigInt.from(30));
      expect(state.lifetimeMicros, lifetime);
      expect(engine.claimContract(state, 'missing').accepted, isFalse);
    });
    test('Rechart preserves pending progress, claimed receipts and pass XP',
        () {
      var state = assigned(
          state: GameState(lifetimeMicros: r(1000000000)), discoveries: []);
      state = engine.advance(state, const Duration(minutes: 10)).state;
      final restore =
          state.dailyContracts.firstWhere((c) => c.kind == 'restore');
      state = engine.claimContract(state, restore.id).state;
      final before = state.daily.toJson();
      final reset = engine.rechart(state).state;
      expect(reset.daily.toJson(), before);
      expect(engine.claimContract(reset, restore.id).accepted, isFalse);
    });
  });

  group('calibration parity and saved plans', () {
    test(
        'calibration consumes one charge, records collectible once and retries are inert',
        () {
      final state = GameState(focusCharges: 2);
      final completed = engine.completeCalibration(state, 'calibration.01',
          operationSequence: BigInt.one);
      expect(completed.accepted, isTrue);
      expect(completed.state.focusCharges, 1);
      expect(completed.state.focusRemainingMicros, r(600));
      expect(completed.state.completedCalibrationIds, {'calibration.01'});
      expect(
          engine
              .completeCalibration(completed.state, 'calibration.01',
                  operationSequence: BigInt.one)
              .accepted,
          isFalse);
      final repeatedPattern = engine
          .completeCalibration(completed.state, 'calibration.01',
              operationSequence: BigInt.two)
          .state;
      expect(repeatedPattern.completedCalibrationIds.length, 1);
      expect(repeatedPattern.focusRemainingMicros, r(1200));
      expect(
          repeatedPattern.daily.discoveryTotals['calibration'], BigInt.from(2));
      expect(
          engine
              .completeCalibration(repeatedPattern, 'calibration.02')
              .accepted,
          isFalse);
      expect(engine.completeCalibration(state, 'calibration.99').accepted,
          isFalse);
    });
    test('six plans require exactly five 50-Note slot purchases', () {
      var state = GameState(
          charts: BigInt.from(10),
          lifetimeMicros: r(1000000000),
          surveyNotes: BigInt.from(250));
      expect(state.automationPlans.length, 1);
      expect(
          engine
              .saveAutomationPlan(
                  state, AutomationPlan(id: 'extra-1', name: 'Extra'))
              .accepted,
          isFalse);
      for (var index = 1; index <= 5; index++) {
        state = engine.buyPlanSlot(state).state;
        state = engine
            .saveAutomationPlan(
                state, AutomationPlan(id: 'extra-$index', name: 'Plan $index'))
            .state;
      }
      expect(state.automationPlans.length, 6);
      expect(state.surveyNotes, BigInt.zero);
      expect(engine.buyPlanSlot(state).accepted, isFalse);
      expect(GameState.fromJson(state.toJson()).automationPlans.length, 6);
    });
    test('automatic reset requires 100 Charts and both explicit conditions',
        () {
      final plan = AutomationPlan(
          id: 'plan.base',
          name: 'Conditional',
          autoResetEnabled: true,
          minimumAdditionalCharts: BigInt.from(5),
          minimumRunSeconds: 600);
      final early =
          GameState(charts: BigInt.from(25), lifetimeMicros: r(5000000000));
      expect(engine.saveAutomationPlan(early, plan).accepted, isFalse);
      var state = GameState(
          charts: BigInt.from(100),
          lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)));
      state = engine.saveAutomationPlan(state, plan).state;
      final before = engine.advance(state, const Duration(seconds: 599)).state;
      expect(before.rechartCount, 0);
      final after = engine.advance(before, const Duration(seconds: 1));
      expect(after.state.rechartCount, 1);
      expect(after.state.charts, BigInt.from(105));
      expect(after.state.lastRechartElapsedMicros, r(600));
      expect(after.events.where((event) => event.kind == 'rechart').length, 1);
    });
    test(
        'reset entitlement boundary is an advance event and deterministic across chunks',
        () {
      final plan = AutomationPlan(
          id: 'plan.base',
          name: 'One Chart',
          autoResetEnabled: true,
          minimumRunSeconds: 1);
      var state = GameState(
          charts: BigInt.from(100),
          lifetimeMicros:
              engine.lifetimeForCharts(BigInt.from(101)) - BigInt.one,
          elapsedMicros: r(1));
      state = engine.saveAutomationPlan(state, plan).state;
      final first = engine.advance(state, const Duration(microseconds: 1));
      expect(first.state.charts, BigInt.from(101));
      expect(first.events.any((e) => e.kind == 'rechart'), isTrue);
      final whole = engine
          .advance(state, const Duration(seconds: 2), offline: true)
          .state;
      final split = engine
          .advance(
              first.state, const Duration(seconds: 1, microseconds: 999999),
              offline: true,
              offlineElapsedBefore: const Duration(microseconds: 1))
          .state;
      expect(withoutRevision(split), withoutRevision(whole));
    });
    test('priority plan controls the actual purchase decision', () {
      var state = GameState(
          counts: [10, 0, 0, 0, 0],
          charts: BigInt.from(10),
          lifetimeMicros: r(1000000000),
          walletMicros: r(600),
          autoBuyEnabled: true);
      state = engine
          .saveAutomationPlan(
              state,
              AutomationPlan(
                  id: 'plan.base',
                  name: 'Nursery first',
                  purchasePolicy: 'priority',
                  tierPriority: [1, 0, 2, 3, 4]))
          .state;
      final result = engine.advance(state, Duration.zero);
      expect(result.state.counts, [10, 1, 0, 0, 0]);
      expect(result.state.walletMicros, BigInt.zero);
    });
  });
}
