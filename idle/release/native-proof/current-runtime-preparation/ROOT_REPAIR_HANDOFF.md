# Current runner repair handoff

Use current-reviewed-pins.json for the latest runner and build-gate sources. The original author-verification.json remains the historical author result and is not rewritten. The staged Dart harness is unchanged and still requires compilation/native execution.

Root repaired the two independently reproduced findings: native/framework errors anywhere in an interrupted run now reject, including errors buffered beyond the pre-kill snapshot; Android fixture capture checks every component below the app directory for symlink, existence, expected type, readability and directory traversal before bounded reading. Known OS base aliases are permitted. This does not claim protection against a hostile concurrent filesystem writer.

The original28 author tests and18 independent probes pass on repaired runner f63c8bb1f97e5e486fceb9b5831e416efae0d0f4bc73fe248079ca5e3a7cc834. See the independent RUNTIME_REVIEW.md linked in the pin file. Root also added an explicit current-runtime-verifier host gate before native exports;24 tooling tests pass, including an actual failing verifier subprocess that prevents native build invocation. Different-agent review of this gate addition is pending.

No native result, physical-device behavior, real crash association or package acceptance is implied. The18-scenario protocol, protected tablet exclusion and original observed-session/calendar obligations remain unchanged.
