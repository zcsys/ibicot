"""Independent structural, ledger, decision and decimal-oracle balance audit.
Run against an immutable QA workspace. Writes new evidence only.
"""
from pathlib import Path
from decimal import Decimal, localcontext, ROUND_FLOOR
from functools import cmp_to_key
from collections import Counter
import argparse, json, hashlib, math

p=argparse.ArgumentParser();p.add_argument('workspace');p.add_argument('output');a=p.parse_args();W=Path(a.workspace)
def load(rel):return json.loads((W/rel).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
b=load('release/balance/long-horizon-v4-policies.json');s=load('release/balance/supplemental-v2.json');checks=0

def check(ok, label):
 global checks
 checks+=1
 if not ok: raise AssertionError(label)

check(b['status']==s['status']=='complete','complete matrices')
check(len(b['policies'])==b['completed_cases']==94,'94 baseline rows')
check(len(s['trajectories'])==s['completed_trajectories']==90,'90 supplemental rows')
for report,count in [(b,100),(s,104)]:
 check(len(report['source_sha256'])==count,'input count')
 check(hashlib.sha256(json.dumps(report['source_sha256'],separators=(',',':')).encode()).hexdigest()==report['source_digest'],'ordered source digest')
 for rel,h in report['source_sha256'].items(): check(sha((W/'game/simulation'/rel).resolve())==h,'pinned source '+rel)

bonuses=['none','requiredCalibrationsOnly','allFocus','focusAndFreeSupport','focusAndAdSupportFixture'];resets=['atVisits','hourlyAutomatic']
base_grid=set()
for days in [30,90]:
 for visits in [1,3,6]:
  base_grid.update(f'{days}/{visits}/{bo}/{re}/bestPayback/allReady/0' for bo in bonuses for re in resets)
  base_grid.update(f'{days}/{visits}/requiredCalibrationsOnly/atVisits/{buy}/allReady/0' for buy in ['lowestTierFirst','highestTierFirst'])
  base_grid.update(f'{days}/{visits}/requiredCalibrationsOnly/atVisits/bestPayback/{co}/0' for co in ['surveysOnly','oneReadyPerVisit','pursueWithSeason'])
base_grid.update(f'90/3/requiredCalibrationsOnly/atVisits/bestPayback/allReady/{h}' for h in [24,48,72,120])
supp_grid={f'reset/{d}/{v}/{r}' for d in [30,90] for v in [1,3,6] for r in ['fixed-10-charts','fixed-100-charts','multiplier-20-percent','forecast-1h-output-1percent-margin','forecast-8h-output-1percent-margin','forecast-24h-output-1percent-margin']}
supp_grid.update(f'notes/{d}/{seed}/{order}/{co}' for d in [30,90] for seed in ['seed-a','seed-b','seed-c'] for order in ['campaignFirst','plansFirst','decorationsFirst'] for co in ['surveysOnly','oneReadyPerVisit','pursueWithSeason'])
check({r['case_id'] for r in b['policies']}==base_grid,'complete unique baseline grid')
check({r['case_id'] for r in s['trajectories']}==supp_grid,'complete unique supplemental grid')

conserved=[];txcount=0;decision_counts=Counter();recoveries=Counter();censored=[];samples=0;lowbest=0;positive=0;max_relative=Decimal(0)
for report,rows in [(b,b['policies']),(s,s['trajectories'])]:
 for r in rows:
  case=r['case_id'];h=r['horizon_days']*86400
  check(r['elapsed_seconds']==h,case+' exact horizon')
  check(int(r['notes_earned'])==int(r['notes_from_surveys'])+int(r['notes_from_contracts']),case+' source ledger')
  sinks=sum(int(r.get(k,0)) for k in ['notes_spent_dossiers','notes_spent_plans','notes_spent_decorations'])
  check(int(r['notes_earned'])==int(r['notes_unspent'])+sinks,case+' sink conservation')
  check(int(r['notes_from_contracts'])==r['contracts_claimed']*10,case+' daily reward20?')
  check(int(r['notes_from_surveys'])%10==0,case+' survey denomination')
  check(int(r['notes_spent_dossiers'])%100==0 and int(r['notes_spent_dossiers'])<=1200,case+' dossier cap')
  check(r['actual_visits']==r['horizon_days']*r['visits_per_day']-r['break_hours']*r['visits_per_day']//24,case+' visit schedule')
  if r['bonus_policy']=='none': check(r['focus_charges_used']==0 and r['free_support_tokens_used']==0 and r['chapters_completed']==2,case+' no bonus gate')
  if r['bonus_policy']=='requiredCalibrationsOnly':check(r['focus_charges_used']==3 and r['free_support_tokens_used']==0,case+' required only gate')
  if r['contract_policy']=='surveysOnly':check(r['contracts_claimed']==0 and int(r['notes_from_contracts'])==0,case+' surveys only')
  if r['contract_policy']=='oneReadyPerVisit':check(r['contracts_claimed']<=r['actual_visits'],case+' one claim cap')
  check(r['chapters_completed']==len(r['chapter_seconds_upper_bounds']),case+' chapter ledger')
  check(set(r['dossiers_completed'])==set(r['challenge_seconds_upper_bounds']),case+' dossier ledger')
  for field in ['chapter_seconds_upper_bounds','challenge_seconds_upper_bounds']:
   check(all(0<=t<=h for t in r[field].values()),case+' no completion after censor')
  for field in ['first_reset_seconds_upper_bound','full_note_budget_seconds_upper_bound','full_collection_affordable_seconds_upper_bound','all_sinks_purchased_seconds_upper_bound']:
   if field in r:check(r[field] is None or 0<=r[field]<=h,case+' timed bound '+field)
  for cp in r['checkpoints_at_last_visit'].values():check(cp['elapsed_seconds']<=h,case+' last visit is not final instant')
  conserved.append(case)
  if report is not s:continue
  check(r['notes_conserved'] is True,case+' reported conservation')
  purchases=r['note_purchases'];check(len({t['id'] for t in purchases})==len(purchases),case+' no duplicate debit');check(sum(int(t['cost_notes']) for t in purchases)==sinks,case+' transaction sum')
  mandatory=[1,5,9,2,6,10];optional=[3,7,11,4,8,12]
  dossiers=lambda values:[f'challenge.{i:02}' for i in values]
  plans=[f'plan.extra.{i}' for i in range(1,6)];decor=[f'cosmetic.core.decoration.{i:02}' for i in range(1,7)]
  order={'campaignFirst':dossiers(mandatory+optional)+plans+decor,'plansFirst':plans+dossiers(mandatory)+decor+dossiers(optional),'decorationsFirst':decor+plans+dossiers(mandatory+optional)}[r['sink_order']]
  check([t['id'] for t in purchases]==order[:len(purchases)],case+' strict wishlist prefix')
  cumulative=0;prior=0;earned_at_purchase=0
  for t in purchases:
   cost=100 if t['id'].startswith('challenge.') else 50
   check(int(t['cost_notes'])==cost,case+' actual sink cost');check(prior<=t['elapsed_seconds']<=h,case+' monotonic debit time');prior=t['elapsed_seconds'];cumulative+=cost
   earning=cumulative+int(t['notes_after']);check(0<=int(t['notes_after']) and earned_at_purchase<=earning<=int(r['notes_earned']),case+' no debit underflow/invented income');earned_at_purchase=earning;txcount+=1
  check(sum(t['id'].startswith('plan.') for t in purchases)==r['plan_slots_bought'] and int(r['notes_spent_plans'])==r['plan_slots_bought']*50,case+' real plan ledger')
  check(sum(t['id'].startswith('cosmetic.') for t in purchases)==r['decorations_bought'] and int(r['notes_spent_decorations'])==r['decorations_bought']*50,case+' real decoration ledger')
  check((r['all_sinks_purchased_seconds_upper_bound'] is not None)==(len(purchases)==23),case+' purchase censor completeness')
  if len(purchases)==23:check(r['all_sinks_purchased_seconds_upper_bound']==purchases[-1]['elapsed_seconds'] and sinks==1750,case+' complete actual collection')
  if r['group']=='notes' and r['horizon_days']==90:check(len(purchases)==23 and len(r['dossiers_completed'])==12,case+' long complete collection')
  if r['chapters_completed']<6:censored.append(case)
  check(sum(d['reset'] for d in r['reset_decisions'])==r['recharts'],case+' reset ledger count')
  last_reset=None
  for d in r['reset_decisions']:
   reason=d['reason'];decision_counts[reason]+=1
   check(0<=d['elapsed_seconds']<=h,case+' decision horizon')
   if d['reset'] and last_reset is not None:check(d['elapsed_seconds']-last_reset>=600,case+' minimum reset run')
   if d['reset']:last_reset=d['elapsed_seconds']
   if reason=='fixed_horizon_new_radiance':check(d['reset']==(int(d['reset_gain_micros'])*100>int(d['retained_gain_micros'])*101),case+' strict forecast objective')
   elif reason=='permanent_multiplier_gain':check(d['reset']==(int(d['after_multiplier_raw'])*100>=int(d['before_multiplier_raw'])*120),case+' actual multiplier gain')
   elif reason=='fixed_additional_charts':check(d['reset']==(int(d['additional_charts'])>=int(r['reset_policy'].split('-')[1])),case+' fixed additional award')
   elif reason=='shared_10_minute_minimum_run':check(not d['reset'],case+' early reset denied')
  records=r['reconstruction_observations'];check(len(records)==r['recharts'],case+' all resets resolved or censored')
  reset_times={d['elapsed_seconds'] for d in r['reset_decisions'] if d['reset']}
  check({o['reset_at_seconds'] for o in records}==reset_times,case+' unique reconstruction starts')
  for o in records:
   if 'recovered_at_seconds_upper_bound' in o:
    check(o['recovery_seconds_upper_bound']==o['recovered_at_seconds_upper_bound']-o['reset_at_seconds'] and o['reset_at_seconds']<=o['recovered_at_seconds_upper_bound']<=h,case+' recovery bounds');recoveries['observed']+=1
   else:check(o.get('superseded_without_observed_recovery') is True,case+' explicit supersession');recoveries['superseded']+=1
  check([sum(v[i] for v in r['purchases_by_elapsed_period'].values()) for i in range(5)]==r['purchase_tier_counts'],case+' tier purchase period sum')
  for m in r['marginal_samples']:
   samples+=1;rows=m['rows'];check(len(rows)==5,'five marginal tiers');check([t['tier'] for t in rows]==[1,2,3,4,5],'tiers ordered')
   ranked=sorted(rows,key=cmp_to_key(lambda x,y:(int(y['total_gain_raw'])*int(x['cost_micros'])>int(x['total_gain_raw'])*int(y['cost_micros']))-(int(y['total_gain_raw'])*int(x['cost_micros'])<int(x['total_gain_raw'])*int(y['cost_micros']))))
   check(m['efficiency_ranking']==[t['tier'] for t in ranked],'exact ratio ranking');lowbest+=m['efficiency_ranking'][0] in [1,2]
   n=m['counts'];charts=int(m['charts']);scale=10**24;prestige=scale+math.isqrt(charts*scale*scale//10)
   def decimal_rates(counts):
    with localcontext() as ctx:
     ctx.prec=90
     x=(Decimal(25+counts[0])/25).ln()/Decimal(2).ln();y=(Decimal(25+counts[1])/25).ln()/Decimal(2).ln()
     syn=[Decimal(1)]*3+[1+x*Decimal('.20')+y*Decimal('.10'),1+x*Decimal('.10')+y*Decimal('.25')]
     return [Decimal(counts[i]*20**i*2**min(counts[i]//25,4))*syn[i]*prestige for i in range(5)]
   original=decimal_rates(n)
   for t in rows:
    tier=t['tier']-1;owned=n[tier]
    def cumulative(c):
     num=30*20**tier*10**6*25*(28**c-25**c);den=3*25**c;return (num+den-1)//den
    price=cumulative(owned+1)-cumulative(owned)
    check(price==int(t['cost_micros']),'independent rational telescoping price')
    check(t['affordable']==(price<=int(m['wallet_micros'])),'affordability')
    direct,cross,total=[int(t[k]) for k in ['direct_gain_raw','cross_tier_gain_raw','total_gain_raw']]
    check(total==direct+cross,'direct/external sum')
    if tier<2:check(cross>0,'positive low-tier externality');positive+=1
    else:check(cross==0,'no reverse undocumented externality')
    den=total*10**6;check(int(t['payback_seconds_ceiling'])==(price*scale+den-1)//den,'exact payback ceiling')
    nn=n.copy();nn[tier]+=1;after=decimal_rates(nn)
    with localcontext() as ctx:
     ctx.prec=80
     targets=[after[tier]-original[tier],sum(after)-sum(original)]
     for actual,expected in zip([direct,total],targets):
      err=abs(Decimal(actual)-expected)/max(abs(expected),Decimal(1));max_relative=max(max_relative,err);check(err<Decimal('1e-20'),'independent high-precision mathematical rate tolerance')

# Compare all persisted summary fields and checkpoints, excluding only route
# labels, measured host runtimes, and serialized byte count (receipt text length).
def econ(v):
 if isinstance(v,dict):return {k:econ(x) for k,x in v.items() if k not in ['case_id','bonus_policy','runtime_milliseconds','main_serialized_bytes']}
 if isinstance(v,list):return [econ(x) for x in v]
 return v
by={r['case_id']:r for r in b['policies']};pairs=[]
for key,row in by.items():
 if row['bonus_policy']!='focusAndFreeSupport':continue
 other=key.replace('focusAndFreeSupport','focusAndAdSupportFixture');check(econ(row)==econ(by[other]),'all-field free/ad fixture equality '+key);pairs.append([key,other])
check(len(pairs)==12,'twelve pairs')
for item in s['season_isolation']:
 check(all(item[k] for k in ['main_profiles_differ','main_profiles_unchanged','paired_event_states_identical','main_power_injection_rejected']),'isolation claims')
 obs={v['day']:v for v in item['observations']};check(obs[28]['lifetime_micros']==obs[29]['lifetime_micros']==obs[30]['lifetime_micros'],'paused archive no production');check(int(item['archive_resume_day31_lifetime_micros'])>int(obs[30]['lifetime_micros']),'resumed archive produces')

summary=load('release/balance/supplemental-v2-summary.json');check(summary['raw_report_sha256']==sha(W/'release/balance/supplemental-v2.json'),'summary raw digest')
check(samples==225 and lowbest==41 and positive==450,'reported numerical totals')
for day in [30,90]:
 for visits in [1,3,6]:
  rows=[r for r in s['trajectories'] if r['group']=='reset' and r['horizon_days']==day and r['visits_per_day']==visits]
  winner=max(rows,key=lambda r:int(r['lifetime_r_micros']))
  check(winner['reset_policy']==('forecast-24h-output-1percent-margin' if day==30 else 'multiplier-20-percent'),'reported matched lifetime winner')
result={'status':'pass','assertions':checks,'baseline_cases':94,'supplemental_cases':90,'conserved_ledgers':len(conserved),'actual_note_transactions':txcount,'full_summary_free_ad_fixture_pairs':pairs,'decisions':dict(decision_counts),'reconstruction':dict(recoveries),'unreported_final_reconstruction_censoring':0,'marginal_states':samples,'independent_decimal_rate_max_relative_error':str(max_relative),'low_tier_top_rank':lowbest,'positive_low_tier_externalities':positive,'ending_unreached_at_horizon':censored,'limits':['Virtual reachable policies do not establish human 15-30-day pacing or retention.','New/veteran season test is structural isolation: main profiles are deliberately not inputs.','Forecast compares new income over fixed full-rate horizon, without future claims or additional resets.','Ad receipts are synthetic successful fixtures only.','Reconstruction is sampled recovery, not exact first passage time.']}
Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['full_summary_free_ad_fixture_pairs','ending_unreached_at_horizon','limits']},indent=2))
