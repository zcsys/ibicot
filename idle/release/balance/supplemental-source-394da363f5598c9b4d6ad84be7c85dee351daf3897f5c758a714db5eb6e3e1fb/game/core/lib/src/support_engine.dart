part of 'engine.dart';

extension TideglassSupport on TideglassEngine {
  static final _sliceMicros = BigInt.from(300000000);
  static final _sliceDenominator = Fixed.scale * BigInt.from(4);

  String briefingSourceId(GameState state, int slot) =>
      'briefing:${state.daily.accountSeed}:${state.daily.dayHighWater}:$slot';

  /// Digest is metadata from an externally verified completion, not proof.
  String adSupportSourceId(
          GameState state, int slot, String verifiedReceiptDigest) =>
      'ad:${state.daily.accountSeed}:${state.daily.dayHighWater}:$slot:$verifiedReceiptDigest';

  /// Explicit recovery handshake for a legacy save lacking an account clock.
  /// The caller supplies its independently persisted envelope cursor.
  TransitionResult initializeReceiptCursor(
      GameState state, DateTime persistedCursorUtc) {
    if (!state.support.receiptCursorMigrationRequired ||
        state.support.activeSettlementId != null)
      return _reject(state, 'receipt_cursor_migration_not_available');
    final cursor =
        BigInt.from(persistedCursorUtc.toUtc().microsecondsSinceEpoch);
    if (cursor.isNegative) return _reject(state, 'invalid_receipt_cursor');
    return TransitionResult(state.copyWith(
        support: state.support.copyWith(
            lastSettlementThroughUtcMicros: cursor,
            receiptCursorMigrationRequired: false),
        revision: state.revision + 1));
  }

  /// Trusted-adapter boundary: an 'ad' label is NOT verification. The adapter
  /// validates completion first. No-fill/failure does not invoke this command.
  TransitionResult claimSupportToken(
    GameState state, {
    required int accountDay,
    required int slot,
    required String sourceId,
    String route = 'briefing',
  }) {
    if (!state.daily.initialized || accountDay != state.daily.dayHighWater)
      return _reject(state, 'support_account_day_mismatch');
    if (slot < 0 ||
        slot > 5 ||
        sourceId.isEmpty ||
        !{'briefing', 'ad'}.contains(route))
      return _reject(state, 'invalid_support_grant');
    final support = _syncSupportDay(state).support;
    if (support.grantSourceIds.contains(sourceId))
      return _reject(state, 'support_source_already_used');
    final expected = briefingSourceId(state, slot);
    final adPrefix = 'ad:${state.daily.accountSeed}:$accountDay:$slot:';
    if ((route == 'briefing' && sourceId != expected) ||
        (route == 'ad' &&
            (!sourceId.startsWith(adPrefix) ||
                !RegExp(r'^[0-9a-f]{64}$')
                    .hasMatch(sourceId.substring(adPrefix.length)))))
      return _reject(state, 'support_source_not_bound_to_day_and_slot');
    if (support.tokens.any((token) => token.slot == slot))
      return _reject(state, 'support_slot_already_granted');
    final token = SupportToken(
        id: 'support:${state.daily.accountSeed}:$accountDay:$slot',
        sourceId: sourceId,
        route: route,
        accountDay: accountDay,
        slot: slot);
    final after = state.copyWith(
        support: support.copyWith(tokens: [...support.tokens, token]),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'support_granted', details: {
        'token_id': token.id,
        'source_id': sourceId,
        'account_day': accountDay,
        'slot': slot,
        'route': route,
      })
    ]);
  }

  SupportToken? _availableToken(GameState state, String id) {
    if (state.support.tokenDay != state.daily.dayHighWater) return null;
    for (final token in state.support.tokens) {
      if (token.id == id && !token.spent) return token;
    }
    return null;
  }

  TransitionResult useSupportBoost(GameState state, String tokenId) {
    final token = _availableToken(state, tokenId);
    if (token == null) return _reject(state, 'support_token_unavailable');
    final after = state.copyWith(
        support: state.support.copyWith(
            remainingMicros:
                state.support.remainingMicros + BigInt.from(1200000000),
            tokens: state.support.tokens
                .map((t) => t.id == tokenId ? t.consume() : t)
                .toList()),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'support_boost_queued', details: {
        'token_id': tokenId,
        'receipt_id': 'consume:$tokenId',
        'seconds': 1200,
      })
    ]);
  }

  BigInt salvageBonusMicros(SalvageCache cache) {
    final rate = cache.settlementRateRaw;
    if (rate == null) return BigInt.zero;
    final cap = rate * BigInt.from(300000000) ~/ Fixed.scale;
    return cache.unboostedMicros < cap ? cache.unboostedMicros : cap;
  }

  /// Token consumption, genuine slice claim, and wallet/lifetime reward form
  /// one immutable transition. Persist the complete result as one commit.
  TransitionResult claimSalvageCache(
      GameState state, String tokenId, String cacheId) {
    if (_availableToken(state, tokenId) == null)
      return _reject(state, 'support_token_unavailable');
    final matches = state.support.caches.where((c) => c.id == cacheId);
    if (matches.isEmpty) return _reject(state, 'salvage_cache_unavailable');
    final cache = matches.single;
    if (cache.settlementRateRaw == null ||
        state.support.activeSettlementId != null)
      return _reject(state, 'offline_settlement_not_finalized');
    if (state.support.claimedSliceIds.contains(cacheId))
      return _reject(state, 'salvage_cache_already_claimed');
    final bonus = salvageBonusMicros(cache);
    if (bonus == BigInt.zero) return _reject(state, 'salvage_cache_empty');
    final after = state.copyWith(
        walletMicros: state.walletMicros + bonus,
        lifetimeMicros: state.lifetimeMicros + bonus,
        support: state.support.copyWith(
            tokens: state.support.tokens
                .map((t) => t.id == tokenId ? t.consume() : t)
                .toList(),
            caches: state.support.caches
                .map((c) => c.id == cacheId ? c.claim() : c)
                .toList()),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'salvage_claimed', details: {
        'token_id': tokenId,
        'cache_id': cacheId,
        'settlement_id': cache.settlementId,
        'receipt_id': 'consume:$tokenId',
        'slice_receipt_id': 'salvage:$cacheId',
        'bonus_micros': bonus.toString(),
      })
    ]);
  }

  GameState _syncSupportDay(GameState state) {
    if (!state.daily.initialized ||
        state.support.tokenDay == state.daily.dayHighWater) return state;
    return state.copyWith(
        support: state.support
            .copyWith(tokenDay: state.daily.dayHighWater, tokens: []));
  }

  SupportState _captureSlice(SupportState support, BigInt offset, BigInt step,
      BigInt unboostedRate, int weight) {
    if (support.activeSettlementId == null) return support;
    final next = offset + step;
    if (offset >= TideglassEngine.totalOfflineMicros) {
      return support.copyWith(
          nextOffsetMicros: next,
          sliceStartOffsetMicros: next,
          sliceNumerator: BigInt.zero);
    }
    final numerator =
        support.sliceNumerator + unboostedRate * step * BigInt.from(weight);
    if (next - support.sliceStartOffsetMicros < _sliceMicros) {
      return support.copyWith(
          nextOffsetMicros: next, sliceNumerator: numerator);
    }
    final id =
        '${support.activeSettlementId}:${support.sliceStartOffsetMicros}';
    final cache = SalvageCache(
        id: id,
        settlementId: support.activeSettlementId!,
        startElapsedMicros:
            support.sourceStartElapsedMicros + support.sliceStartOffsetMicros,
        endElapsedMicros: support.sourceStartElapsedMicros + next,
        unboostedMicros: numerator ~/ _sliceDenominator);
    final caches = [...support.caches, cache];
    if (caches.length > 6) caches.removeAt(0);
    return support.copyWith(
        caches: caches,
        nextOffsetMicros: next,
        sliceStartOffsetMicros: next,
        sliceNumerator: BigInt.zero);
  }
}
