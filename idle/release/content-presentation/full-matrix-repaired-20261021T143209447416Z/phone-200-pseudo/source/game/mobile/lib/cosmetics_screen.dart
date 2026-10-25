import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'cosmetics.dart';
import 'cosmetic_art.dart';
import 'palette.dart';

/// Ownership and equipped selections are supplied by the authoritative parent.
/// Store callbacks never optimistically add ownership in this view.
class CosmeticsScreen extends StatefulWidget {
  CosmeticsScreen({
    super.key,
    required Set<String> ownedIds,
    required this.equippedId,
    required this.onEquip,
    this.equippedDecorationId,
    this.onUnequipDecoration,
    this.onBuyDecoration,
    this.notes = 0,
    List<CosmeticStoreOffer> offers = const [],
    this.onPurchase,
    this.onRestore,
    this.commerceUnavailableReason =
        UiEnglish.cosmeticsPurchasesAndRestorationAreNotAvailableIn,
    this.previewCounts = const [25, 25, 10, 10, 1],
    this.restoration = 6,
    this.servicePanel,
  }) : ownedIds = Set.unmodifiable(ownedIds),
       offers = List.unmodifiable(offers) {
    for (final id in ownedIds) {
      cosmeticById(id);
    }
    if ((equippedId != null && !ownedIds.contains(equippedId)) ||
        (equippedDecorationId != null &&
            !ownedIds.contains(equippedDecorationId))) {
      throw ArgumentError(UiEnglish.cosmeticsOnlyOwnedAppearancesMayBeEquipped);
    }
  }
  final Set<String> ownedIds;
  final String? equippedId, equippedDecorationId;
  final ValueChanged<String?> onEquip;
  final VoidCallback? onUnequipDecoration;
  final ValueChanged<String>? onBuyDecoration;
  final Widget? servicePanel;
  final int notes;
  final List<CosmeticStoreOffer> offers;
  final Future<void> Function(CosmeticStoreOffer)? onPurchase;
  final Future<void> Function()? onRestore;
  final String commerceUnavailableReason;
  final List<int> previewCounts;
  final int restoration;
  @override
  State<CosmeticsScreen> createState() => _CosmeticsScreenState();
}

class _CosmeticsScreenState extends State<CosmeticsScreen> {
  int filter = 0;
  bool busy = false;
  String? feedback;
  final scroll = ScrollController();
  @override
  void dispose() {
    scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = cosmeticCatalogue.where(
      (item) => switch (filter) {
        1 => widget.ownedIds.contains(item.id),
        2 =>
          item.source == CosmeticSource.chapter ||
              item.source == CosmeticSource.decoration,
        3 => item.source == CosmeticSource.freePass,
        4 => item.source == CosmeticSource.premiumPass,
        5 => item.source == CosmeticSource.shop,
        _ => true,
      },
    );
    return Scaffold(
      appBar: readingAppBar(
        context,
        title: UiEnglish.cosmeticsHarborCollection,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          controller: scroll,
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (widget.servicePanel != null) widget.servicePanel!,
                  LocalizedText(
                    UiEnglish.cosmeticsWidgetOwnedIdsLengthOfAppearancesKept(
                      widget.ownedIds.length,
                    ),
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 12),
                  const LocalizedText(
                    UiEnglish
                        .cosmeticsOneHarborAppearanceAndOneEarnedDecoration,
                    style: _muted,
                  ),
                  const SizedBox(height: 18),
                  if (widget.equippedId != null)
                    OutlinedButton(
                      key: const ValueKey('remove-appearance'),
                      onPressed: () => widget.onEquip(null),
                      child: const LocalizedText(
                        UiEnglish.cosmeticsRemoveHarborAppearance,
                      ),
                    ),
                  if (widget.equippedDecorationId != null &&
                      widget.onUnequipDecoration != null)
                    OutlinedButton(
                      key: const ValueKey('remove-collection-decoration'),
                      onPressed: widget.onUnequipDecoration,
                      child: const LocalizedText(
                        UiEnglish.cosmeticsRemoveEarnedDecoration,
                      ),
                    ),
                  if (feedback != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: LocalizedText(
                        feedback!,
                        style: const TextStyle(color: TideColors.amber),
                      ),
                    ),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (var i = 0; i < 6; i++)
                        ChoiceChip(
                          key: ValueKey('cosmetic-filter-$i'),
                          label: LocalizedText(
                            [
                              UiEnglish.cosmeticsAll,
                              UiEnglish.cosmeticsOwned,
                              UiEnglish.cosmeticsCore,
                              UiEnglish.cosmeticsFreePass,
                              UiEnglish.cosmeticsPremium,
                              UiEnglish.cosmeticsShop,
                            ][i],
                          ),
                          selected: filter == i,
                          onSelected: (_) {
                            setState(() => filter = i);
                            scroll.jumpTo(0);
                          },
                        ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  if (filtered.isEmpty)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 24),
                      child: LocalizedText(
                        UiEnglish.cosmeticsYourKeepsakesWillAppearHereAsThe,
                      ),
                    ),
                  for (final item in filtered) _item(item),
                  const SizedBox(height: 8),
                  if (widget.onRestore != null)
                    OutlinedButton(
                      key: const ValueKey('restore-cosmetics'),
                      onPressed: busy ? null : () => _restore(),
                      child: LocalizedText(
                        busy
                            ? UiEnglish.cosmeticsContactingTheStore
                            : UiEnglish.cosmeticsRestorePurchases,
                      ),
                    )
                  else
                    LocalizedText(
                      widget.commerceUnavailableReason,
                      style: _muted,
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _item(CosmeticDefinition item) {
    final owned = widget.ownedIds.contains(item.id);
    final equipped =
        item.id == widget.equippedId || item.id == widget.equippedDecorationId;
    final offers = widget.offers.where(
      (offer) => offer.cosmeticIds.contains(item.id),
    );
    return Container(
      key: ValueKey('collection-${item.id}'),
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: TideColors.panel,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: equipped ? TideColors.teal : TideColors.line),
      ),
      child: Material(
        color: Colors.transparent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Semantics(
              button: true,
              label: Presentation.text(
                UiEnglish.cosmeticsEnlargeItemTitlePreview(
                  Presentation.authored((item.title).toString()),
                ),
              ),
              child: InkWell(
                onTap: () => _preview(item),
                borderRadius: BorderRadius.circular(22),
                child: ExcludeSemantics(
                  child: CosmeticPreview(
                    id: item.id,
                    counts: widget.previewCounts,
                    restoration: widget.restoration,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            LocalizedText(
              item.title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            LocalizedText(item.description, style: _muted),
            const SizedBox(height: 12),
            LocalizedText(
              equipped
                  ? UiEnglish.cosmeticsEquipped
                  : owned
                  ? UiEnglish.cosmeticsKeptInYourCollection
                  : item.unlockLabel,
              style: TextStyle(
                color: owned ? TideColors.teal : TideColors.amber,
              ),
            ),
            const SizedBox(height: 12),
            if (owned && !equipped)
              FilledButton(
                key: ValueKey('equip-${item.id}'),
                onPressed: () => widget.onEquip(item.id),
                child: const LocalizedText(UiEnglish.cosmeticsEquip),
              ),
            if (!owned &&
                item.source == CosmeticSource.decoration &&
                widget.onBuyDecoration != null)
              OutlinedButton(
                key: ValueKey('acquire-${item.id}'),
                onPressed: widget.notes >= 50
                    ? () => widget.onBuyDecoration!(item.id)
                    : null,
                child: const LocalizedText(
                  UiEnglish.cosmeticsKeepDecorationNotes,
                ),
              ),
            if (!owned && item.paid) ...[
              if (offers.isEmpty || widget.onPurchase == null)
                LocalizedText(widget.commerceUnavailableReason, style: _muted)
              else
                for (final offer in offers)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: OutlinedButton(
                      key: ValueKey('purchase-${item.id}-${offer.productId}'),
                      onPressed: busy ? null : () => _purchase(offer),
                      child: LocalizedText(
                        UiEnglish.cosmeticStoreOffer(
                          offer.productTitle,
                          offer.localizedPrice,
                        ),
                      ),
                    ),
                  ),
              if (item.source == CosmeticSource.premiumPass)
                LocalizedText(
                  UiEnglish.cosmeticsVerifiedPassOwnershipAndLevelItemOrdinal(
                    item.ordinal * 3,
                  ),
                  style: _muted,
                ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _preview(CosmeticDefinition item) => showDialog<void>(
    context: context,
    builder: (dialog) => Dialog.fullscreen(
      child: Scaffold(
        appBar: readingAppBar(
          dialog,
          title: item.title,
          leading: CloseButton(onPressed: () => Navigator.pop(dialog)),
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 960),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CosmeticPreview(
                      id: item.id,
                      counts: widget.previewCounts,
                      restoration: widget.restoration,
                      otherDecorationId:
                          item.source == CosmeticSource.decoration
                          ? null
                          : widget.equippedDecorationId,
                    ),
                    const SizedBox(height: 16),
                    LocalizedText(item.description),
                    const SizedBox(height: 20),
                    TextButton(
                      onPressed: () => Navigator.pop(dialog),
                      child: const LocalizedText(
                        UiEnglish.cosmeticsBackToCollection,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  Future<void> _purchase(CosmeticStoreOffer offer) async {
    setState(() {
      busy = true;
      feedback = null;
    });
    try {
      await widget.onPurchase!(offer);
      if (mounted) {
        setState(
          () =>
              feedback = UiEnglish.cosmeticsStoreRequestSentDeliveryMayStillBe,
        );
      }
    } catch (_) {
      if (mounted) {
        setState(
          () =>
              feedback = UiEnglish.cosmeticsTheStoreCouldNotCompleteThisRequest,
        );
      }
    } finally {
      if (mounted) {
        setState(() => busy = false);
        if (scroll.hasClients) scroll.jumpTo(0);
      }
    }
  }

  Future<void> _restore() async {
    setState(() {
      busy = true;
      feedback = null;
    });
    try {
      await widget.onRestore!();
      if (mounted) {
        setState(
          () => feedback =
              UiEnglish.cosmeticsRestorationRequestedTheStoreMayRespondLater,
        );
      }
    } catch (_) {
      if (mounted) {
        setState(
          () => feedback =
              UiEnglish.cosmeticsRestorationCouldNotBeCheckedPleaseTry,
        );
      }
    } finally {
      if (mounted) {
        setState(() => busy = false);
        if (scroll.hasClients) scroll.jumpTo(0);
      }
    }
  }

  static const _muted = TextStyle(
    color: TideColors.muted,
    fontSize: 13,
    height: 1.45,
  );
}
