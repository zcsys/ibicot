import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';

final engine = TideglassEngine();
final million = BigInt.from(1000000);
BigInt r(String whole) => BigInt.parse(whole) * million;
GameState rich({List<int> counts = const [1, 0, 0, 0, 0], BigInt? charts}) =>
    GameState(
        counts: counts,
        walletMicros: r('1000000000000'),
        lifetimeMicros: r('1000000000000'),
        charts: charts);

Map<String, dynamic> withoutRevision(GameState state) =>
    state.toJson()..remove('revision');

void main() {
  final fixture = jsonDecode(
      File('../../implementation/fixtures/economy_reference.json')
          .readAsStringSync()) as Map<String, dynamic>;
  final cases = fixture['cases'] as Map<String, dynamic>;

  group('bounded reference conformance', () {
    for (final dynamic item in cases['cost']) {
      final c = item as Map<String, dynamic>;
      test(c['id'] as String, () {
        final input = c['input'];
        final actual = engine.priceMicros(
            input['tier_index'] as int, input['owned'] as int);
        final expected = (c['expected_cost_radiance'] as num).toDouble();
        // Reference binary64 error grows with magnitude. Settlement differs by
        // less than one micro-R; this tolerance never grants a real purchase.
        expect(actual.toDouble() / 1e6,
            closeTo(expected, 0.0000011 + expected.abs() * 1e-12));
      });
    }
    for (final dynamic item in cases['bulk_cost']) {
      final c = item as Map<String, dynamic>;
      test(c['id'] as String, () {
        final input = c['input'];
        final actual = engine.bulkPriceMicros(input['tier_index'] as int,
            input['owned'] as int, input['quantity'] as int);
        final expected = (c['expected_cost_radiance'] as num).toDouble();
        expect(actual.toDouble() / 1e6,
            closeTo(expected, 0.0000011 + expected.abs() * 1e-12));
      });
    }
    for (final dynamic item in cases['integer_entitlement']) {
      final c = item as Map<String, dynamic>;
      test(c['id'] as String, () {
        final lifetime = BigInt.parse(
                c['input']['lifetime_radiance_integer_string'] as String) *
            million;
        expect(engine.prestigeEntitlement(lifetime),
            BigInt.from(c['expected_charts'] as int));
      });
    }
    for (final dynamic item in cases['milestone']) {
      final c = item as Map<String, dynamic>;
      test(
          c['id'] as String,
          () => expect(engine.milestoneMultiplier(c['input']['owned'] as int),
              c['expected_multiplier']));
    }
    for (final dynamic item in cases['synergy_output']) {
      final c = item as Map<String, dynamic>;
      test(c['id'] as String, () {
        final state = rich(
            counts: List<int>.from(c['input']['counts'] as List),
            charts: BigInt.from(c['input']['charts'] as int));
        final actual = double.parse(
            engine.outputPerSecond(state).toDecimalString(decimals: 12));
        final expected =
            (c['expected']['output_with_synergy'] as num).toDouble();
        expect(actual, closeTo(expected, expected.abs() * 1e-12 + 1e-12));
      });
    }
  });

  group('settlement and commands', () {
    test('original first-run command sequence replays milestone timings', () {
      var state = GameState.initial();
      final expected = (cases['first_run'] as List).single['expected'];
      final firstTierTimes = <int, double>{1: 0};
      var purchases = 0;
      final target = TideglassEngine.firstPrestigeMicros;
      final referenceCommands = expected['purchase_events'] as List;
      while (state.lifetimeMicros < target) {
        if (purchases == referenceCommands.length) {
          final wait = ceilDivide(
              (target - state.lifetimeMicros) * Fixed.scale * BigInt.from(400) -
                  state.earningRemainder,
              engine.outputPerSecond(state).raw * BigInt.from(400));
          state =
              engine.advance(state, Duration(microseconds: wait.toInt())).state;
          break;
        }
        final tier = (referenceCommands[purchases]['tier'] as int) - 1;
        final price = engine.priceMicros(tier, state.counts[tier]);
        if (state.walletMicros >= price) {
          state = engine.buy(state, tier, 1).state;
          purchases++;
          firstTierTimes.putIfAbsent(
              tier + 1, () => state.elapsedMicros.toDouble() / 1e6);
          continue;
        }
        final purchaseWait = engine.waitForPurchase(state, tier)!;
        final neededNumerator =
            (target - state.lifetimeMicros) * Fixed.scale * BigInt.from(400) -
                state.earningRemainder;
        final targetWait = ceilDivide(neededNumerator,
            engine.outputPerSecond(state).raw * BigInt.from(400));
        final duration = targetWait < BigInt.from(purchaseWait.inMicroseconds)
            ? Duration(microseconds: targetWait.toInt())
            : purchaseWait;
        state = engine.advance(state, duration).state;
      }
      expect(state.counts, expected['state']['counts']);
      expect(purchases, expected['purchase_event_count']);
      expect(state.elapsedMicros.toDouble() / 1e6,
          closeTo((expected['state']['time'] as num).toDouble(), 0.001));
      for (final dynamic event in expected['first_tier_events']) {
        expect(firstTierTimes[event['tier']],
            closeTo((event['first_owned_seconds'] as num).toDouble(), 0.001));
      }
      // Exact target stopping rounds time upward to a microsecond; never claim
      // an earlier entitlement by allowing a floating-point epsilon.
      expect(engine.prestigeAward(state), BigInt.from(10));
    });
    test('gift does not create wallet or lifetime', () {
      final state = GameState.initial();
      expect(state.counts, [1, 0, 0, 0, 0]);
      expect(state.walletMicros, BigInt.zero);
      expect(state.lifetimeMicros, BigInt.zero);
      expect(engine.outputPerSecond(state).raw, Fixed.scale);
      expect(engine.priceMicros(0, 1), BigInt.from(33600000));
    });
    test('batch splits settle identically across tiers and milestones', () {
      for (var tier = 0; tier < 5; tier++) {
        for (final owned in [0, 1, 24, 99, 1000]) {
          final combined = engine.bulkPriceMicros(tier, owned, 31);
          final split = engine.bulkPriceMicros(tier, owned, 7) +
              engine.bulkPriceMicros(tier, owned + 7, 24);
          expect(combined, split);
        }
      }
    });
    test('one micro below price cannot buy', () {
      final price = engine.priceMicros(0, 1);
      final state = GameState(
          walletMicros: price - BigInt.one, lifetimeMicros: price - BigInt.one);
      final result = engine.buy(state, 0, 1);
      expect(result.accepted, isFalse);
      expect(identical(result.state, state), isTrue);
      expect(
          engine
              .buy(state.copyWith(walletMicros: price, lifetimeMicros: price),
                  0, 1)
              .accepted,
          isTrue);
    });
    test('locked purchases cannot spend rich wallet', () {
      expect(engine.buy(rich(), 4, 1).accepted, isFalse);
      expect(engine.maximumAffordable(rich(), 4), 0);
    });
    test('max buy proves affordable maximum with exact comparisons', () {
      final state = rich();
      final count = engine.maximumAffordable(state, 0);
      expect(engine.bulkPriceMicros(0, 1, count) <= state.walletMicros, isTrue);
      expect(
          engine.bulkPriceMicros(0, 1, count + 1) > state.walletMicros, isTrue);
      final result = engine.buyMax(state, 0);
      expect(result.state.counts[0], count + 1);
      expect(result.state.lifetimeMicros, state.lifetimeMicros);
      expect(result.state.walletMicros.isNegative, isFalse);
    });
    test('whole-tier milestone jump is included in marginal output', () {
      final state = GameState(counts: [24, 0, 0, 0, 0]);
      expect(engine.marginalOutputPerSecond(state, 0).raw,
          Fixed.scale * BigInt.from(26));
      expect(engine.nextMilestoneQuantity(state, 0), 1);
    });
    test('synergy creates network value for early tiers', () {
      final state =
          rich(counts: [100, 100, 50, 50, 50], charts: BigInt.from(100));
      final network = engine.marginalOutputPerSecond(state, 0);
      final direct =
          engine.prestigeMultiplier(state.charts).raw * BigInt.from(16);
      expect(network.raw > direct * BigInt.from(100), isTrue);
    });
  });

  group('exact prestige and serialization', () {
    test('first gate at exact micro boundary; award is delta, repeat is inert',
        () {
      final below = GameState(
          lifetimeMicros: TideglassEngine.firstPrestigeMicros - BigInt.one);
      expect(engine.rechart(below).accepted, isFalse);
      final state = below.copyWith(
          lifetimeMicros: TideglassEngine.firstPrestigeMicros,
          walletMicros: r('500'),
          focusCharges: 2,
          focusRemainingMicros: million * BigInt.from(30),
          surveyNotes: BigInt.from(20));
      final reset = engine.rechart(state);
      expect(reset.state.charts, BigInt.from(10));
      expect(reset.state.walletMicros, BigInt.zero);
      expect(reset.state.lifetimeMicros, state.lifetimeMicros);
      expect(reset.state.focusCharges, 2);
      expect(reset.state.focusRemainingMicros, state.focusRemainingMicros);
      expect(reset.state.surveyNotes, BigInt.from(20));
      expect(engine.rechart(reset.state).accepted, isFalse);
    });
    test('every next-Chart threshold is exact within one micro', () {
      for (final charts in [10, 24, 25, 99, 100, 1000]) {
        final provisional = GameState(
            charts: BigInt.from(charts),
            lifetimeMicros: r('1000000000000000000'));
        final threshold = engine.nextChartLifetimeMicros(provisional);
        expect(engine.prestigeEntitlement(threshold), BigInt.from(charts + 1));
        expect(engine.prestigeEntitlement(threshold - BigInt.one),
            BigInt.from(charts));
      }
    });
    test('huge lifetime entitlement verified by integer inequalities', () {
      final lifetime = BigInt.from(10).pow(1000) + BigInt.from(12345);
      final charts = engine.prestigeEntitlement(lifetime);
      final rhs = BigInt.from(10).pow(20) * lifetime.pow(13);
      final denominator = TideglassEngine.firstPrestigeMicros.pow(13);
      expect(charts.pow(20) * denominator <= rhs, isTrue);
      expect((charts + BigInt.one).pow(20) * denominator > rhs, isTrue);
    });
    test('large prices remain exact positive integers without double overflow',
        () {
      final price = engine.priceMicros(4, 10000);
      expect(price.bitLength, greaterThan(1024));
      expect(engine.bulkPriceMicros(4, 10000, 2),
          price + engine.priceMicros(4, 10001));
    });
    test('JSON roundtrip preserves quantities beyond 2^53 and remainder', () {
      final state = GameState(
          walletMicros: BigInt.from(10).pow(100),
          lifetimeMicros: BigInt.from(10).pow(101),
          elapsedMicros: BigInt.from(10).pow(30),
          earningRemainder: BigInt.from(123456789));
      final restored = GameState.fromJson(
          jsonDecode(jsonEncode(state.toJson())) as Map<String, dynamic>);
      expect(restored.toJson(), state.toJson());
    });
    test('invalid strings, impossible Charts and unknown versions fail closed',
        () {
      final json = GameState.initial().toJson();
      expect(() => GameState.fromJson({...json, 'wallet_micros': 0.1}),
          throwsFormatException);
      expect(() => GameState.fromJson({...json, 'wallet_micros': '01'}),
          throwsFormatException);
      expect(() => GameState.fromJson({...json, 'schema_version': 999}),
          throwsFormatException);
      expect(() => GameState.fromJson({...json, 'future_field': 'x'}),
          throwsFormatException);
      expect(() => GameState(charts: BigInt.from(100)), throwsArgumentError);
      expect(() => GameState(walletMicros: BigInt.one), throwsArgumentError);
    });
  });

  group('real timeline, returns and timer caps', () {
    test('same duration split into microsteps preserves all earned remainders',
        () {
      final initial =
          GameState(charts: BigInt.from(11), lifetimeMicros: r('2000000000'));
      final whole =
          engine.advance(initial, const Duration(microseconds: 1001)).state;
      var split = initial;
      for (var i = 0; i < 1001; i++) {
        split = engine.advance(split, const Duration(microseconds: 1)).state;
      }
      expect(withoutRevision(split), withoutRevision(whole));
    });
    test('offline envelope earns 24h full plus 48h quarter only', () {
      for (final entry
          in {2: 2, 8: 8, 24: 24, 48: 30, 72: 36, 168: 36}.entries) {
        final after = engine
            .advance(GameState.initial(), Duration(hours: entry.key),
                offline: true)
            .state;
        expect(after.lifetimeMicros, BigInt.from(entry.value * 3600) * million);
        expect(after.focusCharges, entry.key >= 24 ? 12 : entry.key ~/ 2);
        expect(after.completedSurveys, entry.key >= 24 ? 3 : entry.key ~/ 8);
      }
    });
    test('offline chunks carry absence offset across full/tail boundary', () {
      final first = engine
          .advance(GameState.initial(), const Duration(hours: 30),
              offline: true)
          .state;
      final second = engine
          .advance(first, const Duration(hours: 42),
              offline: true, offlineElapsedBefore: const Duration(hours: 30))
          .state;
      final whole = engine
          .advance(GameState.initial(), const Duration(hours: 72),
              offline: true)
          .state;
      expect(withoutRevision(second), withoutRevision(whole));
    });
    test('Focus lasts real ten minutes within quarter-rate tail', () {
      final initial = GameState(focusCharges: 1);
      final active = engine.activateFocus(initial).state;
      final after = engine.advance(active, const Duration(hours: 1),
          offline: true, offlineElapsedBefore: const Duration(hours: 24));
      // Quarter of 600*1.2 + 3000 = 930 R. Expiry is not extended to 40m.
      expect(after.state.lifetimeMicros, r('930'));
      expect(after.state.focusRemainingMicros, BigInt.zero);
      expect(
          after.events
              .where((e) => e.kind == 'focus_expired')
              .single
              .elapsedMicros,
          million * BigInt.from(600));
    });
    test('queues cap, collection is once, cycles resume without manual launch',
        () {
      final full = engine
          .advance(GameState.initial(), const Duration(days: 7), offline: true)
          .state;
      final collected = engine.collectSurveys(full);
      expect(collected.state.surveyNotes, BigInt.from(30));
      expect(engine.collectSurveys(collected.state).accepted, isFalse);
      final later =
          engine.advance(collected.state, const Duration(hours: 8)).state;
      expect(later.completedSurveys, 1);
      expect(later.focusCharges, 12);
      expect(later.focusPhaseMicros, BigInt.zero);
    });
    test('negative elapsed time cannot reduce or increase progress', () {
      final initial = GameState.initial();
      final result = engine.advance(initial, const Duration(seconds: -1));
      expect(result.accepted, isFalse);
      expect(identical(result.state, initial), isTrue);
    });
    test(
        'autobuy is free at ten Charts and identical online/offline through 24h',
        () {
      expect(engine.setAutoBuy(GameState.initial(), true).accepted, isFalse);
      final state = engine
          .setAutoBuy(
              GameState(
                  charts: BigInt.from(10), lifetimeMicros: r('1000000000')),
              true)
          .state;
      final online = engine.advance(state, const Duration(hours: 2)).state;
      final offline =
          engine.advance(state, const Duration(hours: 2), offline: true).state;
      expect(offline.toJson(), online.toJson());
      expect(online.counts[4], greaterThan(0));
    });
    test('autobuy is deterministic across arbitrary replay chunk boundaries',
        () {
      final state = GameState(
          charts: BigInt.from(25),
          lifetimeMicros: r('5000000000'),
          autoBuyEnabled: true);
      final whole = engine.advance(state, const Duration(minutes: 30)).state;
      final a = engine.advance(state, const Duration(seconds: 731)).state;
      final b = engine.advance(a, const Duration(seconds: 1069)).state;
      expect(withoutRevision(b), withoutRevision(whole));
    });
    test('event budget never mutates input state on failure', () {
      final initial = GameState(
          charts: BigInt.from(10),
          lifetimeMicros: r('1000000000'),
          autoBuyEnabled: true);
      final before = initial.toJson();
      expect(
          () => engine.advance(initial, const Duration(hours: 24),
              maximumEvents: 1),
          throwsStateError);
      expect(initial.toJson(), before);
    });
  });
}
