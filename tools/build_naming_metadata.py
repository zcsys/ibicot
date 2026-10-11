"""Generate runtime naming metadata from the approved complete naming JSON.

IDs, formulas, sector assignments and quantities are checked before applying
labels. No simulation population or economic parameter is changed.
"""
import json
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "catalogs/midbridge-4259-recursive"
SOURCE = ROOT / 'docs/midbridge_complete_naming_catalog.json'


def read_names():
    return json.loads(SOURCE.read_text())


def names_only(source):
    """Explicit allowlist: never import prose, new roles, rules or populations.

    IDs, recipe facts and coverage bind names to existing entities. Equipment
    maker identities are excluded: the commission cannot add supplier companies.
    """
    fields = {
        'main_elements':('element_id','name','symbol'),
        'materials':('material_id','sector_id','name','symbol','refinery_sector_name'),
        't0_companies':('company_id','name','elements_extracted'),
        't1_companies':('sector_id','material_id','generic_stem'),
        't2_sectors':('sector_id','preferred_material_id','paired_t1_sector_id','name'),
        't2_companies':('sector_id','facility_stem'),
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
    def indexed(key, field, expected):
        records = names[key]
        result = {p[field]: p for p in records}
        assert len(result) == len(records) and set(result) == set(expected), key
        return result

    raw = indexed('main_elements', 'element_id', ['RAW-'+s for s in 'WEFA'])
    assert [p['symbol'] for p in names['main_elements']] == list('WEFA')
    indexed('t0_companies', 'company_id', [f'T0-{i:02}' for i in range(1,21)])
    # Existing roster: all four, triples, pairs, then two of each singleton.
    coverage = [list(c) for size in (4,3,2) for c in combinations('WEFA', size)]
    coverage += [[s] for s in 'WEFA' for _ in range(2)]
    coverage.insert(1, list('WEFA'))
    for i, (company, slots) in enumerate(zip(names['t0_companies'], coverage), 1):
        assert company['company_id'] == f'T0-{i:02}'
        assert company['company_number'] == hex(i)
        assert company['element_ids'] == ['RAW-'+s for s in slots]
        assert company['elements_extracted'] == [raw['RAW-'+s]['name'] for s in slots]
    materials = indexed('materials', 'material_id', [p['id'] for p in catalog['products'] if p['tier']==1])
    t1 = indexed('t1_companies', 'sector_id', [f'S1-{i:02}' for i in range(1,15)])
    t2 = indexed('t2_companies', 'sector_id', [f'S2-{i:02}' for i in range(1,15)])
    assert [p['sector_id'] for p in names['t1_companies']] == [f'S1-{i:02}' for i in range(1,15)]
    assert [p['sector_id'] for p in names['t2_companies']] == [f'S2-{i:02}' for i in range(1,15)]
    assert all('flagship_name' not in p and p['generic_stem'] for p in t1.values())
    assert all('flagship_name' not in p and p['facility_stem'] for p in t2.values())
    families = {p['family_id']: p for p in names['machine_families']}
    selection = json.loads((DEST/'starting-selection.json').read_text())
    invented = set(selection['inventedRecipeIds'])
    rows = {p['recipe_id']: p for p in names['products']}
    assert len(rows) == len(names['products']) == len(catalog['products']) == 269
    assert set(rows) == {p['id'] for p in catalog['products']}
    for p in catalog['products']:
        n = rows[p['id']]
        assert n['invented_at_start'] == (p['tier']==1 or p['id'] in invented)
        family = families[n['machine_family_id']]
        assert (family['name'], family['sector_id'], family['complexity']) == (n['machine_family'], n['sector_id'], n['complexity'])
        if p['tier']==1:
            m = materials[p['id']]
            assert m['name']==n['product_name'] and m['sector_id']==p['sectorId']
            assert m['symbol']==p['symbol'].strip('()').replace('+','')
            assert t1[p['sectorId']]['material_id']==p['id']
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
    # Validate against the existing structure; do not rewrite structural or
    # historical exports for a display-only change.
    apply_names(json.loads((DEST / 'catalog.json').read_text()), names)
    (DEST / 'naming.json').write_text(json.dumps(names_only(names), indent=2)+'\n')
