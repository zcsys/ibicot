#!/usr/bin/env python3
"""Publish provenance for the fixed 36 authored cosmetics, never verification.

Run render_cosmetics_test.dart first. Only cosmetic rows in existing registries
are changed; no new manifest asset identities or economic content is created.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


catalogue = read("game/client/art/cosmetics/catalogue.json")
manifest = read("implementation/content/launch_manifest.json")
contract = read("implementation/art/production_contract.json")
expected = {item["id"] for item in manifest["cosmetics"]}
assert len(catalogue) == len(expected) == 36
assert {item["id"] for item in catalogue} == expected
sources = ["game/mobile/lib/cosmetic_art.dart", "game/mobile/lib/cosmetics.dart"]
decoration_snapshot = "source/art/cosmetics/earned-decoration-original.dart"
snapshot_path = ROOT / decoration_snapshot
snapshot_path.parent.mkdir(parents=True, exist_ok=True)
snapshot_path.write_text("// Original six earned decorations, retained under the same identities.\n"
                         + "void _drawEarnedDecoration("
                         + (ROOT / sources[0]).read_text().split("void _drawEarnedDecoration(", 1)[1])
all_exports = []
for item in catalogue:
    identity = item["id"]
    asset_id = f"asset.{identity}"
    source = f"source/art/cosmetics/{identity}.scene.json"
    presentation = f"game/assets/cosmetics/{identity}.presentation.json"
    provenance = f"source/provenance/{asset_id}.json"
    exports = [f"game/client/art/cosmetics/{identity}.{suffix}.png" for suffix in ["overlay", "preview"]]
    assert all((ROOT / path).is_file() for path in exports), identity
    all_exports.extend(exports)
    write(source, {
        "schema_version": 1, "id": identity, "asset_id": asset_id,
        "title": item["title"], "description": item["description"],
        "source": item["source"], "ordinal": item["ordinal"],
        "view_box": [0, 0, 640, 388],
        "geometry_source": sources[0], "renderer": "drawCosmetic",
        "selector": identity, "palette_only_variant": False,
        "reuse": "Existing earned decoration geometry, same asset identity" if item["source"] == "decoration" else None,
        "notes": "The named renderer branch contains the exact authored paths, shapes and coordinates. This descriptor locates code-native source; it is not a placeholder scene.",
    })
    write(presentation, {
        "schema_version": 1, "id": identity, "renderer_source": sources[0],
        "render_function": "drawCosmetic", "preview_widget": "CosmeticPreview",
        "view_box": [0, 0, 640, 388], "reduced_motion_phase": 0,
        "exported_overlay": exports[0], "exported_full_harbor_preview": exports[1],
        "economic_effects": [], "production_status": "in_production",
        "verification_evidence": None,
    })
    media = [source, *sources]
    if item["source"] == "decoration":
        media.append(decoration_snapshot)
    write(provenance, {
        "asset_id": asset_id, "author_or_tool": "Tideglass client/native AI artist; original Dart Canvas geometry",
        "creation_date": "2026-10-16", "source_media_paths": media,
        "source_media_sha256": {path: digest(path) for path in media},
        "source_kind": "original_code_native_vector",
        "license_or_authorship_basis": "Original artwork authored for this project. Existing six decorations reuse this project's earlier original geometry under the same IDs. No external image source or stock artwork.",
        "license_evidence_paths": [source],
        "allowed_uses": ["commercial_game", "modification", "distribution", "marketing"],
        "attribution_text": "Original Tideglass artwork; no third-party attribution requirement.",
        "reference_asset_permissions": ["Project-owned HarborArt used only as the preview background."],
        "export_tool_and_version": "Flutter 3.47.7 / Dart 3.13.5 / shared drawCosmetic Canvas renderer",
        "exported_paths": exports, "exported_sha256": {path: digest(path) for path in exports},
        "reviewer": None, "review_evidence": None,
        "author_review_evidence": "release/cosmetics-author-review.md",
        "status": "in_production",
    })
    row = next(row for row in contract["assets"] if row["asset_id"] == asset_id)
    row.update(status="in_production", source_exists=True, export_exists=True,
               source_descriptor_path=source, export_descriptor_path=presentation,
               provenance_path=provenance, verification_evidence=None)
    entity = next(row for row in manifest["cosmetics"] if row["id"] == identity)
    entity.update(production_status="in_production", verification_evidence=None, authored_title=item["title"])
    asset = next(row for row in manifest["assets"] if row["id"] == asset_id)
    asset.update(delivery_status="in_production", source_path=source,
                 runtime_source=sources[0], license_evidence=provenance,
                 verification_evidence=None)

write("implementation/content/launch_manifest.json", manifest)
write("implementation/art/production_contract.json", contract)
write("game/client/art/cosmetics/export-index.json", {
    "schema_version": 1, "asset_count": 36, "export_count": 72,
    "runtime_source": sources[0], "runtime_source_sha256": digest(sources[0]),
    "exported_files": {path: digest(path) for path in all_exports},
    "status": "in_production", "independent_review": None,
})
print("Published 36 existing cosmetic identities, 72 rendered exports, provenance and in-production rows.")
