enum CosmeticSource { chapter, decoration, freePass, premiumPass, shop }

class CosmeticDefinition {
  const CosmeticDefinition(
    this.id,
    this.title,
    this.description,
    this.source,
    this.ordinal,
  );
  final String id, title, description;
  final CosmeticSource source;
  final int ordinal;
  bool get paid =>
      source == CosmeticSource.premiumPass || source == CosmeticSource.shop;
  String get unlockLabel => switch (source) {
    CosmeticSource.chapter => 'Restore chapter $ordinal',
    CosmeticSource.decoration => '50 Survey Notes',
    CosmeticSource.freePass => 'Free pass · level ${ordinal * 3}',
    CosmeticSource.premiumPass => 'Premium pass · level ${ordinal * 3}',
    CosmeticSource.shop => 'Optional store appearance',
  };
}

/// Exactly the approved 12 core / 10 free / 10 premium / 4 shop identities.
const cosmeticCatalogue = <CosmeticDefinition>[
  CosmeticDefinition(
    "cosmetic.core.chapter.01",
    "First Light Cairn",
    "A stone bearing and folded pennant beside the first beacon.",
    CosmeticSource.chapter,
    1,
  ),
  CosmeticDefinition(
    "cosmetic.core.chapter.02",
    "Shared Horizon Bridge",
    "A suspension footbridge links the lights above the water.",
    CosmeticSource.chapter,
    2,
  ),
  CosmeticDefinition(
    "cosmetic.core.chapter.03",
    "Quiet Watch Chimes",
    "A watch station carries brass chimes through the evening.",
    CosmeticSource.chapter,
    3,
  ),
  CosmeticDefinition(
    "cosmetic.core.chapter.04",
    "Three Passage Gates",
    "Three open arches mark the routes you have charted.",
    CosmeticSource.chapter,
    4,
  ),
  CosmeticDefinition(
    "cosmetic.core.chapter.05",
    "Keeper’s Desk",
    "An open chart, ink bottle and feather remember the keeper’s work.",
    CosmeticSource.chapter,
    5,
  ),
  CosmeticDefinition(
    "cosmetic.core.chapter.06",
    "Sea of Stars Lanterns",
    "Six floating lanterns rise above the restored harbor.",
    CosmeticSource.chapter,
    6,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.01",
    "Beacon pennants",
    "A light strand of folded flags follows the beacon’s curve.",
    CosmeticSource.decoration,
    1,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.02",
    "Glass buoys",
    "Seven luminous glass floats drift in the harbor.",
    CosmeticSource.decoration,
    2,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.03",
    "Aurora kite",
    "A two-part kite catches a quiet current above the fleet.",
    CosmeticSource.decoration,
    3,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.04",
    "Tide rings",
    "Concentric ripples trace the moving water.",
    CosmeticSource.decoration,
    4,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.05",
    "Shore garden",
    "A small garden grows among the lighthouse rocks.",
    CosmeticSource.decoration,
    5,
  ),
  CosmeticDefinition(
    "cosmetic.core.decoration.06",
    "Returning comets",
    "Three bright comets leave golden tracks in the night.",
    CosmeticSource.decoration,
    6,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.01",
    "Harbor Lantern",
    "Harbor Lantern changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    1,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.02",
    "Moonwake Hull",
    "Moonwake Hull changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    2,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.03",
    "Starfinder Pennant",
    "Starfinder Pennant changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    3,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.04",
    "Silver Nursery",
    "Silver Nursery changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    4,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.05",
    "Nightcurrent Dynamo",
    "Nightcurrent Dynamo changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    5,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.06",
    "Duskweave Loom",
    "Duskweave Loom changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    6,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.07",
    "Farwatch Dome",
    "Farwatch Dome changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    7,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.08",
    "Meteor Mooring",
    "Meteor Mooring changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    8,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.09",
    "Returning Star Banner",
    "Returning Star Banner changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    9,
  ),
  CosmeticDefinition(
    "cosmetic.free_pass.10",
    "Homeward Sky",
    "Homeward Sky changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.freePass,
    10,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.01",
    "Opal Hull",
    "Opal Hull changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    1,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.02",
    "Constellation Sails",
    "Constellation Sails changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    2,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.03",
    "Blue Hour Nursery",
    "Blue Hour Nursery changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    3,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.04",
    "Comet Dynamo",
    "Comet Dynamo changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    4,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.05",
    "Velvet Night Loom",
    "Velvet Night Loom changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    5,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.06",
    "Aurora Observatory",
    "Aurora Observatory changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    6,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.07",
    "Starpath Dock",
    "Starpath Dock changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    7,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.08",
    "Luminous Compass",
    "Luminous Compass changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    8,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.09",
    "Lantern Constellation",
    "Lantern Constellation changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    9,
  ),
  CosmeticDefinition(
    "cosmetic.premium_pass.10",
    "Celestial Harbor",
    "Celestial Harbor changes the appearance of your harbor collection. It never changes production, storage, Charts or contract targets.",
    CosmeticSource.premiumPass,
    10,
  ),
  CosmeticDefinition(
    "cosmetic.shop.01",
    "Tidal Clock",
    "A pendulum clock tower measures the evening tide.",
    CosmeticSource.shop,
    1,
  ),
  CosmeticDefinition(
    "cosmetic.shop.02",
    "Paper Voyagers",
    "A procession of folded paper boats glides home.",
    CosmeticSource.shop,
    2,
  ),
  CosmeticDefinition(
    "cosmetic.shop.03",
    "Coral Sanctuary",
    "Two branching coral gardens frame the working harbor.",
    CosmeticSource.shop,
    3,
  ),
  CosmeticDefinition(
    "cosmetic.shop.04",
    "Voyager Festival",
    "Firework rosettes and a shore arch celebrate the returning fleet.",
    CosmeticSource.shop,
    4,
  ),
];

CosmeticDefinition cosmeticById(String id) => cosmeticCatalogue.firstWhere(
  (item) => item.id == id,
  orElse: () => throw ArgumentError.value(id, "id", "Unknown cosmetic"),
);

/// Offers are supplied by the platform adapter after it has obtained localized
/// product information. Constructing this value never proves ownership.
class CosmeticStoreOffer {
  CosmeticStoreOffer({
    required this.productId,
    required this.productTitle,
    required this.localizedPrice,
    required Set<String> cosmeticIds,
  }) : cosmeticIds = Set.unmodifiable(cosmeticIds) {
    if ([
          productId,
          productTitle,
          localizedPrice,
        ].any((v) => v.trim().isEmpty) ||
        cosmeticIds.isEmpty ||
        cosmeticIds.any((id) => !cosmeticById(id).paid)) {
      throw ArgumentError(
        "A localized offer needs a real product and known paid contents.",
      );
    }
  }
  final String productId, productTitle, localizedPrice;
  final Set<String> cosmeticIds;
}
