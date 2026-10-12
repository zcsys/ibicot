"""Strict economic-state proof for adding industrial measurement arrays only."""
import argparse
import json
from pathlib import Path
import numpy as np
from .compare_runs import compare
from .purchase_reporting import report


def verify(before,after):
    before,after=Path(before),Path(after)
    result=compare(before,after)
    allowed={'purchase-schema.json'}
    issues=[]
    for path in before.glob('purchase-*.npz'):
        with np.load(path,allow_pickle=False) as old,np.load(after/path.name,allow_pickle=False) as new:
            if set(new.files)-set(old.files)!={'industrialObservations'} or set(old.files)-set(new.files):
                issues.append('unexpected measurement additions: '+path.name)
        allowed.add('different array keys: '+path.name)
    issues.extend(item for item in result['differences'] if item not in allowed)
    old_schema=json.loads((before/'purchase-schema.json').read_text())
    new_schema=json.loads((after/'purchase-schema.json').read_text())
    if old_schema.get('version')!=1 or new_schema.get('version')!=2 or new_schema.get('retail')!=old_schema:
        issues.append('retail measurement schema changed unexpectedly')
    summary=report(after)
    result.update(status='pass' if not issues else 'fail',differences=issues,
        addedMeasurement='industrialObservations',industrialRows=len(summary['rows']),
        scope='All previously recorded arrays, checkpoint JSON, config and tick invariants match. Only the declared new industrial array and additive schema envelope are excluded from equality; new history coverage/shape/finite values are validated separately.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before',type=Path);parser.add_argument('after',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.before,args.after)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='fileHashes'}))
    if result['differences']:
        raise SystemExit(1)
