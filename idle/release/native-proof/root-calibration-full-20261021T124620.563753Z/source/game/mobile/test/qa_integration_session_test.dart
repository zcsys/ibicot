import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

// Independent integration assertions authored by /root/qa_integration.
// Test-only seeds and accelerated clocks are not natural-player evidence.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final epoch = DateTime.utc(2026, 10, 16, 12);
  late StoryCatalogue catalogue;
  setUpAll(() async => catalogue = await StoryCatalogue.load());

  Map<String, dynamic> payload(GameState main, StoryProgress story) => {
    'client_schema_version': 2,
    'core': main.toJson(),
    'story': story.toJson(),
    'client_preferences': const ClientPreferences().toJson(),
  };

  test(
    'QA: import rejects an impossible pass receipt before replacing a valid branch',
    () async {
      final directory = Directory.systemTemp.createTempSync(
        'tideglass-qa-pass-',
      );
      final other = Directory.systemTemp.createTempSync('tideglass-qa-source-');
      addTearDown(() => directory.deleteSync(recursive: true));
      addTearDown(() => other.deleteSync(recursive: true));
      final game = GameController(
        catalogue: catalogue,
        clock: () => epoch,
        startTicker: false,
      );
      addTearDown(game.dispose);
      SaveRepository target() => SaveRepository(
        directory,
        economicVersion: economyVersion,
        economicDigest: bundledEconomyDigest,
        validatePayload: (p) => validateClientPayload(p, catalogue: catalogue),
      );
      final repository = target();
      await repository.load();
      await repository.save(
        payload(game.state, game.story),
        settledThrough: epoch,
      );
      final before = (await repository.load()).snapshot!;
      final bad =
          jsonDecode(jsonEncode(payload(game.state, game.story)))
              as Map<String, dynamic>;
      final reward = catalogue.seasonDefinition.rewards.firstWhere(
        (r) => r.track == 'free',
      );
      final account = game.state.daily.accountSeed!;
      (bad['story']['pass']['claims'] as Map)[reward.id] = {
        'account_id': account,
        'pass_id': catalogue.seasonDefinition.passId,
        'reward_id': reward.id,
        'receipt_id': 'pass:$account:${reward.id}',
        'entitlement_verification_receipt_id': null,
      };
      // A structurally valid source envelope isolates the target's semantic
      // validator. Its shared XP remains zero, below this reward's threshold.
      final source = SaveRepository(
        other,
        economicVersion: economyVersion,
        economicDigest: bundledEconomyDigest,
        validatePayload: (_) {},
      );
      await source.load();
      await source.save(bad, settledThrough: epoch);
      final exported = await source.exportSave();
      await expectLater(
        repository.importSave(exported),
        throwsA(isA<SaveException>()),
      );
      final after = (await target().load()).snapshot!;
      expect(after.saveId, before.saveId);
      expect(after.payload, before.payload);
    },
  );

  for (final pair in <int, int>{
    2: 7200,
    8: 28800,
    24: 86400,
    48: 108000,
    72: 129600,
  }.entries) {
    test(
      'QA: ${pair.key}-hour return settles both fleets once with exact envelope',
      () {
        var now = epoch;
        final game = GameController(
          catalogue: catalogue,
          clock: () => now,
          startTicker: false,
        );
        addTearDown(game.dispose);
        game.suspend();
        now = now.add(Duration(hours: pair.key));
        game.resume();
        final expected = BigInt.from(pair.value) * BigInt.from(1000000);
        expect(game.state.lifetimeMicros, expected);
        expect(game.state.walletMicros, expected);
        expect(game.story.season!.fleet.lifetimeMicros, expected);
        expect(game.state.focusCharges, (pair.key ~/ 2).clamp(0, 12));
        expect(game.state.completedSurveys, (pair.key ~/ 8).clamp(0, 3));
        expect(game.state.support.caches.length, 6);
        final main = jsonEncode(game.state.toJson());
        final story = jsonEncode(game.story.toJson());
        game.resume();
        expect(jsonEncode(game.state.toJson()), main);
        expect(jsonEncode(game.story.toJson()), story);
        final restored = GameController(
          initialState: GameState.fromJson(game.state.toJson()),
          initialStory: StoryProgress.fromJson(
            game.story.toJson(),
            seasonDefinition: catalogue.seasonDefinition,
          ),
          catalogue: catalogue,
          settledThrough: now,
          clock: () => now,
          startTicker: false,
        );
        addTearDown(restored.dispose);
        expect(restored.state.lifetimeMicros, expected);
        expect(restored.story.season!.fleet.lifetimeMicros, expected);
        expect(
          restored.state.support.caches.map((c) => c.id),
          game.state.support.caches.map((c) => c.id),
        );
      },
    );
  }

  for (final visits in [1, 3, 6]) {
    test('QA: $visits daily visits preserve unboosted daily supply', () {
      var now = epoch;
      final game = GameController(
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(game.dispose);
      var collected = BigInt.zero;
      for (var visit = 0; visit < visits; visit++) {
        game.suspend();
        now = now.add(Duration(hours: 24 ~/ visits));
        game.resume();
        final before = game.state.surveyNotes;
        game.collectSurveys();
        collected += game.state.surveyNotes - before;
      }
      expect(game.state.lifetimeMicros, BigInt.from(86400000000));
      expect(game.story.season!.fleet.lifetimeMicros, BigInt.from(86400000000));
      expect(collected, BigInt.from(30));
      expect(game.state.focusCharges, 12);
      expect(game.state.dailyContracts.length, 6);
    });
  }

  test(
    'QA: failure in a secondary timeline preserves every prior partition',
    () {
      var now = epoch;
      final game = _RejectingSeasonController(
        catalogue: catalogue,
        clock: () => now,
      );
      addTearDown(game.dispose);
      final main = jsonEncode(game.state.toJson());
      final story = jsonEncode(game.story.toJson());
      now = now.add(const Duration(minutes: 10));
      expect(game.tick, throwsStateError);
      expect(jsonEncode(game.state.toJson()), main);
      expect(jsonEncode(game.story.toJson()), story);
      expect(game.settledThrough, epoch);
      game.reject = false;
      game.tick();
      expect(game.state.lifetimeMicros, BigInt.from(600000000));
      expect(game.story.season!.fleet.lifetimeMicros, BigInt.from(600000000));
    },
  );
}

class _RejectingSeasonController extends GameController {
  _RejectingSeasonController({
    required StoryCatalogue catalogue,
    required DateTime Function() clock,
  }) : super(catalogue: catalogue, clock: clock, startTicker: false);
  bool reject = true;
  @override
  SeasonEngine get seasonEngine => reject
      ? _RejectingSeasonEngine(catalogue!.seasonDefinition)
      : SeasonEngine(catalogue!.seasonDefinition);
}

class _RejectingSeasonEngine extends SeasonEngine {
  _RejectingSeasonEngine(super.definition);
  @override
  SeasonResult advanceTo(
    SeasonState state,
    DateTime nowUtc, {
    bool offline = false,
    Duration offlineElapsedBefore = Duration.zero,
    int maximumEvents = 100000,
  }) => SeasonResult(state, accepted: false, reason: 'qa_injected_failure');
}
