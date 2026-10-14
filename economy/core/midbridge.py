"""Runtime adapter for the complete binary catalog, shared with the browser.

Names come from the accepted Midbridge Colony commission. Stable recipe codes
and numeric market indices remain separate from display names and symbols.
"""
import json
from pathlib import Path

CATALOG_REVISION = 'midbridge-invented-105-t3-calibration-v13'
ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'catalogs/midbridge-4263/catalog.json'


def load_catalog():
    defaults = json.loads((DIRECTORY.parent / 'runtime-defaults.json').read_text())
    data = dict(defaults['constants'])
    catalog = json.loads(DIRECTORY.read_text())
    names = json.loads((DIRECTORY.parent / 'naming.json').read_text())
    material_names = {p['material_id']:p for p in names['materials']}
    recipe_names = {p['recipe_id']:p for p in names['products']}
    t1_companies = {p['sector_id']:p for p in names['t1_companies']}
    t2_companies = {p['sector_id']:p for p in names['t2_companies']}
    families = {p['family_id']:p for p in names['machine_families']}
    classes = {int(p['complexity'][2:]):p['name'] for p in names['equipment_classes']}

    def equipment(p):
        n = recipe_names[p['id']]
        family = families[n['machine_family_id']]
        return {'installationName':n['installation_name'], 'machineFamily':family['name'],
                'machineFamilyId':family['family_id'], 'equipmentClass':classes[p['complexity']],
                'formula':p['formula']}
    assert catalog['selection'] == 'full-universe'
    selection=json.loads((DIRECTORY.parent/'starting-selection.json').read_text())
    assert selection['allocationPolicy'] == 'reverse-complexity-product-counts'
    assert selection['distributorPolicy'] == 'default-output-capacity-less-intermediate-use-with-complexity-calibration'
    data['T3_COMPLEXITY_DEMAND_MULTIPLIERS'] = {int(c):float(v) for c,v in selection['distributorComplexityMultipliers'].items()}
    assert set(data['T3_COMPLEXITY_DEMAND_MULTIPLIERS']) == {3,4}
    assert all(0 < v < float('inf') for v in data['T3_COMPLEXITY_DEMAND_MULTIPLIERS'].values())
    invented=set(selection['inventedRecipeIds'])
    rows = catalog['products']
    assert len(invented)==105 and invented <= {p['id'] for p in rows if p['tier']==2}
    for p in rows:
        if p['id'] in invented:
            assert all(i in invented or i.startswith(('C1-','C2-')) for i in p['inputs'])
    materials = [p for p in rows if p['tier'] == 1]
    outputs = sorted((p for p in rows if p['tier'] == 2), key=lambda p: (p['id'] not in invented, p['sectorId'], p['complexity'], p['id']))
    # Compact active input markets: 14 refined materials + 36 invented C3s.
    inputs = materials + [p for p in outputs if p['complexity'] == 3 and p['id'] in invented]
    lookup = {p['id']: i for i, p in enumerate(inputs)}
    codes = {p['id']: p['symbol'].strip('()') if p['tier'] == 1 else p['id'] for p in rows}
    raw = {p['symbol']: p['name'] for p in names['main_elements']}
    data['ELEMENTS'] = [raw[slot] for slot in 'WEFA']
    elements = dict(zip('WEFA', data['ELEMENTS']))
    data['PRODUCTS'] = [{**defaults['refineryTemplate'], 'code': codes[p['id']],
        **equipment(p), 'catalogId': p['id'], 'name': recipe_names[p['id']]['product_name'],
        'symbol': material_names[p['id']]['symbol'], 'sector':material_names[p['id']]['refinery_sector_name'],
        'companyName': t1_companies[p['sectorId']]['generic_stem'], 'complexity': p['complexity'],
        'role': 'Basic refined material' if p['complexity']==1 else 'Compound refined material',
        'inputs': {elements[k[-1]]: q for k, q in p['ingredientQuantities'].items()},
        'outputQty': 1, 'storageSpacePerUnit': p['complexity']}
        for p in materials]
    sectors = [p['name'] for p in names['t2_sectors']]
    products = []
    for p in outputs:
        sector = int(p['sectorId'].split('-')[1]) - 1
        template = defaults['manufacturerTemplates'][str(p['complexity'])]
        group = 'c3' if p['complexity'] == 3 else ('c4_basic_c3' if p['inputComplexities'] == [1, 3] else 'c4_compound_pair')
        products.append({**template, 'id': len(products), 'code': p['id'], 'catalogId': p['id'], 'name': recipe_names[p['id']]['product_name'],
            **equipment(p),
            'inputs': {codes[k]: q for k, q in p['ingredientQuantities'].items()},
            'primaryMaterial': codes[p['preferredMaterialId']],
            'ingredientCatalogIds':dict(p['ingredientQuantities']),
            'ingredients': sorted([[lookup[k], q] for k, q in p['ingredientQuantities'].items()]) if p['id'] in invented else [],
            'recipeKey': p['id'], 'complexity': p['complexity'], 'outputQty': 1,
            'storageSpacePerUnit': p['complexity'], 'sectorIndex': sector, 'sector': sectors[sector],
            'manufacturer': t2_companies[p['sectorId']]['facility_stem'],
            'invented': p['id'] in invented,
            'demandGroup': group, 'distributorWeight': 0})
    all_products=products
    products=[p for p in all_products if p['invented']]
    by_id = {p['catalogId']: p for p in data['PRODUCTS'] + all_products}
    data['TIER_BOUNDARIES'] = {**data['TIER_BOUNDARIES'], 'T2':[3,4]}
    data.update(T2_INPUT_PRODUCTS=[by_id[p['id']] for p in inputs],
        T2_PRODUCTS=products, T2_Catalog=all_products, T2_UNINVENTED_PRODUCTS=[p for p in all_products if not p['invented']],
        T2_Catalog_COUNT=len(all_products), T2_COMPLEXITY_COUNTS=[sum(p['complexity'] == c for p in products) for c in range(1, 6)],
        INVENTED_PER_COMPLEXITY={str(c): sum(p['complexity'] == c for p in products) for c in (3,4,5)},
        T2_SECTORS=sectors, T2_SECTOR_WEIGHTS=[1]*14, T2_ADJACENCY=[[] for _ in sectors],
        T2_SECTOR_DEFINITIONS=[{'name':p['name'],'description':'Preferred input: '+material_names[p['preferred_material_id']]['name']} for p in names['t2_sectors']],
        T2_SECTOR_MANUFACTURERS=[{'sector':s,'company':p['facility_stem']} for s,p in zip(sectors,names['t2_companies'])],
        T2_MANUFACTURER_BY_SECTOR={s:p['facility_stem'] for s,p in zip(sectors,names['t2_companies'])},
        T1_COMPANY_NAMES=[p['companyName'] for p in data['PRODUCTS']],
        # Existing machinery supplier is T0 company 6; rename it, do not add the
        # commission's four independent maker companies. Its role stays intact.
        EQUIPMENT_MAKERS=[names['t0_companies'][6]['name']],
        EQUIPMENT_CONFIG={str(c):name for c,name in classes.items()},
        NAMING_CATALOG=names,
        WORLD_STORY={**data['WORLD_STORY'], 'name':names['world']['game_title']},
        MIDBRIDGE={'tier0Companies':[{'name':p['name'],'elements':p['elements_extracted']} for p in names['t0_companies']]})
    return data
