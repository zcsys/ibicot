"""Tideglass deterministic reference economy, not a production game server.

Run: python3 economy.py
The policy buys the unlocked single producer with greatest marginal output/cost,
saving until affordable. It is reproducible, not claimed globally optimal.
Python float is adequate for these bounded experiments; production needs a
large-number representation and an integer currency settlement ledger.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "economy.json").read_text())


@dataclass
class State:
    counts: list[int] = field(default_factory=lambda: [1, 0, 0, 0, 0])
    wallet: float = 0.0
    lifetime: float = 0.0
    charts: int = 0
    time: float = 0.0

    def clone(self):
        return State(self.counts.copy(), self.wallet, self.lifetime, self.charts, self.time)


def cost(i, n, q=None):
    q = CFG["purchase_growth"] if q is None else q
    return CFG["base_cost"] * CFG["tier_ratio"] ** i * q ** n


def bulk_cost(i, n, k, q=None):
    q = CFG["purchase_growth"] if q is None else q
    return cost(i, n, q) * math.expm1(k * math.log(q)) / (q - 1)


def milestone(n):
    return CFG["milestone_multiplier"] ** min(CFG["milestone_cap"], n // CFG["milestone_interval"])


def output(s, synergy=True):
    multipliers = [1.0] * 5
    if synergy and s.charts >= CFG["synergy_unlock_charts"]:
        for i, row in enumerate(CFG["synergy_matrix"]):
            x = math.log2(1 + s.counts[i] / CFG["synergy_count_scale"])
            for j, a in enumerate(row):
                multipliers[j] += a * x
    permanent = 1 + (s.charts / CFG["prestige_power_scale"]) ** CFG["prestige_power_exponent"]
    return permanent * sum(n * CFG["base_output"] * CFG["tier_ratio"] ** i * milestone(n) * multipliers[i]
                           for i, n in enumerate(s.counts))


def eligible(lifetime):
    # Decimal alpha=13/20 admits exact integer-boundary verification in production:
    # p**20 * L0**13 <= 10**20 * L**13 (after common unit scaling).
    return math.floor(CFG["prestige_scale_award"] * (max(0, lifetime) / CFG["prestige_scale_earnings"]) ** CFG["prestige_exponent"] + 1e-10)


def reset(s):
    target = eligible(s.lifetime)
    if s.lifetime < CFG["prestige_scale_earnings"] or target <= s.charts:
        return False
    s.charts = target
    s.counts = [1, 0, 0, 0, 0]
    s.wallet = 0.0
    return True


def choose_purchase(s, q=None, synergy=True):
    r = output(s, synergy)
    candidates = []
    for i in range(5):
        if i and s.counts[i - 1] < CFG["unlock_previous_count"]:
            continue
        c = cost(i, s.counts[i], q)
        after = s.clone()
        after.counts[i] += 1
        candidates.append(((output(after, synergy) - r) / c, i, c))
    _, i, c = max(candidates)
    return i, c


def simulate(s, duration, q=None, synergy=True, target_lifetime=math.inf, events=None):
    end = s.time + duration
    while s.time < end - 1e-9 and s.lifetime < target_lifetime - 1e-6:
        r = output(s, synergy)
        i, c = choose_purchase(s, q, synergy)
        wait = max(0.0, (c - s.wallet) / r)
        dt = min(wait, end - s.time, max(0.0, (target_lifetime - s.lifetime) / r))
        s.wallet += r * dt
        s.lifetime += r * dt
        s.time += dt
        if dt + 1e-8 < wait:
            break
        s.wallet = max(0.0, s.wallet - c)
        s.counts[i] += 1
        if events is not None:
            events.append({"seconds": s.time, "tier": i + 1, "owned": s.counts[i], "lifetime": s.lifetime, "output": output(s, synergy)})
    return s


def effective_offline_seconds(seconds):
    t = max(0, seconds)
    return min(t, CFG["full_offline_seconds"]) + CFG["catchup_tail_rate"] * min(max(t - CFG["full_offline_seconds"], 0), CFG["catchup_tail_seconds"])


def save_csv(name, rows):
    with (ROOT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def report():
    event_rows = []
    first = simulate(State(), 86400, target_lifetime=CFG["prestige_scale_earnings"], events=event_rows)
    tiers = []
    for i, name in enumerate(CFG["producer_names"]):
        t = 0.0 if i == 0 else next(e["seconds"] for e in event_rows if e["tier"] == i + 1)
        tiers.append({"tier": i+1, "name": name, "first_owned_seconds": t})
    sensitivity = []
    for q in [1.07, 1.10, 1.12, 1.15]:
        s = simulate(State(), 86400, q=q, target_lifetime=CFG["prestige_scale_earnings"])
        sensitivity.append({"purchase_growth": q, "first_prestige_seconds": s.time, "output_at_target": output(s)})

    # Decision experiment: start from the first eligible reset, then enumerate
    # ONE reset at integer minute offsets through a fixed 8-hour future horizon.
    # All future purchases follow the policy above. This is not full control search.
    horizon = 8 * 3600
    candidates = []
    base = first.clone()
    stay = simulate(base.clone(), horizon)
    for minutes in range(481):
        s = simulate(base.clone(), minutes * 60)
        reset(s)
        simulate(s, horizon - minutes * 60)
        candidates.append({"reset_after_minutes": minutes, "terminal_lifetime": s.lifetime, "terminal_chart_potential": eligible(s.lifetime), "banked_charts": s.charts})
    best = max(candidates, key=lambda x: x["terminal_lifetime"])
    save_csv("reset_sweep.csv", candidates)
    save_csv("growth_sensitivity.csv", sensitivity)
    save_csv("first_run_purchases.csv", event_rows)

    repeated = State()
    repeated_rows = []
    for cycle in range(12):
        target_charts = 10 if repeated.charts == 0 else 2 * repeated.charts
        target = CFG["prestige_scale_earnings"] * (target_charts / CFG["prestige_scale_award"]) ** (1 / CFG["prestige_exponent"])
        start = repeated.time
        simulate(repeated, 86400, target_lifetime=target)
        reset(repeated)
        repeated_rows.append({"reset": cycle+1, "elapsed_seconds": repeated.time, "cycle_seconds": repeated.time-start, "banked_charts": repeated.charts})
    save_csv("repeated_prestiges.csv", repeated_rows)

    # Counts are a diagnostic state, not a claimed typical player distribution.
    diag = State([100, 100, 50, 50, 50], charts=100)
    synergy_rows = []
    for i in [0, 1, 3, 4]:
        after = diag.clone()
        after.counts[i] += 1
        d = output(after) - output(diag)
        direct = output(after, False) - output(diag, False)
        synergy_rows.append({"tier": i+1, "cost": cost(i, diag.counts[i]), "total_marginal_output": d, "direct_marginal_output": direct, "payback_seconds": cost(i, diag.counts[i]) / d})
    save_csv("synergy_diagnostics.csv", synergy_rows)
    summary = {
        "assumptions": "No boosts, quests, paid effects or manual taps. Idealized instant single-purchase marginal-ROI policy. One free Tier 1 counted in ownership. Lifetime excludes the gift. No automatic prestiges.",
        "first_run": {"seconds_to_1e9": first.time, "counts": first.counts, "output": output(first), "tiers": tiers},
        "sensitivity": sensitivity,
        "reset_experiment": {"horizon_seconds": horizon, "allowed_future_resets": 1, "grid_minutes": 1, "no_reset_terminal_lifetime": stay.lifetime, "reset_now": candidates[0], "best": best, "best_vs_no_reset_ratio": best["terminal_lifetime"] / stay.lifetime},
        "synergy": synergy_rows,
        "repeated_prestiges": repeated_rows,
        "offline": [{"absent_hours": h, "credited_hours": effective_offline_seconds(h * 3600) / 3600} for h in [2, 8, 24, 48, 72, 168]]
    }
    (ROOT / "simulation_results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    report()
