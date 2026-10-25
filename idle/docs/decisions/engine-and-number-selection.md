# Engine and number selection

Decision date: 16 October 2026. Owner: director. M0-02 accepted by the director after independent QA cross-review (release/qa/integration-initial-20261016T104939468348Z/M0-02_REVIEW.md); M0-03's real service-account qualification remains open. A native client choice is not proof of successful purchases, ads or cloud services.

## Chosen implementation

Use Flutter for the native iOS/Android client and pure Dart packages for the economy, progression, persistence and event rules. The game is a responsive two-dimensional management interface with scalable text, semantic controls and small vector scenes. A separate renderer/physics engine would add little to this v1. macOS is an internal test target, not a substitute public platform. Exact Flutter/Dart/Android/iOS toolchain versions and executable artifacts are recorded by the platform build manifest; the choice is based on these actual exports, not documentation alone.

The immutable `ce46598c4b513477c643f0dff4f5160400ac800b4ee76579c48ca2a5e08e1ffd` candidate ran the same deterministic native purchase/Rechart fixture on iOS and Android: 60 R with one gifted Skiff, buy the second at 33.6 R, retain 26.4 R, cancel reset unchanged, then the seeded eligibility case awards 10 Charts and rebuilds to one Skiff without changing lifetime. Native disk reload assertions and later separate-process natural first-purchase tests are preserved in `release/native-proof/qualification.json` and the per-run evidence. That candidate has a stale schema-negative host-test failure; its build/runtime evidence cannot be described as a clean full candidate. The next candidate must rerun all relevant gates.

## Representations compared

| Candidate | Benefit | Observed or structural limitation | Decision |
|---|---|---|---|
| Native 64-bit integer micro-R | Fast exact small values | The probe's maximum signed integer plus one wraps negative; a late-game wallet can exceed this finite range | Use ordinary integers only for bounded native indices, not economic ledgers |
| Binary64 floating point | Convenient rates and large exponent range | `2^53` and `2^53+1` become equal; the actual tier-five/count-500 price and one micro-R below it become equal; `10^3000` becomes infinity | Display/interpolation only; never settle purchases or Charts |
| Floating logarithmic/mantissa-exponent balance | Extends exponent range and suits approximate idle displays | The probe's adjacent values near `10^30` map to the same logarithm; more range does not retain a one-micro-R difference without a separate exact remainder ledger | Rejected as sole settlement authority |
| BigInt micro-R plus BigInt fixed-point rates | Exact integer wallet/price/Chart decisions, deterministic save strings and carried residue | Work and memory grow with digit count; irrational rate multipliers remain approximations at explicit precision | Selected; benchmark resource limits and preserve a replay event budget |

Dart's primary references describe [binary64 doubles](https://api.dart.dev/dart-core/double-class.html), [native integer overflow](https://api.dart.dev/dart-core/int-class.html), and [arbitrary-precision BigInt](https://api.dart.dev/dart-core/BigInt-class.html). The local probe `game/qa/number_approach_probe.dart` produces `release/number-approach-probe.json`, including the actual boundary purchase and 3,001-digit neighbor distinction. It is a representation experiment, not a broad library performance ranking.

Production prices telescope across bulk/split purchases using exact rational cumulative rounding. Chart entitlement uses an integer-root inequality. Rates use 24-decimal fixed point with documented approximation bounds; no floating epsilon can authorize an unaffordable purchase. Full formulas and event ordering are in `numbers-and-event-order.md`. Independent QA already compared 474 arithmetic cases and the complete bounded blueprint fixture families; its reports state the tested versions and limits.

The host probe measures 100 repeated bulk-price calculations at each of counts 100, 500 and 1,000 and records raw microsecond timings. JIT warm-up and shared-host load are not controlled, so the rows are diagnostic observations, not mobile latency guarantees. Physical release/profile startup, frame, thermal and replay measurements remain required by the quality protocol. Counts still use native integer indices and must fail safely at native resource limits; this is not a promise of infinite computation or save size.
