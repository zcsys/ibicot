# tideglass_events

Pure Dart production runtime for the isolated Night of Returning Stars fleet and cosmetic pass. It depends on the exact core economy and keeps seasonal quantities outside the main GameState. No UI, network purchase verification or store implementation is included.

## Runtime contract

```dart
final definition = SeasonDefinition.fromJson(decodedSeasonManifest);
final seasonEngine = SeasonEngine(definition);
final passEngine = PassEngine([definition]);
var season = SeasonState.initial(
  definition, SeasonSchedule(configuredStartUtc), nowUtc,
  runId: stableAccountSeasonRunId,
);
var pass = PassState.initial([definition]);
season = seasonEngine.advanceTo(season, returnUtc, offline: true).state;
```

The rollout adapter supplies the start date. No production launch date is invented by this package. The saved schedule is exactly 28 UTC days. Rules version, full definition digest and base economy version are pinned. Keep the exact old definition available when restoring an older pinned run; do not reinterpret its state using a newly deployed definition. Unrecognized definitions reject and require a separately reviewed migration.

`SeasonEngine` exposes `advanceTo`, `purchase`, `configurePolicy`, `resumeArchive`, `pauseArchive`, `claimMilestone`, rate/price/affordability previews and badge IDs. Automation is free in this isolated fleet. The default is off. Both policies use exact core prices, milestones and carried fixed-point remainder. The event matrix is `[[10,20],[25,10]]` percent, with immediate synergy and no prestige multiplier. `rechart` explicitly rejects. Main wallet, Charts, Notes, Focus, Support, daily ledgers, purchased ownership and plan objects cannot be parsed as fleet fields. Its five-field serialized fleet contains only counts, wallet, cumulative event production, elapsed time and numeric remainder.

Live time is the half-open interval `[start,end)`. The absolute settled-through cursor never rewinds; repeated or earlier times earn nothing. A return crossing the end settles only the live portion and archives the saved fleet. The archived fleet pauses until `resumeArchive`, which retains earned progress and skips the paused interval. A late profile begins with the same gifted Skiff and zero currency, then may resume the archive. `pauseArchive` and `resumeArchive` expect the controller to settle a return first with the correct offline options. They settle remaining foreground elapsed time themselves. Archive completion remains available without a purchase.

Offline advancement uses the main game's 24-hour full, next-48-hour quarter, then zero envelope. When chunked, pass the original absence's already simulated duration as `offlineElapsedBefore`. Time before a future season start still belongs to that absence. Core main queues generated during the reused numeric advance are discarded; they never exist in the serialized event state or expose reward actions. Parent/controller must advance the main saved policy alongside the event and atomically commit both partitions. Event play itself does not advance or mutate a main GameState.

## Shared XP and rewards

`main.daily.passXpById` remains the only XP ledger and `main.daily.selectedPassId` its only destination selector. PassState contains pinned definition digests, cosmetic/fragment claim receipts, and retained event-objective bindings. It has no XP field, premium-owned flag, multiplier or economic grant. Each pass has 30 levels × 500 XP. Selection changes one key; existing totals are preserved. Live and archived passes can be selected, and an upcoming pass cannot. The production catalogue contains Season 1 only; multiple-pass selection is exercised using a test-only second catalogue, not a promised Season 2 asset set.

- `selectPass(main, pass, season)` selects one available pass for future contract claims.
- `bindEventAlternative(main, pass, contractId, season)` records a frozen ten-minute event-production target and current event lifetime baseline for that retained slot. Production before assignment cannot count. The definition digest, run identity and original daily objective fingerprint are pinned. A native reroll invalidates that binding; `pruneAlternatives(main, pass)` removes stale fingerprints, claimed slots and expired slots. Rebinding the rerolled slot freezes a new target and baseline from current event production, excluding all earlier event earnings. The same current fingerprint cannot be rebound, and reloads or purchases cannot reroll its target.
- `claimDaily(main, pass, contractId, {alternativeSeason})` delegates to the existing core `claimContract`. Main and event routes share that slot's claimed flag, ten Notes and 250 XP. There is no event bonus XP. An alternative must match the bound run, identity and target; expired slots and repeated claims reject. Binding a slot does not erase the native route; either route consumes the same single receipt. Save returned main and pass together.
- `claimFreeReward(main, pass, passId, rewardId)` checks shared XP and the unique slot receipt. It grants only the defined cosmetic or narrative fragment.
- `claimPremiumReward(..., entitlementReader: reader)` awaits an explicitly injected `VerifiedPassEntitlementReader`, requires matching account/pass identity and a verification receipt, then uses the same level threshold. The adapter must actually verify and restore store/account ownership; the concrete value type is an in-process result, not cryptographic proof. The package implements no local `premiumOwned=true` shortcut. Serialize the awaited command and commit its complete returned state before accepting another command.
- `cosmeticIds(pass)` derives only earned free cosmetics and `fragmentIds(pass)` derives narrative fragments. Local premium claim/verification strings never establish paid ownership. `verifiedCosmeticIds(main, pass, entitlementReader: reader)` reconciles every unlocked premium appearance against independently verified account/pass ownership and authoritative XP, so forged local receipts cannot grant appearances and missing local delivery receipts do not block legitimate restoration. No reward modifies core power. Previously earned free and premium rewards remain available after archive; premium access still requires the verified adapter.

The narrow core `DailyContractAlternative` interface is trusted gameplay composition, not store or server verification. The events package validates actual saved scenario progress before offering an implementation to the core. Core validates identity, nonempty alternative receipt, qualification, current slot retention and the existing claimed flag; it retains sole grant authority. A caller implementing arbitrary qualification is trusted code and must not expose it as a client/network claim payload.

## Authored content and evidence

`content/season.01.json` supplies all 30 free slots (ten cosmetics, twenty complete story fragments), ten premium cosmetics, start/live/end/archive copy and three cosmetic-only badge milestones. Reward IDs match the reviewed launch manifest. Cosmetic names/copy do not certify finished visual assets or delivery through the native client. Badge thresholds are 10^9, 10^13 and 10^15 event Radiance, newly authored here because the blueprint prescribed personal milestones without numeric thresholds.

`tool/season_pacing.dart` generates `content/season.01.pacing.json`. This is deterministic fixed-policy host simulation with no purchased effects; it is not player pacing or retention evidence. The first provisional badge set completed too quickly in that simulation and was revised before integration. The current free best-payback policy reaches the final badge between day 14 and day 21 in continuous simulation. A single uninterrupted 28-day absence receives only the existing 72-hour envelope and does not earn that final badge. Native replay performance, policy variety, human pacing and the real 28-day seasonal study remain launch gates.

Pass reward receipts are bounded at 40 for the v1 catalogue. Active alternative bindings are pruned against the at-most-21 retained daily slots when binding or claiming. Core schema 4 uses monotone discovery/settlement identities and preserves pre-v4 opaque sets as frozen deny-lists. This package does not silently discard receipts.

From this directory:

```sh
../../tool/dart pub get
../../tool/dart analyze
../../tool/dart test
../../tool/dart run tool/season_pacing.dart > content/season.01.pacing.json
```

Tests cover definition completeness, original reward IDs, fixed matrix reference values, half-open start/end boundaries, offline weights and chunk/reload parity, pinned versions, main/paid-field rejection, archive continuation, one selected pass, the 20-completed-day free pass budget, prebinding exclusion, native/event duplicate prevention, verified-adapter negative cases, all forty reward slots, and actual repository atomic save/reload/interruption. These host tests do not establish external entitlement authenticity, device crash durability, player retention, asset completion or native UI acceptance.
