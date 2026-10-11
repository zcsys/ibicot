"""Rebuild named catalog artifacts from the accepted Markdown commission.

IDs, formulas, sector assignments and quantities are checked before applying
labels. No simulation population or economic parameter is changed.
"""
import csv
import json
import re
from pathlib import Path
from build_recursive_catalog import build, validate, write, DEST

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/Midbridge_Colony_Naming_Catalog.md'


def read_names():
    return json.loads(re.search(r'```json\s*(.*?)```', SOURCE.read_text(), re.S)[1])


def names_only(source):
    """Explicit allowlist: never import prose, new roles, rules or populations.

    IDs, recipe facts and coverage bind names to existing entities. Equipment
    maker identities are excluded: the commission cannot add supplier companies.
    """
    fields = {
        'main_elements':('element_id','name','symbol'),
        'materials':('material_id','sector_id','name','symbol','refinery_sector_name'),
        't0_companies':('company_id','name','elements_extracted'),
        't1_companies':('sector_id','material_id','flagship_name','generic_stem'),
        't2_sectors':('sector_id','preferred_material_id','paired_t1_sector_id','name'),
        't2_companies':('sector_id','flagship_name','generic_stem'),
        'equipment_classes':('complexity','name'),
        'extraction_equipment':('equipment_id','element_id','name'),
        'machine_families':('family_id','sector_id','tier','complexity','name','series','recipe_count'),
        'products':('recipe_id','tier','complexity','sector_id','preferred_material_id',
            'unchanged_formula','product_name','machine_family','installation_name',
            'machine_family_id','inputs','ingredient_quantities','output_formula','output_units','space_per_output'),
    }
    return {'world':{'game_title':source['world']['game_title']},
            **{key:[{f:row[f] for f in allowed} for row in source[key]] for key,allowed in fields.items()}}


def apply_names(catalog, names):
    rows = {p['recipe_id']: p for p in names['products']}
    assert len(rows) == len(names['products']) == len(catalog['products']) == 269
    assert set(rows) == {p['id'] for p in catalog['products']}
    for p in catalog['products']:
        n = rows[p['id']]
        for field, source in [('formula','unchanged_formula'), ('sectorId','sector_id'),
                ('ingredientQuantities','ingredient_quantities'), ('inputs','inputs'),
                ('symbol','output_formula'), ('outputQuantity','output_units'),
                ('spacePerItem','space_per_output')]:
            assert p[field] == n[source], (p['id'], field)
        assert n['tier'] == f"T{p['tier']}" and n['complexity'] == f"C-{p['complexity']}"
        assert n['preferred_material_id'] == p.get('preferredMaterialId',p['id'])
        p.update(name=n['product_name'],
                 installationName=n['installation_name'], machineFamily=n['machine_family'],
                 machineFamilyId=n['machine_family_id'])
    assert len({p['product_name'] for p in rows.values()}) == 269
    assert len({p['installation_name'] for p in rows.values()}) == 269
    material = {p['sector_id']:p for p in names['materials']}
    sectors = {p['sector_id']:p for p in names['t2_sectors']}
    for s in catalog['sectors']:
        s['name'] = material[s['id']]['refinery_sector_name'] if s['tier']==1 else sectors[s['id']]['name']
    catalog['world']['title'] = names['world']['game_title']
    catalog['namingSource'] = str(SOURCE.relative_to(ROOT))
    return catalog


if __name__ == '__main__':
    names = read_names()
    catalog = apply_names(build(), names)
    report = validate(catalog)
    write(catalog, report)
    write(catalog, dict(report), prefix='universe-')
    # Complete named CSV complements the structural recipe export.
    with (DEST/'named-products.csv').open('w',newline='') as f:
        fields=['recipe_id','product_name','tier','complexity','sector_id','unchanged_formula','machine_family','installation_name']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader(); writer.writerows(names['products'])
    for prefix in ('','universe-'):
        path=DEST/(prefix+'CATALOG.md')
        text=path.read_text().replace('Names remain unset.', 'Names are applied from the accepted Midbridge Colony Naming Catalog; see naming.json and named-products.csv.')
        text+='\n## Accepted product and installation names\n\n| Recipe | Product | Installation |\n|---|---|---|\n'
        text+=''.join(f"| {p['recipe_id']} | {p['product_name']} | {p['installation_name']} |\n" for p in names['products'])
        path.write_text(text)
    (DEST/'naming.json').write_text(json.dumps(names_only(names),indent=2)+'\n')
