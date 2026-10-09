"""Scheduler cadence and batch helpers (JS worker §9.3 semantics)."""
from __future__ import annotations

# Scheduler modes mirror the canon machine contract (docs/design_canon.md §12):
#   fixed — one tick then 500 ms wall delay (~2 ticks/s)
#   max   — loop ticks within a 45 ms wall budget, then yield
#   step  — exactly one tick (only when not running)
FIXED_DELAY_S = 0.5
MAX_BUDGET_S = 0.045


def batch_run(runtime, ticks):
    """Advance ``ticks`` ticks synchronously (used by the headless CLI)."""
    for _ in range(ticks):
        runtime.step()
    return runtime.publish()
