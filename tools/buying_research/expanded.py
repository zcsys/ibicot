"""Create an isolated source copy with a dependency-closed invented selection.

The production adapter deliberately fixes 105; the only adapter edits below
relax that assertion to the exact experimental count and change its revision.
"""
import argparse
import difflib
import json
import shutil
from pathlib import Path
from .provenance import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--selection',choices=('all-c3','all'),required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    for name in ('economy','tools/buying_research','catalogs/midbridge-4259-recursive'):
        shutil.copytree(ROOT/name,a.output/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (a.output/'tools/__init__.py').write_text('')
    catpath=a.output/'catalogs/midbridge-4259-recursive';rows=json.loads((catpath/'catalog.json').read_text())['products']
    selection=json.loads((catpath/'starting-selection.json').read_text());before=selection['inventedRecipeIds']
    ids=set(before)|{p['id'] for p in rows if p['complexity']==3 or a.selection=='all' and p['tier']==2}
    for row in rows:
        if row['id'] in ids:
            assert all(x in ids or x.startswith(('C1-','C2-')) for x in row['inputs']),row['id']
    selection['inventedRecipeIds']=sorted(ids);selection['selectionId']='research-'+a.selection
    (catpath/'starting-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    adapter=a.output/'economy/core/midbridge.py';original=adapter.read_text()
    changed=original.replace('len(invented)==105',f'len(invented)=={len(ids)}').replace('midbridge-invented-105-reverse-v7',f'research-{a.selection}-{len(ids)}-reverse-v7')
    adapter.write_text(changed)
    (a.output/'expansion.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='baseline/economy/core/midbridge.py',tofile='expanded/economy/core/midbridge.py')))
    (a.output/'expansion.json').write_text(json.dumps(dict(selection=a.selection,oldCount=len(before),newCount=len(ids),
        added=sorted(ids-set(before)),dependencyClosed=True,selectionSHA256=sha(catpath/'starting-selection.json'),
        note='Population allocation and demand routing are recalculated by unchanged production initialization; inspect allocation.json.'),indent=2)+'\n')
    print(str(a.output.resolve()))


if __name__=='__main__':main()
