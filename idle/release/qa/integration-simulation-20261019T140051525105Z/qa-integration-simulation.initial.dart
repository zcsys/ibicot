import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import '../lib/game_controller.dart';
import '../lib/offline_replay.dart';
import '../lib/story_state.dart';
import '../../simulation/lib/policy_run.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final content = SimulationContent('../content', '../events/content');
  const engine = TideglassEngine();
  PolicyRun policy({
    int chunk = 4,
    BonusPolicy bonus = BonusPolicy.requiredCalibrationsOnly,
  }) => PolicyRun(
    content,
    visitsPerDay: 3,
    bonus: bonus,
    resetPolicy: ResetPolicy.atVisits,
    offlineChunkHours: chunk,
  );
  StoryProgress story(PolicyRun p) => StoryProgress(
    campaign: p.campaign,
    dossiers: p.dossiers,
    season: p.season,
    pass: p.pass,
  );
  Map<String, dynamic> economic(GameState s) => s.toJson()
    ..remove('daily')
    ..remove('revision');

  test(
    '120h single-absence simulator and native worker preserve economic partitions',
    () async {
      final catalogue = await StoryCatalogue.load();
      final run = policy()..run(days: 5);
      final initial = run.main;
      final initialStory = story(run);
      final from = run.cursor,
          through = run.cursor.add(const Duration(hours: 120));
      final native = await replayOfflineSession(
        main: initial,
        story: initialStory,
        catalogue: catalogue,
        settledThrough: from,
        now: through,
      );
      run.advanceTo(through, offline: true);
      expect(economic(run.main), economic(native.main));
      expect(run.dossiers.toJson(), native.story.dossiers.toJson());
      expect(run.season.toJson(), native.story.season!.toJson());
      expect(run.pass.toJson(), native.story.pass!.toJson());
      expect(
        run.main.support.nextSettlementSequence,
        native.main.support.nextSettlementSequence,
      );
      expect(run.main.support.activeSettlementRequest, isNull);
      expect(
        run.main.daily.lastMaterializedDay,
        lessThan(native.main.daily.lastMaterializedDay),
      );
      expect(
        run.main.daily.contracts.length,
        lessThan(native.main.daily.contracts.length),
      );
      print(
        jsonEncode({
          'finding': 'end_of_run_daily_materialization_gap',
          'simulator_last_day': run.main.daily.lastMaterializedDay,
          'native_last_day': native.main.daily.lastMaterializedDay,
          'simulator_contracts': run.main.daily.contracts.length,
          'native_contracts': native.main.daily.contracts.length,
        }),
      );
    },
  );

  test('one 120h absence is invariant under 1h versus 4h simulator chunks', () {
    final a = policy(chunk: 1)..run(days: 5);
    final b = policy(chunk: 4)..run(days: 5);
    a.advanceTo(a.cursor.add(const Duration(hours: 120)), offline: true);
    b.advanceTo(b.cursor.add(const Duration(hours: 120)), offline: true);
    expect(economic(a.main), economic(b.main));
    expect(a.main.daily.toJson(), b.main.daily.toJson());
    expect(a.dossiers.toJson(), b.dossiers.toJson());
    expect(a.season.toJson(), b.season.toJson());
    expect(a.pass.toJson(), b.pass.toJson());
    expect(
      a.notesSpent + a.main.surveyNotes,
      a.surveyNotesEarned + a.contractNotesEarned,
    );
  });

  test(
    '72h and120h single absences give same core income with no automation',
    () {
      final a = policy(), b = policy();
      a.advanceTo(a.cursor.add(const Duration(hours: 72)), offline: true);
      b.advanceTo(b.cursor.add(const Duration(hours: 120)), offline: true);
      expect(a.main.walletMicros, b.main.walletMicros);
      expect(a.main.lifetimeMicros, BigInt.from(129600000000));
      expect(b.main.completedSurveys, 3);
      expect(b.main.focusCharges, 12);
      expect(b.main.elapsedMicros, BigInt.from(432000000000));
      expect(b.main.support.nextSettlementSequence, BigInt.two);
    },
  );

  test(
    'minimal campaign uses three actual accessible Focus activations; none does not',
    () async {
      final catalogue = await StoryCatalogue.load();
      final none = policy(bonus: BonusPolicy.none)..run(days: 5);
      final minimal = policy()..run(days: 5);
      expect(none.focusUsed, 0);
      expect(none.main.completedCalibrationIds, isEmpty);
      expect(none.campaign.restoredHarbor, 2);
      expect(minimal.focusUsed, 3);
      expect(minimal.main.completedCalibrationIds.length, 3);
      expect(minimal.campaign.restoredHarbor, greaterThanOrEqualTo(3));
      final game = GameController(
        initialState: none.main,
        initialStory: story(none),
        catalogue: catalogue,
        settledThrough: none.cursor,
        clock: () => none.cursor,
        startTicker: false,
      );
      addTearDown(game.dispose);
      for (var n = 1; n <= 3; n++) {
        expect(
          game.completeCalibration(
            'calibration.${n.toString().padLeft(2, '0')}',
          ),
          isTrue,
        );
      }
      expect(game.state.completedCalibrationIds.length, 3);
      expect(game.story.campaign.restoredHarbor, greaterThanOrEqualTo(3));
      expect(game.state.focusRemainingMicros, BigInt.from(1800000000));
    },
  );

  test(
    'client permits repeated archive reflection omitted by claim-ready policy',
    () async {
      final catalogue = await StoryCatalogue.load();
      final run = policy()..run(days: 2);
      final game = GameController(
        initialState: run.main,
        initialStory: story(run),
        catalogue: catalogue,
        settledThrough: run.cursor,
        clock: () => run.cursor,
        startTicker: false,
      );
      addTearDown(game.dispose);
      final before = game.state.daily.discoveryTotals['archive'] ?? BigInt.zero;
      expect(game.readArchive('archive.intro'), isTrue);
      expect(game.readArchive('archive.intro'), isTrue);
      expect(game.state.daily.discoveryTotals['archive'], before + BigInt.two);
    },
  );

  test(
    'exhausted first-completion dossiers must not be offered as available discovery',
    () async {
      final catalogue = await StoryCatalogue.load();
      var now = PolicyRun.epoch;
      final allIds = catalogue.dossiers.map((d) => d.id).toSet();
      GameState? seeded;
      DailyContract? goal;
      for (var i = 0; i < 100; i++) {
        final s = engine
            .refreshContracts(
              GameState(
                counts: [100, 100, 100, 100, 100],
                lifetimeMicros: BigInt.from(10).pow(30),
                charts: BigInt.from(100),
                surveysCollectedTotal: BigInt.from(12),
                completedCalibrationIds: {
                  'calibration.01',
                  'calibration.02',
                  'calibration.03',
                },
                rechartCount: 2,
              ),
              now,
              accountSeed: 'qa-exhausted-$i',
              utcOffsetMinutes: 0,
              availableDiscoveryKinds: ['archive', 'challenge', 'calibration'],
            )
            .state;
        final goals = s.dailyContracts.where(
          (c) => c.discoveryKind == 'challenge',
        );
        if (goals.isNotEmpty) {
          seeded = s;
          goal = goals.first;
          break;
        }
      }
      expect(goal, isNotNull);
      final game = GameController(
        initialState: seeded,
        catalogue: catalogue,
        initialStory: StoryProgress(
          campaign: CampaignProgress(
            completed: {'chapter.01', 'chapter.02', 'chapter.03'},
          ),
          dossiers: DossierCollection(owned: allIds, completed: allIds),
        ),
        settledThrough: now,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(game.dispose);
      expect(game.openDossier('challenge.01'), isTrue);
      expect(game.setDossierPlan(automatic: true), isTrue);
      final before =
          game.state.daily.discoveryTotals['challenge'] ?? BigInt.zero;
      now = now.add(const Duration(days: 3));
      game.tick();
      expect(game.story.dossiers.active!.complete, isTrue);
      expect(
        game.state.daily.discoveryTotals['challenge'] ?? BigInt.zero,
        before,
      );
      expect(engine.contractProgress(game.state, goal!), BigInt.zero);
      expect(game.claimContract(goal.id), isFalse);
      // Product defect: no further first completion exists to satisfy this kind.
      expect(game.availableDiscoveries, isNot(contains('challenge')));
    },
  );
}
