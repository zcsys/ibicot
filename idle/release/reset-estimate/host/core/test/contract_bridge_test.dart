import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';

class TestAlternative implements DailyContractAlternative {
  @override
  final String contractId;
  @override
  final String receiptId;
  final bool complete;
  TestAlternative(this.contractId,
      {this.receiptId = 'test-gameplay-bridge', this.complete = true});
  @override
  bool qualifies(GameState main, DailyContract contract) => complete;
}

void main() {
  const engine = TideglassEngine();
  final now = DateTime.utc(2026, 10, 16, 12);
  GameState ready() => engine
      .refreshContracts(GameState.initial(), now, accountSeed: 'bridge')
      .state;
  test('calendar rollback preserves UTC anchor and next midnight boundary', () {
    final original = ready();
    final rollback = engine
        .refreshContracts(original, now.subtract(const Duration(days: 1)))
        .state;
    expect(rollback.daily.utcAnchorMicros, original.daily.utcAnchorMicros);
    final before = engine
        .advance(rollback, const Duration(hours: 11, minutes: 59, seconds: 59))
        .state;
    expect(before.daily.dayHighWater, original.daily.dayHighWater);
    final midnight = engine.advance(before, const Duration(seconds: 1)).state;
    expect(midnight.daily.dayHighWater, original.daily.dayHighWater + 1);
    expect(midnight.dailyContracts.length, 6);
  });
  test(
      'bridge rejects wrong contract identity, empty receipt and incomplete objective',
      () {
    final state = ready();
    final id = state.dailyContracts.first.id;
    for (final alternative in [
      TestAlternative('wrong'),
      TestAlternative(id, receiptId: ''),
      TestAlternative(id, complete: false)
    ]) {
      final result = engine.claimContract(state, id, alternative: alternative);
      expect(result.accepted, isFalse);
      expect(result.state.toJson(), state.toJson());
    }
  });
  test('alternative and ordinary route share exactly one core reward receipt',
      () {
    final state = ready();
    final id = state.dailyContracts.first.id;
    final claimed =
        engine.claimContract(state, id, alternative: TestAlternative(id));
    expect(claimed.accepted, isTrue);
    expect(claimed.state.passXp, BigInt.from(250));
    expect(claimed.state.surveyNotes, BigInt.from(10));
    expect(claimed.state.lifetimeMicros, BigInt.zero);
    expect(engine.claimContract(claimed.state, id).accepted, isFalse);
    expect(
        engine
            .claimContract(claimed.state, id, alternative: TestAlternative(id))
            .accepted,
        isFalse);
  });
}
