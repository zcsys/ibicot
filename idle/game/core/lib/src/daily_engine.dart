part of 'engine.dart';

extension TideglassDaily on TideglassEngine {
  static final _dayMicros =
      BigInt.from(86400) * TideglassEngine.microsPerSecond;

  BigInt contractProgress(GameState state, DailyContract contract) {
    final raw = switch (contract.kind) {
      'restore' => state.lifetimeMicros - contract.lifetimeBaselineMicros,
      'build' => state.lifetimePurchasedCount - contract.purchasedBaseline,
      'discover' =>
        (state.daily.discoveryTotals[contract.discoveryKind] ?? BigInt.zero) -
            contract.discoveryBaseline,
      _ => throw StateError('Unknown contract kind'),
    };
    return raw < BigInt.zero
        ? BigInt.zero
        : raw > contract.target
            ? contract.target
            : raw;
  }

  BigInt _cheapestPrice(GameState state) {
    var cheapest = priceMicros(0, state.counts[0]);
    for (var tier = 1; tier < 5; tier++) {
      if (!isUnlocked(state, tier)) continue;
      final price = priceMicros(tier, state.counts[tier]);
      if (price < cheapest) cheapest = price;
    }
    return cheapest;
  }

  DailyContract _makeContract(
      GameState state, DailyState daily, int day, int slot,
      {DailyContract? reroll}) {
    final kinds = [
      'restore',
      'build',
      if (daily.availableDiscoveryKinds.isNotEmpty) 'discover'
    ];
    if (reroll != null) kinds.remove(reroll.kind);
    final seed = stableContractSeed(
        '${daily.accountSeed}:$day:$slot:${reroll == null ? 0 : 1}');
    final kind = kinds[seed % kinds.length];
    final discovery = kind == 'discover'
        ? daily.availableDiscoveryKinds[
            (seed ~/ kinds.length) % daily.availableDiscoveryKinds.length]
        : null;
    final rate = reroll?.rateSnapshotRaw ?? outputPerSecond(state).raw;
    final cheapest =
        reroll?.cheapestPriceSnapshotMicros ?? _cheapestPrice(state);
    BigInt target;
    if (kind == 'restore') {
      target = ceilDivide(rate * BigInt.from(600), Fixed.scale) *
          TideglassEngine.microsPerSecond;
    } else if (kind == 'build') {
      final amount = rate *
          BigInt.from(300) *
          TideglassEngine.microsPerSecond ~/
          (cheapest * Fixed.scale);
      target = amount < BigInt.one
          ? BigInt.one
          : amount > BigInt.from(5)
              ? BigInt.from(5)
              : amount;
    } else {
      target = BigInt.one;
    }
    return DailyContract(
        id: 'contract:${daily.accountSeed}:$day:$slot',
        accountDay: day,
        slot: slot,
        kind: kind,
        discoveryKind: discovery,
        target: target,
        rateSnapshotRaw: rate,
        cheapestPriceSnapshotMicros: cheapest,
        lifetimeBaselineMicros: state.lifetimeMicros,
        purchasedBaseline: state.lifetimePurchasedCount,
        discoveryBaseline: daily.discoveryTotals[discovery] ?? BigInt.zero,
        rerolled: reroll != null);
  }

  /// Call after settling a return. New missed-day slots use this current frozen
  /// snapshot and cannot receive progress from before assignment.
  TransitionResult refreshContracts(
    GameState state,
    DateTime nowUtc, {
    String? accountSeed,
    int? utcOffsetMinutes,
    List<String> availableDiscoveryKinds = const [],
  }) {
    _requireRules(state);
    final previous = state.daily;
    if (previous.initialized &&
        ((accountSeed != null && accountSeed != previous.accountSeed) ||
            (utcOffsetMinutes != null &&
                utcOffsetMinutes != previous.utcOffsetMinutes))) {
      return _reject(state, 'account_seed_and_day_offset_are_fixed');
    }
    if (!previous.initialized && accountSeed == null)
      return _reject(state, 'account_seed_required');
    final offset = utcOffsetMinutes ?? previous.utcOffsetMinutes;
    final requestedUtc = BigInt.from(nowUtc.toUtc().microsecondsSinceEpoch);
    final establishedUtc = previous.initialized
        ? previous.utcAnchorMicros! + state.elapsedMicros
        : requestedUtc;
    final utcMicros =
        requestedUtc > establishedUtc ? requestedUtc : establishedUtc;
    final calculated = ((utcMicros +
                BigInt.from(offset * 60) * TideglassEngine.microsPerSecond) ~/
            _dayMicros)
        .toInt();
    final day =
        calculated > previous.dayHighWater ? calculated : previous.dayHighWater;
    final retained =
        previous.contracts.where((c) => c.accountDay >= day - 6).toList();
    var daily = previous.copyWith(
        accountSeed: accountSeed,
        utcOffsetMinutes: offset,
        utcAnchorMicros: utcMicros - state.elapsedMicros,
        dayHighWater: day,
        contracts: retained,
        availableDiscoveryKinds: availableDiscoveryKinds);
    final first = previous.initialized
        ? (previous.lastMaterializedDay + 1 > day - 6
            ? previous.lastMaterializedDay + 1
            : day - 6)
        : day;
    for (var date = first; date <= day; date++) {
      for (var slot = 0; slot < 3; slot++) {
        retained.add(_makeContract(state, daily, date, slot));
      }
    }
    daily = daily.copyWith(lastMaterializedDay: day, contracts: retained);
    final after = _syncSupportDay(
        state.copyWith(daily: daily, revision: state.revision + 1));
    return TransitionResult(after, events: [
      _event(after, 'contracts_refreshed', details: {
        'account_day': day,
        'materialized': retained.length -
            previous.contracts.where((c) => c.accountDay >= day - 6).length,
      })
    ]);
  }

  GameState _advanceCalendar(GameState state, {required bool offline}) {
    if (!state.daily.initialized) return state;
    final daily = state.daily;
    final utc = daily.utcAnchorMicros! + state.elapsedMicros;
    final day = ((utc +
                BigInt.from(daily.utcOffsetMinutes * 60) *
                    TideglassEngine.microsPerSecond) ~/
            _dayMicros)
        .toInt();
    if (day <= daily.dayHighWater) return state;
    final advanced = daily.copyWith(
        dayHighWater: day,
        contracts: daily.contracts
            .where((contract) => contract.accountDay >= day - 6)
            .toList());
    final result = state.copyWith(daily: advanced);
    if (offline) return result;
    return refreshContracts(result,
            DateTime.fromMicrosecondsSinceEpoch(utc.toInt(), isUtc: true),
            availableDiscoveryKinds: daily.availableDiscoveryKinds)
        .state;
  }

  BigInt? _untilDayBoundary(GameState state) {
    if (!state.daily.initialized) return null;
    final daily = state.daily;
    return BigInt.from(daily.dayHighWater + 1) * _dayMicros -
        BigInt.from(daily.utcOffsetMinutes * 60) *
            TideglassEngine.microsPerSecond -
        (daily.utcAnchorMicros! + state.elapsedMicros);
  }

  TransitionResult rerollContract(GameState state, String contractId) {
    _requireRules(state);
    final matches = state.daily.contracts.where((c) => c.id == contractId);
    if (matches.isEmpty) return _reject(state, 'contract_not_retained');
    final contract = matches.single;
    if (contract.claimed || contract.rerolled)
      return _reject(state, 'contract_reroll_unavailable');
    final replacement = _makeContract(
        state, state.daily, contract.accountDay, contract.slot,
        reroll: contract);
    final after = state.copyWith(
        daily: state.daily.copyWith(
            contracts: state.daily.contracts
                .map((c) => c.id == contractId ? replacement : c)
                .toList()),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'contract_rerolled', details: {'contract_id': contractId})
    ]);
  }

  TransitionResult claimContract(GameState state, String contractId,
      {DailyContractAlternative? alternative}) {
    _requireRules(state);
    final matches = state.daily.contracts.where((c) => c.id == contractId);
    if (matches.isEmpty) return _reject(state, 'contract_not_retained');
    final contract = matches.single;
    if (contract.claimed) return _reject(state, 'contract_already_claimed');
    if (alternative != null) {
      if (alternative.contractId != contractId ||
          alternative.receiptId.isEmpty ||
          !alternative.qualifies(state, contract))
        return _reject(state, 'contract_alternative_incomplete_or_mismatched');
    } else if (contractProgress(state, contract) < contract.target) {
      return _reject(state, 'contract_incomplete');
    }
    final passId = state.daily.selectedPassId;
    final xp = Map<String, BigInt>.from(state.daily.passXpById);
    xp[passId] = (xp[passId] ?? BigInt.zero) + BigInt.from(250);
    final daily = state.daily.copyWith(
        passXpById: xp,
        contracts: state.daily.contracts
            .map((c) => c.id == contractId ? c.withClaim(passId) : c)
            .toList());
    final after = state.copyWith(
        daily: daily,
        surveyNotes: state.surveyNotes + BigInt.from(10),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'contract_claimed', details: {
        'contract_id': contractId,
        'receipt_id': 'claim:$contractId',
        if (alternative != null)
          'alternative_receipt_id': alternative.receiptId,
        'notes': '10',
        'pass_id': passId,
        'xp': '250',
      })
    ]);
  }

  /// Content IDs identify collectibles; operation IDs identify completions.
  /// Repeated operation delivery cannot count the same discovery twice.
  TransitionResult recordDiscovery(GameState state, String kind,
      {BigInt? operationSequence, String? operationId, String? contentId}) {
    _requireRules(state);
    if (!{'calibration', 'archive', 'challenge'}.contains(kind))
      return _reject(state, 'invalid_discovery');
    if (operationId != null)
      return _reject(
          state,
          state.daily.discoveryOperationIds.contains(operationId)
              ? 'discovery_already_recorded'
              : 'legacy_discovery_identity_not_accepted');
    final sequence = operationSequence;
    if (sequence == null || sequence != state.nextDiscoverySequence)
      return _reject(state, 'discovery_sequence_not_next');
    final identity =
        'discovery:${state.daily.accountSeed ?? 'local'}:$sequence';
    if (state.daily.discoveryOperationIds.contains(identity))
      return _reject(state, 'legacy_discovery_identity_reused');
    final totals = Map<String, BigInt>.from(state.daily.discoveryTotals);
    totals[kind] = (totals[kind] ?? BigInt.zero) + BigInt.one;
    final after = state.copyWith(
        daily: state.daily
            .copyWith(discoveryTotals: totals, discoverySequence: sequence),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'discovery_recorded', details: {
        'kind': kind,
        'operation_id': identity,
        'operation_sequence': sequence.toString(),
        if (contentId != null) 'content_id': contentId,
      })
    ]);
  }

  TransitionResult completeCalibration(GameState state, String patternId,
      {BigInt? operationSequence, String? operationId}) {
    _requireRules(state);
    if (!RegExp(r'^calibration\.(0[1-9]|1[0-2])$').hasMatch(patternId))
      return _reject(state, 'unknown_calibration');
    final sequence = operationSequence ?? state.nextDiscoverySequence;
    final discovered = recordDiscovery(state, 'calibration',
        operationSequence: sequence,
        operationId: operationId,
        contentId: patternId);
    if (!discovered.accepted) return discovered;
    final focused = activateFocus(discovered.state);
    // Failed activation must not consume a discovery sequence or completion.
    if (!focused.accepted)
      return _reject(state, focused.reason ?? 'insufficient_focus');
    final after = focused.state.copyWith(
        completedCalibrationIds: {...state.completedCalibrationIds, patternId});
    return TransitionResult(after,
        events: [...discovered.events, ...focused.events]);
  }

  TransitionResult buyPlanSlot(GameState state) {
    _requireRules(state);
    if (state.charts < BigInt.from(10))
      return _reject(state, 'automation_requires_10_charts');
    if (state.extraPlanSlots >= 5)
      return _reject(state, 'all_plan_slots_owned');
    if (state.surveyNotes < BigInt.from(50))
      return _reject(state, 'insufficient_notes');
    final after = state.copyWith(
        extraPlanSlots: state.extraPlanSlots + 1,
        surveyNotes: state.surveyNotes - BigInt.from(50),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'plan_slot_purchased', details: {'notes': '50'})
    ]);
  }

  TransitionResult saveAutomationPlan(GameState state, AutomationPlan plan) {
    _requireRules(state);
    if (state.charts < BigInt.from(10))
      return _reject(state, 'automation_requires_10_charts');
    if (plan.autoResetEnabled && state.charts < BigInt.from(100))
      return _reject(state, 'automatic_rechart_requires_100_charts');
    final plans = state.automationPlans.toList();
    final index = plans.indexWhere((existing) => existing.id == plan.id);
    if (index >= 0) {
      plans[index] = plan;
    } else {
      if (plans.length >= 1 + state.extraPlanSlots)
        return _reject(state, 'no_free_plan_slot');
      plans.add(plan);
    }
    final after =
        state.copyWith(automationPlans: plans, revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'automation_plan_saved', details: {'plan_id': plan.id})
    ]);
  }

  TransitionResult selectAutomationPlan(GameState state, String planId) {
    _requireRules(state);
    if (!state.automationPlans.any((plan) => plan.id == planId))
      return _reject(state, 'unknown_plan');
    if (state.selectedAutomationPlanId == planId)
      return _reject(state, 'unchanged');
    final after = state.copyWith(
        selectedAutomationPlanId: planId, revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'automation_plan_selected', details: {'plan_id': planId})
    ]);
  }

  int _plannedPurchaseTier(GameState state) {
    final plan = state.selectedAutomationPlan;
    if (plan.purchasePolicy == 'greedy') return chooseAutoBuyTier(state);
    return plan.tierPriority.firstWhere((tier) => isUnlocked(state, tier));
  }

  bool _automaticRechartEligible(GameState state) {
    final plan = state.selectedAutomationPlan;
    return plan.autoResetEnabled &&
        state.charts >= BigInt.from(100) &&
        state.elapsedMicros - state.lastRechartElapsedMicros >=
            BigInt.from(plan.minimumRunSeconds) *
                TideglassEngine.microsPerSecond &&
        prestigeAward(state) >= plan.minimumAdditionalCharts;
  }
}
