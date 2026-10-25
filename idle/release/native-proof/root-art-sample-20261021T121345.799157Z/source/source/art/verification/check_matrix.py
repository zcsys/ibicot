#!/usr/bin/env python3
"""Validate bounded matrix evidence; never write canonical acceptance fields."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--proof", required=True, type=Path,
                        help="Platform lane evidence directory with source-before and verification JSON")
    parser.add_argument("--full", action="store_true",
                        help="Require every ID × condition and supplemental case in one successful full run")
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    proof = json.loads((args.proof / "verification.json").read_text())
    pins = json.loads((args.proof / "source-before.json").read_text())
    contract = json.loads((ROOT / "implementation/art/production_contract.json").read_text())
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)

    groups = {
        group: {a["asset_id"] for a in contract["assets"]
                if a["asset_id"].startswith(f"asset.{group}.")}
        for group in ("harbor", "producer", "cosmetic")
    }
    check({k: len(v) for k, v in groups.items()} ==
          {"harbor": 7, "producer": 25, "cosmetic": 36}, "Original contract identity counts changed")
    expected_conditions = {
        f"{viewport}-{scale}-{motion}": (size, scale / 100, motion == "reduced")
        for viewport, size in (("phone", [320, 720]), ("tablet", [1024, 768]))
        for scale in (100, 150, 200) for motion in ("normal", "reduced")
    }
    rows = report["rows"]
    identities = [(r["asset_id"], r["condition_id"]) for r in rows]
    check(len(set(identities)) == len(identities), "Duplicate asset/condition rows")
    check(report["observed_passing_matrix_rows"] == len(rows), "Declared row total differs from rows")
    check(report["expected_matrix_rows"] == 816, "Unexpected required matrix size")
    check(report["complete_matrix_observed"] == (len(set(identities)) == 816), "False matrix completeness claim")
    check(report["canonical_verification_written"] is False, "Canonical acceptance must not be promoted")
    check(report["external_store_or_rights_evidence"] is False, "Synthetic fixture cannot assert rights/store evidence")
    check(report["synthetic_paid_ownership"] is True, "Paid fixtures must be explicitly synthetic")
    for row in rows:
        tag = f"{row['asset_id']}/{row['condition_id']}"
        check(row["asset_id"] in groups.get(row["group"], set()), f"Unknown contract ID: {tag}")
        expected = expected_conditions.get(row["condition_id"])
        check(expected is not None, f"Unknown condition: {tag}")
        if expected:
            check((row["viewport"], row["text_scale"], row["reduced_motion"]) == expected,
                  f"Condition settings mismatch: {tag}")
        check(row["result"] == "passed_bounded_host_case", f"Unexpected row result: {tag}")
        check(row["layout_exception"] is False, f"Layout exception: {tag}")
        if row["group"] == "cosmetic":
            check(row["states"] == ["locked", "owned", "equipped"], f"Missing state transition: {tag}")
            check(row["same_id_across_consumers"] is True, f"Appearance identity mismatch: {tag}")
            check(row["thumbnail_is_component_fixture"] is True, f"Thumbnail route misrepresented: {tag}")
            check(row["economic_state_unchanged_by_presentation_and_equip"] is True,
                  f"Economic mutation: {tag}")
            check(row["actual_harbor_producer_and_purchase_bounds_unchanged"] is True,
                  f"Cosmetic changes actual app bounds: {tag}")
        else:
            check(row["economic_state_unchanged"] is True, f"Economic mutation: {tag}")

    check(proof["source_differences"] == [], "Sources drifted during platform run")
    if "art_report_sha256" in proof:
        check(proof["art_report_sha256"] == sha(args.report), "Report differs from platform-recorded output hash")
    elif args.full:
        check(False, "Full-run report lacks a platform-recorded output hash")
    for result in proof["results"]:
        log = args.proof / f"{result['name']}.log"
        check(log.exists(), f"Missing {result['name']} log")
        if log.exists():
            check(sha(log) == result["log_sha256"], f"Changed {result['name']} log")
        check(result["exit_code"] == 0, f"Platform command {result['name']} did not pass")
    test_results = [r for r in proof["results"] if "test" in r.get("command", [])]
    check(bool(test_results), "No actual Flutter test execution recorded")
    for result in test_results:
        command = result["command"]
        check("test/art_catalogue_variants_test.dart" in command, "Proof is for another test")
        check(f"--dart-define=TIDEGLASS_ART_REPORT_DIR={args.report.resolve().parent}" in command,
              "Proof command does not bind this report directory")
        if args.full:
            check("--plain-name" not in command and "--name" not in command,
                  "Filtered test command cannot establish full-run success")
    test_path = "game/mobile/test/art_catalogue_variants_test.dart"
    check(test_path in pins, "Missing exact test source pin")
    # Frozen copies, not the moving workspace, establish the actual tested input.
    for path, digest in pins.items():
        frozen = args.proof / "source" / path
        check(frozen.is_file(), f"Missing frozen input: {path}")
        if frozen.is_file():
            check(sha(frozen) == digest, f"Frozen input differs: {path}")

    if args.full:
        expected = {(asset, condition) for ids in groups.values() for asset in ids
                    for condition in expected_conditions}
        check(set(identities) == expected, f"Missing or extra matrix pairs: {len(expected-set(identities))} missing")
        supplements = report["supplemental_cases"]
        counts = Counter(s["case"] for s in supplements)
        check(counts == {"declared_text_palette": 1, "actual_app_animation_lifecycle": 1,
                         "actual_initial_producer_locks": 12, "selected_locked_component_matrix": 12},
              f"Incomplete supplemental cases: {dict(counts)}")
        for name in ("actual_initial_producer_locks", "selected_locked_component_matrix"):
            check({s["condition_id"] for s in supplements if s["case"] == name} == set(expected_conditions),
                  f"Missing conditions for {name}")

    output = {"result": "failed" if failures else "passed_bounded_evidence_integrity",
              "full_mode": args.full, "observed_rows": len(rows),
              "rows_by_group": dict(Counter(r["group"] for r in rows)),
              "frozen_inputs_checked": len(pins), "failures": failures,
              "report_sha256": sha(args.report), "canonical_acceptance": False}
    print(json.dumps(output, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
