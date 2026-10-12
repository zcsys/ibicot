"""Optional bounded snapshots of the existing Distributor basket decision."""
import numpy as np
from .decision_traces import DecisionTrace
from .jit import njit

FIELDS=('status','market','latent','rounding','halfPrice','eta','incumbent','bid','formulaFee',
        'preferenceAfter','feePaid','surplus','goodsCost','potentialQuantity','offerCount')
OFFER_FIELDS=('supplier','price','stock','desired','allocated','requested')


class RetailTrace:
    def __init__(self,population,sample_size,seed,tick,activation):
        if not np.isfinite(activation) or not 0<=activation<=1:
            raise ValueError('invalid activation probability')
        sample=DecisionTrace(population,sample_size,seed,tick,3,0)
        self.firms=sample.firms
        self.arrays=(sample.arrays[0],np.zeros((len(self.firms),len(FIELDS))),np.zeros((len(self.firms),6,len(OFFER_FIELDS))))
        self.metadata=dict(schema=1,kind='distributor-decision',sampling=sample.metadata['sampling'],
                           seed=seed,tick=tick,population=population,requestedSample=sample_size,
                           boundary='selected-basket-before-commit',cashConstraint='none',activation=activation)

    def export(self):
        rows=[]
        for slot,buyer in enumerate(self.firms):
            h=self.arrays[1][slot]
            status=('inactive','zero-potential','captured')[int(h[0])]
            row=dict(buyer=int(buyer),status=status)
            if status!='inactive':
                row['inputs']=dict(zip(FIELDS[1:],h[1:].tolist()))
            if status=='captured':
                row['offers']=self.arrays[2][slot,:int(h[-1])].tolist()
            rows.append(row)
        return dict(**self.metadata,offerFields=OFFER_FIELDS,decisions=rows)


@njit
def capture(trace,buyer,market,latent,rounding,half,eta,incumbent,bid,fee,new_incumbent,charge,
            objective,goods,potential,ids,quotes,stocks,desired,allocation,ranks):
    lookup,headers,offers=trace
    slot=lookup[buyer]
    if slot<0:
        return
    if len(ids)>6 or headers[slot,0]:
        raise ValueError('duplicate or oversized retail trace; no purchase committed')
    headers[slot,1]=market
    headers[slot,2]=latent
    headers[slot,3]=rounding
    headers[slot,4]=half
    headers[slot,5]=eta
    headers[slot,6]=incumbent
    headers[slot,7]=bid
    headers[slot,8]=fee
    headers[slot,9]=new_incumbent
    headers[slot,10]=charge
    headers[slot,11]=objective
    headers[slot,12]=goods
    headers[slot,13]=potential
    headers[slot,14]=len(ids)
    for i in range(len(ids)):
        offers[slot,i,0]=ids[i]
        offers[slot,i,1]=quotes[i]
        offers[slot,i,2]=stocks[i]
        offers[slot,i,3]=desired[i]
        offers[slot,i,4]=allocation[i]
    bought=0
    for i in ranks:
        if allocation[i]>0:
            offers[slot,i,5]=max(0,desired[i]-bought)
            bought+=allocation[i]
    if bought==0 and len(ids)>0:
        i=ranks[0]
        if desired[i]>0 and stocks[i]==0:
            offers[slot,i,5]=desired[i]
    headers[slot,0]=2


def verify_export(document):
    """Replay the existing quantity curve/solver; separately check postings.

    This is reconstruction, not an independent proof of solver optimality.
    """
    import math
    from .retail import solve_retail
    from economy.core.rng import random_
    if document['schema']!=1 or document['kind']!='distributor-decision' or tuple(document['offerFields'])!=OFFER_FIELDS:
        raise ValueError('unsupported retail trace')
    sample=RetailTrace(document['population'],document['requestedSample'],document['seed'],document['tick'],document['activation'])
    if [r['buyer'] for r in document['decisions']]!=sample.firms.tolist():
        raise ValueError('retail sample identity mismatch')
    counts=dict(inactive=0,zeroPotential=0,captured=0)
    for row in document['decisions']:
        active=random_(document['seed'],document['tick'],row['buyer']+2000000)<document['activation']
        if (row['status']=='inactive')==active:
            raise ValueError('retail activation differs')
        if row['status']=='inactive':
            if set(row)!={'buyer','status'}:
                raise ValueError('inactive buyer has fabricated observations')
            counts['inactive']+=1
            continue
        h=row['inputs']
        if not all(math.isfinite(v) for v in h.values()):
            raise ValueError('nonfinite retail trace')
        rounding=random_(document['seed'],document['tick'],row['buyer']+7000000)
        latent=h['latent'];potential=math.floor(latent)+int(rounding<latent%1)
        if h['rounding']!=rounding or h['potentialQuantity']!=potential:
            raise ValueError('retail rounding/potential differs')
        if row['status']=='zero-potential':
            if potential>0 or 'offers' in row:
                raise ValueError('invalid zero potential')
            counts['zeroPotential']+=1
            continue
        if row['status']!='captured' or potential<=0:
            raise ValueError('invalid retail status')
        o=np.asarray(row['offers'],dtype=float).reshape((-1,len(OFFER_FIELDS)))
        if len(o)>6 or len(o)!=h['offerCount'] or not np.isfinite(o).all():
            raise ValueError('invalid retail offers')
        for column in (0,2,3,4,5):
            if np.any(o[:,column]!=np.floor(o[:,column])) or np.any(o[:,column]<0) or np.any(o[:,column]>=2**53):
                raise ValueError('invalid retail integer')
        ids=o[:,0].astype(np.int64);prices=o[:,1];stocks=o[:,2].astype(np.int64)
        if len(set(ids))!=len(ids) or np.any(prices<=0):
            raise ValueError('invalid retail identities/quotes')
        half=h['halfPrice'];eta=h['eta']
        if eta<=0:
            raise ValueError('invalid retail elasticity')
        desired=[]
        for price in prices:
            q=latent/(1+(price/half)**eta) if half>0 else 0.
            desired.append(math.floor(q)+int(rounding<q%1))
        if desired!=o[:,3].tolist():
            raise ValueError('retail quote demand differs')
        inc=int(h['incumbent']);positions=np.flatnonzero(ids==inc)
        bid=desired[int(positions[0])] if len(positions) else 0
        if bid!=h['bid']:
            raise ValueError('retail incumbent bid differs')
        values=np.array([half*(latent/max(unit+rounding,1e-12)-1)**(1/eta)
                         if half>0 and unit+rounding<latent else 0. for unit in range(potential)])
        result=solve_retail(values,prices,stocks,ids,inc,bid,h['formulaFee'],1e100,np.array(desired,dtype=np.int64))
        if not np.array_equal(result[0],o[:,4]) or not np.allclose(result[1:4],[h['surplus'],h['goodsCost'],h['feePaid']],rtol=1e-12,atol=1e-12) or result[4]!=h['preferenceAfter']:
            raise ValueError('retail selection replay differs')
        purchased=o[:,4];requests=np.zeros(len(o));bought=0
        for i in np.argsort(prices):
            if purchased[i]>0:
                requests[i]=max(0,desired[i]-bought)
                if purchased[i]>min(stocks[i],requests[i]):
                    raise ValueError('retail request/stock exceeded')
                bought+=purchased[i]
        if bought==0 and len(o):
            i=np.argsort(prices)[0]
            if desired[i]>0 and stocks[i]==0:
                requests[i]=desired[i]
        payable=(h['formulaFee'] if len(positions) and bid>0 and stocks[positions[0]]>=bid
                 and any(q>0 and supplier!=inc for q,supplier in zip(purchased,ids)) else 0.)
        if not np.array_equal(requests,o[:,5]) or not math.isclose(payable,h['feePaid'],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('retail requests/fee differ')
        preference=inc
        for i in sorted(range(len(o)),key=lambda i:(prices[i],ids[i]!=inc,ids[i])):
            if purchased[i]>0 and purchased[i]>=desired[i]:
                preference=int(ids[i])
                break
        if preference!=h['preferenceAfter'] or not math.isclose(float(np.dot(purchased,prices)),h['goodsCost'],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('retail preference/goods payment differs')
        counts['captured']+=1
    return counts
