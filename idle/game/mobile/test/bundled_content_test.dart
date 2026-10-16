import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass/bundled_content.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

class AlteredBundle extends CachingAssetBundle {
  AlteredBundle(this.changedPath);
  final String changedPath;
  @override
  Future<ByteData> load(String key) async {
    final original = await rootBundle.load(key);
    if (key != changedPath) return original;
    final bytes = Uint8List.fromList(
      original.buffer.asUint8List(
        original.offsetInBytes,
        original.lengthInBytes,
      ),
    );
    // Retain byte length: a size-only check must not accept altered rules.
    bytes[bytes.length ~/ 2] ^= 1;
    return ByteData.sublistView(bytes);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('bundled catalogue verifies all pinned gameplay files', () async {
    await verifyBundledContent();
    final manifest =
        jsonDecode(await rootBundle.loadString('assets/config/manifest.json'))
            as Map;
    final files = (manifest['files'] as Map).keys.cast<String>();
    expect(files.length, 29);
    for (final path in ['assets/config/manifest.json', ...files]) {
      await expectLater(
        verifyBundledContent(bundle: AlteredBundle(path)),
        throwsFormatException,
        reason: 'Altered $path must be rejected before loading progress.',
      );
    }
  });

  test('new sessions pin content and prior story versions migrate', () async {
    final catalogue = await StoryCatalogue.load();
    final game = GameController(
      catalogue: catalogue,
      startTicker: false,
      clock: () => DateTime.utc(2026, 10, 16),
    );
    addTearDown(game.dispose);
    expect(game.story.contentDigest, bundledManifestDigest);
    final old = StoryProgress().toJson()
      ..['schema_version'] = 1
      ..remove('season')
      ..remove('pass')
      ..remove('content_digest')
      ..remove('equipped_appearance');
    final migrated = StoryProgress.fromJson(old);
    expect(migrated.campaign.completed, isEmpty);
    final pinned = game.story.toJson()..['content_digest'] = 'f' * 64;
    expect(() => StoryProgress.fromJson(pinned), throwsFormatException);
  });

  test(
    'incompatible newest snapshot never silently rolls back to backup',
    () async {
      final catalogue = await StoryCatalogue.load();
      for (final fault in [
        'client',
        'core',
        'economy',
        'ordering',
        'story',
        'content',
        'season',
      ]) {
        final dir = Directory.systemTemp.createTempSync('tideglass-pinning-');
        addTearDown(() => dir.deleteSync(recursive: true));
        final game = GameController(
          catalogue: catalogue,
          startTicker: false,
          clock: () => DateTime.utc(2026, 10, 16),
        );
        addTearDown(game.dispose);
        Map<String, dynamic> payload() => {
          'client_schema_version': 2,
          'core': game.state.toJson(),
          'story': game.story.toJson(),
          'client_preferences': const ClientPreferences().toJson(),
        };
        final writer = SaveRepository(
          dir,
          economicVersion: economyVersion,
          economicDigest: bundledEconomicDigest,
          validatePayload:
              (_) {}, // Represents a future compatible application.
        );
        await writer.load();
        await writer.save(payload(), settledThrough: game.settledThrough);
        final newer = payload();
        switch (fault) {
          case 'client':
            newer['client_schema_version'] = 999;
          case 'core':
            newer['core']['schema_version'] = 999;
          case 'economy':
            newer['core']['economic_version'] = 'future-economy';
          case 'ordering':
            newer['core']['event_order_version'] = 999;
          case 'story':
            newer['story']['schema_version'] = 999;
          case 'content':
            newer['story']['content_digest'] = 'f' * 64;
          case 'season':
            newer['story']['season']['rules_digest'] = 'f' * 64;
        }
        await writer.save(newer, settledThrough: game.settledThrough);
        final savedFiles = {
          for (final file in dir.listSync().whereType<File>())
            if (file.path.endsWith('.json')) file.path: file.readAsBytesSync(),
        };
        final reader = SaveRepository(
          dir,
          economicVersion: economyVersion,
          economicDigest: bundledEconomicDigest,
          validatePayload: (p) =>
              validateClientPayload(p, catalogue: catalogue),
        );
        await expectLater(
          reader.load(),
          throwsA(isA<IncompatibleSaveException>()),
          reason: '$fault mismatch must preserve the newest generation.',
        );
        for (final entry in savedFiles.entries) {
          expect(File(entry.key).readAsBytesSync(), entry.value);
        }
      }
    },
  );
}
