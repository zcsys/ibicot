# Independent screenshot exporter review

Disposition: **changes required for the reviewed version**. This is a bounded conversion-tool review for M7-05/S40. It establishes neither new native capture evidence nor current-candidate creative, visual selection, store ingestion, publication, or native release acceptance.

Reviewed archived source: `export_screenshots.py`, SHA-256 `7a284bd9d5287f7c245dee99bf3b66377d26a6a4f6ff430be02b27f3b56a6097`. The copied source was executed directly for every control and the historical reproduction. Root began a separate repair after receiving the findings; live tool SHA at seal is `ec447cddb2b70f44b33440c3daf41392f782f65ee2468e55d8b048bcf952aa51`. That repair is outside this review and requires a new exact-source review.

## Findings

1. **Opacity check misses RGB PNG transparency keys.** The exporter accepts PNG color type 2 with a `tRNS` chunk. The synthetic `(23,42,91)` transparent key survives the RGB export; the resulting output is mode RGB yet has effective alpha extrema `(0,0)`. Retained counterexample: `controls/trns_must_reject/` and the earlier `synthetic-trns/` / `unexpected-trns-output/`. Checking Pillow mode and an RGBA-only alpha branch does not guarantee opaque PNG output. Reject transparency-key input or verify effective opacity before explicitly removing the transparency metadata, then independently inspect the actual output PNG.

2. **Opacity check loses native 16-bit alpha precision.** The native RGBA16 synthetic fixture uses alpha `65534`, which is not fully opaque. Pillow exposes this as alpha `255`; the exporter accepts it and drops that native nonopaque alpha. Retained counterexample: `controls/translucent16_must_reject/`. Check opacity at the actual native sample depth; for RGBA16 every alpha sample must be `65535` before channel removal. This issue did not affect the four historical images: independent native decompression found every alpha sample exactly `65535`.

3. **The unchanged-pixel claim overstates 16-bit preservation.** All four historical raw PNGs are actual 16-bit RGBA, not 8-bit RGBA. Exported PNGs are actual 8-bit RGB. Independent IDAT decompression (all raw scanline filters are 0), big-endian 16-bit sample decoding and comparison prove the output is each original RGB16 sample's high byte. Millions of original color samples are not representable exactly in 8 bits, so `rgb_pixels_unchanged: true` and “preserve every RGB pixel” are false when read as preservation of captured sample values. Example: native first main pixel `(2924,6324,8752)` becomes `(11,24,34)`, which expands to `(2827,6168,8738)` at 16 bits. Explicit, bounded 16→8 quantization is an acceptable implementation choice for RGB8 export, but the mapping and precision loss must be recorded accurately. This review does not require keeping 16-bit store outputs.

## Historical reproduction

Exact historical candidate from the author manifest: `152805bf9e269f49d14486286656ac0174a808384d10e6623533a4f92690dc11`. Historical raw directory: `/Users/csys/Desktop/ibicot/idle/release/native-proof/integration-ios-phone-20261021T112255.702927Z`. This is a historical tool control only. Its four exports reproduce the root author's output bytes exactly. Every source manifest, report and screenshot hash is preserved. The source and output dimensions are all 1206×2622. Each actual output IHDR has bit depth 8 and color type 2, with no alpha channel or tRNS chunk. The four historical outputs are opaque despite the two synthetic rejection holes.

| Historical image | Native RGB16 samples not exactly 8-bit representable | Reproduced output SHA-256 |
|---|---:|---|
| ios-phone-capture-challenge.png | 9469896 / 9486396 | 5f4dc9fe4fef911c333a85a9a5bc9578c43ad0e2aed6c7fcfc7cb3b6b4c896f7 |
| ios-phone-capture-chapter.png | 9469215 / 9486396 | 3bd118f291973d6557ce5883a25dcc99e09c3efb1b96333292c7c3e2c5add71c |
| ios-phone-capture-main.png | 9464536 / 9486396 | 72b1980b0a0e604a489ea6db3c5e39ab29615dff3435e7d1b9512c32c2766435 |
| ios-phone-capture-season.png | 9472487 / 9486396 | 80e9baf7e70058a55323c7982092116803d919efde925fd13ad15c74fb326b70 |

`historical-independent-checks.json` records exact source/report/manifest hashes before and after, native sample/alpha findings, actual PNG IHDR and chunks, high-byte mapping, output hashes, and equality to the author exports. `historical-reproduction.log` retains the complete conversion manifest. No crop, resize, composite, or UI fabrication was observed; quantization occurred as described above. No colorimetric or store-platform acceptance claim is made.

## Bounded controls

26 controls completed: 24 matched their expected outcome; the two opacity controls above unexpectedly accepted. Twenty-two rejection controls passed, including absent/invalid/mismatched candidate, missing capture manifest or verification, mismatched capture manifest hash, raw hash/bytes/dimensions, missing raw file, failed native status, mismatched device/harness identity, unsafe/duplicate names, more than 20 MiB input, more than 16 million pixels, and existing output directory nonoverwrite. The existing-output sentinel bytes were unchanged. Every invoked synthetic source remained unchanged. Rejected preflight cases created no output directory, except the deliberately pre-existing directory which was preserved. Positive opaque8 and opaque16 fixtures also ran successfully; the latter is successful conversion with explicit precision-loss limitations, not a proof of unchanged native samples.

All controls are marked `synthetic_control_only`; their self-contained matching manifests are test inputs, not signed native evidence. `review_checks.py`, `review-checks.log`, `controls.json`, per-case `result.json`, all input files and any unexpected outputs are retained. The command-line missing-candidate failure is separately retained in `missing-candidate-cli.log`. No native/Flutter/device operations or production/shared source edits were performed.

## Handoff

Root has the concrete failures and is authoring a separate repair. Re-review that repair against a separately pinned hash, preserve these original failures, and require correct rejection of both native16 alpha and tRNS plus truthful recorded quantization. Current candidate capture and store dimensions/visual selection remain separate downstream obligations.
