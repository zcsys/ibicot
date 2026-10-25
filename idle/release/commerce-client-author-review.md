# Verified cosmetic store presentation — author handoff

2026-10-16. Client implementation is ready for independent review and root integration. This evidence does not establish live app-store or deployed provider acceptance.

## Implemented contract

- `verifiedPaidCosmetics(NativeServicesManager manager, GameController game)` returns an immutable set. Shop appearances require current manager-verified IDs. Premium appearances require both the matching verified pass entitlement and the earned level in the actual authored reward table. It never consults saved premium-claim flags, a stored appearance preference, product metadata, or purchase callback success as proof.
- The manager owns account/harbor-seed/session binding and verification expiry. Account mismatch, expired observations and failed refresh remove the projection; an equipped preference does not bypass it. Soundtrack and unknown IDs never become appearances.
- `CommerceScreen({required game, required manager})` wraps the actual `CosmeticsScreen`. Its optional `servicePanel` keeps availability, refresh, retry and per-product delivery status inside the same scroll view. It supplies actual localized prices/titles returned by the native storefront and maps only the fixed product IDs.
- Opening a purchase, pending payment, restore request and retry are all described as pending work. None grants ownership. In-flight purchases suppress repeated purchase offers. Confirmed server ownership makes an earned appearance available through the existing controller equip command.
- The supporter product reuses the four existing shop IDs. Its purchase/price is withheld until authenticated soundtrack delivery exists. Previously verified appearances still work; there is no invented download.
- `SeasonScreen` adds an optional `NativeServicesManager? services` parameter. It links to the actual collection/store panel and distinguishes verified earned premium appearances from previews and future level requirements. No async premium claim is written to gameplay state.
- The default unconfigured build provides earned collection controls and an explicit unavailable-service explanation, without fake prices or purchase actions.

## Verification

`../../tool/flutter test test/service_cosmetics_test.dart test/cosmetics_test.dart test/season_ui_test.dart` — **29 passed** (8 new commerce cases, 9 collection cases, 12 seasonal cases).

The new cases check: exact pass-level thresholds and server/harbor binding; 14 maximum paid appearances without extra supporter assets; expired observations; actual returned localized metadata; withheld supporter; unconfigured guest rendering; pending purchase without grant or repeat offer; failed delivery retry without repurchase; verified equip and removal on failed ownership refresh; restore request without a grant; and seasonal earned premium presentation/navigation without saved premium claims. Narrow 320px/200% text checks are included.

`../../tool/flutter analyze lib/service_cosmetics.dart lib/cosmetics_screen.dart lib/season_screen.dart test/service_cosmetics_test.dart` — **no issues**.

Store and server responses in the new commerce tests are explicitly named fixtures behind the real native manager. No real purchase occurred. Native SDK/provider acceptance, deployed services and authenticated soundtrack delivery remain separate release gates. Root owns bootstrap/controller routing; QA owns independent acceptance.

## Files handed back

`game/mobile/lib/service_cosmetics.dart`, the small `CosmeticsScreen.servicePanel` and pending-status seam, optional services integration in `season_screen.dart`, and `test/service_cosmetics_test.dart`. No app/bootstrap/controller changes were made by this lane.
