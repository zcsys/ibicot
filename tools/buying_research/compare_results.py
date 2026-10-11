"""Compare completed study outputs without treating ticks as independent trials."""
import argparse
import csv
import json
from pathlib import Path


def relative(a, b):
    return float(a / b - 1) if b is not None and b != 0 and a is not None else None


def fairness(control, reverse):
    """Preregistered route mean/tail flags; undefined zero bases stay missing."""
    cg = {x['group']: x for x in control['groups']}
    cd = {(x['tier'], x['route']): x for x in control['companyDistributions']}
    rows = []
    for row in reverse['groups']:
        base = cg[row['group']]
        metrics = {}
        for name in ('earningsPerCompanyTick', 'retailFulfillment'):
            change = relative(row[name], base[name])
            metrics[name] = dict(control=base[name], reversed=row[name], relativeChange=change,
                                 exceedsFivePercent=None if change is None else abs(change) > .05)
        rows.append(dict(group=row['group'], means=metrics))
    tails = []
    for row in reverse['companyDistributions']:
        base = cd[(row['tier'], row['route'])]
        changes = {}
        for metric in ('earningsPerTickQuantiles', 'soldPerTickQuantiles'):
            changes[metric] = {}
            for quantile in ('p05', 'p95'):
                a, b = row[metric][quantile], base[metric][quantile]
                change = relative(a, b)
                changes[metric][quantile] = dict(control=b, reversed=a, absoluteChange=a-b,
                    relativeChange=change, exceedsTenPercent=None if change is None else abs(change) > .1)
        tails.append(dict(tier=row['tier'], route=row['route'], count=row['count'], metrics=changes))
    return dict(control=control['run'], reversed=reverse['run'],
                window=[control['startTick'], control['endTick']], means=rows, tails=tails,
                caveat='Matched seed and full-population initial state, both industry and retail priorities reversed. Distribution changes test sensitivity, not equality of every contested buyer outcome. Undefined relative changes are not passes.')


def compare(root, study, diagnostics, baseline_replay_verification=None):
    master = json.loads((study / 'study.json').read_text())
    if master['status'] != 'complete' or master['pending']:
        raise ValueError('The study is incomplete')
    rows = {x['id']: x for x in master['runs']}
    control = rows['20261011-control-market-137']
    output = dict(pairedHeldOut=master['paired'], ablations=[], extendedLocal=[], expanded=[],
                  performance=[], recovery=[], invariants={}, fairness={}, longRunDrift=[])
    with (study/'annual-groups.csv').open() as f:
        annual={(x['run'],int(x['end']),x['group']):x for x in csv.DictReader(f)}
    for run, row in rows.items():
        if row['ticks']>=7200:
            end=row['ticks'];latest=json.loads((study/(run+'-lastYear.json')).read_text())
            drift=[]
            for group in latest['groups']:
                prior=annual[(run,end-360,group['group'])]
                p=float(prior['realizedPrice']) if prior['realizedPrice'] else None
                price_change=relative(group['realizedPrice'],p)
                unit_change=relative(group['sold'],float(prior['sold']))
                drift.append(dict(group=group['group'],companyCount=group['companyDenominator'],
                    previousYearPrice=p,lastYearPrice=group['realizedPrice'],priceChange=price_change,
                    soldUnitsChange=unit_change,retailUnitsChange=relative(group['retailUnits'],float(prior['retailUnits'])),
                    netProfitChange=relative(group['netEarnings'],float(prior['netEarnings'])),
                    flagsPriceRiseOverTenPercentWithFewerSoldUnits=bool(price_change is not None and unit_change is not None and price_change>.1 and unit_change<0),
                    initialPriceForCurrentSalesMix=group.get('initialQuoteForCurrentSalesMix'),
                    priceRelativeToInitialQuotes=group.get('realizedPriceRelativeToInitialQuotes'),
                    finishedCoverage=group['finishedCoverage'],finishedTurnover=group['finishedTurnoverInPeriod']))
            output['longRunDrift'].append(dict(id=run,windows=[[end-719,end-360],[end-359,end]],groups=drift,
                caveat='The numerical flag means price rose over 10% while sold units fell; the magnitude and model explanation must be assessed separately. Current-sales-mix initial-quote comparison is not a fixed-basket price index.'))
        if '-ablation-' in run:
            output['ablations'].append(dict(id=run, options=row.get('options', {}), treatment=row['treatment'],
                window=row['finalWindow'], retailPerTick=row['retailPerTick'],
                retailChangeFromMarket=relative(row['retailPerTick'], control['retailPerTick']),
                netPerTick=row['netPerTick'], netMargin=row['netMargin'], utilization=row['utilization']))
        if '-sales-floor-' in run:
            output['extendedLocal'].append(row)
        if '-expanded-' in run and row['treatment']=='market':
            baseline = rows[run.replace('-market-', '-baseline-')]
            manifest = json.loads((root/run/'manifest.json').read_text())
            output['expanded'].append(dict(id=run, baseline=baseline['id'],
                retailRatio=row['retailPerTick']/baseline['retailPerTick'],
                baselineRetail=baseline['retailPerTick'], candidateRetail=row['retailPerTick'],
                baselineNet=baseline['netPerTick'], candidateNet=row['netPerTick'],
                baselineMargins=baseline['netMargin'], candidateMargins=row['netMargin'],
                sourceIdentity=manifest['sourceIdentity']))
    for kind in ('all', 'lastYear'):
        base = json.loads((study/f'20261011-control-market-137-{kind}.json').read_text())
        rev = json.loads((study/f'20261011-ablation-reverse-order-137-{kind}.json').read_text())
        output['fairness'][kind] = fairness(base, rev)
    # Load by the embedded run identity, independent of the diagnostic filename.
    diagnostic_rows={}
    for file in sorted(diagnostics.glob('*.json')):
        data = json.loads(file.read_text())
        if 'run' in data:
            name=Path(data['run']).name
            if name in diagnostic_rows:raise ValueError('Duplicate diagnostic run: '+name)
            diagnostic_rows[name]=data
        if 'recovery' in data:
            item=dict(data['recovery'])
            job=rows[Path(item['run']).name]
            item['scenario']=job.get('scenario','none')
            item['temporaryShockRecoveryGateApplicable']=item['scenario'] in ('demand-up','demand-down','raw-outage','supplier-outage')
            output['recovery'].append(item)
    if set(diagnostic_rows)!=set(rows):
        raise ValueError('Diagnostic coverage does not match the completed economic study')
    output['diagnosticCoverage']=dict(runs=len(diagnostic_rows),exactStudyMatch=True)
    output['informationComparisons']=[]
    for regime,run in (('local','20261011-recovery-none-local-137'),
                       ('market','20261011-control-market-137'),
                       ('hybrid','20261011-recovery-none-hybrid-137')):
        data=json.loads((study/(run+'-all.json')).read_text());diag=diagnostic_rows[run]
        if [data['startTick'],data['endTick']]!=[1,1080] or [diag['startTick'],diag['endTick']]!=[1,1080]:
            raise ValueError('Information diagnostics require matched three-year windows')
        output['informationComparisons'].append(dict(regime=regime,id=run,window=[1,1080],
            requests=data['requests'],fees=diag['fees'],synchrony=diag['groups'],
            forecastSnapshots=diag['decisionForecastSnapshots'],
            caveat='Forecast errors score the declared lagged output forecast against endogenous own first requests, not exogenous latent demand. CV ratios and synchrony describe these policy histories, not an identified causal bullwhip mechanism.'))
    output['longRunBalances']=[]
    for run in ('20261011-baseline-137-two-generations','20261011-long-market-137'):
        d=diagnostic_rows[run]
        output['longRunBalances'].append(dict(id=run,window=[d['startTick'],d['endTick']],
            balances=d['balanceChanges'],scope=d['balanceChangesScope'],fees=d['fees'],annualAdaptation=d['annualAdaptation']))
    output['feeDependenceCases']=[]
    for run,d in diagnostic_rows.items():
        for tier,f in d['fees'].items():
            if f['feeReceiptWithNoMerchandiseSaleCompanies'] or f['positiveNetDespiteNegativeMerchandiseGrossCompanies']:
                output['feeDependenceCases'].append(dict(id=run,tier=tier,window=[d['startTick'],d['endTick']],**f))
    output['feeDependenceScope']='Counts refer to each run/tier observation window, not unique people or independent replications across runs. Absence of observed cases does not negate the independently verified split-fee lock-in counterexample.'
    for key in ('maxCompanyToleranceRatio','maxMoneyToleranceRatio','maxGoodsToleranceRatio',
                'priceFloorLineTicks','priceCeilingLineTicks'):
        observed = [(x['id'],x['invariants'][key]) for x in rows.values() if key in x['invariants']]
        output['invariants'][key] = dict(observedRuns=len(observed),totalRuns=len(rows),
            missingRuns=[x['id'] for x in rows.values() if key not in x['invariants']],
            maximum=max(v for _,v in observed),worstRun=max(observed,key=lambda x:x[1])[0])
    output['invariants']['gateFailures']=[x['id'] for x in rows.values() if x.get('invariantGate') is False]
    if baseline_replay_verification is not None:
        proof = json.loads(Path(baseline_replay_verification).read_text())
        expected = (root/'20261011-baseline-137-two-generations').resolve()
        if proof['status'] != 'pass' or proof['differences'] or Path(proof['before']).resolve() != expected:
            raise ValueError('Baseline supplementary measurement requires a passing exact replay proof')
        if proof['window'] != [1, 14400]:
            raise ValueError('Baseline replay must cover the complete preserved trajectory')
        output['invariants']['baselineSupplement'] = dict(
            verification=str(Path(baseline_replay_verification).resolve()),
            replay=proof['after'], exactProductTicks=proof['productTicks'],
            gate=proof['verifiedReplayInvariantGate'], measurements=proof['verifiedReplayInvariants'],
            note='Additional counters from a separately verified identical trajectory. The original manifest lacks them; observedRuns above counts direct records only.')
    plan=(json.loads((root/'mature-benchmark-plan.json').read_text())+
          json.loads((root/'adverse-benchmark-plan.json').read_text()))
    for job in plan:
        m=json.loads((root/job['id']/'manifest.json').read_text())
        if m['status']!='complete':raise ValueError('mature benchmark incomplete: '+job['id'])
        output['performance'].append(dict(**job,fullObservedTick=m['fullObservedTick'],warmTick=m['warmTick'],
            recording=m['recording'],publish=m['publish'],encoding=m['encoding'],firstTickMs=m['firstTickMs'],
            initializationMs=m['initializationMs'],peakRSSBytes=m['peakRSSBytes'],invariantGate=m['invariantGate']))
    profiles={x['id']:x for x in output['performance']}
    output['performanceGates']=[]
    for label,base,candidate in (
        ('ordinary startup','20261011-final-startup-profile-baseline-137','20261011-final-startup-profile-market-137'),
        ('initial fees x10','20261011-adverse-profile-baseline-137','20261011-adverse-profile-market-137'),
        ('cash-starved empty downstream stock','20261012-adverse-stock-cash-profile-baseline-137','20261012-adverse-stock-cash-profile-market-137'),
        ('mature repetition 1','20261011-mature-baseline-1','20261011-mature-market-1'),
        ('mature repetition 2','20261011-mature-baseline-2','20261011-mature-market-2')):
        b,c=profiles[base],profiles[candidate]
        med=c['fullObservedTick']['medianMs'];tail=c['fullObservedTick']['p95Ms']
        med_ratio=med/b['fullObservedTick']['medianMs'];tail_ratio=tail/b['fullObservedTick']['p95Ms']
        memory_limit=2*b['peakRSSBytes']+256*1024**2
        output['performanceGates'].append(dict(window=label,baseline=base,candidate=candidate,
            medianRatio=med_ratio,p95Ratio=tail_ratio,medianAtMostTwiceBaseline=med_ratio<=2,
            p95AtMostTwoPointFiveBaseline=tail_ratio<=2.5,medianAtMost500ms=med<=500,
            candidatePeakRSSBytes=c['peakRSSBytes'],memoryLimitBytes=memory_limit,
            memoryWithinBudget=c['peakRSSBytes']<=memory_limit))
    output['scope']='Every ratio uses its declared observation window. Three held-out seeds are short-run replication, not held-out complete-generation validation. Concurrent campaign timings are excluded from performance acceptance.'
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--study',type=Path,required=True)
    p.add_argument('--diagnostics',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline-replay-verification',type=Path)
    a=p.parse_args();result=compare(a.root,a.study,a.diagnostics,a.baseline_replay_verification)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(ablations=len(result['ablations']),recoveries=len(result['recovery']),output=str(a.output))))


if __name__=='__main__':main()
