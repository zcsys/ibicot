# Device-local ownership clock

`OwnershipClockBridge` lives in `game/mobile/lib/ownership_clock.dart`. Construct one bridge per Flutter engine. It implements `ChangeNotifier`; `current` returns `TrustedDeviceTime?`, `restartContinuity` describes the current evidence, `refresh()` asynchronously requests a fresh native sample, `invalidate()` cancels pending samples and clears the projection, and `dispose()` releases observers/timers. The default refresh interval is 10 seconds; samples expire after 30 seconds. The request deadline is 3 seconds. `autoRefresh: false` is for controlled host tests or a caller that schedules refreshes itself.

## Integrating the lease cache

- Pass `deviceTime: () => ownershipClock.current` to `SecureOwnershipLeaseCache`, plus device-only secure read/write/delete callbacks.
- Await a successful `ownershipClock.refresh()` before `accept`, `load`, and resume. A failed sample cannot authorize a new anchored lease. The cache also rejects `accept` when its configured native callback returns null.
- Call `checkpoint(accountId: ...)` on background. Lifecycle/native sleep observers may invalidate the bridge first; a temporary null sample preserves the old persisted anchor and budget, updates the wall-time high-water mark, and temporarily hides grants. The next fresh sample still subtracts actual sleep time from the old anchor.
- Observe bridge notifications to refresh ownership UI. Between samples, a short projection uses a monotonic stopwatch. A wall/stopwatch divergence over 250 ms, stale sample, native invalidation, or lifecycle suspension hides the projection until refresh. No wall-clock extrapolation replaces missing native evidence.
- Capture a native sample as a lower bound and the entire request/response duration as uncertainty. Cache elapsed calculations charge the upper bound, so channel delay cannot extend a lease. Accept/load capture clocks before queueing or awaiting secure storage; results recheck expiry after persistence. A delayed response can shorten availability, never increase it.
- `clear(accountId: ...)` removes ownership but retains its anti-replay record. `erase(accountId: ...)` deletes the device-local record after confirmed remote account deletion; absent/failing secure deletion reports an error. Cleanup for account A never drops an active account B grant.

## Native evidence and limitations

Android uses `SystemClock.elapsedRealtimeNanos()`, which includes sleep, and `Settings.Global.BOOT_COUNT`. An app-private, nonexportable AndroidKeyStore HMAC-SHA256 key derives an opaque epoch from that count. A replaced/invalidated key, reboot, or different device changes the epoch or makes sampling unavailable. No boot count, key, identifier, or derived sample goes to the service or telemetry. The manifest disables Android backup, and secure credentials/lease storage must remain device-only. This design depends on Android's OS integrity and KeyStore; it is not resistance to a compromised OS.

Apple uses `mach_continuous_time()` with checked integer timebase conversion. Each native process generates a new random epoch. **iOS and macOS leases cannot be resumed after process exit without fresh online verification.** No undocumented boot identity or inferred uptime-to-wall identity is used. iOS 18's documented removal of app access to `kern.bootsessionuuid` prevents claiming that identity as a portable app API. Native lifecycle/sleep notifications invalidate projections. Keychain values must use a `ThisDeviceOnly` accessibility class; process epochs additionally prevent restored cache continuity.

Both Apple targets include `PrivacyInfo.xcprivacy` with system boot time reason `35F9.1`: measuring intervals/timers inside the app. Clock evidence and derived epoch data remain on-device. These manifests add this implementation's required-reason declaration; they do not attest that every SDK's complete release privacy declarations or store questionnaires have been reviewed.

## Verification and external gates

Eight Flutter host tests exercise the actual MethodChannel contract, request uncertainty, process-only Apple behavior, stale/suspend evidence, lifecycle/pending cancellation, reordered responses/key changes, native invalidation, malformed/failed/late evidence, and disposal. These are host tests, not a physical-device security qualification. Thirteen cache author tests and six independent QA cases cover crypto, expiry, sleep/reboot, storage faults, asynchronous expiry, deletion, and account cleanup isolation. iOS and macOS entrypoints were type-checked against the installed native SDK/Flutter headers with generated-registration placeholders; full target builds and native device sleep/reboot/key invalidation tests remain separate release gates. No live store success or production signing key is represented by fixture tests.

Primary references reviewed 2026-10-19:

- [Android elapsed realtime including sleep](https://developer.android.com/reference/android/os/SystemClock#elapsedRealtimeNanos())
- [Android boot count](https://developer.android.com/reference/android/provider/Settings.Global#BOOT_COUNT)
- [AndroidKeyStore HMAC key generation](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec)
- [Android key isolation](https://developer.android.com/privacy-and-security/keystore)
- [Apple continuous time](https://developer.apple.com/documentation/kernel/1646199-mach_continuous_time)
- [iOS 18 API availability changes](https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-18-release-notes?changes=_2)
- [Apple required reason values, including 35F9.1](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitypereasons)
