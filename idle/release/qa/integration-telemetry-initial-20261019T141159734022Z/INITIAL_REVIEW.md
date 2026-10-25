# Initial telemetry failure evidence

The pinned source reproduces QA015 in two of eight independent cases: an older consent read can revive local collection after a newer confirmed withdrawal, and can lower a newer confirmed revision. Six adversarial cases pass. The service rejects events using withdrawn/stale revisions; no backend acceptance is claimed.

The 26-test regression also passes: six GameTelemetry author cases, one actual app lifecycle case, thirteen native-manager cases and six repaired simulation/client probes. These independently confirm the QA014 availability repair and SIM001 final-return bookkeeping repair in this pin. Two real HTTP consent-read cases pass. Focused telemetry/QA analysis is clean.

The initial pin is `6e54c44cdadad3b0057e45e8a68f37c0407d3d4253c9b7872ff3bc00ef47f3a2`, with278 original inputs and three separately pinned test inputs. One first regression invocation failed before loading any tests because two simultaneous Flutter invocations shared a native-asset output path; its harness log is preserved, and the successful rerun was serial. The independent eight-case failure log was successful execution, not a harness error.

No release gate is accepted. Later signed-ownership/soundtrack/backend changes and moving localization are excluded. Repaired telemetry has a separate immutable source pin and review.
