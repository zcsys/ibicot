library;

import 'dart:convert';
import 'package:tideglass_core/tideglass_core.dart';

/// A dossier owns a separate fleet. Main Charts, Focus, Support, Notes and
/// wallet never enter this state; the only main-world transaction is entry.
class ChallengeDefinition {
  ChallengeDefinition({
    required this.id,
    required this.family,
    required this.title,
    required this.intro,
    required this.completion,
    required List<int?> tierCaps,
    required List<List<int>> matrix,
    required this.synergyImmediate,
    required this.automaticOnly,
    required this.goalMicros,
  }) : tierCaps = List.unmodifiable(tierCaps),
       matrix = List.unmodifiable(
         matrix.map((v) => List<int>.unmodifiable(v)),
       ) {
    if (!RegExp(r'^challenge\.(0[1-9]|1[0-2])$').hasMatch(id) ||
        !{
          'constrained_fleets',
          'synergy_priorities',
          'automation_planning',
        }.contains(family) ||
        tierCaps.length != 5 ||
        (tierCaps[0] != null && tierCaps[0]! < 1) ||
        tierCaps.any((n) => n != null && n < 0) ||
        matrix.length != 2 ||
        matrix.any(
          (row) => row.length != 2 || row.any((v) => v < 0 || v > 100),
        ) ||
        goalMicros <= BigInt.zero) {
      throw const FormatException('Invalid challenge rules.');
    }
    // A capped prerequisite cannot strand a later required producer.
    for (var tier = 1; tier < 5; tier++) {
      if (tierCaps[tier] != 0 &&
          tierCaps[tier - 1] != null &&
          tierCaps[tier - 1]! < 10) {
        throw const FormatException('Challenge has an unreachable producer.');
      }
    }
  }
  final String id, family, title, intro, completion;
  final List<int?> tierCaps;
  final List<List<int>> matrix;
  final bool synergyImmediate, automaticOnly;
  final BigInt goalMicros;

  factory ChallengeDefinition.fromJson(Map<String, dynamic> json) {
    if (json['schema_version'] != 1 ||
        json['dossier_cost_notes'] != 100 ||
        json['main_power_import'] != false ||
        json['economic_export'] != false ||
        json['prestige_enabled'] != false ||
        json['focus_enabled'] != false ||
        json['support_enabled'] != false ||
        json['replay_cost_notes'] != 0 ||
        json['dossier_persistent'] != true ||
        json['main_policy_continues'] != true ||
        json['offline_envelope'] != '24h_full_48h_quarter' ||
        !{
          'manual_or_automatic',
          'automatic_only',
        }.contains(json['construction_mode']) ||
        json['goal'] is! Map ||
        json['goal']['kind'] != 'lifetime_r') {
      throw const FormatException(
        'Unsupported or economically unsafe dossier.',
      );
    }
    return ChallengeDefinition(
      id: json['id'] as String,
      family: json['family'] as String,
      title: json['title'] as String,
      intro: json['intro'] as String,
      completion: json['completion'] as String,
      tierCaps: List<int?>.from(json['tier_caps'] as List),
      matrix: (json['synergy_percent_matrix'] as List)
          .map((v) => List<int>.from(v))
          .toList(),
      synergyImmediate: json['synergy_immediate'] as bool,
      automaticOnly: json['construction_mode'] == 'automatic_only',
      goalMicros:
          BigInt.parse(json['goal']['amount'] as String) * BigInt.from(1000000),
    );
  }
}

enum ChallengePolicy { bestPayback, tierPriority }

class ChallengeRun {
  ChallengeRun({
    required this.dossierId,
    GameState? fleet,
    this.automatic = false,
    this.policy = ChallengePolicy.bestPayback,
    List<int> priority = const [4, 3, 2, 1, 0],
    this.complete = false,
  }) : fleet = fleet ?? GameState.initial(),
       priority = List.unmodifiable(priority) {
    if (priority.length != 5 ||
        priority.toSet().length != 5 ||
        priority.any((v) => v < 0 || v > 4)) {
      throw const FormatException(
        'Priority must contain each tier exactly once.',
      );
    }
    if (this.fleet.charts != BigInt.zero ||
        this.fleet.focusRemainingMicros != BigInt.zero ||
        jsonEncode(this.fleet.support.toJson()) !=
            jsonEncode(SupportState().toJson()) ||
        this.fleet.surveyNotes != BigInt.zero ||
        this.fleet.autoBuyEnabled) {
      throw const FormatException('Main-world power cannot enter a challenge.');
    }
  }
  final String dossierId;
  final GameState fleet;
  final bool automatic, complete;
  final ChallengePolicy policy;
  final List<int> priority;
  ChallengeRun copyWith({
    GameState? fleet,
    bool? automatic,
    ChallengePolicy? policy,
    List<int>? priority,
    bool? complete,
  }) => ChallengeRun(
    dossierId: dossierId,
    fleet: fleet ?? this.fleet,
    automatic: automatic ?? this.automatic,
    policy: policy ?? this.policy,
    priority: priority ?? this.priority,
    complete: complete ?? this.complete,
  );
  Map<String, dynamic> toJson() => {
    'dossier_id': dossierId,
    'fleet': fleet.toJson(),
    'automatic': automatic,
    'policy': policy.name,
    'priority': priority,
    'complete': complete,
  };
  factory ChallengeRun.fromJson(Map<String, dynamic> json) => ChallengeRun(
    dossierId: json['dossier_id'] as String,
    fleet: GameState.fromJson(Map<String, dynamic>.from(json['fleet'])),
    automatic: json['automatic'] as bool,
    policy: ChallengePolicy.values.byName(json['policy'] as String),
    priority: List<int>.from(json['priority']),
    complete: json['complete'] as bool,
  );
}

/// Reuses the exact production price/milestone/number implementation while
/// overriding only the dossier's published constraints and synergy matrix.
class ChallengeEconomy extends TideglassEngine {
  const ChallengeEconomy(this.definition);
  final ChallengeDefinition definition;
  @override
  bool isUnlocked(GameState state, int tierIndex) =>
      super.isUnlocked(state, tierIndex) &&
      (definition.tierCaps[tierIndex] == null ||
          state.counts[tierIndex] < definition.tierCaps[tierIndex]!);
  @override
  Fixed synergyMultiplier(GameState state, int tierIndex) {
    if (!definition.synergyImmediate || tierIndex < 3) return Fixed.one;
    final a = log2Ratio(BigInt.from(25 + state.counts[0]), BigInt.from(25));
    final b = log2Ratio(BigInt.from(25 + state.counts[1]), BigInt.from(25));
    return Fixed.raw(
      Fixed.scale +
          (a.raw * BigInt.from(definition.matrix[0][tierIndex - 3]) +
                  b.raw * BigInt.from(definition.matrix[1][tierIndex - 3])) ~/
              BigInt.from(100),
    );
  }

  @override
  TransitionResult buy(GameState state, int tierIndex, int quantity) {
    final cap = definition.tierCaps[tierIndex];
    if (cap != null && state.counts[tierIndex] + quantity > cap) {
      return TransitionResult(
        state,
        accepted: false,
        reason: 'dossier_berth_limit',
      );
    }
    return super.buy(state, tierIndex, quantity);
  }

  @override
  int maximumAffordable(GameState state, int tierIndex) {
    final n = super.maximumAffordable(state, tierIndex);
    final cap = definition.tierCaps[tierIndex];
    return cap == null ? n : n.clamp(0, cap - state.counts[tierIndex]);
  }

  @override
  TransitionResult rechart(GameState state) => TransitionResult(
    state,
    accepted: false,
    reason: 'dossier_has_no_rechart',
  );

  void validateRun(ChallengeRun run) {
    if (run.dossierId != definition.id)
      throw const FormatException('Wrong dossier rules.');
    for (var tier = 0; tier < 5; tier++) {
      final cap = definition.tierCaps[tier];
      if (cap != null && run.fleet.counts[tier] > cap)
        throw const FormatException('Fleet exceeds berth limit.');
    }
    if (run.complete && run.fleet.lifetimeMicros < definition.goalMicros) {
      throw const FormatException('Unreached challenge completion.');
    }
  }

  ChallengeRun newRun() => ChallengeRun(
    dossierId: definition.id,
    automatic: definition.automaticOnly,
  );
  ChallengeRun purchase(ChallengeRun run, int tier, int quantity) {
    validateRun(run);
    if (definition.automaticOnly) return run;
    final next = buy(run.fleet, tier, quantity);
    return next.accepted ? run.copyWith(fleet: next.state) : run;
  }

  int? nextTier(ChallengeRun run) {
    if (run.policy == ChallengePolicy.tierPriority) {
      for (final tier in run.priority) {
        if (isUnlocked(run.fleet, tier)) return tier;
      }
      return null;
    }
    int? chosen;
    var gain = BigInt.from(-1), cost = BigInt.one;
    for (var tier = 0; tier < 5; tier++) {
      if (!isUnlocked(run.fleet, tier)) continue;
      final delta = marginalOutputPerSecond(run.fleet, tier).raw;
      final price = priceMicros(tier, run.fleet.counts[tier]);
      if (delta * cost >= gain * price) {
        chosen = tier;
        gain = delta;
        cost = price;
      }
    }
    return chosen;
  }

  /// Production and automatic purchases share exact microsecond boundaries.
  /// The same absence offset is carried when a replay is split into chunks.
  ChallengeRun advanceRun(
    ChallengeRun initial,
    Duration duration, {
    bool offline = false,
    Duration offlineElapsedBefore = Duration.zero,
    int maximumEvents = 100000,
  }) {
    validateRun(initial);
    if (duration.isNegative ||
        offlineElapsedBefore.isNegative ||
        maximumEvents <= 0) {
      throw ArgumentError('Invalid challenge interval.');
    }
    var run = initial;
    var left = BigInt.from(duration.inMicroseconds);
    var offset = BigInt.from(offlineElapsedBefore.inMicroseconds);
    var iterations = 0;
    while (true) {
      if (++iterations > maximumEvents)
        throw StateError(
          'Challenge replay needs smaller carried-offset chunks.',
        );
      final tier = run.automatic || definition.automaticOnly
          ? nextTier(run)
          : null;
      final cost = tier == null
          ? null
          : priceMicros(tier, run.fleet.counts[tier]);
      if (tier != null && cost != null && cost <= run.fleet.walletMicros) {
        final result = buy(run.fleet, tier, 1);
        if (!result.accepted)
          throw StateError('A chosen challenge purchase must be valid.');
        run = run.copyWith(fleet: result.state);
        continue;
      }
      if (left == BigInt.zero) break;
      var step = left;
      void limit(BigInt v) {
        if (v > BigInt.zero && v < step) step = v;
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
      final rate = outputPerSecond(run.fleet).raw;
      if (cost != null && weight > 0 && rate > BigInt.zero) {
        final needed =
            (cost - run.fleet.walletMicros) * Fixed.scale * BigInt.from(400) -
            run.fleet.earningRemainder;
        limit(ceilDivide(needed, rate * BigInt.from(weight * 100)));
      }
      final next = super.advance(
        run.fleet,
        Duration(microseconds: step.toInt()),
        offline: offline,
        autoBuy: false,
        offlineElapsedBefore: Duration(microseconds: offset.toInt()),
      );
      run = run.copyWith(
        fleet: next.state,
        complete:
            run.complete || next.state.lifetimeMicros >= definition.goalMicros,
      );
      left -= step;
      offset += step;
    }
    return run;
  }
}

class ProgressFacts {
  ProgressFacts({
    required this.main,
    required this.recharts,
    required this.surveysCollected,
    required Set<String> calibrations,
    required Set<String> completedChallenges,
  }) : calibrations = Set.unmodifiable(calibrations),
       completedChallenges = Set.unmodifiable(completedChallenges);
  final GameState main;
  final int recharts, surveysCollected;
  final Set<String> calibrations, completedChallenges;
}

class CampaignProgress {
  CampaignProgress({Set<String> completed = const {}})
    : completed = Set.unmodifiable(completed) {
    if (completed.length > 6 ||
        !List.generate(
          completed.length,
          (i) => 'chapter.${(i + 1).toString().padLeft(2, '0')}',
        ).every(completed.contains)) {
      throw const FormatException(
        'Campaign must preserve a contiguous completed chapter prefix.',
      );
    }
  }
  final Set<String> completed;
  int get restoredHarbor => completed.length;
  bool get hasEnding => completed.contains('chapter.06');
  Set<String> get cosmeticIds =>
      completed.map((id) => 'cosmetic.core.$id').toSet();
  Set<String> get archiveIds => {
    for (var chapter = 1; chapter <= 6; chapter++)
      if (completed.contains('chapter.${chapter.toString().padLeft(2, '0')}'))
        for (var entry = (chapter - 1) * 3 + 1; entry <= chapter * 3; entry++)
          'archive.main.${entry.toString().padLeft(2, '0')}',
  };
  Map<String, dynamic> toJson() => {
    'completed_chapters': completed.toList()..sort(),
  };
  factory CampaignProgress.fromJson(Map<String, dynamic> json) {
    final values = List<String>.from(json['completed_chapters']);
    if (values.toSet().length != values.length ||
        values.length > 6 ||
        !List.generate(
          values.length,
          (i) => 'chapter.${(i + 1).toString().padLeft(2, '0')}',
        ).every(values.contains)) {
      throw const FormatException(
        'Campaign must preserve a contiguous completed chapter prefix.',
      );
    }
    return CampaignProgress(completed: values.toSet());
  }
}

class Campaign {
  Campaign(Map<String, dynamic> source, List<ChallengeDefinition> dossiers)
    : chapters = List.unmodifiable(
        (source['chapters'] as List).map(
          (v) => _frozenMap(Map<String, dynamic>.from(v)),
        ),
      ),
      families = Map.unmodifiable({for (final d in dossiers) d.id: d.family}) {
    if (source['schema_version'] != 1 ||
        chapters.length != 6 ||
        families.length != 12) {
      throw const FormatException(
        'Incomplete campaign or challenge catalogue.',
      );
    }
    for (var index = 0; index < 6; index++) {
      final chapter = chapters[index];
      final suffix = (index + 1).toString().padLeft(2, '0');
      final previous = index == 0
          ? null
          : 'chapter.${index.toString().padLeft(2, '0')}';
      if (chapter['id'] != 'chapter.$suffix' ||
          chapter['order'] != index + 1 ||
          chapter['prerequisite'] != previous ||
          chapter['objective_mode'] != 'all' ||
          chapter['reward_cosmetic_id'] != 'cosmetic.core.chapter.$suffix' ||
          chapter['harbor_state'] != 'harbor.restored.$suffix' ||
          chapter['economic_rewards'] is! List ||
          (chapter['economic_rewards'] as List).isNotEmpty ||
          chapter['paid_requirements'] is! List ||
          (chapter['paid_requirements'] as List).isNotEmpty ||
          chapter['objectives'] is! List ||
          (chapter['objectives'] as List).isEmpty) {
        throw const FormatException(
          'Invalid campaign order, reward, or objective contract.',
        );
      }
      for (final raw in chapter['objectives'] as List) {
        if (raw is! Map || raw['value'] is! int || (raw['value'] as int) < 1) {
          throw const FormatException('Invalid campaign objective value.');
        }
        final valid = switch (raw['kind']) {
          'owned_min' =>
            raw['tier'] is int && raw['tier'] >= 1 && raw['tier'] <= 5,
          'stat_min' => {
            'recharts',
            'charts_awarded',
            'surveys_collected',
            'unique_calibrations',
          }.contains(raw['stat']),
          'challenge_family_min' => families.values.contains(raw['family']),
          _ => false,
        };
        if (!valid)
          throw const FormatException('Unsupported campaign objective.');
      }
    }
  }
  final List<Map<String, dynamic>> chapters;
  final Map<String, String> families;
  bool objectiveMet(Map<String, dynamic> goal, ProgressFacts facts) {
    final value = goal['value'] as int;
    return switch (goal['kind']) {
      'owned_min' => facts.main.counts[(goal['tier'] as int) - 1] >= value,
      'challenge_family_min' =>
        facts.completedChallenges
                .where((id) => families[id] == goal['family'])
                .length >=
            value,
      'stat_min' => switch (goal['stat']) {
        'recharts' => facts.recharts >= value,
        'charts_awarded' => facts.main.charts >= BigInt.from(value),
        'surveys_collected' => facts.surveysCollected >= value,
        'unique_calibrations' => facts.calibrations.length >= value,
        _ => throw const FormatException('Unknown campaign statistic.'),
      },
      _ => throw const FormatException('Unknown campaign objective.'),
    };
  }

  CampaignProgress evaluate(CampaignProgress previous, ProgressFacts facts) {
    final complete = previous.completed.toSet();
    for (final chapter in chapters) {
      final id = chapter['id'] as String;
      if (complete.contains(id)) continue;
      final prior = chapter['prerequisite'] as String?;
      if (prior != null && !complete.contains(prior)) break;
      if ((chapter['objectives'] as List).every(
        (v) => objectiveMet(Map<String, dynamic>.from(v), facts),
      )) {
        complete.add(id);
      } else {
        break;
      }
    }
    return CampaignProgress(completed: complete);
  }
}

Object? _freeze(Object? value) {
  if (value is Map) return _frozenMap(Map<String, dynamic>.from(value));
  if (value is List) return List<Object?>.unmodifiable(value.map(_freeze));
  return value;
}

Map<String, dynamic> _frozenMap(Map<String, dynamic> value) =>
    Map<String, dynamic>.unmodifiable(
      value.map((key, value) => MapEntry(key, _freeze(value))),
    );

/// Must be saved atomically alongside the returned main state. Opening a
/// previously owned dossier is free; replay and completion never export money.
class DossierCollection {
  DossierCollection({
    Set<String> owned = const {},
    Set<String> completed = const {},
    this.active,
  }) : owned = Set.unmodifiable(owned),
       completed = Set.unmodifiable(completed) {
    if (owned.any(
          (id) => !RegExp(r'^challenge\.(0[1-9]|1[0-2])$').hasMatch(id),
        ) ||
        !owned.containsAll(completed) ||
        (active != null && !owned.contains(active!.dossierId))) {
      throw const FormatException('Invalid dossier ownership or active fleet.');
    }
  }
  final Set<String> owned, completed;
  final ChallengeRun? active;
  Map<String, dynamic> toJson() => {
    'schema_version': 1,
    'owned': owned.toList()..sort(),
    'completed': completed.toList()..sort(),
    'active': active?.toJson(),
  };
  factory DossierCollection.fromJson(Map<String, dynamic> json) {
    if (json['schema_version'] != 1 || json.length != 4)
      throw const FormatException('Unsupported dossier state.');
    final owned = List<String>.from(json['owned']),
        completed = List<String>.from(json['completed']);
    if (owned.toSet().length != owned.length ||
        completed.toSet().length != completed.length) {
      throw const FormatException('Duplicate dossier receipt.');
    }
    return DossierCollection(
      owned: owned.toSet(),
      completed: completed.toSet(),
      active: json['active'] == null
          ? null
          : ChallengeRun.fromJson(Map<String, dynamic>.from(json['active'])),
    );
  }
  DossierTransition open(
    GameState main,
    CampaignProgress campaign,
    ChallengeDefinition definition, {
    bool replaceActive = false,
  }) {
    if (campaign.restoredHarbor < 3)
      return DossierTransition(
        main,
        this,
        false,
        'Restore chapter three first.',
      );
    if (active?.dossierId == definition.id)
      return DossierTransition(main, this, true, null);
    if (active != null && !replaceActive)
      return DossierTransition(
        main,
        this,
        false,
        'Confirm replacing the current challenge fleet.',
      );
    final price = owned.contains(definition.id)
        ? BigInt.zero
        : BigInt.from(100);
    if (main.surveyNotes < price)
      return DossierTransition(
        main,
        this,
        false,
        'This dossier needs 100 Survey Notes.',
      );
    final next = DossierCollection(
      owned: {...owned, definition.id},
      completed: completed,
      active: ChallengeEconomy(definition).newRun(),
    );
    return DossierTransition(
      main.copyWith(
        surveyNotes: main.surveyNotes - price,
        revision: main.revision + (price > BigInt.zero ? 1 : 0),
      ),
      next,
      true,
      null,
    );
  }

  DossierCollection withRun(ChallengeRun run, ChallengeDefinition definition) {
    if (active?.dossierId != run.dossierId)
      throw const FormatException('Cannot settle a different active dossier.');
    ChallengeEconomy(definition).validateRun(run);
    return DossierCollection(
      owned: owned,
      completed: {...completed, if (run.complete) run.dossierId},
      active: run,
    );
  }

  DossierCollection restart(ChallengeDefinition definition) {
    if (!owned.contains(definition.id))
      throw const FormatException('Dossier must be owned before replay.');
    if (active != null && active!.dossierId != definition.id) {
      throw const FormatException(
        'Use explicit replacement before replaying a different active dossier.',
      );
    }
    return DossierCollection(
      owned: owned,
      completed: completed,
      active: ChallengeEconomy(definition).newRun(),
    );
  }

  DossierCollection leave() =>
      DossierCollection(owned: owned, completed: completed);
}

class DossierTransition {
  const DossierTransition(this.main, this.dossiers, this.accepted, this.reason);
  final GameState main;
  final DossierCollection dossiers;
  final bool accepted;
  final String? reason;
}
