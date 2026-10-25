# tideglass_core

Pure Dart economy and timeline for Tideglass. The package owns exact currency,
immutable transitions and forecasts; the client owns presentation and the
persistence adapter owns atomic save/settlement commits.

```dart
import 'package:tideglass_core/tideglass_core.dart';

const engine = TideglassEngine();
var state = GameState.initial();
state = engine.advance(state, const Duration(seconds: 40)).state;
final purchase = engine.buy(state, 0, 1);
if (purchase.accepted) state = purchase.state;
print(formatMicros(state.walletMicros));
print(engine.outputPerSecond(state).toDecimalString());
```

Run `../../tool/dart analyze` and `../../tool/dart test` in this directory.
See `docs/decisions/numbers-and-event-order.md` in the repository for the exact
settlement rules, precision limits, event order and offline chunking contract.

This is actual runtime code under provisional native qualification. It does not
yet implement all daily, seasonal, commerce or campaign systems.

Offline salvage capture is opt-in. Capture a request before replay:

```dart
final request = OfflineSettlementRequest(
  sequence: state.nextSettlementSequence,
  fromUtc: persistedCursorUtc,
  throughUtc: returnUtc,
);
final result = engine.advance(state, returnUtc.difference(persistedCursorUtc),
  offline: true, offlineSettlement: request);
```

Reuse that exact request when retrying. Chunked calls carry the original
`offlineElapsedBefore` and set `finalizeOfflineSettlement: false` until the exact
endpoint. Persist partial state with its matching partial wall cursor. A prior
sequence, overlapping UTC interval, changed request or incorrect endpoint
rejects. No request means ordinary production without cache capture. The old
arbitrary `offlineSettlementId` API rejects new operations.

`recordDiscovery` and retry-safe `completeCalibration` calls use a captured
`operationSequence: state.nextDiscoverySequence`. Opaque legacy operation IDs
are frozen deny-lists; new per-interaction arrays are not created. The default
calibration call treats each invocation as a new intentional action.

Support token grant/use/cache claims are separate immutable commands. Use
`briefingSourceId(state, slot)` for the day-bound free route. Ad source digests
remain metadata from an external verified adapter; they are never proof by
themselves. Persist a successful claim before another purchase/reset.

Schema 4 explicitly upgrades versions 1–3. Pending schema-3 capture requires
`finishLegacyOfflineSettlement` with its frozen identity and carried offset;
it cannot be silently restarted. Legacy history without an account clock
requires `initializeReceiptCursor` from the independent save envelope first.
The decision document details these recovery contracts and the 20-year receipt
workload (12,008-byte core state after 87,600 returns and 43,800 claims).
