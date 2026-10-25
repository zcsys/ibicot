# Independent local public-page review

Result: no blocking finding within the bounded local-draft scope. Reviewed by `/root/art_content_engineer` on 21 October 2026, independently of `/root`, the page author. This acknowledges source, registration and sampled local presentation only. It does not approve publication, a legal policy, consent, SDK disclosures or complete asset variants.

## Reproduced checks

`python3 release/public-pages/independent_probe.py` passed. The independent parser verified all 28 internal page/fragment links, unique IDs, one h1 and a skip link on each page, and no scripts, forms, iframes, inputs or external resource URLs. Actual GET requests to both pages and the stylesheet at `127.0.0.1:8779` returned 200, matched the local file bytes exactly and set no cookie. No author registration script was executed.

The manifest diff against `evidence/launch-manifest-before.json` is exactly eight leaf changes: source path, production evidence and delivery status for the two page assets, plus production status for the corresponding two support entities. All 164 asset identities remain unchanged. Verification and license evidence stay null. Both provenance records match every source/export hash and preserve null reviewer fields, unrecorded distribution approval, false production acceptance and every original required variant. The extracted source/export text matches each actual HTML page. Neither descriptor claims client loading or a configured native URL.

The registration script was read as a mutation tool, not run during review. Its ID mapping, extraction, stable paths and in-production-only output agree with the resulting records. The independent probes hash 21 review inputs and record the exact eight-field diff in `independent-probes.json`.

## Content and visual review

The full HTML and browser accessibility text were read against `services/docs/PRIVACY.md`, current `help_content.dart`, soundtrack cache code, study recorder and study gate. Account deletion, sign-out, local guest progress, personal exports, recovery-code loss and failed remote requests remain distinct. The cache wording matches the three-export, 64 MiB-per-export reservation and cleanup on a later startup/export; it does not promise deletion at exactly 24 hours. Study enrollment is separately provisioned and opt-in; default erasure, pending errors and previously exported copies are stated without claiming a live study or participant approval. Optional SDK traffic remains explicitly unqualified.

All four existing actual browser captures were visually inspected: support/privacy at 1280×720 and support/privacy at 320×780. In those sampled first viewports, headers, navigation, status notices and body text wrap without overlapping or horizontal clipping. The images do not cover every lower section or expanded disclosure; no full-page visual certification is inferred. The same palette and typographic hierarchy remain legible in the samples, without a numerical full-contrast claim.

An independent Chrome visit to the same local support URL exposed the expected headings, named navigation, disclosure buttons and local-preview notice. Opening “A paid appearance is missing” showed the verified-ownership/recovery text; following the header Privacy link navigated to the actual privacy page and its full accessibility text. This is a browser observation, not physical screen-reader or keyboard-traversal certification. The four captures are author captures independently inspected here, not re-labeled as reviewer-produced captures.

No invented operator, mailbox, response time, approved backup policy, live account/store provider or public enrollment was found. `publication.json` keeps operator, contacts, URLs, backup policy and SDK audit null and public authorization false. Both pages prominently say they are development references. The public web deletion-request route remains absent and is stated as a release requirement, not presented as implemented.

## Nonblocking evidence finding

PP-01: all four files named `evidence/*.png` contain JPEG/JFIF bytes, confirmed by file signatures. Their actual dimensions are correct and they render normally. The evidence filenames should use `.jpg`, or the author should create real PNG exports while preserving the original capture/hash history. This does not change the page behavior or local editorial result. It must not be described as inspected lossless PNG evidence. No image was converted or renamed by this reviewer.

## Scope and remaining gates

This contributes to M5-03/M7-05 and S27/S39 as a working local source, exact registration and bounded editorial/presentation review. Original 100/150/200% and pseudolocalized acceptance remains open; this sampled 100% browser review is not complete variant acceptance. Native URL wiring, target assistive interaction, physical validation, rights/distribution approval, final operator/contact/territory/age/retention wording, actual SDK traffic and working hosted support/privacy/deletion endpoints remain open. Nothing was published. No runtime, author source, manifest, provenance or canonical reviewer field was changed by this review.

## PP-01 correction follow-up

The author renamed the four current captures to `.jpg` and retained the original bytes under `evidence/history/`. A bounded independent follow-up compared current files, preserved originals, the original review hashes and `evidence/capture-format-correction.json`: all four are byte-identical JPEGs. PP-01 is resolved for the current evidence names; its original finding and original review pins remain above/in the first probe. Updated author-report and correction hashes are recorded in `rename-followup-probe.json`. No new browser pass or broader acceptance was inferred.
