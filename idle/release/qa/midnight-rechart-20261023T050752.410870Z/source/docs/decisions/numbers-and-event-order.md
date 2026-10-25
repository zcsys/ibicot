# Production numbers and event order, version 2

Status: implemented in the provisional pure-Dart `tideglass_core` package and tested on the host Dart VM. Native Flutter qualification, mobile performance and independent production acceptance remain separate gates. The Python reference and economic constants are unchanged.

## Quantities and rounding

| Quantity | Representation | Rule |
|---|---|---|
| Wallet and lifetime Radiance | Nonnegative `BigInt` micro-R | One micro-R is `10^-6` Radiance. Never converted through `double` for settlement |
| Charts and Survey Notes | Nonnegative `BigInt` integers | Charts use exact entitlement comparison; Notes use integer grants |
| Counts and local revision | Nonnegative Dart integers | Five counts; native integer representability remains a runtime resource limit, not an intentional economy cap |
| Rates and multipliers | Signed `BigInt` fixed point, scale `10^24` | Deterministic arithmetic; no platform floating-point logarithm or square root |
| Elapsed time and timer phases | Nonnegative integer microseconds | Remainders persist; UI frame rate does not control earnings |
| Fractional earning residue | Integer numerator modulo `400 × 10^24` | Carried across advance calls, saves, timer boundaries and Rechart |

Price settlement is defined on a canonical cumulative curve. For tier index `i` (zero based), base price in micro-R is `b_i = 30 × 20^i × 10^6`, and:

`T_i(n) = ceil[b_i × 25 × (28^n − 25^n) / (3 × 25^n)]`.

Buying `k` structures from ownership `n` costs exactly `T_i(n+k) − T_i(n)`. This preserves geometric growth `q = 28/25 = 1.12`, and single, bulk, maximum and split purchases telescope to the same integer price. The difference from the unrounded mathematical batch is strictly less than one micro-R. A purchase one micro-R below the settled price fails; test tolerances never affect affordability.

The gifted first Skiff contributes ownership and output only. Its cumulative-curve position affects the next cost, as in the reference, but creates neither lifetime income nor a wallet gift.

## Exact prestige boundaries

Lifetime and the reference scale both use micro-R, so `L0 = 10^15`. Entitlement is the greatest integer `P` satisfying:

`P^20 × L0^13 ≤ 10^20 × L^13`.

The implementation computes the exact integer twentieth root of `floor(10^20 × L^13 / L0^13)`. Integer Newton iteration is corrected against exact powers. It does not use a floating-point epsilon, logarithm or approximate exponent to award Charts. The next threshold is the smallest integer micro-R value satisfying the corresponding inequality.

Rechart requires `L ≥ L0` and new entitlement above awarded Charts. It resets counts to `[1,0,0,0,0]` and wallet to zero, retains lifetime, timer phases, queued Focus, Notes, numeric residue and saved autobuy selection, and awards only the entitlement difference. Repeating it without earnings is rejected. State import rejects awarded Charts above exact lifetime entitlement and cannot accept a positive award below the first-reset gate.

## Deterministic square root and logarithm

The permanent multiplier uses an integer square root on the scaled ratio. The square-root component is rounded down with absolute multiplier error below `10^-24`.

For synergy, normalize `(25+n)/25` to `[1,2)` with an exact binary exponent, then evaluate `ln(x) = 2 × atanh((x−1)/(x+1))` by its positive odd-power series. Here the series ratio is at most `1/9`. Every operation truncates at 24 decimal places. `ln(2)` uses the same deterministic algorithm, and the integer binary exponent is added exactly. The intended conservative absolute error budget for this normalized calculation is `10^-20` in `log2`; bounded reference cases currently compare output within `10^-12` relative error. This is a conservative implementation budget, not an externally certified numerical proof at every representable state.

Fixed-rate production is deterministic at that chosen approximation. High precision does not make irrational rates exact. Multiplication error scales with producer count and permanent power; use relative-rate bounds and actual boundary tests rather than claiming a universal one-micro-R lifetime error. Charts and price decisions continue to use exact accounted integer quantities.

## Timeline ordering and policy

An `advance` call has no access to wall time, files or networks. Its caller supplies elapsed duration and whether it represents an offline absence. The core advances to the next affordability, timer or offline-rate boundary:

1. Earn over the preceding half-open interval using its old rate, old bonus and applicable offline weight; carry fractional earning residue.
2. At the boundary, resolve Focus expiry, Support expiry, Focus generation, then Survey completion in that order.
3. Advance the fixed-offset account-day high-water mark and expire old contract slots. Online play assigns new contracts at the boundary; offline play leaves unmaterialized slots for the return snapshot.
4. Evaluate the selected plan's opt-in automatic Rechart. It requires at least 100 Charts, the explicit minimum run duration, and the explicit minimum additional-Chart threshold. Then perform affordable saved-policy purchases. Recompute output and candidate investment after each purchase.
5. Return the new immutable state; player commands submitted afterward observe the completed boundary.

Boundary purchases also occur at the final instant of an advance call. Splitting a replay into smaller calls therefore does not postpone an otherwise affordable purchase. The local revision can differ when calls are chunked; economic quantities, timer state and chosen purchases must match.

The initial autobuyer is the documented single-purchase marginal-network-output/cost heuristic. It waits for the chosen candidate even when a lower-efficiency alternative is currently affordable. Equal comparisons choose the higher tier. It is disabled before ten awarded Charts and is a saved opt-in switch. The alternative priority policy waits for the first unlocked tier in the saved five-tier priority order. Neither policy claims global optimality.

The Python float policy can choose a different tier when cross-tier efficiencies are almost identical. Under the production settlement rule, the idealized first run reached initial prestige at 1,005.902727 seconds with counts `[23,23,23,30,28]`, versus the reference float policy's 1,005.033849 seconds and `[23,30,23,23,28]`; both made 126 purchases. The timing difference is approximately 0.0865%. This is disclosed policy/settlement sensitivity, not silently widened discrete conformance. Replaying the reference's actual purchase-command sequence in the production core matches its counts and milestone times within one millisecond.

Saved plans have one free base slot and at most five extra slots costing 50 Notes each. Automatic Rechart is disabled by default and cannot be configured before 100 Charts. Its minimum additional Charts and positive minimum run seconds are explicit user conditions, not a forecast of mathematically optimal reset time. Reset threshold and minimum-run expiry are events in the same online/offline timeline.

Core events include economic version, local revision, kind, timestamp and deterministic details. They are local transition identities, not globally trusted commercial or claim receipts. The persistence/claim service must prefix or bind its own branch/operation identities and atomically commit state with settlement and deduplication data.

## Offline time and daily queues implemented here

Offline earning weight is `1` through 24 hours, `1/4` for the next 48 hours, and zero thereafter. Focus expiry and queue generation use actual elapsed time independently. A Focus charge queues 600 real seconds at +20%, and multiple charges extend duration. Surveys auto-repeat every eight hours until three completed surveys are stored; collection grants ten Notes per completion exactly once. Focus stores twelve charges generated every two hours.

At capacity, generation pauses without hidden overflow. Reaching capacity at a completion boundary leaves phase zero. Collection/activation restarts from that saved phase. Below capacity, fractional phase is retained across advancement and saves. This implements one daily collection without a requirement for two-hour visits.

**Chunking contract:** an offline continuation must pass the original absence's already simulated duration as `offlineElapsedBefore`. Starting every chunk at zero would incorrectly renew the full-rate window. The storage transaction must record the returned state and its advanced settlement cursor together. The core alone cannot prove a return was claimed once or that device wall time is authentic.

An event budget causes an exception before any caller-owned state is mutated. The caller may retry with smaller chunks while carrying the offline offset; it must not silently drop elapsed time. Device throughput and background replay UI still need measurement.

## Serialization and remaining work

`GameState.toJson/fromJson` uses exact canonical decimal strings for all BigInt values, strict state keys, and explicit state/economic/event-order versions. Current state and event-order versions are 4. Versions 1 and 2 are explicitly migrated with an empty Support ledger; v2 retains its existing daily contracts, statistics, collectibles and plans. Version 3 preserves its Support values and migrates opaque receipt history into frozen deny-lists; new actions use bounded monotone identities described below. Version 1 is explicitly migrated, preserving money, Charts, all old timers, elapsed time and numeric residue. Newly tracked historical counters receive conservative recoverable history: current structures minus the gift for purchases, one previous Rechart when Charts exist, and old Note balance divided by ten for Surveys (v1's only Note source). Last-Rechart time initializes to current elapsed time, avoiding an immediate automatic reset based on invented history. New daily ledgers, collectibles and conditional plans begin empty/disabled. Other unsupported versions fail closed. Local saves wrap this gameplay payload in the independently reviewed envelope. The current engine embeds baseline constants; remote configuration loading/digest qualification remains an integration responsibility before accepting M1-04.

### Daily assignment and receipt rules

- The account seed and UTC offset are chosen once. A stable FNV-1a function selects contract families and available discovery kinds; reloads do not reroll. Offset/seed changes are rejected after initialization. The account-day high-water mark never decreases after clock rollback. Refresh also clamps requested UTC to the already established anchor-plus-elapsed time, so a backward clock cannot postpone the next midnight.
- Three slots per retained day use stable `contract:seed:day:slot` identities, with at most seven daily sets. First initialization grants today's slots only. After an offline return, missed slots materialize at the current snapshot; they receive no invented earnings or purchases from before their assignment.
- Restore targets are `ceil(600 × unboosted rate)` whole Radiance, stored in micro-R. Build targets are `min(5,max(1,floor(300 × unboosted rate / cheapest unlocked price)))` structures. Discover targets one available calibration/archive/challenge interaction. The client/content layer supplies which discovery routes are unlocked.
- Snapshot rate and cheapest price never change after assignment. The one free reroll changes family, retains that original difficulty snapshot, resets progress baselines to the reroll moment, and preserves the same slot identity. Claimed contracts cannot reroll.
- A successful claim atomically adds ten Notes and 250 XP to the currently selected pass (`pass.01` in the first-season implementation), marks the stable contract claimed and records its credited pass. Replay rejects the claimed slot. Notes/XP do not enter Radiance or lifetime production. Existing assignments progress offline, while Rechart retains their baselines and claim flags.
- Calibration validates one of twelve stable pattern IDs. Puzzle and accessible paths call the same completion command: consume one Focus charge, queue 600 seconds at +20%, record the collectible once, and record the discovery completion. Stable operation IDs make retries inert; repeated intentional completions consume another charge but do not duplicate the collectible.

Daily grants are implemented within one local progression branch. They do not prove cross-device/account-authoritative receipt delivery; cloud conflict selection must still avoid adding divergent branches. The separate paid entitlement/service ledger remains required.

Implemented: five-tier purchases and milestones; exact lifetime/Charts; synergy; saved purchase/reset plans and Note-priced slots; Focus and Surveys; calibration completion and persistent statistics; real-time Focus expiry; offline weight and account-day boundaries; seeded contracts, reroll, seven-day backlog and local idempotent Note/XP claims; immutable commands; previews; exact state serialization and explicit v1/v2/v3 migration; local shared Support grants, queued boosts and genuine offline salvage claims.

Not yet implemented in this core checkpoint: archived pass switching and external store/ad verification. Authored challenge/event and campaign runtimes are owned by the separate content package and require their own integration evidence. Persistence integration has separate non-author host evidence, but native crash/power-loss tests and full service integration are still required. The implemented daily subset does not close the full v1 gate.

## Executable evidence

From `game/core`, run:

```sh
../../tool/dart pub get
../../tool/dart analyze
../../tool/dart test
```

Tests consume the original bounded fixture file, exercise exact one-micro-R thresholds, 1,000-digit lifetime earnings, count-10,000 prices, invalid imports, split-batch price equivalence, fractional earning continuity, online/offline policy parity, capped queues, real-time bonus expiry, and the original first-run purchase policy. These are host production-core tests, not device, receipt-verification or player-study evidence.

## Support, salvage and bounded receipt identities (state/event version 4)

The local allowance has six account-day slots and stable `support:seed:day:slot` token identities. Briefing and verified-ad adapter routes share one command and allowance. A briefing source is canonically `briefing:seed:day:slot`. An ad source is `ad:seed:day:slot:64-lowercase-hex-receipt-digest`; the digest is metadata from a separately verified completion, not verification performed by this core. The platform/service adapter must validate the real completion and its bound account/day/slot before invoking the grant. No-fill/failure does not call it. Old-day requests and mismatched slot/day source IDs reject. Current-day source identities are stored only in the at-most-six tokens, so they expire without permitting an earlier day's request to become valid again. Frozen pre-v4 source deny-lists remain unchanged.

Unspent tokens expire when the fixed-offset account-day high-water mark advances. Each consumed boost token adds 1,200 real seconds at +25%. Queued effects survive Rechart, expire using actual offline elapsed time and may cross midnight. Focus and Support add to 145% of unboosted output. Six tokens yield at most 1,800 constant-rate production-equivalent seconds, without claiming that bound for compounded trajectories.

Salvage capture requires `OfflineSettlementRequest(sequence: state.nextSettlementSequence, fromUtc: savedCursor, throughUtc: requestedEndpoint)`. The adapter captures this request before simulation and retains it for retries. The request's canonical identity includes account, sequence and both UTC endpoints. New sequences must be exactly the previous finalized sequence plus one. A request before the last finalized UTC endpoint rejects even if relabelled with a new sequence. When an account clock exists, a new request cannot begin before the already produced anchor-plus-elapsed cursor either. Offline simulation without a request earns normally and creates no caches, preserving isolated challenge/event behavior. The old arbitrary `offlineSettlementId` path rejects new operations.

The production integral captures complete, nonoverlapping 300-real-second slices. It applies the actual full/quarter offline weight and actual ownership/policy timeline, excludes Focus/Support bonuses and earlier salvage rewards, and truncates each completed slice below one micro-R. There is no slice beyond the credited 72-hour window. The inventory retains the six latest complete slices and discards an incomplete final slice without inventing earnings. On finalization, retained slices freeze the final unboosted rate. Bonus is `min(sliceMicros, floor(300 × frozenSettlementRate × 10^6))`; later purchases or Rechart cannot alter that cap.

One immutable claim consumes a current-day token, marks that cached slice claimed, and adds the bonus to wallet and lifetime. Persist that result before another purchase/reset. A repeated claim rejects without consuming its new token. Only genuine timeline production enters future slices, so a match cannot be matched again. Old slice receipts no longer need an ever-growing new set: claimed flags live in the six retained caches, and source sequence/UTC high-waters prevent an evicted slice from being recreated. The compatibility `claimedSliceIds` getter projects at most those six current IDs. Frozen schema-3 claim IDs remain a migration deny-list and are never appended to by new claims.

For chunking, pass the SAME request, the exact `offlineElapsedBefore`, and `finalizeOfflineSettlement: false` until the last chunk. The active request, source elapsed cursor, partial unboosted numerator and slice offset persist. A changed request or offset rejects. The final chunk must end at exactly `throughUtc`; shorter finalizations and overshoots reject. Only finalization advances the sequence/UTC high-water and stores one most-recent identity for diagnostics. Pending caches cannot be claimed. Event-budget failure leaves the original immutable state untouched; retry or continue from the last committed partial snapshot. The adapter commits returned state and the corresponding wall cursor atomically, including partial snapshots. A failed post-rename write may already have committed: reload before retrying, never manufacture a new identity for the same interval.

Discovery operations use `operationSequence: state.nextDiscoverySequence`. Exactly the next sequence succeeds; gaps, old sequences and new opaque `operationId` strings reject. The sequence increments atomically with the discovery counter and any calibration charge/benefit. A failed calibration activation does not consume it. `completeCalibration` defaults to the next sequence for a new intentional action, but callback retries must reuse the captured explicit sequence. Only a logarithmically growing integer counter remains, with no per-interaction receipt growth. Original opaque discovery IDs remain frozen and reject replay, including when supplied alongside a new sequence.

Migration preserves prior money, timers, claims and opaque histories. Schema 3's current slices recover their claimed flags from the original list. Its clock anchor plus elapsed time seeds the new UTC high-water. If finalized legacy settlements exist without an account clock, capture rejects until `initializeReceiptCursor(state, persistedEnvelopeCursor)` supplies the independently saved cursor; that explicit handshake grants no production. An already-pending v3 accumulator stays intact and blocks new advancement. `finishLegacyOfflineSettlement` requires its exact frozen identity, exact carried offset and a valid final UTC cursor. It settles only the remaining duration, freezes caches, and records that single migrated legacy completion before new sequenced returns are accepted. This is the one permitted addition to a frozen old settlement deny-list. New opaque operations cannot use the recovery path.

The legacy arrays can already be large; migration preserves them rather than silently dropping replay evidence. Fresh production arrays stay empty. An existing save already exceeding the persistence decoder's 2 MiB limit still needs explicit recovery tooling; this change does not claim to load an arbitrarily oversized legacy file. Fresh growth is limited to fixed inventory/slot counts and numeric counters, rather than the number of interactions. It does not authenticate device wall time, establish cross-device authority or merge divergent save branches.

Executable workload evidence: 20 account-calendar years with 87,600 archive discoveries, 87,600 five-minute return settlements and 43,800 salvage claims produced a 12,008-byte core JSON state. It retained 21 daily slots, six tokens, six cached slices and six current slice-claim flags; fresh legacy receipt arrays remained empty. This is a receipt-growth stress workload, not a simulation of continuous 20-year economy/retention. Tests additionally exercise schema 1/2/3 persisted-shape fixtures, opaque-ID deny-lists, copied old UTC intervals, sequencing gaps, exact final endpoints, chunk save/reload, event-budget abort, and real repository interruptions after flush and after rename. These are host transaction tests; external receipt authenticity, device power-loss behavior and account/cloud reconciliation remain separate release gates.

## Shared contract alternative interface

`DailyContractAlternative` is an explicitly trusted in-process gameplay interface used by `game/events`. `claimContract` keeps its ordinary behavior when no alternative is provided. With an alternative, the contract identity must match, its receipt identity must be nonempty, and its qualification method must pass. Retention and the existing claimed flag are still checked before the same single ten-Note/250-XP grant. It is not a network claim or a store-verification primitive. The events implementation binds the original daily snapshot to an actual pinned event run and frozen post-assignment production target. Its own package tests exercise wrong runs, prebinding earnings, expiry, rerolls and main/event duplicate claims. The main `DailyState` remains the sole pass-XP ledger.
