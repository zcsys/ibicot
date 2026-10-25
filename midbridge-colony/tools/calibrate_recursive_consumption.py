"""Independently measure weighted final demand for the selected invented recipes."""
from collections import Counter
import json
from build_recursive_catalog import build, validate, DEST


def calculate():
    catalog=build();validate(catalog)
    selected=set(json.loads((DEST/'starting-selection.json').read_text())['inventedRecipeIds'])
    rows=catalog['products']; by={p['id']:p for p in rows}
    products=[p for p in rows if p['id'] in selected]
    assert len(products)==105
    from economy.core import model as M
    # Recompute dependency flows from structural recipe rows, independently of
    # the compact runtime ingredient indices and its production-weight ledger.
    weights=dict(M.T2_FINAL_DEMAND_WEIGHTS)
    final={p['id']:weights[p['id']] for p in products}
    production=Counter(final)
    for p in sorted(products,key=lambda p:-p['complexity']):
        for i,q in p['ingredientQuantities'].items():
            if by[i]['tier']==2:
                assert i in selected
                production[i]+=q*production[p['id']]
    consumption=Counter()
    for p in products:
        for i,q in p['ingredientQuantities'].items():
            if by[i]['tier']==1:consumption[i]+=q*production[p['id']]
    assert len(consumption)==14
    for p in M.T2_PRODUCTS:
        assert production[p['catalogId']]==M.T2_PRODUCT_FIRM_COUNTS[p['id']]*M.T2_ALLOCATION_CAPACITIES[p['complexity']]
    input_space=sum(consumption[p['id']]*p['spacePerItem'] for p in rows if p['tier']==1)
    assert input_space==sum(final[p['id']]*p['spacePerItem'] for p in products)
    return {'selectionId':'midbridge-invented-105-v1','invented':105,'uninvented':150,
            'finalDemandWeights':weights,'materialConsumption':dict(consumption),
            'productionPerProduct':dict(production),'conservedSpace':input_space,
            'limits':['Reverse-complexity allocation concentrates capacity in C3; refined-material demand is not equal.',
                      'Prices, stock, cash and production gates still affect purchases.']}

if __name__=='__main__':
    report=calculate()
    (DEST/'consumption-calibration.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified weighted 105-product flow:',report['materialConsumption'])
