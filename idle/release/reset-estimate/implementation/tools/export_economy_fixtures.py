#!/usr/bin/env python3
"""Export bounded Python reference cases for future native-core conformance.

This is a development tool, not a production runtime. Expected amounts use the
existing model's binary64 arithmetic; a native implementation must separately
prove settlement and exact integer entitlement at its chosen precision.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import economy as reference  # noqa: E402

DESTINATION = ROOT / "implementation" / "fixtures" / "economy_reference.json"


def exact_integer_entitlement(lifetime: int) -> int:
    """Independent integer oracle for alpha=13/20 and whole-R inputs only."""
    if lifetime < 0:
        lifetime = 0
    lhs_factor = 1_000_000_000**13
    rhs = 10**20 * lifetime**13
    low, high = 0, 1
    while high**20 * lhs_factor <= rhs:
        high *= 2
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**20 * lhs_factor <= rhs:
            low = middle
        else:
            high = middle
    return low


def first_whole_radiance_for_charts(charts: int) -> int:
    """Find the smallest whole-R lifetime reaching a Chart entitlement."""
    rhs = charts**20 * 1_000_000_000**13
    low, high = 0, 1
    while 10**20 * high**13 < rhs:
        high *= 2
    while low + 1 < high:
        middle = (low + high) // 2
        if 10**20 * middle**13 >= rhs:
            high = middle
        else:
            low = middle
    return high


def state_case(case_id, counts, charts):
    state = reference.State(counts=counts, charts=charts)
    return {
        "id": case_id,
        "input": asdict(state),
        "expected": {
            "output_with_synergy": reference.output(state),
            "output_without_synergy": reference.output(state, synergy=False),
        },
    }


def build_fixture():
    cost_cases = []
    bulk_cases = []
    for tier in range(5):
        for count in (0, 1, 24, 25, 100):
            cost_cases.append({
                "id": f"cost_t{tier + 1}_n{count}",
                "input": {"tier_index": tier, "owned": count},
                "expected_cost_radiance": reference.cost(tier, count),
            })
        for count, quantity in ((0, 0), (0, 1), (1, 9), (24, 1), (24, 26), (100, 10)):
            bulk_cases.append({
                "id": f"bulk_t{tier + 1}_n{count}_k{quantity}",
                "input": {"tier_index": tier, "owned": count, "quantity": quantity},
                "expected_cost_radiance": reference.bulk_cost(tier, count, quantity),
            })

    milestone_cases = [{
        "id": f"milestone_n{count}",
        "input": {"owned": count},
        "expected_multiplier": reference.milestone(count),
    } for count in (0, 1, 24, 25, 26, 49, 50, 74, 75, 99, 100, 101, 125)]

    entitlement_cases = []
    lifetimes = {0, 1, 999_999_999, 1_000_000_000, 1_000_000_001,
                 10_000_000_000, 100_000_000_000, 1_000_000_000_000}
    for charts in (11, 25, 100):
        threshold = first_whole_radiance_for_charts(charts)
        lifetimes.update((threshold - 1, threshold, threshold + 1))
    for lifetime in sorted(lifetimes):
        entitlement_cases.append({
            "id": f"entitlement_L{lifetime}",
            "input": {"lifetime_radiance_integer_string": str(lifetime)},
            "expected_charts": exact_integer_entitlement(lifetime),
            "reference_float_charts": reference.eligible(lifetime),
            "first_reset_earnings_gate_passed": lifetime >= 1_000_000_000,
        })

    reset_cases = []
    reset_inputs = [
        ("reset_below_first_gate", reference.State([25, 10, 0, 0, 0], 300, 999_999_999, 0, 900)),
        ("reset_first_eligible", reference.State([60, 50, 25, 10, 1], 1234, 1_000_000_000, 0, 1000)),
        ("reset_already_awarded", reference.State([25, 10, 0, 0, 0], 300, 1_000_000_000, 10, 1200)),
        ("reset_incremental_award", reference.State([100, 75, 50, 25, 10], 5000, 10_000_000_000, 10, 1500)),
    ]
    for case_id, state in reset_inputs:
        before = asdict(state)
        accepted = reference.reset(state)
        after = asdict(state)
        second_accepted = reference.reset(state)
        reset_cases.append({
            "id": case_id,
            "input": before,
            "expected": {
                "accepted": accepted,
                "awarded_charts": after["charts"] - before["charts"],
                "state": after,
                "repeat_without_earnings_accepted": second_accepted,
                "state_after_repeat": asdict(state),
            },
        })

    synergy_cases = [
        state_case("output_initial", [1, 0, 0, 0, 0], 0),
        state_case("synergy_locked_24_charts", [100, 100, 50, 50, 50], 24),
        state_case("synergy_unlocked_25_charts", [100, 100, 50, 50, 50], 25),
        state_case("synergy_diagnostic_100_charts", [100, 100, 50, 50, 50], 100),
        state_case("synergy_no_target_owned", [100, 100, 50, 0, 0], 100),
    ]
    diagnostic = reference.State([100, 100, 50, 50, 50], charts=100)
    marginal_cases = []
    for tier in range(5):
        after = diagnostic.clone()
        after.counts[tier] += 1
        marginal_cases.append({
            "id": f"marginal_t{tier + 1}",
            "input": {"state": asdict(diagnostic), "buy_one_tier_index": tier},
            "expected": {
                "cost_radiance": reference.cost(tier, diagnostic.counts[tier]),
                "full_delta_radiance_per_second": reference.output(after) - reference.output(diagnostic),
                "direct_delta_radiance_per_second": reference.output(after, False) - reference.output(diagnostic, False),
            },
        })

    purchase_choices = []
    for case_id, counts in (("choice_initial", [1, 0, 0, 0, 0]),
                            ("choice_below_t2_unlock", [9, 0, 0, 0, 0]),
                            ("choice_at_t2_unlock", [10, 0, 0, 0, 0]),
                            ("choice_before_t1_milestone", [24, 10, 0, 0, 0])):
        state = reference.State(counts=counts)
        tier, price = reference.choose_purchase(state)
        purchase_choices.append({
            "id": case_id,
            "input": asdict(state),
            "expected": {"tier_index": tier, "price_radiance": price},
        })

    events = []
    first = reference.simulate(reference.State(), 86400, target_lifetime=1_000_000_000, events=events)
    first_tier_events = [{"tier": 1, "first_owned_seconds": 0.0}]
    for tier in range(2, 6):
        event = next(row for row in events if row["tier"] == tier)
        first_tier_events.append({"tier": tier, "first_owned_seconds": event["seconds"]})

    offline_cases = [{
        "id": f"offline_seconds_{seconds}",
        "input": {"absence_real_seconds": seconds},
        "expected_effective_production_seconds": reference.effective_offline_seconds(seconds),
    } for seconds in (-1, 0, 7200, 28800, 86400, 86401, 172800, 259200, 604800)]

    return {
        "schema_version": 1,
        "fixture_set": "tideglass-bounded-reference-v1",
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("economy.py", "economy.json")
        },
        "purpose": "Inputs and expected bounded reference behavior for implementing and reviewing a native deterministic economy core.",
        "limitations": [
            "This fixture exporter and the existing Python model are development references, not the production game runtime.",
            "Cost and production values are unrounded binary64 values. They do not choose production settlement precision, smallest units or arithmetic representation.",
            "Default continuous comparisons use relative 1e-9 and absolute 1e-6 in these bounded cases only; affordability, counts and Charts must match exactly and must not use this tolerance to grant purchases.",
            "Integer-entitlement cases use an independent exact integer oracle for whole-R inputs; production fractional-unit scaling and extreme range still need qualification.",
            "The first-run trace uses idealized instant, single-purchase marginal-ROI selection even before free autobuy unlock. It is not player telemetry or a runtime automation entitlement test.",
            "Offline cases verify only the credited-time envelope. Bonus expiry, Focus, Surveys, day rollover, contracts, reset policies and save replay need separate native timeline fixtures.",
            "Reset fixtures cover only fields present in the Python State. Notes, timers, discoveries, cosmetics and claim receipts must be retained in the fuller production state.",
        ],
        "comparison": {"continuous_relative_tolerance": 1e-9, "continuous_absolute_tolerance": 1e-6, "discrete": "exact"},
        "indexing": {"tier_index": "zero-based", "tier": "one-based display identifier"},
        "configuration": reference.CFG,
        "cases": {
            "cost": cost_cases,
            "bulk_cost": bulk_cases,
            "milestone": milestone_cases,
            "integer_entitlement": entitlement_cases,
            "reset": reset_cases,
            "synergy_output": synergy_cases,
            "marginal_purchase": marginal_cases,
            "purchase_choice": purchase_choices,
            "offline_envelope": offline_cases,
            "first_run": [{
                "id": "idealized_first_run_to_initial_prestige",
                "input": {"state": asdict(reference.State()), "max_duration_seconds": 86400, "stop_lifetime_radiance": 1_000_000_000},
                "expected": {
                    "state": asdict(first),
                    "output_radiance_per_second": reference.output(first),
                    "purchase_event_count": len(events),
                    "first_tier_events": first_tier_events,
                    "purchase_events": events,
                },
            }],
        },
    }


def verify_fixture(fixture):
    """Check useful independent identities; not a claim of native conformance."""
    checks = 0

    def check(condition, message):
        nonlocal checks
        if not condition:
            raise AssertionError(message)
        checks += 1

    def close(a, b):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)

    ids = [case["id"] for group in fixture["cases"].values() for case in group]
    check(len(ids) == len(set(ids)), "Fixture IDs must be unique")
    for case in fixture["cases"]["bulk_cost"]:
        args = case["input"]
        summed = math.fsum(reference.cost(args["tier_index"], count)
                           for count in range(args["owned"], args["owned"] + args["quantity"]))
        check(close(case["expected_cost_radiance"], summed), case["id"])
    for case in fixture["cases"]["milestone"]:
        count = case["input"]["owned"]
        expected = math.prod(2 for threshold in (25, 50, 75, 100) if count >= threshold)
        check(case["expected_multiplier"] == expected, case["id"])
    for case in fixture["cases"]["integer_entitlement"]:
        check(case["expected_charts"] == case["reference_float_charts"], case["id"])
    for case in fixture["cases"]["reset"]:
        before, expected = case["input"], case["expected"]
        check(expected["state"]["lifetime"] == before["lifetime"], case["id"] + " retains lifetime")
        check(expected["state"]["time"] == before["time"], case["id"] + " retains time")
        check(expected["repeat_without_earnings_accepted"] is False, case["id"] + " no repeat award")
        check(expected["state_after_repeat"] == expected["state"], case["id"] + " repeat unchanged")
    for case in fixture["cases"]["synergy_output"]:
        state = case["input"]
        n = state["counts"]
        sources = [math.log2(1 + n[i] / 25) for i in (0, 1)]
        s4 = 1 + .2 * sources[0] + .1 * sources[1] if state["charts"] >= 25 else 1
        s5 = 1 + .1 * sources[0] + .25 * sources[1] if state["charts"] >= 25 else 1
        tier_rates = [count * 20**i * 2**min(4, count // 25) for i, count in enumerate(n)]
        independent = (1 + math.sqrt(state["charts"] / 10)) * math.fsum(
            rate * multiplier for rate, multiplier in zip(tier_rates, [1, 1, 1, s4, s5]))
        check(close(independent, case["expected"]["output_with_synergy"]), case["id"])
    first = fixture["cases"]["first_run"][0]["expected"]
    state = first["state"]
    check(close(state["lifetime"], 1_000_000_000), "First run reaches initial reset gate")
    check(state["charts"] == 0, "Simulation does not silently reset")
    check(900 < state["time"] < 1200, "First-run baseline remains in its stated bounded range")
    check(first["purchase_event_count"] == sum(state["counts"]) - 1, "Gift excluded from purchase count")
    spent = math.fsum(reference.cost(i, previous)
                      for i, count in enumerate(state["counts"])
                      for previous in range(1 if i == 0 else 0, count))
    check(close(state["lifetime"] - spent, state["wallet"]), "Lifetime equals spent plus wallet; gift earns no lifetime")
    times = [event["seconds"] for event in first["purchase_events"]]
    check(times == sorted(times), "Purchase event times are ordered")
    check(fixture["cases"]["offline_envelope"][-1]["expected_effective_production_seconds"] == 129600,
          "Offline credit saturates at 36 hours")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify identities and fail if the committed fixture differs; do not write files.")
    args = parser.parse_args()
    fixture = build_fixture()
    checks = verify_fixture(fixture)
    serialized = json.dumps(fixture, indent=2, allow_nan=False) + "\n"
    if args.check:
        if not DESTINATION.exists() or DESTINATION.read_text() != serialized:
            print("Fixture differs or is missing; regenerate with this script without --check.", file=sys.stderr)
            return 1
        operation = "Verified"
    else:
        DESTINATION.parent.mkdir(parents=True, exist_ok=True)
        DESTINATION.write_text(serialized)
        operation = "Wrote"
    count = sum(len(group) for group in fixture["cases"].values())
    print(f"{operation} {DESTINATION.relative_to(ROOT)}: {count} cases; {checks} independent identity/invariant checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
