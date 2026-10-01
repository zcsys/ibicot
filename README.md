# Phase 0 Economy Engine — multi-file source project

This directory is the cleaned project layout for the Phase 0 simulator.

**Run**

Double-click the launcher for your operating system. Each starts the local
server and opens the simulator in your browser. Keep its terminal window open;
press Ctrl+C there to stop it.

| Operating system | Launcher |
| --- | --- |
| macOS | **Start Phase 0.command** |
| Windows | **Start Phase 0.bat** |
| Linux | **Start Phase 0.sh** |

On Linux, make the launcher executable once if your file manager does not
offer to run it: `chmod +x 'Start Phase 0.sh'`. Then double-click it and choose
“Run” when prompted.

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
