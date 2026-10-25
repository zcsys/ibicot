import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_events/tideglass_events.dart';

Map<String, dynamic> readObject(String path) =>
    Map<String, dynamic>.from(jsonDecode(File(path).readAsStringSync()));

/// Virtual deterministic policies, not human cohorts or retention evidence.
class SimulationContent {
  SimulationContent(String contentDirectory, String eventsDirectory) {
    challenges = [
      for (var i = 1; i <= 12; i++)
        ChallengeDefinition.fromJson(
          readObject(
            '$contentDirectory/challenges/challenge.${i.toString().padLeft(2, '0')}.json',
          ),
        ),
    ];
    campaign = Campaign(
      readObject('$contentDirectory/progression/campaign.json'),
      challenges,
    );
    season = SeasonDefinition.fromJson(
      readObject('$eventsDirectory/season.01.json'),
    );
  }
  late final List<ChallengeDefinition> challenges;
  late final Campaign campaign;
  late final SeasonDefinition season;
}

enum BonusPolicy {
  none,
  requiredCalibrationsOnly,
  allFocus,
  focusAndFreeSupport,
  focusAndAdSupportFixture,
}

enum ResetPolicy { atVisits, hourlyAutomatic }

enum PurchasePolicy { bestPayback, lowestTierFirst, highestTierFirst }

enum ContractPolicy {
  surveysOnly,
  oneReadyPerVisit,
  allReady,
  pursueWithSeason,
}

class PolicyRun {
  PolicyRun(
    this.content, {
    required this.visitsPerDay,
    required this.bonus,
    required this.resetPolicy,
    this.purchasePolicy = PurchasePolicy.bestPayback,
    this.contractPolicy = ContractPolicy.allReady,
    this.seed = 'policy-audit-01',
    this.offlineChunkHours = 4,
    this.breakStartsDay,
    this.breakHours = 0,
  }) {
    if (![1, 3, 6].contains(visitsPerDay) || offlineChunkHours < 1)
      throw ArgumentError('Invalid visit policy.');
    main = engine
        .refreshContracts(
          GameState.initial(),
          epoch,
          accountSeed: seed,
          utcOffsetMinutes: 0,
          availableDiscoveryKinds: ['archive'],
        )
        .state;
    season = SeasonState.initial(
      content.season,
      SeasonSchedule(epoch),
      epoch,
      runId: 'audit-$seed',
    );
    season = seasonEngine.configurePolicy(season, automatic: true).state;
    pass = PassState.initial([content.season]);
    final selected = passEngine.selectPass(main, pass, season);
    main = selected.main;
    pass = selected.pass;
  }
  static final epoch = DateTime.utc(2026, 10, 16);
  static const engine = TideglassEngine();
  final SimulationContent content;
  final int visitsPerDay, offlineChunkHours;
  final BonusPolicy bonus;
  final ResetPolicy resetPolicy;
  final PurchasePolicy purchasePolicy;
  final ContractPolicy contractPolicy;
  final String seed;
  final int? breakStartsDay;
  final int breakHours;
  late GameState main;
  late SeasonState season;
  late PassState pass;
  CampaignProgress campaign = CampaignProgress();
  DossierCollection dossiers = DossierCollection();
  DateTime cursor = epoch;
  final chapterAt = <String, int>{};
  final challengeAt = <String, int>{};
  final readArchives = <String>{};
  final checkpoints = <String, Map<String, dynamic>>{};
  int visits = 0,
      manualPurchases = 0,
      contractsClaimed = 0,
      supportUsed = 0,
      focusUsed = 0;
  BigInt notesSpent = BigInt.zero;
  BigInt surveyNotesEarned = BigInt.zero, contractNotesEarned = BigInt.zero;
  int _visitContractClaims = 0;
  int? firstResetSeconds;
  int? fullNoteBudgetSeconds, fullCollectionAffordableSeconds;
  int archiveReflections = 0,
      seasonalContractBindings = 0,
      seasonalContractClaims = 0;
  SeasonEngine get seasonEngine => SeasonEngine(content.season);
  PassEngine get passEngine => PassEngine([content.season]);
  Duration get elapsed => cursor.difference(epoch);

  List<String> get availableDiscoveries => [
    'archive',
    if (campaign.restoredHarbor >= 3 &&
        content.challenges.any((d) => !dossiers.completed.contains(d.id)))
      'challenge',
    if (main.focusCharges > 0 || main.completedCalibrationIds.isNotEmpty)
      'calibration',
  ];

  void _refreshDaily() => _main(
    engine.refreshContracts(
      main,
      cursor,
      availableDiscoveryKinds: availableDiscoveries,
    ),
  );

  void _main(TransitionResult result) {
    if (result.accepted) main = result.state;
  }

  void _evaluate() {
    campaign = content.campaign.evaluate(
      campaign,
      ProgressFacts(
        main: main,
        recharts: main.rechartCount,
        surveysCollected: main.surveysCollectedTotal.toInt(),
        calibrations: main.completedCalibrationIds,
        completedChallenges: dossiers.completed,
      ),
    );
    for (final id in campaign.completed) {
      chapterAt.putIfAbsent(id, () => elapsed.inSeconds);
    }
    if (main.rechartCount > 0) firstResetSeconds ??= elapsed.inSeconds;
  }

  void _step(
    Duration duration, {
    required bool offline,
    required Duration offset,
    OfflineSettlementRequest? receipt,
    bool finalChunk = true,
  }) {
    final through = cursor.add(duration);
    final advanced = engine.advance(
      main,
      duration,
      offline: offline,
      offlineElapsedBefore: offset,
      offlineSettlement: receipt,
      finalizeOfflineSettlement: finalChunk,
    );
    if (!advanced.accepted)
      throw StateError(advanced.reason ?? 'Main advance rejected');
    main = advanced.state;
    if (dossiers.active != null) {
      final current = dossiers.active!;
      final definition = content.challenges.firstWhere(
        (d) => d.id == current.dossierId,
      );
      final run = ChallengeEconomy(definition).advanceRun(
        current,
        duration,
        offline: offline,
        offlineElapsedBefore: offset,
      );
      final first = run.complete && !dossiers.completed.contains(run.dossierId);
      dossiers = dossiers.withRun(run, definition);
      if (first) {
        challengeAt[run.dossierId] = through.difference(epoch).inSeconds;
        _main(
          engine.recordDiscovery(
            main,
            'challenge',
            operationSequence: main.nextDiscoverySequence,
            contentId: run.dossierId,
          ),
        );
      }
    }
    final event = seasonEngine.advanceTo(
      season,
      through,
      offline: offline,
      offlineElapsedBefore: offset,
    );
    if (event.accepted) season = event.state;
    cursor = through;
    _evaluate();
    if (!offline &&
        jsonEncode(main.daily.availableDiscoveryKinds) !=
            jsonEncode(availableDiscoveries)) {
      _refreshDaily();
    }
  }

  void advanceTo(DateTime target, {required bool offline}) {
    if (!target.isAfter(cursor)) return;
    final from = cursor;
    final receipt = offline
        ? OfflineSettlementRequest(
            sequence: main.nextSettlementSequence,
            fromUtc: from,
            throughUtc: target,
          )
        : null;
    while (cursor.isBefore(target)) {
      final remaining = target.difference(cursor);
      final offset = cursor.difference(from);
      final chunk = Duration(hours: offlineChunkHours);
      final step =
          remaining < chunk || (offline && offset >= const Duration(hours: 72))
          ? remaining
          : chunk;
      _step(
        step,
        offline: offline,
        offset: offset,
        receipt: receipt,
        finalChunk: cursor.add(step) == target,
      );
    }
    if (offline) {
      // A returned player sees newly assigned missed-day slots only after the
      // whole absence has settled, matching the native worker's final commit.
      _refreshDaily();
      pass = passEngine.pruneAlternatives(main, pass).pass;
    }
  }

  void _resetIfUseful() {
    final minimum = main.charts < BigInt.from(50)
        ? BigInt.from(10)
        : main.charts ~/ BigInt.from(5);
    if (engine.prestigeAward(main) >= minimum &&
        (main.rechartCount == 0 ||
            main.elapsedMicros - main.lastRechartElapsedMicros >=
                BigInt.from(600000000))) {
      _main(engine.rechart(main));
      _evaluate();
    }
    if (main.charts >= BigInt.from(10) && !main.autoBuyEnabled)
      _main(engine.setAutoBuy(main, true));
    if (main.charts >= BigInt.from(10)) {
      final automaticReset =
          resetPolicy == ResetPolicy.hourlyAutomatic &&
          main.charts >= BigInt.from(100);
      _main(
        engine.saveAutomationPlan(
          main,
          AutomationPlan(
            id: 'plan.base',
            name: 'Audit hourly threshold',
            purchasePolicy: purchasePolicy == PurchasePolicy.bestPayback
                ? 'greedy'
                : 'priority',
            tierPriority: purchasePolicy == PurchasePolicy.lowestTierFirst
                ? const [0, 1, 2, 3, 4]
                : const [4, 3, 2, 1, 0],
            autoResetEnabled: automaticReset,
            minimumAdditionalCharts: main.charts ~/ BigInt.from(5),
            minimumRunSeconds: 3600,
          ),
        ),
      );
    }
  }

  void _visitActions() {
    if (contractPolicy == ContractPolicy.pursueWithSeason &&
        season.phase == SeasonPhase.archived &&
        !season.archiveActive) {
      season = seasonEngine.resumeArchive(season, cursor).state;
    }
    _refreshDaily();
    final beforeSurveys = main.surveyNotes;
    _main(engine.collectSurveys(main));
    surveyNotesEarned += main.surveyNotes - beforeSurveys;
    // Three accessible completions are mandatory chapter content; the minimal
    // policy stops there, so it is explicitly not a zero-Focus experiment.
    while (bonus != BonusPolicy.none &&
        main.focusCharges > 0 &&
        (bonus != BonusPolicy.requiredCalibrationsOnly ||
            main.completedCalibrationIds.length < 3)) {
      final next = (main.completedCalibrationIds.length % 12) + 1;
      final result = engine.completeCalibration(
        main,
        'calibration.${next.toString().padLeft(2, '0')}',
        operationSequence: main.nextDiscoverySequence,
      );
      if (!result.accepted) break;
      main = result.state;
      focusUsed++;
    }
    _evaluate();
    final unread = [
      'archive.intro',
      ...campaign.archiveIds,
    ].where((id) => !readArchives.contains(id));
    if (unread.isNotEmpty) {
      final id = unread.first;
      _main(
        engine.recordDiscovery(
          main,
          'archive',
          operationSequence: main.nextDiscoverySequence,
          contentId: id,
        ),
      );
      readArchives.add(id);
      archiveReflections++;
    }
    for (final contract in main.dailyContracts.toList()) {
      if (contractPolicy == ContractPolicy.surveysOnly ||
          (contractPolicy == ContractPolicy.oneReadyPerVisit &&
              _visitContractClaims >= 1))
        break;
      final beforeClaim = main.surveyNotes;
      var result = passEngine.claimDaily(main, pass, contract.id);
      if (!result.accepted &&
          !contract.claimed &&
          contractPolicy == ContractPolicy.pursueWithSeason) {
        // Reflection is a repeatable player command in the real client; it
        // consumes a fresh operation sequence without granting Focus or power.
        if (contract.discoveryKind == 'archive') {
          _main(
            engine.recordDiscovery(
              main,
              'archive',
              operationSequence: main.nextDiscoverySequence,
              contentId: 'archive.intro',
            ),
          );
          archiveReflections++;
          result = passEngine.claimDaily(main, pass, contract.id);
        }
        if (!result.accepted) {
          if (pass.alternatives.containsKey(contract.id)) {
            result = passEngine.claimDaily(
              main,
              pass,
              contract.id,
              alternativeSeason: season,
            );
            if (result.accepted) seasonalContractClaims++;
          } else {
            final binding = passEngine.bindEventAlternative(
              main,
              pass,
              contract.id,
              season,
            );
            if (binding.accepted) {
              pass = binding.pass;
              seasonalContractBindings++;
            }
          }
        }
      }
      if (result.accepted) {
        main = result.main;
        pass = result.pass;
        contractsClaimed++;
        _visitContractClaims++;
        contractNotesEarned += main.surveyNotes - beforeClaim;
      }
    }
    pass = passEngine.pruneAlternatives(main, pass).pass;
    _resetIfUseful();
    if (bonus == BonusPolicy.focusAndFreeSupport ||
        bonus == BonusPolicy.focusAndAdSupportFixture) {
      for (var slot = 0; slot < 6; slot++) {
        final adFixture = bonus == BonusPolicy.focusAndAdSupportFixture;
        final digest = sha256.convert(
          utf8.encode(
            'SIMULATED-RECEIPT:$seed:${main.daily.dayHighWater}:$slot',
          ),
        );
        final grant = engine.claimSupportToken(
          main,
          accountDay: main.daily.dayHighWater,
          slot: slot,
          sourceId: adFixture
              ? engine.adSupportSourceId(main, slot, digest.toString())
              : engine.briefingSourceId(main, slot),
          route: adFixture ? 'ad' : 'briefing',
        );
        if (grant.accepted) main = grant.state;
      }
      for (final token in main.support.tokens.where((t) => !t.spent).toList()) {
        final used = engine.useSupportBoost(main, token.id);
        if (used.accepted) {
          main = used.state;
          supportUsed++;
        }
      }
    }
    _evaluate();
    if (dossiers.active?.complete == true) dossiers = dossiers.leave();
    if (dossiers.active == null && campaign.restoredHarbor >= 3) {
      // Complete two of each family before the six optional dossiers.
      for (final ordinal in [1, 5, 9, 2, 6, 10, 3, 7, 11, 4, 8, 12]) {
        final definition = content.challenges[ordinal - 1];
        if (dossiers.completed.contains(definition.id)) continue;
        final before = main.surveyNotes;
        final opened = dossiers.open(main, campaign, definition);
        if (opened.accepted) {
          main = opened.main;
          dossiers = opened.dossiers;
          notesSpent += before - main.surveyNotes;
          dossiers = dossiers.withRun(
            dossiers.active!.copyWith(automatic: true),
            definition,
          );
        }
        break;
      }
    }
    if (season.phase == SeasonPhase.archived && !season.archiveActive) {
      season = seasonEngine.resumeArchive(season, cursor).state;
    }
    for (final reward in content.season.rewards.where(
      (r) => r.track == 'free',
    )) {
      final claimed = passEngine.claimFreeReward(
        main,
        pass,
        content.season.passId,
        reward.id,
      );
      if (claimed.accepted) {
        main = claimed.main;
        pass = claimed.pass;
      }
    }
    for (final milestone in content.season.milestones) {
      final claimed = seasonEngine.claimMilestone(season, milestone.id);
      if (claimed.accepted) season = claimed.state;
    }
    if (notesSpent + main.surveyNotes >= BigInt.from(1750)) {
      fullNoteBudgetSeconds ??= elapsed.inSeconds;
    }
    if (dossiers.completed.length == 12 &&
        main.surveyNotes >= BigInt.from(550)) {
      fullCollectionAffordableSeconds ??= elapsed.inSeconds;
    }
  }

  void visit({required DateTime end}) {
    visits++;
    _visitContractClaims = 0;
    _visitActions();
    while (cursor.isBefore(end)) {
      if (main.autoBuyEnabled) {
        advanceTo(end, offline: false);
      } else {
        while (true) {
          final tier = switch (purchasePolicy) {
            PurchasePolicy.bestPayback => engine.chooseAutoBuyTier(main),
            PurchasePolicy.lowestTierFirst => 0,
            PurchasePolicy.highestTierFirst => [
              4,
              3,
              2,
              1,
              0,
            ].firstWhere((tier) => engine.isUnlocked(main, tier)),
          };
          final purchase = engine.buy(main, tier, 1);
          if (!purchase.accepted) break;
          main = purchase.state;
          manualPurchases++;
        }
        _resetIfUseful();
        final next = cursor.add(const Duration(seconds: 5));
        advanceTo(next.isBefore(end) ? next : end, offline: false);
      }
    }
    _visitActions();
  }

  Map<String, dynamic> run({required int days}) {
    final end = epoch.add(Duration(days: days));
    final interval = Duration(seconds: 86400 ~/ visitsPerDay);
    var nextVisit = epoch;
    for (var day = 1; day <= days; day++) {
      final boundary = epoch.add(Duration(days: day));
      while (nextVisit.isBefore(boundary)) {
        final inBreak =
            breakStartsDay != null &&
            !nextVisit.isBefore(epoch.add(Duration(days: breakStartsDay!))) &&
            nextVisit.isBefore(
              epoch.add(Duration(days: breakStartsDay!, hours: breakHours)),
            );
        if (!inBreak) {
          advanceTo(nextVisit, offline: true);
          final visitEnd = nextVisit.add(
            Duration(minutes: visits == 0 ? 30 : 5),
          );
          visit(end: visitEnd.isBefore(end) ? visitEnd : end);
        }
        nextVisit = nextVisit.add(interval);
      }
      // Checkpoints must not split an absence: doing so would renew its cap.
      // Only record at an actual visit or the single final settlement.
      if (day == 30 || day == 90) {
        checkpoints['$day'] = summary()
          ..['measurement_cursor_utc'] = cursor.toIso8601String();
      }
    }
    advanceTo(end, offline: true);
    return summary()..['checkpoints_at_last_visit'] = checkpoints;
  }

  Map<String, dynamic> summary() => {
    'visits_per_day': visitsPerDay,
    'bonus_policy': bonus.name,
    'reset_policy': resetPolicy.name,
    'purchase_policy': purchasePolicy.name,
    'contract_policy': contractPolicy.name,
    'break_starts_day': breakStartsDay,
    'break_hours': breakHours,
    'seed': seed,
    'elapsed_seconds': elapsed.inSeconds,
    'actual_visits': visits,
    'first_reset_seconds_upper_bound': firstResetSeconds,
    'lifetime_r_micros': main.lifetimeMicros.toString(),
    'charts': main.charts.toString(),
    'counts': [...main.counts],
    'recharts': main.rechartCount,
    'notes_unspent': main.surveyNotes.toString(),
    'notes_spent_dossiers': notesSpent.toString(),
    'notes_earned': (notesSpent + main.surveyNotes).toString(),
    'notes_from_surveys': surveyNotesEarned.toString(),
    'notes_from_contracts': contractNotesEarned.toString(),
    'full_note_budget_seconds_upper_bound': fullNoteBudgetSeconds,
    'full_collection_affordable_seconds_upper_bound':
        fullCollectionAffordableSeconds,
    'optional_plan_decoration_budget_remaining': 550,
    'focus_charges_used': focusUsed,
    'free_support_tokens_used': supportUsed,
    'contracts_claimed': contractsClaimed,
    'archive_reflections': archiveReflections,
    'seasonal_contract_bindings': seasonalContractBindings,
    'seasonal_contract_claims': seasonalContractClaims,
    'chapters_completed': campaign.restoredHarbor,
    'chapter_seconds_upper_bounds': {...chapterAt},
    'dossiers_completed': dossiers.completed.toList()..sort(),
    'challenge_seconds_upper_bounds': {...challengeAt},
    'pass_level': passEngine.level(main, content.season.passId),
    'pass_claims': pass.claims.length,
    'season_badges': season.claimedMilestones.length,
    'season_lifetime_micros': season.fleet.lifetimeMicros.toString(),
    'main_serialized_bytes': utf8.encode(jsonEncode(main.toJson())).length,
    'manual_purchase_commands': manualPurchases,
  };
}
