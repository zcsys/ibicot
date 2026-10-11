"""Aggregate disjoint recorded intervals; period ratios use summed accounts."""
import argparse
import json
from pathlib import Path
import numpy as np


def ratio(a,b):return float(a/b) if b else None


def analyze(path,start=1,end=None):
    path=Path(path);schema=json.loads((path/'measurement-schema.json').read_text())
    fields=schema['fields'];ix={v:i for i,v in enumerate(fields)};products=schema['products']
    initial_quotes=None
    snapshot=path/'initial-snapshot.json'
    if snapshot.exists():
        initial=json.loads(snapshot.read_text());quotes=[]
        # Recorder and exporter both iterate their recorded catalog order. T1's
        # snapshot code is its elemental formula, not its catalog ID. Do not join
        # display names. T2 explicitly exposes the stable catalog ID as code.
        for tier,key,field in (('t0','elements','price'),('t1','products','avgPrice'),('t2','tier2Products','avgPrice')):
            entries=initial[key];metadata=[p for p in products if p['tier']==tier]
            if len(entries)!=len(metadata):raise ValueError('initial snapshot/catalog length mismatch')
            if tier=='t2' and [p['code'] for p in entries]!=[p['id'] for p in metadata]:
                raise ValueError('initial snapshot/catalog order mismatch')
            quotes.extend(p[field] for p in entries)
        initial_quotes=np.array(quotes,dtype=float)
    chunks=[];ticks=[]
    for file in sorted(path.glob('products-*.npz')):
        with np.load(file) as z:
            take=(z['ticks']>=start)&(True if end is None else z['ticks']<=end)
            if take.any():chunks.append(z['data'][take]);ticks.extend(z['ticks'][take].tolist())
    if not ticks:raise ValueError('no completed recording interval in requested window')
    if ticks!=list(range(ticks[0],ticks[-1]+1)):raise ValueError('gaps or overlapping product periods')
    data=np.concatenate(chunks);length=len(ticks)
    # Recorder versions before the independent legacy audit apportioned total
    # T0 company earnings equally across installed lines. Retain their raw files
    # and reconstruct product net earnings from the independently stored posted
    # accounts. Tier totals and company earnings are unaffected.
    data[:,:,ix['net']]=data[:,:,ix['revenue']]-data[:,:,ix['cogs']]+data[:,:,ix['switchIncome']]-data[:,:,ix['switchExpense']]-data[:,:,ix['rent']]
    product_rows=[]
    def group(label,mask):
        x=data[:,mask,:].sum(axis=1);s=x.sum(axis=0)
        gross=s[ix['revenue']]-s[ix['cogs']]
        count=float(x[:,ix['companies']].mean())
        unit=x[:,ix['sold']];orders=x[:,ix['attempted']]
        row=dict(group=label,ticks=length,companyDenominator=count,
            companyDenominatorMeaning=('Allocated company equivalents, not unique raw-product owners; the earnings-per-company field uses that fractional denominator.'
                if label.startswith('t0:') else 'Company count for the tested tier or disjoint single-route ownership group.'),
            revenue=float(s[ix['revenue']]),cogs=float(s[ix['cogs']]),sold=float(s[ix['sold']]),
            netEarnings=float(s[ix['net']]),grossMargin=ratio(gross,s[ix['revenue']]),
            netMargin=ratio(s[ix['net']],s[ix['revenue']]),earningsPerCompanyTick=ratio(s[ix['net']],count*length),
            realizedPrice=ratio(s[ix['revenue']],s[ix['sold']]),
            made=float(s[ix['made']]),utilization=ratio(s[ix['made']],s[ix['capacity']]),
            meanFinished=float(x[:,ix['finished']].mean()),meanInputSpace=float(x[:,ix['rawSpace']].mean()),
            finishedCoverage=ratio(x[:,ix['finished']].mean(),unit.mean()),
            finishedTurnoverInPeriod=ratio(unit.sum(),x[:,ix['finished']].mean()),
            realizedCOGSPerUnit=ratio(s[ix['cogs']],s[ix['sold']]),
            netPerUnit=ratio(s[ix['net']],s[ix['sold']]),
            endingCash=float(x[-1,ix['cash']]),endingEquity=float(x[-1,ix['equity']]),
            switchingIncome=float(s[ix['switchIncome']]),switchingExpense=float(s[ix['switchExpense']]),
            retailUnits=float(s[ix['retailSold']]),retailRequested=float(s[ix['retailRequested']]),
            retailFulfillment=ratio(s[ix['retailSold']],s[ix['retailRequested']]),
            intermediateUnits=float(s[ix['intermediateSold']]),
            salesCV=ratio(unit.std(),unit.mean()),supplierAttemptCV=ratio(orders.std(),orders.mean()),
            lastYearRealizedPrice=ratio(x[-360:,ix['revenue']].sum(),x[-360:,ix['sold']].sum()),
            previousYearRealizedPrice=ratio(x[-720:-360,ix['revenue']].sum(),x[-720:-360,ix['sold']].sum()))
        for field in ('recordedUnitCostSum','initialReferenceCostSum'):
            row[field.replace('Sum','Mean')]=ratio(s[ix[field]],s[ix['lines']]) if field in ix else None
        if initial_quotes is not None:
            sold_by_product=data[:,mask,ix['sold']].sum(axis=0)
            initial_basket_value=float(np.dot(sold_by_product,initial_quotes[mask]))
            row['initialQuoteForCurrentSalesMix']=ratio(initial_basket_value,s[ix['sold']])
            row['realizedPriceRelativeToInitialQuotes']=ratio(s[ix['revenue']],initial_basket_value)
        return row
    groups=[]
    for tier in ('t0','t1','t2'):
        groups.append(group(tier,np.array([p['tier']==tier for p in products])))
    for route in dict.fromkeys(p['route'] for p in products):
        groups.append(group(route,np.array([p['route']==route for p in products])))
    for i,p in enumerate(products):
        mask=np.zeros(len(products),dtype=bool);mask[i]=True
        product_rows.append(dict(p,**group(p['tier']+':'+p['id'],mask)))
    companies={};company_start=None;company_end=None
    for file in sorted(path.glob('companies-*.npz')):
        with np.load(file) as z:
            a=int(z['startTick']);b=int(z['endTick'])
            if a<ticks[0] or b>ticks[-1]:continue
            if company_end is not None and a!=company_end+1:raise ValueError('company interval gap/overlap')
            company_start=a if company_start is None else company_start;company_end=b
            for tier in ('t0','t1','t2'):
                for name in ('netEarnings','revenue','cogs','sold'):
                    key=tier+'_'+name
                    if key not in companies:companies[key]=z[key].copy()
                    else:companies[key]+=z[key]
            line_firm=z['t2LineFirm'];line_product=z['t2LineProduct'];operates=z['t1Operates']
    distributions=[];product_distributions=[]
    if company_end is not None:
        for tier in ('t0','t1','t2'):
            names=['all']
            if tier=='t1':names+=list(dict.fromkeys(p['route'] for p in products if p['tier']==tier))
            if tier=='t2':names+=list(dict.fromkeys(p['route'] for p in products if p['tier']==tier))
            for name in names:
                net=companies[tier+'_netEarnings'];sold=companies[tier+'_sold']
                mask=np.ones(len(net),dtype=bool)
                if name!='all':
                    metadata=[p for p in products if p['tier']==tier]
                    product_mask=np.array([p['route']==name for p in metadata])
                    if tier=='t1':mask=(operates.reshape(len(net),-1)[:,product_mask]>0).any(axis=1)
                    else:
                        mask=np.zeros(len(net),dtype=bool);mask[line_firm[product_mask[line_product]]]=True
                selected=net[mask];units=sold[mask];period=company_end-company_start+1
                distributions.append(dict(tier=tier,route=name,count=int(mask.sum()),startTick=company_start,endTick=company_end,
                    negativeShare=float(np.mean(selected < -1e-6)),zeroSalesShare=float(np.mean(units==0)),
                    earningsPerTickQuantiles=dict(zip(('min','p05','p25','median','p75','p95','max'),
                        np.quantile(selected/period,[0,.05,.25,.5,.75,.95,1]).tolist())),
                    soldPerTickQuantiles=dict(zip(('min','p05','p25','median','p75','p95','max'),
                        np.quantile(units/period,[0,.05,.25,.5,.75,.95,1]).tolist())),
                    totalNet=float(selected.sum()),totalUnits=float(units.sum()),
                    salesHHI=float(np.square(units/units.sum()).sum()) if units.sum() else None))
        # Default research T1/T2 companies each own one product, so these are
        # additive company distributions within a product. Do not apportion a
        # multi-product T0 company's entire earnings as if they were line profit.
        for tier in ('t1','t2'):
            net=companies[tier+'_netEarnings'];sold=companies[tier+'_sold']
            metadata=[p for p in products if p['tier']==tier]
            if tier=='t1':
                membership=operates.reshape(len(net),-1)>0
                single=bool(np.all(membership.sum(axis=1)==1))
            else:single=bool(np.all(np.bincount(line_firm,minlength=len(net))==1))
            if not single:continue
            period=company_end-company_start+1
            for pi,product in enumerate(metadata):
                if tier=='t1':mask=membership[:,pi]
                else:
                    mask=np.zeros(len(net),dtype=bool);mask[line_firm[line_product==pi]]=True
                if not mask.any():continue
                earnings=net[mask];units=sold[mask]
                product_distributions.append(dict(tier=tier,product=product['id'],route=product['route'],
                    count=int(mask.sum()),startTick=company_start,endTick=company_end,
                    negativeShare=float(np.mean(earnings < -1e-6)),zeroSalesShare=float(np.mean(units==0)),
                    earningsPerTickQuantiles=dict(zip(('min','p05','median','p95','max'),np.quantile(earnings/period,[0,.05,.5,.95,1]).tolist())),
                    soldPerTickQuantiles=dict(zip(('min','p05','median','p95','max'),np.quantile(units/period,[0,.05,.5,.95,1]).tolist())),
                    totalNet=float(earnings.sum()),totalUnits=float(units.sum()),
                    salesHHI=float(np.square(units/units.sum()).sum()) if units.sum() else None,
                    equalShareNormalizedSalesHHI=float(len(units)*np.square(units/units.sum()).sum()) if units.sum() else None))
    return dict(run=str(path.resolve()),startTick=ticks[0],endTick=ticks[-1],
                productNetMethod='revenue - COGS + allocated fee income - allocated fee expense - allocated rent',groups=groups,products=product_rows,
                companyDistributions=distributions,productCompanyDistributions=product_distributions,
                productCompanyDistributionScope='Single-product T1/T2 companies only. T0 company portfolios overlap raw products; company totals and product accounts are reported separately rather than inventing historical line distributions.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=analyze(a.run,a.start,a.end)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result['groups'],indent=2))


if __name__=='__main__':main()
