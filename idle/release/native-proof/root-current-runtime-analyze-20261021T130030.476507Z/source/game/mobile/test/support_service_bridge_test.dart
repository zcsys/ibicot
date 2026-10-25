import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/support_service_bridge.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

class ClaimsClient extends TideglassServiceClient {
  ClaimsClient() : super(endpoint: Uri.parse('https://example.invalid'));
  final claims = <Map<String, dynamic>>[];
  bool fail = false;
  int briefingCalls = 0;
  Completer<void>? gate;
  @override
  Future<Map<String, dynamic>> supportClaims() async {
    if (gate != null) await gate!.future;
    if (fail) throw const ServiceException('service_unavailable');
    return {'claims': claims};
  }

  @override
  Future<Map<String, dynamic>> claimSupport({
    required int dayId,
    required int slot,
    required String route,
    String? proof,
  }) async {
    briefingCalls++;
    if (fail) throw const ServiceException('service_unavailable');
    return {};
  }
}

class ClaimsManager extends NativeServicesManager {
  ClaimsManager(ClaimsClient client) : super(client: client);
  int adRequests = 0;
  Map<String, dynamic>? adResult;
  @override
  bool get adsAvailable => signedIn;
  @override
  Future<Map<String, dynamic>?> requestRewardedSupport({
    required int dayId,
    required int slot,
    bool Function()? isStillEligible,
  }) async {
    if (isStillEligible?.call() == false) return null;
    adRequests++;
    return adResult;
  }
}

void main() {
  late GameController game;
  late ClaimsClient client;
  late ClaimsManager manager;
  late SupportServiceBridge bridge;
  setUp(() {
    game = GameController(
      startTicker: false,
      clock: () => DateTime.utc(2026, 10, 16, 12),
    );
    client = ClaimsClient();
    manager = ClaimsManager(client)..recoveryAcknowledged = true;
    bridge = SupportServiceBridge(game, manager);
  });
  tearDown(() {
    bridge.dispose();
    manager.dispose();
    client.close();
    game.dispose();
  });
  void signIn([String account = 'account-one']) {
    client.session = ServiceSession(
      accountId: account,
      token: 'test-only',
      expiresAt: DateTime.utc(2030),
    );
    manager.recoveryAcknowledged = true;
  }

  Map<String, dynamic> receipt(int slot, {String? seed, int? day}) {
    final actualDay = day ?? game.state.daily.dayHighWater;
    return {
      'day_id': actualDay,
      'slot': slot,
      'route': 'ad',
      'receipt_id': 'test-receipt-$slot',
      'authority': 'test-only-verifier',
      'source_id':
          'ad:${seed ?? game.state.daily.accountSeed}:$actualDay:$slot:${'a' * 64}',
    };
  }

  test(
    'guest briefings grant exactly six shared slots without network',
    () async {
      for (var slot = 0; slot < 6; slot++) {
        await bridge.completeBriefing(slot);
      }
      await bridge.completeBriefing(0);
      expect(game.state.support.tokens.length, 6);
      expect(client.briefingCalls, 0);
      expect(manager.adRequests, 0);
    },
  );
  test('service outage cannot deny the equal free reward', () async {
    signIn();
    client.fail = true;
    await bridge.completeBriefing(0);
    expect(game.state.support.tokens.length, 1);
    expect(bridge.message, contains('ready locally'));
    expect(game.state.support.tokens.single.route, 'briefing');
  });
  test(
    'failed local commit reports pending durability before account sync',
    () async {
      signIn();
      bridge.dispose();
      game.dispose();
      game = GameController(
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 16, 12),
        onPersist: (_, _) async => throw StateError('disk unavailable'),
      );
      bridge = SupportServiceBridge(game, manager);
      await bridge.completeBriefing(0);
      expect(game.state.support.tokens.length, 1);
      expect(game.saveError, isNotNull);
      expect(bridge.message, contains('saving has not finished'));
      expect(client.briefingCalls, 0);
    },
  );
  test(
    'authenticated replay cannot replace or re-spend a delivered token',
    () async {
      signIn();
      client.claims.add(receipt(0));
      await bridge.restoreClaims();
      final token = game.state.support.tokens.single;
      expect(game.useSupportBoost(token.id), isTrue);
      final remaining = game.state.support.remainingMicros;
      await bridge.restoreClaims();
      expect(game.state.support.tokens.length, 1);
      expect(game.state.support.tokens.single.spent, isTrue);
      expect(game.state.support.remainingMicros, remaining);
      expect(game.useSupportBoost(token.id), isFalse);
    },
  );
  test(
    'wrong seed, old day, invalid slot and malformed receipt grant nothing',
    () async {
      signIn();
      client.claims.addAll([
        receipt(0, seed: 'different-harbor'),
        receipt(1, day: game.state.daily.dayHighWater - 1),
        receipt(6),
        receipt(2)..remove('authority'),
      ]);
      await bridge.restoreClaims();
      expect(game.state.support.tokens, isEmpty);
    },
  );
  test(
    'response from a signed-out account is discarded after an await',
    () async {
      signIn();
      client.claims.add(receipt(0));
      client.gate = Completer<void>();
      final pending = bridge.restoreClaims();
      signIn('account-two');
      client.gate!.complete();
      await pending;
      expect(game.state.support.tokens, isEmpty);
    },
  );
  test('no-fill preserves the slot for an equal free briefing', () async {
    signIn();
    await bridge.watchAd(0);
    expect(manager.adRequests, 1);
    expect(game.state.support.tokens, isEmpty);
    await bridge.completeBriefing(0);
    expect(game.state.support.tokens.length, 1);
  });
  test(
    'recovered shared slot prevents an unnecessary ad, with no wallet reward',
    () async {
      signIn();
      client.claims.add(receipt(0));
      final wallet = game.state.walletMicros;
      await bridge.watchAd(0);
      expect(manager.adRequests, 0);
      expect(game.state.support.tokens.length, 1);
      expect(game.state.walletMicros, wallet);
    },
  );
  test('new verified ad token and repeated callbacks use one slot', () async {
    signIn();
    manager.adResult = receipt(0);
    await bridge.watchAd(0);
    expect(game.state.support.tokens.length, 1);
    await bridge.watchAd(0);
    expect(manager.adRequests, 1);
    expect(game.state.support.tokens.length, 1);
  });
}
