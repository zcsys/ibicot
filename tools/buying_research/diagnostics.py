"""Demand, fee, identity, inventory and recovery diagnostics from saved evidence."""
import argparse
import json
from pathlib import Path
import numpy as np
from .analyze import ratio


def products(path,start,end):
    path=Path(path);schema=json.loads((path/'measurement-schema.json').read_text());rows=[];ticks=[]
    for file in sorted(path.glob('products-*.npz')):
        with np.load(file,allow_pickle=False) as z:
            keep=(z['ticks']>=start)&(z['ticks']<=end)
            if keep.any():rows.append(z['data'][keep]);ticks.extend(z['ticks'][keep].tolist())
    if ticks!=list(range(start,end+1)):raise ValueError('requested product interval is incomplete')
    return schema,np.concatenate(rows)


def concentration(x):
    total=float(x.sum());positive=int(np.count_nonzero(x>0));n=len(x)
    return dict(total=total,positiveCompanies=positive,shareReceiving=positive/n,
        HHI=ratio(np.square(x).sum(),total*total),
        largestShare=ratio(x.max(),total),topOnePercentShare=ratio(np.sort(x)[-max(1,int(np.ceil(n*.01))):].sum(),total))


def synchrony(x):
    # First differences remove level/trend; correlations still do not identify causes.
    delta=np.diff(x,axis=0);sd=delta.std(axis=0);delta=delta[:,sd>1e-9]
    if delta.shape[1]<2:return None
    corr=np.corrcoef(delta,rowvar=False);off=corr[np.triu_indices(len(corr),1)]
    eigen=np.linalg.eigvalsh(corr)
    return dict(nonconstantProducts=len(corr),meanPairCorrelation=float(off.mean()),
        medianPairCorrelation=float(np.median(off)),p95PairCorrelation=float(np.quantile(off,.95)),
        leadingCorrelationEigenvalueShare=float(eigen[-1]/eigen.sum()))


def diagnose(path,start,end):
    path=Path(path);schema,data=products(path,start,end);ix={v:i for i,v in enumerate(schema['fields'])}
    meta=schema['products'];result=dict(run=str(path.resolve()),startTick=start,endTick=end,products=[],fees={},groups={})
    requested=[];events={};forecast_snapshots=[];request_ticks=[]
    company_files=sorted(path.glob('companies-*.npz'))
    with np.load(company_files[0],allow_pickle=False) as z:
        active1=z['t1Operates'].astype(bool)
    for file in sorted(path.glob('requests-*.npz')):
        a,b=map(int,file.stem.split('-')[1:]);lo=max(a,start);hi=min(b,end)
        if lo>hi:continue
        with np.load(file,allow_pickle=False) as z:
            requested.append(z['requested'][lo-a:hi-a+1]);request_ticks.extend(range(lo,hi+1))
            if a>=start and b<=end:
                for tier,key in (('t1','companyEvents1'),('t2','companyEvents2')):
                    if key in z:events[tier]=events.get(tier,0)+z[key]
                for tier in ('1','2'):
                    pred=z['localForecast'+tier];obs=z['localRequests'+tier]
                    take=active1 if tier=='1' else np.ones(len(pred),dtype=bool)
                    forecast_snapshots.append(dict(tier='t'+tier,tick=b,activeLines=int(take.sum()),
                        sumDecisionForecast=float(pred[take].sum()),sumOwnFirstRequests=float(obs[take].sum()),
                        shareZeroFirstRequests=float(np.mean(obs[take]==0)) if take.any() else None,
                        shareNearZeroForecast=float(np.mean(pred[take]<1e-6)) if take.any() else None))
    req=np.concatenate(requested) if requested else None
    if req is not None and request_ticks!=list(range(start,end+1)):raise ValueError('request interval incomplete')
    for i,m in enumerate(meta):
        row=data[:,i];sold=row[:,ix['sold']].sum();revenue=row[:,ix['revenue']].sum()
        q=float(req[:,i].sum()) if req is not None else None
        result['products'].append(dict(**m,sold=float(sold),requested=q,
            fulfillment=ratio(sold,q) if q is not None else None,goodsPrice=ratio(revenue,sold),
            initialReferenceCost=ratio(row[:,ix['initialReferenceCostSum']].sum(),row[:,ix['lines']].sum()) if 'initialReferenceCostSum' in ix else None,
            stockAtFirstRecordedClose=float(row[0,ix['finished']]),stockAtEnd=float(row[-1,ix['finished']]),
            zeroSalesTicks=int(np.count_nonzero(row[:,ix['sold']]==0)),noTradeInWindow=bool(sold==0)))
    for tier in ('t0','t1','t2'):
        mask=np.array([m['tier']==tier for m in meta]);rows=data[:,mask];totals=rows.sum(axis=1)
        potential=totals[:,ix['retailPotential']].sum();wanted=totals[:,ix['retailRequested']].sum();retail=totals[:,ix['retailSold']].sum()
        result['groups'][tier]=dict(retailPotential=float(potential),retailRequested=float(wanted),retailSupplied=float(retail),
            retailPriceAndFeeLost=float(potential-wanted),retailStockLost=float(wanted-retail),
            finishedStockFirstDifferenceSynchrony=synchrony(rows[:,:,ix['finished']]),
            uniqueRequestFirstDifferenceSynchrony=synchrony(req[:,mask]) if req is not None else None)
    company={};covered=[];last={}
    for file in sorted(path.glob('companies-*.npz')):
        with np.load(file,allow_pickle=False) as z:
            a=int(z['startTick']);b=int(z['endTick'])
            if a<start or b>end:continue
            covered.extend(range(a,b+1))
            for tier in ('t0','t1','t2'):
                for name in ('revenue','cogs','sold','netEarnings','switchingIncome','switchingExpense','rent'):
                    key=tier+'_'+name;company[key]=company.get(key,0)+z[key]
                last[tier+'_equity']=z[tier+'_equity'];last[tier+'_cash']=z[tier+'_cash']
    result['companyIntervalComplete']=covered==list(range(start,end+1));result['companyCoveredTicks']=len(covered)
    if covered:
        for tier in ('t0','t1','t2'):
            rev=company[tier+'_revenue'];cogs=company[tier+'_cogs'];net=company[tier+'_netEarnings'];fees=company[tier+'_switchingIncome']
            result['fees'][tier]=dict(receipts=concentration(fees),feeToMerchandiseRevenue=ratio(fees.sum(),rev.sum()),
                feeReceiptWithNoMerchandiseSaleCompanies=int(np.count_nonzero((fees>0)&(company[tier+'_sold']==0))),
                positiveNetDespiteNegativeMerchandiseGrossCompanies=int(np.count_nonzero((net>1e-6)&(rev-cogs< -1e-6))),
                negativeMerchandiseGrossShare=float(np.mean(rev-cogs< -1e-6)),
                totalMerchandiseGross=float((rev-cogs).sum()),totalNet=float(net.sum()))
        opening=path/'opening-company-accounts.npz'
        if start==1 and result['companyIntervalComplete'] and opening.exists():
            with np.load(opening,allow_pickle=False) as z:
                result['balanceChanges']={tier:dict(cash=float((last[tier+'_cash']-z[tier+'_cash']).sum()),
                    equity=float((last[tier+'_equity']-z[tier+'_equity']).sum()),postedEarnings=float(company[tier+'_netEarnings'].sum()),
                    maxCompanyEquityMinusPostedEarnings=float(np.max(np.abs(last[tier+'_equity']-z[tier+'_equity']-company[tier+'_netEarnings']))))
                    for tier in ('t0','t1','t2')}
            result['balanceChangesScope']='Per-company recorded opening balances and final company accounts; no equity-derived earnings.'
        elif start==1 and result['companyIntervalComplete'] and (path/'initial-snapshot.json').exists():
            initial=json.loads((path/'initial-snapshot.json').read_text())
            if initial['tick']!=0:raise ValueError('initial balance snapshot is not tick zero')
            result['balanceChanges']={tier:dict(cash=float(last[tier+'_cash'].sum()-initial['tiers'][tier]['cash']),
                equity=float(last[tier+'_equity'].sum()-initial['tiers'][tier]['equity']),
                postedEarnings=float(company[tier+'_netEarnings'].sum()),
                aggregateEquityMinusPostedEarnings=float(last[tier+'_equity'].sum()-initial['tiers'][tier]['equity']-company[tier+'_netEarnings'].sum()),
                maxCompanyEquityMinusPostedEarnings=None) for tier in ('t0','t1','t2')}
            result['balanceChangesScope']='Historical recorder lacks opening company arrays. Cash/equity changes use the saved tick-zero tier snapshot, while earnings are summed independently from company postings. No per-company opening reconciliation is inferred.'
    rc=path/'research-config.json'
    if rc.exists():
        names=json.loads(rc.read_text())['eventFields'];result['companyEventDistributions']={}
        for tier,x in events.items():
            result['companyEventDistributions'][tier]={name:dict(total=float(x[:,j].sum()),
                quantiles=dict(zip(('min','p05','median','p95','max'),np.quantile(x[:,j],[0,.05,.5,.95,1]).tolist())),
                zeroShare=float(np.mean(x[:,j]==0))) for j,name in enumerate(names)}
    result['decisionForecastSnapshots']=forecast_snapshots
    history=[json.loads(line) for line in (path/'ticks.jsonl').open() if line.strip()]
    history=[x for x in history if start<=x['tick']<=end]
    if [x['tick'] for x in history]!=list(range(start,end+1)):raise ValueError('tick series interval incomplete')
    result['annualAdaptation']={}
    for name in ('lm1','lm2','lm3','aov1','aov2','aov3'):
        x=np.array([row[name] for row in history]);result['annualAdaptation'][name]=dict(first=x[0].tolist(),last=x[-1].tolist(),
            min=np.min(x,axis=0).tolist(),max=np.max(x,axis=0).tolist(),
            yearEnds=[dict(tick=row['tick'],value=row[name]) for row in history if row['tick']%360==0])
    result['caveats']=[
        'Requested/fulfilled goods-price summaries are published analysis from completed ticks. R1 decisions consume lagged requested quantity only; average price and fulfillment are diagnostics, not extra fitted demand parameters.',
        'Retail price-and-fee loss is latent potential minus funded price/fee-sensitive intention; baseline uses its last attempted price-dependent quantity and is not the same intention protocol.',
        'Fee concentration and negative merchandise profit flag dependence on transfer receipts, not proof of strategic farming by these nonstrategic bots.',
        'Identity tie bias is separately established in equal-quote-tie-audit.json; first-difference synchrony is descriptive and does not isolate its cause.',
        'No genuine backlog is carried. Turnover, not unrecorded physical item age, is available.']
    return result


def recovery(path,control,start=1,end=1080,shock_end=360):
    schema,x=products(path,start,end);schema2,y=products(control,start,end)
    if schema['products']!=schema2['products']:raise ValueError('recovery requires matched catalog')
    ix={v:i for i,v in enumerate(schema['fields'])};iy={v:i for i,v in enumerate(schema2['fields'])}
    a=x[:,:,ix['retailSold']].sum(axis=1);b=y[:,:,iy['retailSold']].sum(axis=1)
    ca=np.r_[0,np.cumsum(a)];cb=np.r_[0,np.cumsum(b)];points=[]
    for tick in range(max(shock_end+360,start+359),end+1):
        j=tick-start+1;points.append(dict(tick=tick,ratio=ratio(ca[j]-ca[j-360],cb[j]-cb[j-360])))
    hits=[p['tick'] for p in points if p['ratio'] is not None and p['ratio']>=.9]
    valid=[p['ratio'] for p in points if p['ratio'] is not None]
    return dict(run=str(Path(path).resolve()),control=str(Path(control).resolve()),window=[start,end],
        shockEndedTick=shock_end,trailingTicks=360,firstFullPostShockWindowMeeting90Percent=hits[0] if hits else None,
        finalRatio=points[-1]['ratio'] if points else None,minPostShockRatio=min(valid) if valid else None,
        maxPostShockRatio=max(valid) if valid else None,reaches90PercentWithin720Ticks=bool(hits and hits[0]<=shock_end+720),
        stillAtLeast90PercentAtEnd=bool(points and points[-1]['ratio'] is not None and points[-1]['ratio']>=.9),series=points)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--start',type=int,default=1)
    p.add_argument('--end',type=int,required=True);p.add_argument('--control',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=diagnose(a.run,a.start,a.end)
    if a.control:result['recovery']=recovery(a.run,a.control,a.start,a.end)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(run=str(a.run),output=str(a.output),products=len(result['products']))))


if __name__=='__main__':main()
