# Independent repaired screenshot exporter review

Disposition: **passed for bounded RGB8 conversion tooling**. No unresolved finding was reproduced within the reviewed purpose. This closes the three findings against the earlier exporter; the original failed review and raw counterexamples remain immutable. This review does not qualify current-candidate captures, visual selection, store ingestion, publication, or native release gates.

Exact reviewed and executed script SHA-256: `ec447cddb2b70f44b33440c3daf41392f782f65ee2468e55d8b048bcf952aa51`. The fresh archived `export_screenshots.py` was used throughout; the live script still matches at seal. Author handoff: `release/store/screenshot-export-repair-20261023T041208.557192Z/AUTHOR_REVIEW.md`, pinned in `baseline.json`. Earlier failed review: `release/qa/client-screenshot-export-20261023T040546.847914Z/REVIEW.md`; its entire file inventory remained unchanged during this retest.

## Findings resolved

- **RGB transparency keys:** the exact earlier RGB+tRNS failure input now rejects before output creation. Output generation permits only a fresh RGB8 header, preserved color-definition chunks, pixel data and IEND; no tRNS or alpha channel is present in inspected outputs.
- **Native 16-bit alpha:** the exact earlier alpha65534 failure input now rejects before output creation. Additional native16 alpha65534,65280 and0 controls across filters4,3 and1 reject. The decoder checks actual native alpha, independent of Pillow's 8-bit representation; native8 alpha254 also rejects.
- **Precision disclosure:** native16 RGB is deliberately mapped to nearest RGB8 using `(sample + 128) // 257`. Independent expected values used Python `round(sample / 257)`; integer16-bit values have no exact half-step ties. Exhaustive checking of every 0…65535 value in each RGB channel confirms the mapping,195840 changed samples of196608 in the exhaustive fixture, and maximum native sample error128. The manifest truthfully reports source bit depth, nonrepresentable-sample count, maximum error, and whether native RGB samples remain exact. A complete0…255 RGB8 control remains exact. Historical first main pixel `(2924,6324,8752)` becomes `(11,25,34)` under the declared nearest mapping.

## Independent validation

All **80** checks passed:

| Check group | Cases | Result |
|---|---:|---|
| RGB/RGBA8/16 with filters0,1,2,3,4 plus mixed-filter rows | 24 | Exact expected RGB8 values, alpha handling, output roundtrip and color-definition bytes |
| Exhaustive native16 rounding and native8 identity | 2 | Every native value checked; truthful counts and error bound |
| Format, opacity, decompression and dimension rejection | 24 | All rejected with retained reasons |
| Replay of original conversion/provenance controls | 26 | Both original opacity failures now reject; source hashes and existing output protected |
| Independent historical native16 comparison | 4 | Exact declared mapping, counts, error, dimensions and color chunks verified |

The format controls cover malformed signature/CRC/truncation/trailing data, too-short/too-long raster, concatenated or incomplete zlib streams, invalid filter, native8/16 nonopacity, RGB transparency keys, animation, unknown critical chunk, unsupported interlace/palette/depth, zero/excessive dimensions, duplicate header and duplicate color definition. The original replay covers exact candidate presence/format/mismatch, manifest/report existence and native flags, hash and size/dimension mismatches, device/harness identity, unsafe/duplicate names,20MiB and16-million-pixel bounds, and existing-directory nonoverwrite. Rejected preflight cases created no output; the deliberate existing-output sentinel was preserved.

Source review confirms bounded CRC-checked chunk parsing; permitted noninterlaced RGB/RGBA8/16; byte-based reconstruction of PNG filters0–4; decompression constrained to exactly the header-derived raster size; native alpha inspection before conversion; and independently reopened RGB8 outputs matching the declared pixels. This is a purpose-built capture converter, not a generalized PNG decoder or validator. The20MiB input and16-million-pixel limits are enforced on the export path.

`independent_checks.py` is the reproducible review harness. `checks.log`, `checks.json`, `checks-progress.json`, generated controls, original-input references and source hashes, and all fresh output PNGs are retained. Synthetic inputs are test controls, never native evidence. No Flutter, device, native execution, production edit or shared-script edit occurred.

## Historical source and output identity

Exact historical candidate: `152805bf9e269f49d14486286656ac0174a808384d10e6623533a4f92690dc11`. Source directory: `release/native-proof/integration-ios-phone-20261021T112255.702927Z`. These captures are historical controls, not current release creative.

All four source images independently decode as noninterlaced16-bit RGBA,1206×2622, with all native alpha samples65535 and source scanline filter0. Their actual IDAT data was independently decompressed and interpreted as big-endian16-bit samples. Fresh output PNGs were independently decoded from their IDAT rows and reopened with Pillow; actual IHDR is8-bit truecolor, unchanged1206×2622 geometry, and no alpha or tRNS. All corresponding samples equal the declared nearest RGB8 mapping. There is no resize, crop, compositing, frame substitution or invented UI.

The source iCCP and cICP payloads are preserved verbatim, including the source Display P3 color definitions. The output is not retagged as sRGB and no gamut conversion is asserted. Non-color ancillary metadata is explicitly omitted, as disclosed by the converter. This is byte-preservation of source color definitions, not a separate colorimetric calibration or store-ingestion claim.

| Historical image | Native RGB samples not exactly8-bit representable | Maximum native sample error | Fresh output SHA-256 |
|---|---:|---:|---|
| ios-phone-capture-main.png | 9464536 | 128 | f216732a21cd741caccfc94823cbd55fa6797cd354cec8974eb18649925e0117 |
| ios-phone-capture-chapter.png | 9469215 | 128 | 25738d2090498007ef1c2575c1b09666b9fc230ae53aa54cca64a86c646bb163 |
| ios-phone-capture-challenge.png | 9469896 | 128 | 8c2757c16ec0b4215751596e1f1c3832cc24f3f2ab0012ccb8e3a44f874950f1 |
| ios-phone-capture-season.png | 9472487 | 128 | 401a39343099fd8ccf2ed9da03e26f3b59aef910d791175de9e18c9ab9650d41 |

Every fresh historical output also matches the author's repaired export byte for byte. All source report/manifest/raw file hashes are unchanged. All original failed-review artifacts are unchanged. Exact before/after source pins and color-chunk hashes are in `checks.json`; baseline author and previous-review pins are in `baseline.json`.

## Bounded handoff

The reviewed script is usable for honestly disclosed RGB8 export of eligible opaque native captures. Preserve the original native images and exact provenance alongside converted files. Apply this tool only to the separately verified current-candidate gallery when that evidence exists; those future exports and current store creative require their own qualification. No new native or store-completion claim follows from these historical controls.
