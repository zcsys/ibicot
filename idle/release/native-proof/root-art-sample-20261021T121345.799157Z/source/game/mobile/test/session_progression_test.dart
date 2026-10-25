import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  const engine = TideglassEngine();
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  StoryProgress unlocked() => StoryProgress(
    campaign: CampaignProgress(
      completed: {'chapter.01', 'chapter.02', 'chapter.03'},
    ),
  );
  GameState funded() =>
      GameState.initial().copyWith(surveyNotes: BigInt.from(150));
  SaveRepository repository(Directory dir) => SaveRepository(
    dir,
    economicVersion: economyVersion,
    economicDigest: bundledEconomyDigest,
    validatePayload: validateClientPayload,
  );
  Map<String, dynamic> payload(GameState core, StoryProgress story) => {
    'client_schema_version': 2,
    'core': core.toJson(),
    'story': story.toJson(),
    'client_preferences': const ClientPreferences().toJson(),
  };

  test(
    'dossier debit and ownership persist together; reopening does not debit twice',
    () async {
      final dir = Directory.systemTemp.createTempSync('tideglass-story-');
      addTearDown(() => dir.deleteSync(recursive: true));
      final store = repository(dir);
      await store.load();
      final game = GameController(
        initialState: funded(),
        initialStory: unlocked(),
        catalogue: catalogue,
        clock: () => epoch,
        startTicker: false,
        onSessionPersist: (core, story, cursor) =>
            store.save(payload(core, story), settledThrough: cursor),
      );
      expect(game.openDossier('challenge.01'), isTrue);
      expect(game.state.surveyNotes, BigInt.from(50));
      expect(game.buyDecoration('cosmetic.core.decoration.01'), isTrue);
      await game.save();
      expect(game.saveError, isNull);
      final saved = (await repository(dir).load()).snapshot!;
      game.dispose();
      final restored = GameController(
        initialState: GameState.fromJson(
          Map<String, dynamic>.from(saved.payload['core']),
        ),
        initialStory: StoryProgress.fromJson(
          Map<String, dynamic>.from(saved.payload['story']),
        ),
        catalogue: catalogue,
        settledThrough: saved.settledThrough,
        clock: () => epoch,
        startTicker: false,
      );
      addTearDown(restored.dispose);
      expect(restored.state.surveyNotes, BigInt.zero);
      expect(restored.story.dossiers.owned, {'challenge.01'});
      expect(restored.story.equippedDecoration, 'cosmetic.core.decoration.01');
      expect(restored.openDossier('challenge.01'), isTrue);
      expect(restored.state.surveyNotes, BigInt.zero);
      expect(restored.buyDecoration('cosmetic.core.decoration.01'), isFalse);
      expect(restored.restartDossier(), isTrue);
      expect(restored.story.dossiers.owned, {'challenge.01'});
    },
  );

  test(
    'main production and separate challenge advance through the same absence',
    () {
      var now = epoch;
      final game = GameController(
        initialState: funded(),
        initialStory: unlocked(),
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
      );
      addTearDown(game.dispose);
      expect(game.openDossier('challenge.05'), isTrue);
      expect(game.setDossierPlan(automatic: true), isTrue);
      final before = game.state;
      game.suspend();
      now = now.add(const Duration(hours: 2));
      game.resume();
      final expected = engine
          .advance(before, const Duration(hours: 2), offline: true)
          .state;
      expect(game.state.walletMicros, expected.walletMicros);
      expect(game.state.lifetimeMicros, expected.lifetimeMicros);
      expect(
        game.story.dossiers.active!.fleet.counts.reduce((a, b) => a + b),
        greaterThan(1),
      );
      expect(game.story.dossiers.active!.fleet.charts, BigInt.zero);
      expect(game.story.dossiers.active!.fleet.support.caches, isEmpty);
      expect(game.state.surveyNotes, BigInt.from(50));
      expect(game.state.support.caches.length, 6);
    },
  );

  test(
    'replacement requires confirmation and archive commands reject locked identifiers',
    () {
      final game = GameController(
        initialState: funded(),
        initialStory: unlocked(),
        catalogue: catalogue,
        clock: () => epoch,
        startTicker: false,
      );
      addTearDown(game.dispose);
      expect(game.openDossier('challenge.01'), isTrue);
      game.state = game.state.copyWith(
        surveyNotes: BigInt.from(100),
      ); // Explicit test fixture only.
      expect(game.openDossier('challenge.02'), isFalse);
      expect(game.story.dossiers.active!.dossierId, 'challenge.01');
      expect(game.state.surveyNotes, BigInt.from(100));
      expect(game.openDossier('challenge.02', replaceActive: true), isTrue);
      expect(game.state.surveyNotes, BigInt.zero);
      expect(game.readArchive('archive.main.18'), isFalse);
      expect(game.readArchive('archive.fake'), isFalse);
      expect(game.readArchive('archive.main.01'), isTrue);
      expect(game.readArchive('archive.intro'), isTrue);
    },
  );

  test(
    'schema2 validates atomic story and schema1 migration input remains supported',
    () {
      final value = payload(GameState.initial(), StoryProgress());
      expect(() => validateClientPayload(value), returnsNormally);
      final old = Map<String, dynamic>.from(value)..remove('story');
      old['client_schema_version'] = 1;
      expect(() => validateClientPayload(old), returnsNormally);
      final forged = Map<String, dynamic>.from(value);
      forged['story'] = {'schema_version': 1};
      expect(() => validateClientPayload(forged), throwsFormatException);
      expect(
        () => StoryProgress(equippedDecoration: 'cosmetic.core.decoration.01'),
        throwsFormatException,
      );
    },
  );

  test(
    'unspent main support inventory cannot be imported into a challenge',
    () {
      var main = engine
          .refreshContracts(
            GameState.initial(),
            epoch,
            accountSeed: 'support-import',
          )
          .state;
      main = engine
          .claimSupportToken(
            main,
            accountDay: main.daily.dayHighWater,
            slot: 0,
            sourceId: engine.briefingSourceId(main, 0),
          )
          .state;
      expect(main.supportRemainingMicros, BigInt.zero);
      expect(
        () => ChallengeRun(dossierId: 'challenge.01', fleet: main),
        throwsFormatException,
      );
    },
  );

  test(
    'controller offline salvage is bounded, durable and never pays a slice twice',
    () {
      var now = epoch;
      final game = GameController(clock: () => now, startTicker: false);
      addTearDown(game.dispose);
      game.suspend();
      now = now.add(const Duration(minutes: 15));
      game.resume();
      expect(game.state.walletMicros, BigInt.from(900000000));
      expect(game.state.support.caches.length, 3);
      final cache = game.state.support.caches.first;
      expect(game.completeCrewBriefing(0), isTrue);
      expect(game.completeCrewBriefing(0), isFalse);
      final token = game.state.support.tokens.single;
      expect(
        game.buy(0),
        isTrue,
      ); // Increased rate cannot enlarge the settled cache.
      final before = game.state.walletMicros;
      expect(game.claimSalvage(token.id, cache.id), isTrue);
      expect(game.state.walletMicros - before, BigInt.from(300000000));
      expect(game.claimSalvage(token.id, cache.id), isFalse);
      final roundTrip = GameState.fromJson(game.state.toJson());
      expect(roundTrip.support.claimedSliceIds.contains(cache.id), isTrue);
      expect(roundTrip.support.tokens.single.spent, isTrue);
      final count = roundTrip.support.caches.length;
      game.resume();
      expect(game.state.support.caches.length, count);
    },
  );
}
