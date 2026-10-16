import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

import '../../game/mobile/lib/game_controller.dart';

void main() {
  test('fractional settlement survives save and immediate reopen without income replay', () async {
    final directory = await Directory('../../.tooling/review-temp')
        .create(recursive: true);
    final temporary = await directory.createTemp('controller-roundtrip-');
    addTearDown(() => temporary.delete(recursive: true));
    final store = SaveRepository(
      temporary,
      economicVersion: economyVersion,
      economicDigest: 'a' * 64,
      validatePayload: (payload) => GameState.fromJson(payload),
    );
    await store.load();
    var now = DateTime.utc(2026, 10, 16, 9);
    final controller = GameController(
      startTicker: false,
      clock: () => now,
      onPersist: (state, boundary) async {
        await store.save(state.toJson(), settledThrough: boundary);
      },
    );
    addTearDown(controller.dispose);
    now = now.add(const Duration(microseconds: 1750123));
    controller.tick();
    await controller.save();
    final snapshot = (await store.load()).snapshot!;
    expect(snapshot.settledThrough, now);
    final reopened = GameController(
      startTicker: false,
      clock: () => now,
      initialState: GameState.fromJson(snapshot.payload),
      settledThrough: snapshot.settledThrough,
    );
    addTearDown(reopened.dispose);
    expect(reopened.state.toJson(), controller.state.toJson());
  });

  test('suspended ticks cannot replace the real offline interval with online credit', () {
    var now = DateTime.utc(2026, 10, 16, 9);
    final controller = GameController(startTicker: false, clock: () => now);
    addTearDown(controller.dispose);
    controller.suspend();
    now = now.add(const Duration(hours: 48));
    controller.tick();
    expect(controller.state.lifetimeMicros, BigInt.zero);
    controller.resume();
    expect(controller.state.lifetimeMicros, BigInt.from(30 * 3600 * 1000000));
    final afterResume = controller.state.toJson();
    controller.resume();
    expect(controller.state.toJson(), afterResume);
  });

  test('queued snapshots preserve order through a failed write and recover with current cursor', () async {
    var now = DateTime.utc(2026, 10, 16, 9);
    final saved = <(BigInt, DateTime)>[];
    var attempts = 0;
    final controller = GameController(
      startTicker: false,
      clock: () => now,
      onPersist: (state, boundary) async {
        if (++attempts == 1)
          throw const FileSystemException('injected failure');
        saved.add((state.lifetimeMicros, boundary));
      },
    );
    addTearDown(controller.dispose);
    now = now.add(const Duration(milliseconds: 1250));
    controller.tick();
    await controller.save();
    expect(controller.saveError, isNotNull);
    now = now.add(const Duration(milliseconds: 1750));
    controller.tick();
    await controller.save();
    expect(controller.saveError, isNull);
    expect(saved.single, (BigInt.from(3000000), now));
  });
}
