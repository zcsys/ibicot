#!/usr/bin/env python3
"""Build an author-only per-ID index after both actual full matrix checks pass."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "release/art/catalogue-variants"
RUNS = {
    "en-US": "root-art-full-20261021T122040.006324Z",
    "qps-ploc": "root-art-pseudo-full-20261021T122636.246158Z",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def main():
    runs = {}
    for locale, name in RUNS.items():
        proof = ROOT / "release/native-proof" / name
        report = OUT / name / "matrix-results.json"
        check = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("check_matrix.py")),
             str(report), "--proof", str(proof), "--full"],
            check=True, capture_output=True, text=True,
        )
        checked = json.loads(check.stdout)
        assert checked["presentation_locale"] == locale
        (OUT / f"{locale}-author-check.json").write_text(check.stdout)
        data = json.loads(report.read_text())
        runs[locale] = {
            "proof_directory": relative(proof),
            "proof_sha256": sha(proof / "verification.json"),
            "source_index_sha256": sha(proof / "source-before.json"),
            "report_path": relative(report), "report_sha256": sha(report),
            "source_pins": json.loads((proof / "source-before.json").read_text()),
            "data": data, "check": checked,
        }
    contract_path = ROOT / "implementation/art/production_contract.json"
    contract = json.loads(contract_path.read_text())
    assets = [a for a in contract["assets"]
              if any(a["asset_id"].startswith(f"asset.{g}.") for g in ("harbor", "producer", "cosmetic"))]
    assert len(assets) == 68
    grouped = {}
    for locale, run in runs.items():
        grouped[locale] = defaultdict(list)
        for row in run["data"]["rows"]:
            grouped[locale][row["asset_id"]].append(row)
    index = []
    for asset in assets:
        aid = asset["asset_id"]
        evidence = {}
        for locale, run in runs.items():
            rows = grouped[locale][aid]
            assert len(rows) == 12 and len({r["condition_id"] for r in rows}) == 12
            evidence[locale] = {
                "report_path": run["report_path"], "report_sha256": run["report_sha256"],
                "condition_ids": sorted(r["condition_id"] for r in rows),
                "passed_bounded_host_rows": len(rows),
            }
        index.append({
            "asset_id": aid, "original_required_variants": asset["required_variants"],
            "original_source_descriptor": asset["source_descriptor_path"],
            "original_export_descriptor": asset["export_descriptor_path"],
            "evidence_by_presentation_locale": evidence,
            "review_boundary": "Host behavioral evidence only; original asset approval remains open",
        })
    en = runs["en-US"]["source_pins"]
    ps = runs["qps-ploc"]["source_pins"]
    differences = [{"path": p, "en-US_sha256": en.get(p), "qps-ploc_sha256": ps.get(p)}
                   for p in sorted(en.keys() | ps.keys()) if en.get(p) != ps.get(p)]
    result = {
        "schema_version": 1, "author": "/root/art_content_engineer",
        "status": "author_evidence_ready_for_independent_review",
        "original_contract_sha256": sha(contract_path),
        "asset_count": 68, "passed_host_rows": 1632,
        "runs": {locale: {k: v for k, v in r.items() if k not in ("source_pins", "data")}
                 for locale, r in runs.items()},
        "between_run_source_differences": differences, "assets": index,
        "selected_and_high_stage_locked_are_component_fixtures": True,
        "thumbnail_160px_is_component_fixture": True,
        "paid_ownership_is_synthetic": True,
        "canonical_verification_written": False,
        "original_variant_acceptance_promoted": False,
        "native_physical_rights_or_provider_approval": False,
    }
    target = OUT / "per-id-evidence.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"index": relative(target), "sha256": sha(target),
                      "assets": len(index), "rows": 1632,
                      "between_run_changed_paths": [d["path"] for d in differences]}, indent=2))


if __name__ == "__main__":
    main()
