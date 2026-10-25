# Android media — author review

Three selected screenshots and a 19-second preview derive from strict-passing native gallery `integration-android-20261023T085458.804768Z`, frozen production candidate 3b00. Earlier failed recorder/ACK attempts remain unchanged. The actual capture completed all four screenshot receipts and stopped the owned recorder; its temporary display override was restored.

The author visually inspected all four exported PNGs and five decoded preview frames. The stills show the harbor, chapter 4 objectives, a passage fleet and the actual Season Fleet. Text and controls in these views are readable; no test pointer is visible. The Season still explicitly identifies a local 28-day preview schedule and is internal only. The selected preview shows the harbor, producer list, Logbook, chapter and passage screens; its interval ends before the Season route. Native OS status icons and navigation bar are retained. There is no retouching, inpainting, cropping or invented UI.

All four native PNGs are opaque RGBA8 at 1080×1920. Export removes opaque alpha, preserves native RGB samples and the sRGB color chunk, and does not resize. Unlike the earlier iOS native 16-bit inputs, these Android inputs require no quantization. Whole-image independent comparison is a separate review step.

The raw source has 44 decoded frames over 28.5978778 seconds, nominal 1.5386 fps, with sample gaps 0.34577–1.08206 seconds. The preview selects seconds 0.5–19.5 at original speed and full display dimensions, with no padding. It encodes 570 frames at 30 fps by holding displayed source samples; this does not create additional captured motion or establish device frame-rate performance. The source and output are silent. H.264 avcC confirms High profile level 4.0. Requested 11 Mbps differs from measured estimated 1,550,393.625 bps; no store encoding qualification is claimed.

The seeded production UI demonstrates implemented presentation, not natural progression, paid ownership, human pacing, physical-device performance or a completed season. This packet is a local media candidate pending independent review and later store requirements. No program or scope status is changed.
