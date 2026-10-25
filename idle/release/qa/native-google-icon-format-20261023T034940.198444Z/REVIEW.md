# Google store icon encoding review

Decision: **the encoding correction is independently verified** for M5-06/S43 preparation. Renderer `300630f3e08276808012e2d8f9c59dfd562f00a2bb4316f583140fe5fa01d2c0` may enter the next candidate. No original package acceptance, platform ingestion or submission is established.

Reviewer `/root/native_verifier` inspected the root-authored diff, actual PNG headers, decoded pixels, provenance and archived prior output. The [official Google Play asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en), independently reopened on 23 October 2026, specify a 512×512 app icon with 32-bit PNG alpha and a maximum 1024KB file size. The feature graphic uses JPEG or 24-bit PNG without alpha at 1024×500.

| Actual file | Inspection |
|---|---|
| `google-icon-512.png` | IHDR 512×512, 8 bits per channel, color type 6; decoded RGBA; 25,617 bytes; every alpha value 255 |
| Previous icon | IHDR color type 2; decoded RGB, 23,049 bytes |
| RGB comparison | All 262,144 pixels identical before and after; no geometry or color change |
| Feature PNG | IHDR 1024×500, 8 bits per channel, color type 2; decoded RGB; 55,095 bytes; byte-identical to prior output |
| Feature SVG | Byte-identical to prior output |
| Source/provenance | Geometry, app-icon SVG and both system-font hashes unchanged; current output dimensions, encoding, sizes and hashes match the manifest |

The renderer was executed in a disposable minimal workspace containing only its source, native geometry source and source SVG. It reproduced the icon PNG, feature PNG, feature SVG and provenance JSON byte-for-byte. The script and resulting copies are retained here; live output was never overwritten. The first review fixture used macOS’s `/var` alias while the renderer resolved `/private/var`, causing only the provenance source-path key to differ; that attempt and explanation remain preserved. Using the canonical workspace path reproduced the entire manifest exactly.

The new icon was visually inspected: the existing lighthouse, beam, star and water-line artwork remains intact, with no added badge or promotional text. This format review does not replace the broader store creative review or prove Play Console acceptance.

`inspection.json` contains raw IHDR-derived values, actual hashes, reproduction results and scope limits. `verification.json` seals the review inputs and outputs. No Flutter, device, native catalogue, gameplay source, geometry, font, original criterion or status was changed.
