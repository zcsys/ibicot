# External acceptance dependencies

User confirmed on 16 October 2026 that no developer accounts, physical test devices, hosting or human playtesters are available. Local engineering and simulator verification continue. These evidence gates remain open; no account enrollment, purchase, credential access or publication is authorized by the local build work.

| Gate | Required external input | Local work that remains possible | Acceptance evidence still needed |
|---|---|---|---|
| Apple distribution and commerce | Authorized Apple developer team, approved bundle identity, signing access and configured sandbox products | Unsigned simulator app, StoreKit local configuration simulation, native adapter implementation | Signed install/update; authentic sandbox purchase, pending, restore, duplicate, cancellation and revocation cases |
| Google distribution and commerce | Authorized Play developer account, application identity, license testers and configured test products | Debug emulator app and native billing adapter implementation | Play-distributed test app; billing pending, acknowledgement, restore and interruption cases |
| Ad delivery | No paid account required for Google's sample ad IDs; production configuration later requires authorized publisher settings | Real test-ad callbacks, consent/refusal/no-fill handling and equal free reward ledger | Network/consent behavior verified on native targets; production identifiers and policy configuration before release |
| Cloud operations | Hosting destination, deployment authority, operational credentials and privacy/retention choices | Local server and protocol conflict/recovery tests | Hosted cross-device branch conflict, backup recovery, entitlement separation, deletion and incident drills |
| Minimum-OS and physical performance | Representative physical iOS 16 and Android 10+ devices, plus modern devices | iOS 26.3.1 simulator and Android API 35 emulator, headless and accessibility tests | Frame time, memory, battery, thermal, background/resume and platform accessibility evidence on the physical matrix |
| Human usability and balance | Authorized human testers and test protocol | Deterministic economic sweeps, replay traces and scripted UI tests | Observed onboarding/comprehension, return behavior, accessibility and retention cohort evidence |
| Public release | Owner approval, identity, privacy/store materials and credentials | Reviewable candidate artifacts and checksums | Submission, review, production monitoring and rollback rehearsal |

Seeded UI fixtures and accelerated deterministic replay must always be labeled. Neither substitutes for real elapsed onboarding, human playtesting, store transactions or physical-device performance.
