/// Persisted daily content and player policy. These types carry data only;
/// rewards and transitions remain in TideglassEngine.
class DailyContract {
  final String id;
  final int accountDay;
  final int slot;
  final String kind;
  final String? discoveryKind;
  final BigInt target;
  final BigInt rateSnapshotRaw;
  final BigInt cheapestPriceSnapshotMicros;
  final BigInt lifetimeBaselineMicros;
  final BigInt purchasedBaseline;
  final BigInt discoveryBaseline;
  final bool rerolled;
  final bool claimed;
  final String? creditedPassId;

  DailyContract(
      {required this.id,
      required this.accountDay,
      required this.slot,
      required this.kind,
      this.discoveryKind,
      required this.target,
      required this.rateSnapshotRaw,
      required this.cheapestPriceSnapshotMicros,
      required this.lifetimeBaselineMicros,
      required this.purchasedBaseline,
      required this.discoveryBaseline,
      this.rerolled = false,
      this.claimed = false,
      this.creditedPassId}) {
    if (id.isEmpty ||
        accountDay < 0 ||
        slot < 0 ||
        slot > 2 ||
        !{'restore', 'build', 'discover'}.contains(kind) ||
        target <= BigInt.zero ||
        rateSnapshotRaw <= BigInt.zero ||
        cheapestPriceSnapshotMicros <= BigInt.zero ||
        lifetimeBaselineMicros.isNegative ||
        purchasedBaseline.isNegative ||
        discoveryBaseline.isNegative ||
        (kind == 'discover' && discoveryKind == null) ||
        (kind != 'discover' && discoveryKind != null) ||
        claimed != (creditedPassId != null)) {
      throw ArgumentError('Invalid daily contract');
    }
  }

  DailyContract withClaim(String passId) => DailyContract(
      id: id,
      accountDay: accountDay,
      slot: slot,
      kind: kind,
      discoveryKind: discoveryKind,
      target: target,
      rateSnapshotRaw: rateSnapshotRaw,
      cheapestPriceSnapshotMicros: cheapestPriceSnapshotMicros,
      lifetimeBaselineMicros: lifetimeBaselineMicros,
      purchasedBaseline: purchasedBaseline,
      discoveryBaseline: discoveryBaseline,
      rerolled: rerolled,
      claimed: true,
      creditedPassId: passId);

  Map<String, dynamic> toJson() => {
        'id': id,
        'account_day': accountDay,
        'slot': slot,
        'kind': kind,
        'discovery_kind': discoveryKind,
        'target': target.toString(),
        'rate_snapshot_raw': rateSnapshotRaw.toString(),
        'cheapest_price_snapshot_micros':
            cheapestPriceSnapshotMicros.toString(),
        'lifetime_baseline_micros': lifetimeBaselineMicros.toString(),
        'purchased_baseline': purchasedBaseline.toString(),
        'discovery_baseline': discoveryBaseline.toString(),
        'rerolled': rerolled,
        'claimed': claimed,
        'credited_pass_id': creditedPassId,
      };

  factory DailyContract.fromJson(Map<String, dynamic> json) => DailyContract(
      id: json['id'] as String,
      accountDay: json['account_day'] as int,
      slot: json['slot'] as int,
      kind: json['kind'] as String,
      discoveryKind: json['discovery_kind'] as String?,
      target: parseNonnegativeInteger(json['target']),
      rateSnapshotRaw: parseNonnegativeInteger(json['rate_snapshot_raw']),
      cheapestPriceSnapshotMicros:
          parseNonnegativeInteger(json['cheapest_price_snapshot_micros']),
      lifetimeBaselineMicros:
          parseNonnegativeInteger(json['lifetime_baseline_micros']),
      purchasedBaseline: parseNonnegativeInteger(json['purchased_baseline']),
      discoveryBaseline: parseNonnegativeInteger(json['discovery_baseline']),
      rerolled: json['rerolled'] as bool,
      claimed: json['claimed'] as bool,
      creditedPassId: json['credited_pass_id'] as String?);
}

class AutomationPlan {
  final String id;
  final String name;
  final String purchasePolicy;
  final List<int> tierPriority;
  final bool autoResetEnabled;
  final BigInt minimumAdditionalCharts;
  final int minimumRunSeconds;

  AutomationPlan(
      {required this.id,
      required this.name,
      this.purchasePolicy = 'greedy',
      List<int> tierPriority = const [4, 3, 2, 1, 0],
      this.autoResetEnabled = false,
      BigInt? minimumAdditionalCharts,
      this.minimumRunSeconds = 600})
      : tierPriority = List.unmodifiable(tierPriority),
        minimumAdditionalCharts = minimumAdditionalCharts ?? BigInt.one {
    if (id.isEmpty ||
        name.isEmpty ||
        name.length > 120 ||
        !{'greedy', 'priority'}.contains(purchasePolicy) ||
        tierPriority.length != 5 ||
        tierPriority.toSet().length != 5 ||
        tierPriority.any((tier) => tier < 0 || tier > 4) ||
        this.minimumAdditionalCharts <= BigInt.zero ||
        minimumRunSeconds <= 0) {
      throw ArgumentError('Invalid automation plan');
    }
  }

  factory AutomationPlan.base() =>
      AutomationPlan(id: 'plan.base', name: 'Base plan');
  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'purchase_policy': purchasePolicy,
        'tier_priority': tierPriority,
        'auto_reset_enabled': autoResetEnabled,
        'minimum_additional_charts': minimumAdditionalCharts.toString(),
        'minimum_run_seconds': minimumRunSeconds
      };
  factory AutomationPlan.fromJson(Map<String, dynamic> json) => AutomationPlan(
      id: json['id'] as String,
      name: json['name'] as String,
      purchasePolicy: json['purchase_policy'] as String,
      tierPriority: List<int>.from(json['tier_priority'] as List),
      autoResetEnabled: json['auto_reset_enabled'] as bool,
      minimumAdditionalCharts:
          parseNonnegativeInteger(json['minimum_additional_charts']),
      minimumRunSeconds: json['minimum_run_seconds'] as int);
}

class DailyState {
  final String? accountSeed;
  final int utcOffsetMinutes;
  final int dayHighWater;
  final int lastMaterializedDay;
  final BigInt? utcAnchorMicros;
  final List<String> availableDiscoveryKinds;
  final List<DailyContract> contracts;
  final Map<String, BigInt> discoveryTotals;

  /// Frozen legacy opaque identities; new discovery uses a monotone sequence.
  final Set<String> discoveryOperationIds;
  final BigInt discoverySequence;
  BigInt get nextDiscoverySequence => discoverySequence + BigInt.one;
  final String selectedPassId;
  final Map<String, BigInt> passXpById;

  DailyState(
      {this.accountSeed,
      this.utcOffsetMinutes = 0,
      this.dayHighWater = -1,
      this.lastMaterializedDay = -1,
      this.utcAnchorMicros,
      List<String> availableDiscoveryKinds = const [],
      List<DailyContract> contracts = const [],
      Map<String, BigInt> discoveryTotals = const {},
      Set<String> discoveryOperationIds = const {},
      BigInt? discoverySequence,
      this.selectedPassId = 'pass.01',
      Map<String, BigInt>? passXpById})
      : availableDiscoveryKinds = List.unmodifiable(availableDiscoveryKinds),
        contracts = List.unmodifiable(contracts),
        discoveryTotals = Map.unmodifiable(discoveryTotals),
        discoveryOperationIds = Set.unmodifiable(discoveryOperationIds),
        discoverySequence = discoverySequence ?? BigInt.zero,
        passXpById = Map.unmodifiable(passXpById ?? {'pass.01': BigInt.zero}) {
    if (this.discoverySequence.isNegative ||
        utcOffsetMinutes < -720 ||
        utcOffsetMinutes > 840 ||
        dayHighWater < -1 ||
        lastMaterializedDay < -1 ||
        lastMaterializedDay > dayHighWater ||
        contracts.length > 21 ||
        contracts.map((c) => c.id).toSet().length != contracts.length ||
        (accountSeed == null) != (utcAnchorMicros == null) ||
        (accountSeed == null && (dayHighWater != -1 || contracts.isNotEmpty)) ||
        (accountSeed != null &&
            !RegExp(r'^[A-Za-z0-9_-]{1,128}$').hasMatch(accountSeed!)) ||
        availableDiscoveryKinds.any((kind) =>
            !{'calibration', 'archive', 'challenge'}.contains(kind)) ||
        availableDiscoveryKinds.toSet().length !=
            availableDiscoveryKinds.length ||
        discoveryTotals.values.any((count) => count.isNegative) ||
        this.passXpById.values.any((xp) => xp.isNegative) ||
        !this.passXpById.containsKey(selectedPassId)) {
      throw ArgumentError('Invalid daily state');
    }
    for (final contract in contracts) {
      if (contract.accountDay > dayHighWater ||
          contract.accountDay < dayHighWater - 6 ||
          contract.id !=
              'contract:$accountSeed:${contract.accountDay}:${contract.slot}') {
        throw ArgumentError(
            'Contract does not belong to retained account-day slot');
      }
    }
  }

  bool get initialized => accountSeed != null;
  BigInt get passXp => passXpById[selectedPassId]!;

  DailyState copyWith(
          {String? accountSeed,
          int? utcOffsetMinutes,
          int? dayHighWater,
          int? lastMaterializedDay,
          BigInt? utcAnchorMicros,
          List<String>? availableDiscoveryKinds,
          List<DailyContract>? contracts,
          Map<String, BigInt>? discoveryTotals,
          Set<String>? discoveryOperationIds,
          BigInt? discoverySequence,
          String? selectedPassId,
          Map<String, BigInt>? passXpById}) =>
      DailyState(
          accountSeed: accountSeed ?? this.accountSeed,
          utcOffsetMinutes: utcOffsetMinutes ?? this.utcOffsetMinutes,
          dayHighWater: dayHighWater ?? this.dayHighWater,
          lastMaterializedDay: lastMaterializedDay ?? this.lastMaterializedDay,
          utcAnchorMicros: utcAnchorMicros ?? this.utcAnchorMicros,
          availableDiscoveryKinds:
              availableDiscoveryKinds ?? this.availableDiscoveryKinds,
          contracts: contracts ?? this.contracts,
          discoveryTotals: discoveryTotals ?? this.discoveryTotals,
          discoveryOperationIds:
              discoveryOperationIds ?? this.discoveryOperationIds,
          discoverySequence: discoverySequence ?? this.discoverySequence,
          selectedPassId: selectedPassId ?? this.selectedPassId,
          passXpById: passXpById ?? this.passXpById);

  Map<String, dynamic> toJson() => {
        'account_seed': accountSeed,
        'utc_offset_minutes': utcOffsetMinutes,
        'day_high_water': dayHighWater,
        'last_materialized_day': lastMaterializedDay,
        'utc_anchor_micros': utcAnchorMicros?.toString(),
        'available_discovery_kinds': availableDiscoveryKinds,
        'contracts': contracts.map((c) => c.toJson()).toList(),
        'discovery_totals': discoveryTotals
            .map((key, value) => MapEntry(key, value.toString())),
        'discovery_operation_ids': discoveryOperationIds.toList()..sort(),
        'discovery_sequence': discoverySequence.toString(),
        'selected_pass_id': selectedPassId,
        'pass_xp_by_id':
            passXpById.map((key, value) => MapEntry(key, value.toString()))
      };

  factory DailyState.fromJson(Map<String, dynamic> json,
          {bool legacy = false}) =>
      DailyState(
          discoverySequence: legacy
              ? BigInt.zero
              : parseNonnegativeInteger(json['discovery_sequence']),
          accountSeed: json['account_seed'] as String?,
          utcOffsetMinutes: json['utc_offset_minutes'] as int,
          dayHighWater: json['day_high_water'] as int,
          lastMaterializedDay: json['last_materialized_day'] as int,
          utcAnchorMicros: json['utc_anchor_micros'] == null
              ? null
              : BigInt.parse(json['utc_anchor_micros'] as String),
          availableDiscoveryKinds:
              List<String>.from(json['available_discovery_kinds'] as List),
          contracts: (json['contracts'] as List)
              .map((c) =>
                  DailyContract.fromJson(Map<String, dynamic>.from(c as Map)))
              .toList(),
          discoveryTotals: (json['discovery_totals'] as Map).map((key, value) =>
              MapEntry(key as String, parseNonnegativeInteger(value))),
          discoveryOperationIds:
              Set<String>.from(json['discovery_operation_ids'] as List),
          selectedPassId: json['selected_pass_id'] as String,
          passXpById: (json['pass_xp_by_id'] as Map).map((key, value) =>
              MapEntry(key as String, parseNonnegativeInteger(value))));
}

BigInt parseNonnegativeInteger(Object? value) {
  if (value is! String || !RegExp(r'^(0|[1-9][0-9]*)$').hasMatch(value)) {
    throw const FormatException(
        'Expected a canonical nonnegative integer string');
  }
  return BigInt.parse(value);
}

/// Portable stable FNV-1a hash; never Dart's process-dependent String.hashCode.
int stableContractSeed(String value) {
  var result = BigInt.parse('14695981039346656037');
  final mask = (BigInt.one << 64) - BigInt.one;
  final prime = BigInt.parse('1099511628211');
  for (final code in value.codeUnits) {
    result = ((result ^ BigInt.from(code)) * prime) & mask;
  }
  return (result & BigInt.from(0x7fffffff)).toInt();
}
