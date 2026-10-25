# Conditional Rechart estimate — author handoff

This implements the missing conditional-estimate portion of original M2-03/S07. It is a restricted production-engine comparison, not a claim of universally optimal reset timing. Original acceptance remains: “Show marginal network output, next threshold and conditional reset estimate with readable assumptions and no claim of a universal optimum.” Original dependency remains M2-01. No economy constant, state schema, saved plan, entitlement or acceptance status changes.

## Runtime contract

`game/core/lib/rechart_forecast.dart` adds `estimateRechart(GameState, {horizonSeconds: 86400, maximumWork: 20000})`. It uses the unchanged production `buy`, `advance`, `chooseAutoBuyTier`, and `rechart` methods. Both paths begin at the same immutable snapshot and lifetime total. The keep path retains and can spend the existing wallet. The reset path actually discards its wallet and returns to the gifted Skiff with the exact new Charts. Neither old lifetime earnings nor discarded wallet is counted as newly produced Radiance.

The explicit policy buys at opening and each whole minute. At each decision, it repeatedly selects the highest marginal network output per cost single-unit purchase and buys it if affordable. When that selected unit is unaffordable, it waits until the next minute. This does not opportunistically buy a worse affordable unit. The same active policy applies before and after the 10-Chart autobuyer unlock; it is an assumption about future player actions, not an automation grant. The preview replaces saved plans only inside its immutable projection and permits no later Rechart.

Existing Focus and Support queues retain their duration and expire through the real timeline. No future bonus activations, claims or paid grants occur. The horizon is at most 24 hours at full production, sampled every minute. Account receipts, calendar contracts, discovery history and optional cosmetic state are excluded from the projection because they cannot affect this policy's production; an independent fine-step test retains full account state and verifies the economic result across an account-day boundary.

The result contains exact integer additional-production totals, the first sampled catch-up, and a separately labeled break-even sample: the first minute after the last sampled deficit, provided the reset path remains caught up at the horizon. The copy explicitly limits this to one-minute checks through 24 hours; crossings between checks or after the horizon are not ruled out. No catch-up is reported honestly. Reconstruction means the first sampled rebuilt fleet reaching the opening unboosted rate; production continues during reconstruction. No arbitrary zero-output rebuilding time is inserted.

Unlock metadata uses exact 10/25/100 total-Chart thresholds. The next target is the next unreached unlock after the previewed claim, or one additional Chart after 100, without inventing another feature. The lifetime target uses the existing exact boundary method.

## Bounded execution and UI

The algorithm rejects unsupported rules, pending replay, excessive input magnitude, or exhausted work. A 24-hour horizon allows 1,440 samples, with a shared maximum 20,000 work units (API ceiling 50,000) and per-advance timeline budget. Partial results are never shown as complete advice. Input limits are 10,000 owned units per tier and 4,096-bit listed ledger/timer values; these are forecast availability limits, not gameplay limits.

`RechartForecastTask` runs one projection in a dedicated isolate with a three-second wall timer. Dismissal, failure, completion, or deadline kills the worker and closes its receive port. A timed-out Future alone is not used as cancellation. The main preview keeps both choices usable while calculation is pending or unavailable. The existing App Rechart dialog captures one opening snapshot for the reward/power/estimate text, and the existing actual command still owns the reset.

`RechartEstimatePanel` uses wrapping text in the existing ReadingDialog's scrolling/fullscreen layout. English copy lives in `rechart_copy.dart` and uses the existing pseudolocalization/template boundary; numbers never feed back into rules. The assumptions explicitly state buying policy, active purchase requirements, future-reset/bonus exclusions, wallet-loss/objective, retained boost expiry and snapshot age. No new asset or translation locale is added.

## Executed author checks

- Ten new pure Dart tests pass: analytic 77.25/154.5-R first-minute bonus expiration, one-second full-state counterfactual oracle, wallet-loss/objective accounting, exact 24-hour reference, no-catch-up late claim, exact unlock boundaries, unavailable/limit states, real isolate parity, and cancellation/deadline cleanup.
- The full isolated core suite passes **206 tests**, including all 196 existing cases. Earlier sandbox runs omitted the relative reference/config files; both failed logs are retained, the complete fixture layout was then copied, and the full suite passed without changing production code or assertions.
- Scoped Dart analyzers are clean for the new pure runtime/tests and staged App/panel/copy/worker/widget test. `git apply --check` passes for the full patch against the recorded live baseline.
- Seven representative 24-hour forecasts took 72–170 ms on this author host. This is not minimum-device performance evidence. Sixty additional synthetic cases found no transient crossing; that search is exploratory and does not establish monotone dominance.

The eight staged files are pinned in `staged-pins.json`; the original App and nine unchanged core library files are in `base-pins.json`. `IMPLEMENTATION.patch` includes only one modification to an existing file (`app.dart`) plus seven new files. The main economic library bytes remain unchanged. Existing numerical acceptance is not broadened to the new forecast without separate review.

## Remaining before acceptance

Actual Flutter execution and pixel inspection are the next author gate: 320/1024 pixels at 200% text, English and pseudo, all status presentations, real isolate result, every assumption and both existing actions. The final staged UI test defines twelve cases per locale and optional source-pinned image capture. This report will be supplemented with real results after the lead promotes the frozen files and grants the exclusive lane. Different-agent numerical/UI review is still required. No M2-03/S07, whole-device or release status is changed by this handoff.
