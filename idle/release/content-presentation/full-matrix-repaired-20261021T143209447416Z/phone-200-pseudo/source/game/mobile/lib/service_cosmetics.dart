import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'cosmetics.dart';
import 'cosmetics_screen.dart';
import 'game_controller.dart';
import 'native_services.dart';
import 'palette.dart';
import 'soundtrack_export.dart';
import 'package:tideglass_platform/soundtrack_cache.dart';

/// Server ownership and earned XP are independently required. A stored equipped
/// ID, premium claim, store callback or cached product price cannot grant items.
Set<String> verifiedPaidCosmetics(
  NativeServicesManager manager,
  GameController game,
) {
  final entitlements = manager.ownedEntitlementIds;
  final result = <String>{
    for (final item in cosmeticCatalogue)
      if (item.source == CosmeticSource.shop && entitlements.contains(item.id))
        item.id,
  };
  final definition = game.catalogue?.seasonDefinition;
  if (definition != null &&
      game.story.pass != null &&
      entitlements.contains(definition.passId)) {
    final level = game.passEngine!.level(game.state, definition.passId);
    result.addAll(
      definition.rewards
          .where(
            (reward) =>
                reward.track == 'premium' &&
                reward.kind == 'cosmetic' &&
                reward.level <= level,
          )
          .map((reward) => reward.contentId),
    );
  }
  return Set.unmodifiable(result);
}

/// Uses only localized offers actually returned by the native storefront.
/// Supporter purchase requires explicit configuration and a current, validated
/// service capability. The included appearances remain the same four shop IDs.
List<CosmeticStoreOffer> cosmeticStoreOffers(NativeServicesManager manager) {
  if (!manager.commerceAvailable ||
      !manager.recoveryAcknowledged ||
      manager.lastError == 'ownership_verification_unavailable') {
    return const [];
  }
  const inFlight = {
    'opening_store',
    'pending',
    'verifying',
    'pending_verification',
    'verification_pending',
    'delivery_needs_retry',
    'account_recovery_required',
    'verified',
  };
  final owned = manager.ownedEntitlementIds;
  return List.unmodifiable([
    for (final product in manager.offers)
      if (product.price.trim().isNotEmpty &&
          product.title.trim().isNotEmpty &&
          (product.id != 'dev.tideglass.supporter' ||
              (manager.supporterDeliveryReady &&
                  !owned.contains('soundtrack.01'))) &&
          !inFlight.contains(manager.purchaseStates[product.id]) &&
          !(product.id == 'dev.tideglass.pass.01' &&
              owned.contains('pass.01')) &&
          _productCosmetics(product.id).isNotEmpty)
        CosmeticStoreOffer(
          productId: product.id,
          productTitle: product.title,
          localizedPrice: product.price,
          cosmeticIds: _productCosmetics(product.id),
        ),
  ]);
}

Set<String> _productCosmetics(String productId) {
  if (productId == 'dev.tideglass.supporter') {
    return {for (var i = 1; i <= 4; i++) 'cosmetic.shop.0$i'};
  }
  if (productId == 'dev.tideglass.pass.01') {
    return {
      for (final item in cosmeticCatalogue)
        if (item.source == CosmeticSource.premiumPass) item.id,
    };
  }
  for (var i = 1; i <= 4; i++) {
    final suffix = i.toString().padLeft(2, '0');
    if (productId == 'dev.tideglass.cosmetic.$suffix') {
      return {'cosmetic.shop.$suffix'};
    }
  }
  return const {};
}

class CommerceScreen extends StatefulWidget {
  const CommerceScreen({
    super.key,
    required this.game,
    required this.manager,
    this.onExportSoundtrack,
  });
  final GameController game;
  final NativeServicesManager manager;
  final Future<SoundtrackExportResult> Function(NativeServicesManager, Rect)?
  onExportSoundtrack;
  @override
  State<CommerceScreen> createState() => _CommerceScreenState();
}

class _CommerceScreenState extends State<CommerceScreen> {
  bool _working = false;
  String? _message;
  NativeServicesManager get manager => widget.manager;
  GameController get game => widget.game;
  bool get busy => _working || manager.busy;

  Future<void> _run(Future<void> Function() action, String message) async {
    if (busy) return;
    setState(() {
      _working = true;
      _message = null;
    });
    try {
      await action();
      if (mounted) setState(() => _message = message);
    } catch (error) {
      if (mounted) setState(() => _message = _failure(error));
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _purchase(CosmeticStoreOffer offer) async {
    try {
      await manager.buy(offer.productId);
    } catch (error) {
      if (mounted) setState(() => _message = _failure(error));
      rethrow;
    }
  }

  Future<void> _downloadSoundtrack(BuildContext buttonContext) async {
    if (busy) return;
    final box = buttonContext.findRenderObject()! as RenderBox;
    final anchor = box.localToGlobal(Offset.zero) & box.size;
    setState(() {
      _working = true;
      _message = UiEnglish.soundtrackChecking;
    });
    try {
      final result = await (widget.onExportSoundtrack ?? exportSoundtrack)(
        manager,
        anchor,
      );
      if (!mounted) return;
      setState(
        () => _message = switch (result) {
          SoundtrackExportResult.handedOff => UiEnglish.soundtrackHandedOff,
          SoundtrackExportResult.cancelled => UiEnglish.soundtrackCancelled,
          SoundtrackExportResult.unknown => UiEnglish.soundtrackUnknown,
        },
      );
    } on SoundtrackCacheException catch (error) {
      if (mounted) {
        setState(
          () => _message = error.code == 'recent_exports_at_capacity'
              ? UiEnglish.soundtrackCacheFull
              : UiEnglish.soundtrackFailed,
        );
      }
    } catch (_) {
      if (mounted) setState(() => _message = UiEnglish.soundtrackFailed);
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: Listenable.merge([game, manager]),
    builder: (context, _) {
      final owned = {
        ...game.ownedCosmetics,
        ...verifiedPaidCosmetics(manager, game),
      };
      return CosmeticsScreen(
        ownedIds: owned,
        equippedId: owned.contains(game.story.equippedAppearance)
            ? game.story.equippedAppearance
            : null,
        equippedDecorationId: game.story.equippedDecoration,
        onEquip: game.equipCosmetic,
        onUnequipDecoration: game.unequipDecoration,
        onBuyDecoration: game.buyDecoration,
        notes: game.state.surveyNotes > BigInt.from(1000000000)
            ? 1000000000
            : game.state.surveyNotes.toInt(),
        previewCounts: game.state.counts,
        restoration: game.story.campaign.restoredHarbor,
        offers: busy ? const [] : cosmeticStoreOffers(manager),
        onPurchase: _purchase,
        onRestore: manager.commerceAvailable
            ? () async {
                await manager.restorePurchases();
                if (mounted) {
                  setState(
                    () => _message = UiEnglish
                        .serviceRestorationRequestedTheAppStoreMayRespond,
                  );
                }
              }
            : null,
        commerceUnavailableReason: _unavailable,
        servicePanel: _panel(context),
      );
    },
  );

  String get _unavailable {
    if (!manager.configured) {
      return UiEnglish.serviceOnlineServicesAreNotConfiguredInThis2;
    }
    if (!manager.signedIn) {
      return UiEnglish.serviceRecoverOrCreateAnOptionalAccountIn;
    }
    if (!manager.configuration.commerceEnabled) {
      return UiEnglish.serviceStorePurchasesAndRestorationAreNotEnabled;
    }
    if (!manager.recoveryAcknowledged) {
      return UiEnglish.serviceKeepAndConfirmYourAccountRecoveryDetails;
    }
    if (manager.lastError == 'ownership_verification_unavailable') {
      return UiEnglish.serviceOwnershipCouldNotBeVerifiedRefreshWhen;
    }
    if (!manager.commerceAvailable) {
      return UiEnglish.serviceRefreshTheStoreToCheckAvailabilityAnd;
    }
    return UiEnglish.serviceOnlyAvailableStorefrontOffersAreShownPurchases;
  }

  Widget _panel(BuildContext context) => Container(
    key: const ValueKey('commerce-service-panel'),
    margin: const EdgeInsets.only(bottom: 24),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: TideColors.panel,
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: TideColors.line),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        LocalizedText(
          UiEnglish.serviceStoreAndDelivery,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        LocalizedText(
          _unavailable,
          key: const ValueKey('commerce-availability'),
        ),
        if (_message != null)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Semantics(
              liveRegion: true,
              child: LocalizedText(
                _message!,
                key: const ValueKey('commerce-result'),
              ),
            ),
          ),
        if (manager.configured && manager.signedIn) ...[
          const SizedBox(height: 12),
          if (manager.configuration.commerceEnabled)
            OutlinedButton(
              key: const ValueKey('refresh-commerce'),
              onPressed: busy
                  ? null
                  : () => _run(
                      () async {
                        await manager.loadOffers();
                        await manager.refreshOwnership();
                      },
                      UiEnglish
                          .serviceAvailableStorefrontOffersAndCurrentVerifiedOwnership,
                    ),
              child: LocalizedText(
                busy
                    ? UiEnglish.serviceChecking
                    : UiEnglish.serviceRefreshStoreAndOwnership,
              ),
            )
          else
            OutlinedButton(
              key: const ValueKey('refresh-owned-cosmetics'),
              onPressed: busy
                  ? null
                  : () => _run(
                      manager.refreshOwnership,
                      UiEnglish
                          .serviceCurrentOwnershipCheckedWithTheAccountService,
                    ),
              child: const LocalizedText(
                UiEnglish.serviceCheckExistingOwnership,
              ),
            ),
          if (manager.purchaseStates.values.any(
            (value) => {
              'delivery_needs_retry',
              'pending_verification',
              'verification_pending',
              'account_recovery_required',
            }.contains(value),
          ))
            OutlinedButton(
              key: const ValueKey('retry-purchase-delivery'),
              onPressed: busy
                  ? null
                  : () => _run(
                      manager.retryPurchases,
                      UiEnglish
                          .serviceDeliveryRetryRequestedReviewThePurchaseStatus,
                    ),
              child: const LocalizedText(
                UiEnglish.serviceRetryPurchaseDelivery,
              ),
            ),
        ],
        for (final entry in manager.purchaseStates.entries)
          Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                LocalizedText(
                  _productTitle(entry.key),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                LocalizedText(
                  _purchaseState(entry.value),
                  key: ValueKey('purchase-status-${entry.key}'),
                ),
              ],
            ),
          ),
        const SizedBox(height: 16),
        LocalizedText(
          manager.supporterDeliveryReady
              ? UiEnglish.soundtrackReady
              : UiEnglish.soundtrackUnavailable,
          key: const ValueKey('supporter-fulfillment-status'),
        ),
        for (final offer in cosmeticStoreOffers(
          manager,
        ).where((offer) => offer.productId == 'dev.tideglass.supporter'))
          OutlinedButton(
            key: const ValueKey('purchase-supporter-bundle'),
            onPressed: busy
                ? null
                : () => _run(
                    () => _purchase(offer),
                    UiEnglish.serviceWaitingForTheAppStore,
                  ),
            child: LocalizedText(
              UiEnglish.cosmeticStoreOffer(
                offer.productTitle,
                offer.localizedPrice,
              ),
            ),
          ),
        if (manager.ownedEntitlementIds.contains('soundtrack.01'))
          Builder(
            builder: (buttonContext) => OutlinedButton.icon(
              key: const ValueKey('download-soundtrack'),
              onPressed: busy ? null : () => _downloadSoundtrack(buttonContext),
              icon: const Icon(Icons.download_rounded),
              label: const LocalizedText(UiEnglish.soundtrackDownload),
            ),
          ),
        const SizedBox(height: 12),
        const LocalizedText(
          UiEnglish.servicePremiumAppearancesAlsoRequireTheirEarnedPass,
        ),
      ],
    ),
  );

  String _productTitle(String id) {
    for (final product in manager.offers) {
      if (product.id == id) return product.title;
    }
    if (id == 'dev.tideglass.pass.01') {
      return UiEnglish.serviceReturningStarsPremiumAppearances;
    }
    if (id == 'dev.tideglass.supporter') {
      return UiEnglish.serviceSupporterBundle;
    }
    final ids = _productCosmetics(id);
    return ids.length == 1
        ? cosmeticById(ids.single).title
        : UiEnglish.serviceStoreRequest;
  }
}

String _purchaseState(String status) => switch (status) {
  'opening_store' => UiEnglish.serviceWaitingForTheAppStore,
  'not_started' => UiEnglish.serviceTheStoreRequestDidNotStartNothing,
  'pending' => UiEnglish.serviceWaitingForApprovalOrPaymentNothingHas,
  'cancelled' => UiEnglish.serviceCancelledNothingWasAdded,
  'failed' || 'error' => UiEnglish.serviceTheStoreReportedAFailureNothingWas,
  'account_recovery_required' =>
    UiEnglish.serviceRecoverTheAccountToContinueDeliveryAvoid,
  'verifying' => UiEnglish.serviceCheckingThePurchaseWithTheAccountService,
  'pending_verification' || 'verification_pending' =>
    UiEnglish.serviceVerificationIsPendingNoAppearanceHasBeen,
  'delivery_needs_retry' => UiEnglish.serviceDeliveryNeedsARetryAvoidBuyingThe,
  'revoked' => UiEnglish.serviceCurrentStoreVerificationNoLongerGrantsThis,
  'verified' =>
    UiEnglish.servicePurchaseResponseVerifiedAppearancesAreShownOnly,
  _ => UiEnglish.serviceWaitingForAConfirmedStoreStatus,
};

String _failure(Object error) {
  if (error is ServiceException &&
      error.code == 'link_progress_before_purchase') {
    return UiEnglish.serviceLinkThisHarborToYourAccountFirst;
  }
  return UiEnglish.serviceThisRequestCouldNotBeConfirmedCheck;
}
