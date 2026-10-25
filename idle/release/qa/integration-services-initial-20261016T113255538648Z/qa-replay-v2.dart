import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/offline_replay.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  for (final through in [
    const Duration(minutes: 5),
    const Duration(hours: 120),
  ]) {
    test(
      'QA persisted schema-3 partial replay carries its original cap through ${through.inMinutes} minutes',
      () async {
        final raw =
            jsonDecode(
                  await File(
                    '../core/test/fixtures/state-v3-pending.json',
                  ).readAsString(),
                )
                as Map<String, dynamic>;
        final main = GameState.fromJson(raw);
        final before = jsonEncode(main.toJson());
        final result = await replayOfflineSession(
          main: main,
          story: StoryProgress(),
          catalogue: catalogue,
          settledThrough: epoch.add(const Duration(seconds: 100)),
          now: epoch.add(through),
        );
        final seconds = through.inHours > 72 ? 129600 : 300;
        expect(
          result.main.lifetimeMicros,
          BigInt.from(seconds) * BigInt.from(1000000),
        );
        expect(result.main.support.activeSettlementId, isNull);
        expect(result.main.support.closedSettlementIds, {'opaque-pending'});
        if (through.inHours > 24) {
          expect(result.main.support.tokens, isEmpty);
        } else {
          expect(result.main.support.tokens.single.spent, true);
        }
        expect(jsonEncode(main.toJson()), before);
        final reopened = await replayOfflineSession(
          main: result.main,
          story: result.story,
          catalogue: catalogue,
          settledThrough: result.settledThrough,
          now: result.settledThrough,
        );
        expect(reopened.main.lifetimeMicros, result.main.lifetimeMicros);
        expect(reopened.main.support.toJson(), result.main.support.toJson());
      },
    );
  }
  test('QA zero-duration final typed replay closes exactly once', () async {
    final initial = GameController(
      catalogue: catalogue,
      startTicker: false,
      clock: () => epoch,
    );
    addTearDown(initial.dispose);
    final request = OfflineSettlementRequest(
      sequence: initial.state.nextSettlementSequence,
      fromUtc: epoch,
      throughUtc: epoch.add(const Duration(seconds: 1)),
    );
    final pending = const TideglassEngine()
        .advance(
          initial.state,
          Duration.zero,
          offline: true,
          offlineSettlement: request,
          finalizeOfflineSettlement: false,
        )
        .state;
    final result = await replayOfflineSession(
      main: pending,
      story: initial.story,
      catalogue: catalogue,
      settledThrough: epoch,
      now: epoch,
    );
    expect(result.main.support.activeSettlementId, isNull);
    expect(
      result.main.nextSettlementSequence,
      initial.state.nextSettlementSequence + BigInt.one,
    );
    expect(result.main.lifetimeMicros, pending.lifetimeMicros);
  });
  test(
    'QA century absence yields UI execution and retains the seventy-two-hour production cap',
    () async {
      final initial = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
      );
      addTearDown(initial.dispose);
      final capped = await replayOfflineSession(
        main: initial.state,
        story: initial.story,
        catalogue: catalogue,
        settledThrough: epoch,
        now: epoch.add(const Duration(hours: 72)),
      );
      var heartbeats = 0;
      final timer = Timer.periodic(const Duration(milliseconds: 1), (_) {
        heartbeats++;
      });
      final result = await replayOfflineSession(
        main: initial.state,
        story: initial.story,
        catalogue: catalogue,
        settledThrough: epoch,
        now: DateTime.utc(2126, 10, 16, 12),
        chunk: const Duration(minutes: 17),
      );
      timer.cancel();
      expect(heartbeats, greaterThan(0));
      expect(result.main.lifetimeMicros, capped.main.lifetimeMicros);
      expect(
        result.story.season!.fleet.lifetimeMicros,
        capped.story.season!.fleet.lifetimeMicros,
      );
      expect(result.settledThrough, DateTime.utc(2126, 10, 16, 12));
    },
  );
}
