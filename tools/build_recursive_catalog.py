"""Build and validate the complete binary-recipe catalog in memory.

Run: python3 tools/build_recursive_catalog.py
Prints a validation report without writing catalogs or modifying runtime data.
Stable IDs are determined by complexity and canonical unordered input pairs.
C-1 refining remains the one-input foundation; C-2 refines raw inputs from T0.
"""
from collections import Counter
from itertools import combinations_with_replacement, product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'catalogs/midbridge-4263'
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
    catalog = {'schemaVersion': 6, 'catalogId': 'midbridge-4263-v6-' + ('balanced' if balanced else 'universe'),
            'selection': 'equal-direct-appearances' if balanced else 'full-universe',
            'status': ('appearance-count experiment; not active' if balanced else 'active fresh-world catalog; supply calibration provisional'),
            'world': {'title': 'Midbridge Colony', 'year': 4263},
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


if __name__ == '__main__':
    print(json.dumps(validate(build()), indent=2))
