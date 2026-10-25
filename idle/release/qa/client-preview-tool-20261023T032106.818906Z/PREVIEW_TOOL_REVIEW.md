# Independent native-preview tooling review

Reviewer: `/root/client_asset_review`; tool author: `/root`. **The bounded silent-video tooling review passes with no blocking finding.** This does not approve current store creative, a public submission or Tideglass v1. No Flutter, simulator/device operation, live source edit or external service was used.

## Actual reproduction

Both exact current Swift sources compile successfully. The independent run exports the real historical candidate152 recording from source time 2 seconds for 20 seconds, then decodes the result through the inspector. Source bytes remain unchanged.

| Control | Observed result |
|---|---|
| Historical portrait recording | 20 seconds; 886×1920; H.264 (`avc1`); 600 decoded display frames; first at 0, last at 19.9666667 seconds; every frame gap 1/30 second within floating-point precision |
| Quarter-turn metadata fixture | 20 seconds; 1920×886; same 600-frame timing; the source transform `[0,1,-1,0,2622,0]` is respected |
| Audio-bearing fixture | Independent fixture inspection confirms one actual audio track. Export rejects it before creating output; source audio/video bytes remain intact |
| Twelve negative/preservation probes | All reject while preserving existing source/output/evidence or leaving the requested new output absent |

The original source is 1206×2622, 25.275 seconds, with sparse native frames. The portrait export uses the smaller width/height scale, yielding 1.443936 pixels of horizontal padding and no vertical padding. The source is read through its full transformed rectangle; the implementation contains no crop or time-scale operation. Composition insertion maps original source `[2,22)` onto output `[0,20)`, then samples the displayed source at 30 Hz. Repeated held frames do not fabricate progression or interpolate new gameplay.

The independent source probe extracts the displayed original frames at source 2, 7, 12, 17 and 21.966667 seconds. Their actual held-frame times are recorded; sparse sources need not have a new encoded frame exactly at each request. Independent in-memory affine comparison of all five source/output pairs in both orientations supports the full-frame mapping. Mean absolute RGB errors are 4.13–4.78 on the 0–255 scale, versus 12.61–35.49 for deliberate mirror/flip controls. These are compression/sampling comparisons, not pixel identity or a substitute for visual review. No altered reference media is saved by that analysis.

I visually inspected portrait output samples 0, 2 and 4 and the quarter-turn sample 0. Their geometry, orientation and complete captured screen match the source. The late selected image is at 19.933333 seconds, exactly as the inspector records; it is not mislabeled as the final decoded frame at 19.966667. The historical interval ends during an actual page transition. That is preserved source behavior and makes this interval unsuitable as final editorial creative.

## Rejections and preservation

The twelve actual probes cover existing output, source-as-output, a symlink alias to the source, duration below 15 or above 30 seconds, an interval beyond the source, negative and nonfinite start times, odd dimensions, oversized dimensions, a video containing audio, and reuse of an existing inspector evidence directory. Logs record each rejection; SHA-256 comparisons establish preserved inputs/existing outputs. The successful audio-bearing fixture is an explicitly synthetic test composition of historical footage and the project's existing `harbor.m4a`, not store creative or a native capture claim.

The quarter-turn fixture changes only track-orientation metadata on the historical video. It tests transform handling, not actual physical orientation behavior. The original historical source and the two live tool sources have their original hashes at the end of review.

## Limits that remain explicit

- The encoder requests 11 Mbps, but portrait content averages **2.072202 Mbps**; the rotated control averages 2.141291 Mbps. A requested rate is not a measured conforming rate.
- The accepted inputs and outputs are silent. This tool intentionally rejects audio-bearing video instead of silently discarding its audio; it does not provide an audio-preserving editing path or sound qualification.
- This is historical candidate152 footage. It cannot establish current gameplay, current screenshots, current native integration, final branding/copy or store conformance.
- Final current source captures, intentional editorial intervals and their own inspection are still required. Store publication/account gates remain unchanged. No new provider, editor purchase or extra approval workflow is introduced.

`verification.json` binds the actual input/output bytes, commands, metadata, twelve rejection records and ten frame comparisons. `source_probe.swift` and `compare_frames.py` are the independent probes. All processes from this review have finished.
