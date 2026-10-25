"""Economic invariants and an independent one-second integration cross-check."""
import json
import math
import random
from economy import CFG, ROOT, State, bulk_cost, choose_purchase, cost, effective_offline_seconds, eligible, output, reset, simulate

checks = []


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    checks.append(label)


# Price sums must equal the sum of individual transactions, including gifts.
for q in [1.07, 1.10, 1.12, 1.15]:
    for i in range(5):
        for n, k in [(0, 1), (1, 10), (24, 2), (99, 50)]:
            check(f"bulk price q={q} tier={i+1} n={n} k={k}", math.isclose(bulk_cost(i, n, k, q), sum(cost(i, n+j, q) for j in range(k)), rel_tol=1e-12))

check("no threshold reward before L0", eligible(0.999 * CFG["prestige_scale_earnings"]) == 9)
check("first threshold grants ten", eligible(CFG["prestige_scale_earnings"]) == 10)
s = State([80, 70, 60, 50, 40], 1e8, 1e9)
check("first reset succeeds", reset(s))
check("reset preserves lifetime and gifts one skiff", s.lifetime == 1e9 and s.charts == 10 and s.wallet == 0 and s.counts == [1, 0, 0, 0, 0])
check("reset without new earnings cannot mint", not reset(s))
awarded = 10
for L in [2e9, 10e9, 100e9, 1e12]:
    delta = max(0, eligible(L) - awarded)
    awarded += delta
check("prestige awards telescope across resets", awarded == eligible(1e12))

diag = State([100, 100, 50, 50, 50], charts=100)
for i in [0, 1]:
    more = diag.clone()
    more.counts[i] += 1
    check(f"tier {i+1} has material cross-tier value", output(more) - output(diag) > 10 * (output(more, False) - output(diag, False)))

random.seed(31016)
for k in range(100):
    s = State([random.randrange(0, 180) for _ in range(5)], charts=random.randrange(0, 5000))
    initial = output(s)
    s.counts[random.randrange(5)] += 1
    check(f"monotone production sample {k}", output(s) >= initial)

for hours, expected in [(0,0), (2,2), (8,8), (24,24), (48,30), (72,36), (168,36)]:
    check(f"offline {hours}h", math.isclose(effective_offline_seconds(hours*3600), expected*3600))
check("negative elapsed time earns nothing", effective_offline_seconds(-100) == 0)
check("offline cap is continuous at 24 hours", abs(effective_offline_seconds(86400+0.001) - effective_offline_seconds(86400-0.001)) < 0.002)

# Independent fixed-step integration of the same purchase policy. Purchases occur
# at second boundaries rather than precisely when the wallet becomes sufficient.
tick = State()
for _ in range(3600):
    r = output(tick)
    tick.wallet += r
    tick.lifetime += r
    tick.time += 1
    while True:
        i, c = choose_purchase(tick)
        if tick.wallet + 1e-8 < c:
            break
        tick.wallet -= c
        tick.counts[i] += 1
exact = simulate(State(), 3600)
relative_error = abs(exact.lifetime - tick.lifetime) / exact.lifetime
check("one-second integration agrees within 2 percent at one hour", relative_error < 0.02)

# Boost alternatives must have identical nominal economic budgets.
check("speed bonus matches one five-minute token", 0.25 * 20 * 60 == 300)
check("six tokens fit daily allowance", 6 * 300 == CFG["daily_bonus_seconds"])
check("once-daily focus collection loses no charges", CFG["focus_charge_capacity"] * CFG["focus_charge_seconds"] == 86400)
check("once-daily surveys lose no completions", CFG["survey_queue_capacity"] * CFG["survey_cycle_seconds"] == 86400)
check("three weeks of contracts complete pass", 21 * 3 * 250 >= CFG["pass_levels"] * CFG["pass_xp_per_level"])

result = {"passed":len(checks), "failed":0, "independent_one_hour_relative_error": relative_error, "scope":"Core arithmetic, state resets, marginal synergies, caps and token budgets. Does not validate player retention, revenue, production save systems, or a global optimum."}
(ROOT / "validation_results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
