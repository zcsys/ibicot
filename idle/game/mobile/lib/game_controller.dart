import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'story_state.dart';
import 'audio_bus.dart';
import 'bundled_content.dart';
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
    StoryProgress? initialStory,
    this.engine = const TideglassEngine(),
    bool startTicker = true,
    DateTime Function()? clock,
  }) : state = initialState ?? GameState.initial(),
       _clock = clock ?? DateTime.now,
       _persist = onPersist,
       _persistSession = onSessionPersist,
       story = initialStory ?? StoryProgress() {
    if (story.contentDigest != null &&
        story.contentDigest != bundledManifestDigest) {
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
    return _storyChanged(
      'Your harbor appearance is saved. Production is unchanged.',
    );
  }

  List<String> get availableDiscoveries => [
    'archive',
    if (story.campaign.restoredHarbor >= 3) 'challenge',
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
      throw StateError('Time settlement rejected: ${advanced.reason}');
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
          throw StateError('Challenge discovery rejected: ${discovery.reason}');
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
        throw StateError('Season settlement rejected: ${seasonal.reason}');
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
        replayError =
            'Your time away could not be gathered. Your prior progress is safe; try again.';
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
      'A new ${TideglassEngine.producerNames[tier]} joins your harbor.',
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
      'A new chart. A brighter beginning.',
      cue: TideCue.rechart,
    );
  }

  bool setAutoBuy(bool enabled) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.setAutoBuy(state, enabled),
      enabled
          ? 'Your fleet is building automatically.'
          : 'Automatic building paused.',
    );
  }

  bool activateFocus() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.activateFocus(state),
      'Your constellation is focused for ten more minutes.',
    );
  }

  bool collectSurveys() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.collectSurveys(state),
      'Survey Notes added to your archive.',
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
      'A constellation recorded. Ten minutes of Focus queued.',
      cue: TideCue.calibration,
    );
  }

  bool claimContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.pass != null) {
      return _acceptPass(
        passEngine!.claimDaily(state, story.pass!, id),
        'Contract complete: 10 Notes and 250 pass XP.',
      );
    }
    return _accept(
      engine.claimContract(state, id),
      'Contract complete: 10 Notes and 250 pass XP.',
    );
  }

  bool rerollContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.rerollContract(state, id),
      'A new objective, with the original difficulty snapshot.',
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
      'The keeper’s account is recorded in your logbook.',
    );
  }

  bool savePlan(AutomationPlan plan) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.saveAutomationPlan(state, plan),
      'Your crew’s plan is saved.',
    );
  }

  bool selectPlan(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.selectAutomationPlan(state, id),
      'The crew will follow the selected plan.',
    );
  }

  bool buyPlanSlot() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.buyPlanSlot(state),
      'An additional plan slot is ready.',
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
      'One Support token is ready for this account day.',
    );
  }

  bool useSupportBoost(String tokenId) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.useSupportBoost(state, tokenId),
      'Twenty minutes of Support queued at +25%.',
    );
  }

  bool claimSalvage(String tokenId, String cacheId) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    return _accept(
      engine.claimSalvageCache(state, tokenId, cacheId),
      'A genuine five-minute salvage slice has been matched.',
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
      'The seasonal fleet grows.',
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
      'Seasonal plan updated.',
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
          ? 'The archived fleet continues at its own pace.'
          : 'Archived fleet paused.',
    );
  }

  bool claimSeasonMilestone(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptSeason(
      seasonEngine!.claimMilestone(story.season!, id),
      'A seasonal badge has been recorded.',
    );
  }

  bool selectSeasonPass() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptPass(
      passEngine!.selectPass(state, story.pass!, story.season!),
      'Future contract XP goes to this selected pass.',
    );
  }

  bool bindSeasonContract(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.season == null) return false;
    return _acceptPass(
      passEngine!.bindEventAlternative(state, story.pass!, id, story.season!),
      'This contract can also be completed with new seasonal production.',
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
      'The shared contract grants 10 Notes and 250 XP once.',
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
      'An earned pass reward is added to your collection.',
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
    return _storyChanged(
      'A separate fleet is ready. Your harbor continues its work.',
    );
  }

  bool leaveDossier() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (story.dossiers.active == null) return false;
    story = story.copyWith(dossiers: story.dossiers.leave());
    return _storyChanged(
      'Returned to the harbor. Dossier ownership and completion are kept.',
    );
  }

  bool restartDossier() {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    final active = story.dossiers.active;
    if (active == null || catalogue == null) return false;
    story = story.copyWith(
      dossiers: story.dossiers.restart(catalogue!.dossier(active.dossierId)),
    );
    return _storyChanged('A fresh challenge fleet. Replays cost no Notes.');
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
    return _storyChanged('A vessel joins the challenge fleet.');
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
    return _storyChanged('Challenge plan updated.');
  }

  bool buyDecoration(String id) {
    if (_suspended || replaying || replayError != null) return false;
    _advanceTo(_clock());
    if (!RegExp(r'^cosmetic\.core\.decoration\.0[1-6]$').hasMatch(id) ||
        story.decorations.contains(id) ||
        state.surveyNotes < BigInt.from(50)) {
      return false;
    }
    state = state.copyWith(
      surveyNotes: state.surveyNotes - BigInt.from(50),
      revision: state.revision + 1,
    );
    story = story.copyWith(
      decorations: {...story.decorations, id},
      equippedDecoration: id,
    );
    return _storyChanged(
      'A new decoration for your harbor. Production is unchanged.',
    );
  }

  bool equipDecoration(String id) {
    if (_suspended || replaying || replayError != null) return false;
    if (!story.decorations.contains(id)) return false;
    story = story.copyWith(equippedDecoration: id);
    return _storyChanged('Harbor decoration changed.');
  }

  bool unequipDecoration() {
    if (_suspended || replaying || replayError != null) return false;
    story = story.copyWith(clearDecoration: true);
    return _storyChanged('The original harbor appearance is restored.');
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
        saveError =
            'Your harbor is still open, but its latest progress could not be written. ${error.runtimeType}';
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
