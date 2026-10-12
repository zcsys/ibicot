"""Generate runtime naming metadata from the approved Midbridge naming catalog.

The naming source is ``catalogs/midbridge-4263/naming-source.json``. Structural facts
(recipe IDs, formulas, ingredient quantities, complexity, sector assignments,
preferred materials, invention flags) are validated against the retained
structural catalog before any label is applied, so only display names change.

All tiers, including the twenty T0 company identities, use this current source.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "catalogs/midbridge-4263"
NEW_SOURCE = ROOT / "catalogs/midbridge-4263/naming-source.json"
SYMBOLS = "WEFA"


def read_new():
    return json.loads(NEW_SOURCE.read_text())


def element_id(symbol):
    return "RAW-" + symbol


def equipment_id(raw):
    return "EX-" + raw.strip("raw()")


def family_id(sector_id, complexity):
    return f"MF-{sector_id}-{complexity}"


def build_names():
    new = read_new()
    struct = json.loads((DEST / "catalog.json").read_text())
    selection = json.loads((DEST / "starting-selection.json").read_text())

    # ---- Structural cross-references -------------------------------------
    sproducts = {p["id"]: p for p in struct["products"]}
    assert len(sproducts) == 269
    assert len(new["recipes"]) == 269
    assert {r["recipe_id"] for r in new["recipes"]} == set(sproducts)

    invented = set(selection["inventedRecipeIds"])
    assert len(invented) == 105

    # ---- Main elements ----------------------------------------------------
    main_elements = [
        {"element_id": element_id(e["symbol"]), "name": e["name"], "symbol": e["symbol"]}
        for e in new["elements"]
    ]
    assert [e["symbol"] for e in main_elements] == list(SYMBOLS)
    assert [e["name"] for e in main_elements] == ["Organics", "Inorganics", "Metals", "Radioactives"]

    # ---- Refined materials ------------------------------------------------
    materials = [
        {
            "material_id": m["material_id"],
            "sector_id": m["refinery_sector_id"],
            "name": m["public_name"],
            "symbol": m["symbol"],
            "refinery_sector_name": m["refinery_sector_name"],
        }
        for m in new["refined_materials"]
    ]
    assert len(materials) == 14
    assert {m["material_id"] for m in materials} == {p["id"] for p in sproducts.values() if p["tier"] == 1}

    # ---- T0 companies (the "Old Toby & Daughters" version) ----------------
    # The new catalog's T0 names are the restored earlier-approved set, which
    # includes "Old Toby & Daughters" and "The Oligarch". Convert the catalog's
    # "extracts" string into the runtime element list.
    t0_companies = [
        {
            "company_id": f"T0-{i + 1:02}",
            "name": c["name"],
            "elements_extracted": [e.strip() for e in c["extracts"].split("+")],
        }
        for i, c in enumerate(new["t0_companies"])
    ]
    assert len(t0_companies) == 20
    assert "Old Toby & Daughters, Inc." in [c["name"] for c in t0_companies]

    # ---- T1 companies (generic stem only, like T2) -------------------------
    t1_companies = [
        {
            "sector_id": c["sector_id"],
            "material_id": c["material_id"],
            "generic_stem": c["generic_stem"],
        }
        for c in new["t1_companies"]
    ]
    assert len(t1_companies) == 14
    assert [c["sector_id"] for c in t1_companies] == [f"S1-{i:02}" for i in range(1, 15)]

    # ---- T2 sectors (name + pairing + preferred material) -----------------
    # The new catalog names each application sector; its preferred material and
    # paired refinery sector follow the one-to-one S1/S2 pairing by index.
    material_by_refinery = {m["refinery_sector_id"]: m for m in new["refined_materials"]}
    t2_sectors = []
    for s in new["t2_sectors"]:
        paired = "S1-" + s["sector_id"].split("-")[1]
        t2_sectors.append({
            "sector_id": s["sector_id"],
            "preferred_material_id": material_by_refinery[paired]["material_id"],
            "paired_t1_sector_id": paired,
            "name": s["name"],
        })
    assert len(t2_sectors) == 14
    assert [s["sector_id"] for s in t2_sectors] == [f"S2-{i:02}" for i in range(1, 15)]

    # ---- T2 companies (facility stems, no flagships) ----------------------
    t2_companies = [
        {"sector_id": c["sector_id"], "facility_stem": c["facility_stem"]}
        for c in new["t2_companies"]
    ]
    assert len(t2_companies) == 14

    # ---- Equipment classes -------------------------------------------------
    equipment_classes = [
        {"complexity": c["complexity"], "name": c["name"]}
        for c in new["equipment_classes"]
    ]
    assert len(equipment_classes) == 4

    # ---- Extraction equipment ----------------------------------------------
    extraction_equipment = [
        {"equipment_id": equipment_id(e["raw"]), "element_id": element_id(e["raw"].strip("raw()")), "name": e["equipment"]}
        for e in new["extraction_equipment"]
    ]
    assert len(extraction_equipment) == 4
    assert [e["element_id"] for e in extraction_equipment] == [f"RAW-{s}" for s in SYMBOLS]

    # ---- Machine families (14 T1 + 28 T2) ----------------------------------
    t1_families = {f["sector_id"]: f["family"] for f in new["t1_equipment_families"]}
    t2_families = {(f["sector_id"], f["complexity"]): f for f in new["t2_equipment_families"]}
    complexity_by_t1 = {s: ("C-1" if int(s.split("-")[1]) <= 4 else "C-2") for s in t1_families}

    machine_families = []
    for sector, name in sorted(t1_families.items()):
        cplx = complexity_by_t1[sector]
        count = sum(1 for r in new["recipes"] if r["sector_id"] == sector and r["tier"] == "T1")
        machine_families.append({
            "family_id": family_id(sector, cplx),
            "sector_id": sector,
            "tier": "T1",
            "complexity": cplx,
            "name": name,
            "recipe_count": count,
        })
    for (sector, cplx), f in sorted(t2_families.items()):
        count = sum(1 for r in new["recipes"] if r["sector_id"] == sector and r["complexity"] == cplx)
        machine_families.append({
            "family_id": family_id(sector, cplx),
            "sector_id": sector,
            "tier": "T2",
            "complexity": cplx,
            "name": f["family"],
            "recipe_count": count,
        })
    assert len(machine_families) == 42
    assert len({f["family_id"] for f in machine_families}) == 42

    # ---- Products (269 recipe-linked names + structural facts) ------------
    products = []
    for r in new["recipes"]:
        rid = r["recipe_id"]
        s = sproducts[rid]
        # Validate structural identity before accepting the label.
        assert r["tier"] == f"T{s['tier']}"
        assert r["complexity"] == f"C-{s['complexity']}"
        assert r["sector_id"] == s["sectorId"]
        assert r["preferred_material_id"] == (s.get("preferredMaterialId") or s["id"])
        assert r["unchanged_formula"] == s["formula"]
        # The recipe's machine family must match the sector/complexity family.
        if s["tier"] == 1:
            expected_family = t1_families[r["sector_id"]]
        else:
            expected_family = t2_families[(r["sector_id"], r["complexity"])]["family"]
        assert r["machine_family"] == expected_family, rid
        assert (s["tier"] == 1 or r["recipe_id"] in invented) == (s["tier"] == 1 or rid in invented)

        products.append({
            "recipe_id": rid,
            "tier": r["tier"],
            "complexity": r["complexity"],
            "sector_id": r["sector_id"],
            "preferred_material_id": r["preferred_material_id"],
            "unchanged_formula": r["unchanged_formula"],
            "product_name": r["product_name"],
            "machine_family": r["machine_family"],
            "installation_name": r["installation_name"],
            "machine_family_id": family_id(r["sector_id"], r["complexity"]),
            "inputs": s["inputs"],
            "ingredient_quantities": s["ingredientQuantities"],
            "output_formula": s["symbol"],
            "output_units": s["outputQuantity"],
            "space_per_output": s["spacePerItem"],
        })
    assert len(products) == 269
    assert len({p["product_name"] for p in products}) == 269
    assert len({p["installation_name"] for p in products}) == 269

    return {
        "world": {"game_title": "Midbridge Colony"},
        "main_elements": main_elements,
        "materials": materials,
        "t0_companies": t0_companies,
        "t1_companies": t1_companies,
        "t2_sectors": t2_sectors,
        "t2_companies": t2_companies,
        "equipment_classes": equipment_classes,
        "extraction_equipment": extraction_equipment,
        "machine_families": machine_families,
        "products": products,
    }


def names_only(names):
    """Return the exact runtime allowlist; never import prose or new roles."""
    return names


if __name__ == "__main__":
    names = build_names()
    out = DEST / "naming.json"
    out.write_text(json.dumps(names, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)} ({len(names['products'])} products, "
          f"{len(names['machine_families'])} machine families, "
          f"{len(names['t0_companies'])} T0 companies)")
