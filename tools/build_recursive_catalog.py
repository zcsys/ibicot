"""Build the complete unnamed, binary-recipe catalog without changing the engine.

Run: python3 tools/build_recursive_catalog.py
Stable IDs are determined by complexity and canonical unordered input pairs.
C-1 refining remains the one-input foundation; C-2 refines raw inputs from T0.
"""
from collections import Counter
from itertools import combinations_with_replacement, product
from pathlib import Path
import csv
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'catalogs/midbridge-4259-recursive'
SYMBOLS = ('W', 'E', 'F', 'A')


def build(balanced=False):
    raw = [{'id': f'RAW-{s}', 'symbol': f'raw({s})', 'tier': 0,
            'spacePerItem': 1, 'ancestry': {s: 1}} for s in SYMBOLS]
    by_id = {p['id']: p for p in raw}
    pools = {c: [] for c in range(1, 5)}

    def add(c, inputs, expression):
        pid = f'C{c}-{len(pools[c])+1:03}'
        ancestry = Counter()
        for ingredient in inputs:
            ancestry.update(by_id[ingredient]['ancestry'])
        quantities = dict(Counter(inputs))
        formula = ' + '.join(f"{q} {by_id[i]['symbol']}" for i, q in quantities.items())
        p = {'id': pid, 'tier': 1 if c <= 2 else 2, 'complexity': c,
             'symbol': expression, 'inputs': list(inputs),
             'ingredientQuantities': quantities, 'outputId': pid, 'outputQuantity': 1,
             'formula': formula + ' → 1 ' + expression,
             'inputComplexities': [sum(by_id[i]['ancestry'].values()) for i in inputs],
             'inputTiers': [by_id[i]['tier'] for i in inputs],
             'spacePerItem': c, 'ancestry': dict(ancestry),
             'sectorId': None, 'selectedAtStart': None}
        pools[c].append(p)
        by_id[pid] = p

    for s in SYMBOLS:
        add(1, [f'RAW-{s}'], s)
    for a, b in combinations_with_replacement(SYMBOLS, 2):
        add(2, [f'RAW-{a}', f'RAW-{b}'], f'({a}+{b})')
    for c in range(3, 5):
        for left in range(1, c//2+1):
            right = c-left
            pairs = (combinations_with_replacement(pools[left], 2) if left == right
                     else product(pools[left], pools[right]))
            for a, b in pairs:
                add(c, [a['id'], b['id']], f"({a['symbol']}+{b['symbol']})")
    if balanced:
        # Keep all C3 and all compound-pair C4 recipes. Each compound then
        # appears in 4 + 10 = 14 recipes. Each basic already appears in 10 C3s,
        # so retain four basic+C3 recipes per basic. This choice is symmetric
        # under relabeling the four raw symbols and retains every dependency.
        def keep(p):
            if p['inputComplexities'] == [2, 2]:
                return True
            basic, component = (by_id[i] for i in p['inputs'])
            inner_basic, compound = (by_id[i] for i in component['inputs'])
            return basic['id'] == inner_basic['id'] and len(compound['ingredientQuantities']) == 1
        pools[4] = [p for p in pools[4] if keep(p)]
    rows = [p for c in pools for p in pools[c]]
    # Every application sector is anchored to a direct T1 ingredient.
    # Allocate forced recipes first; distribute ambiguous pairs by current load.
    sectors = []
    for index, material in enumerate(pools[1]+pools[2]):
        t1, t2 = f'S1-{index+1:02}', f'S2-{index+1:02}'
        material['sectorId'] = t1
        sectors.append({'id': t1, 'tier': 1, 'materialId': material['id'], 'pairedSectorId': t2})
        sectors.append({'id': t2, 'tier': 2, 'materialId': material['id'], 'preferredMaterialId': material['id'], 'pairedSectorId': t1})
    material_sector = {s['materialId']: s['id'] for s in sectors if s['tier']==2}
    loads = Counter()
    def eligible(p):
        return sorted({material_sector[i] for i in p['inputs'] if i in material_sector})
    for p in sorted(pools[3]+pools[4], key=lambda p: (len(eligible(p)), p['id'])):
        options = eligible(p)
        assert options
        p['sectorId'] = min(options, key=lambda sector: (loads[sector], sector))
        p['preferredMaterialId'] = next(s['materialId'] for s in sectors if s['id']==p['sectorId'])
        loads[p['sectorId']] += 1
    catalog = {'schemaVersion': 6, 'catalogId': 'midbridge-4259-recursive-v6-' + ('balanced' if balanced else 'universe'),
            'selection': 'equal-direct-appearances' if balanced else 'full-universe',
            'status': ('appearance-count experiment; not active' if balanced else 'active fresh-world catalog; supply calibration provisional'),
            'world': {'title': 'Midbridge Colony', 'year': 4259},
            'rules': {'maximumComplexity': 4, 'outputItemsPerBatch': 1, 'manufacturingInputItemsPerBatch': 2,
                      'repeatedInputsAllowedByTier': {'T1': True, 'T2': True}, 'inputOrderMatters': False,
                      'complexity': 'sum of raw ancestry units',
                      'C1Exception': 'one raw item from T0 yields one basic refined item',
                      'C2Sourcing': 'two raw items from T0; never refined inputs from T1',
                      'T2Sourcing': 'two lower-complexity products from T1 and/or T2',
                      'productIdentity': 'immediate unordered ingredient pair; nested structure retained',
                      'storage': 'raw items use one space; product items use complexity spaces',
                      'inputStorageAllocation': 'half of goods space, weighted by recipe quantity times item space',
                      'finishedStorageAllocation': 'half of goods space'},
            'sectorAssignment': 'T1 sectors pair one-to-one with T2 sectors by material. Each T2 recipe must include its sector preferred material as a direct input. Forced assignments are made first, then recipes eligible for two sectors go to the less populated eligible sector, with sector ID as tie-breaker. Equal sector sizes are not guaranteed.',
            'sectors': sectors, 'rawResources': raw, 'products': rows}

    selection_file=DEST/'starting-selection.json'
    if not balanced and selection_file.exists():
        selection=json.loads(selection_file.read_text())
        selected=set(selection['inventedRecipeIds'])
        assert selected <= {p['id'] for p in rows if p['tier']==2}
        for p in rows:
            p['selectedAtStart']=p['tier']==1 or p['id'] in selected
        catalog['startingSelectionId']=selection['selectionId']
        catalog['status']='complete recipe universe; fixed 105-product invented T2 subset'
    return catalog


def validate(catalog):
    rows = catalog['products']
    by_id = {p['id']: p for p in catalog['rawResources']+rows}
    counts = Counter(p['complexity'] for p in rows)
    balanced = catalog['selection'] == 'equal-direct-appearances'
    assert counts == {1: 4, 2: 10, 3: 40, 4: 71 if balanced else 215}
    assert len(rows) == len({p['id'] for p in rows}) == (125 if balanced else 269)
    assert len({p['symbol'] for p in rows}) == len(rows)
    sectors = {s['id']: s for s in catalog['sectors']}
    assert len(sectors) == 28
    for tier in (1, 2):
        group = [s for s in sectors.values() if s['tier'] == tier]
        assert len(group) == 14
        assert {s['materialId'] for s in group} == {p['id'] for p in rows if p['tier'] == 1}
        for sector in group:
            partner = sectors[sector['pairedSectorId']]
            assert partner['pairedSectorId'] == sector['id']
            assert partner['materialId'] == sector['materialId'] and partner['tier'] != tier
    seen = set()
    for p in rows:
        c = p['complexity']
        assert len(p['inputs']) == (1 if c == 1 else 2)
        assert p['outputQuantity'] == 1 and p['outputId'] == p['id']
        assert dict(Counter(p['inputs'])) == p['ingredientQuantities']
        assert sum(by_id[i]['spacePerItem'] for i in p['inputs']) == p['spacePerItem'] == c
        ancestry = Counter()
        for i in p['inputs']:
            ancestry.update(by_id[i]['ancestry'])
            assert by_id[i]['tier'] == 0 if c <= 2 else by_id[i]['complexity'] < c
        assert dict(ancestry) == p['ancestry'] and sum(ancestry.values()) == c
        key = (c, tuple(sorted(p['inputs'])))
        assert key not in seen
        seen.add(key)
        assert p['sectorId'] in sectors and sectors[p['sectorId']]['tier'] == p['tier']
        if p['tier'] == 1:
            assert sectors[p['sectorId']]['materialId'] == p['id']
        else:
            assert sectors[p['sectorId']]['preferredMaterialId'] == p['preferredMaterialId']
            assert p['preferredMaterialId'] in p['inputs']
        assert p['selectedAtStart'] is None or isinstance(p['selectedAtStart'],bool)
    # Independently enumerate all unordered pairs of earlier products at each
    # complexity, rather than repeating the generator's partition traversal.
    for c in range(2, 5):
        candidates = (catalog['rawResources'] if c == 2 else [p for p in rows if p['complexity'] < c])
        expected = {tuple(sorted((a['id'], b['id'])))
                    for a, b in combinations_with_replacement(candidates, 2)
                    if a['spacePerItem']+b['spacePerItem'] == c}
        actual = {tuple(sorted(p['inputs'])) for p in rows if p['complexity'] == c}
        assert actual <= expected
        if not balanced or c < 4:
            assert actual == expected
    splits = Counter('+'.join(map(str, p['inputComplexities'])) for p in rows if p['tier'] == 2)
    assert splits == {'1+2': 40, '1+3': 16 if balanced else 160, '2+2': 55}
    distribution = {s: {c: sum(p['sectorId']==s and p['complexity']==c for p in rows) for c in (3,4)}
                    for s in sectors if sectors[s]['tier']==2}
    assert sum(sum(counts.values()) for counts in distribution.values()) == (111 if balanced else 255)
    appearances = Counter()
    quantities = Counter()
    for p in rows:
        if p['tier'] != 2: continue
        appearances.update(i for i in set(p['inputs']) if by_id[i]['tier']==1)
        quantities.update(i for i in p['inputs'] if by_id[i]['tier']==1)
    if balanced:
        assert len(appearances)==14 and set(appearances.values())=={14}
        # Upper bound: a compound can appear in at most 4 C3 + 10 C4
        # recipes. Equal appearances limit basic-containing recipes to
        # 4*14=56; at most 55 compound-pair recipes remain. Total <=111.
        assert sum(p['tier']==2 for p in rows) == 4*14+55
    return {'result': 'pass', 'sectorCounts': {'T1':14,'T2':14},
            'allRecipesAssigned': True, 'everyT2RecipeIncludesPreferredMaterial': True, 'T2RepeatedImmediateInputs': sum(len(set(p['inputs'])) == 1 for p in rows if p['tier']==2), 'T2SectorComplexityCounts': distribution, 'totalRecipes': len(rows), 'T1': 14, 'T2': 111 if balanced else 255,
            'complexityCounts': dict(counts), 'T2InputComplexityPairs': dict(splits),
            'duplicateUnorderedPairs': 0, 'completePairEnumeration': not balanced,
            'T1DirectRecipeAppearances': dict(appearances), 'T1IngredientUnitsAcrossRecipes': dict(quantities),
            'maximumBalancedT2Recipes': 111, 'balancedMaximumAchieved': balanced,
            'spaceConservedForEveryRecipe': True, 'acyclicDependencies': True,
            'C2RepeatedRawPairs': sum(len(p['ingredientQuantities']) == 1 for p in rows if p['complexity']==2),
            'C4RepeatedCompoundPairs': sum(len(p['ingredientQuantities']) == 1 and p['inputComplexities']==[2,2] for p in rows if p['complexity']==4)}


def write(catalog, report, prefix=""):
    DEST.mkdir(parents=True, exist_ok=True)
    rows = catalog['products']
    payload = json.dumps(catalog, indent=2)+'\n'
    (DEST/(prefix+'catalog.json')).write_text(payload)
    fields = ['id','tier','complexity','sector_id','preferred_material_id','input_1','input_2','output_quantity','space_per_item','output_formula','recipe','invented_at_start','name','installation_name']
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
    for p in rows:
        writer.writerow(dict(zip(fields,[p['id'],p['tier'],p['complexity'],p['sectorId'],p.get('preferredMaterialId',p['id']),p['inputs'][0],p['inputs'][1] if len(p['inputs'])==2 else '',1,p['spacePerItem'],p['symbol'],p['formula'],p['selectedAtStart'],p.get('name',''),p.get('installationName','')])))
    (DEST/(prefix+'catalog.csv')).write_text(out.getvalue())
    balanced = catalog['selection'] == 'equal-direct-appearances'
    scope = 'Balanced' if balanced else 'Complete candidate'
    intro = f"# {scope} recursive recipe catalog\n\n**Midbridge Colony · 4259**\n\n"
    intro += f"{len(rows)} production recipes: 14 T1 and {report['T2']} T2. Four raw resources are source nodes, not production recipes. Names, when assigned, are included in the CSV. Starting invention flags are preserved. This export does not modify or restart the engine.\n\n"
    if catalog.get('startingSelectionId'):
        intro += 'Starting selection: 105 invented T2 products (36 C3 and 69 C4), 150 uninvented. All 14 T1 recipes are invented. Company shares reverse the product-count shares across complexities. Distributor routing follows default capacity less intermediate use; activation is 10.5% per tick. See starting-selection.json and docs/midbridge-integration.md for calibration details.\n\n'
    intro += '| Output class | Recipe count |\n|---|---:|\n'
    for c, count in report['complexityCounts'].items():
        intro += f'| C-{c} | {count} |\n'
    intro += f'| **Total** | **{len(rows)}** |\n\n'
    if balanced:
        intro += "Every T1 material appears as a direct ingredient in exactly **14 distinct T2 recipes**. Repeating a material within one recipe counts as one appearance. Compound quantities total 15 per material, versus 14 for basics: appearance equality is not consumption equality.\n\nAll 40 C-3 recipes and all 55 C-2+C-2 recipes are retained. The remaining 16 C-4 recipes are `B + (B + (X+X))`, for each of four basics B and four raw symbols X. Every T2 ingredient has its own production recipe in this catalog.\n\nThis is the largest unique subset satisfying equal direct appearances: each compound can appear in at most 4 C-3 plus 10 C-4 recipes, limiting the common appearance count to 14. Basic-containing recipes therefore number at most 4×14=56, and compound-pair recipes at most 55, giving 111 T2 recipes. The full 255-T2 candidate pool is retained in universe-catalog.json, universe-catalog.csv and universe-CATALOG.md.\n\n"
    intro += "C-1 refining uses one raw item; C-2 uses two raw items directly from T0. Every T2 recipe uses two items from lower-complexity products and yields one item. Repeats are allowed in both tiers; reversing an ingredient pair does not create a new recipe. Parenthesized structures remain distinct even when raw ancestry is equal. Every output occupies its complexity in storage spaces. Half of goods space is reserved for finished goods; input space is weighted by quantity × item space.\n\nProduct IDs come from the full universe and are retained in the subset, so gaps are intentional. Input IDs specify immediate products, not flattened ancestry. Sector membership requires its preferred material to be a direct input.\n\n"
    md=intro
    md += '## Fourteen paired sectors\n\nEach refinery material has one T1 sector and one corresponding T2 application sector. All recipes are assigned. Every T2 recipe directly consumes its sector’s preferred T1 material. Recipes with a single eligible sector are assigned first; those with two eligible sectors go to the less populated eligible sector, breaking ties by sector ID. This replaces round-robin allocation. Sector sizes follow ingredient eligibility and are not forced equal.\n\n'
    md += '| T1 sector | Material ID | Material formula | T2 sector | C-3 | C-4 | T2 total |\n|---|---|---|---|---:|---:|---:|\n'
    sector_rows=[]
    for sector in catalog['sectors']:
        if sector['tier']!=1: continue
        material=next(p for p in rows if p['id']==sector['materialId'])
        counts=report['T2SectorComplexityCounts'][sector['pairedSectorId']]
        sector_rows.append([sector['id'],material['id'],material['symbol'],sector['pairedSectorId'],counts[3],counts[4],sum(counts.values())])
        md += '| ' + ' | '.join(str(v) for v in sector_rows[-1]) + ' |\n'
    md += '\n'
    sector_csv=io.StringIO(); sector_writer=csv.writer(sector_csv)
    sector_writer.writerow(['t1_sector','material_id','material_formula','t2_sector','c3_products','c4_products','t2_total'])
    sector_writer.writerows(sector_rows)
    (DEST/(prefix+'sectors.csv')).write_text(sector_csv.getvalue())
    for c in range(1,5):
        md+=f'## C-{c} · {report["complexityCounts"][c]} recipes\n\n| Product / recipe ID | Sector | Input item 1 | Input item 2 | Recipe → one output |\n|---|---|---|---|---|\n'
        for p in rows:
            if p['complexity']==c:
                md+=f"| {p['id']} | {p['sectorId']} | {p['inputs'][0]} | {p['inputs'][1] if len(p['inputs'])==2 else '—'} | `{p['formula']}` |\n"
        md+='\n'
    (DEST/(prefix+'CATALOG.md')).write_text(md)
    report['catalogSha256']=hashlib.sha256(payload.encode()).hexdigest()
    (DEST/(prefix+'validation.json')).write_text(json.dumps(report,indent=2)+'\n')
    # Verify the human-readable/CSV delivery contains every exported ID.
    parsed=list(csv.DictReader(io.StringIO((DEST/(prefix+'catalog.csv')).read_text())))
    assert [r['id'] for r in parsed] == [p['id'] for p in rows]
    assert [r['sector_id'] for r in parsed] == [p['sectorId'] for p in rows]
    assert len([line for line in md.splitlines() if line.startswith('| C') and ' | RAW-' in line or line.startswith('| C') and ' | C' in line]) == len(rows)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    catalog=build()
    write(catalog,validate(catalog))
    universe=build(balanced=False)
    write(universe,validate(universe),prefix='universe-')
