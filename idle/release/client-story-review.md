# Campaign and challenge client handoff — 2026-10-16

## Implemented behavior

`StoryScreen(game: controller, initialTab: 0)` is reachable from Logbook → Restoration. Its four tabs expose the actual pinned catalogue and controller commands:

- Six sequential chapters show current objective values, retained completed achievements, authored hints and completion text. The final chapter reveals the authored ending; continued play remains available.
- Eighteen archive accounts display their chapter requirement. Only restored accounts expose `readArchive`; the controller also guards against unknown or locked IDs.
- Twelve dossiers appear in three rule families. Entry requires three restored chapters and 100 Survey Notes once. Owned replay is free. Opening/replacing, restarting and discarding a passage require explicit confirmation describing losses and retained ownership. Cancellation does not mutate state or jump the viewport.
- The active passage has its own five-tier fleet, Radiance balance, lifetime goal, actual berth caps, cross-tier matrix, automatic plan and completion copy. Main-world production continues. Best-payback and tier-priority approaches use the production runtime; priority arrows persist the selected ordering. Focus, Support and Rechart controls are absent from the passage fleet.
- Six original optional decoration overlays can be previewed, purchased for 50 Notes, equipped and removed. Ownership is retained when removed. These mutations use the controller and do not change production.
- Logbook also reaches the separate production `SupportScreen`, without an unavailable ad/store button.

The main harbor now reads `story.campaign.restoredHarbor` and the saved equipped decoration. Each restored chapter adds an actual distinct constellation and horizon light; the sky gradually brightens. All seven states and six overlays share one original vector scene. This is concrete implemented art, not acceptance of the entire v1 art inventory.

## Files and ownership

- `game/mobile/lib/story_screen.dart`: new production screen and confirmations.
- `game/mobile/lib/app.dart`: Restoration and Crew Support navigation, saved restoration/decoration bindings, reduced-motion preference propagated to route descendants.
- `game/mobile/lib/harbor_art.dart`: six constellations, seven restoration states, six decoration overlays.
- `game/mobile/test/story_ui_test.dart`: twelve interaction/layout cases.
- `game/client/design/render_story_test.dart`: reproducible widget-rendered review fixtures; explicitly separate from native evidence.

No changes were made to controller, bootstrap, persistence, progression math, native scaffolds or dependency declarations in this lane. App/harbor ownership returns to the lead after this handoff. The art/audio lane is authoring `StagedProducerArt(tier, count, size)` in a separate new file; current cards still use the earlier base producer silhouettes until that handoff is integrated.

## Verification evidence

- Full mobile test suite: **54 passed** before the final two presentation-only repairs.
- Story UI suite: **12 passed**: six chapters; actual dossier cost and isolated fleet; replacement cancellation; passage purchases; alternate policy priority; archive access; authored ending; cosmetic cost/equip and zero production change; app navigation; explicit restart and free owned replay; unequip; narrow layout with expanded network and archive.
- Analyzer: **no issues found**.
- Final focused rerun after the scroll/contrast repairs: **13 passed** (twelve story interactions plus the visual renderer).
- `release/client-story-proof/harbor-contact-sheet.png`: seven restoration states and six distinct decorations, rendered with the actual vector painter and inspected.
- `campaign-phone.png`, `passage-phone.png`, `archive-phone.png`, `decorations-phone.png` in the same folder: actual production widgets at 390×844 with deterministic seeded progress, inspected.
- Layout tests cover 320px width at 200% text, including alternate priority controls, ending, decorations, expanded network table and archive content. Buttons inherit 48dp minimum targets; ordering arrows have descriptive tooltips. Reduced motion is propagated to descendants and viewport transitions.

The captures use Flutter's widget renderer with bundled Roboto/Material fonts. They are not screenshots from a native phone, evidence of natural pacing, screen-reader audits or human usability studies. Native integrated candidate screenshots remain a separate platform gate. Story UI English copy has not yet been fully extracted for localization. Campaign/collectible badges are recorded as content IDs but do not yet have the full separate cosmetic collection presentation. None of these checks proves all 36 cosmetics, store acceptance or finished v1.

## Next integration

Wire the new staged producer artwork when the art lane hands it off. Add the season/pass presentation only against the lead's forthcoming persisted controller API. Keep main and event/challenge wallets visibly separate, preserve confirmation semantics, and run native integrated captures after all lanes are stable.
