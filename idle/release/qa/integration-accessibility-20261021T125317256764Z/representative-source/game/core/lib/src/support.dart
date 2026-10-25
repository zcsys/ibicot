import 'daily.dart';

/// Local transition ledger. Route labels are metadata, never evidence that an
/// advertisement was verified. Trusted adapters must validate completion first.
class SupportToken {
  final String id, sourceId, route;
  final int accountDay, slot;
  final bool spent;
  SupportToken(
      {required this.id,
      required this.sourceId,
      required this.route,
      required this.accountDay,
      required this.slot,
      this.spent = false}) {
    if (id.isEmpty ||
        sourceId.isEmpty ||
        accountDay < 0 ||
        slot < 0 ||
        slot > 5 ||
        !{'briefing', 'ad'}.contains(route))
      throw ArgumentError('Invalid Support token');
  }
  SupportToken consume() => SupportToken(
      id: id,
      sourceId: sourceId,
      route: route,
      accountDay: accountDay,
      slot: slot,
      spent: true);
  Map<String, dynamic> toJson() => {
        'id': id,
        'source_id': sourceId,
        'route': route,
        'account_day': accountDay,
        'slot': slot,
        'spent': spent
      };
  factory SupportToken.fromJson(Map<String, dynamic> json) {
    _keys(json, {'id', 'source_id', 'route', 'account_day', 'slot', 'spent'});
    return SupportToken(
        id: json['id'] as String,
        sourceId: json['source_id'] as String,
        route: json['route'] as String,
        accountDay: json['account_day'] as int,
        slot: json['slot'] as int,
        spent: json['spent'] as bool);
  }
}

class SalvageCache {
  final String id, settlementId;
  final BigInt startElapsedMicros, endElapsedMicros, unboostedMicros;
  final BigInt? settlementRateRaw;
  final bool claimed;
  SalvageCache(
      {required this.id,
      required this.settlementId,
      required this.startElapsedMicros,
      required this.endElapsedMicros,
      required this.unboostedMicros,
      this.settlementRateRaw,
      this.claimed = false}) {
    if (id.isEmpty ||
        settlementId.isEmpty ||
        startElapsedMicros.isNegative ||
        endElapsedMicros - startElapsedMicros != BigInt.from(300000000) ||
        unboostedMicros.isNegative ||
        (settlementRateRaw?.isNegative ?? false)) {
      throw ArgumentError('Invalid salvage slice');
    }
  }
  SalvageCache finalize(BigInt rate) => SalvageCache(
      id: id,
      settlementId: settlementId,
      startElapsedMicros: startElapsedMicros,
      endElapsedMicros: endElapsedMicros,
      unboostedMicros: unboostedMicros,
      settlementRateRaw: rate,
      claimed: claimed);
  SalvageCache claim() => SalvageCache(
      id: id,
      settlementId: settlementId,
      startElapsedMicros: startElapsedMicros,
      endElapsedMicros: endElapsedMicros,
      unboostedMicros: unboostedMicros,
      settlementRateRaw: settlementRateRaw,
      claimed: true);
  Map<String, dynamic> toJson() => {
        'id': id,
        'settlement_id': settlementId,
        'start_elapsed_micros': startElapsedMicros.toString(),
        'end_elapsed_micros': endElapsedMicros.toString(),
        'unboosted_micros': unboostedMicros.toString(),
        'settlement_rate_raw': settlementRateRaw?.toString(),
        'claimed': claimed
      };
  factory SalvageCache.fromJson(Map<String, dynamic> json,
      {bool legacy = false, bool legacyClaimed = false}) {
    final keys = {
      'id',
      'settlement_id',
      'start_elapsed_micros',
      'end_elapsed_micros',
      'unboosted_micros',
      'settlement_rate_raw'
    };
    if (!legacy) keys.add('claimed');
    _keys(json, keys);
    return SalvageCache(
        claimed: legacy ? legacyClaimed : json['claimed'] as bool,
        id: json['id'] as String,
        settlementId: json['settlement_id'] as String,
        startElapsedMicros:
            parseNonnegativeInteger(json['start_elapsed_micros']),
        endElapsedMicros: parseNonnegativeInteger(json['end_elapsed_micros']),
        unboostedMicros: parseNonnegativeInteger(json['unboosted_micros']),
        settlementRateRaw: json['settlement_rate_raw'] == null
            ? null
            : parseNonnegativeInteger(json['settlement_rate_raw']));
  }
}

/// Explicit UTC interval and monotone source sequence captured by the save
/// adapter before replay. Canonical identity cannot relabel an old interval.
class OfflineSettlementRequest {
  final BigInt sequence, fromUtcMicros, throughUtcMicros;
  OfflineSettlementRequest(
      {required this.sequence,
      required DateTime fromUtc,
      required DateTime throughUtc})
      : fromUtcMicros = BigInt.from(fromUtc.toUtc().microsecondsSinceEpoch),
        throughUtcMicros =
            BigInt.from(throughUtc.toUtc().microsecondsSinceEpoch) {
    _validate();
  }
  OfflineSettlementRequest._(
      this.sequence, this.fromUtcMicros, this.throughUtcMicros) {
    _validate();
  }
  void _validate() {
    if (sequence <= BigInt.zero ||
        fromUtcMicros.isNegative ||
        throughUtcMicros <= fromUtcMicros)
      throw ArgumentError('Invalid monotone offline interval.');
  }

  BigInt get durationMicros => throughUtcMicros - fromUtcMicros;
  String identity(String? accountSeed) =>
      'offline:${accountSeed ?? 'local'}:$sequence:$fromUtcMicros:$throughUtcMicros';
  bool sameAs(OfflineSettlementRequest other) =>
      sequence == other.sequence &&
      fromUtcMicros == other.fromUtcMicros &&
      throughUtcMicros == other.throughUtcMicros;
  Map<String, dynamic> toJson() => {
        'sequence': sequence.toString(),
        'from_utc_micros': fromUtcMicros.toString(),
        'through_utc_micros': throughUtcMicros.toString()
      };
  factory OfflineSettlementRequest.fromJson(Map<String, dynamic> json) {
    _keys(json, {'sequence', 'from_utc_micros', 'through_utc_micros'});
    return OfflineSettlementRequest._(
        parseNonnegativeInteger(json['sequence']),
        parseNonnegativeInteger(json['from_utc_micros']),
        parseNonnegativeInteger(json['through_utc_micros']));
  }
}

class SupportState {
  final BigInt remainingMicros;
  final int tokenDay;
  final List<SupportToken> tokens;
  final List<SalvageCache> caches;

  /// Frozen schema3 deny-lists. New production operations never append here.
  final Set<String> legacyClaimedSliceIds, closedSettlementIds, grantSourceIds;
  final BigInt lastSettlementSequence;
  final BigInt? lastSettlementThroughUtcMicros;
  final String? lastFinalizedSettlementId;
  final bool receiptCursorMigrationRequired;
  final String? activeSettlementId;
  final OfflineSettlementRequest? activeSettlementRequest;
  final BigInt sourceStartElapsedMicros,
      nextOffsetMicros,
      sliceStartOffsetMicros,
      sliceNumerator;
  BigInt get nextSettlementSequence => lastSettlementSequence + BigInt.one;
  bool get hasLegacyPendingSettlement =>
      activeSettlementId != null && activeSettlementRequest == null;

  /// Bounded compatibility projection for inventory UI; at most six values.
  Set<String> get claimedSliceIds => {
        for (final cache in caches)
          if (cache.claimed || legacyClaimedSliceIds.contains(cache.id))
            cache.id
      };
  SupportState(
      {BigInt? remainingMicros,
      this.tokenDay = -1,
      List<SupportToken> tokens = const [],
      List<SalvageCache> caches = const [],
      Set<String> legacyClaimedSliceIds = const {},
      Set<String> closedSettlementIds = const {},
      Set<String> grantSourceIds = const {},
      BigInt? lastSettlementSequence,
      this.lastSettlementThroughUtcMicros,
      this.lastFinalizedSettlementId,
      this.receiptCursorMigrationRequired = false,
      this.activeSettlementId,
      this.activeSettlementRequest,
      BigInt? sourceStartElapsedMicros,
      BigInt? nextOffsetMicros,
      BigInt? sliceStartOffsetMicros,
      BigInt? sliceNumerator})
      : remainingMicros = remainingMicros ?? BigInt.zero,
        tokens = List.unmodifiable(tokens),
        caches = List.unmodifiable(caches),
        legacyClaimedSliceIds = Set.unmodifiable(legacyClaimedSliceIds),
        closedSettlementIds = Set.unmodifiable(closedSettlementIds),
        grantSourceIds = Set.unmodifiable(grantSourceIds),
        lastSettlementSequence = lastSettlementSequence ?? BigInt.zero,
        sourceStartElapsedMicros = sourceStartElapsedMicros ?? BigInt.zero,
        nextOffsetMicros = nextOffsetMicros ?? BigInt.zero,
        sliceStartOffsetMicros = sliceStartOffsetMicros ?? BigInt.zero,
        sliceNumerator = sliceNumerator ?? BigInt.zero {
    if (this.remainingMicros.isNegative ||
        tokenDay < -1 ||
        tokens.length > 6 ||
        tokens.any((t) => t.accountDay != tokenDay) ||
        tokens.map((t) => t.slot).toSet().length != tokens.length ||
        tokens.map((t) => t.id).toSet().length != tokens.length ||
        tokens.map((t) => t.sourceId).toSet().length != tokens.length ||
        caches.length > 6 ||
        caches.map((c) => c.id).toSet().length != caches.length ||
        [
          this.sourceStartElapsedMicros,
          this.nextOffsetMicros,
          this.sliceStartOffsetMicros,
          this.sliceNumerator,
          this.lastSettlementSequence
        ].any((n) => n.isNegative) ||
        (lastSettlementThroughUtcMicros?.isNegative ?? false) ||
        (this.lastSettlementSequence > BigInt.zero &&
            lastSettlementThroughUtcMicros == null) ||
        this.sliceStartOffsetMicros > this.nextOffsetMicros ||
        this.nextOffsetMicros - this.sliceStartOffsetMicros >=
            BigInt.from(300000000) ||
        (activeSettlementId != null &&
            (activeSettlementId!.isEmpty ||
                closedSettlementIds.contains(activeSettlementId))) ||
        (activeSettlementRequest != null &&
            (activeSettlementId == null ||
                activeSettlementRequest!.sequence != nextSettlementSequence ||
                this.nextOffsetMicros >
                    activeSettlementRequest!.durationMicros ||
                (lastSettlementThroughUtcMicros != null &&
                    activeSettlementRequest!.fromUtcMicros <
                        lastSettlementThroughUtcMicros!))) ||
        (activeSettlementId == null &&
            (this.sourceStartElapsedMicros != BigInt.zero ||
                this.nextOffsetMicros != BigInt.zero ||
                this.sliceStartOffsetMicros != BigInt.zero ||
                this.sliceNumerator != BigInt.zero)))
      throw ArgumentError('Invalid Support ledger');
  }
  SupportState copyWith(
          {BigInt? remainingMicros,
          int? tokenDay,
          List<SupportToken>? tokens,
          List<SalvageCache>? caches,
          Set<String>? legacyClaimedSliceIds,
          Set<String>? closedSettlementIds,
          Set<String>? grantSourceIds,
          BigInt? lastSettlementSequence,
          BigInt? lastSettlementThroughUtcMicros,
          String? lastFinalizedSettlementId,
          bool? receiptCursorMigrationRequired,
          String? activeSettlementId,
          OfflineSettlementRequest? activeSettlementRequest,
          bool clearActiveSettlement = false,
          BigInt? sourceStartElapsedMicros,
          BigInt? nextOffsetMicros,
          BigInt? sliceStartOffsetMicros,
          BigInt? sliceNumerator}) =>
      SupportState(
          remainingMicros: remainingMicros ?? this.remainingMicros,
          tokenDay: tokenDay ?? this.tokenDay,
          tokens: tokens ?? this.tokens,
          caches: caches ?? this.caches,
          legacyClaimedSliceIds:
              legacyClaimedSliceIds ?? this.legacyClaimedSliceIds,
          closedSettlementIds: closedSettlementIds ?? this.closedSettlementIds,
          grantSourceIds: grantSourceIds ?? this.grantSourceIds,
          lastSettlementSequence:
              lastSettlementSequence ?? this.lastSettlementSequence,
          lastSettlementThroughUtcMicros: lastSettlementThroughUtcMicros ??
              this.lastSettlementThroughUtcMicros,
          lastFinalizedSettlementId:
              lastFinalizedSettlementId ?? this.lastFinalizedSettlementId,
          receiptCursorMigrationRequired: receiptCursorMigrationRequired ??
              this.receiptCursorMigrationRequired,
          activeSettlementId: clearActiveSettlement
              ? null
              : activeSettlementId ?? this.activeSettlementId,
          activeSettlementRequest: clearActiveSettlement
              ? null
              : activeSettlementRequest ?? this.activeSettlementRequest,
          sourceStartElapsedMicros: clearActiveSettlement
              ? BigInt.zero
              : sourceStartElapsedMicros ?? this.sourceStartElapsedMicros,
          nextOffsetMicros: clearActiveSettlement
              ? BigInt.zero
              : nextOffsetMicros ?? this.nextOffsetMicros,
          sliceStartOffsetMicros: clearActiveSettlement
              ? BigInt.zero
              : sliceStartOffsetMicros ?? this.sliceStartOffsetMicros,
          sliceNumerator: clearActiveSettlement
              ? BigInt.zero
              : sliceNumerator ?? this.sliceNumerator);
  Map<String, dynamic> toJson() => {
        'remaining_micros': remainingMicros.toString(),
        'token_day': tokenDay,
        'tokens': tokens.map((t) => t.toJson()).toList(),
        'caches': caches.map((c) => c.toJson()).toList(),
        'claimed_slice_ids': legacyClaimedSliceIds.toList()..sort(),
        'closed_settlement_ids': closedSettlementIds.toList()..sort(),
        'grant_source_ids': grantSourceIds.toList()..sort(),
        'last_settlement_sequence': lastSettlementSequence.toString(),
        'last_settlement_through_utc_micros':
            lastSettlementThroughUtcMicros?.toString(),
        'last_finalized_settlement_id': lastFinalizedSettlementId,
        'receipt_cursor_migration_required': receiptCursorMigrationRequired,
        'active_settlement_id': activeSettlementId,
        'active_settlement_request': activeSettlementRequest?.toJson(),
        'source_start_elapsed_micros': sourceStartElapsedMicros.toString(),
        'next_offset_micros': nextOffsetMicros.toString(),
        'slice_start_offset_micros': sliceStartOffsetMicros.toString(),
        'slice_numerator': sliceNumerator.toString()
      };
  factory SupportState.fromJson(Map<String, dynamic> json,
      {bool legacy = false, BigInt? migrationUtcMicros}) {
    final keys = {
      'remaining_micros',
      'token_day',
      'tokens',
      'caches',
      'claimed_slice_ids',
      'closed_settlement_ids',
      'grant_source_ids',
      'active_settlement_id',
      'source_start_elapsed_micros',
      'next_offset_micros',
      'slice_start_offset_micros',
      'slice_numerator'
    };
    if (!legacy)
      keys.addAll({
        'last_settlement_sequence',
        'last_settlement_through_utc_micros',
        'last_finalized_settlement_id',
        'receipt_cursor_migration_required',
        'active_settlement_request'
      });
    _keys(json, keys);
    final claims = _strings(json['claimed_slice_ids']);
    final closed = _strings(json['closed_settlement_ids']);
    return SupportState(
        remainingMicros: parseNonnegativeInteger(json['remaining_micros']),
        tokenDay: json['token_day'] as int,
        tokens: (json['tokens'] as List)
            .map((t) => SupportToken.fromJson(Map<String, dynamic>.from(t)))
            .toList(),
        caches: (json['caches'] as List)
            .map((c) => SalvageCache.fromJson(Map<String, dynamic>.from(c),
                legacy: legacy, legacyClaimed: claims.contains(c['id'])))
            .toList(),
        legacyClaimedSliceIds: claims,
        closedSettlementIds: closed,
        grantSourceIds: _strings(json['grant_source_ids']),
        lastSettlementSequence: legacy
            ? BigInt.zero
            : parseNonnegativeInteger(json['last_settlement_sequence']),
        lastSettlementThroughUtcMicros: legacy
            ? migrationUtcMicros
            : json['last_settlement_through_utc_micros'] == null
                ? null
                : parseNonnegativeInteger(
                    json['last_settlement_through_utc_micros']),
        lastFinalizedSettlementId:
            legacy ? null : json['last_finalized_settlement_id'] as String?,
        receiptCursorMigrationRequired: legacy
            ? (migrationUtcMicros == null && closed.isNotEmpty)
            : json['receipt_cursor_migration_required'] as bool,
        activeSettlementId: json['active_settlement_id'] as String?,
        activeSettlementRequest: legacy ||
                json['active_settlement_request'] == null
            ? null
            : OfflineSettlementRequest.fromJson(
                Map<String, dynamic>.from(json['active_settlement_request'])),
        sourceStartElapsedMicros:
            parseNonnegativeInteger(json['source_start_elapsed_micros']),
        nextOffsetMicros: parseNonnegativeInteger(json['next_offset_micros']),
        sliceStartOffsetMicros:
            parseNonnegativeInteger(json['slice_start_offset_micros']),
        sliceNumerator: parseNonnegativeInteger(json['slice_numerator']));
  }
}

Set<String> _strings(Object? raw) {
  final list = List<String>.from(raw as List);
  if (list.toSet().length != list.length || list.any((v) => v.isEmpty))
    throw const FormatException('Invalid legacy receipt list.');
  return list.toSet();
}

void _keys(Map<String, dynamic> json, Set<String> keys) {
  if (json.length != keys.length || !json.keys.every(keys.contains))
    throw const FormatException('Unexpected or missing Support fields');
}
