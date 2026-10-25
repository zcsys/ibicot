# Tideglass visual direction and client binding

Status: director-selected implementation direction, 21 October 2026. This records the current client. Independent client review of the consolidated representative direction is recorded in `release/art/entry-gates/CLIENT_STYLE_REVIEW.md`. It does not approve every asset or physical-device budgets.

## Visual rules

The harbor uses deep ocean navy, moonlit teal and warm amber. Its stable lighthouse and five readable working silhouettes remain the anchor. Chapter restoration adds one constellation group and one quay light per chapter and progressively lifts the sky gradient. Restoring the harbor does not require a new painted scene or new cosmetic identity. `harbor.unlit` means unrestored; the initial lighthouse, moon and stars remain illuminated.

The producer families remain distinguishable by geometry: triangular sail, prism nursery, wheel, vertical loom and observatory. Each has five additive constructions at ownership 0/25/50/75/100. Stage zero is the base silhouette, including when no producer is owned; lock state is separately represented by an icon and adjacent text. Construction changes add outriggers, instruments, lamps and constellation detail. Never replace the family silhouette with an unrelated reward image. Harbor miniatures currently use the shared base silhouettes; staged cards are used in the harbor purchase list and seasonal fleet. This difference is deliberate presentation reuse, not a claim that every miniature has all stages.

## Palette and typography

Runtime authority is `game/mobile/lib/palette.dart`.

| Token | sRGB hex | Role |
|---|---|---|
| deep | #071923 | Page background |
| panel | #102A37 | Content panels |
| raised | #173643 | Selected/raised surfaces |
| line | #294753 | Separators and outlines |
| teal | #79E0CC | Primary actions and illumination |
| amber | #F4CA88 | Radiance, milestone accents |
| text | #E6EEE9 | Primary text |
| muted | #A1BAC3 | Secondary text |
| warning | #FFAE9A | Errors and caution |

Text and numerical values are native widgets, never painted into artwork. The Material 3 theme uses inherited SDK/platform typefaces; no custom font file is declared in pubspec. Headline sizes are36/28, titles21/16, body16/14 with1.45 line height, and buttons14 logical pixels before text scaling. Small captions remain in the implementation and require full readability/accessibility qualification; this guide does not certify them. MaterialIcons are provided through the Flutter SDK. Final SDK/font notice and distribution qualification remains required; this is a source inventory, not complete SDK license approval.

Phone content scrolls vertically; wider layouts constrain text width. Controls use the theme's48×48 logical-pixel minimum. Long text must wrap or scroll and must remain reachable at100/150/200% and in the pseudolocale. Prices, timers, counts, lock/ownership text and action names stay outside raster media. Color never substitutes for the adjacent status/action wording.

## Scale, motion and reuse

The harbor painter's reference box is640×388; producer geometry uses100×100 and scales into square cards (58 logical pixels in the main and seasonal cards). Rounded viewport clipping belongs to the widget. The renderer uses Flutter Canvas paths, gradients and native Material controls. Review PNG/SVG exports are not loaded as textures by the current app.

Harbor waves use an8-second decorative animation cycle. Local reduced motion or OS disableAnimations stops the controller and renders the static state without removing counts, rewards, locks or chapter information. Producer stage geometry itself is static. No economic timing, reward or action requires animation. Avoid flashing, camera shake, particles that obscure controls and continuously announced economic ticks. Background/lifecycle performance still requires actual target verification.

## Authoring and adapter rules

- Producers: `tools/assets/export_producers.py` emits original JSON/SVG presentation exports and `producer_art_data.dart`; `producer_art.dart` interprets those geometric primitives. The exporter is a production mutation tool and should not be rerun merely to inspect the build.
- Harbor: `harbor_art.dart` draws the scene directly. Seven source/export descriptors register selectors and sampled captures; they are not runtime-loaded scenes.
- Cosmetics: `cosmetic_art.dart` and the immutable catalogue draw the36 original items. Selection/ownership uses the existing catalogue and game state; artwork has no economic effect.
- Seasonal presentation reuses actual `SeasonScreen`, harbor and producer components. Internal runbooks/Season2planning remain outside mobile asset declarations.
- Audio is authored score/synthesis, exported masters and compressed native playback. Capability and rights are tracked separately; no image-generation capability is implied to produce music.

Palette/renderers and generated inputs are source-controlled authority. New raster assets or atlases require an explicit pipeline addition and the original alpha/color/import/budget qualification; the current vector route is not permission to skip future texture checks.

## Reviewed samples and limits

The director inspected the7-state harbor contact sheet, the25-producer contact sheet, an actual iPhone simulator main screen and a native producer-stage gallery from candidate152805bf9e26. Silhouettes are distinct; construction additions and constellation restoration are visible; sampled artwork stays inside its view boxes. The main screen retains the harbor as anchor with live readable controls. Native stage gallery is explicitly seeded verification content, not natural progression or store creative.

Independent producer and registration reviews are linked in style-qualification.json. This direction chooses an already implemented coherent look. Full per-asset variants, screen-reader navigation, contrast/readability, physical minimum-device GPU/memory and performance remain separate requirements. Static captures do not prove animation quality or human comprehension.
