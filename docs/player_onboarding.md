# Player app: first playable case

Open `/play.html` on the economy service. This is a separate page; the administrative dashboard is unchanged. No per-player economy is created or advanced.

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

One employer, Meridian Works, makes the first catalog T1 product. The page has no company search, leaderboards or competitor comparison. It sees only a limited market brief: mean asking price among installed producers of that product, the simulation tick and up to 12 observed references. This is explicitly an asking-price average, not a transaction-weighted price. The browser caches the last brief for connection failures; mutations require the server.

Prototype scenario constants (not economy calibration): opening cash $240,000; opening finished stock 12,000; unit cost 55% of the opening reference rounded to cents; salary up to $500 per work period. The scripted employer's initial cash and stock are opening scenario endowments.

For chosen price `p` and latest available market reference `r`, demand is `floor(12,000 / (1 + (p/r)^2))`. Replenish toward 12,000 units before selling, within available company cash after reserving salary. Sell the smaller of stock and demand. Sales recognize fixed unit cost as COGS; replenishment exchanges cash for stock. Pay salary only up to available cash after sales. Operating profit is revenue minus COGS minus salary, before discretionary bonuses. Company cash and personal money remain separate.

Price is initially the only operating control. Two completed periods reveal financial statements and history. Four reveal personal bonus authority. A positive bonus up to available company cash transfers that exact amount to the personal wallet, reduces company cash and is recorded in the ledger. Bonuses are not capped by a performance score or a fraction of profits. There is no automatic replenishment funding or hidden bailout after extraction.

## Acquisition and live control

The first available unowned, bot-controlled T1 producer of the same product is offered at a fixed scenario price of $200,000. This is a deliberately authored onboarding offer, not a market valuation or book-equity formula. Buying spends personal money, records payment to an external departing owner, and preserves all acquired-company cash, inventory, machinery and liabilities. It grants ownership and price control of the existing company. The employment ends; further demo work and bonuses are rejected. The player app does not start, pause or reset the shared simulation; the existing server scheduler remains responsible for its cadence. The market brief labels a paused world, and the refresh control retrieves updated observations. The same separate page then displays live cash and stock and accepts live selling-price changes only for the person's owned company.

Ownership is durable in SQLite. The service projects it onto the existing controller arrays on startup, checkpoint load and administrative world reset. `ECONOMY_WORLD_ID` defaults to `local`. Use a separate player database and world ID for an independent world or test server. Catalog changes that invalidate owned companies require an explicit migration; unsupported ownership targets fail rather than being reassigned.

Physical company balances still belong to economy checkpoints. SQLite is not rewound when loading an older economy checkpoint. Back up/restore both the player database and economy checkpoint together for a consistent complete-world recovery. A service restart without a checkpoint preserves people, employment, wallets, ownership and player prices, but uses fresh economy balances under the existing service startup behavior.

## Verification

Run `PYTHONPATH=.pydeps:. python3.12 -m unittest discover -s tests/py -p test_onboarding.py` and `node --check web/play.js`. The integration tests cover cash/inventory reconciliation, demand response, unlock enforcement, ledger sums, reload identity, isolated players, stale actions, duplicate and competing acquisitions, unchanged target treasury, employment termination and restoration of ownership projection.
