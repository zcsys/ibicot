# Season and pass client handoff — 2026-10-16

`SeasonScreen(game: controller, initialTab: 0)` is reachable from Logbook → Night of Returning Stars. It reads the pinned catalogue and saved seasonal/pass state. All economic and reward actions go through the controller.

## Implemented scope

| Scope | Actual client behavior |
|---|---|
| Separate fleet | Five producers, single/max purchases, own wallet/rate/lifetime, immediate cross-tier matrix and current link factors. Main production remains independent. |
| Automation | Free toggle, best-payback and tier-priority policies, accessible priority arrows, saved ordering. |
| Seasonal clock | Exact saved start/end dates, 28-day duration, upcoming/live/archived status, time remaining. `local_development` rollout is explicitly labeled a local preview schedule. |
| Archive | Actual free resume/pause commands; retained fleet; copy explains that paused time gives no event earnings. |
| Personal bearings | Three authored badge titles/descriptions/thresholds and one-time cosmetic-only claims. |
| Pass | All 30 levels, authoritative selected-pass XP, 500 XP per level, ten free appearance receipts and twenty complete readable accounts. Narrative text becomes readable after its real claim. |
| Premium previews | Ten authored previews at levels 3/6/…/30; no price, ownership, purchase or claim control is invented. Purchasing/delivery unavailability is stated. |
| Shared contracts | Retained daily slots can receive a frozen event-production alternative. Main and seasonal routes share a single claim, 10 Notes and 250 XP. Claimed slots cannot be rebound or claimed again. |
| Audio integration | Existing AudioSettings is visible when a real bus is supplied. Season navigation starts the current theme and restores harbor/dawn on return. No audio command runs inside widget build; no-audio test controllers remain supported. |
| Producer stages | Main and seasonal cards now use the art lane's StagedProducerArt with real counts, 58dp size and explicit locked state. |

## Verification

- **12 season UI tests passed**, covering wallet isolation; single/max; both automatic policies and ordering at 320px/200% text; archive pause/resume; both main/event shared-claim directions; all 30 levels and real free collection; fragment reading; badge claim; app navigation; XP threshold rejection; saved dates differing from the catalogue; and upcoming purchase prevention.
- The focused visual renderer passed (**13 total** with those interaction tests). Captures in `release/client-season-proof/` show fleet, pass, expanded reward/premium preview, shared contracts and archived fleet at 390×844. Each was inspected. Selected-pass status was changed from disabled-button styling to readable positive status after inspection.
- The final integrated mobile test run completed with **90 tests passed**, including four producer-art tests. No client regression failures remained.
- `season_screen.dart`, `app.dart` and `season_ui_test.dart` separately analyzed with **no issues**. The later whole-mobile analysis found six brace-style informational lints in the lead's concurrently edited `game_controller.dart`; those are reported to the lead and were not changed by this lane.
- The producer art was independently reviewed in `release/art/producer-independent-review.md`.

## Honest limits

Captures are deterministic Flutter widget fixtures, not native phone screenshots, natural pacing evidence or a 28-day study. Physical VoiceOver/TalkBack, device performance and integrated store/build acceptance remain separate gates. English seasonal UI copy is not fully extracted for localization.

The twenty pass appearance previews currently use explicitly identified collection motifs and authored names/body copy. They are clearly labeled previews. They are not the twenty finished equipped appearances. Free ownership receipts are real; harbor equipping awaits the lead's unified cosmetic integration. Premium ownership is never inferred from local claim strings. The complete 36-cosmetic asset/delivery requirement is not claimed by this handoff.

## Ownership handoff

This lane changed `game/mobile/lib/season_screen.dart`, `game/mobile/lib/app.dart`, `game/mobile/test/season_ui_test.dart` and the visual renderer `game/client/design/render_season_test.dart`. Controller/bootstrap/story persistence, core, event engine, dependency declarations and audio implementation remained owned by their assigned lanes. App and season screen ownership return to the lead now for final integration and native candidate capture.
