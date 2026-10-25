import 'package:tideglass_core/tideglass_core.dart';
import 'definition.dart';

enum SeasonPhase { upcoming, live, archived }

enum SeasonPolicy { bestPayback, tierPriority }

/// Only event production quantities can be serialized here. Main daily,
/// Support, Chart, Note, entitlement and automation-plan fields cannot enter.
class SeasonFleet {
  final List<int> counts;
  final BigInt walletMicros, lifetimeMicros, elapsedMicros, earningRemainder;
  SeasonFleet._(List<int> counts, this.walletMicros, this.lifetimeMicros,
      this.elapsedMicros, this.earningRemainder)
      : counts = List.unmodifiable(counts) {
    asCore.validate();
  }
  factory SeasonFleet.initial() => SeasonFleet._(
      [1, 0, 0, 0, 0], BigInt.zero, BigInt.zero, BigInt.zero, BigInt.zero);
  GameState get asCore => GameState(
      counts: counts,
      walletMicros: walletMicros,
      lifetimeMicros: lifetimeMicros,
      elapsedMicros: elapsedMicros,
      earningRemainder: earningRemainder);
  factory SeasonFleet._fromCore(GameState state) => SeasonFleet._(
      state.counts,
      state.walletMicros,
      state.lifetimeMicros,
      state.elapsedMicros,
      state.earningRemainder);
  Map<String, dynamic> toJson() => {
        'counts': counts,
        'wallet_micros': walletMicros.toString(),
        'lifetime_micros': lifetimeMicros.toString(),
        'elapsed_micros': elapsedMicros.toString(),
        'earning_remainder': earningRemainder.toString()
      };
  factory SeasonFleet.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {
      'counts',
      'wallet_micros',
      'lifetime_micros',
      'elapsed_micros',
      'earning_remainder'
    });
    return SeasonFleet._(
        List<int>.from(json['counts']),
        parseNonnegativeInteger(json['wallet_micros']),
        parseNonnegativeInteger(json['lifetime_micros']),
        parseNonnegativeInteger(json['elapsed_micros']),
        parseNonnegativeInteger(json['earning_remainder']));
  }
}

class SeasonState {
  final String seasonId, rulesVersion, rulesDigest, baseEconomyVersion, runId;
  final BigInt startsAtMicros, endsAtMicros, settledThroughMicros;
  final SeasonFleet fleet;
  final bool automatic, archiveActive;
  final SeasonPolicy policy;
  final List<int> priority;
  final Set<String> claimedMilestones;
  SeasonState._(
      {required this.seasonId,
      required this.rulesVersion,
      required this.rulesDigest,
      required this.baseEconomyVersion,
      required this.runId,
      required this.startsAtMicros,
      required this.endsAtMicros,
      required this.settledThroughMicros,
      required this.fleet,
      this.automatic = false,
      this.archiveActive = false,
      this.policy = SeasonPolicy.bestPayback,
      List<int> priority = const [4, 3, 2, 1, 0],
      Set<String> claimedMilestones = const {}})
      : priority = List.unmodifiable(priority),
        claimedMilestones = Set.unmodifiable(claimedMilestones) {
    if (runId.isEmpty ||
        runId.length > 200 ||
        startsAtMicros.isNegative ||
        settledThroughMicros.isNegative ||
        endsAtMicros - startsAtMicros != BigInt.from(2419200000000) ||
        (archiveActive && settledThroughMicros < endsAtMicros) ||
        priority.length != 5 ||
        priority.toSet().length != 5 ||
        priority.any((v) => v < 0 || v > 4))
      throw const FormatException('Invalid pinned season state.');
  }
  factory SeasonState.initial(
          SeasonDefinition definition, SeasonSchedule schedule, DateTime nowUtc,
          {required String runId}) =>
      SeasonState._(
          seasonId: definition.id,
          rulesVersion: definition.rulesVersion,
          rulesDigest: definition.digest,
          baseEconomyVersion: economyVersion,
          runId: runId,
          startsAtMicros: schedule.startsAtMicros,
          endsAtMicros: schedule.endsAtMicros,
          settledThroughMicros:
              BigInt.from(nowUtc.toUtc().microsecondsSinceEpoch),
          fleet: SeasonFleet.initial());
  SeasonPhase get phase => settledThroughMicros < startsAtMicros
      ? SeasonPhase.upcoming
      : settledThroughMicros < endsAtMicros
          ? SeasonPhase.live
          : SeasonPhase.archived;
  bool get canPlay =>
      phase == SeasonPhase.live ||
      (phase == SeasonPhase.archived && archiveActive);
  SeasonState _copy(
          {SeasonFleet? fleet,
          BigInt? settledThroughMicros,
          bool? automatic,
          bool? archiveActive,
          SeasonPolicy? policy,
          List<int>? priority,
          Set<String>? claimedMilestones}) =>
      SeasonState._(
          seasonId: seasonId,
          rulesVersion: rulesVersion,
          rulesDigest: rulesDigest,
          baseEconomyVersion: baseEconomyVersion,
          runId: runId,
          startsAtMicros: startsAtMicros,
          endsAtMicros: endsAtMicros,
          settledThroughMicros:
              settledThroughMicros ?? this.settledThroughMicros,
          fleet: fleet ?? this.fleet,
          automatic: automatic ?? this.automatic,
          archiveActive: archiveActive ?? this.archiveActive,
          policy: policy ?? this.policy,
          priority: priority ?? this.priority,
          claimedMilestones: claimedMilestones ?? this.claimedMilestones);
  Map<String, dynamic> toJson() => {
        'schema_version': 1,
        'season_id': seasonId,
        'rules_version': rulesVersion,
        'rules_digest': rulesDigest,
        'base_economy_version': baseEconomyVersion,
        'run_id': runId,
        'starts_at_micros': startsAtMicros.toString(),
        'ends_at_micros': endsAtMicros.toString(),
        'settled_through_micros': settledThroughMicros.toString(),
        'fleet': fleet.toJson(),
        'automatic': automatic,
        'archive_active': archiveActive,
        'policy': policy.name,
        'priority': priority,
        'claimed_milestones': claimedMilestones.toList()..sort()
      };
  factory SeasonState.fromJson(
      Map<String, dynamic> json, SeasonDefinition definition) {
    exactKeys(json, {
      'schema_version',
      'season_id',
      'rules_version',
      'rules_digest',
      'base_economy_version',
      'run_id',
      'starts_at_micros',
      'ends_at_micros',
      'settled_through_micros',
      'fleet',
      'automatic',
      'archive_active',
      'policy',
      'priority',
      'claimed_milestones'
    });
    if (json['schema_version'] != 1)
      throw const FormatException('Unsupported season save version.');
    final state = SeasonState._(
        seasonId: json['season_id'] as String,
        rulesVersion: json['rules_version'] as String,
        rulesDigest: json['rules_digest'] as String,
        baseEconomyVersion: json['base_economy_version'] as String,
        runId: json['run_id'] as String,
        startsAtMicros: parseNonnegativeInteger(json['starts_at_micros']),
        endsAtMicros: parseNonnegativeInteger(json['ends_at_micros']),
        settledThroughMicros:
            parseNonnegativeInteger(json['settled_through_micros']),
        fleet: SeasonFleet.fromJson(Map<String, dynamic>.from(json['fleet'])),
        automatic: json['automatic'] as bool,
        archiveActive: json['archive_active'] as bool,
        policy: SeasonPolicy.values.byName(json['policy'] as String),
        priority: List<int>.from(json['priority']),
        claimedMilestones: stringSet(json['claimed_milestones']));
    SeasonEngine(definition).validate(state);
    return state;
  }
}

class SeasonEvent {
  final String kind;
  final BigInt atUtcMicros;
  final Map<String, dynamic> details;
  SeasonEvent(this.kind, this.atUtcMicros,
      {Map<String, dynamic> details = const {}})
      : details = Map.unmodifiable(details);
}

class SeasonResult {
  final SeasonState state;
  final bool accepted;
  final String? reason;
  final List<SeasonEvent> events;
  SeasonResult(this.state,
      {this.accepted = true, this.reason, List<SeasonEvent> events = const []})
      : events = List.unmodifiable(events);
}

class _FleetEconomy extends TideglassEngine {
  final SeasonDefinition definition;
  const _FleetEconomy(this.definition);
  @override
  Fixed prestigeMultiplier(BigInt charts) => Fixed.one;
  @override
  Fixed synergyMultiplier(GameState state, int tierIndex) {
    if (tierIndex < 3) return Fixed.one;
    final a = log2Ratio(BigInt.from(25 + state.counts[0]), BigInt.from(25));
    final b = log2Ratio(BigInt.from(25 + state.counts[1]), BigInt.from(25));
    return Fixed.raw(Fixed.scale +
        (a.raw * BigInt.from(definition.matrix[0][tierIndex - 3]) +
                b.raw * BigInt.from(definition.matrix[1][tierIndex - 3])) ~/
            BigInt.from(100));
  }
}

class SeasonEngine {
  final SeasonDefinition definition;
  late final _FleetEconomy _economy = _FleetEconomy(definition);
  SeasonEngine(this.definition);
  void validate(SeasonState state) {
    if (state.seasonId != definition.id ||
        state.rulesVersion != definition.rulesVersion ||
        state.rulesDigest != definition.digest ||
        state.baseEconomyVersion != economyVersion)
      throw const FormatException('Pinned season parameters do not match.');
    for (final id in state.claimedMilestones) {
      final goals = definition.milestones.where((m) => m.id == id);
      if (goals.isEmpty ||
          state.fleet.lifetimeMicros < goals.single.lifetimeMicros)
        throw const FormatException('Unreached or unknown seasonal milestone.');
    }
  }

  Fixed outputPerSecond(SeasonState state) {
    validate(state);
    return _economy.outputPerSecond(state.fleet.asCore);
  }

  Fixed synergyMultiplier(SeasonState state, int tier) {
    validate(state);
    return _economy.synergyMultiplier(state.fleet.asCore, tier);
  }

  BigInt priceMicros(SeasonState state, int tier) {
    validate(state);
    return _economy.priceMicros(tier, state.fleet.counts[tier]);
  }

  int maximumAffordable(SeasonState state, int tier) {
    validate(state);
    return _economy.maximumAffordable(state.fleet.asCore, tier);
  }

  bool isUnlocked(SeasonState state, int tier) =>
      _economy.isUnlocked(state.fleet.asCore, tier);
  SeasonResult purchase(SeasonState state, int tier, int quantity) {
    validate(state);
    if (!state.canPlay)
      return SeasonResult(state,
          accepted: false, reason: 'season_fleet_paused');
    final result = _economy.buy(state.fleet.asCore, tier, quantity);
    return result.accepted
        ? SeasonResult(state._copy(fleet: SeasonFleet._fromCore(result.state)))
        : SeasonResult(state, accepted: false, reason: result.reason);
  }

  SeasonResult rechart(SeasonState state) {
    validate(state);
    return SeasonResult(state,
        accepted: false, reason: 'season_has_no_rechart');
  }

  SeasonResult configurePolicy(SeasonState state,
      {required bool automatic,
      SeasonPolicy policy = SeasonPolicy.bestPayback,
      List<int> priority = const [4, 3, 2, 1, 0]}) {
    validate(state);
    return SeasonResult(
        state._copy(automatic: automatic, policy: policy, priority: priority));
  }

  SeasonResult resumeArchive(SeasonState state, DateTime nowUtc) {
    final settled = advanceTo(state, nowUtc);
    if (settled.state.phase != SeasonPhase.archived)
      return SeasonResult(settled.state,
          accepted: false,
          reason: 'season_not_archived',
          events: settled.events);
    if (settled.state.archiveActive)
      return SeasonResult(settled.state,
          accepted: false,
          reason: 'archive_already_active',
          events: settled.events);
    return SeasonResult(settled.state._copy(archiveActive: true), events: [
      ...settled.events,
      SeasonEvent('archive_resumed', settled.state.settledThroughMicros)
    ]);
  }

  SeasonResult pauseArchive(SeasonState state, DateTime nowUtc) {
    final settled = advanceTo(state, nowUtc);
    if (!settled.state.archiveActive)
      return SeasonResult(settled.state,
          accepted: false,
          reason: 'archive_not_active',
          events: settled.events);
    return SeasonResult(settled.state._copy(archiveActive: false), events: [
      ...settled.events,
      SeasonEvent('archive_paused', settled.state.settledThroughMicros)
    ]);
  }

  SeasonResult claimMilestone(SeasonState state, String milestoneId) {
    validate(state);
    final matches = definition.milestones.where((m) => m.id == milestoneId);
    if (matches.isEmpty ||
        state.claimedMilestones.contains(milestoneId) ||
        state.fleet.lifetimeMicros < matches.single.lifetimeMicros)
      return SeasonResult(state,
          accepted: false, reason: 'milestone_unavailable');
    final milestone = matches.single;
    return SeasonResult(
        state._copy(
            claimedMilestones: {...state.claimedMilestones, milestoneId}),
        events: [
          SeasonEvent('season_badge_claimed', state.settledThroughMicros,
              details: {
                'receipt_id': 'season:${state.runId}:$milestoneId',
                'badge_id': milestone.badgeId
              })
        ]);
  }

  Set<String> badgeIds(SeasonState state) {
    validate(state);
    return definition.milestones
        .where((m) => state.claimedMilestones.contains(m.id))
        .map((m) => m.badgeId)
        .toSet();
  }

  /// Advance absolute monotone UTC high-water time. Only live intervals or an
  /// explicitly resumed archive earn. Offline offsets belong to the full
  /// absence, including time before a scheduled season start.
  SeasonResult advanceTo(SeasonState state, DateTime nowUtc,
      {bool offline = false,
      Duration offlineElapsedBefore = Duration.zero,
      int maximumEvents = 100000}) {
    validate(state);
    if (offlineElapsedBefore.isNegative || maximumEvents <= 0)
      throw ArgumentError('Invalid replay options.');
    final now = BigInt.from(nowUtc.toUtc().microsecondsSinceEpoch);
    if (now <= state.settledThroughMicros)
      return SeasonResult(state,
          accepted: false,
          reason: now < state.settledThroughMicros
              ? 'clock_rollback'
              : 'already_settled');
    final events = <SeasonEvent>[];
    final from = state.settledThroughMicros;
    var begin = from > state.startsAtMicros ? from : state.startsAtMicros;
    var end = now < state.endsAtMicros ? now : state.endsAtMicros;
    if (state.archiveActive) {
      begin = from;
      end = now;
    }
    var fleet = state.fleet;
    if (end > begin) {
      fleet = _advanceFleet(state, end - begin,
          offline: offline,
          offset:
              BigInt.from(offlineElapsedBefore.inMicroseconds) + begin - from,
          maximumEvents: maximumEvents);
    }
    if (from < state.startsAtMicros && now >= state.startsAtMicros)
      events.add(SeasonEvent('season_started', state.startsAtMicros));
    if (from < state.endsAtMicros && now >= state.endsAtMicros)
      events.add(SeasonEvent('season_archived', state.endsAtMicros));
    return SeasonResult(state._copy(fleet: fleet, settledThroughMicros: now),
        events: events);
  }

  SeasonFleet _advanceFleet(SeasonState state, BigInt duration,
      {required bool offline,
      required BigInt offset,
      required int maximumEvents}) {
    var fleet = state.fleet.asCore;
    var left = duration;
    var iterations = 0;
    while (true) {
      if (++iterations > maximumEvents)
        throw StateError(
            'Season replay requires smaller carried-offset chunks.');
      int? tier;
      if (state.automatic) {
        tier = state.policy == SeasonPolicy.bestPayback
            ? _economy.chooseAutoBuyTier(fleet)
            : state.priority.firstWhere((t) => _economy.isUnlocked(fleet, t));
      }
      final cost =
          tier == null ? null : _economy.priceMicros(tier, fleet.counts[tier]);
      if (tier != null && cost! <= fleet.walletMicros) {
        fleet = _economy.buy(fleet, tier, 1).state;
        continue;
      }
      if (left == BigInt.zero) break;
      var step = left;
      void limit(BigInt n) {
        if (n > BigInt.zero && n < step) step = n;
      }

      final weight = !offline || offset < TideglassEngine.fullOfflineMicros
          ? 4
          : offset < TideglassEngine.totalOfflineMicros
              ? 1
              : 0;
      if (offline && offset < TideglassEngine.fullOfflineMicros)
        limit(TideglassEngine.fullOfflineMicros - offset);
      if (offline && offset < TideglassEngine.totalOfflineMicros)
        limit(TideglassEngine.totalOfflineMicros - offset);
      if (cost != null && weight > 0) {
        final need =
            (cost - fleet.walletMicros) * Fixed.scale * BigInt.from(400) -
                fleet.earningRemainder;
        limit(ceilDivide(need,
            _economy.outputPerSecond(fleet).raw * BigInt.from(weight * 100)));
      }
      // Extract only production quantities; generated main daily queues never
      // become part of a seasonal fleet or provide an action/reward route.
      fleet = _economy
          .advance(fleet, Duration(microseconds: step.toInt()),
              offline: offline,
              autoBuy: false,
              offlineElapsedBefore: Duration(microseconds: offset.toInt()))
          .state;
      fleet = SeasonFleet._fromCore(fleet).asCore;
      left -= step;
      offset += step;
    }
    return SeasonFleet._fromCore(fleet);
  }
}
