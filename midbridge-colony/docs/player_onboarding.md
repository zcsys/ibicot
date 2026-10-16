# Player app: first playable case

Open `/play.html` on the economy service. The current UI shows only company cash, a price slider, a responsive sales-per-tick EMA, inventory, last-tick production, unit cost and storage boxes separating raw inputs, finished goods, machinery and empty space. Scripted work advances 1.3 times per second (approximately 769 ms) while the page is visible; the sales EMA weights each new observed tick at 65%, and duplicate ticks do not update it; the last 120 work ticks seed it after reload. Personal identity is created silently and remains persisted. Name entry, finance panels, bonuses and acquisition controls are removed from this minimal screen; their backend actions remain available for subsequent UI work. Existing owners see live company cash and an EMA of observed tick sales, without inventing observations for missed ticks. This is a separate page; the administrative dashboard is unchanged. No per-player economy is created or advanced.

## Person, employment, ownership

`economy/server/players.py` owns the SQLite store, default `data/players.sqlite3` (ignored by Git). Override with `ECONOMY_PLAYERS_DB`. Schema version 1 is initialized automatically:

- `world_catalog`: catalog revision guard; mismatches require explicit migration.
- `players`: stable UUID, display name, personal balance in integer cents, creation date.
- `sessions`: hashed random device credential linked to a person. The browser receives an HttpOnly, SameSite=Strict cookie (Secure under HTTPS).
- `employment`: a person's scripted employer and operating state, including progression, revision, limited history and acquisition receipt. The employer is never inserted into the live company registry.
- `ledger`: signed salary, bonus and purchase entries with resulting personal balance.
- `ownership`: unique `(world, tier, company_id)` ownership linked to a person, purchase consideration and controlled selling price.

Transactions use `BEGIN IMMEDIATE`, validate funds and progression on the server, and atomically commit employment changes, wallet entries and ownership. A revision check rejects replayed actions and stale tabs. Competing buyers cannot purchase the same company. Failed purchase attempts do not debit a wallet or silently substitute another target; refreshing obtains a new offer.

This is a local device identity, not an email/password account. Clearing the cookie loses automatic access to that person. Account recovery, cross-device login and a public multiplayer authentication boundary are outside this first case. The existing dashboard and its administrative endpoints remain trusted local tools; do not expose this service as a public multiplayer server.

## Scripted employment

One employer, Meridian Works, makes the first catalog T1 product. The demo neither initializes nor reads the shared world. It uses local T1 configuration defaults and its own market state, persisted with the person. Reads do not advance prices; each successful work tick does. Raw prices fluctuate around $1.25 and sales references around $2.32 using bounded, smoothed deterministic waves. Raw target = `1.25 × (1 + .28 sin(.19t) + .10 sin(.53t))`, smoothing weight .45. Sales target = `2.32 × (1 + .18 sin(.13t + .7) + .07 sin(.37t))`, smoothing weight .30. These are authored demo conditions, not live market quotes or calibrated equilibrium predictions.

The demo is a single-line T1 C1 refinery: one raw Organics unit becomes one Biochemical Feedstock unit. It retains scripted customer demand and never submits trades to the live economy. Starting cash is $240,000 with 12,000 finished units. T1 storage, machinery footprint, production capacity and conversion cost come from local configuration defaults. Raw supply quotes come from the demo’s own fluctuation model.

Each work tick buys whole 1,000-unit raw lots toward half the goods space, limited by cash and shared storage. Production is bounded by the actual T1 line capacity, held raw inputs, finished-stock target and conversion cash. A price below input-basis-plus-conversion cost stops production but still permits sales of existing stock. Demand remains `floor(12,000 / (1 + (price/reference)^2))`. Salary is up to $500, funded from company cash after trading.

Raw purchases use weighted-average inventory basis. Production moves raw basis plus conversion into finished-goods basis; sales recognize that basis as COGS. The displayed unit cost is the current raw inventory basis plus conversion, so it changes with replenishment prices, not with the player's selling price. Weighted-average held raw stock smooths changes; without new purchases its cost basis stays unchanged even as quotes fluctuate. Existing demo profiles start with zero raw stock and retain their finished-stock basis on migration; balances and progress are preserved.

The storage view contains 80 small proportionally filled boxes and an exact numeric legend. Machinery, raw inputs, finished goods and empty space have distinct colors. There is no production-capacity row. Moving the price slider below unit cost shows an immediate warning without preventing the choice.

The backend makes financial progression eligible after two completed periods and bonus authority eligible after four. The current minimal UI exposes only price. A positive bonus up to available company cash transfers that exact amount to the personal wallet, reduces company cash and is recorded in the ledger. Bonuses are not capped by a performance score or a fraction of profits. There is no automatic replenishment funding or hidden bailout after extraction.

## Acquisition and live control

The first available unowned, bot-controlled T1 producer of the same product is offered at a fixed scenario price of $200,000. This is a deliberately authored onboarding offer, not a market valuation or book-equity formula. Buying spends personal money, records payment to an external departing owner, and preserves all acquired-company cash, inventory, machinery and liabilities. It grants ownership and price control of the existing company. The employment ends; further demo work and bonuses are rejected. The player app does not start, pause or reset the shared simulation; the existing server scheduler remains responsible for its cadence. The existing acquisition API initializes the shared world only when actually buying or viewing an already-owned live company; it is not part of the demo loop. The same separate page then displays live cash and stock and accepts live selling-price changes only for the person's owned company.

Ownership is durable in SQLite. The service projects it onto the existing controller arrays on startup, checkpoint load and administrative world reset. `ECONOMY_WORLD_ID` defaults to `local`. Use a separate player database and world ID for an independent world or test server. Catalog changes that invalidate owned companies require an explicit migration; unsupported ownership targets fail rather than being reassigned.

Physical company balances still belong to economy checkpoints. SQLite is not rewound when loading an older economy checkpoint. Back up/restore both the player database and economy checkpoint together for a consistent complete-world recovery. A service restart without a checkpoint preserves people, employment, wallets, ownership and player prices, but uses fresh economy balances under the existing service startup behavior.

## Verification

Run `PYTHONPATH=.pydeps:. python3.12 -m unittest discover -s tests/py -p test_onboarding.py` and `node --check web/play.js`. The integration tests cover cash/inventory reconciliation, demand response, unlock enforcement, ledger sums, reload identity, isolated players, stale actions, duplicate and competing acquisitions, unchanged target treasury, employment termination and restoration of ownership projection.

A reset button sits 65vh below the main controls. It restores the demo opening cash, inventory, quote, employment progression and personal balance while retaining the person and an auditable wallet reset entry. The revision stays monotonic to reject stale requests. Owned live companies cannot be reset through this action.

Net earnings per tick uses the same 65% EMA as sales. Demo earnings are posted sales less inventory COGS and salary; live company earnings include the kernel’s switching, rent and intelligence entries. The EMA updates once per new observed tick, seeds from saved demo history on reload, and clears on reset. Negative earnings display in red.

The sales EMA readout rounds to the nearest whole unit; net earnings EMA retains cents. Internal EMA calculations retain full precision.

The demo production slider sits directly under Price. It sets an integer units-per-tick target from zero to configured T1 line capacity, persists across reloads, and returns to full capacity on reset. Actual production remains constrained by raw inputs, conversion cash, output storage and the below-cost gate. A brief notice appears when constrained; the redundant last-tick production row is removed. Live-company production remains kernel-managed and does not expose this demo control.
