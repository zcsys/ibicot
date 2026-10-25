# Native replay and appearance integration

Implemented locally on 16 October 2026. These changes remain subject to a fresh
independent native review; a host test does not establish physical performance.

`offline_replay.dart` settles a return on a separate Dart isolate. Main,
challenge and seasonal fleets share the same elapsed interval and retain the
original absence offset across chunks. The 24-hour full-rate and subsequent
48-hour quarter-rate envelope is never restarted at a chunk boundary. Progress
messages update the loading screen; production commands are blocked during a
resume. Backgrounding again does not restart online production after the worker
finishes.

The original durable snapshot remains unchanged while the worker runs. Only a
complete combined result enters the normal atomic save transaction. Process
interruption therefore replays owed work from the last committed snapshot;
there is no best-effort partial award or discarded remainder. Previously
persisted typed continuations retain their exact request and offset. The worker
also has a legacy continuation route; additional native migration evidence is
still required. Resource-budget failures preserve the original state and show
a retry/error flow; the UI must never claim the failed interval was settled.

Repository snapshot validation compares main calendar, seasonal cursor and
receipt boundaries before import or commit. Payload validation separately checks
the pass account/XP and pinned dossier rules. Incompatible content requires a
compatible executable instead of silently selecting an earlier generation.
New recovery references are relative to the save directory, avoiding inclusion
of a host username in a newly exported recovery branch. The migration test
resolves that reference against the repository and checks the file still exists.

Story schema 4 adds `equipped_appearance` as a preference. Earned chapter and
claimed free-pass cosmetics are projected from actual progression. The six
Note-funded decorations retain their separate selection and can coexist with
an appearance. Importing a paid appearance ID never establishes ownership: it
is hidden unless an independent entitlement path authorizes it. The current
integration exposes earned ownership; native paid integration is in progress.
All 36 designs have distinct authored geometry and matched previews, with no
production multiplier or new economic field.

Author integration checks: six worker/lifecycle tests, four appearance-session
tests, three bundle-pinning tests and the existing combined suite passed (134
mobile tests at this checkpoint). The native candidate built from that state
is recorded separately. The earlier independent `bc5e726d…` review covers its
own pinned state, not these later integration changes. No physical-device,
store, listening, human-study or elapsed-season requirement is waived.
