import 'strings.dart';
import 'package:flutter/foundation.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'game_controller.dart';
import 'native_services.dart';

/// Optional service delivery never uploads a save or replaces a progression
/// branch. Server receipts and local day/slot identities make retries bounded.
class SupportServiceBridge extends ChangeNotifier {
  SupportServiceBridge(this.game, this.manager);
  final GameController game;
  final NativeServicesManager manager;
  bool busy = false, _disposed = false;
  String? message;

  bool _available(int day, int slot) =>
      !_disposed &&
      day == game.state.daily.dayHighWater &&
      slot >= 0 &&
      slot < 6 &&
      (game.state.support.tokenDay != day ||
          !game.state.support.tokens.any((token) => token.slot == slot));

  bool _sameSession(String? account, String? seed) =>
      !_disposed &&
      account != null &&
      manager.session?.accountId == account &&
      game.state.daily.accountSeed == seed;

  Future<void> _perform(Future<void> Function() action) async {
    if (busy || _disposed) return;
    busy = true;
    message = null;
    notifyListeners();
    try {
      await action();
    } catch (_) {
      message = game.saveError != null
          ? UiEnglish.supportYourTokenIsInMemoryButSaving
          : UiEnglish.supportTheServiceCouldNotConfirmDeliveryYour;
    } finally {
      busy = false;
      if (!_disposed) notifyListeners();
    }
  }

  Future<void> _saveLocal() async {
    await game.save();
    if (game.saveError != null) {
      throw StateError(UiEnglish.supportLocalDeliveryIsNotDurable);
    }
  }

  Future<void> completeBriefing(int slot) => _perform(() async {
    final day = game.state.daily.dayHighWater;
    final account = manager.session?.accountId;
    final seed = game.state.daily.accountSeed;
    final generation = manager.client?.sessionGeneration;
    if (!game.completeCrewBriefing(slot)) {
      message = UiEnglish.supportThisSlotIsNoLongerAvailableCheck;
      return;
    }
    await _saveLocal();
    message = UiEnglish.supportYourFreeSupportTokenIsReady;
    if (_sameSession(account, seed) &&
        generation == manager.client?.sessionGeneration &&
        manager.recoveryAcknowledged) {
      // An optional sync failure cannot revoke the free local completion.
      try {
        await manager.client!.claimSupport(
          dayId: day,
          slot: slot,
          route: 'briefing',
        );
      } catch (_) {
        message = UiEnglish.supportYourFreeTokenIsReadyLocallyIts;
      }
    }
  });

  Future<int> _restoreCurrent() async {
    final account = manager.session?.accountId;
    final seed = game.state.daily.accountSeed;
    if (account == null) {
      throw const ServiceException('authentication_required');
    }
    final response = await manager.client!.supportClaims();
    if (!_sameSession(account, seed)) return 0;
    var count = 0;
    for (final value in response['claims'] as List) {
      if (_apply(value)) count++;
    }
    if (count > 0) await _saveLocal();
    return count;
  }

  bool _apply(Object? value) {
    if (_disposed ||
        value is! Map ||
        value['day_id'] is! int ||
        value['slot'] is! int ||
        value['source_id'] is! String ||
        value['route'] is! String ||
        value['receipt_id'] is! String ||
        value['authority'] is! String ||
        (value['receipt_id'] as String).isEmpty ||
        (value['authority'] as String).isEmpty) {
      return false;
    }
    return game.acceptVerifiedSupportReceipt(
      day: value['day_id'] as int,
      slot: value['slot'] as int,
      sourceId: value['source_id'] as String,
      route: value['route'] as String,
    );
  }

  Future<void> restoreClaims() => _perform(() async {
    final restored = await _restoreCurrent();
    message = restored == 0
        ? UiEnglish.supportNoNewCurrentDayTokenWasAvailable
        : UiEnglish.supportRestoredCurrentDaySupportTokenRestoredS(
            restored,
            restored == 1 ? '' : 's',
          );
  });

  Future<void> watchAd(int slot) => _perform(() async {
    if (!manager.adsAvailable || !manager.recoveryAcknowledged) {
      message = UiEnglish.supportOptionalAdsAreUnavailableTheFreeBriefing;
      return;
    }
    final day = game.state.daily.dayHighWater;
    final account = manager.session?.accountId;
    final seed = game.state.daily.accountSeed;
    // Tell the shared allowance about completed free slots before requesting
    // another route. This does not upload economic state or spend a token.
    for (final token in game.state.support.tokens) {
      if (token.accountDay == day && token.route == 'briefing') {
        await manager.client!.claimSupport(
          dayId: day,
          slot: token.slot,
          route: 'briefing',
        );
        if (!_sameSession(account, seed)) return;
      }
    }
    await _restoreCurrent();
    if (!_sameSession(account, seed) || !_available(day, slot)) {
      message = UiEnglish.supportThisSlotIsAlreadyAvailableOrIts;
      return;
    }
    final receipt = await manager.requestRewardedSupport(
      dayId: day,
      slot: slot,
      isStillEligible: () =>
          _sameSession(account, seed) && _available(day, slot),
    );
    if (!_sameSession(account, seed)) return;
    if (receipt != null && _apply(receipt)) {
      await _saveLocal();
      message = UiEnglish.supportOneVerifiedSupportTokenIsReady;
    } else {
      message = UiEnglish.supportNoNewTokenWasConfirmedYouCan;
    }
  });

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
