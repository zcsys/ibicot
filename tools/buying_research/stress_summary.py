"""Compare transient phases to same-policy controls without conflating shocks."""
import argparse
import json
from pathlib import Path

from .analyze import analyze, ratio


PHASES = (('before', 1, 180), ('intervention', 181, 360),
          ('first180After', 361, 540), ('finalYear', 721, 1080))
CONTROLS = dict(baseline='20261011-baseline-137-two-generations',
                market='20261011-control-market-137',
                local='20261011-recovery-none-local-137',
                hybrid='20261011-recovery-none-hybrid-137')


def summarize(root, plan, partial=False):
    results, pending, cache = [], [], {}
    for job in plan:
        scenario = job.get('scenario', 'none')
        if scenario == 'none':
            continue
        control = CONTROLS[job['treatment']]
        for run in (job['id'], control):
            path = root/run/'manifest.json'
            if not path.exists() or json.loads(path.read_text())['status'] != 'complete':
                pending.append(dict(id=job['id'], waitingFor=run))
                break
        else:
            phases = []
            for label, start, end in PHASES:
                key = (control, start, end)
                if key not in cache:
                    cache[key] = analyze(root/control, start, end)
                base = {g['group']: g for g in cache[key]['groups']}
                actual = analyze(root/job['id'], start, end)
                groups = []
                for g in actual['groups']:
                    b = base[g['group']]; length = end-start+1
                    groups.append(dict(group=g['group'], companies=g['companyDenominator'],
                        soldPerTick=g['sold']/length, retailPerTick=g['retailUnits']/length,
                        retailRelativeToControl=ratio(g['retailUnits'], b['retailUnits']),
                        netPerTick=g['netEarnings']/length, controlNetPerTick=b['netEarnings']/length,
                        netPerCompanyTick=g['earningsPerCompanyTick'], netMargin=g['netMargin'],
                        realizedPrice=g['realizedPrice'], utilization=g['utilization'],
                        finishedCoverage=g['finishedCoverage']))
                phases.append(dict(label=label, window=[start,end], groups=groups,
                    companyDistributions=actual['companyDistributions']))
            results.append(dict(**job, control=control, phases=phases,
                temporaryIntervention=scenario in ('demand-up','demand-down','raw-outage','supplier-outage'),
                interpretation=('Permanent initial-condition change; phase labels are calendar windows, not shock removal.'
                    if scenario in ('small-cash','large-fees','asymmetric') else
                    'One-time endogenous-history reset at tick 361; no physical shutdown or asset reset.'
                    if scenario=='reentry' else
                    'One-time quote jump at tick 181; price learning continues and no price restoration is forced.'
                    if scenario=='quote-shock' else
                    'Temporary intervention at ticks 181–360, restored before tick 361.')))
    if pending and not partial:
        raise ValueError('Stress study or required controls incomplete: '+str(pending))
    return dict(status='partial' if pending else 'complete', runs=results, pending=pending,
        caveat='Ratios compare the same policy/seed/calendar window. Baseline and R1 demand-loss denominators differ, so comparisons use actual retail transactions and posted accounts. Company distributions are available only for complete recorded 360-tick company intervals; no 180-tick company history is invented.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan',type=Path);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--partial',action='store_true')
    a=p.parse_args();result=summarize(a.root,json.loads(a.plan.read_text()),a.partial)
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=result['status'],runs=len(result['runs']),pending=len(result['pending']))))


if __name__=='__main__':
    main()
