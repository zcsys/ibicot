import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const engine = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 16, 12);
BigInt r(int value) => BigInt.from(value) * BigInt.from(1000000);
GameState ready({GameState? state, DateTime? now}) => engine
    .refreshContracts(state ?? GameState.initial(), now ?? epoch,
        accountSeed: 'support-test')
    .state;
GameState grant(GameState state, int slot, {String route = 'briefing'}) =>
    engine
        .claimSupportToken(state,
            accountDay: state.daily.dayHighWater,
            slot: slot,
            sourceId: route == 'briefing'
                ? engine.briefingSourceId(state, slot)
                : engine.adSupportSourceId(state, slot, 'a' * 64),
            route: route)
        .state;
OfflineSettlementRequest request(
        {int seconds = 300, int sequence = 1, int startSeconds = 0}) =>
    OfflineSettlementRequest(
        sequence: BigInt.from(sequence),
        fromUtc: epoch.add(Duration(seconds: startSeconds)),
        throughUtc: epoch.add(Duration(seconds: startSeconds + seconds)));
GameState boosted({int count = 1, GameState? state}) {
  var result = ready(state: state);
  for (var slot = 0; slot < count; slot++) {
    result = grant(result, slot);
    result =
        engine.useSupportBoost(result, result.support.tokens.last.id).state;
  }
  return result;
}

Map<String, dynamic> withoutRevision(GameState state) =>
    state.toJson()..remove('revision');

void main() {
  group('Support allowance and boost', () {
    test('briefing and verified-ad adapters draw the same six slots', () {
      var state = ready();
      for (var slot = 0; slot < 6; slot++) {
        state = grant(state, slot, route: slot.isEven ? 'briefing' : 'ad');
      }
      expect(state.support.tokens.length, 6);
      expect(
          engine
              .claimSupportToken(state,
                  accountDay: state.daily.dayHighWater,
                  slot: 6,
                  sourceId: 'seventh')
              .accepted,
          isFalse);
      expect(
          engine
              .claimSupportToken(state,
                  accountDay: state.daily.dayHighWater,
                  slot: 0,
                  sourceId: 'ad-repeat',
                  route: 'ad')
              .accepted,
          isFalse);
      expect(state.walletMicros, BigInt.zero);
    });
    test('no-fill route and invalid callbacks consume nothing', () {
      final state = ready();
      final failed = engine.claimSupportToken(state,
          accountDay: state.daily.dayHighWater,
          slot: 0,
          sourceId: 'no-fill',
          route: 'no-fill');
      expect(failed.accepted, isFalse);
      expect(failed.state.toJson(), state.toJson());
      expect(grant(failed.state, 0).support.tokens.length, 1);
    });
    test('source identity is one-use even when callback changes slot', () {
      final state = grant(ready(), 0);
      final result = engine.claimSupportToken(state,
          accountDay: state.daily.dayHighWater,
          slot: 1,
          sourceId: state.support.tokens.single.sourceId);
      expect(result.accepted, isFalse);
      expect(result.reason, 'support_source_not_bound_to_day_and_slot');
    });
    test('token consumes once and queues exactly twenty real minutes', () {
      final state = grant(ready(), 0);
      final used =
          engine.useSupportBoost(state, state.support.tokens.single.id);
      expect(used.state.supportRemainingMicros, r(1200));
      expect(
          engine
              .useSupportBoost(used.state, state.support.tokens.single.id)
              .accepted,
          isFalse);
      expect(used.events.single.details['receipt_id'],
          'consume:${state.support.tokens.single.id}');
    });
    test('six boosts queue two hours and award 1800 constant-rate seconds', () {
      final initial = boosted(count: 6);
      final after = engine.advance(initial, const Duration(hours: 2)).state;
      expect(after.walletMicros, r(9000));
      expect(after.supportRemainingMicros, BigInt.zero);
    });
    test('Focus and Support are additive 1.45 then expire independently', () {
      final initial = boosted(state: GameState(focusCharges: 1));
      final focused = engine.activateFocus(initial).state;
      expect(engine.activeOutputPerSecond(focused).toDecimalString(), '1.45');
      final after =
          engine.advance(focused, const Duration(seconds: 1201)).state;
      expect(after.walletMicros, r(1621)); //600*1.45+600*1.25+1
      expect(after.supportRemainingMicros, BigInt.zero);
      expect(after.focusRemainingMicros, BigInt.zero);
    });
    test('Rechart preserves queued expiry without refreshing it', () {
      var state = boosted(state: GameState(lifetimeMicros: r(1000000000)));
      state = engine.advance(state, const Duration(seconds: 77)).state;
      final reset = engine.rechart(state).state;
      expect(reset.supportRemainingMicros, r(1123));
      expect(reset.support.toJson(), state.support.toJson());
      expect(
          engine
              .advance(reset, const Duration(seconds: 1123))
              .state
              .supportRemainingMicros,
          BigInt.zero);
    });
    test('midnight expires unspent tokens but running effects survive', () {
      var state = ready(now: DateTime.utc(2026, 10, 16, 23, 59, 59));
      state = grant(grant(state, 0), 1);
      final oldDay = state.daily.dayHighWater;
      final oldId = state.support.tokens.last.id;
      state =
          engine.useSupportBoost(state, state.support.tokens.first.id).state;
      state = engine.advance(state, const Duration(seconds: 2)).state;
      expect(state.support.tokens, isEmpty);
      expect(state.supportRemainingMicros, r(1198));
      expect(engine.useSupportBoost(state, oldId).accepted, isFalse);
      expect(
          engine
              .claimSupportToken(state,
                  accountDay: oldDay, slot: 2, sourceId: 'late-ad')
              .accepted,
          isFalse);
      expect(grant(state, 0).support.tokens.length, 1);
    });
    test('clock rollback cannot renew allowance or reuse old source next day',
        () {
      var state = grant(ready(), 0);
      final source = state.support.tokens.single.sourceId;
      final originalDay = state.daily.dayHighWater;
      state = engine
          .refreshContracts(state, epoch.subtract(const Duration(days: 1)))
          .state;
      expect(state.daily.dayHighWater, originalDay);
      expect(state.support.tokens.length, 1);
      state = engine
          .refreshContracts(state, epoch.add(const Duration(days: 1)))
          .state;
      expect(state.support.tokens, isEmpty);
      expect(
          engine
              .claimSupportToken(state,
                  accountDay: state.daily.dayHighWater,
                  slot: 0,
                  sourceId: source)
              .accepted,
          isFalse);
    });
  });
  group('genuine offline salvage', () {
    test('simulation without a settlement identity creates no caches', () {
      final state = engine
          .advance(ready(), const Duration(hours: 1), offline: true)
          .state;
      expect(state.support.caches, isEmpty);
      expect(state.support.closedSettlementIds, isEmpty);
    });
    test('cache integral excludes Focus and Support rewards', () {
      var state = boosted(state: GameState(focusCharges: 1));
      state = engine.activateFocus(state).state;
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true, offlineSettlement: request())
          .state;
      expect(state.walletMicros, r(435));
      final cache = state.support.caches.single;
      expect(cache.unboostedMicros, r(300));
      expect(cache.settlementRateRaw, Fixed.scale);
      expect(cache.endElapsedMicros - cache.startElapsedMicros, r(300));
    });
    test('less than five minutes never invents a full slice', () {
      final state = engine
          .advance(ready(), const Duration(seconds: 299),
              offline: true, offlineSettlement: request(seconds: 299))
          .state;
      expect(state.support.caches, isEmpty);
    });
    test('retains latest six complete slices and excludes production beyond72h',
        () {
      final state = engine
          .advance(ready(), const Duration(days: 5),
              offline: true, offlineSettlement: request(seconds: 5 * 86400))
          .state;
      expect(state.support.caches.length, 6);
      expect(state.support.caches.last.endElapsedMicros, r(259200));
      expect(state.support.caches.first.startElapsedMicros, r(257400));
      for (final cache in state.support.caches)
        expect(cache.unboostedMicros, r(75));
    });
    test('salvage uses min genuine slice and frozen settlement cap', () {
      final cache = SalvageCache(
          id: 'test',
          settlementId: 'pure-helper',
          startElapsedMicros: BigInt.zero,
          endElapsedMicros: r(300),
          unboostedMicros: r(900),
          settlementRateRaw: Fixed.scale);
      expect(engine.salvageBonusMicros(cache), r(300));
      final tail = SalvageCache(
          id: 'tail',
          settlementId: 'pure-helper',
          startElapsedMicros: BigInt.zero,
          endElapsedMicros: r(300),
          unboostedMicros: r(75),
          settlementRateRaw: Fixed.scale);
      expect(engine.salvageBonusMicros(tail), r(75));
    });
    test('claim commits one token and slice with wallet/lifetime together', () {
      var state = grant(grant(ready(), 0), 1);
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true, offlineSettlement: request())
          .state;
      final cache = state.support.caches.single;
      final first = state.support.tokens.first.id,
          second = state.support.tokens.last.id;
      final result = engine.claimSalvageCache(state, first, cache.id);
      expect(result.accepted, isTrue);
      expect(result.state.walletMicros, r(600));
      expect(result.state.lifetimeMicros, r(600));
      expect(result.state.support.tokens.first.spent, isTrue);
      expect(result.state.support.claimedSliceIds, contains(cache.id));
      final repeat = engine.claimSalvageCache(result.state, second, cache.id);
      expect(repeat.accepted, isFalse);
      expect(repeat.state.support.tokens.last.spent, isFalse);
      expect(result.state.support.caches.single.unboostedMicros, r(300));
    });
    test('later purchases do not alter frozen settlement cap', () {
      var state = grant(ready(), 0);
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true, offlineSettlement: request())
          .state;
      final cache = state.support.caches.single;
      final bought = engine.buy(state, 0, 1).state;
      expect(engine.outputPerSecond(bought).raw, Fixed.scale * BigInt.from(2));
      expect(bought.support.caches.single.settlementRateRaw, Fixed.scale);
      final claimed = engine
          .claimSalvageCache(bought, bought.support.tokens.single.id, cache.id)
          .state;
      expect(claimed.walletMicros - bought.walletMicros, r(300));
    });
    test('new salvage never doubles an earlier salvage reward', () {
      var state = grant(grant(ready(), 0), 1);
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true, offlineSettlement: request())
          .state;
      state = engine
          .claimSalvageCache(state, state.support.tokens.first.id,
              state.support.caches.single.id)
          .state;
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true,
              offlineSettlement: request(sequence: 2, startSeconds: 300))
          .state;
      expect(state.support.caches.last.unboostedMicros, r(300));
      expect(state.lifetimeMicros, r(900));
    });
    test('replayed settlement IDs reject without earning income twice', () {
      final state = engine
          .advance(ready(), const Duration(minutes: 5),
              offline: true, offlineSettlement: request())
          .state;
      final repeated = engine.advance(
          GameState.fromJson(state.toJson()), const Duration(minutes: 5),
          offline: true, offlineSettlement: request());
      expect(repeated.accepted, isFalse);
      expect(repeated.state.toJson(), state.toJson());
    });
    test('chunk accumulator survives reload and equals complete settlement',
        () {
      final initial = boosted(state: GameState(focusCharges: 1));
      final focused = engine.activateFocus(initial).state;
      final full = engine
          .advance(focused, const Duration(seconds: 1001),
              offline: true, offlineSettlement: request(seconds: 1001))
          .state;
      var chunk = engine
          .advance(focused, const Duration(microseconds: 123456789),
              offline: true,
              offlineSettlement: request(seconds: 1001),
              finalizeOfflineSettlement: false)
          .state;
      chunk = GameState.fromJson(
          jsonDecode(jsonEncode(chunk.toJson())) as Map<String, dynamic>);
      chunk = engine
          .advance(chunk, const Duration(microseconds: 877543211),
              offline: true,
              offlineElapsedBefore: const Duration(microseconds: 123456789),
              offlineSettlement: request(seconds: 1001))
          .state;
      expect(withoutRevision(chunk), withoutRevision(full));
    });
    test('pending cache cannot be claimed and continuity mismatch rejects', () {
      var state = grant(ready(), 0);
      state = engine
          .advance(state, const Duration(minutes: 5),
              offline: true,
              offlineSettlement: request(seconds: 301),
              finalizeOfflineSettlement: false)
          .state;
      expect(
          engine
              .claimSalvageCache(state, state.support.tokens.single.id,
                  state.support.caches.single.id)
              .reason,
          'offline_settlement_not_finalized');
      expect(
          engine
              .advance(state, const Duration(seconds: 1),
                  offline: true, offlineSettlement: request(seconds: 301))
              .accepted,
          isFalse);
      expect(
          engine.advance(state, const Duration(seconds: 1)).accepted, isFalse);
      expect(
          engine
              .advance(state, const Duration(seconds: 1),
                  offline: true,
                  offlineSettlement: request(seconds: 301, sequence: 2),
                  offlineElapsedBefore: const Duration(minutes: 5))
              .accepted,
          isFalse);
    });
  });
  group('Support persistence and migration', () {
    test('v2 migrates with its daily progress and no invented Support receipts',
        () {
      final original = ready();
      final old = original.toJson()..remove('support');
      (old['daily'] as Map).remove('discovery_sequence');
      old['schema_version'] = 2;
      old['event_order_version'] = 2;
      final migrated = GameState.fromJson(old);
      expect(migrated.daily.toJson(), original.daily.toJson());
      expect(migrated.support.tokens, isEmpty);
      expect(migrated.support.caches, isEmpty);
      expect(migrated.toJson()['schema_version'], 4);
    });
    test('strict Support serialization rejects omitted and negative quantities',
        () {
      final json = ready().toJson();
      final support = Map<String, dynamic>.from(json['support'] as Map);
      expect(
          () => GameState.fromJson({
                ...json,
                'support': {...support}..remove('tokens')
              }),
          throwsFormatException);
      expect(
          () => GameState.fromJson({
                ...json,
                'support': {...support, 'remaining_micros': '-1'}
              }),
          throwsFormatException);
    });
    test('real repository reload preserves atomic consumption and slice denial',
        () async {
      final directory =
          await Directory.systemTemp.createTemp('support-receipt-');
      try {
        SaveRepository repository() => SaveRepository(directory,
            economicVersion: economyVersion,
            economicDigest:
                '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',
            validatePayload: (p) =>
                GameState.fromJson(p['core'] as Map<String, dynamic>),
            now: () => epoch);
        final repo = repository();
        await repo.load();
        var state = grant(grant(ready(), 0), 1);
        state = engine
            .advance(state, const Duration(minutes: 5),
                offline: true, offlineSettlement: request())
            .state;
        final cache = state.support.caches.single.id;
        state = engine
            .claimSalvageCache(state, state.support.tokens.first.id, cache)
            .state;
        await repo.save({'core': state.toJson()},
            settledThrough: epoch.add(const Duration(minutes: 5)));
        final loaded = GameState.fromJson((await repository().load())
            .snapshot!
            .payload['core'] as Map<String, dynamic>);
        expect(loaded.toJson(), state.toJson());
        expect(
            engine
                .claimSalvageCache(loaded, loaded.support.tokens.last.id, cache)
                .accepted,
            isFalse);
      } finally {
        await directory.delete(recursive: true);
      }
    });
  });
}
