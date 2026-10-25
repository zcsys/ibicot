# Independent Android local media review

**Pass for the bounded local selection; no new media defect found.** Independently reviewed the root-authored packet `release/store/media-3b00-android-20261025T150512.754160Z` against successful native gallery `integration-android-20261023T085458.804768Z`, frozen production candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59`. The main, chapter and challenge stills plus the 19-second preview are supported local candidates. Season remains internal only. This does not accept M5-06, S43, a store submission, physical-device performance, final sound direction or the complete v1.

## Exact source and independence

Rehashed 25 author-packet files, all 19 author input pins and 15 native verification evidence files. The successful native report, its captured harness/driver/recorder, result, log, manifest, raw PNGs and original MP4 remain intact. The source video hash is `655ce0a9ad3fbbb46fcde000643a8ecd58658aa507a003c79358435de7e531ef`. No old failed draft was deleted or overwritten; prior failures remain separate from this fresh successful gallery. No Flutter, native or device command was run for this review.

The reviewer previously authored parts of the capture harness and ACK protocol. Their approval is not self-issued here: the separately authored lead reviews pinned in `packet-analysis.json` cover those exact changes, braces, cadence and recorder headroom. This review independently evaluates the author's actual export packet and native-to-output bridge. Earlier phone/tablet reviews are not repeated.

## Whole-image checks and visual findings

All four original screenshots are 1080×1920, RGBA8 with every alpha sample exactly 255. The outputs are PNG RGB8 (IHDR color type 2), no alpha/tRNS, with the source sRGB chunk preserved. Every RGB sample in every image matches the actual native source exactly: no quantization, crop, resize, compositing or pixel cleanup. `actual-png-analysis.json` records all four source/output hashes and whole-image results.

The reviewer opened all four actual exports. Main shows the restored harbor and producer UI; chapter shows chapter 4, Three Ways Through, and the three family objectives; challenge shows A Shallow Channel and its actual fleet. They are readable, full-frame and free of the former test pointer overlay. Native OS status/navigation chrome is retained. The actual Season Fleet shows Returning stars, Night of Returning Stars and an explicit local 28-day preview window (16 October–13 November 2026 UTC). It is excluded from the listing selection, and is not evidence of a completed live season or public schedule.

## Actual video checks

| Property | Source | Selected output |
|---|---:|---:|
| Dimensions | 1080×1920 | 1080×1920 |
| Duration | 28.5978778 s | 19 s |
| Decoded frames | 44 | 570 |
| Nominal cadence | 1.5386 fps | approximately 30 fps |
| Audio tracks | 0 | 0 |
| Interval and speed | original real time | 0.5–19.5 s, speed 1 |

Independently decoded output metadata and five actual frames. Timestamp gaps are uniformly 1/30 second; output time ends at 18.9666667 seconds. Actual H.264 avcC is High profile, level 4.0. Measured estimated bitrate is **1,550,393.625 bps**, distinct from the requested 11 Mbps. The output is silent because the raw capture has no audio; no source audio was discarded. The raw sample gaps of 0.34577–1.08206 seconds and 44 total frames explicitly limit the captured motion. Encoding held source samples at 30 fps does not add captured motion or establish device frame-rate performance.

Five independently decoded output frames were compared with the exact source times at output time plus 0.5 seconds. Source held-sample timestamps and all comparison results are recorded in `packet-analysis.json`. Mean absolute channel error from compression/color conversion is 3.33–4.78; horizontal/vertical flipped controls are substantially worse. This supports orientation and temporal correspondence, not lossless video. Full-frame geometry matches with no padding or cropped content. The initial convenience source sample run used a different middle timestamp; it is preserved and superseded for comparison by `source-exact-sampled`, not silently removed.

The reviewer visually inspected the five output frames: harbor, producer list after the actual purchase/scroll, Logbook, chapter 4 and passage fleet. No test pointer, invented UI, retouching, or debug panel was seen. The interval ends before the Season route. Real hit-tested gestures, native completion and seeded fixture disclosure remain explicit; this is implemented presentation, not natural-player pacing, paid ownership or player-study evidence.

## Original scope boundary

M5-06 remains governed by its original clause: “Remove placeholders, integrate final sound direction, and prepare representative screenshots, icon and short footage.” Its M4-07 dependency and in-progress status remain unchanged. S43 still requires “Changed screens rechecked on targets; final screenshots/footage represent shipped product.” These outputs close the particular absence of independently inspected current Android local exports. They do not establish a shipped release, store-ingestion/encoding acceptance, final sound direction, every asset's production acceptance or the remaining upstream/external conditions. The measured bitrate, silent tracks, emulator capture cadence and internal-only seasonal material must remain disclosed in later handoffs.

The proposed evidence-note correction is in `m5-06-note-proposal.json`; it makes no metadata change. The existing named M4-07 client judgment remains valid within its narrower clause and unresolved M4-06 dependency.
