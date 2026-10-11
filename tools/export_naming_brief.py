"""Export the current recursive catalog into the existing creative handoff folder.

The template contains only the user's fixed names, setting and commission.
All counts, formulas, sector mappings and attachments are verified on export.
"""
from collections import Counter
from pathlib import Path
import csv
import io
import json
import sys
from build_recursive_catalog import build, validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from economy.core import model as M
DEST = ROOT / 'catalogs/midbridge-4259/naming-handoff'
catalog = build()
validation = validate(catalog)
rows = catalog['products']
# Refuse to publish a handoff that differs from the catalog loaded by the engine.
# Display names are deliberately excluded from this structural comparison.
active = json.loads((ROOT/'catalogs/midbridge-4259-recursive/catalog.json').read_text())
structural = ('id','tier','complexity','symbol','inputs','ingredientQuantities',
              'outputQuantity','spacePerItem','formula','sectorId','preferredMaterialId')
def structure(items):
    return {p['id']:{k:p.get(k) for k in structural} for p in items}
assert structure(rows) == structure(active['products']), 'Generated recipes differ from active engine catalog'
runtime = {p['catalogId']:p for p in M.PRODUCTS+M.T2_Catalog}
assert set(runtime) == {p['id'] for p in rows}
raw_ids = dict(zip(M.ELEMENTS, ('RAW-W','RAW-E','RAW-F','RAW-A')))
code_ids = {p['code']:p['catalogId'] for p in runtime.values()}
for row in rows:
    p = runtime[row['id']]
    ids = raw_ids if row['tier']==1 else code_ids
    assert {ids[k]:q for k,q in p['inputs'].items()} == row['ingredientQuantities'], row['id']
    assert p['complexity'] == row['complexity']
    assert p['outputQty'] == row['outputQuantity']
    assert p['storageSpacePerUnit'] == row['spacePerItem']
    if row['tier']==2:
        assert row['sectorId'] == f"S2-{p['sectorIndex']+1:02}"
        assert code_ids[p['primaryMaterial']] == row['preferredMaterialId']
        if p['invented']: assert {M.T2_INPUT_PRODUCTS[i]['catalogId']:q for i,q in p['ingredients']} == row['ingredientQuantities']
by_id = {p['id']: p for p in rows}
assert Counter(p['complexity'] for p in rows) == {1:4,2:10,3:40,4:215}
records = [{'recipe_id': p['id'], 'tier':p['tier'], 'complexity':p['complexity'],
            'inputs':p['inputs'], 'ingredient_quantities':p['ingredientQuantities'],
            'formula':p['formula'], 'output_formula':p['symbol'], 'output_units':1,
            'space_per_output':p['spacePerItem'], 'sector_id':p['sectorId'],
            'preferred_material_id':p.get('preferredMaterialId',p['id'])} for p in rows]
DEST.mkdir(parents=True, exist_ok=True)
(DEST/'recipes.json').write_text(json.dumps({'format':'nameless-midbridge-full-universe-v4',
    'catalog_id':catalog['catalogId'], 'counts':{'refining':14,'manufacturing':255,'total':269},
    'company_populations':{'T0':M.N0,'T1':M.N1,'T2':M.N2_FIRMS,'T3':M.N_DISTRIBUTORS},
    'company_numbering':M.COMPANY_NUMBERING, 'rules':catalog['rules'], 'sectors':catalog['sectors'],
    'fixed_refined_symbols':{p['id']:p['symbol'].replace('(','').replace(')','').replace('+','') for p in rows if p['tier']==1},
    'recipes':records},indent=2)+'\n')
fields=['recipe_id','tier','complexity','sector_id','preferred_material_id','input_1','input_2','formula','output_units','space_per_output']
out=io.StringIO();writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
for r in records:
    entry={**r,'input_1':r['inputs'][0],'input_2':r['inputs'][1] if len(r['inputs'])>1 else ''}
    writer.writerow({k:entry[k] for k in fields})
(DEST/'recipes.csv').write_text(out.getvalue())
sectors='| T1 sector | Material ID | Material formula | T2 sector | C-3 | C-4 | T2 total |\n|---|---|---|---|---:|---:|---:|\n'
for sector in catalog['sectors']:
    if sector['tier'] != 1: continue
    counts=Counter(p['complexity'] for p in rows if p['sectorId']==sector['pairedSectorId'])
    sectors+=f"| {sector['id']} | {sector['materialId']} | `{by_id[sector['materialId']]['symbol']}` | {sector['pairedSectorId']} | {counts[3]} | {counts[4]} | {sum(counts.values())} |\n"
# Coverage only; none of the authored resource/company names are exported.
old=M._DATA['MIDBRIDGE']
t0='| Company number | Fixed name, if any | Elements extracted |\n|---|---|---|\n'
for i,co in enumerate(old['tier0Companies']):
    name=('Raw Materials Corp.','Elements Inc.')[i] if i<2 else '—'
    t0+=f"| {M.company_number(0,i)} | {name} | {' + '.join(co['elements'])} |\n"
recipes='| Recipe ID | Tier | Complexity | Sector | Preferred material ID | Input 1 | Input 2 | Formula → one output |\n|---|---|---|---|---|---|---|---|\n'
for r in records:
    recipes+=f"| {r['recipe_id']} | T{r['tier']} | C-{r['complexity']} | {r['sector_id']} | {r['preferred_material_id']} | {r['inputs'][0]} | {r['inputs'][1] if len(r['inputs'])>1 else '—'} | `{r['formula']}` |\n"
numbering='| Tier | First company number | Last company number | Companies |\n|---|---|---|---:|\n'
for tier,block in M.COMPANY_NUMBERING.items():
    numbering+=f"| {tier} | {hex(block['start'])} | {hex(block['start']+block['count']-1)} | {block['count']:,} |\n"
numbering+='\nThese ranges reflect the current full population. Product/recipe IDs remain separate identifiers.\n'
brief=(ROOT/'tools/naming_brief_template.md').read_text().replace('{{SECTORS}}',sectors).replace('{{T0_COMPANIES}}',t0).replace('{{RECIPES}}',recipes).replace('{{COMPANY_NUMBERING}}',numbering)
assert '{{' not in brief
assert all(word not in brief for word in ('105-product','105 T2','invented_at_start','companies_per_product','distributor_weight'))
assert '<thing they are doing> facility <global hex company number>' in brief
assert 'No T2 flagship names' in brief
assert 'WW, WE, WF, WA, EE, EF, EA, FF, FA, AA' in brief
assert 'Do not invent new tickers' in brief
assert 'All twenty T0 companies are public companies' in brief
assert 'No Ltd., Limited, LLC, LLP' in brief
assert 'Do not invent anything other than the requested names.' in brief
for stale in ('430','420','1,515','1,529','165','C-5','64,500','ten T2','ten T1','selected-'):
    assert stale not in (ROOT/'tools/naming_brief_template.md').read_text(), stale
assert len(records)==269 and all(r['sector_id'] for r in records)
assert len(list(csv.DictReader(io.StringIO(out.getvalue()))))==269
(DEST/'CREATIVE_BRIEF.md').write_text(brief)
print('Updated creative brief and both attachments: full possible universe: 269 recipes, 14 paired sectors; no starting-selection data.')
