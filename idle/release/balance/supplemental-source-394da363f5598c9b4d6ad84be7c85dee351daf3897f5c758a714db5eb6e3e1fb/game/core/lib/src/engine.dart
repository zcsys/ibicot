import 'fixed.dart';
import 'state.dart';
import 'daily.dart';
import 'support.dart';

part 'daily_engine.dart';
part 'support_engine.dart';

/// Trusted in-process gameplay bridge. Implementations must validate their own
/// pinned scenario/run and frozen objective against authoritative saved state.
/// This is not a store receipt or an externally verified claim capability.
abstract interface class DailyContractAlternative {
  String get contractId;
  String get receiptId;
  bool qualifies(GameState main, DailyContract contract);
}

/// Versioned baseline economy. Pure methods return immutable states; no file,
/// network, wall-clock or store operations occur in this package.
class TideglassEngine {
  const TideglassEngine();

  static const producerNames = [
    'Spark Skiff',
    'Prism Nursery',
    'Tide Dynamo',
    'Aurora Loom',
    'Dawn Observatory',
  ];
  static final microsPerSecond = BigInt.from(1000000);
  static final firstPrestigeMicros = BigInt.from(10).pow(15);
  static final focusCycleMicros = BigInt.from(7200) * microsPerSecond;
  static final surveyCycleMicros = BigInt.from(28800) * microsPerSecond;
  static final fullOfflineMicros = BigInt.from(86400) * microsPerSecond;
  static final totalOfflineMicros = BigInt.from(259200) * microsPerSecond;
  static final _earningDenominator = Fixed.scale * BigInt.from(400);
  static final _prestigeDenominator = firstPrestigeMicros.pow(13);
  // These memoize immutable arithmetic only. Bounds apply per isolate; no
  // gameplay state, ownership, clock, or persistence depends on cache contents.
  static final _prices = _NumericMemo<(int, int), BigInt>(2048);
  static final _countLogs = _NumericMemo<int, Fixed>(1024);
  static final _chartPower = _NumericMemo<BigInt, Fixed>(128);
  static final _rates =
      _NumericMemo<(int, int, int, int, int, BigInt), Fixed>(512);

  void _tier(int tierIndex) {
    if (tierIndex < 0 || tierIndex >= 5)
      throw RangeError.range(tierIndex, 0, 4, 'tierIndex');
  }

  /// Canonical rounded cumulative curve. Differences telescope exactly, so
  /// dividing one batch into many purchases never changes the settled price.
  BigInt _cumulativePriceMicros(int tierIndex, int count) {
    _tier(tierIndex);
    if (count < 0) throw RangeError.value(count, 'count');
    if (count == 0) return BigInt.zero;
    if (count <= 8192) {
      return _prices.read((tierIndex, count),
          () => _uncachedCumulativePriceMicros(tierIndex, count));
    }
    return _uncachedCumulativePriceMicros(tierIndex, count);
  }

  BigInt _uncachedCumulativePriceMicros(int tierIndex, int count) {
    final numeratorPower = BigInt.from(28).pow(count);
    final denominatorPower = BigInt.from(25).pow(count);
    final base =
        BigInt.from(30) * BigInt.from(20).pow(tierIndex) * microsPerSecond;
    return ceilDivide(
        base * BigInt.from(25) * (numeratorPower - denominatorPower),
        BigInt.from(3) * denominatorPower);
  }

  BigInt priceMicros(int tierIndex, int owned) =>
      bulkPriceMicros(tierIndex, owned, 1);

  BigInt bulkPriceMicros(int tierIndex, int owned, int quantity) {
    _tier(tierIndex);
    if (owned < 0 || quantity < 0)
      throw ArgumentError('Ownership and quantity must be nonnegative');
    if (quantity == 0) return BigInt.zero;
    return _cumulativePriceMicros(tierIndex, owned + quantity) -
        _cumulativePriceMicros(tierIndex, owned);
  }

  int milestoneMultiplier(int owned) {
    if (owned < 0) throw ArgumentError('Ownership must be nonnegative');
    final milestone = owned ~/ 25;
    return 1 << (milestone > 4 ? 4 : milestone);
  }

  bool isUnlocked(GameState state, int tierIndex) {
    _tier(tierIndex);
    return tierIndex == 0 || state.counts[tierIndex - 1] >= 10;
  }

  Fixed prestigeMultiplier(BigInt charts) {
    if (charts.isNegative) throw ArgumentError('Charts must be nonnegative');
    if (charts.bitLength <= 4096) {
      return _chartPower.read(
          charts, () => _uncachedPrestigeMultiplier(charts));
    }
    return _uncachedPrestigeMultiplier(charts);
  }

  Fixed _uncachedPrestigeMultiplier(BigInt charts) {
    return Fixed.raw(Fixed.scale +
        integerRoot(charts * Fixed.scale.pow(2) ~/ BigInt.from(10), 2));
  }

  Fixed synergyMultiplier(GameState state, int tierIndex) {
    _tier(tierIndex);
    if (state.charts < BigInt.from(25) || tierIndex < 3) return Fixed.one;
    final x1 = _synergyCountLog(state.counts[0]);
    final x2 = _synergyCountLog(state.counts[1]);
    final a = tierIndex == 3 ? 20 : 10;
    final b = tierIndex == 3 ? 10 : 25;
    return Fixed.raw(Fixed.scale +
        (x1.raw * BigInt.from(a) + x2.raw * BigInt.from(b)) ~/
            BigInt.from(100));
  }

  Fixed _synergyCountLog(int count) => _countLogs.read(
      count, () => log2Ratio(BigInt.from(25 + count), BigInt.from(25)));

  /// Unboosted producer rate. Focus is applied by the timeline, not hidden in
  /// this value; forecasts explicitly state whether bonuses are ignored.
  Fixed producerOutputPerSecond(GameState state, int tierIndex) {
    _tier(tierIndex);
    final direct = BigInt.from(state.counts[tierIndex]) *
        BigInt.from(20).pow(tierIndex) *
        BigInt.from(milestoneMultiplier(state.counts[tierIndex]));
    return Fixed.raw(direct * synergyMultiplier(state, tierIndex).raw) *
        prestigeMultiplier(state.charts);
  }

  Fixed outputPerSecond(GameState state) {
    // Scenario subclasses override producer rules and may read other state.
    // Only this exact baseline type has the complete key declared below.
    if (runtimeType == TideglassEngine && state.charts.bitLength <= 4096) {
      final n = state.counts;
      return _rates.read((n[0], n[1], n[2], n[3], n[4], state.charts),
          () => _uncachedOutputPerSecond(state));
    }
    return _uncachedOutputPerSecond(state);
  }

  Fixed _uncachedOutputPerSecond(GameState state) {
    var sum = BigInt.zero;
    for (var tier = 0; tier < 5; tier++) {
      sum += producerOutputPerSecond(state, tier).raw;
    }
    return Fixed.raw(sum);
  }

  Fixed activeOutputPerSecond(GameState state) =>
      Fixed.raw(outputPerSecond(state).raw *
          BigInt.from(100 +
              (state.focusRemainingMicros > BigInt.zero ? 20 : 0) +
              (state.support.remainingMicros > BigInt.zero ? 25 : 0)) ~/
          BigInt.from(100));

  Fixed marginalOutputPerSecond(GameState state, int tierIndex,
      {int quantity = 1}) {
    _tier(tierIndex);
    if (quantity < 0) throw ArgumentError('Quantity must be nonnegative');
    final afterCounts = state.counts.toList();
    afterCounts[tierIndex] += quantity;
    return outputPerSecond(state.copyWith(counts: afterCounts)) -
        outputPerSecond(state);
  }

  BigInt prestigeEntitlement(BigInt lifetimeMicros) {
    if (lifetimeMicros.isNegative)
      throw ArgumentError('Lifetime must be nonnegative');
    final ratio = BigInt.from(10).pow(20) *
        lifetimeMicros.pow(13) ~/
        _prestigeDenominator;
    return integerRoot(ratio, 20);
  }

  BigInt prestigeAward(GameState state) {
    if (state.lifetimeMicros < firstPrestigeMicros) return BigInt.zero;
    final difference = prestigeEntitlement(state.lifetimeMicros) - state.charts;
    return difference > BigInt.zero ? difference : BigInt.zero;
  }

  BigInt nextChartLifetimeMicros(GameState state) {
    return lifetimeForCharts(state.charts + BigInt.one);
  }

  BigInt lifetimeForCharts(BigInt target) {
    if (target <= BigInt.zero) return BigInt.zero;
    final rhs = target.pow(20) * _prestigeDenominator;
    final divisor = BigInt.from(10).pow(20);
    var root = integerRoot(rhs ~/ divisor, 13);
    if (root.pow(13) * divisor < rhs) root += BigInt.one;
    return root < firstPrestigeMicros ? firstPrestigeMicros : root;
  }

  int nextMilestoneQuantity(GameState state, int tierIndex) {
    _tier(tierIndex);
    return 25 - state.counts[tierIndex] % 25;
  }

  int maximumAffordable(GameState state, int tierIndex) {
    _tier(tierIndex);
    if (!isUnlocked(state, tierIndex) ||
        priceMicros(tierIndex, state.counts[tierIndex]) > state.walletMicros)
      return 0;
    var low = 1;
    var high = 2;
    while (bulkPriceMicros(tierIndex, state.counts[tierIndex], high) <=
        state.walletMicros) {
      low = high;
      high *= 2;
    }
    while (low + 1 < high) {
      final middle = (low + high) ~/ 2;
      if (bulkPriceMicros(tierIndex, state.counts[tierIndex], middle) <=
          state.walletMicros) {
        low = middle;
      } else {
        high = middle;
      }
    }
    return low;
  }

  /// Unboosted constant-rate forecast. Ignores future purchases/bonuses; null
  /// means locked or longer than the maximum Duration used by this API.
  Duration? waitForPurchase(GameState state, int tierIndex,
      {int quantity = 1}) {
    if (!isUnlocked(state, tierIndex)) return null;
    final cost = bulkPriceMicros(tierIndex, state.counts[tierIndex], quantity);
    if (cost <= state.walletMicros) return Duration.zero;
    final rawRate = outputPerSecond(state).raw;
    if (rawRate == BigInt.zero) return null;
    final wait = ceilDivide((cost - state.walletMicros) * Fixed.scale, rawRate);
    if (wait > BigInt.from(9007199254740991)) return null;
    return Duration(microseconds: wait.toInt());
  }

  TransitionResult _reject(GameState state, String reason) =>
      TransitionResult(state, accepted: false, reason: reason);
  CoreEvent _event(GameState after, String kind,
          {int index = 0, Map<String, dynamic> details = const {}}) =>
      CoreEvent(
          id: '$economyVersion:${after.revision}:$index:$kind',
          kind: kind,
          elapsedMicros: after.elapsedMicros,
          details: details);

  TransitionResult buy(GameState state, int tierIndex, int quantity) {
    _tier(tierIndex);
    if (quantity <= 0) return _reject(state, 'quantity_must_be_positive');
    if (!isUnlocked(state, tierIndex)) return _reject(state, 'producer_locked');
    final cost = bulkPriceMicros(tierIndex, state.counts[tierIndex], quantity);
    if (cost > state.walletMicros)
      return _reject(state, 'insufficient_radiance');
    final counts = state.counts.toList();
    counts[tierIndex] += quantity;
    final after = state.copyWith(
        counts: counts,
        walletMicros: state.walletMicros - cost,
        revision: state.revision + 1,
        lifetimePurchasedCount:
            state.lifetimePurchasedCount + BigInt.from(quantity));
    return TransitionResult(after, events: [
      _event(after, 'purchase', details: {
        'tier_index': tierIndex,
        'quantity': quantity,
        'cost_micros': cost.toString(),
        'owned': counts[tierIndex],
        'milestone_before': milestoneMultiplier(state.counts[tierIndex]),
        'milestone_after': milestoneMultiplier(counts[tierIndex]),
      })
    ]);
  }

  TransitionResult buyMax(GameState state, int tierIndex) {
    final amount = maximumAffordable(state, tierIndex);
    return amount == 0
        ? _reject(state, 'no_affordable_unlocked_purchase')
        : buy(state, tierIndex, amount);
  }

  TransitionResult rechart(GameState state) {
    final award = prestigeAward(state);
    if (award == BigInt.zero) return _reject(state, 'no_new_eligible_charts');
    final after = state.copyWith(
        counts: [1, 0, 0, 0, 0],
        walletMicros: BigInt.zero,
        charts: state.charts + award,
        rechartCount: state.rechartCount + 1,
        lastRechartElapsedMicros: state.elapsedMicros,
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'rechart', details: {'awarded_charts': award.toString()})
    ]);
  }

  TransitionResult setAutoBuy(GameState state, bool enabled) {
    if (enabled && state.charts < BigInt.from(10))
      return _reject(state, 'autobuy_requires_10_charts');
    if (state.autoBuyEnabled == enabled)
      return TransitionResult(state, accepted: false, reason: 'unchanged');
    final after =
        state.copyWith(autoBuyEnabled: enabled, revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'autobuy_changed', details: {'enabled': enabled})
    ]);
  }

  TransitionResult activateFocus(GameState state, {int charges = 1}) {
    if (charges <= 0 || charges > state.focusCharges)
      return _reject(state, 'insufficient_focus');
    final after = state.copyWith(
        focusCharges: state.focusCharges - charges,
        focusRemainingMicros: state.focusRemainingMicros +
            BigInt.from(charges * 600) * microsPerSecond,
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'focus_queued', details: {'charges': charges})
    ]);
  }

  TransitionResult collectSurveys(GameState state) {
    if (state.completedSurveys == 0)
      return _reject(state, 'no_completed_surveys');
    final gained = BigInt.from(state.completedSurveys * 10);
    final after = state.copyWith(
        completedSurveys: 0,
        surveyNotes: state.surveyNotes + gained,
        surveysCollectedTotal:
            state.surveysCollectedTotal + BigInt.from(state.completedSurveys),
        revision: state.revision + 1);
    return TransitionResult(after, events: [
      _event(after, 'surveys_collected', details: {'notes': gained.toString()})
    ]);
  }

  /// Reference-compatible greedy single-unit policy, enabled only at 10 Charts.
  /// Equal efficiency selects the higher tier deterministically.
  int chooseAutoBuyTier(GameState state) {
    final before = outputPerSecond(state).raw;
    var chosen = 0;
    var chosenDelta = BigInt.from(-1);
    var chosenCost = BigInt.one;
    for (var tier = 0; tier < 5; tier++) {
      if (!isUnlocked(state, tier)) continue;
      final delta = marginalOutputPerSecond(state, tier).raw;
      final cost = priceMicros(tier, state.counts[tier]);
      if (delta * chosenCost >= chosenDelta * cost) {
        chosen = tier;
        chosenDelta = delta;
        chosenCost = cost;
      }
    }
    assert(before > BigInt.zero);
    return chosen;
  }

  /// Advance the saved policy through integer-microsecond affordability and
  /// timer boundaries. Offline chunking MUST carry offlineElapsedBefore from
  /// the same absence; resetting it for every chunk would renew the full rate.
  /// No offline claim/settlement timestamp is persisted here; storage commits
  /// this returned state and its settlement cursor atomically.
  TransitionResult advance(
    GameState initial,
    Duration duration, {
    bool offline = false,
    bool? autoBuy,
    Duration offlineElapsedBefore = Duration.zero,
    int maximumEvents = 100000,
    OfflineSettlementRequest? offlineSettlement,
    String? offlineSettlementId,
    bool finalizeOfflineSettlement = true,
  }) {
    if (offlineSettlementId != null)
      return _reject(
          initial,
          initial.support.closedSettlementIds.contains(offlineSettlementId)
              ? 'offline_settlement_already_finalized'
              : 'legacy_offline_identity_not_accepted');
    return _advance(initial, duration,
        offline: offline,
        autoBuy: autoBuy,
        offlineElapsedBefore: offlineElapsedBefore,
        maximumEvents: maximumEvents,
        offlineSettlement: offlineSettlement,
        finalizeOfflineSettlement: finalizeOfflineSettlement);
  }

  /// Only finishes an already persisted schema3 accumulator. New opaque-ID
  /// settlements are never accepted. Save returned state and throughUtc together.
  TransitionResult finishLegacyOfflineSettlement(
    GameState initial,
    Duration remainingDuration, {
    required String frozenSettlementId,
    required Duration offlineElapsedBefore,
    required DateTime throughUtc,
    int maximumEvents = 100000,
  }) =>
      _advance(initial, remainingDuration,
          offline: true,
          offlineElapsedBefore: offlineElapsedBefore,
          maximumEvents: maximumEvents,
          legacySettlementId: frozenSettlementId,
          legacyThroughUtc:
              BigInt.from(throughUtc.toUtc().microsecondsSinceEpoch));

  TransitionResult _advance(
    GameState initial,
    Duration duration, {
    bool offline = false,
    bool? autoBuy,
    Duration offlineElapsedBefore = Duration.zero,
    int maximumEvents = 100000,
    OfflineSettlementRequest? offlineSettlement,
    String? legacySettlementId,
    BigInt? legacyThroughUtc,
    bool finalizeOfflineSettlement = true,
  }) {
    if (duration.isNegative || offlineElapsedBefore.isNegative)
      return _reject(initial, 'negative_elapsed_time');
    if (maximumEvents <= 0)
      throw ArgumentError('maximumEvents must be positive');
    final enabled = autoBuy ?? initial.autoBuyEnabled;
    if (enabled && initial.charts < BigInt.from(10))
      return _reject(initial, 'autobuy_requires_10_charts');
    final offlineSettlementId =
        offlineSettlement?.identity(initial.daily.accountSeed) ??
            legacySettlementId;
    if (offlineSettlementId != null && !offline)
      return _reject(initial, 'offline_settlement_requires_offline_advance');
    var state = initial;
    final support = state.support;
    final before = BigInt.from(offlineElapsedBefore.inMicroseconds);
    if (offlineSettlement != null) {
      if (support.receiptCursorMigrationRequired)
        return _reject(initial, 'legacy_receipt_cursor_migration_required');
      if (support.closedSettlementIds.contains(offlineSettlementId))
        return _reject(initial, 'legacy_offline_identity_reused');
      if (support.hasLegacyPendingSettlement)
        return _reject(
            initial, 'legacy_offline_settlement_requires_completion');
      if (support.activeSettlementRequest == null &&
          initial.daily.initialized &&
          offlineSettlement.fromUtcMicros <
              initial.daily.utcAnchorMicros! + initial.elapsedMicros)
        return _reject(initial, 'offline_interval_precedes_production_cursor');
      if (offlineSettlement.sequence != support.nextSettlementSequence)
        return _reject(initial, 'offline_sequence_not_next');
      if (support.lastSettlementThroughUtcMicros != null &&
          offlineSettlement.fromUtcMicros <
              support.lastSettlementThroughUtcMicros!)
        return _reject(initial, 'offline_interval_precedes_receipt_high_water');
      final afterOffset = before + BigInt.from(duration.inMicroseconds);
      if (afterOffset > offlineSettlement.durationMicros ||
          (finalizeOfflineSettlement &&
              afterOffset != offlineSettlement.durationMicros))
        return _reject(initial, 'offline_final_endpoint_mismatch');
      if (support.activeSettlementRequest != null) {
        if (!support.activeSettlementRequest!.sameAs(offlineSettlement) ||
            support.activeSettlementId != offlineSettlementId ||
            support.nextOffsetMicros != before ||
            support.sourceStartElapsedMicros + before != state.elapsedMicros)
          return _reject(initial, 'offline_settlement_continuation_mismatch');
      } else {
        if (before != BigInt.zero)
          return _reject(initial, 'offline_settlement_must_start_at_zero');
        state = state.copyWith(
            support: support.copyWith(
                activeSettlementId: offlineSettlementId,
                activeSettlementRequest: offlineSettlement,
                sourceStartElapsedMicros: state.elapsedMicros));
      }
    } else if (legacySettlementId != null) {
      if (!support.hasLegacyPendingSettlement ||
          support.activeSettlementId != legacySettlementId ||
          support.nextOffsetMicros != before ||
          support.sourceStartElapsedMicros + before != state.elapsedMicros)
        return _reject(initial, 'legacy_offline_continuation_mismatch');
      if (legacyThroughUtc == null ||
          legacyThroughUtc.isNegative ||
          (support.lastSettlementThroughUtcMicros != null &&
              legacyThroughUtc <
                  support.lastSettlementThroughUtcMicros! +
                      BigInt.from(duration.inMicroseconds)))
        return _reject(
            initial, 'legacy_offline_endpoint_precedes_saved_cursor');
    } else if (support.activeSettlementId != null) {
      return _reject(initial, 'offline_settlement_continuation_required');
    }
    final events = <CoreEvent>[];
    var remaining = BigInt.from(duration.inMicroseconds);
    var offset = BigInt.from(offlineElapsedBefore.inMicroseconds);
    var iterations = 0;
    while (remaining > BigInt.zero) {
      if (++iterations > maximumEvents) {
        throw StateError(
            'Timeline event budget exceeded; retry with smaller chunks and carried offline offset. Input state was not mutated.');
      }
      if (_automaticRechartEligible(state)) {
        final reset = rechart(state);
        state = reset.state;
        events.addAll(reset.events);
        continue;
      }
      int? autoTier;
      BigInt? autoCost;
      if (enabled) {
        autoTier = _plannedPurchaseTier(state);
        autoCost = priceMicros(autoTier, state.counts[autoTier]);
        if (state.walletMicros >= autoCost) {
          final purchase = buy(state, autoTier, 1);
          state = purchase.state;
          events.addAll(purchase.events);
          continue;
        }
      }
      final weight = !offline || offset < fullOfflineMicros
          ? 4
          : offset < totalOfflineMicros
              ? 1
              : 0;
      final bonusPercent = 100 +
          (state.focusRemainingMicros > BigInt.zero ? 20 : 0) +
          (state.support.remainingMicros > BigInt.zero ? 25 : 0);
      final unboostedRate = outputPerSecond(state).raw;
      final numeratorPerMicrosecond =
          unboostedRate * BigInt.from(weight * bonusPercent);
      var step = remaining;
      void limit(BigInt candidate) {
        if (candidate > BigInt.zero && candidate < step) step = candidate;
      }

      if (offline && offset < fullOfflineMicros)
        limit(fullOfflineMicros - offset);
      if (offline && offset < totalOfflineMicros)
        limit(totalOfflineMicros - offset);
      if (state.focusCharges < 12)
        limit(focusCycleMicros - state.focusPhaseMicros);
      if (state.completedSurveys < 3)
        limit(surveyCycleMicros - state.surveyPhaseMicros);
      if (state.focusRemainingMicros > BigInt.zero)
        limit(state.focusRemainingMicros);
      if (state.support.remainingMicros > BigInt.zero)
        limit(state.support.remainingMicros);
      if (offlineSettlementId != null && offset < totalOfflineMicros)
        limit(state.support.sliceStartOffsetMicros +
            TideglassSupport._sliceMicros -
            offset);
      final dayBoundary = _untilDayBoundary(state);
      if (dayBoundary != null) limit(dayBoundary);
      final resetPlan = state.selectedAutomationPlan;
      if (resetPlan.autoResetEnabled) {
        limit(state.lastRechartElapsedMicros +
            BigInt.from(resetPlan.minimumRunSeconds) * microsPerSecond -
            state.elapsedMicros);
        final resetTarget =
            lifetimeForCharts(state.charts + resetPlan.minimumAdditionalCharts);
        if (resetTarget > state.lifetimeMicros &&
            numeratorPerMicrosecond > BigInt.zero) {
          final needed =
              (resetTarget - state.lifetimeMicros) * _earningDenominator -
                  state.earningRemainder;
          limit(ceilDivide(needed > BigInt.zero ? needed : BigInt.zero,
              numeratorPerMicrosecond));
        }
      }
      if (autoCost != null && numeratorPerMicrosecond > BigInt.zero) {
        final numeratorNeeded =
            (autoCost - state.walletMicros) * _earningDenominator -
                state.earningRemainder;
        limit(ceilDivide(
            numeratorNeeded > BigInt.zero ? numeratorNeeded : BigInt.zero,
            numeratorPerMicrosecond));
      }
      final producedNumerator =
          state.earningRemainder + numeratorPerMicrosecond * step;
      final earned = producedNumerator ~/ _earningDenominator;
      var focusPhase = state.focusPhaseMicros;
      var focusCharges = state.focusCharges;
      var surveyPhase = state.surveyPhaseMicros;
      var surveys = state.completedSurveys;
      if (focusCharges < 12) {
        focusPhase += step;
        if (focusPhase >= focusCycleMicros) {
          focusCharges++;
          focusPhase -= focusCycleMicros;
        }
      }
      if (surveys < 3) {
        surveyPhase += step;
        if (surveyPhase >= surveyCycleMicros) {
          surveys++;
          surveyPhase -= surveyCycleMicros;
        }
      }
      final focusRemaining = state.focusRemainingMicros > step
          ? state.focusRemainingMicros - step
          : BigInt.zero;
      final hadBonus = state.focusRemainingMicros > BigInt.zero;
      final hadSupport = state.support.remainingMicros > BigInt.zero;
      var support = state.support.copyWith(
          remainingMicros: state.support.remainingMicros > step
              ? state.support.remainingMicros - step
              : BigInt.zero);
      if (offlineSettlementId != null)
        support = _captureSlice(support, offset, step, unboostedRate, weight);
      final previousFocus = state.focusCharges;
      final previousSurveys = state.completedSurveys;
      state = state.copyWith(
          walletMicros: state.walletMicros + earned,
          lifetimeMicros: state.lifetimeMicros + earned,
          elapsedMicros: state.elapsedMicros + step,
          earningRemainder: producedNumerator % _earningDenominator,
          focusCharges: focusCharges,
          focusPhaseMicros: focusPhase,
          completedSurveys: surveys,
          surveyPhaseMicros: surveyPhase,
          focusRemainingMicros: focusRemaining,
          support: support,
          revision: state.revision + 1);
      // Earnings settle first; equal-time expiry, Focus, then Survey events.
      if (hadBonus && focusRemaining == BigInt.zero)
        events.add(_event(state, 'focus_expired', index: 0));
      if (hadSupport && support.remainingMicros == BigInt.zero)
        events.add(_event(state, 'support_expired', index: 4));
      if (focusCharges > previousFocus)
        events.add(_event(state, 'focus_generated', index: 1));
      if (surveys > previousSurveys)
        events.add(_event(state, 'survey_completed', index: 2));
      final previousDay = state.daily.dayHighWater;
      state = _syncSupportDay(_advanceCalendar(state, offline: offline));
      if (state.daily.dayHighWater > previousDay) {
        events.add(_event(state, 'account_day_advanced', index: 3, details: {
          'account_day': state.daily.dayHighWater,
          'materialized_online': !offline
        }));
      }
      remaining -= step;
      offset += step;
    }
    // Purchases exactly at the final boundary happen after timer events, just
    // as they do at an internal boundary. Prevent chunk-end policy drift.
    while (true) {
      if (_automaticRechartEligible(state)) {
        if (++iterations > maximumEvents)
          throw StateError('Timeline event budget exceeded');
        final reset = rechart(state);
        state = reset.state;
        events.addAll(reset.events);
        continue;
      }
      if (!enabled) break;
      final tier = _plannedPurchaseTier(state);
      if (priceMicros(tier, state.counts[tier]) > state.walletMicros) break;
      if (++iterations > maximumEvents)
        throw StateError('Timeline event budget exceeded');
      final purchase = buy(state, tier, 1);
      state = purchase.state;
      events.addAll(purchase.events);
    }
    if (offlineSettlementId != null && finalizeOfflineSettlement) {
      final support = state.support;
      final rate = outputPerSecond(state).raw;
      state = state.copyWith(
          support: support.copyWith(
              caches: support.caches
                  .map((cache) => cache.settlementId == offlineSettlementId
                      ? cache.finalize(rate)
                      : cache)
                  .toList(),
              // Legacy sets remain frozen except this one already-pending
              // legacy operation, whose completion adds its final deny-list ID.
              closedSettlementIds: legacySettlementId == null
                  ? support.closedSettlementIds
                  : {...support.closedSettlementIds, legacySettlementId},
              lastSettlementSequence:
                  offlineSettlement?.sequence ?? support.lastSettlementSequence,
              lastSettlementThroughUtcMicros:
                  offlineSettlement?.throughUtcMicros ?? legacyThroughUtc,
              lastFinalizedSettlementId: offlineSettlementId,
              receiptCursorMigrationRequired: false,
              clearActiveSettlement: true),
          revision: state.revision + 1);
      events.add(_event(state, 'offline_salvage_finalized', details: {
        'settlement_id': offlineSettlementId,
        'settlement_rate_raw': rate.toString(),
      }));
    }
    return TransitionResult(state, events: events);
  }
}

/// FIFO eviction affects performance only; a miss always computes the exact
/// same canonical integer result. Large price/Chart values bypass retention.
class _NumericMemo<K, V> {
  _NumericMemo(this.capacity);
  final int capacity;
  final Map<K, V> _values = {};

  V read(K key, V Function() calculate) {
    final cached = _values[key];
    if (cached != null) return cached;
    final value = calculate();
    if (_values.length >= capacity) _values.remove(_values.keys.first);
    _values[key] = value;
    return value;
  }
}
