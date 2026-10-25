# Tideglass client experience

Status: implemented client slice in progress; native qualification, complete v1 content and human tests remain open.

## Four critical flows

1. **First purchase.** A free Spark Skiff starts producing immediately. A dismissible onboarding card identifies Radiance, the next skiff and the permanent skyline. Producer controls show current count, next output change and cost. Unaffordable purchase controls explain the wait; unlocks explain the previous-tier count. Large buy controls work without timing or repeated taps.
2. **Rechart.** The Atlas shows currently awarded Charts and the lifetime entitlement available to claim. Confirmation states the exact new Charts and before/after power; the wallet and fleet are rebuilt, while lifetime earnings, Charts, archive/cosmetic ownership and time-bound effects persist. A second deliberate action executes the transition. No automatic reset is on by default.
3. **Return.** Lifecycle resume settles elapsed time once using the core's offline engine. The return panel states elapsed time, full/quarter-rate credited time, Radiance earned and the policy used. The reward is committed before the acknowledgement; dismissing cannot claim twice.
4. **Recovery.** The client shows a recoverable load error with retry and export/diagnostic entry points. It never silently replaces a damaged save with a new harbor. Starting anew is a separate confirmed action and retains the recoverable file until the persistence layer safely commits a new profile.

## Visual language

Deep ocean navy, moonlit teal, warm amber. Use a spacious illustrated harbor as the visual anchor; purchase success briefly lights the producer's part of the scene. Five original code-native silhouettes are drawn from reusable vector geometry. These are one representative slice, not proof of all 25 finished producer presentations or seven complete harbor presentations. Constellation lines and wave motion respect the operating-system reduced-motion setting and the local preference.

The layout is a vertically scrolling phone harbor. Tablet uses a 360-pixel minimum side panel and flexible production list when space permits. Content widths are capped for readability. Interactive targets are at least 48 logical pixels. Text wraps at 200% scale. All actionable controls have semantic labels, lock and ownership states use words as well as color, and economic updates do not continuously steal screen-reader focus.

## Boundary

`GameController` dispatches immutable core commands and owns animation/tick notification only. Prices, output, progression and awards come from `tideglass_core`. It accepts a persistence adapter; save completion/error is observable. The interface never grants store entitlements or invents asynchronous service success.

No disabled shop/cloud/season screen is presented as shipped functionality. Additional features enter navigation when their real runtime and content are integrated. This slice is intentionally not declared a finished v1.

## Verification

Widget checks cover first purchase, unavailable controls, confirmation/cancellation, saved settings and narrow/large-text layouts. Native screenshot and device evidence must be captured from actual builds and recorded separately. Test coverage cannot replace player comprehension or a physical accessibility audit.
