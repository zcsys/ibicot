// M3-10 collision fixture. Synthetic timestamps/states exercise the production
// event engine; no calendar elapsed, OS-clock or participant evidence is claimed.
import 'dart:convert';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';

const engine = TideglassEngine();
final second = BigInt.from(1000000);

({GameState state, String claimedContract, String oldToken, DateTime midnight})
    fixture(int offset) {
  final midnight =
      DateTime.utc(2026, 10, 17).subtract(Duration(minutes: offset));
  var state = GameState(
    counts: [10, 1, 0, 0, 0],
    walletMicros: BigInt.from(10).pow(12),
    lifetimeMicros: engine.lifetimeForCharts(BigInt.from(105)),
    charts: BigInt.from(100),
    elapsedMicros: second * BigInt.from(599),
    focusPhaseMicros: second * BigInt.from(7199),
    surveyPhaseMicros: second * BigInt.from(28799),
    focusRemainingMicros: second,
    support: SupportState(remainingMicros: second),
  );
  state = engine
      .refreshContracts(state, midnight.subtract(const Duration(seconds: 1)),
          accountSeed: 'boundary-collision', utcOffsetMinutes: offset)
      .state;
  var contract = state.dailyContracts.first;
  if (contract.kind != 'build') {
    final reroll = engine.rerollContract(state, contract.id);
    expect(reroll.accepted, isTrue);
    state = reroll.state;
    contract = state.dailyContracts.first;
  }
  expect(contract.kind, 'build');
  final purchase = engine.buy(state, 0, contract.target.toInt());
  expect(purchase.accepted, isTrue);
  final claim = engine.claimContract(purchase.state, contract.id);
  expect(claim.accepted, isTrue);
  state = claim.state;
  final grant = engine.claimSupportToken(state,
      accountDay: state.daily.dayHighWater,
      slot: 0,
      sourceId: engine.briefingSourceId(state, 0));
  expect(grant.accepted, isTrue);
  state = grant.state;
  final oldToken = state.support.tokens.single.id;
  state = engine
      .saveAutomationPlan(
          state,
          AutomationPlan(
            id: 'plan.base',
            name: 'Boundary fixture',
            autoResetEnabled: true,
            minimumAdditionalCharts: BigInt.from(5),
            minimumRunSeconds: 600,
          ))
      .state;
  expect(state.rechartCount, 0);
  expect(state.surveyNotes, BigInt.from(10));
  expect(state.daily.passXpById['pass.01'], BigInt.from(250));
  return (
    state: state,
    claimedContract: contract.id,
    oldToken: oldToken,
    midnight: midnight
  );
}

Map<String, dynamic> economicState(GameState state) =>
    state.toJson()..remove('revision');
List<Map<String, dynamic>> eventValues(List<CoreEvent> events) =>
    events.map((event) => event.toJson()..remove('id')).toList();

void main() {
  for (final offset in [0, 180]) {
    for (final offline in [false, true]) {
      test(
          'Rechart collides with midnight and timers offset=$offset offline=$offline',
          () {
        final f = fixture(offset), initial = f.state;
        final oldDay = initial.daily.dayHighWater;
        final oldContracts =
            initial.dailyContracts.map((c) => c.toJson()).toList();
        final oldRate = engine.outputPerSecond(initial).raw;
        final earnedBeforeReset = oldRate *
            BigInt.from(145) *
            second ~/
            (Fixed.scale * BigInt.from(100));
        final justBefore = engine.advance(
            initial, const Duration(microseconds: 999999),
            offline: offline);
        expect(justBefore.state.rechartCount, 0);
        expect(justBefore.state.daily.dayHighWater, oldDay);
        expect(justBefore.state.focusCharges, 0);
        expect(justBefore.state.completedSurveys, 0);
        expect(justBefore.events, isEmpty);
        final collision = engine.advance(initial, const Duration(seconds: 1),
            offline: offline);
        final after = collision.state;
        expect(collision.events.map((event) => event.kind), [
          'focus_expired',
          'support_expired',
          'focus_generated',
          'survey_completed',
          'account_day_advanced',
          'rechart',
        ]);
        expect(collision.events.map((event) => event.elapsedMicros),
            everyElement(second * BigInt.from(600)));
        expect(collision.events.last.details['awarded_charts'], '5');
        expect(after.charts, BigInt.from(105));
        expect(after.rechartCount, 1);
        expect(after.lastRechartElapsedMicros, second * BigInt.from(600));
        expect(after.counts, [1, 0, 0, 0, 0]);
        expect(after.walletMicros, BigInt.zero);
        expect(
            after.lifetimeMicros, initial.lifetimeMicros + earnedBeforeReset);
        expect(after.focusCharges, 1);
        expect(after.completedSurveys, 1);
        expect(after.focusRemainingMicros, BigInt.zero);
        expect(after.supportRemainingMicros, BigInt.zero);
        expect(after.focusPhaseMicros, BigInt.zero);
        expect(after.surveyPhaseMicros, BigInt.zero);
        expect(after.daily.dayHighWater, oldDay + 1);
        expect(after.support.tokens, isEmpty);
        expect(engine.useSupportBoost(after, f.oldToken).accepted, isFalse);
        final oldDayGrant = engine.claimSupportToken(after,
            accountDay: oldDay,
            slot: 1,
            sourceId: engine.briefingSourceId(initial, 1));
        expect(oldDayGrant.accepted, isFalse);
        expect(oldDayGrant.reason, 'support_account_day_mismatch');
        expect(oldDayGrant.state.toJson(), after.toJson());
        expect(after.surveyNotes, initial.surveyNotes);
        expect(after.daily.passXpById, initial.daily.passXpById);
        expect(
            after.dailyContracts
                .where((c) => c.accountDay == oldDay)
                .map((c) => c.toJson())
                .toList(),
            oldContracts);
        expect(
            engine.claimContract(after, f.claimedContract).accepted, isFalse);
        final surveys = engine.collectSurveys(after);
        expect(surveys.accepted, isTrue);
        expect(surveys.state.surveyNotes, BigInt.from(20));
        expect(engine.collectSurveys(surveys.state).accepted, isFalse);
        expect(surveys.state.daily.passXpById, initial.daily.passXpById);
        var returned = after;
        if (offline) {
          expect(after.dailyContracts.length, 3);
          returned = engine.refreshContracts(after, f.midnight).state;
        }
        final newContracts = returned.dailyContracts
            .where((c) => c.accountDay == oldDay + 1)
            .toList();
        expect(newContracts.length, 3);
        // Online midnight snapshots precede reset; offline assignment is at
        // return after reset. This intentional distinction must stay visible.
        final snapshotRate =
            offline ? engine.outputPerSecond(after).raw : oldRate;
        for (final contract in newContracts) {
          expect(contract.rateSnapshotRaw, snapshotRate);
          expect(contract.lifetimeBaselineMicros, after.lifetimeMicros);
          expect(contract.purchasedBaseline, initial.lifetimePurchasedCount);
          expect(contract.claimed, isFalse);
        }
        final whole = engine.advance(initial, const Duration(seconds: 2),
            offline: offline);
        final boundaryPart = engine.advance(
            justBefore.state, const Duration(microseconds: 1),
            offline: offline,
            offlineElapsedBefore: const Duration(microseconds: 999999));
        final tail = engine.advance(
            boundaryPart.state, const Duration(seconds: 1),
            offline: offline, offlineElapsedBefore: const Duration(seconds: 1));
        expect(economicState(boundaryPart.state), economicState(after));
        expect(economicState(tail.state), economicState(whole.state));
        expect(
            eventValues(
                [...justBefore.events, ...boundaryPart.events, ...tail.events]),
            eventValues(whole.events));
        final repeated = engine.advance(tail.state, Duration.zero,
            offline: offline, offlineElapsedBefore: const Duration(seconds: 2));
        expect(economicState(repeated.state), economicState(tail.state));
        expect(repeated.events, isEmpty);
        expect(engine.claimContract(repeated.state, f.claimedContract).accepted,
            isFalse);
        print('MIDNIGHT_RECHART ${jsonEncode({
              'offset_minutes': offset,
              'offline': offline,
              'events': eventValues(collision.events),
              'earned_before_reset_micros': earnedBeforeReset.toString(),
              'charts': after.charts.toString(),
              'notes': after.surveyNotes.toString(),
              'pass_xp': after.daily.passXpById['pass.01'].toString(),
              'new_contract_snapshot':
                  '${offline ? 'return_after_reset' : 'midnight_before_reset'}',
              'whole_split_equal': true,
              'receipt_replay_rejected': true
            })}');
      });
    }
  }
}
