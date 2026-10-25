import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });

  test(
    'seasonal alternative uses one shared claim and excludes earlier production',
    () {
      var now = epoch;
      final game = GameController(
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(game.dispose);
      final first = game.state.dailyContracts.first.id;
      expect(game.bindSeasonContract(first), isTrue);
      expect(game.seasonContractProgress(first), BigInt.zero);
      now = now.add(const Duration(minutes: 10));
      game.tick();
      expect(game.seasonContractProgress(first), BigInt.from(600000000));
      expect(game.claimSeasonContract(first), isTrue);
      expect(game.state.passXp, BigInt.from(250));
      expect(game.state.surveyNotes, BigInt.from(10));
      expect(game.claimContract(first), isFalse);
      expect(game.claimSeasonContract(first), isFalse);
      final second = game.state.dailyContracts
          .where((c) => !c.claimed)
          .first
          .id;
      expect(game.bindSeasonContract(second), isTrue);
      expect(game.seasonContractProgress(second), BigInt.zero);
      now = now.add(const Duration(minutes: 10));
      game.tick();
      expect(game.claimSeasonContract(second), isTrue);
      expect(game.state.passXp, BigInt.from(500));
      final reward = catalogue.seasonDefinition.rewards.firstWhere(
        (r) => r.track == 'free' && r.level == 1,
      );
      final wallet = game.state.walletMicros, life = game.state.lifetimeMicros;
      expect(game.claimFreePassReward(reward.id), isTrue);
      expect(game.claimFreePassReward(reward.id), isFalse);
      expect(game.state.walletMicros, wallet);
      expect(game.state.lifetimeMicros, life);
      expect(
        game.passEngine!.fragmentIds(game.story.pass!),
        contains(reward.contentId),
      );
    },
  );

  test('reroll prunes stale seasonal binding and creates a fresh baseline', () {
    var now = epoch;
    final game = GameController(
      catalogue: catalogue,
      clock: () => now,
      startTicker: false,
    );
    addTearDown(game.dispose);
    final id = game.state.dailyContracts.first.id;
    expect(game.bindSeasonContract(id), isTrue);
    now = now.add(const Duration(minutes: 20));
    game.tick();
    expect(game.rerollContract(id), isTrue);
    expect(game.story.pass!.alternatives.containsKey(id), isFalse);
    expect(game.bindSeasonContract(id), isTrue);
    expect(game.seasonContractProgress(id), BigInt.zero);
  });

  test('season end archives exactly and manual resume skips paused time', () {
    var now = epoch;
    final game = GameController(
      catalogue: catalogue,
      clock: () => now,
      startTicker: false,
    );
    addTearDown(game.dispose);
    game.suspend();
    now = DateTime.utc(2026, 11, 15, 12);
    game.resume();
    expect(game.story.season!.phase, SeasonPhase.archived);
    expect(game.story.season!.archiveActive, isFalse);
    final before = game.story.season!.fleet.lifetimeMicros;
    now = now.add(const Duration(days: 1));
    game.tick();
    expect(game.story.season!.fleet.lifetimeMicros, before);
    expect(game.setSeasonArchiveActive(true), isTrue);
    now = now.add(const Duration(seconds: 60));
    game.tick();
    expect(
      game.story.season!.fleet.lifetimeMicros - before,
      BigInt.from(60000000),
    );
    expect(game.setSeasonArchiveActive(false), isTrue);
    final after = game.story.season!.fleet.lifetimeMicros;
    now = now.add(const Duration(seconds: 60));
    game.tick();
    expect(game.story.season!.fleet.lifetimeMicros, after);
  });

  test(
    'loading content for the first time never invents prior seasonal earnings',
    () {
      final game = GameController(
        catalogue: catalogue,
        settledThrough: epoch.subtract(const Duration(days: 2)),
        clock: () => epoch,
        startTicker: false,
      );
      addTearDown(game.dispose);
      expect(game.state.walletMicros, BigInt.from(108000000000));
      expect(game.story.season!.fleet.walletMicros, BigInt.zero);
      expect(
        game.story.season!.settledThroughMicros,
        BigInt.from(epoch.microsecondsSinceEpoch),
      );
    },
  );

  test('main Charts Focus and Support do not change seasonal production', () {
    var now = epoch;
    final rich = GameState(
      charts: BigInt.from(1000),
      lifetimeMicros: BigInt.from(10).pow(23),
      focusCharges: 1,
    );
    final game = GameController(
      initialState: rich,
      catalogue: catalogue,
      clock: () => now,
      startTicker: false,
    );
    addTearDown(game.dispose);
    expect(game.activateFocus(), isTrue);
    expect(game.completeCrewBriefing(0), isTrue);
    expect(game.useSupportBoost(game.state.support.tokens.single.id), isTrue);
    final output = game.seasonEngine!.outputPerSecond(game.story.season!);
    expect(output.raw, Fixed.one.raw);
    now = now.add(const Duration(seconds: 10));
    game.tick();
    expect(game.story.season!.fleet.walletMicros, BigInt.from(10000000));
    expect(game.state.walletMicros, greaterThan(BigInt.from(10000000)));
  });

  test(
    'combined save reload preserves season cursor and rejects a mismatched partition',
    () {
      var now = epoch;
      final game = GameController(
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
      );
      now = now.add(const Duration(seconds: 100));
      game.tick();
      expect(game.buyInSeason(0), isTrue);
      final story = StoryProgress.fromJson(game.story.toJson());
      final core = GameState.fromJson(game.state.toJson());
      game.dispose();
      final restored = GameController(
        catalogue: catalogue,
        initialStory: story,
        initialState: core,
        settledThrough: now,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(restored.dispose);
      expect(restored.story.season!.fleet.counts[0], 2);
      expect(restored.story.season!.fleet.walletMicros, BigInt.from(66400000));
      expect(
        () => GameController(
          catalogue: catalogue,
          initialStory: story,
          initialState: core,
          settledThrough: now.subtract(const Duration(seconds: 1)),
          clock: () => now,
          startTicker: false,
        ),
        throwsFormatException,
      );
    },
  );
}
