"""Audit catalog scope under executed same-sector installation restrictions."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/'catalogs/midbridge-4259-recursive/catalog.json'
SELECTION=CATALOG.with_name('starting-selection.json')


def audit(catalog,selected):
    products=catalog['products'];by={p['id']:p for p in products}
    if len(by)!=len(products) or len(set(selected))!=len(selected) or not set(selected)<=set(by):
        raise ValueError('invalid recipe identities or selection')
    edges=[];same=[]
    for p in products:
        if p['tier']!=2:continue
        for ingredient in sorted(set(p['inputs'])):
            if ingredient not in by:raise ValueError('unknown ingredient')
            source=by[ingredient]
            if source['tier']==2:
                row=dict(output=p['id'],input=ingredient,outputSector=p['sectorId'],inputSector=source['sectorId'],
                         initiallyInvented=p['id'] in selected and ingredient in selected)
                edges.append(row)
                if source['sectorId']==p['sectorId']:same.append(row)
    return dict(catalogId=catalog['catalogId'],products=len(products),manufacturedProducts=sum(p['tier']==2 for p in products),
                selectedManufacturedProducts=sum(by[i]['tier']==2 for i in selected),
                manufacturedInputEdges=len(edges),initiallyInventedEdges=sum(e['initiallyInvented'] for e in edges),
                sameSectorEdges=same,edges=edges,
                conclusion=('No same-sector manufactured-input edge exists in this catalog. Under same-sector installation, own output cannot be an input to another installed line.' if not same else
                            'Same-sector manufactured-input edges exist; self-supply needs explicit handling.'),
                boundary='Conditional on executed same-sector installation and fixed company sector; not proof for a different catalog or ownership rule. Duplicate-product installation is separately prohibited and tested.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    selected=json.loads(SELECTION.read_text())['inventedRecipeIds']
    result=audit(json.loads(CATALOG.read_text()),selected)
    files=(CATALOG,SELECTION,ROOT/'economy/core/state.py',Path(__file__))
    result['sourceHashes']={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
    for source in files:
        target=a.output/'source'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('edges','sourceHashes')}))


if __name__=='__main__':main()
