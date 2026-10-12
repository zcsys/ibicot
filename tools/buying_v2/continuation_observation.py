"""Numeric realized observations: schema 2 adds frozen purchase overhead."""
import numpy as np
from .jit import njit
from .float_sum import add,finish


@njit
def emit(kind,label,iv,fv,money,equity,earnings,stock,basis,quotes,sold,details,
         allocation,preferences,fees,outputs,goods,conversion):
    schema=3 if kind==1 and np.any(stock!=np.floor(stock)) else (2 if kind==0 and iv[3]==2 else 1)
    ints=[schema,kind,label];floats=[money[0],equity,earnings]
    if kind==0:
        count=iv[0];n=len(preferences);nl=len(outputs)
        ints.extend([count,n,nl,iv[2],iv[3]])
        order=np.arange(count)
        for j in range(1,count):
            i=order[j];k=j-1
            while k>=0 and (iv[4+4*i]<iv[4+4*order[k]] or (iv[4+4*i]==iv[4+4*order[k]] and iv[5+4*i]<iv[5+4*order[k]])):
                order[k+1]=order[k];k-=1
            order[k+1]=i
        for j in range(count):
            i=order[j]
            for k in range(4):ints.append(iv[4+4*i+k])
            floats.extend([fv[4+i],fv[4+count+i]])
        for i in range(iv[2]):ints.append(iv[4+4*count+iv[1]+i])
        for q in allocation:ints.append(q)
        for i in range(count):ints.append(iv[4+4*count+i])
        for q in preferences:ints.append(q)
        for q in outputs:ints.append(q)
        for i in range(4):floats.append(fv[i])
        for f in fees:floats.append(f)
        floats.extend([goods,conversion])
        if iv[3]==2:floats.append(fv[-1])
    elif kind==1:
        ints.append(len(stock))
        if schema==3:
            for q in stock:floats.append(q)
        else:
            for q in stock:ints.append(int(q))
        for b in basis:floats.append(b)
        for p in quotes:floats.append(p)
    elif kind==2 or kind==3:
        ints.append(len(sold))
        for q in sold:ints.append(q)
        for j in range(3):floats.append(details[j])
    elif kind==4:
        ints.append(len(quotes))
        for p in quotes:floats.append(p)
    elif kind==5:
        ints.append(int(details[0]));floats.extend([details[2],details[3],money[1]])
    elif kind==6:floats.extend([details[0],money[2]])
    return np.array(ints,np.int64),np.array(floats,np.float64)


def decode(record,labels):
    """Diagnostic projection only; compiled grouping can compare numeric records."""
    iv,fv=record;i=[int(x) for x in iv];f=[float(x) for x in fv]
    if i[0] not in (1,2,3):raise ValueError('unknown observation schema')
    kind=i[1]
    if i[0]==3 and kind!=1:raise ValueError('schema 3 requires native opening stock')
    if i[0]==2 and kind!=0:raise ValueError('schema 2 requires a frozen purchase')
    if kind==0 and (len(i)<8 or (i[0]==2)!=(i[7]==2)):
        raise ValueError('purchase observation schema mismatch')
    names=('Purchase','OpenBook','SettleBook','SharedSettleBook','SetQuotes','Rent','EndTick')
    d=dict(event=names[kind],label=labels[i[2]],cash=f[0],equity=f[1],postedEarnings=f[2])
    if kind==0:
        count,n,nl,active,after=i[3:8];cursor=8;offers=[];reliability=[]
        for j in range(count):
            m,s,stock,lot=i[cursor:cursor+4];cursor+=4
            offers.append((m,s,f[3+2*j],stock,lot));reliability.append(f[4+2*j])
        lines=tuple(i[cursor:cursor+active]);cursor+=active
        allocation=tuple(i[cursor:cursor+count]);cursor+=count
        funded=tuple(i[cursor:cursor+count]);cursor+=count
        preferences=tuple(i[cursor:cursor+n]);cursor+=n
        outputs=tuple(i[cursor:cursor+nl]);cursor+=nl
        k=3+2*count;unit,multiple,bill,threshold=f[k:k+4];k+=4
        fees=tuple(f[k:k+n]);k+=n
        d.update(observedPurchase=(tuple(offers),tuple(reliability),unit,multiple,lines,bill,threshold,'after' if after==1 else 'before'),
            allocation=allocation,fundedDemands=funded,preferences=preferences,outputs=outputs,fees=fees,goods=f[k],conversion=f[k+1])
        if after==2:d['observedPurchase']+=(f[-1],)
    elif kind==1:
        n=i[3]
        if i[0]==3:d.update(openingStock=tuple(f[3:3+n]),openingBasis=tuple(f[3+n:3+2*n]),openingQuote=tuple(f[3+2*n:]))
        else:d.update(openingStock=tuple(i[4:]),openingBasis=tuple(f[3:3+n]),openingQuote=tuple(f[3+n:]))
    elif kind in (2,3):d.update(sold=tuple(i[4:]),sales=f[3],cogs=f[4],feeIncome=f[5])
    elif kind==4:d['quotes']=tuple(f[3:])
    elif kind==5:d.update(eligible=bool(i[3]),charge=f[3],paid=f[4],arrears=f[5])
    else:d.update(netTransfers=f[3],nextTransferEMA=f[4])
    return d


@njit
def purchase_payment(record):
    from_schema,values=record
    if from_schema[0] not in (1,2) or from_schema[1]!=0:raise ValueError('payment requires purchase observation')
    n=from_schema[4];offset=7+2*from_schema[3]
    total=correction=0.
    for j in range(n):total,correction=add(total,correction,values[offset+j])
    return values[offset+n]+finish(total,correction)
