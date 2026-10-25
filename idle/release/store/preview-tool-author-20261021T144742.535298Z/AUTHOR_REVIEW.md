# Native preview editor author proof

The macOS26 AVFoundation tool trims and scales a real silent recording with aspect-fit padding and fixed30fps sampling. It never crops UI, changes game speed, inserts invented gameplay or discards source audio; it rejects source recordings containing audio rather than silently losing it. Current SDK configuration APIs compile without warnings.

Historical candidate152 footage is used only as a tooling control. The final export is20s,886×1920 H.264,600 decoded frames at exact1/30-second intervals starting0. Source bytes remain unchanged. Four rejection checks preserve existing output/source and reject short/out-of-source intervals. Root visually inspected beginning/middle/last selected frames; the historical test interval ends mid-transition and is not final release creative.

Initial sparse-frame passthrough did not preserve exact trim timing; it is retained. Fixed-frame source sampling repairs this. The first compressed-sample inspector counted encoder priming/edit markers; the corrected inspector decodes actual display frames and uses output presentation timestamps. Both prior metadata records remain.

The encoder requests11Mbps but actual content-average is2.07Mbps; this is a silent review edit, not submitted or declared App Store conformant. Apple current specifications were checked at https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications/ on21October2026. The final current native recording, editorial interval and different-reviewer check remain pending.
