"""Bounded, read-only snapshots of validated industrial D3 purchase plans.

Sampling is systematic, with a hash-derived rotation, and never consumes world
randomness. These diagnostics are not a representative population estimator.
"""
import hashlib
import numpy as np
from .jit import njit

VERSION = 1
MAX_MATERIALS = 12
MAX_OFFERS = 72
MATERIAL_FIELDS = ('material', 'held', 'basis', 'target', 'space', 'incumbent',
                   'bid', 'formulaFee', 'preferenceAfter', 'feePaid')
OFFER_FIELDS = ('materialIndex', 'supplier', 'price', 'stock', 'funded', 'allocated', 'requested')


class DecisionTrace:
    def __init__(self, population, sample_size, seed, tick, tier, phase):
        if any(isinstance(v, bool) or int(v) != v or v < 0 for v in (population, sample_size, seed, tick, tier, phase)):
            raise ValueError('trace identity and sample sizes must be nonnegative integers')
        count = min(sample_size, population)
        key = f'industrial-trace-v1:{seed}:{tick}:{tier}:{phase}'.encode()
        rotation = int.from_bytes(hashlib.sha256(key).digest()[:8], 'big') % population if population else 0
        self.firms = np.array(sorted((rotation + j * population // count) % population for j in range(count)), dtype=np.int64)
        lookup = np.full(population, -1, dtype=np.int64)
        lookup[self.firms] = np.arange(count)
        # Header: captured, number of materials/offers, opening cash/room, lot.
        self.arrays = (lookup, np.zeros((count, 6)),
                       np.zeros((count, MAX_MATERIALS, len(MATERIAL_FIELDS))),
                       np.zeros((count, MAX_OFFERS, len(OFFER_FIELDS))))
        self.metadata = dict(schema=VERSION, sampling='systematic-hash-rotation-v1',
                             seed=seed, tick=tick, tier=tier, phase=phase,
                             population=population, requestedSample=sample_size,
                             policy='v2-industrial-replenishment-reference-v1',
                             boundary='validated-allocation-before-commit')

    def export(self):
        _, headers, materials, offers = self.arrays
        rows = []
        for slot, firm in enumerate(self.firms):
            h = headers[slot]
            row = dict(firm=int(firm), status='captured' if h[0] else 'callback-not-observed')
            if h[0]:
                row.update(cash=float(h[3]), freeSpace=float(h[4]), lot=int(h[5]),
                           materials=materials[slot, :int(h[1])].tolist(),
                           offers=offers[slot, :int(h[2])].tolist())
            rows.append(row)
        return dict(**self.metadata, materialFields=MATERIAL_FIELDS, offerFields=OFFER_FIELDS, decisions=rows)


@njit
def capture(trace, firm, cash, room, lot, materials, held, basis, targets, spaces,
            incumbents, bids, fees, preferences, charges, om, suppliers, prices,
            stocks, funded, allocation, requests):
    lookup, headers, material_rows, offer_rows = trace
    slot = lookup[firm]
    if slot < 0:
        return
    n, count = len(materials), len(suppliers)
    if n > material_rows.shape[1] or count > offer_rows.shape[1]:
        raise ValueError('trace capacity exceeded; no purchase committed')
    if headers[slot, 0]:
        raise ValueError('duplicate company phase trace; no purchase committed')
    for j in range(n):
        material_rows[slot,j,0] = materials[j]
        material_rows[slot,j,1] = held[j]
        material_rows[slot,j,2] = basis[j]
        material_rows[slot,j,3] = targets[j]
        material_rows[slot,j,4] = spaces[j]
        material_rows[slot,j,5] = incumbents[j]
        material_rows[slot,j,6] = bids[j]
        material_rows[slot,j,7] = fees[j]
        material_rows[slot,j,8] = preferences[j]
        material_rows[slot,j,9] = charges[j]
    for i in range(count):
        offer_rows[slot,i,0] = om[i]
        offer_rows[slot,i,1] = suppliers[i]
        offer_rows[slot,i,2] = prices[i]
        offer_rows[slot,i,3] = stocks[i]
        offer_rows[slot,i,4] = funded[i]
        offer_rows[slot,i,5] = allocation[i]
        offer_rows[slot,i,6] = requests[i]
    headers[slot,1] = n
    headers[slot,2] = count
    headers[slot,3] = cash
    headers[slot,4] = room
    headers[slot,5] = lot
    headers[slot,0] = 1


def capture_problem(trace, firm, p, materials, allocation, requests, preferences, fees, lot):
    if trace[0][firm] < 0:
        return
    ints = lambda a: np.asarray(a, dtype=np.int64)
    floats = lambda a: np.asarray(a, dtype=np.float64)
    capture(trace, firm, p.cash, p.free_space, lot, ints(materials), ints(p.held), floats(p.basis),
            ints([s-h for s,h in zip(p.slots,p.held)]), floats(p.spaces), ints(p.incumbents),
            ints(p.bids), floats(p.fees), ints(preferences), floats(fees),
            ints([o.material for o in p.offers]), ints([o.supplier for o in p.offers]),
            floats([o.price for o in p.offers]), ints([o.stock for o in p.offers]),
            ints(p.funded_demands), ints(allocation), ints(requests))


def verify_export(document, max_nodes=100000):
    """Reconstruct sampled D3 problems, replay reference selection, and check
    allocation accounting/D1/D2 independently of compiled settlement.

    A plan trace is not proof that a transaction committed. Whole-world parity
    and ledger checks are separate requirements.
    """
    from .industry_oracle import Problem, Offer
    from .funding import replenishment_plan
    if (document['schema'] != VERSION or tuple(document['materialFields']) != MATERIAL_FIELDS
            or tuple(document['offerFields']) != OFFER_FIELDS
            or document['policy'] != 'v2-industrial-replenishment-reference-v1'):
        raise ValueError('unsupported decision trace contract')
    expected = DecisionTrace(document['population'], document['requestedSample'], document['seed'],
                             document['tick'], document['tier'], document['phase'])
    if [r['firm'] for r in document['decisions']] != expected.firms.tolist():
        raise ValueError('trace sample identity mismatch')
    captured = 0
    for row in document['decisions']:
        if row['status'] == 'callback-not-observed':
            if set(row) != {'firm','status'}:
                raise ValueError('unobserved decision has fabricated measurements')
            continue
        if row['status'] != 'captured':
            raise ValueError('unknown trace status')
        mats=np.asarray(row['materials'],dtype=float)
        offers=np.asarray(row['offers'],dtype=float).reshape((-1,len(OFFER_FIELDS)))
        if (mats.ndim!=2 or mats.shape[1]!=len(MATERIAL_FIELDS) or not 0<len(mats)<=MAX_MATERIALS
                or len(offers)>MAX_OFFERS or not np.isfinite(mats).all() or not np.isfinite(offers).all()):
            raise ValueError('invalid trace dimensions/values')
        for values in (mats[:,[0,1,3,5,6,8]],offers[:,[0,1,3,4,5,6]]):
            if np.any(values != np.floor(values)) or np.any(np.abs(values)>=2**53):
                raise ValueError('trace integer is not exact')
        lot=row['lot']
        if not isinstance(lot,int) or lot<1:
            raise ValueError('invalid trace lot')
        vector=lambda col: tuple(mats[:,col])
        p=Problem(tuple(map(int,vector(1))), vector(2), vector(4),
                  tuple(int(h+t) for h,t in zip(vector(1),vector(3))), row['freeSpace'],row['cash'],
                  tuple(Offer(int(o[0]),int(o[1]),o[2],int(o[3]),lot) for o in offers),
                  tuple(map(int,vector(5))),tuple(map(int,vector(6))),vector(7),(),
                  tuple((0.,)*(int(h+t)+1) for h,t in zip(vector(1),vector(3))),
                  funded_demands=tuple(int(o[4]) for o in offers))
        funded,result=replenishment_plan(p,max_nodes)
        if funded.bids!=p.bids or funded.funded_demands!=p.funded_demands or tuple(result[0])!=tuple(offers[:,5]):
            raise ValueError('trace reference replay differs')
        bought=[0]*len(mats);paid=[0.]*len(mats);prefs=list(p.incumbents)
        for i in sorted(range(len(offers)),key=lambda i:(offers[i,0],offers[i,2],offers[i,1])):
            o=p.offers[i];q=int(offers[i,5]);request=0
            if q:
                request=max(0,p.funded_demands[i]-bought[o.material])
                if q<0 or q%lot or q>min(o.stock,request):
                    raise ValueError('invalid trace allocation')
                if q>=p.funded_demands[i]>0:
                    prefs[o.material]=o.supplier
            if request!=offers[i,6]:
                raise ValueError('trace remaining request differs')
            bought[o.material]+=q
        for j in range(len(mats)):
            incumbent=next((o for o in p.offers if o.material==j and o.supplier==p.incumbents[j]),None)
            outside=any(o.material==j and o.supplier!=p.incumbents[j] and offers[i,5]>0 for i,o in enumerate(p.offers))
            if outside and incumbent is not None and 0<p.bids[j]<=incumbent.stock:
                paid[j]=p.fees[j]
        if tuple(prefs)!=tuple(mats[:,8]) or not np.allclose(paid,mats[:,9],rtol=1e-12,atol=1e-12):
            raise ValueError('trace preference/fee differs')
        goods=sum(o.price*offers[i,5] for i,o in enumerate(p.offers))
        if goods+sum(paid)>p.cash+1e-9 or sum(q*s for q,s in zip(bought,p.spaces))>p.free_space+1e-9:
            raise ValueError('trace cash/storage overflow')
        if any(q>t for q,t in zip(bought,vector(3))):
            raise ValueError('trace input slot overflow')
        captured+=1
    return dict(sampled=len(document['decisions']),captured=captured,
                notObserved=len(document['decisions'])-captured)
