import 'presentation.dart';
import 'strings.dart';
import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'package:tideglass_progression/decoration_purchase.dart' as decoration;
import 'story_state.dart';
import 'audio_bus.dart';
import 'bundled_content.dart';
import 'content_compatibility.dart';
import 'offline_replay.dart';
import 'cosmetics.dart';

typedef PersistGame =
    Future<void> Function(GameState state, DateTime settledThrough);

typedef PersistSession =
    Future<void> Function(
      GameState state,
      StoryProgress story,
      DateTime settledThrough,
    );

enum PurchaseMode { single, milestone, maximum }

class ReturnReport {
  const ReturnReport({
    required this.absence,
    required this.earnedMicros,
    required this.automated,
  });
  final Duration absence;
  final BigInt earnedMicros;
  final bool automated;
  Duration get fullRate => Duration(seconds: absence.inSeconds.clamp(0, 86400));
  Duration get quarterRate =>
      Duration(seconds: (absence.inSeconds - 86400).clamp(0, 172800));
  Duration get uncredited =>
      Duration(seconds: (absence.inSeconds - 259200).clamp(0, 3153600000));
}

/// Presentation coordinator. Commands and all awards remain in the pure core.
/// Persisted snapshots include their real settlement boundary, so opening a
/// return dialog or retrying a write can never replay the same time interval.
class GameController extends ChangeNotifier {
  GameController({
    GameState? initialState,
    DateTime? settledThrough,
    PersistGame? onPersist,
    PersistSession? onSessionPersist,
    this.catalogue,
    this.audio,
    this.verifiedPaidCosmetics,
    StoryProgress? initialStory,
    this.engine = const TideglassEngine(),
    bool startTicker = true,
    DateTime Function()? clock,
  }) : state = initialState ?? GameState.initial(),
       _clock = clock ?? DateTime.now,
       _persist = onPersist,
       _persistSession = onSessionPersist,
       story = initialStory ?? StoryProgress() {
    if (!acceptsStoryContentDigest(story.contentDigest)) {
      throw const FormatException('Pinned story content differs.');
    }
    if (catalogue != null) {
      story = story.copyWith(contentDigest: bundledManifestDigest);
    }
    final active = story.dossiers.active;
    if (active != null) {
      if (catalogue == null) {
        throw const FormatException('A dossier needs its pinned catalogue.');
      }
      ChallengeEconomy(
        catalogue!.dossier(active.dossierId),
      ).validateRun(active);
    }
    _lastSettled = settledThrough ?? _clock();
    if (state.support.receiptCursorMigrationRequired) {
      if (settledThrough == null) {
        throw const FormatException(
          'Legacy receipt migration needs the saved time cursor.',
        );
      }
      final migrated = engine.initializeReceiptCursor(
        state,
        settledThrough.toUtc(),
      );
      if (!migrated.accepted) {
        throw const FormatException(
          'Legacy receipt cursor could not be established.',
        );
      }
      state = migrated.state;
    }
    if (state.support.activeSettlementId != null) {
      throw const FormatException(
        'An unfinished imported replay requires its recorded continuation before opening this client.',
      );
    }
    if (story.season != null) {
      if (catalogue == null ||
          settledThrough == null ||
          story.season!.settledThroughMicros !=
              BigInt.from(_lastSettled.toUtc().microsecondsSinceEpoch)) {
        throw const FormatException(
          'Main and seasonal snapshots must share one settlement cursor.',
        );
      }
      seasonEngine!.validate(story.season!);
      passEngine!.validate(story.pass!, main: state);
    }
    if (settledThrough != null) _advanceTo(_clock(), offline: true);
    _evaluateCampaign();
    _refreshDaily(_lastSettled);
    if (catalogue != null && story.season == null) {
      story = story.copyWith(
        season: SeasonState.initial(
          catalogue!.seasonDefinition,
          catalogue!.seasonSchedule,
          _lastSettled.toUtc(),
          runId:
              'season:${state.daily.accountSeed}:${_lastSettled.toUtc().microsecondsSinceEpoch}',
        ),
        pass: PassState.initial([catalogue!.seasonDefinition]),
      );
    }
    if (startTicker) {
      _ticker = Timer.periodic(
        const Duration(milliseconds: 250),
        (_) => tick(),
      );
    }
  }
  final TideglassEngine engine;
  final TideAudioBus? audio;

  /// Independent account authority supplies only paid appearance identities.
  /// This projection is never persisted in a gameplay save or used for output.
  final Iterable<String> Function()? verifiedPaidCosmetics;
  final StoryCatalogue? catalogue;
  StoryProgress story;
  SeasonEngine? get seasonEngine =>
      catalogue == null ? null : SeasonEngine(catalogue!.seasonDefinition);
  PassEngine? get passEngine =>
      catalogue == null ? null : PassEngine([catalogue!.seasonDefinition]);
  final PersistSession? _persistSession;
  GameState state;
  final DateTime Function() _clock;
  final PersistGame? _persist;
  late DateTime _lastSettled;
  Timer? _ticker;
  bool _suspended = false;
  bool _resumeWanted = true;
  bool replaying = false;
  ReplayProgress? replayProgress;
  String? replayError;
  Future<void>? _resumeTask;
  bool _disposed = false;
  int _ticksSinceSave = 0;
  Future<void> _saveTail = Future.value();
  ReturnReport? returnReport;
  String? saveError;
  bool saving = false;
  bool get hasPersistence => _persist != null || _persistSession != null;
  DateTime get settledThrough => _lastSettled;
  PurchaseMode purchaseMode = PurchaseMode.single;
  String? lastAction;

  Set<String> get ownedCosmetics => {
    ...story.campaign.cosmeticIds,
    ...story.decorations,
    if (story.pass != null) ...passEngine!.cosmeticIds(story.pass!),
    ...?verifiedPaidCosmetics?.call().where(
      (id) => cosmeticCatalogue.any((item) => item.id == id && item.paid),
    ),
  };
  String? get visibleAppearance =>
      ownedCosmetics.contains(story.equippedAppearance)
      ? story.equippedAppearance
      : null;

  bool equipCosmetic(String? id) {
    if (_suspended || replaying || replayError != null) return false;
    if (id != null) {
      if (!ownedCosmetics.contains(id)) return false;
      if (cosmeticById(id).source == CosmeticSource.decoration) {
        return equipDecoration(id);
      }
    }
    story = story.copyWith(equippedAppearance: id, clearAppearance: id == null);
    return _storyChanged(UiEnglish.gameYourHarborAppearanceIsSavedProductionIs);
  }

  List<String> get availableDiscoveries => [
    'archive',
    if (story.campaign.restoredHarbor >= 3 &&
        catalogue?.dossiers.any(
              (d) => !story.dossiers.completed.contains(d.id),
            ) ==
            true)
      'challenge',
    if (state.focusCharges > 0 || state.completedCalibrationIds.isNotEmpty)
      'calibration',
  ];
  void _refreshDaily(DateTime now) {
    // A reversed device clock must not move the daily calendar behind the
    // already accepted save cursor. Production waits until time catches up.
    final calendarNow = now.isBefore(_lastSettled) ? _lastSettled : now;
    String? seed;
    if (!state.daily.initialized) {
      final random = Random.secure();
      seed = List.generate(
        16,
        (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
      ).join();
    }
    state = engine
        .refreshContracts(
          state,
          calendarNow.toUtc(),
          accountSeed: seed,
          utcOffsetMinutes: state.daily.initialized
              ? null
              : now.timeZoneOffset.inMinutes,
          availableDiscoveryKinds: availableDiscoveries,
        )
        .state;
  }

  void tick() {
    if (_suspended || _disposed) return;
    _advanceTo(_clock());
    if (++_ticksSinceSave >= 20) {
      _ticksSinceSave = 0;
      unawaited(save());
    }
    notifyListeners();
  }

  void _advanceTo(DateTime now, {bool offline = false}) {
    final elapsed = now.difference(_lastSettled);
    if (elapsed.isNegative || elapsed == Duration.zero) return;
    final previous = state;
    final advanced = engine.advance(
      state,
      elapsed,
      offline: offline,
      offlineSettlement: offline
          ? OfflineSettlementRequest(
              sequence: state.nextSettlementSequence,
              fromUtc: _lastSettled.toUtc(),
              throughUtc: now.toUtc(),
            )
          : null,
    );
    if (!advanced.accepted) {
      throw StateError(
        UiEnglish.gameTimeSettlementRejectedAdvancedReason(advanced.reason),
      );
    }
    var nextState = advanced.state;
    var nextStory = story;
    final active = nextStory.dossiers.active;
    if (active != null && catalogue != null) {
      final definition = catalogue!.dossier(active.dossierId);
      final next = ChallengeEconomy(
        definition,
      ).advanceRun(active, elapsed, offline: offline);
      final firstCompletion =
          next.complete &&
          !nextStory.dossiers.completed.contains(next.dossierId);
      nextStory = nextStory.copyWith(
        dossiers: nextStory.dossiers.withRun(next, definition),
      );
      if (firstCompletion) {
        final discovery = engine.recordDiscovery(
          nextState,
          'challenge',
          operationSequence: nextState.nextDiscoverySequence,
          contentId: next.dossierId,
        );
        if (!discovery.accepted) {
          throw StateError(
            UiEnglish.gameChallengeDiscoveryRejectedDiscoveryReason(
              discovery.reason,
            ),
          );
        }
        nextState = discovery.state;
      }
    }
    if (nextStory.season != null) {
      final seasonal = seasonEngine!.advanceTo(
        nextStory.season!,
        now.toUtc(),
        offline: offline,
      );
      if (!seasonal.accepted) {
        throw StateError(
          UiEnglish.gameSeasonSettlementRejectedSeasonalReason(seasonal.reason),
        );
      }
      nextStory = nextStory.copyWith(season: seasonal.state);
    }
    if (catalogue != null) {
      nextStory = nextStory.copyWith(
        campaign: catalogue!.campaign.evaluate(
          nextStory.campaign,
          _factsFor(nextState, nextStory),
        ),
      );
    }
    if (nextStory.pass != null) {
      nextStory = nextStory.copyWith(
        pass: passEngine!.pruneAlternatives(nextState, nextStory.pass!).pass,
      );
    }
    // Publish every partition together only after all timelines succeed.
    state = nextState;
    story = nextStory;
    _lastSettled = now;
    if (offline && state.daily.initialized) _refreshDaily(now);
    _refreshDiscoveryAvailability();
    if (offline && elapsed >= const Duration(seconds: 60)) {
      returnReport = ReturnReport(
        absence: elapsed,
        earnedMicros: state.lifetimeMicros - previous.lifetimeMicros,
        automated: previous.autoBuyEnabled,
      );
    }
  }

  void suspend() {
    _resumeWanted = false;
    if (_disposed || _suspended) return;
    _advanceTo(_clock());
    _suspended = true;
    unawaited(save());
  }

  void resume() {
    _resumeWanted = true;
    if (_disposed || !_suspended || replaying) return;
    _advanceTo(_clock(), offline: true);
    _suspended = false;
    unawaited(save());
    notifyListeners();
  }

  Future<void> resumeWithProgress() {
    _resumeWanted = true;
    if (_disposed) return Future.value();
    if (_resumeTask != null) return _resumeTask!;
    if (!_suspended) return Future.value();
    if (catalogue == null) {
      resume();
      return Future.value();
    }
    final task = _resumeInWorker();
    _resumeTask = task.whenComplete(() => _resumeTask = null);
    return _resumeTask!;
  }

  /// Wait for an existing worker without starting another return or changing
  /// whether the player intends to remain in the background.
  Future<void> waitForPendingReplay() => _resumeTask ?? Future.value();

  Future<void> _resumeInWorker() async {
    replaying = true;
    replayProgress = null;
    replayError = null;
    notifyListeners();
    final before = state;
    final from = _lastSettled;
    final target = _clock();
    try {
      final result = await replayOfflineSession(
        main: before,
        story: story,
        catalogue: catalogue!,
        settledThrough: from,
        now: target,
        onProgress: (value) {
          if (!_disposed) {
            replayProgress = value;
            notifyListeners();
          }
        },
      );
      if (_disposed) return;
      state = result.main;
      story = result.story;
      _lastSettled = result.settledThrough;
      _suspended = !_resumeWanted;
      if (target.difference(from) >= const Duration(minutes: 1)) {
        returnReport = ReturnReport(
          absence: target.difference(from),
          earnedMicros: state.lifetimeMicros - before.lifetimeMicros,
          automated: before.autoBuyEnabled,
        );
      }
      await save();
    } catch (_) {
      if (!_disposed) {
        replayError = UiEnglish.gameYourTimeAwayCouldNotBeGathered;
      }
    } finally {
      replaying = false;
      if (!_disposed) notifyListeners();
    }
  }

  void acknowledgeReturn() {
    returnReport = null;
    notifyListeners();
  }

  void selectPurchaseMode(PurchaseMode value) {
    purchaseMode = value;
    notifyListeners();
  }

  int quantityFor(int tier) => switch (purchaseMode) {
    PurchaseMode.single => 1,
    PurchaseMode.milestone => engine.nextMilestoneQuantity(state, tier),
    PurchaseMode.maximum => engine.maximumAffordable(state, tier),
  };
  BigInt priceFor(int tier) {
    final quantity = quantityFor(tier);
    return quantity == 0
        ? engine.priceMicros(tier, state.counts[tier])
        : engine.bulkPriceMicros(tier, state.counts[tier], quantity);
  }

  bool canBuy(int tier) =>
      engine.isUnlocked(state, tier) &&
      quantityFor(tier) > 0 &&
      state.walletMicros >= priceFor(tier);
  bool buy(int tier) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final result = purchaseMode == PurchaseMode.maximum
        ? engine.buyMax(state, tier)
        : engine.buy(state, tier, quantityFor(tier));
    return _accept(
      result,
      UiEnglish.gameANewTideglassEngineProducerNamesTierJoinsYour(
        Presentation.authored((UiEnglish.producerNames[tier]).toString()),
      ),
      cue: result.state.counts[tier] ~/ 25 > state.counts[tier] ~/ 25
          ? TideCue.milestone
          : TideCue.purchase,
    );
  }

  bool rechart() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.rechart(state),
      UiEnglish.gameANewChartABrighterBeginning,
      cue: TideCue.rechart,
    );
  }

  bool setAutoBuy(bool enabled) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.setAutoBuy(state, enabled),
      enabled
          ? UiEnglish.gameYourFleetIsBuildingAutomatically
          : UiEnglish.gameAutomaticBuildingPaused,
    );
  }

  bool activateFocus() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.activateFocus(state),
      UiEnglish.gameYourConstellationIsFocusedForTenMore,
    );
  }

  bool collectSurveys() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.collectSurveys(state),
      UiEnglish.gameSurveyNotesAddedToYourArchive,
      cue: TideCue.survey,
    );
  }

  bool completeCalibration(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.completeCalibration(
        state,
        id,
        operationSequence: state.nextDiscoverySequence,
      ),
      UiEnglish.gameAConstellationRecordedTenMinutesOfFocus,
      cue: TideCue.calibration,
    );
  }

  bool claimContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.pass != null) {
      return _acceptPass(
        passEngine!.claimDaily(state, story.pass!, id),
        UiEnglish.gameContractCompleteNotesAndPassXP,
      );
    }
    return _accept(
      engine.claimContract(state, id),
      UiEnglish.gameContractCompleteNotesAndPassXP2,
    );
  }

  bool rerollContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.rerollContract(state, id),
      UiEnglish.gameANewObjectiveWithTheOriginalDifficulty,
    );
  }

  bool readArchive(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (id != 'archive.intro' &&
        (!story.campaign.archiveIds.contains(id) ||
            !(catalogue?.archive.any((entry) => entry['id'] == id) ?? false))) {
      return false;
    }
    return _accept(
      engine.recordDiscovery(
        state,
        'archive',
        operationSequence: state.nextDiscoverySequence,
        contentId: id,
      ),
      UiEnglish.gameTheKeeperSAccountIsRecordedIn,
    );
  }

  bool savePlan(AutomationPlan plan) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.saveAutomationPlan(state, plan),
      UiEnglish.gameYourCrewSPlanIsSaved,
    );
  }

  bool selectPlan(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.selectAutomationPlan(state, id),
      UiEnglish.gameTheCrewWillFollowTheSelectedPlan,
    );
  }

  bool buyPlanSlot() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.buyPlanSlot(state),
      UiEnglish.gameAnAdditionalPlanSlotIsReady,
    );
  }

  bool completeCrewBriefing(int slot) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final day = state.daily.dayHighWater;
    return _accept(
      engine.claimSupportToken(
        state,
        accountDay: day,
        slot: slot,
        sourceId: 'briefing:${state.daily.accountSeed}:$day:$slot',
      ),
      UiEnglish.gameOneSupportTokenIsReadyForThis,
    );
  }

  /// Called only by the authenticated Support adapter. A source label alone
  /// is not proof: the adapter checks the service session and response first.
  bool acceptVerifiedSupportReceipt({
    required int day,
    required int slot,
    required String sourceId,
    required String route,
  }) {
    if (_disposed || _suspended || replaying || replayError != null) {
      return false;
    }
    _advanceTo(_clock());
    return _accept(
      engine.claimSupportToken(
        state,
        accountDay: day,
        slot: slot,
        sourceId: sourceId,
        route: route,
      ),
      UiEnglish.gameOneVerifiedSupportTokenIsReadyFor,
    );
  }

  bool useSupportBoost(String tokenId) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.useSupportBoost(state, tokenId),
      UiEnglish.gameTwentyMinutesOfSupportQueuedAt,
    );
  }

  bool claimSalvage(String tokenId, String cacheId) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.claimSalvageCache(state, tokenId, cacheId),
      UiEnglish.gameAGenuineFiveMinuteSalvageSliceHas,
    );
  }

  bool buyInSeason(int tier, {bool maximum = false}) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final season = story.season;
    if (season == null) return false;
    final quantity = maximum
        ? seasonEngine!.maximumAffordable(season, tier)
        : 1;
    if (quantity == 0) return false;
    return _acceptSeason(
      seasonEngine!.purchase(season, tier, quantity),
      UiEnglish.gameTheSeasonalFleetGrows,
    );
  }

  bool setSeasonPlan({
    bool? automatic,
    SeasonPolicy? policy,
    List<int>? priority,
  }) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final season = story.season;
    if (season == null) return false;
    return _acceptSeason(
      seasonEngine!.configurePolicy(
        season,
        automatic: automatic ?? season.automatic,
        policy: policy ?? season.policy,
        priority: priority ?? season.priority,
      ),
      UiEnglish.gameSeasonalPlanUpdated,
    );
  }

  bool setSeasonArchiveActive(bool active) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final season = story.season;
    if (season == null) return false;
    return _acceptSeason(
      active
          ? seasonEngine!.resumeArchive(season, _lastSettled.toUtc())
          : seasonEngine!.pauseArchive(season, _lastSettled.toUtc()),
      active
          ? UiEnglish.gameTheArchivedFleetContinuesAtItsOwn
          : UiEnglish.gameArchivedFleetPaused,
    );
  }

  bool claimSeasonMilestone(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptSeason(
      seasonEngine!.claimMilestone(story.season!, id),
      UiEnglish.gameASeasonalBadgeHasBeenRecorded,
    );
  }

  bool selectSeasonPass() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptPass(
      passEngine!.selectPass(state, story.pass!, story.season!),
      UiEnglish.gameFutureContractXPGoesToThisSelected,
    );
  }

  bool bindSeasonContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptPass(
      passEngine!.bindEventAlternative(state, story.pass!, id, story.season!),
      UiEnglish.gameThisContractCanAlsoBeCompletedWith,
    );
  }

  BigInt seasonContractProgress(String id) {
    final binding = story.pass?.alternatives[id];
    if (binding == null || story.season == null) return BigInt.zero;
    final value = story.season!.fleet.lifetimeMicros - binding.baselineMicros;
    return value < BigInt.zero
        ? BigInt.zero
        : value > binding.targetMicros
        ? binding.targetMicros
        : value;
  }

  bool claimSeasonContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptPass(
      passEngine!.claimDaily(
        state,
        story.pass!,
        id,
        alternativeSeason: story.season!,
      ),
      UiEnglish.gameTheSharedContractGrantsNotesAndXP,
    );
  }

  bool claimFreePassReward(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.pass == null) return false;
    return _acceptPass(
      passEngine!.claimFreeReward(
        state,
        story.pass!,
        catalogue!.seasonDefinition.passId,
        id,
      ),
      UiEnglish.gameAnEarnedPassRewardIsAddedTo,
    );
  }

  bool _acceptSeason(SeasonResult result, String message) {
    if (!result.accepted) return false;
    story = story.copyWith(season: result.state);
    return _storyChanged(message);
  }

  bool _acceptPass(PassTransition result, String message) {
    if (!result.accepted) return false;
    state = result.main;
    story = story.copyWith(pass: result.pass);
    return _storyChanged(message);
  }

  ProgressFacts get progressFacts => _factsFor(state, story);
  ProgressFacts _factsFor(GameState main, StoryProgress progress) =>
      ProgressFacts(
        main: main,
        recharts: main.rechartCount,
        surveysCollected: main.surveysCollectedTotal > BigInt.from(1 << 30)
            ? 1 << 30
            : main.surveysCollectedTotal.toInt(),
        calibrations: main.completedCalibrationIds,
        completedChallenges: progress.dossiers.completed,
      );

  void _evaluateCampaign() {
    if (catalogue == null) return;
    story = story.copyWith(
      campaign: catalogue!.campaign.evaluate(story.campaign, progressFacts),
    );
    _refreshDiscoveryAvailability();
  }

  void _refreshDiscoveryAvailability() {
    if (state.daily.initialized &&
        !listEquals(
          state.daily.availableDiscoveryKinds,
          availableDiscoveries,
        )) {
      // Existing goals remain frozen; only newly assigned or rerolled slots use
      // the now-available interactions. Calendar time follows settled work.
      _refreshDaily(_lastSettled);
    }
  }

  void _settleChallenge(ChallengeRun run, ChallengeDefinition definition) {
    final firstCompletion =
        run.complete && !story.dossiers.completed.contains(run.dossierId);
    story = story.copyWith(dossiers: story.dossiers.withRun(run, definition));
    if (firstCompletion) {
      state = engine
          .recordDiscovery(
            state,
            'challenge',
            operationSequence: state.nextDiscoverySequence,
            contentId: run.dossierId,
          )
          .state;
    }
  }

  bool openDossier(String id, {bool replaceActive = false}) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (catalogue == null) return false;
    final result = story.dossiers.open(
      state,
      story.campaign,
      catalogue!.dossier(id),
      replaceActive: replaceActive,
    );
    if (!result.accepted) {
      lastAction = result.reason;
      return false;
    }
    state = result.main;
    story = story.copyWith(dossiers: result.dossiers);
    return _storyChanged(UiEnglish.gameASeparateFleetIsReadyYourHarbor);
  }

  bool leaveDossier() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.dossiers.active == null) return false;
    story = story.copyWith(dossiers: story.dossiers.leave());
    return _storyChanged(UiEnglish.gameReturnedToTheHarborDossierOwnershipAnd);
  }

  bool restartDossier() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final active = story.dossiers.active;
    if (active == null || catalogue == null) return false;
    story = story.copyWith(
      dossiers: story.dossiers.restart(catalogue!.dossier(active.dossierId)),
    );
    return _storyChanged(UiEnglish.gameAFreshChallengeFleetReplaysCostNo);
  }

  bool buyInDossier(int tier) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final active = story.dossiers.active;
    if (active == null || catalogue == null) return false;
    final definition = catalogue!.dossier(active.dossierId);
    final next = ChallengeEconomy(definition).purchase(active, tier, 1);
    if (identical(next, active)) return false;
    _settleChallenge(next, definition);
    return _storyChanged(UiEnglish.gameAVesselJoinsTheChallengeFleet);
  }

  bool setDossierPlan({
    bool? automatic,
    ChallengePolicy? policy,
    List<int>? priority,
  }) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final active = story.dossiers.active;
    if (active == null || catalogue == null) return false;
    final definition = catalogue!.dossier(active.dossierId);
    if (definition.automaticOnly && automatic == false) return false;
    _settleChallenge(
      active.copyWith(automatic: automatic, policy: policy, priority: priority),
      definition,
    );
    return _storyChanged(UiEnglish.gameChallengePlanUpdated);
  }

  bool buyDecoration(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final purchase = decoration.buyDecoration(state, story.decorations, id);
    if (!purchase.accepted) return false;
    state = purchase.main;
    story = story.copyWith(decorations: purchase.owned, equippedDecoration: id);
    return _storyChanged(UiEnglish.gameANewDecorationForYourHarborProduction);
  }

  bool equipDecoration(String id) {
    if (_suspended || replaying || replayError != null) return false;
    if (!story.decorations.contains(id)) return false;
    story = story.copyWith(equippedDecoration: id);
    return _storyChanged(UiEnglish.gameHarborDecorationChanged);
  }

  bool unequipDecoration() {
    if (_suspended || replaying || replayError != null) return false;
    story = story.copyWith(clearDecoration: true);
    return _storyChanged(UiEnglish.gameTheOriginalHarborAppearanceIsRestored);
  }

  bool _storyChanged(String message) {
    _evaluateCampaign();
    if (audio != null) unawaited(audio!.playCue(TideCue.panel));
    lastAction = message;
    unawaited(save());
    notifyListeners();
    return true;
  }

  bool _accept(
    TransitionResult result,
    String message, {
    TideCue cue = TideCue.claim,
  }) {
    if (!result.accepted) return false;
    state = result.state;
    if (story.pass != null) {
      story = story.copyWith(
        pass: passEngine!.pruneAlternatives(state, story.pass!).pass,
      );
    }
    if (audio != null) unawaited(audio!.playCue(cue));
    _evaluateCampaign();
    lastAction = message;
    unawaited(save());
    notifyListeners();
    return true;
  }

  Future<void> save() {
    if (!hasPersistence) return Future.value();
    final snapshot = state;
    final storySnapshot = story;
    final boundary = _lastSettled;
    _saveTail = _saveTail.then((_) async {
      if (!_disposed) {
        saving = true;
        notifyListeners();
      }
      try {
        if (_persistSession != null) {
          await _persistSession(snapshot, storySnapshot, boundary);
        } else {
          await _persist!(snapshot, boundary);
        }
        saveError = null;
      } catch (error) {
        saveError = UiEnglish.gameYourHarborIsStillOpenButIts(
          error.runtimeType,
        );
      } finally {
        saving = false;
        if (!_disposed) notifyListeners();
      }
    });
    return _saveTail;
  }

  @override
  void dispose() {
    _disposed = true;
    _ticker?.cancel();
    super.dispose();
  }
}
