# Phase 0 Economy Engine — multi-file source project

This directory is the cleaned project layout for the Phase 0 simulator.

**Run**

On macOS, double-click **Start Phase 0.command**. It starts the local server
and opens the simulator in your browser. Keep the Terminal window open;
press Ctrl+C there to stop it.

From a terminal on any platform with Python 3:

```bash
python3 serve.py
```

Use the HTTP address printed by the launcher. Opening the HTML directly as a
`file:` URL cannot run browser workers.

**Edit**

Start with `engine/model.js` and `engine/reference_kernel.js` for the economic
model, then use `phase0_economy_engine_worker.js` for orchestration and
`phase0_economy_engine_app.js` for the UI.

The complete simulation is source-controlled. Its rules and invariants are
documented in [the economic contract](spec/economy_contract.md), and covered
by the tests in `tests/`.
