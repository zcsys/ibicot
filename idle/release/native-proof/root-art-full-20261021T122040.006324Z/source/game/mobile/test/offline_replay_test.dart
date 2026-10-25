import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/offline_replay.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  for (final hours in [24, 72, 120]) {
    test(
      'worker $hours-hour replay preserves all three fleets and one absence cap',
      () async {
        final initial = GameController(
          catalogue: catalogue,
          initialState: GameState.initial().copyWith(
            surveyNotes: BigInt.from(100),
          ),
          initialStory: StoryProgress(
            campaign: CampaignProgress(
              completed: {'chapter.01', 'chapter.02', 'chapter.03'},
            ),
          ),
          startTicker: false,
          clock: () => epoch,
        );
        addTearDown(initial.dispose);
        initial.openDossier('challenge.05');
        initial.setDossierPlan(automatic: true);
        initial.setSeasonPlan(automatic: true);
        final before = jsonEncode(initial.state.toJson());
        final end = epoch.add(Duration(hours: hours));
        final reference = GameController(
          initialState: initial.state,
          initialStory: initial.story,
          catalogue: catalogue,
          settledThrough: epoch,
          clock: () => end,
          startTicker: false,
        );
        addTearDown(reference.dispose);
        final progress = <ReplayProgress>[];
        final result = await replayOfflineSession(
          main: initial.state,
          story: initial.story,
          catalogue: catalogue,
          settledThrough: epoch,
          now: end,
          chunk: const Duration(minutes: 37),
          onProgress: progress.add,
        );
        expect(jsonEncode(initial.state.toJson()), before);
        expect(result.settledThrough, end);
        expect(result.main.walletMicros, reference.state.walletMicros);
        expect(result.main.lifetimeMicros, reference.state.lifetimeMicros);
        expect(result.main.counts, reference.state.counts);
        expect(result.main.earningRemainder, reference.state.earningRemainder);
        expect(result.main.support.toJson(), reference.state.support.toJson());
        expect(result.main.completedSurveys, reference.state.completedSurveys);
        expect(result.main.focusCharges, reference.state.focusCharges);
        expect(result.story.season!.toJson(), reference.story.season!.toJson());
        expect(
          result.story.dossiers.active!.fleet.counts,
          reference.story.dossiers.active!.fleet.counts,
        );
        expect(
          result.story.dossiers.active!.fleet.walletMicros,
          reference.story.dossiers.active!.fleet.walletMicros,
        );
        expect(
          result.story.dossiers.completed,
          reference.story.dossiers.completed,
        );
        expect(progress.first.fraction, 0);
        expect(progress.last.fraction, 1);
        for (var i = 1; i < progress.length; i++) {
          expect(
            progress[i].fraction,
            greaterThanOrEqualTo(progress[i - 1].fraction),
          );
        }
      },
    );
  }

  test(
    'typed pending replay resumes the recorded interval without earning it twice',
    () async {
      final initial = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
      );
      addTearDown(initial.dispose);
      final end = epoch.add(const Duration(hours: 2));
      final request = OfflineSettlementRequest(
        sequence: initial.state.nextSettlementSequence,
        fromUtc: epoch,
        throughUtc: end,
      );
      final partial = const TideglassEngine()
          .advance(
            initial.state,
            const Duration(minutes: 37),
            offline: true,
            offlineSettlement: request,
            finalizeOfflineSettlement: false,
          )
          .state;
      final cursor = epoch.add(const Duration(minutes: 37));
      final story = initial.story.copyWith(
        season: SeasonEngine(
          catalogue.seasonDefinition,
        ).advanceTo(initial.story.season!, cursor, offline: true).state,
      );
      final result = await replayOfflineSession(
        main: partial,
        story: story,
        catalogue: catalogue,
        settledThrough: cursor,
        now: end,
        chunk: const Duration(minutes: 11),
      );
      final full = await replayOfflineSession(
        main: initial.state,
        story: initial.story,
        catalogue: catalogue,
        settledThrough: epoch,
        now: end,
      );
      expect(result.main.walletMicros, full.main.walletMicros);
      expect(result.main.lifetimeMicros, full.main.lifetimeMicros);
      expect(result.main.support.toJson(), full.main.support.toJson());
      expect(result.story.season!.toJson(), full.story.season!.toJson());
      expect(result.main.support.activeSettlementId, isNull);
    },
  );

  test(
    'background resume publishes one complete snapshot and gates interaction',
    () async {
      var now = epoch;
      final snapshots = <ReplayedSession>[];
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => now,
        onSessionPersist: (main, story, cursor) async {
          snapshots.add(ReplayedSession(main, story, cursor));
        },
      );
      addTearDown(game.dispose);
      game.suspend();
      await game.save();
      snapshots.clear();
      now = epoch.add(const Duration(hours: 24));
      final operation = game.resumeWithProgress();
      expect(game.replaying, isTrue);
      expect(game.buy(0), isFalse);
      expect(game.completeCrewBriefing(0), isFalse);
      expect(game.selectSeasonPass(), isFalse);
      await operation;
      expect(game.replaying, isFalse);
      expect(game.replayError, isNull);
      expect(game.returnReport!.absence, const Duration(hours: 24));
      expect(snapshots.length, 1);
      expect(snapshots.single.main.support.activeSettlementId, isNull);
      expect(snapshots.single.settledThrough, now);
      expect(
        snapshots.single.story.season!.settledThroughMicros,
        BigInt.from(now.microsecondsSinceEpoch),
      );
      expect(game.buy(0), isTrue);
    },
  );

  test(
    'backgrounding again during replay does not restart online production',
    () async {
      var now = epoch;
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => now,
      );
      addTearDown(game.dispose);
      game.suspend();
      now = epoch.add(const Duration(hours: 8));
      final replay = game.resumeWithProgress();
      game.suspend();
      await replay;
      final settled = game.state.lifetimeMicros;
      now = now.add(const Duration(hours: 8));
      game.tick();
      expect(game.state.lifetimeMicros, settled);
      await game.resumeWithProgress();
      expect(game.state.lifetimeMicros, greaterThan(settled));
    },
  );
}
