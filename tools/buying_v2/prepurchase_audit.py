"""Reconcile persisted sampled state records, without rerunning the simulation."""
import json
import math
from pathlib import Path


def audit(path):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines()]
    identities=set()
    result=dict(phases=len(rows),captured=0,missing=0,positivePendingCash=0,
                positiveSettledSales=0,settledUnits=0.,positiveOffers=0,positiveSupplierSales=0,supplierUnits=0.)
    for row in rows:
        identity=(row['tick'],row['phase'])
        if identity in identities: raise ValueError('duplicate phase')
        identities.add(identity)
        records={r['firm']:r for r in row['records']}
        if len(records)!=len(row['records']): raise ValueError('duplicate buyer')
        if set(records)&set(row['missing']) or sorted(list(records)+row['missing'])!=row['requested']:
            raise ValueError('sampling coverage mismatch')
        if sorted(s['firm'] for s in row['settlement'])!=sorted(records): raise ValueError('settlement coverage mismatch')
        for r in records.values():
            if (r['tick'],r['phase'])!=identity: raise ValueError('record identity mismatch')
            result['positivePendingCash']+=r['pendingSellerCash']>0
            result['positiveOffers']+=sum(o['current']['fin']>0 for m in r['offers'] for o in m['suppliers'])
        for s in row['settlement']:
            if not math.isclose(s['cashAfter'],s['cashBefore']+s['cashDelta'],rel_tol=1e-12,abs_tol=1e-9):
                raise ValueError('cash does not reconcile')
            if [x['line'] for x in s['lines']]!=records[s['firm']]['installedLines']:
                raise ValueError('line coverage mismatch')
            for x in s['lines']:
                units=x['unitsBefore']-x['sold']
                value=x['unitsBefore']*x['basisBefore']-x['sold']*x['soldBasis']
                if not math.isclose(x['unitsAfter'],units,rel_tol=1e-12,abs_tol=1e-9):
                    raise ValueError('units do not reconcile')
                if not math.isclose(x['unitsAfter']*x['basisAfter'],value,rel_tol=1e-12,abs_tol=1e-8):
                    raise ValueError('book value does not reconcile')
                result['positiveSettledSales']+=x['sold']>0
                result['settledUnits']+=x['sold']
        for x in row.get('sellerSettlement',[]):
            if not math.isclose(x['cashAfter'],x['cashBefore']+x['cashDelta'],rel_tol=1e-12,abs_tol=1e-9): raise ValueError('supplier cash does not reconcile')
            if not math.isclose(x['unitsAfter'],x['unitsBefore']-x['sold'],rel_tol=1e-12,abs_tol=1e-9): raise ValueError('supplier units do not reconcile')
            value=x['unitsBefore']*x['basisBefore']-x['sold']*x['soldBasis']
            if not math.isclose(x['unitsAfter']*x['basisAfter'],value,rel_tol=1e-12,abs_tol=1e-8): raise ValueError('supplier value does not reconcile')
            result['positiveSupplierSales']+=x['sold']>0
            result['supplierUnits']+=x['sold']
        result['captured']+=len(records);result['missing']+=len(row['missing'])
    if identities and identities!={(t,p) for t in range(1,max(t for t,p in identities)+1) for p in (3,4)}:
        raise ValueError('phase coverage gap')
    return result
