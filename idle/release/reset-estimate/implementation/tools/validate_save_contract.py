#!/usr/bin/env python3
"""Validate the Tideglass envelope and its domain invariants using stdlib only.

This deliberately implements only the schema keywords used by the checked-in
contract. It is not a general JSON Schema implementation, persistence engine,
receipt verifier, migration implementation, gameplay validator or clock oracle.
Run without arguments for positive/negative fixtures; pass --save PATH for an
individual save. --config PATH additionally checks the pinned config digest.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts/save-envelope.schema.json"
FIXTURE_PATH = ROOT / "fixtures/save_contract_cases.json"


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def reject_constant(value):
        raise ValueError(f"non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=reject_duplicate_keys,
                      parse_constant=reject_constant)


def type_matches(value, name):
    return {"object": lambda: isinstance(value, dict),
            "array": lambda: isinstance(value, list),
            "string": lambda: isinstance(value, str),
            "integer": lambda: type(value) is int,
            "null": lambda: value is None}[name]()


def check_schema(value, spec, root, path="$", errors=None):
    errors = [] if errors is None else errors
    if "$ref" in spec:
        target = root
        for part in spec["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return check_schema(value, target, root, path, errors)
    types = spec.get("type")
    if types and not any(type_matches(value, t) for t in ([types] if isinstance(types, str) else types)):
        errors.append(f"{path}: wrong type; expected {types}")
        return errors
    if "const" in spec and (type(value) is not type(spec["const"]) or value != spec["const"]):
        errors.append(f"{path}: expected constant {spec['const']!r}")
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{path}: value is outside enum")
    if isinstance(value, dict):
        for key in spec.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required field missing")
        properties = spec.get("properties", {})
        for key, child in value.items():
            if key in properties:
                check_schema(child, properties[key], root, f"{path}.{key}", errors)
            elif spec.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: unexpected field")
    if isinstance(value, list):
        for index, child in enumerate(value):
            if "items" in spec:
                check_schema(child, spec["items"], root, f"{path}[{index}]", errors)
    if type(value) is int and "minimum" in spec and value < spec["minimum"]:
        errors.append(f"{path}: below minimum {spec['minimum']}")
    if isinstance(value, str):
        if len(value) < spec.get("minLength", 0):
            errors.append(f"{path}: too short")
        if "pattern" in spec and re.search(spec["pattern"], value) is None:
            errors.append(f"{path}: does not match required pattern")
        try:
            if spec.get("format") == "uuid":
                uuid.UUID(value)
            elif spec.get("format") == "date-time":
                datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{path}: invalid {spec['format']}")
    return errors


def validate(envelope, schema=None, config_path=None):
    schema = schema or read_json(SCHEMA_PATH)
    errors = check_schema(envelope, schema, schema)
    if errors:
        return errors  # Domain comparisons require well-typed data.
    parent = envelope["parent"]
    revision = envelope["revision"]
    if parent is None:
        if revision != 0:
            errors.append("$.revision: a root snapshot must have revision 0")
    else:
        if revision != parent["revision"] + 1:
            errors.append("$.revision: child must increment parent revision by exactly one")
        if parent["save_id"] == envelope["save_id"]:
            errors.append("$.parent.save_id: snapshot cannot be its own parent")
        if parent["branch_id"] != envelope["branch_id"] and not any(
            all(reference[k] == parent[k] for k in ("save_id", "branch_id", "revision"))
            for reference in envelope["preserved_branches"]
        ):
            errors.append("$.preserved_branches: fork requires a parent-branch recovery reference")
    for key in ("save_id", "recovery_reference"):
        values = [r[key] for r in envelope["preserved_branches"]]
        if len(set(values)) != len(values):
            errors.append(f"$.preserved_branches: duplicate {key}")
    for reference in envelope["preserved_branches"]:
        if reference["save_id"] == envelope["save_id"]:
            errors.append("$.preserved_branches: current snapshot is not a divergent recovery snapshot")
        if reference["branch_id"] == envelope["branch_id"]:
            errors.append("$.preserved_branches: divergent reference must use another branch")
    applied = envelope["applied_operation_ids"]
    if len(set(applied)) != len(applied):
        errors.append("$.applied_operation_ids: duplicate operation ID")
    pending = envelope["pending_operations"]
    for key in ("operation_id", "idempotency_key"):
        values = [operation[key] for operation in pending]
        if len(set(values)) != len(values):
            errors.append(f"$.pending_operations: duplicate {key}")
    sources = [(operation["kind"], operation["source_id"]) for operation in pending]
    if len(set(sources)) != len(sources):
        errors.append("$.pending_operations: duplicate kind/source reward identity")
    settlements = 0
    for index, operation in enumerate(pending):
        path = f"$.pending_operations[{index}]"
        if operation["operation_id"] in applied:
            errors.append(f"{path}: already applied operation cannot remain pending")
        if operation["branch_id"] != envelope["branch_id"]:
            errors.append(f"{path}.branch_id: operation targets a different branch")
        if operation["expected_revision"] != revision:
            errors.append(f"{path}.expected_revision: operation targets a stale or future revision")
        if operation["economic_config"] != envelope["economic_config"]:
            errors.append(f"{path}.economic_config: operation must use the pinned economic version and digest")
        interval = operation["offline_interval"]
        if operation["kind"] == "offline_settlement":
            settlements += 1
            if interval is None:
                errors.append(f"{path}.offline_interval: settlement requires an interval")
            else:
                if datetime.fromisoformat(interval["start_utc"].replace("Z", "+00:00")) != datetime.fromisoformat(envelope["settled_through_utc"].replace("Z", "+00:00")):
                    errors.append(f"{path}.offline_interval: must begin at settled_through_utc")
                if datetime.fromisoformat(interval["end_utc"].replace("Z", "+00:00")) <= datetime.fromisoformat(interval["start_utc"].replace("Z", "+00:00")):
                    errors.append(f"{path}.offline_interval: end must be strictly after start")
        elif interval is not None:
            errors.append(f"{path}.offline_interval: only offline settlement may carry an interval")
    if settlements > 1:
        errors.append("$.pending_operations: only one offline settlement may be prepared")
    entitlements = [entry["entitlement_id"] for entry in envelope["commerce_cache"]["entries"]]
    if len(set(entitlements)) != len(entitlements):
        errors.append("$.commerce_cache.entries: duplicate entitlement ID")
    if config_path is not None:
        digest = hashlib.sha256(Path(config_path).read_bytes()).hexdigest()
        if envelope["economic_config"]["sha256"] != digest:
            errors.append("$.economic_config.sha256: digest does not match supplied config bytes")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, help="Validate one envelope JSON file")
    parser.add_argument("--config", type=Path, help="Also compare config file bytes with pinned SHA-256")
    args = parser.parse_args()
    try:
        if args.save:
            errors = validate(read_json(args.save), config_path=args.config)
            print(json.dumps({"valid": not errors, "errors": errors, "scope": "envelope_contract_only"}, indent=2))
            return 1 if errors else 0
        fixtures = read_json(FIXTURE_PATH)
        results = []
        for case in fixtures["cases"]:
            errors = validate(case["envelope"], config_path=args.config)
            passed = (not errors) == case["valid"]
            if not case["valid"] and case.get("error_contains"):
                passed = passed and any(case["error_contains"] in error for error in errors)
            results.append({"id": case["id"], "passed": passed, "expected_valid": case["valid"], "errors": errors})
        failed = [r for r in results if not r["passed"]]
        print(json.dumps({"scope": "envelope_contract_only", "cases": len(results), "passed": len(results) - len(failed), "failed": failed}, indent=2))
        return 1 if failed else 0
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"valid": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
