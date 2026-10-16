import 'dart:convert';
import 'dart:io';

import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

Map<String, dynamic> read(String path) =>
    Map<String, dynamic>.from(jsonDecode(File(path).readAsStringSync()));
final dossiers = List.generate(
  12,
  (i) => ChallengeDefinition.fromJson(
    read(
      '../content/challenges/challenge.${(i + 1).toString().padLeft(2, '0')}.json',
    ),
  ),
);
final campaign = Campaign(
  read('../content/progression/campaign.json'),
  dossiers,
);

void main() {
  test(
    'dossier purchase charges exactly100Notes once and preserves mainmoney',
    () {
      final main = GameState(surveyNotes: BigInt.from(200));
      final progress = CampaignProgress(
        completed: {'chapter.01', 'chapter.02', 'chapter.03'},
      );
      final first = DossierCollection().open(main, progress, dossiers.first);
      expect(first.accepted, isTrue);
      expect(first.main.surveyNotes, BigInt.from(100));
      expect(first.main.revision, main.revision + 1);
      expect(first.main.walletMicros, main.walletMicros);
      final again = first.dossiers.open(first.main, progress, dossiers.first);
      expect(again.main.surveyNotes, BigInt.from(100));
      expect(again.dossiers.owned, {'challenge.01'});
      final closed = again.dossiers.leave();
      final replay = closed.open(again.main, progress, dossiers.first);
      expect(replay.main.surveyNotes, BigInt.from(100));
      expect(replay.dossiers.active!.fleet.walletMicros, BigInt.zero);
      final restored = DossierCollection.fromJson(replay.dossiers.toJson());
      expect(restored.owned, replay.dossiers.owned);
    },
  );
  test(
    'dossier entry rejects missingunlock, missingNotes and unconfirmedreplacement',
    () {
      final opened = CampaignProgress(
        completed: {'chapter.01', 'chapter.02', 'chapter.03'},
      );
      expect(
        DossierCollection().open(GameState(), opened, dossiers.first).accepted,
        isFalse,
      );
      final rich = GameState(surveyNotes: BigInt.from(200));
      expect(
        DossierCollection()
            .open(rich, CampaignProgress(), dossiers.first)
            .accepted,
        isFalse,
      );
      final one = DossierCollection().open(rich, opened, dossiers.first);
      expect(
        one.dossiers.open(one.main, opened, dossiers[1]).accepted,
        isFalse,
      );
      final two = one.dossiers.open(
        one.main,
        opened,
        dossiers[1],
        replaceActive: true,
      );
      expect(two.accepted, isTrue);
      expect(two.main.surveyNotes, BigInt.zero);
      expect(two.dossiers.owned.length, 2);
      expect(() => two.dossiers.restart(dossiers.first), throwsFormatException);
    },
  );
  test(
    'invalid campaign order,goal mode and unknownconstruction cannotload',
    () {
      for (final key in ['id', 'prerequisite', 'objective_mode']) {
        final source = read('../content/progression/campaign.json');
        source['chapters'][0][key] = 'invalid';
        expect(() => Campaign(source, dossiers), throwsFormatException);
      }
      final definition = read('../content/challenges/challenge.01.json');
      definition['construction_mode'] = 'paid_boost';
      expect(
        () => ChallengeDefinition.fromJson(definition),
        throwsFormatException,
      );
      expect(
        () => CampaignProgress(completed: {'chapter.06'}),
        throwsFormatException,
      );
    },
  );
  test(
    'campaigndeepcopy cannot mutate shippedgoals through callerreferences',
    () {
      final source = read('../content/progression/campaign.json');
      final subject = Campaign(source, dossiers);
      source['chapters'][0]['objectives'][0]['value'] = 999;
      expect(subject.chapters[0]['objectives'][0]['value'], 1);
      expect(
        () => subject.chapters[0]['objectives'][0]['value'] = 999,
        throwsUnsupportedError,
      );
    },
  );
  test('exact launch counts, family coverage, persistent100Note entry', () {
    expect(dossiers.length, 12);
    for (final family in [
      'constrained_fleets',
      'synergy_priorities',
      'automation_planning',
    ]) {
      expect(dossiers.where((d) => d.family == family).length, 4);
    }
    expect(campaign.chapters.length, 6);
  });
  for (final definition in dossiers) {
    test('${definition.id} has a reachable automatic baseline', () {
      final engine = ChallengeEconomy(definition);
      var run = engine.newRun().copyWith(automatic: true);
      for (var i = 0; i < 48 && !run.complete; i++) {
        run = engine.advanceRun(run, const Duration(minutes: 30));
      }
      expect(run.complete, isTrue, reason: definition.title);
      expect(run.fleet.charts, BigInt.zero);
      expect(run.fleet.surveyNotes, BigInt.zero);
      expect(engine.rechart(run.fleet).accepted, isFalse);
      engine.validateRun(ChallengeRun.fromJson(run.toJson()));
    });
  }
  test(
    'best payback and tier priority both reach the first synergy dossier',
    () {
      final engine = ChallengeEconomy(dossiers[4]);
      for (final policy in ChallengePolicy.values) {
        var run = engine.newRun().copyWith(automatic: true, policy: policy);
        for (var i = 0; i < 48 && !run.complete; i++) {
          run = engine.advanceRun(run, const Duration(minutes: 30));
        }
        expect(run.complete, isTrue, reason: policy.name);
      }
    },
  );
  test('capped fleet cannot buy beyond berth limits withbulk or max', () {
    final engine = ChallengeEconomy(dossiers.first);
    final state = GameState(
      counts: [99, 0, 0, 0, 0],
      walletMicros: BigInt.from(10).pow(20),
      lifetimeMicros: BigInt.from(10).pow(20),
    );
    expect(engine.buy(state, 0, 2).accepted, isFalse);
    expect(engine.maximumAffordable(state, 0), 1);
    expect(engine.buyMax(state, 0).state.counts[0], 100);
    expect(engine.isUnlocked(state, 2), isFalse);
  });
  test('automatic-only dossier ignores manualpurchase', () {
    final engine = ChallengeEconomy(dossiers[8]);
    final run = engine.advanceRun(
      engine.newRun().copyWith(automatic: false),
      const Duration(minutes: 5),
    );
    expect(identical(engine.purchase(run, 0, 1), run), isTrue);
    expect(run.fleet.counts.reduce((a, b) => a + b), greaterThan(1));
  });
  test('split offline history preserves exact decisions and remainder', () {
    final engine = ChallengeEconomy(dossiers[4]);
    final seed = engine.newRun().copyWith(automatic: true);
    final whole = engine.advanceRun(
      seed,
      const Duration(hours: 72),
      offline: true,
    );
    var split = seed;
    for (var hour = 0; hour < 72; hour += 6) {
      split = engine.advanceRun(
        split,
        const Duration(hours: 6),
        offline: true,
        offlineElapsedBefore: Duration(hours: hour),
      );
    }
    expect(split.fleet.counts, whole.fleet.counts);
    expect(split.fleet.walletMicros, whole.fleet.walletMicros);
    expect(split.fleet.lifetimeMicros, whole.fleet.lifetimeMicros);
    expect(split.fleet.earningRemainder, whole.fleet.earningRemainder);
  });
  test('main-world power cannot be imported into scenario state', () {
    final main = GameState(
      charts: BigInt.from(10),
      lifetimeMicros: BigInt.from(10).pow(15),
    );
    expect(
      () => ChallengeRun(dossierId: 'challenge.01', fleet: main),
      throwsFormatException,
    );
    expect(
      () => ChallengeRun(
        dossierId: 'challenge.01',
        fleet: GameState(focusRemainingMicros: BigInt.one),
      ),
      throwsFormatException,
    );
    expect(
      () => ChallengeRun(
        dossierId: 'challenge.01',
        fleet: GameState(surveyNotes: BigInt.one),
      ),
      throwsFormatException,
    );
  });
  test(
    'first chapter requires an actual Rechart; restoration neverregresses',
    () {
      var progress = CampaignProgress();
      ProgressFacts facts(int resets) => ProgressFacts(
        main: GameState.initial(),
        recharts: resets,
        surveysCollected: 0,
        calibrations: {},
        completedChallenges: {},
      );
      expect(campaign.evaluate(progress, facts(0)).completed, isEmpty);
      progress = campaign.evaluate(progress, facts(1));
      expect(progress.completed, {'chapter.01'});
      expect(progress.cosmeticIds, {'cosmetic.core.chapter.01'});
      expect(progress.archiveIds.length, 3);
      expect(
        campaign.evaluate(progress, facts(0)).completed,
        progress.completed,
      );
    },
  );
  test(
    'ending needs six selected dossiers and nooptionalNotesinkorpaidreward',
    () {
      final main = GameState(
        counts: [25, 25, 10, 10, 1],
        charts: BigInt.from(100),
        lifetimeMicros: BigInt.from(10).pow(20),
      );
      final facts = ProgressFacts(
        main: main,
        recharts: 5,
        surveysCollected: 12,
        calibrations: {'calibration.01', 'calibration.02', 'calibration.03'},
        completedChallenges: {
          'challenge.01',
          'challenge.02',
          'challenge.05',
          'challenge.06',
          'challenge.09',
          'challenge.10',
        },
      );
      final result = campaign.evaluate(CampaignProgress(), facts);
      expect(result.hasEnding, isTrue);
      expect(result.archiveIds.length, 18);
      expect(result.cosmeticIds.length, 6);
      expect(main.surveyNotes, BigInt.zero);
      expect(
        CampaignProgress.fromJson(result.toJson()).completed,
        result.completed,
      );
    },
  );
  test('chapter5 needs currentfullfleet; forgedcompletionprefixrejected', () {
    final facts = ProgressFacts(
      main: GameState(
        charts: BigInt.from(100),
        lifetimeMicros: BigInt.from(10).pow(20),
      ),
      recharts: 5,
      surveysCollected: 12,
      calibrations: {'1', '2', '3'},
      completedChallenges: {'challenge.01', 'challenge.05', 'challenge.09'},
    );
    final prefix = CampaignProgress(
      completed: {'chapter.01', 'chapter.02', 'chapter.03', 'chapter.04'},
    );
    expect(campaign.evaluate(prefix, facts).completed.length, 4);
    expect(
      () => CampaignProgress.fromJson({
        'completed_chapters': ['chapter.06'],
      }),
      throwsFormatException,
    );
  });
}
