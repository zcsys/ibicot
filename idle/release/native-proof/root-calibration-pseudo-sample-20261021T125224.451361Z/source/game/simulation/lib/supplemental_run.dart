import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_progression/decoration_purchase.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'policy_run.dart'
    show SimulationContent, BonusPolicy, PurchasePolicy, ContractPolicy;
import 'supplemental_math.dart';

enum NoteSinkOrder { campaignFirst, plansFirst, decorationsFirst }

/// Supplemental execution adapter forked from the repaired v3 policy harness.
/// Existing v3 source/reports stay immutable; all economic transitions are
/// delegated to the production packages. This adapter represents virtual play.
class SupplementalRun {
  SupplementalRun(
    this.content, {
    required this.visitsPerDay,
    required this.bonus,
    required this.resetDecision,
    this.sinkOrder = NoteSinkOrder.campaignFirst,
    DateTime? startAt,
    this.utcOffsetMinutes = 0,
    this.purchasePolicy = PurchasePolicy.bestPayback,
    this.contractPolicy = ContractPolicy.allReady,
    this.seed = 'policy-audit-01',
    this.offlineChunkHours = 4,
    this.breakStartsDay,
    this.breakHours = 0,
  }) : epoch = (startAt ?? DateTime.utc(2026, 10, 16)).toUtc() {
    cursor = epoch;
    if (![1, 3, 6].contains(visitsPerDay) || offlineChunkHours < 1)
      throw ArgumentError('Invalid visit policy.');
    main = engine
        .refreshContracts(
          GameState.initial(),
          epoch,
          accountSeed: seed,
          utcOffsetMinutes: utcOffsetMinutes,
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
  final DateTime epoch;
  final int utcOffsetMinutes;
  static const engine = TideglassEngine();
  final SimulationContent content;
  final int visitsPerDay, offlineChunkHours;
  final BonusPolicy bonus;
  final ResetDecision resetDecision;
  final NoteSinkOrder sinkOrder;
  final Set<String> decorations = {};
  final List<Map<String, dynamic>> purchases = [];
  final List<Map<String, dynamic>> resetDecisions = [];
  final List<Map<String, dynamic>> reconstruction = [];
  BigInt? _priorResetRate;
  int? _priorResetSecond;
  final List<Map<String, dynamic>> marginalSamples = [];
  final List<int> purchaseTierCounts = List.filled(5, 0);
  final Map<String, List<int>> purchasesByPeriod = {
    'day0': List.filled(5, 0),
    'days1to6': List.filled(5, 0),
    'days7to29': List.filled(5, 0),
    'days30plus': List.filled(5, 0),
  };

  void _recordPurchase(CoreEvent event) {
    final tier = event.details['tier_index'] as int;
    final quantity = event.details['quantity'] as int;
    final day = (event.elapsedMicros ~/ BigInt.from(86400000000)).toInt();
    final period = day < 1
        ? 'day0'
        : day < 7
        ? 'days1to6'
        : day < 30
        ? 'days7to29'
        : 'days30plus';
    purchaseTierCounts[tier] += quantity;
    purchasesByPeriod[period]![tier] += quantity;
  }

  final Set<int> sampledDays = {};
  BigInt planNotesSpent = BigInt.zero, decorationNotesSpent = BigInt.zero;
  int? allSinksPurchasedSeconds;
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
  late DateTime cursor;
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
    if (_priorResetRate != null &&
        engine.outputPerSecond(main).raw >= _priorResetRate!) {
      reconstruction.add({
        'reset_at_seconds': _priorResetSecond,
        'recovered_at_seconds_upper_bound': elapsed.inSeconds,
        'recovery_seconds_upper_bound': elapsed.inSeconds - _priorResetSecond!,
      });
      _priorResetRate = null;
    }
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
    for (final event in advanced.events.where((e) => e.kind == 'purchase')) {
      _recordPurchase(event);
    }
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
    final decision = resetDecision.evaluate(main);
    // Record only eligible decision opportunities, not every first-run tick.
    if (engine.prestigeAward(main) > BigInt.zero) {
      resetDecisions.add({
        'elapsed_seconds': elapsed.inSeconds,
        'charts_before': main.charts.toString(),
        ...decision.toJson(),
      });
    }
    if (decision.reset) {
      if (_priorResetRate != null) {
        reconstruction.add({
          'reset_at_seconds': _priorResetSecond,
          'superseded_without_observed_recovery': true,
        });
      }
      _priorResetRate = engine.outputPerSecond(main).raw;
      _priorResetSecond = elapsed.inSeconds;
      _main(engine.rechart(main));
      _evaluate();
    }
    if (main.charts >= BigInt.from(10) && !main.autoBuyEnabled) {
      _main(engine.setAutoBuy(main, true));
    }
    // All three strategies decide only at the same visit/action opportunities.
    // No automatic resets occur between visits, avoiding a cadence confound.
  }

  void _purchaseNotes() {
    if (dossiers.active?.complete == true) dossiers = dossiers.leave();
    final dossierOrder = [1, 5, 9, 2, 6, 10, 3, 7, 11, 4, 8, 12];
    final mandatory = dossierOrder.take(6).toList();
    final optional = dossierOrder.skip(6).toList();
    List<String> dossierItems(List<int> values) => [
      for (final n in values) 'dossier:$n',
    ];
    final plans = [for (var n = 1; n <= 5; n++) 'plan:$n'];
    final decor = [for (var n = 1; n <= 6; n++) 'decoration:$n'];
    final order = switch (sinkOrder) {
      NoteSinkOrder.campaignFirst => [
        ...dossierItems(mandatory),
        ...dossierItems(optional),
        ...plans,
        ...decor,
      ],
      NoteSinkOrder.plansFirst => [
        ...plans,
        ...dossierItems(mandatory),
        ...decor,
        ...dossierItems(optional),
      ],
      NoteSinkOrder.decorationsFirst => [
        ...decor,
        ...plans,
        ...dossierItems(mandatory),
        ...dossierItems(optional),
      ],
    };
    for (final item in order) {
      final parts = item.split(':');
      final n = int.parse(parts[1]);
      final before = main.surveyNotes;
      String id;
      if (parts[0] == 'dossier') {
        final definition = content.challenges[n - 1];
        if (dossiers.completed.contains(definition.id)) continue;
        if (dossiers.active != null) break;
        final opened = dossiers.open(main, campaign, definition);
        if (!opened.accepted) break;
        main = opened.main;
        dossiers = opened.dossiers.withRun(
          opened.dossiers.active!.copyWith(automatic: true),
          definition,
        );
        notesSpent += before - main.surveyNotes;
        id = definition.id;
      } else if (parts[0] == 'plan') {
        if (main.extraPlanSlots >= n) continue;
        final purchased = engine.buyPlanSlot(main);
        if (!purchased.accepted) break;
        main = purchased.state;
        planNotesSpent += before - main.surveyNotes;
        id = 'plan.extra.$n';
      } else {
        id = 'cosmetic.core.decoration.${n.toString().padLeft(2, '0')}';
        if (decorations.contains(id)) continue;
        final purchased = buyDecoration(main, decorations, id);
        if (!purchased.accepted) break;
        main = purchased.main;
        decorations.addAll(purchased.owned);
        decorationNotesSpent += before - main.surveyNotes;
      }
      purchases.add({
        'id': id,
        'elapsed_seconds': elapsed.inSeconds,
        'cost_notes': (before - main.surveyNotes).toString(),
        'notes_after': main.surveyNotes.toString(),
      });
      if (parts[0] == 'dossier') break;
    }
    if (dossiers.owned.length == 12 &&
        main.extraPlanSlots == 5 &&
        decorations.length == 6) {
      allSinksPurchasedSeconds ??= elapsed.inSeconds;
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
    _purchaseNotes();
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
    if (totalNotesSpent + main.surveyNotes >= BigInt.from(1750)) {
      fullNoteBudgetSeconds ??= elapsed.inSeconds;
    }
    if (dossiers.completed.length == 12 &&
        totalNotesSpent + main.surveyNotes >= BigInt.from(1750)) {
      fullCollectionAffordableSeconds ??= elapsed.inSeconds;
    }
  }

  void visit({required DateTime end}) {
    final day = elapsed.inDays;
    if ([7, 30, 60, 89].contains(day) && sampledDays.add(day)) {
      marginalSamples.add(
        marginalSnapshot(main, label: 'day$day-before-visit'),
      );
    }
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
          _recordPurchase(purchase.events.single);
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

  BigInt get totalNotesSpent =>
      notesSpent + planNotesSpent + decorationNotesSpent;

  Map<String, dynamic> summary() => {
    'visits_per_day': visitsPerDay,
    'bonus_policy': bonus.name,
    'reset_policy': resetDecision.id,
    'sink_order': sinkOrder.name,
    'start_utc': epoch.toIso8601String(),
    'utc_offset_minutes': utcOffsetMinutes,
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
    'notes_earned': (totalNotesSpent + main.surveyNotes).toString(),
    'notes_spent_plans': planNotesSpent.toString(),
    'notes_spent_decorations': decorationNotesSpent.toString(),
    'plan_slots_bought': main.extraPlanSlots,
    'decorations_bought': decorations.length,
    'all_sinks_purchased_seconds_upper_bound': allSinksPurchasedSeconds,
    'note_purchases': [...purchases],
    'reset_decisions': [...resetDecisions],
    'reconstruction_observations': [...reconstruction],
    'marginal_samples': [...marginalSamples],
    'purchase_tier_counts': [...purchaseTierCounts],
    'purchases_by_elapsed_period': {
      for (final entry in purchasesByPeriod.entries)
        entry.key: [...entry.value],
    },
    'notes_from_surveys': surveyNotesEarned.toString(),
    'notes_from_contracts': contractNotesEarned.toString(),
    'full_note_budget_seconds_upper_bound': fullNoteBudgetSeconds,
    'full_collection_affordable_seconds_upper_bound':
        fullCollectionAffordableSeconds,
    'optional_plan_decoration_budget_remaining':
        (BigInt.from(550) - planNotesSpent - decorationNotesSpent).toString(),
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
