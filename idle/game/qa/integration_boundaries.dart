import 'dart:convert';
import 'dart:io';

import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';

// Independent executable economic boundary checks. Clocks and verified-reader
// inputs are test fixtures; this provides no native ad/store/user evidence.
const core = TideglassEngine();
final epoch = DateTime.utc(2026, 10, 16, 12);
final checks = <String>[];
void check(bool condition, String label) {
  if (!condition) throw StateError(label);
  checks.add(label);
}

BigInt r(int value) => BigInt.from(value) * BigInt.from(1000000);
GameState initial(String account) => core
    .refreshContracts(
      GameState.initial(),
      epoch,
      accountSeed: account,
      availableDiscoveryKinds: ['archive'],
    )
    .state;

class NoEntitlements implements VerifiedPassEntitlementReader {
  @override
  Future<VerifiedPassEntitlement?> read({
    required String accountId,
    required String passId,
  }) async => null;
}

Future<void> main() async {
  final definition = SeasonDefinition.fromJson(
    jsonDecode(File('game/events/content/season.01.json').readAsStringSync())
        as Map<String, dynamic>,
  );
  final seasons = SeasonEngine(definition);
  final passes = PassEngine([definition]);

  GameState withDailySupport(String route) {
    var state = initial('parity').copyWith(focusCharges: 12);
    state = core.activateFocus(state, charges: 12).state;
    for (var slot = 0; slot < 6; slot++) {
      final source = route == 'briefing'
          ? core.briefingSourceId(state, slot)
          : core.adSupportSourceId(
              state,
              slot,
              slot.toString().padLeft(64, '0'),
            );
      final grant = core.claimSupportToken(
        state,
        accountDay: state.daily.dayHighWater,
        slot: slot,
        sourceId: source,
        route: route,
      );
      check(grant.accepted, '$route grants shared slot $slot');
      state = grant.state;
      final token = state.support.tokens.last.id;
      final use = core.useSupportBoost(state, token);
      check(use.accepted, '$route spends shared slot $slot');
      state = use.state;
      check(
        !core.useSupportBoost(state, token).accepted,
        '$route rejects duplicate consume $slot',
      );
    }
    check(
      !core
          .claimSupportToken(
            state,
            accountDay: state.daily.dayHighWater,
            slot: 0,
            sourceId: core.briefingSourceId(state, 0),
          )
          .accepted,
      '$route cannot refill spent slot via briefing',
    );
    return state;
  }

  var free = withDailySupport('briefing');
  var ad = withDailySupport('ad');
  for (final duration in [
    const Duration(seconds: 1),
    const Duration(seconds: 7199),
    const Duration(hours: 22),
  ]) {
    free = core.advance(free, duration).state;
    ad = core.advance(ad, duration).state;
    check(
      free.walletMicros == ad.walletMicros &&
          free.lifetimeMicros == ad.lifetimeMicros &&
          free.earningRemainder == ad.earningRemainder,
      'free/ad economic parity after ${free.elapsedMicros} microseconds',
    );
    if (free.elapsedMicros == BigInt.from(1000000))
      check(
        free.walletMicros == r(1) + BigInt.from(450000),
        'Focus+Support is exactly1.45 on firstsecond',
      );
  }
  check(
    free.lifetimeMicros == r(89640),
    'daily earnings equal86400base+1440Focus+1800Support',
  );

  var main = initial('free-pass');
  var pass = PassState.initial([definition]);
  var season = SeasonState.initial(
    definition,
    SeasonSchedule(epoch),
    epoch,
    runId: 'qa:free-pass',
  );
  for (var day = 0; day < 20; day++) {
    final start = epoch.add(Duration(days: day));
    if (day > 0) season = seasons.advanceTo(season, start, offline: true).state;
    main = core
        .refreshContracts(main, start, availableDiscoveryKinds: ['archive'])
        .state;
    final today = main.dailyContracts
        .where((c) => c.accountDay == main.daily.dayHighWater)
        .toList();
    check(today.length == 3, 'day${day + 1} offers3daily slots');
    for (final contract in today) {
      final bound = passes.bindEventAlternative(
        main,
        pass,
        contract.id,
        season,
      );
      check(
        bound.accepted,
        'day${day + 1} binds${contract.slot} withoutpayment',
      );
      pass = bound.pass;
    }
    season = seasons
        .advanceTo(season, start.add(const Duration(minutes: 10)))
        .state;
    main = core.advance(main, const Duration(minutes: 10)).state;
    for (final contract in today) {
      final claimed = passes.claimDaily(
        main,
        pass,
        contract.id,
        alternativeSeason: season,
      );
      check(claimed.accepted, 'day${day + 1} earns sharedslot${contract.slot}');
      main = claimed.main;
      pass = claimed.pass;
      check(
        !core.claimContract(main, contract.id).accepted,
        'day${day + 1} mainroute cannot duplicate${contract.slot}',
      );
    }
    for (final reward in definition.rewards.where(
      (r) =>
          r.track == 'free' && r.level <= passes.level(main, definition.passId),
    )) {
      if (pass.claims.containsKey(reward.id)) continue;
      final claimed = passes.claimFreeReward(
        main,
        pass,
        definition.passId,
        reward.id,
      );
      check(claimed.accepted, 'free reward${reward.id} claim reachable');
      pass = claimed.pass;
    }
    main = GameState.fromJson(main.toJson());
    pass = PassState.fromJson(pass.toJson(), [definition]);
    season = SeasonState.fromJson(season.toJson(), definition);
    passes.validate(pass, main: main);
  }
  check(
    main.daily.passXpById[definition.passId] == BigInt.from(15000),
    '60freecontracts grant exactly15000XP',
  );
  check(
    passes.level(main, definition.passId) == 30,
    'freepass reaches level30',
  );
  check(
    main.surveyNotes == BigInt.from(600),
    '60contracts grant exactly600Notes',
  );
  check(pass.claims.length == 30, 'all30free slots are retained once');
  check(passes.cosmeticIds(pass).length == 10, 'ten freecosmetics reachable');
  check(
    passes.fragmentIds(pass).length == 20,
    'twenty archivefragments reachable',
  );
  check(
    (await passes.verifiedCosmeticIds(
          main,
          pass,
          entitlementReader: NoEntitlements(),
        )).length ==
        10,
    'missingindependentownership grantsnopremium',
  );
  final premium = definition.rewards.firstWhere((r) => r.track == 'premium');
  check(
    !(await passes.claimPremiumReward(
      main,
      pass,
      definition.passId,
      premium.id,
      entitlementReader: NoEntitlements(),
    )).accepted,
    'premium claim refuses unverifiedownership',
  );
  check(
    season.fleet.asCore.charts == BigInt.zero &&
        season.fleet.asCore.surveyNotes == BigInt.zero &&
        season.fleet.asCore.focusCharges == 0,
    'seasonfleet keeps all mainpower out',
  );
  check(!seasons.rechart(season).accepted, 'season has noRechart');
  stdout.writeln(
    const JsonEncoder.withIndent('  ').convert({
      'reviewer': '/root/qa_integration',
      'kind': 'independent accelerated local economic evidence',
      'observed_utc': DateTime.now().toUtc().toIso8601String(),
      'checks_passed': checks.length,
      'checks': checks,
      'route_parity_24h_lifetime_micros': free.lifetimeMicros.toString(),
      'free_pass': {
        'days_simulated': 20,
        'contracts_claimed': 60,
        'xp': main.daily.passXpById[definition.passId].toString(),
        'level': 30,
        'cosmetics': 10,
        'fragments': 20,
      },
      'limits': [
        'No real ad callback or receipt verification',
        'No physical-device performance',
        'No real20day player observation',
        'Full30/90day balance trajectories remain separate',
      ],
    }),
  );
}
