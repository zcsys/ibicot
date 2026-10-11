"""Compare posted prices, last-batch costs and current-quote replacement bills.

Read saved arrays only. The replacement comparator ignores stocks, sampling,
fees, rent and owned inputs; it is not a claim about an executable purchase.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from economy.core import model as M


def mean(values):
    x=np.asarray(values);x=x[np.isfinite(x)]
    return float(x.mean()) if len(x) else None


def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def validate_replacement_bills(data):
    """Independent catalog-ID arithmetic, without the runtime recipe adapter."""
    run=Path(data['run']);cfg=json.loads((run/'config.json').read_text())
    catalog_path=Path(__file__).resolve().parents[2]/'catalogs/midbridge-4259-recursive/catalog.json'
    manifest=json.loads((run/'manifest.json').read_text())
    assert file_hash(catalog_path)==manifest['sourceHashes']['catalogs/midbridge-4259-recursive/catalog.json']
    catalog={p['id']:p for p in json.loads(catalog_path.read_text())['products']}
    quotes={r['id']:r['postedQuote'] for r in data['products']}
    for code,name in zip(('W','E','F','A'),('Water','Earth','Fire','Air')):
        quotes['RAW-'+code]=quotes[name]
    errors=[];repeated=0
    for row in data['products']:
        if row['tier']=='t0':continue
        product=catalog[row['id']]
        # This catalog's recipes each produce one item. Multiplicities are
        # quantities, so a repeated input contributes its full count.
        assert product['outputQuantity']==1
        expected=cfg['conversionFactor']*max(1,product['complexity']-1)
        expected+=sum(q*quotes[k] for k,q in product['ingredientQuantities'].items())
        errors.append(abs(expected-row['quoteReplacementCost']))
        repeated+=any(q>1 for q in product['ingredientQuantities'].values())
    assert max(errors,default=0)<1e-12
    return dict(status='pass',productsChecked=len(errors),repeatedIngredientProducts=repeated,
        maximumAbsoluteError=max(errors,default=0),catalogSHA256=file_hash(catalog_path))


def snapshot(run, tick):
    run=Path(run);stem=run/f'checkpoint-{tick:06}'
    meta=json.loads(stem.with_suffix('.json').read_text())
    if meta['catalogRevision']!=M.CATALOG_REVISION:
        raise ValueError('Use the matching catalog/source for this checkpoint')
    assert meta['tick']==tick
    cfg=meta['cfg'];initial=json.loads((run/'initial-snapshot.json').read_text())
    lc=int(meta['scalars']['t2LineCount']);rows=[]
    with np.load(stem.with_suffix('.npz'),allow_pickle=False) as z:
        p0=z['t0Price'].reshape(M.N0,M.NE);c0=z['t0Cost'].reshape(M.N0,M.NE)
        for i,product in enumerate(M.ELEMENTS):
            active=np.isfinite(p0[:,i]);saved=initial['elements'][i]
            assert saved['code']==product[0]
            rows.append(dict(tier='t0',group='extraction',id=product,lines=int(active.sum()),
                initialPostedQuote=saved['price'],
                initialReferenceCost=cfg['baseCost']*saved['difficulty'],
                postedQuote=mean(p0[active,i]),lastRecordedUnitCost=mean(c0[active,i]),
                quoteReplacementCost=mean(c0[active,i])))
        raw_quote={r['id']:r['postedQuote'] for r in rows}
        p1=z['t1Price'].reshape(M.N1,M.NP);c1=z['t1UnitCost'].reshape(M.N1,M.NP)
        op=z['t1Operates'].reshape(M.N1,M.NP)
        for i,product in enumerate(M.PRODUCTS):
            active=op[:,i].astype(bool);saved=initial['products'][i]
            assert saved['code']==product['code']
            replacement=sum(q*raw_quote[key] for key,q in product['inputs'].items())/product['outputQty']+M.conversion_cost(product['complexity'],cfg)
            rows.append(dict(tier='t1',group='c'+str(product['complexity']),id=product['catalogId'],
                lines=int(active.sum()),initialPostedQuote=saved['avgPrice'],
                initialReferenceCost=saved['avgUnitCost'],postedQuote=mean(p1[active,i]),
                lastRecordedUnitCost=mean(c1[active,i]),quoteReplacementCost=replacement))
        p2=z['t2Price'][:lc];c2=z['t2UnitCost'][:lc];ids=z['t2LineProduct'][:lc]
        quotes={r['id']:r['postedQuote'] for r in rows if r['tier']=='t1'}
        for product in M.T2_PRODUCTS:
            quotes[product['catalogId']]=mean(p2[ids==product['id']])
        for i,product in enumerate(M.T2_PRODUCTS):
            active=ids==product['id'];saved=initial['tier2Products'][i]
            assert saved['code']==product['catalogId']
            replacement=sum(q*quotes[key] for key,q in product['ingredientCatalogIds'].items())/product['outputQty']+M.conversion_cost(product['complexity'],cfg)
            rows.append(dict(tier='t2',group=product['demandGroup'],id=product['catalogId'],
                lines=int(active.sum()),initialPostedQuote=saved['avgPrice'],
                initialReferenceCost=saved['avgUnitCost'],postedQuote=mean(p2[active]),
                lastRecordedUnitCost=mean(c2[active]),quoteReplacementCost=replacement))
    groups=[]
    for label in ('t0','t1','t2','extraction','c1','c2','c3','c4_basic_c3','c4_compound_pair'):
        selected=[r for r in rows if r['tier']==label or r['group']==label]
        weight=sum(r['lines'] for r in selected)
        groups.append(dict(group=label,activeProductionLines=weight,**{
            key:sum(r[key]*r['lines'] for r in selected)/weight
            for key in ('initialPostedQuote','initialReferenceCost','postedQuote','lastRecordedUnitCost','quoteReplacementCost')}))
    return dict(run=str(run.resolve()),tick=tick,groups=groups,products=rows,
        checkpointJSONSHA256=hashlib.sha256(stem.with_suffix('.json').read_bytes()).hexdigest(),
        checkpointNPZSHA256=file_hash(stem.with_suffix('.npz')),
        definitions=dict(weighting='Arithmetic mean over active production lines, not period-sales weights.',
            lastRecordedUnitCost='T1/T2 last successful batch cost, or synthetic initialized cost before any production; no freshness claim. T0 recorded current extraction cost.',
            quoteReplacementCost='One output bill using arithmetic mean posted input quotes plus conversion. Includes zero-stock quoted suppliers; excludes fees, rent, storage, owned inputs and supplier sampling. T0 uses its recorded extraction cost.',
            timing='All current prices/costs are the saved end-of-tick snapshot, not a reconstructed period average.',
            initial='Original tick-zero snapshot quote and recorded unit cost; T0 initial cost is base cost times saved difficulty.'),
        sourceIdentity=json.loads((run/'manifest.json').read_text())['sourceIdentity'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    p.add_argument('--tick',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=snapshot(a.run,a.tick)
    data['replacementBillValidation']=validate_replacement_bills(data)
    with a.output.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(run=str(a.run),tick=a.tick,products=len(data['products']))))


if __name__=='__main__':main()
