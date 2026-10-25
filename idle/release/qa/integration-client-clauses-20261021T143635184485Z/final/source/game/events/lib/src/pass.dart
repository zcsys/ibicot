import 'package:tideglass_core/tideglass_core.dart';
import 'definition.dart';
import 'season.dart';

/// Trusted store/account adapter. Offline cached verification and revocation
/// belong to the adapter; a local boolean is never accepted as ownership.
abstract interface class VerifiedPassEntitlementReader {
  Future<VerifiedPassEntitlement?> read(
      {required String accountId, required String passId});
}

class VerifiedPassEntitlement {
  final String accountId, passId, verificationReceiptId, authority;
  VerifiedPassEntitlement(
      {required this.accountId,
      required this.passId,
      required this.verificationReceiptId,
      required this.authority}) {
    if ([accountId, passId, verificationReceiptId, authority]
        .any((v) => v.isEmpty))
      throw ArgumentError('Verified entitlement identity is incomplete.');
  }
}

/// Local delivery metadata only; serialized verification IDs do not prove ownership.
class PassReceipt {
  final String accountId, passId, rewardId, receiptId;
  final String? entitlementVerificationReceiptId;
  PassReceipt._(this.accountId, this.passId, this.rewardId, this.receiptId,
      this.entitlementVerificationReceiptId);
  Map<String, dynamic> toJson() => {
        'account_id': accountId,
        'pass_id': passId,
        'reward_id': rewardId,
        'receipt_id': receiptId,
        'entitlement_verification_receipt_id': entitlementVerificationReceiptId
      };
  factory PassReceipt.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {
      'account_id',
      'pass_id',
      'reward_id',
      'receipt_id',
      'entitlement_verification_receipt_id'
    });
    return PassReceipt._(
        json['account_id'] as String,
        json['pass_id'] as String,
        json['reward_id'] as String,
        json['receipt_id'] as String,
        json['entitlement_verification_receipt_id'] as String?);
  }
}

/// One frozen event-production replacement for a retained daily slot. No XP is
/// stored here; actual completion is checked against the current pinned run.
class SeasonContractBinding {
  final String contractId,
      contractFingerprint,
      accountId,
      seasonId,
      runId,
      rulesDigest;
  final BigInt baselineMicros, targetMicros, rateSnapshotRaw;
  SeasonContractBinding._(
      this.contractId,
      this.contractFingerprint,
      this.accountId,
      this.seasonId,
      this.runId,
      this.rulesDigest,
      this.baselineMicros,
      this.targetMicros,
      this.rateSnapshotRaw) {
    if ([
          contractId,
          contractFingerprint,
          accountId,
          seasonId,
          runId,
          rulesDigest
        ].any((s) => s.isEmpty) ||
        baselineMicros.isNegative ||
        targetMicros <= BigInt.zero ||
        rateSnapshotRaw <= BigInt.zero ||
        targetMicros !=
            ceilDivide(rateSnapshotRaw * BigInt.from(600), Fixed.scale) *
                BigInt.from(1000000))
      throw const FormatException('Invalid frozen season contract binding.');
  }
  Map<String, dynamic> toJson() => {
        'contract_id': contractId,
        'contract_fingerprint': contractFingerprint,
        'account_id': accountId,
        'season_id': seasonId,
        'run_id': runId,
        'rules_digest': rulesDigest,
        'baseline_micros': baselineMicros.toString(),
        'target_micros': targetMicros.toString(),
        'rate_snapshot_raw': rateSnapshotRaw.toString()
      };
  factory SeasonContractBinding.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {
      'contract_id',
      'contract_fingerprint',
      'account_id',
      'season_id',
      'run_id',
      'rules_digest',
      'baseline_micros',
      'target_micros',
      'rate_snapshot_raw'
    });
    return SeasonContractBinding._(
        json['contract_id'] as String,
        json['contract_fingerprint'] as String,
        json['account_id'] as String,
        json['season_id'] as String,
        json['run_id'] as String,
        json['rules_digest'] as String,
        parseNonnegativeInteger(json['baseline_micros']),
        parseNonnegativeInteger(json['target_micros']),
        parseNonnegativeInteger(json['rate_snapshot_raw']));
  }
}

String _contractFingerprint(DailyContract contract) {
  final snapshot = contract.toJson()
    ..remove('claimed')
    ..remove('credited_pass_id');
  return canonicalDigest(snapshot);
}

class PassState {
  final Map<String, String> definitionDigests;
  final Map<String, PassReceipt> claims;
  final Map<String, SeasonContractBinding> alternatives;
  PassState._(
      Map<String, String> definitionDigests,
      Map<String, PassReceipt> claims,
      Map<String, SeasonContractBinding> alternatives)
      : definitionDigests = Map.unmodifiable(definitionDigests),
        claims = Map.unmodifiable(claims),
        alternatives = Map.unmodifiable(alternatives);
  factory PassState.initial(Iterable<SeasonDefinition> definitions) =>
      PassState._({for (final d in definitions) d.passId: d.digest}, {}, {});
  PassState _copy(
          {Map<String, PassReceipt>? claims,
          Map<String, SeasonContractBinding>? alternatives}) =>
      PassState._(definitionDigests, claims ?? this.claims,
          alternatives ?? this.alternatives);
  Map<String, dynamic> toJson() => {
        'schema_version': 1,
        'definition_digests': definitionDigests,
        'claims': claims.map((id, r) => MapEntry(id, r.toJson())),
        'alternatives': alternatives.map((id, b) => MapEntry(id, b.toJson()))
      };
  factory PassState.fromJson(
      Map<String, dynamic> json, Iterable<SeasonDefinition> definitions) {
    exactKeys(json,
        {'schema_version', 'definition_digests', 'claims', 'alternatives'});
    if (json['schema_version'] != 1)
      throw const FormatException('Unsupported pass state.');
    final result = PassState._(
        Map<String, String>.from(json['definition_digests']),
        (json['claims'] as Map).map((id, r) => MapEntry(
            id as String, PassReceipt.fromJson(Map<String, dynamic>.from(r)))),
        (json['alternatives'] as Map).map((id, b) => MapEntry(id as String,
            SeasonContractBinding.fromJson(Map<String, dynamic>.from(b)))));
    PassEngine(definitions).validate(result);
    return result;
  }
}

class PassTransition {
  final GameState main;
  final PassState pass;
  final bool accepted;
  final String? reason;
  final PassReceipt? rewardReceipt;
  final List<CoreEvent> events;
  PassTransition(this.main, this.pass,
      {this.accepted = true,
      this.reason,
      this.rewardReceipt,
      List<CoreEvent> events = const []})
      : events = List.unmodifiable(events);
}

class _SeasonAlternative implements DailyContractAlternative {
  final SeasonContractBinding binding;
  final SeasonState current;
  _SeasonAlternative(this.binding, this.current);
  @override
  String get contractId => binding.contractId;
  @override
  String get receiptId => 'event-alternative:${binding.runId}:$contractId';
  @override
  bool qualifies(GameState main, DailyContract contract) =>
      main.daily.accountSeed == binding.accountId &&
      current.seasonId == binding.seasonId &&
      current.runId == binding.runId &&
      current.rulesDigest == binding.rulesDigest &&
      _contractFingerprint(contract) == binding.contractFingerprint &&
      current.fleet.lifetimeMicros - binding.baselineMicros >=
          binding.targetMicros;
}

/// DailyState is the ONLY XP authority. Selection changes its one pass key;
/// every objective award delegates to the existing core claimContract receipt.
class PassEngine {
  final Map<String, SeasonDefinition> definitions;
  static const _core = TideglassEngine();
  PassEngine(Iterable<SeasonDefinition> catalogue)
      : definitions =
            Map.unmodifiable({for (final d in catalogue) d.passId: d}) {
    if (definitions.isEmpty || definitions.length != catalogue.length)
      throw ArgumentError('Pass catalogue must have unique identities.');
  }
  void validate(PassState state, {GameState? main}) {
    if (state.alternatives.length > 21) {
      throw const FormatException(
          'Event bindings exceed retained daily slot capacity.');
    }
    if (state.definitionDigests.length != definitions.length ||
        definitions.entries
            .any((d) => state.definitionDigests[d.key] != d.value.digest))
      throw const FormatException('Pinned pass catalogue differs.');
    for (final entry in state.claims.entries) {
      final receipt = entry.value, definition = definitions[entry.value.passId];
      if (definition == null)
        throw const FormatException('Unknown reward pass.');
      final reward = definition.reward(receipt.rewardId);
      if (entry.key != receipt.rewardId ||
          receipt.accountId.isEmpty ||
          receipt.receiptId !=
              'pass:${receipt.accountId}:${receipt.rewardId}' ||
          (reward.track == 'premium' &&
              (receipt.entitlementVerificationReceiptId?.isNotEmpty != true)) ||
          (reward.track == 'free' &&
              receipt.entitlementVerificationReceiptId != null) ||
          (main != null &&
              (main.daily.accountSeed != receipt.accountId ||
                  (main.daily.passXpById[receipt.passId] ?? BigInt.zero) <
                      BigInt.from(reward.level * 500))))
        throw const FormatException(
            'Invalid reward receipt or insufficient shared XP.');
    }
    for (final entry in state.alternatives.entries) {
      final binding = entry.value;
      if (entry.key != binding.contractId ||
          !definitions.values.any((d) =>
              d.id == binding.seasonId && d.digest == binding.rulesDigest) ||
          (main != null && binding.accountId != main.daily.accountSeed))
        throw const FormatException('Invalid season objective binding.');
    }
  }

  int level(GameState main, String passId) {
    if (!definitions.containsKey(passId))
      throw const FormatException('Unknown pass.');
    final result =
        (main.daily.passXpById[passId] ?? BigInt.zero) ~/ BigInt.from(500);
    return result > BigInt.from(30) ? 30 : result.toInt();
  }

  PassTransition selectPass(
      GameState main, PassState pass, SeasonState season) {
    validate(pass, main: main);
    final matches = definitions.values.where((d) => d.id == season.seasonId);
    if (matches.isEmpty)
      return PassTransition(main, pass,
          accepted: false, reason: 'unknown_pass');
    final definition = matches.single;
    SeasonEngine(definition).validate(season);
    if (season.phase == SeasonPhase.upcoming)
      return PassTransition(main, pass,
          accepted: false, reason: 'pass_not_started');
    if (main.daily.selectedPassId == definition.passId)
      return PassTransition(main, pass,
          accepted: false, reason: 'pass_already_selected');
    final xp = Map<String, BigInt>.from(main.daily.passXpById);
    xp.putIfAbsent(definition.passId, () => BigInt.zero);
    return PassTransition(
        main.copyWith(
            daily: main.daily
                .copyWith(selectedPassId: definition.passId, passXpById: xp),
            revision: main.revision + 1),
        pass);
  }

  PassTransition claimDaily(GameState main, PassState pass, String contractId,
      {SeasonState? alternativeSeason}) {
    validate(pass, main: main);
    if (!definitions.containsKey(main.daily.selectedPassId))
      return PassTransition(main, pass,
          accepted: false, reason: 'selected_pass_unknown');
    DailyContractAlternative? alternative;
    if (alternativeSeason != null) {
      final binding = pass.alternatives[contractId];
      if (binding == null)
        return PassTransition(main, pass,
            accepted: false, reason: 'event_objective_not_assigned');
      final definition =
          definitions.values.where((d) => d.id == alternativeSeason.seasonId);
      if (definition.isEmpty)
        return PassTransition(main, pass,
            accepted: false, reason: 'unknown_event_run');
      SeasonEngine(definition.single).validate(alternativeSeason);
      alternative = _SeasonAlternative(binding, alternativeSeason);
    }
    final claimed =
        _core.claimContract(main, contractId, alternative: alternative);
    final retained = _retainedBindings(claimed.state, pass);
    return PassTransition(claimed.state, pass._copy(alternatives: retained),
        accepted: claimed.accepted,
        reason: claimed.reason,
        events: claimed.events);
  }

  Map<String, SeasonContractBinding> _retainedBindings(
          GameState main, PassState pass) =>
      {
        for (final entry in pass.alternatives.entries)
          if (main.dailyContracts.any((contract) =>
              contract.id == entry.key &&
              !contract.claimed &&
              _contractFingerprint(contract) ==
                  entry.value.contractFingerprint))
            entry.key: entry.value
      };

  /// Call after a native reroll, claim or daily refresh. Removing an obsolete
  /// binding grants nothing; a replacement always starts from current event production.
  PassTransition pruneAlternatives(GameState main, PassState pass) {
    validate(pass, main: main);
    final retained = _retainedBindings(main, pass);
    return PassTransition(main, pass._copy(alternatives: retained),
        accepted: retained.length != pass.alternatives.length,
        reason:
            retained.length == pass.alternatives.length ? 'unchanged' : null);
  }

  PassTransition bindEventAlternative(
      GameState main, PassState pass, String contractId, SeasonState season) {
    validate(pass, main: main);
    final contracts =
        main.dailyContracts.where((c) => c.id == contractId && !c.claimed);
    final definitionsForRun =
        definitions.values.where((d) => d.id == season.seasonId);
    if (contracts.isEmpty || definitionsForRun.isEmpty || !season.canPlay)
      return PassTransition(main, pass,
          accepted: false, reason: 'event_alternative_unavailable');
    final definition = definitionsForRun.single;
    final engine = SeasonEngine(definition);
    engine.validate(season);
    final retained = _retainedBindings(main, pass);
    if (retained.containsKey(contractId))
      return PassTransition(main, pass,
          accepted: false, reason: 'event_alternative_already_assigned');
    final rate = engine.outputPerSecond(season).raw;
    final binding = SeasonContractBinding._(
        contractId,
        _contractFingerprint(contracts.single),
        main.daily.accountSeed!,
        season.seasonId,
        season.runId,
        season.rulesDigest,
        season.fleet.lifetimeMicros,
        ceilDivide(rate * BigInt.from(600), Fixed.scale) * BigInt.from(1000000),
        rate);
    return PassTransition(
        main, pass._copy(alternatives: {...retained, contractId: binding}));
  }

  PassTransition claimFreeReward(
      GameState main, PassState pass, String passId, String rewardId) {
    validate(pass, main: main);
    return _claimReward(main, pass, passId, rewardId, null, premium: false);
  }

  /// Serialize the awaited transition with other commands and atomically save
  /// main+pass. Store verification is explicitly injected, not implemented here.
  Future<PassTransition> claimPremiumReward(
      GameState main, PassState pass, String passId, String rewardId,
      {required VerifiedPassEntitlementReader entitlementReader}) async {
    validate(pass, main: main);
    final accountId = main.daily.accountSeed;
    if (accountId == null)
      return PassTransition(main, pass,
          accepted: false, reason: 'account_identity_required');
    final entitlement =
        await entitlementReader.read(accountId: accountId, passId: passId);
    if (entitlement == null ||
        entitlement.accountId != accountId ||
        entitlement.passId != passId)
      return PassTransition(main, pass,
          accepted: false, reason: 'verified_pass_entitlement_required');
    return _claimReward(main, pass, passId, rewardId, entitlement,
        premium: true);
  }

  PassTransition _claimReward(GameState main, PassState pass, String passId,
      String rewardId, VerifiedPassEntitlement? entitlement,
      {required bool premium}) {
    final definition = definitions[passId];
    if (definition == null || main.daily.accountSeed == null)
      return PassTransition(main, pass,
          accepted: false, reason: 'unknown_pass_or_account');
    final matches = definition.rewards.where(
        (r) => r.id == rewardId && r.track == (premium ? 'premium' : 'free'));
    if (matches.isEmpty || pass.claims.containsKey(rewardId))
      return PassTransition(main, pass,
          accepted: false, reason: 'reward_unavailable_or_claimed');
    final reward = matches.single;
    if (level(main, passId) < reward.level)
      return PassTransition(main, pass,
          accepted: false, reason: 'insufficient_pass_xp');
    final receipt = PassReceipt._(
        main.daily.accountSeed!,
        passId,
        rewardId,
        'pass:${main.daily.accountSeed}:$rewardId',
        entitlement?.verificationReceiptId);
    return PassTransition(
        main, pass._copy(claims: {...pass.claims, rewardId: receipt}),
        rewardReceipt: receipt);
  }

  /// Safe local projection: gameplay saves can confer earned FREE cosmetics
  /// only. A cached premium claim/verification-receipt string is not ownership.
  Set<String> cosmeticIds(PassState pass) {
    validate(pass);
    return {
      for (final receipt in pass.claims.values)
        if (definitions[receipt.passId]!.reward(receipt.rewardId).kind ==
                'cosmetic' &&
            definitions[receipt.passId]!.reward(receipt.rewardId).track ==
                'free')
          definitions[receipt.passId]!.reward(receipt.rewardId).contentId
    };
  }

  /// Reconciles paid appearances against independent verified ownership and
  /// the authoritative shared XP ledger, never local premium claim flags.
  /// Missing local claim receipts therefore do not prevent purchase restore;
  /// forged ones cannot confer a cosmetic when verification fails or is absent.
  Future<Set<String>> verifiedCosmeticIds(GameState main, PassState pass,
      {required VerifiedPassEntitlementReader entitlementReader}) async {
    validate(pass, main: main);
    final result = cosmeticIds(pass);
    final accountId = main.daily.accountSeed;
    if (accountId == null) return result;
    for (final definition in definitions.values) {
      final currentLevel = level(main, definition.passId);
      final eligible = definition.rewards.where((reward) =>
          reward.track == 'premium' && reward.level <= currentLevel);
      if (eligible.isEmpty) continue;
      final entitlement = await entitlementReader.read(
          accountId: accountId, passId: definition.passId);
      if (entitlement?.accountId != accountId ||
          entitlement?.passId != definition.passId) continue;
      result.addAll(eligible.map((reward) => reward.contentId));
    }
    return result;
  }

  Set<String> fragmentIds(PassState pass) {
    validate(pass);
    return _contentIds(pass, 'archive_fragment');
  }

  Set<String> _contentIds(PassState pass, String kind) => {
        for (final receipt in pass.claims.values)
          if (definitions[receipt.passId]!.reward(receipt.rewardId).kind ==
              kind)
            definitions[receipt.passId]!.reward(receipt.rewardId).contentId
      };
}
