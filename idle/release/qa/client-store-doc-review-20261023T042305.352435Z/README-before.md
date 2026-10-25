# Tideglass store preparation

This is a reviewable local draft for M5-06 / S43 (store creative), with M7-05 preparation. It has not been uploaded or submitted. Public release is not authorized, and required account/hosting/device/human/observation gates remain open.

`metadata.en-US.json` contains complete English descriptive copy and internal reviewer notes. Missing account identities, contacts, URLs and ratings are `null`, not invented values. Copy describes the intended fully configured v1; do not submit it with optional features absent from the candidate. Final metadata must be compared with the exact submitted build and enabled service configuration.

The name is 9 characters, subtitle 25, promotional text 140, keywords 77 UTF-8 bytes, short description 75 and full description 1,780 characters. These fit the current [Apple product-page guidance](https://developer.apple.com/app-store/product-page/), [Apple metadata limits](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information) and [Google listing limits](https://support.google.com/googleplay/android-developer/answer/9859152?hl=en-EN), checked on 19 October 2026. Recheck before submission.

## Creative assets and provenance

| Asset | Current source | Remaining delivery work |
|---|---|---|
| Original lighthouse icon | `game/client/art/app-icon.svg`, `app-icon-1024.png`, `app-icon-provenance.json`; native catalogs already use the same geometry | Final visual review and store-specific export validation |
| Main harbor, campaign, challenge and season screenshots | Fresh native capture assignment in progress | Exact candidate, dimensions, platform and setup manifest; visual inspection; store-size validation |
| Short gameplay footage | Fresh native capture assignment in progress | Record actual game behavior, retain unedited source, trim/encode with an edit manifest; inspect final video |
| Google feature graphic and icon export | `creative/google-feature-1024x500.png`, `creative/feature-graphic.svg`, `creative/google-icon-512.png`, with render provenance | Independent visual review; actual listing validation |

Use screenshots from an actual build. A seeded but reachable state must be disclosed in the internal capture manifest, including the seed/setup and displayed content. Test time compression is not normal gameplay pacing. Exclude debugging panels, fixture prices, personal account information and unavailable products. Never present simulator performance as physical-device evidence.

Apple's current [screenshot specification](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/) defines accepted device-size groups. Its [preview specification](https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications/) permits 15–30-second previews and distinguishes accepted video resolutions from native screen dimensions. Google has separate [preview-asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en). Preserve raw captures and prepare platform exports only after checking their actual dimensions against these sources.

## Submission boundary

The draft intentionally contains no final age-rating claim, accessibility certification, public privacy promise, release date, review credential, legal entity, price or territorial availability. Store questionnaires and data disclosures must match the final native SDK/network audit and operator arrangements. Local source functionality and synthetic purchase tests do not satisfy these requirements. Source data practices are described in `services/docs/PRIVACY.md`; that inventory is not a published policy.

When a release candidate is available, review both directions: each advertised capability must have working implementation and evidence, and each shipped data/commerce capability must be accurately represented in the listing and disclosures. Preserve the original 65-package / 44-scope acceptance contract.

Original code-authored store creative is reproducible with `python3 tool/render_store_creative.py`. The renderer reads the existing lighthouse geometry without modifying native catalogs. Both PNGs use opaque RGB; the feature graphic is 1,024 × 500 pixels and the icon is 512 × 512 pixels. No gameplay screenshot is synthesized. Lead visual inspection found readable text and no clipping; independent review remains open.
