# Tideglass persistence and economic transitions

The repository commits one progression branch atomically through alternating
checksummed snapshots. It never merges wallets or treats local data as paid
ownership. Load before saving. `settledThrough` and the corresponding payload
must be committed together.

## Compatible economic upgrades

The ordinary constructor still selects one version plus SHA-256 digest and
rejects every other configuration. The shipped client registers only the
unchanged `tideglass-economy-1.0.0` economy; its predecessor list is empty.
A reviewed application update may explicitly register compiled predecessors:

```dart
final store = SaveRepository(directory,
  economicVersion: destinationVersion,
  economicDigest: destinationDigest,
  validatePayload: validateDestinationPayload,
  validateSnapshot: validateDestinationCursor,
  compatiblePredecessors: [
    CompatibleEconomicPredecessor(
      configuration: EconomicConfiguration(
        version: oldVersion,
        digest: oldDigest,
        validatePayload: validateOldPayload,
        validateSnapshot: validateOldCursor,
      ),
      migratePayload: adoptSettledOldState,
    ),
  ],
);
final source = (await store.load()).snapshot!;
if (store.needsEconomicTransition(source)) {
  final saved = await store.transitionEconomy(
    source: source,
    boundary: capturedBoundary,
    authorizedThrough: authorizedEnd,
    settleOld: replayEveryPartitionUnderItsPinnedRules,
  );
  // Only saved.payload may now be exposed as committed destination progress.
}
```

Both source and destination cross-partition cursor validators are mandatory
when a compatibility edge is registered. No save, downloaded manifest or
arbitrary flag can register an engine or provide executable migration code.
The config digest identifies the reviewed config bytes; registering code that
implements those bytes remains the application's responsibility.

`settleOld` receives the immutable saved source and authorized boundary. It must
be a pure replay of `[source.settledThrough, boundary]`: no external rewards,
side effects, or other-store mutations. Other timeline partitions keep their
own pinned scenario rules. The old payload is validated at the boundary before
`migratePayload` runs; the migrated payload is validated under destination
rules before any committed file is touched. Reentrant callbacks cannot enter
an ancestor repository, including a symlink alias. This is a single-store
transaction, not a distributed transaction over multiple repositories.

The core's `adoptCompatibleState` preserves all balances, counts, timers,
residues, frozen objectives and scenario state; it changes only rules identity
and revision. It rejects an unfinished Support accumulator. Complete the old
accumulator under the old rules before calling it. A zero pending interval may
change rules without producing income. For clock rollback, the application's
authorized boundary can equal the already committed cursor; it must not invent
new elapsed time.

The transition commits payload, cursor, destination pin and one deterministic
local operation receipt together. The receipt binds the complete source
envelope hash, UUID/branch/revision, exact source/destination pins and boundary.
The existing `applied_operation_ids` field stores this single receipt. Ordinary
saves retain it. An ambiguous post-rename retry with the same captured source
returns the latest same-branch snapshot without replaying time; it does not
roll later progress back. A different source or boundary is a conflict. Explicit
imports fork progression and clear the receipt. Importing a predecessor is
rejected before replacing the current branch; use its pinned runtime and the
explicit transition path. Unknown generations fail closed instead of silently
falling back to an older compatible save.

## Writer exclusion

A canonical in-isolate FIFO queue is supplemented by native POSIX `flock` on a
stable `writer.lock` inode. The previous Dart `FileLock.exclusive` was
process-scoped on the macOS host and allowed separate isolates to overwrite a
held writer. Native `flock` excludes separately opened descriptors across
isolates/processes. Acquisition is nonblocking with asynchronous bounded retry;
process exit releases the kernel lock. Never unlink or replace the lock file.
Symlinks and nonregular files are rejected; `O_NOFOLLOW` prevents following a
link substituted at open. The directory remains application-owned, and these
advisory locks require cooperating writers.

Supported implementation targets are iOS/macOS process libc, Android
`libc.so`, and Linux glibc `libc.so.6`; other platforms reject explicitly.
`ffi` is pinned to 2.2.0. The two-argument `open` call uses a Dart-created file,
avoiding variadic `mode_t` ABI assumptions on Apple ARM64. Errno symbols are
`__error` (Apple), `__errno` (Android), and `__errno_location` (glibc).
`O_CLOEXEC` prevents subprocess inheritance. Constants were checked against the
installed Xcode SDK and Android NDK 28.2.13676358 headers. Native AOT/device
qualification is separate from host tests.

Production writes stay in the app's owning isolate; replay workers are pure.
Do not forcibly kill an isolate while it owns a native writer descriptor.
Process termination/restart is covered by the recovery contract; arbitrary
writer-isolate cancellation and device power-loss durability are not claimed.

Run `../../tool/dart analyze` and `../../tool/dart test` here. Focused core tests
also exercise this repository with actual high-precision economic state.
