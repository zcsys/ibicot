# Current candidate host-gate checkpoint

Candidate `a052a44053472684ae5b60ce2b4fd1e9be0fe77f518dfd2a99a80add79094d4e` did **not** pass its host gate. The process is terminal with exit 1. No native exports or runtime cells were attempted. The exclusive Flutter/native lane was released to the lead for repair and a new declared candidate.

Command executed:

```sh
python3 tool/build_native.py ios android macos --candidate /Users/csys/Desktop/ibicot/idle/.tooling/build-candidates/20261023T032609.052120Z-a052a4405347 --host-checks
```

The complete unchanged logs and terminal report are in `release/native-proof/20261023T032749.977866Z/`. This execution folder’s `verification.json` hashes every preserved file and independently revalidates all 1,186 frozen source inputs after the run.

| Finding | Evidence | Required action |
|---|---|---|
| Optional-calibration regression retains the removed chapter-2 stop expectation | `mobile-test.log`: 639 passing methods, one failed assertion in `qa_integration_simulation_test.dart:123`; expected 2, actual 3 | Update the regression to prove the agreed Survey route and optional calibration effects without reinstating a Focus requirement; independently review |
| Operations host suite uses Python without its vault dependency | `operations-test.log`: 58 passing methods, one import error for `cryptography` in the actual vault/signer schema test | Run the dependent gate with the qualified pinned services environment; preserve the actual vault test |

All other host checks pass. The provider environment and provider suite pass under the pinned services environment. No failure was suppressed, no check was skipped, and the immutable candidate was not edited.

Read-only device discovery confirmed the dedicated iPhone `F05BE4B0-52C1-4CA1-B721-BD64AE559E3F` and iPad `089884DC-AD2A-4D69-8C60-C50271AC21BF` are available and shut down. The protected `F103390E-7B7C-4F0B-9404-5E029C7131FF` was not controlled. No Android emulator is active. The workspace-owned AVD is `.tooling/android-avd/Tideglass_API_35.avd`; its configured image is Android 35. The default global AVD list is unrelated and must not be used. Future execution must set the workspace AVD directory and record actual `getprop` version after boot rather than inherit an earlier summary’s API label.

The next candidate still requires all five exports, 22 baseline cells, 18 current-runtime cells on each of iPhone and Android, exact predecessor evidence, four opted-in observation windows, fresh raw media and current artifact/font/license inspection. None is established by this failed host attempt. The reviewed observer and optional hook are integrated, but no Tideglass native observation has been performed.
