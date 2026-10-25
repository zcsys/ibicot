# Tideglass store preparation

This is a reviewable local draft for M5-06 / S43 (store creative), with M7-05 preparation. It has not been uploaded or submitted. Public release is not authorized, and required account/hosting/device/human/observation gates remain open.

`metadata.en-US.json` contains complete English descriptive copy and internal reviewer notes. Missing account identities, contacts, URLs and ratings are `null`, not invented values. Copy describes the intended fully configured v1; do not submit it with optional features absent from the candidate. Final metadata must be compared with the exact submitted build and enabled service configuration.

The name is 9 characters, subtitle 25, promotional text 140, keywords 77 UTF-8 bytes, short description 75 and full description 1,780 characters. These fit the current [Apple product-page guidance](https://developer.apple.com/app-store/product-page/), [Apple metadata limits](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information) and [Google listing limits](https://support.google.com/googleplay/android-developer/answer/9859152?hl=en-EN), checked on 19 October 2026. Recheck before submission.

## Creative assets and provenance

| Asset | Current source | Remaining delivery work |
|---|---|---|
| Original lighthouse icon | `game/client/art/app-icon.svg`, `app-icon-1024.png`, `app-icon-provenance.json`; native catalogs already use the same geometry | Final visual review and store-specific export validation |
| Main harbor, campaign, challenge and season screenshots | Candidate3b00 iPhone/iPad sets independently reviewed; Android correction under native validation | Phone/iPad main, chapter and passage are local candidates; Season is internal preview; final store-size/ingestion validation remains |
| Short gameplay footage | Candidate3b00 iPhone/iPad19-second previews independently reviewed, raw footage retained | Silent previews have measured bitrates below the requested encoder target; sound direction and final store conformance remain open |
| Google feature graphic and icon export | `creative/google-feature-1024x500.png`, `creative/feature-graphic.svg`, `creative/google-icon-512.png`, with render provenance | Local pixel review and corrected icon format reviewed; actual listing preview/ingestion remains |

Use screenshots from an actual build. A seeded but reachable state must be disclosed in the internal capture manifest, including the seed/setup and displayed content. Test time compression is not normal gameplay pacing. Exclude debugging panels, fixture prices, personal account information and unavailable products. Never present simulator performance as physical-device evidence.

Apple's current [screenshot specification](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/) defines accepted device-size groups. Its [preview specification](https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications/) permits 15–30-second previews and distinguishes accepted video resolutions from native screen dimensions. Google has separate [preview-asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en). Preserve raw captures and prepare platform exports only after checking their actual dimensions against these sources.

## Submission boundary

The draft intentionally contains no final age-rating claim, accessibility certification, public privacy promise, release date, review credential, legal entity, price or territorial availability. Store questionnaires and data disclosures must match the final native SDK/network audit and operator arrangements. Local source functionality and synthetic purchase tests do not satisfy these requirements. Source data practices are described in `services/docs/PRIVACY.md`; that inventory is not a published policy.

When a release candidate is available, review both directions: each advertised capability must have working implementation and evidence, and each shipped data/commerce capability must be accurately represented in the listing and disclosures. Preserve the original 65-package / 44-scope acceptance contract.

Original code-authored store creative is reproducible with `python3 tool/render_store_creative.py`. The renderer reads the existing lighthouse geometry without modifying native catalogs. The feature graphic is 1,024 × 500, 24-bit RGB without alpha. The Google icon is 512 × 512, 32-bit RGBA with entirely opaque alpha. No gameplay screenshot is synthesized. [Independent copy/pixel review](CLIENT_REVIEW.md) covers the local draft and unchanged feature graphic. [Independent icon-format review](../qa/native-google-icon-format-20261023T034940.198444Z/REVIEW.md) covers the later encoding correction; all original icon RGB pixels remain identical. Store preview/ingestion is still unperformed.

## Reviewed local media tools

`tools/export_screenshots.py` accepts only a hash-bound successful native gallery and a new output directory. It verifies opacity at the original PNG bit depth, preserves dimensions and color-space definitions, and writes PNG RGB8 without alpha. Native16-bit RGB is deliberately rounded to8-bit; the manifest records that precision reduction and its measured error. It does not resize, crop, composite or invent UI. The first implementation's transparency and precision-reporting failures remain in the [initial review](../qa/client-screenshot-export-20261023T040546.847914Z/REVIEW.md). The [independent repaired review](../qa/client-screenshot-retest-20261023T041554.132148Z/REVIEW.md) passed80 bounded checks. Its four historical exports qualify the converter, not current release screenshots.

`tools/export_preview.swift` and `tools/inspect_preview.swift` preserve a selected real-time full-frame interval and report actual dimensions, codec, duration, frame count and silence. Their [independent tool review](../qa/client-preview-tool-20261023T032106.818906Z/PREVIEW_TOOL_REVIEW.md) covers conversion and rejection behavior. Current native footage, final interval selection and actual exported previews still require their own visual review. Keep raw captures and all conversion/edit manifests. [Current capture/export requirements](current-export-requirements-20261023.json) record the official specifications checked23October2026; none of these local reviews proves store ingestion or authorizes submission.

## Current local media decisions — 23 October 2026

The [iPhone selection](media-3b00-phone-clean-20261023T045548.384747Z/selection.json) and [corrected iPad selection](media-3b00-tablet-corrected-20261023T0811Z/selection.json) each contain three full-display screenshots and one19-second actual-gameplay preview. Their setup is a seeded progression fixture through production UI, not natural player pacing. Both seasonal stills remain internal because their visible dates describe a local28-day preview. [Phone independent review](../qa/client-clean-phone-media-20261023T050152.295344Z/REVIEW.md) and [iPad independent review](../qa/client-current-media-20261023T080835.670842Z/tablet/REVIEW.md) bind the actual outputs and source captures. [Lead bounded decisions](../qa/lead-bounded-review-adoption-20261023T082840.234073Z/DECISIONS.md) adopt the corrected tablet set locally.

The previews retain native display content and chrome, do not fabricate motion, and have no audio track. Actual measured estimated bitrates are about1.853Mbps (phone) and1.663Mbps (tablet), despite the11Mbps encoder request. These are reviewed local candidates, not store-qualified or uploaded assets. Earlier wrong-screen, overlong/frozen-frame and Android publication failures remain in their evidence directories. Android fresh capture validation is still in progress.
