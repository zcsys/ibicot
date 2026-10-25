# Client economic-transition integration

Author: `/root`. Independent reviewer: `/root/qa_integration` (review pending at this handoff).

Work: M1-04, M3-01, M3-10; scope S12/S14/S40. This is the actual native-client bootstrap/replay adapter for the compiled predecessor mechanism. The shipped v1 registers no predecessors and retains its existing economic constants, content quantities, event-order version and schema.

`game/mobile/lib/client_economic_transition.dart` binds an explicitly compiled old engine and digest to the repository's old payload/cursor validators and compatible-state adoption. Saved or remotely supplied data cannot instantiate rules. `bootstrap.dart` loads using the pinned rules, captures one target time, settles the old interval through the existing worker, commits the new pin atomically, then enters ordinary current-rule replay. Its return report includes the old interval once; preferences and story partitions remain in the client envelope. If wall time is earlier than the durable cursor, the transition switches at that cursor with no new credited interval. `offline_replay.dart` accepts a compiled engine parameter; the normal path still defaults to the unchanged v1 engine.

## Executed author integration checks

Actual Flutter execution and source copies: [root-transition-20261021T121321.388435Z](../native-proof/root-transition-20261021T121321.388435Z/verification.json).

- Whole-mobile analyzer: clean.
- Four new actual bootstrap widget cases: compiled synthetic predecessor at 1.5 R/s for 60 seconds produces 90 R; a default-rules reopen one second later produces 91 R; a repeated reopen remains 91 R. Saved preferences and return report are checked. Separate cases reject an unregistered version and a wrong digest with unchanged actual save-generation bytes. Clock rollback changes the pin without income, elapsed time, or cursor credit.
- Four selected bootstrap/replay files: 18 total passing cases, including the four above and existing disk, pending replay and background-worker integration regressions.
- Source differences during execution: none. The archived source includes the reviewed runtime's v2 inputs and exact root adapter/test code.

Synthetic old rules exist only in qualification code; this is no claim of compatibility with an invented released predecessor. Native iOS/Android FFI availability, actual process interruption and the final combined candidate remain separate checks. Core/persistence author and independent evidence are recorded beside this handoff. No work-item or release acceptance is promoted here.
