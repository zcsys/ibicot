import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';

void main() {
  test(
    'startup clock sampling never moves calendar ahead of saved production',
    () {
      var now = DateTime.utc(2026, 10, 16, 12);
      DateTime movingClock() {
        now = now.add(const Duration(microseconds: 137));
        return now;
      }

      final first = GameController(startTicker: false, clock: movingClock);
      expect(
        first.state.daily.utcAnchorMicros! + first.state.elapsedMicros,
        BigInt.from(first.settledThrough.microsecondsSinceEpoch),
      );
      first.suspend();
      now = now.add(const Duration(minutes: 5));
      first.resume();
      expect(first.state.support.caches.length, 1);
      expect(
        first.state.daily.utcAnchorMicros! + first.state.elapsedMicros,
        BigInt.from(first.settledThrough.microsecondsSinceEpoch),
      );
      final reopened = GameController(
        initialState: first.state,
        settledThrough: first.settledThrough,
        startTicker: false,
        clock: movingClock,
      );
      first.dispose();
      addTearDown(reopened.dispose);
      reopened.suspend();
      now = now.add(const Duration(minutes: 5));
      reopened.resume();
      expect(reopened.state.support.caches.length, 2);
    },
  );

  test(
    'newly earned Focus becomes available to future daily discovery goals',
    () {
      var now = DateTime.utc(2026, 10, 16, 12);
      final game = GameController(startTicker: false, clock: () => now);
      addTearDown(game.dispose);
      final before = game.state.dailyContracts.map((c) => c.toJson()).toList();
      expect(game.state.daily.availableDiscoveryKinds, ['archive']);
      now = now.add(const Duration(hours: 2));
      game.tick();
      expect(game.state.daily.availableDiscoveryKinds, [
        'archive',
        'calibration',
      ]);
      expect(game.state.dailyContracts.map((c) => c.toJson()).toList(), before);
    },
  );
}
