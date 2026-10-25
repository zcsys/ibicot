import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

// Non-author repository/client boundary tests. Legacy fixtures are preserved
// JSON schemas, not claims of released native upgrade paths.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async => catalogue = await StoryCatalogue.load());
  Map<String, dynamic> payload(GameState main, StoryProgress story) => {
    'client_schema_version': 2,
    'core': main.toJson(),
    'story': story.toJson(),
    'client_preferences': const ClientPreferences().toJson(),
  };
  SaveRepository checked(Directory directory) => SaveRepository(
    directory,
    economicVersion: economyVersion,
    economicDigest: bundledEconomyDigest,
    validatePayload: (p) => validateClientPayload(p, catalogue: catalogue),
    validateSnapshot: (p, cursor) =>
        validateClientSnapshot(p, cursor, catalogue: catalogue),
  );

  for (final mode in [
    'calendar_before',
    'calendar_after',
    'season_before',
    'season_after',
    'receipt_future',
  ]) {
    test(
      'QA: $mode import cannot replace an internally consistent branch',
      () async {
        final dir = Directory.systemTemp.createTempSync('tideglass-qa-cursor-');
        final sourceDir = Directory.systemTemp.createTempSync(
          'tideglass-qa-import-',
        );
        addTearDown(() => dir.deleteSync(recursive: true));
        addTearDown(() => sourceDir.deleteSync(recursive: true));
        final game = GameController(
          catalogue: catalogue,
          clock: () => epoch,
          startTicker: false,
        );
        addTearDown(game.dispose);
        final repository = checked(dir);
        await repository.load();
        await repository.save(
          payload(game.state, game.story),
          settledThrough: epoch,
        );
        final before = (await repository.load()).snapshot!;
        final bad =
            jsonDecode(jsonEncode(payload(game.state, game.story)))
                as Map<String, dynamic>;
        final cursor = BigInt.from(epoch.microsecondsSinceEpoch);
        if (mode.startsWith('calendar')) {
          bad['core']['daily']['utc_anchor_micros'] =
              (cursor + (mode.endsWith('before') ? -BigInt.one : BigInt.one))
                  .toString();
        } else if (mode.startsWith('season')) {
          bad['story']['season']['settled_through_micros'] =
              (cursor + (mode.endsWith('before') ? -BigInt.one : BigInt.one))
                  .toString();
        } else {
          bad['core']['support']['last_settlement_through_utc_micros'] =
              (cursor + BigInt.one).toString();
        }
        final source = SaveRepository(
          sourceDir,
          economicVersion: economyVersion,
          economicDigest: bundledEconomyDigest,
          validatePayload: (_) {},
        );
        await source.load();
        await source.save(bad, settledThrough: epoch);
        await expectLater(
          repository.importSave(await source.exportSave()),
          throwsA(isA<SaveException>()),
        );
        final after = (await checked(dir).load()).snapshot!;
        expect(after.saveId, before.saveId);
        expect(after.payload, before.payload);
      },
    );
  }

  for (final version in [1, 2, 3]) {
    test(
      'QA: v$version migrates through the real client and repository without replaying committed income',
      () async {
        final dir = Directory.systemTemp.createTempSync(
          'tideglass-qa-migrate-',
        );
        addTearDown(() => dir.deleteSync(recursive: true));
        final raw =
            jsonDecode(
                  File(
                    '../core/test/fixtures/state-v$version.json',
                  ).readAsStringSync(),
                )
                as Map<String, dynamic>;
        final oldCursor = epoch.add(const Duration(minutes: 5));
        final repository = checked(dir);
        await repository.load();
        await repository.save({
          'client_schema_version': 1,
          'core': raw,
          'client_preferences': const ClientPreferences().toJson(),
        }, settledThrough: oldCursor);
        final old = (await checked(dir).load()).snapshot!;
        final now = oldCursor.add(const Duration(minutes: 1));
        final loaded = GameState.fromJson(
          Map<String, dynamic>.from(old.payload['core']),
        );
        final expected = const TideglassEngine()
            .advance(loaded, const Duration(minutes: 1), offline: true)
            .state;
        final game = GameController(
          initialState: loaded,
          catalogue: catalogue,
          settledThrough: old.settledThrough,
          clock: () => now,
          startTicker: false,
          onSessionPersist: (main, story, cursor) =>
              repository.save(payload(main, story), settledThrough: cursor),
        );
        addTearDown(game.dispose);
        expect(game.state.walletMicros, expected.walletMicros);
        expect(game.state.lifetimeMicros, expected.lifetimeMicros);
        expect(game.state.toJson()['schema_version'], 4);
        expect(
          game.story.season!.fleet.lifetimeMicros,
          BigInt.zero,
          reason:
              'A newly introduced event cannot invent production before its first saved fleet.',
        );
        await game.save();
        expect(game.saveError, isNull);
        final latest = (await checked(dir).load()).snapshot!;
        final reload = GameController(
          initialState: GameState.fromJson(
            Map<String, dynamic>.from(latest.payload['core']),
          ),
          initialStory: StoryProgress.fromJson(
            Map<String, dynamic>.from(latest.payload['story']),
            seasonDefinition: catalogue.seasonDefinition,
          ),
          catalogue: catalogue,
          settledThrough: latest.settledThrough,
          clock: () => now,
          startTicker: false,
        );
        addTearDown(reload.dispose);
        expect(reload.state.lifetimeMicros, expected.lifetimeMicros);
        expect(reload.state.walletMicros, expected.walletMicros);
      },
    );
  }
}
