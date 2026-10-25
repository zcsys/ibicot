# M1-07 named client review

Recommendation: eligible for the original reusable visual-component slice criterion. No acceptance or scope status was edited. The lead/director retains the acceptance decision.

The exact `implementation/program.json` criterion is: “Deliver modular producer parts, harbor layers, typography, icons and UI states sufficient for the slice.” Its only dependency is M0-05, currently accepted. The associated S19/S23 identifiers do not turn this bounded visual-component review into acceptance of the entire art or audio scope.

## Inspected implementation

| Requirement | Actual delivery and integration | Review result |
| --- | --- | --- |
| Modular producer parts | `StagedProducerArt` renders five families and five count stages from 25 editable scene JSON files through `producer_art_data.dart`. Main-harbor and season producer cards use this widget; dossier cards reuse `ProducerArt`. | All 25 generated records equal their editable sources. Each family's successive stage preserves its prior shape prefix and adds actual geometry, rather than only recoloring. Count stages are 0/25/50/75/100. Locked opacity/badge and selected frame are reusable states. |
| Harbor layers | `HarborArt` exposes counts, phase, restoration and decoration. Its 640×388 scene composes sky, stars, islands, water, lighthouse, reflection, fleet and quay layers. | Seven restoration stages preserve layout while adding constellation/quay detail and dawn color. Animation phase changes presentation only. Clipped rounded bounds, fixed aspect and image semantics support reuse. |
| Typography | Shared Material theme in `palette.dart`, `LocalizedText`, `ReadingDialog` and `readingAppBar` in `presentation.dart`. | Explicit title/body/label hierarchy and body leading are consistently integrated. Platform/SDK typefaces are used; no custom font file is claimed. Filled/outlined/icon button theme minima are 48×48. |
| Icons | Original lighthouse/star app SVG and raster, SDK Material navigation/status icons, producer lock/selection treatment. | The icon vocabulary is coherent with navy/cyan/amber art. Navigation and lock/completion states have adjacent labels, so color or silhouette is not the sole indicator. This is not a claim that every icon is custom artwork or that release rights approval is complete. |
| UI states sufficient for slice | Main producer cards expose locked requirements, quantity, output, milestone progression, affordable/disabled action states. Shared panels/data rows and navigation; Rechart eligibility/preview/confirmation and return/recovery presentation. | Actual production source integrates the components. Cosmetic owned/equipped/locked states are additional reuse evidence, beyond the minimum slice. Economic decisions remain in controller/core; renderers do not grant rewards. |

The family shape counts across the five stages are Spark Skiff 8/11/16/21/27, Prism Nursery 12/18/24/28/35, Tide Dynamo 16/20/26/31/37, Aurora Loom 11/14/15/20/27, and Dawn Observatory 10/13/16/21/28. The verification JSON records the exact source equality and prefix checks.

## Source-bound evidence

I read the different-author QA report `release/qa/integration-art-matrix-20261021T123739647573Z/ART_MATRIX_REVIEW.md`, its verification data, actual producer/harbor/theme/icon/UI source and the style guide. I then independently ran the repaired Python matrix checker against both preserved full reports. Both returned exit 0: 816 rows per mode (84 harbor, 300 producer, 432 cosmetic), with 524 frozen inputs. All nine selected current runtime sources match the inputs in both preserved runs. These are rechecks of existing renderer executions, not new Flutter runs.

The QA report separately records its representative 8-test/136-row rerun, 1,554 reconciliation checks, 26 adversarial checker cases and 16 declared contrast pairs with minimum ratio 6.277248215353944. I do not recast the representative QA rerun as a new full rendering run. The repaired checker hash is `2bbf0a53b581f220bcbdb5b453ae0ebc50df4abb38f2eea33b4eb9bc4c5b1ed3`.

I visually opened these exact images, whose hashes are in `verification.json`:

- `release/art/producer-contact-sheet.png`: all 25 stages, distinct family silhouettes and visible additive construction; no observed clipping.
- `source/art/registration/harbor-contact-sheet.png`: all seven restoration states, coherent stable composition and progressive constellation/quay detail.
- `game/client/art/app-icon-1024.png`: legible lighthouse/star/beam mark consistent with the palette.
- `release/native-proof/main-launch-20261021T103014.378318Z/ios-phone-main.png`: actual native retained-progress harbor, onboarding and navigation readable in the inspected capture.
- `release/native-proof/integration-ios-phone-20261021T111046.293625Z/ios-phone-session-start-producer-stages.png`: actual native seeded producer gallery, consistent with the source silhouettes.

The two phone images were displayed by the image viewer at 942×2048 from original 1206×2622 files. The retained-progress screenshot is not fresh-player pacing evidence; the seeded gallery is not natural progression or approved store creative.

## Limits and authorship

I found no blocking defect in the original reusable slice-component criterion. This review does not complete all 164 per-asset contracts, all daily-loop status/icon work, audio/S23, legal/rights review, physical touch or screen-reader review, store approval, or new native execution. Narrow captions and individual asset/device gates retain their own requirements. The full matrix's `canonical_acceptance` remains false.

I previously authored portions of the client, harbor and cosmetic presentation. This is the program's named client integration review, with that authorship disclosed, and is supported by the separate QA evidence above; it is not represented as different-author review of every source line. No production source, program acceptance, prerequisite, scope criterion or economic rule was changed.

Exact source hashes, both checker commands and logs, five inspected image hashes and modularity checks are retained in the adjacent `verification.json` and mode-specific logs. No Flutter, simulator, emulator, device or native build command was run in this review lane.
