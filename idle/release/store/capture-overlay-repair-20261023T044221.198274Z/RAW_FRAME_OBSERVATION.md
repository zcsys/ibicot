# Raw pointer observation

Inspected the supplied exported preview frame 1 and the actual raw video, without changing either. The raw-frame probe decodes source frames through AVAssetImageGenerator and writes them to this new evidence directory; it performs no crop, pixel removal, masking, filtering or resynthesis.

The raw frame requested at 5.233333333 seconds resolves to the held source frame at 5.213333333 seconds. It visibly contains the gold test-pointer circle and cross over the Build 1 button. That source time corresponds to exported preview frame 1 at 4.733333333 seconds plus the retained 0.5-second source interval offset. The later raw sample at 6.045 seconds shows the same game screen after the pointer has faded.

The cached SDK confirms the origin: LiveTestWidgetsFlutterBinding.handlePointerEvent records test-sourced down pointers, and its render-view paint callback draws the circle/cross. With shouldPropagateDevicePointerEvents enabled, the device-source branch forwards the unchanged PointerEvent to the framework without adding a painted test-pointer record. DispatchEvent also forwards that branch through normal gesture dispatch. The capture-only subclass selects that existing path while retaining automated-input disclosure; it does not assert physical or human input.

This observation establishes why the existing draft needs a fresh capture. It does not claim the authored correction is already visually qualified on a native retry. All old raw/video/image bytes are retained.
