import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

const engine = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 16, 12);
BigInt r(int n) => BigInt.from(n) * BigInt.from(1000000);
GameState ready() => engine
    .refreshContracts(GameState.initial(), epoch, accountSeed: 'bounded')
    .state;
Map<String, dynamic> fixture(String name) =>
    jsonDecode(File('test/fixtures/$name.json').readAsStringSync())
        as Map<String, dynamic>;
OfflineSettlementRequest request(
        GameState state, DateTime from, Duration duration) =>
    OfflineSettlementRequest(
        sequence: state.nextSettlementSequence,
        fromUtc: from,
        throughUtc: from.add(duration));
void main() {
  test('discovery exactnext sequence rejects replay gaps andopaque newIDs', () {
    var state = ready();
    final first = state.nextDiscoverySequence;
    state = engine
        .recordDiscovery(state, 'archive', operationSequence: first)
        .state;
    state = GameState.fromJson(
        jsonDecode(jsonEncode(state.toJson())) as Map<String, dynamic>);
    expect(state.daily.discoverySequence, BigInt.one);
    expect(state.daily.discoveryOperationIds, isEmpty);
    for (final sequence in [first, first + BigInt.two, BigInt.zero]) {
      final rejected =
          engine.recordDiscovery(state, 'archive', operationSequence: sequence);
      expect(rejected.accepted, isFalse);
      expect(rejected.state.toJson(), state.toJson());
    }
    expect(
        engine
            .recordDiscovery(state, 'archive', operationId: 'new-opaque')
            .accepted,
        isFalse);
    expect(
        engine
            .recordDiscovery(state, 'archive',
                operationSequence: state.nextDiscoverySequence)
            .accepted,
        isTrue);
  });
  test('calibration retry is inertandfailedFocusdoesnotconsumeasequence', () {
    var state = ready().copyWith(focusCharges: 1);
    final seq = state.nextDiscoverySequence;
    final success = engine.completeCalibration(state, 'calibration.01',
        operationSequence: seq);
    expect(success.accepted, isTrue);
    state = GameState.fromJson(success.state.toJson());
    expect(
        engine
            .completeCalibration(state, 'calibration.01',
                operationSequence: seq)
            .accepted,
        isFalse);
    final failed = engine.completeCalibration(state, 'calibration.02',
        operationSequence: state.nextDiscoverySequence);
    expect(failed.accepted, isFalse);
    expect(failed.state.toJson(), state.toJson());
  });
  test('requestsequenceandUTCintervalhighwaterrejectoldandrelabeledreturns',
      () {
    var state = ready();
    const duration = Duration(minutes: 5);
    final original = request(state, epoch, duration);
    state = engine
        .advance(state, duration, offline: true, offlineSettlement: original)
        .state;
    expect(state.support.lastSettlementSequence, BigInt.one);
    expect(state.support.closedSettlementIds, isEmpty);
    expect(state.support.lastSettlementThroughUtcMicros,
        BigInt.from(epoch.add(duration).microsecondsSinceEpoch));
    expect(
        engine
            .advance(state, duration,
                offline: true, offlineSettlement: original)
            .accepted,
        isFalse);
    final relabeled = request(state, epoch, duration);
    expect(
        engine
            .advance(state, duration,
                offline: true, offlineSettlement: relabeled)
            .accepted,
        isFalse);
    final gap = OfflineSettlementRequest(
        sequence: state.nextSettlementSequence + BigInt.one,
        fromUtc: epoch.add(duration),
        throughUtc: epoch.add(const Duration(minutes: 10)));
    expect(
        engine
            .advance(state, duration, offline: true, offlineSettlement: gap)
            .accepted,
        isFalse);
  });
  test('alreadyproducedonlineintervalcannotberelabeledasthefirstofflinecapture',
      () {
    final state = engine.advance(ready(), const Duration(minutes: 5)).state;
    final repeated = engine.advance(state, const Duration(minutes: 5),
        offline: true,
        offlineSettlement: request(state, epoch, const Duration(minutes: 5)));
    expect(repeated.reason, 'offline_interval_precedes_production_cursor');
    expect(repeated.state.toJson(), state.toJson());
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true,
                offlineSettlement: request(
                    state,
                    epoch.add(const Duration(minutes: 5)),
                    const Duration(minutes: 5)))
            .accepted,
        isTrue);
  });
  test('finalendpointmustmatchandabortedbudgetfailureleavesinputuntouched', () {
    final state = ready();
    final identity = request(state, epoch, const Duration(minutes: 10));
    final before = jsonEncode(state.toJson());
    for (final duration in [
      const Duration(minutes: 5),
      const Duration(minutes: 11)
    ]) {
      final result = engine.advance(state, duration,
          offline: true, offlineSettlement: identity);
      expect(result.accepted, isFalse);
      expect(jsonEncode(result.state.toJson()), before);
    }
    expect(
        () => engine.advance(state, const Duration(minutes: 10),
            offline: true, offlineSettlement: identity, maximumEvents: 1),
        throwsStateError);
    expect(jsonEncode(state.toJson()), before);
    expect(state.nextSettlementSequence, BigInt.one);
  });
  test('partialrequestcannotbechangedandonlyfinalcommitadvanceshighwater', () {
    final state = ready();
    final identity = request(state, epoch, const Duration(seconds: 601));
    var partial = engine
        .advance(state, const Duration(seconds: 123),
            offline: true,
            offlineSettlement: identity,
            finalizeOfflineSettlement: false)
        .state;
    expect(partial.support.lastSettlementSequence, BigInt.zero);
    expect(partial.support.activeSettlementRequest!.sameAs(identity), isTrue);
    partial = GameState.fromJson(partial.toJson());
    final changed = OfflineSettlementRequest(
        sequence: identity.sequence,
        fromUtc: epoch,
        throughUtc: epoch.add(const Duration(seconds: 602)));
    expect(
        engine
            .advance(partial, const Duration(seconds: 479),
                offline: true,
                offlineElapsedBefore: const Duration(seconds: 123),
                offlineSettlement: changed)
            .accepted,
        isFalse);
    final complete = engine
        .advance(partial, const Duration(seconds: 478),
            offline: true,
            offlineElapsedBefore: const Duration(seconds: 123),
            offlineSettlement: identity)
        .state;
    final full = engine
        .advance(state, const Duration(seconds: 601),
            offline: true, offlineSettlement: identity)
        .state;
    expect(complete.toJson()..remove('revision'),
        full.toJson()..remove('revision'));
    expect(complete.support.activeSettlementRequest, isNull);
    expect(complete.nextSettlementSequence, BigInt.two);
  });
  test('oldschemafixturesmigrateoncepreservingmoneyandfrozenlegacydenylists',
      () {
    for (final version in [1, 2, 3]) {
      final source = fixture('state-v$version');
      final state = GameState.fromJson(source);
      expect(state.walletMicros, r(600));
      expect(state.lifetimeMicros, r(600));
      expect(state.toJson()['schema_version'], 4);
      expect(GameState.fromJson(state.toJson()).toJson(), state.toJson());
      if (version >= 2) {
        expect(state.daily.discoveryOperationIds,
            {'old-discovery-a', 'old-discovery-b'});
        expect(
            engine
                .recordDiscovery(state, 'archive',
                    operationId: 'old-discovery-a',
                    operationSequence: state.nextDiscoverySequence)
                .accepted,
            isFalse);
        final after = engine
            .recordDiscovery(state, 'archive',
                operationSequence: state.nextDiscoverySequence)
            .state;
        expect(after.daily.discoveryOperationIds,
            state.daily.discoveryOperationIds);
      }
      if (version == 3) {
        expect(state.support.claimedSliceIds, {'old-settlement:0'});
        expect(
            engine
                .advance(state, const Duration(seconds: 1),
                    offline: true, offlineSettlementId: 'old-settlement')
                .accepted,
            isFalse);
        expect(
            engine
                .claimSupportToken(state,
                    accountDay: state.daily.dayHighWater,
                    slot: 1,
                    sourceId: 'old-grant')
                .accepted,
            isFalse);
        expect(
            state.support.lastSettlementThroughUtcMicros,
            BigInt.from(
                epoch.add(const Duration(minutes: 5)).microsecondsSinceEpoch));
      }
    }
  });
  test('frozenlegacysettlementIDcannotbereusedwithnewstructuredsequence', () {
    final raw = fixture('state-v3');
    final provisional = GameState.fromJson(raw);
    final from = epoch.add(const Duration(minutes: 5));
    final typed = request(provisional, from, const Duration(minutes: 5));
    (raw['support'] as Map)['closed_settlement_ids'] = [
      'old-settlement',
      typed.identity('legacy')
    ];
    final state = GameState.fromJson(raw);
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true, offlineSettlement: typed)
            .reason,
        'legacy_offline_identity_reused');
  });
  test('pendingv3accumulatorfinishesoncewithoutreplayingalreadypaid100seconds',
      () {
    var pending = GameState.fromJson(fixture('state-v3-pending'));
    expect(pending.support.hasLegacyPendingSettlement, isTrue);
    expect(
        engine
            .advance(pending, const Duration(seconds: 200), offline: true)
            .accepted,
        isFalse);
    expect(
        engine
            .advance(pending, const Duration(seconds: 200),
                offline: true,
                offlineSettlement: request(
                    pending,
                    epoch.add(const Duration(seconds: 100)),
                    const Duration(seconds: 200)))
            .accepted,
        isFalse);
    final wrong = engine.finishLegacyOfflineSettlement(
        pending, const Duration(seconds: 200),
        frozenSettlementId: 'opaque-pending',
        offlineElapsedBefore: Duration.zero,
        throughUtc: epoch.add(const Duration(minutes: 5)));
    expect(wrong.accepted, isFalse);
    expect(wrong.state.toJson(), pending.toJson());
    pending = GameState.fromJson(pending.toJson());
    final completed = engine.finishLegacyOfflineSettlement(
        pending, const Duration(seconds: 200),
        frozenSettlementId: 'opaque-pending',
        offlineElapsedBefore: const Duration(seconds: 100),
        throughUtc: epoch.add(const Duration(minutes: 5)));
    expect(completed.accepted, isTrue);
    expect(completed.state.lifetimeMicros, r(300));
    expect(completed.state.support.caches.single.unboostedMicros, r(300));
    expect(completed.state.support.closedSettlementIds, {'opaque-pending'});
    expect(completed.state.nextSettlementSequence, BigInt.one);
    expect(
        engine
            .finishLegacyOfflineSettlement(
                completed.state, const Duration(seconds: 200),
                frozenSettlementId: 'opaque-pending',
                offlineElapsedBefore: const Duration(seconds: 100),
                throughUtc: epoch.add(const Duration(minutes: 5)))
            .accepted,
        isFalse);
    final next = request(completed.state, epoch.add(const Duration(minutes: 5)),
        const Duration(minutes: 5));
    final after = engine
        .advance(completed.state, const Duration(minutes: 5),
            offline: true, offlineSettlement: next)
        .state;
    expect(after.lifetimeMicros, r(600));
    expect(after.support.closedSettlementIds, {'opaque-pending'});
  });
  test('legacywithoutclockrequirespersistedenvelopecursorbeforecapture', () {
    final raw = fixture('state-v3');
    final daily = DailyState().toJson()..remove('discovery_sequence');
    raw['daily'] = daily;
    (raw['support'] as Map)['tokens'] = [];
    (raw['support'] as Map)['token_day'] = -1;
    var state = GameState.fromJson(raw);
    expect(state.support.receiptCursorMigrationRequired, isTrue);
    final from = epoch.add(const Duration(minutes: 5));
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true,
                offlineSettlement:
                    request(state, from, const Duration(minutes: 5)))
            .accepted,
        isFalse);
    state = engine.initializeReceiptCursor(state, from).state;
    expect(state.walletMicros, r(600));
    expect(state.support.receiptCursorMigrationRequired, isFalse);
    expect(engine.initializeReceiptCursor(state, from).accepted, isFalse);
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true,
                offlineSettlement:
                    request(state, from, const Duration(minutes: 5)))
            .accepted,
        isTrue);
  });
  for (final stage in [CommitStage.afterFlush, CommitStage.afterRename]) {
    test(
        'partial sequence recovers atomically after ${stage.name} interruption',
        () async {
      final directory =
          await Directory.systemTemp.createTemp('sequence-recovery-');
      try {
        SaveRepository repository({CommitProbe? probe}) => SaveRepository(
            directory,
            economicVersion: economyVersion,
            economicDigest:
                '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',
            now: () => epoch,
            commitProbe: probe,
            validatePayload: (p) =>
                GameState.fromJson(Map<String, dynamic>.from(p['core'])));
        final initial = ready();
        final identity = request(initial, epoch, const Duration(minutes: 10));
        final partial = engine
            .advance(initial, const Duration(minutes: 5),
                offline: true,
                offlineSettlement: identity,
                finalizeOfflineSettlement: false)
            .state;
        final original = repository();
        await original.load();
        await original.save({'core': partial.toJson()},
            settledThrough: epoch.add(const Duration(minutes: 5)));
        final interrupted = repository(probe: (point) async {
          if (point == stage)
            throw const FileSystemException('injected settlement interruption');
        });
        await interrupted.load();
        final complete = engine
            .advance(partial, const Duration(minutes: 5),
                offline: true,
                offlineSettlement: identity,
                offlineElapsedBefore: const Duration(minutes: 5))
            .state;
        await expectLater(
            interrupted.save({'core': complete.toJson()},
                settledThrough: epoch.add(const Duration(minutes: 10))),
            throwsA(isA<FileSystemException>()));
        final recoveredRepository = repository();
        final snapshot = (await recoveredRepository.load()).snapshot!;
        var recovered = GameState.fromJson(
            Map<String, dynamic>.from(snapshot.payload['core']));
        if (stage == CommitStage.afterFlush) {
          expect(recovered.lifetimeMicros, r(300));
          expect(recovered.support.lastSettlementSequence, BigInt.zero);
          expect(recovered.support.activeSettlementRequest!.sameAs(identity),
              isTrue);
          recovered = engine
              .advance(recovered, const Duration(minutes: 5),
                  offline: true,
                  offlineSettlement: identity,
                  offlineElapsedBefore: const Duration(minutes: 5))
              .state;
          await recoveredRepository.save({'core': recovered.toJson()},
              settledThrough: epoch.add(const Duration(minutes: 10)));
        }
        expect(recovered.toJson(), complete.toJson());
        expect(recovered.lifetimeMicros, r(600));
        expect(recovered.support.lastSettlementSequence, BigInt.one);
        expect(
            engine
                .advance(recovered, const Duration(minutes: 10),
                    offline: true, offlineSettlement: identity)
                .accepted,
            isFalse);
      } finally {
        await directory.delete(recursive: true);
      }
    });
  }
  test(
      'twentyyearsofrepeatedinteractionsretainboundedreceiptsandoldreplaysreject',
      () {
    var state = ready();
    final firstDiscovery = state.nextDiscoverySequence;
    final firstRequest = request(state, epoch, const Duration(minutes: 5));
    var cursor = epoch;
    for (var day = 0; day < 20 * 365; day++) {
      cursor = epoch.add(Duration(days: day));
      state = engine.refreshContracts(state, cursor).state;
      for (var action = 0; action < 12; action++) {
        state = engine
            .recordDiscovery(state, 'archive',
                operationSequence: state.nextDiscoverySequence)
            .state;
        final identity = request(state, cursor, const Duration(minutes: 5));
        final result = engine.advance(state, const Duration(minutes: 5),
            offline: true, offlineSettlement: identity);
        expect(result.accepted, isTrue);
        state = result.state;
        cursor = cursor.add(const Duration(minutes: 5));
      }
      for (var slot = 0; slot < 6; slot++) {
        final result = engine.claimSupportToken(state,
            accountDay: state.daily.dayHighWater,
            slot: slot,
            sourceId: engine.briefingSourceId(state, slot));
        expect(result.accepted, isTrue);
        state = result.state;
        final cache = state.support.caches[slot];
        final claim = engine.claimSalvageCache(
            state, state.support.tokens.last.id, cache.id);
        expect(claim.accepted, isTrue);
        state = claim.state;
      }
      if (day % 365 == 0) {
        state = GameState.fromJson(
            jsonDecode(jsonEncode(state.toJson())) as Map<String, dynamic>);
        expect(utf8.encode(jsonEncode(state.toJson())).length, lessThan(25000));
      }
    }
    expect(state.daily.discoverySequence, BigInt.from(20 * 365 * 12));
    expect(state.support.lastSettlementSequence, BigInt.from(20 * 365 * 12));
    expect(state.daily.discoveryOperationIds, isEmpty);
    expect(state.support.closedSettlementIds, isEmpty);
    expect(state.support.grantSourceIds, isEmpty);
    expect(state.support.legacyClaimedSliceIds, isEmpty);
    expect(state.support.tokens.length, 6);
    expect(state.dailyContracts.length, 21);
    expect(
        engine
            .recordDiscovery(state, 'archive',
                operationSequence: firstDiscovery)
            .accepted,
        isFalse);
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true, offlineSettlement: firstRequest)
            .accepted,
        isFalse);
    expect(
        engine
            .advance(state, const Duration(minutes: 5),
                offline: true,
                offlineSettlement:
                    request(state, epoch, const Duration(minutes: 5)))
            .accepted,
        isFalse);
    final finalBytes = utf8.encode(jsonEncode(state.toJson())).length;
    expect(finalBytes, lessThan(25000));
    print(jsonEncode({
      'receipt_workload_years': 20,
      'discovery_operations': state.daily.discoverySequence.toString(),
      'settlements': state.support.lastSettlementSequence.toString(),
      'salvage_claims': 20 * 365 * 6,
      'serialized_core_bytes': finalBytes,
      'cached_slices': state.support.caches.length,
      'retained_current_slice_claims': state.support.claimedSliceIds.length
    }));
  }, timeout: const Timeout(Duration(minutes: 2)));
}
