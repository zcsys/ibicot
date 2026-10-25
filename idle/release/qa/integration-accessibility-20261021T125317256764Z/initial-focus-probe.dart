// Pure-core boundary qualification supplements the UI matrix without a Flutter lane.
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  const engine = TideglassEngine();
  final hour = const Duration(hours: 1).inMicroseconds;
  test('charge boundaries, capacity and later fresh refill have no hidden loss', () {
    final before = engine.advance(GameState.initial(), Duration(microseconds: 2 * hour - 1)).state;
    expect(before.focusCharges, 0);
    final at = engine.advance(before, const Duration(microseconds: 1)).state;
    expect(at.focusCharges, 1);
    final full = engine.advance(at, const Duration(hours: 100)).state;
    expect(full.focusCharges, 12);
    final used = engine.activateFocus(full).state;
    expect(used.focusCharges, 11);
    final justBefore = engine.advance(used, Duration(microseconds: 2 * hour - 1)).state;
    expect(justBefore.focusCharges, 11);
    expect(engine.advance(justBefore, const Duration(microseconds: 1)).state.focusCharges, 12);
  });
  test('queued duration is sequential and exact across submicrosecond-ledger boundaries', () {
    final initial = engine.advance(GameState.initial(), const Duration(hours: 6)).state;
    var state = engine.activateFocus(initial, charges: 3).state;
    expect(state.focusCharges, 0);
    expect(state.focusRemainingMicros, BigInt.from(1800000000));
    expect(engine.activeOutputPerSecond(state).raw,
        engine.outputPerSecond(state).raw * BigInt.from(120) ~/ BigInt.from(100));
    final one = engine.advance(state, const Duration(seconds: 1801)).state;
    state = engine.advance(state, const Duration(microseconds: 1799999999)).state;
    expect(state.focusRemainingMicros, BigInt.one);
    state = engine.advance(state, const Duration(microseconds: 1)).state;
    expect(state.focusRemainingMicros, BigInt.zero);
    expect(engine.activeOutputPerSecond(state).raw, engine.outputPerSecond(state).raw);
    state = engine.advance(state, const Duration(seconds: 1)).state;
    // Revision counts intentionally differ with number of commands.
    for (final field in ['wallet_micros','lifetime_micros','earnings_residue','focus_remaining_micros','focus_phase_micros']) {
      expect(state.toJson().containsKey(field), isTrue, reason: field);
      expect(state.toJson()[field], one.toJson()[field], reason: field);
    }
  });
  test('all twelve IDs have exactly-next reward identity and atomic no-charge rejection', () {
    var state = engine.advance(GameState.initial(), const Duration(hours: 24)).state;
    for (var i = 1; i <= 12; i++) {
      final id = 'calibration.${i.toString().padLeft(2, '0')}';
      final before = state;
      final completed = engine.completeCalibration(before, id, operationSequence: before.nextDiscoverySequence);
      expect(completed.accepted, isTrue);
      state = completed.state;
      expect(state.focusCharges, 12 - i);
      expect(state.focusRemainingMicros, BigInt.from(i * 600000000));
      expect(state.completedCalibrationIds.length, i);
      final retry = engine.completeCalibration(state, id, operationSequence: before.nextDiscoverySequence);
      expect(retry.accepted, isFalse);
      expect(retry.state.toJson(), state.toJson());
    }
    final failed = engine.completeCalibration(state, 'calibration.01');
    expect(failed.accepted, isFalse);
    expect(failed.state.toJson(), state.toJson());
  });
}
