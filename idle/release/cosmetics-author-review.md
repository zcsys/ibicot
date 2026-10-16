# Cosmetic production and client handoff — 2026-10-16

## Fixed scope

Exactly **36 existing cosmetic identities** have concrete authored vector presentations: six chapter keepsakes, six existing earned decorations, ten free pass appearances, ten premium pass appearances, and four shop appearances. The Supporter Bundle reuses the four shop identities; it creates no fifth shop cosmetic. The soundtrack is owned by the audio lane and is outside these 36 rows.

The catalogue is immutable and its identity set is checked against the launch manifest. All twenty pass appearance names match the pinned authored season content. New core/shop names describe their actual geometry: cairn, suspension bridge, chime station, passage gates, keeper’s desk, floating lanterns, tidal clock, paper boats, coral gardens and festival fireworks.

## Actual art and delivery

`drawCosmetic(Canvas, Size, String id, double phase)` uses the harbor’s 640×388 coordinate system. `CosmeticOverlay` and `CosmeticPreview` both invoke that function, so there is no separate mockup geometry. The pass screen now renders these full harbor previews instead of collection motifs. Setting phase to zero gives the static reduced-motion presentation.

The six existing decorations retain their previous geometry and identities. Other appearances add distinct structures, sails, instrument frames, textile shapes, docks, moorings or sky paths. Differences are structural rather than color substitutions. Every item has an exported transparent overlay and a matched full harbor preview (72 files total) under `game/client/art/cosmetics/`. Runtime delivery is code-native Dart, not a dependency on these review PNGs.

The author inspected all 36 full harbor previews on `release/art/cosmetics-contact-sheet.png`, plus collection and unavailable-store phone captures. Shapes remain inside the harbor and recognizable; no missing cells, obvious clipping or obscured interactive text appeared. The full-screen preview was deliberately used on narrow phones so its “enlarge” action actually provides a larger image than the collection card.

## Collection boundary

`CosmeticsScreen` receives exact owned IDs, general equipped ID, separate equipped decoration ID and parent callbacks. It does not grant or persist ownership. Root wraps it in a controller listener and owns save integration.

- `onEquip(String?)`: select an owned appearance; null removes the general appearance.
- `onUnequipDecoration`: removes the separate earned decoration.
- `onBuyDecoration(String)` and `notes`: expose the existing 50-Note command when affordable.
- `offers: List<CosmeticStoreOffer>`: only adapter-supplied product identity, title, localized price and contained paid cosmetic IDs appear as purchase controls.
- `onPurchase` and `onRestore`: async store delegation with bounded busy/error feedback; neither adds optimistic ownership. Missing adapters show the supplied unavailability reason and no invented price or working purchase/restore button.

The screen supports all/owned/core/free/premium/shop filters, large-text wrapping, 48dp inherited controls and accessible preview labels. A premium preview requires verified ownership and its pass level before it can be supplied in the owned set. Constructing an offer object is never proof of an entitlement.

## Checks and evidence

- **9 cosmetic tests passed**, including exact identity/count/name reconciliation; immutable catalogue/offers; nonempty and distinct actual rendered output for every ID; equip/remove callbacks; unavailable storefront; localized-offer delegation without automatic ownership; restore behavior; decoration affordability; all 36 previews and full-screen presentation at 320px/200% text.
- **12 season interaction tests passed** after replacing all pass motif placeholders with actual appearance previews (**21 combined tests**).
- **2 export/render tests passed**, generating 36 overlays, 36 matched previews and the full contact sheet/phone views.
- Cosmetic implementation, pass changes and cosmetic tests analyze without issues.
- Original authorship and source/export SHA-256 hashes are recorded per asset in `source/provenance/`. Regenerate with `tool/publish_cosmetic_assets.py` after the renderer export test if geometry changes.

All 36 registry rows remain **in_production**. This is the author’s review; independent review fields remain null until another lane checks the result. Native combined-client screenshots, physical accessibility, platform commerce acceptance and root’s persisted ownership/equip integration are separate gates. This handoff does not claim those gates or finished v1.
