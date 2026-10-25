#!/usr/bin/env python3
"""Audit corrected v4 against historical v3 and its ethical bonus pairs."""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parent
before=json.loads((base/'long-horizon-v3-policies.json').read_text())
after=json.loads((base/'long-horizon-v4-policies.json').read_text())
assert before['status']==after['status']=='complete'
old={r['case_id']:r for r in before['policies']}
new={r['case_id']:r for r in after['policies']}
assert old.keys()==new.keys() and len(new)==94
keys=['lifetime_r_micros','charts','counts','recharts','notes_earned',
      'chapters_completed','chapter_seconds_upper_bounds',
      'challenge_seconds_upper_bounds','dossiers_completed',
      'pass_level','season_lifetime_micros']
changed=[{'case_id':key,'changed_fields':[field for field in keys
          if old[key][field]!=new[key][field]]} for key in sorted(new)]
changed=[row for row in changed if row['changed_fields']]
route_pairs=[]
for key,r in new.items():
 if r['bonus_policy']!='focusAndFreeSupport':continue
 ad=new[key.replace('focusAndFreeSupport','focusAndAdSupportFixture')]
 fields=keys+['focus_charges_used','free_support_tokens_used','contracts_claimed']
 different=[field for field in fields if r[field]!=ad[field]]
 route_pairs.append({'free_case':key,'ad_fixture_case':ad['case_id'],
                     'economic_differences':different})
assert len(route_pairs)==12 and all(not row['economic_differences'] for row in route_pairs)
conservation=[]
for key,r in new.items():
 assert int(r['notes_earned'])==int(r['notes_unspent'])+int(r['notes_spent_dossiers'])
 assert int(r['notes_earned'])==int(r['notes_from_surveys'])+int(r['notes_from_contracts'])
 conservation.append(key)
fields_count={field:sum(field in row['changed_fields'] for row in changed) for field in keys}
result={'original_matrix':'long-horizon-v3-policies.json',
        'corrected_matrix':'long-horizon-v4-policies.json',
        'original_is_invalidated_scenario_evidence':True,
        'corrected_source_digest':after['source_digest'],
        'corrected_report_sha256':hashlib.sha256((base/'long-horizon-v4-policies.json').read_bytes()).hexdigest(),
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'cases':94,'changed_cases':len(changed),'changes_per_field':fields_count,
        'changes':changed,'bonus_route_pairs':route_pairs,
        'note_conservation_cases':len(conservation),
        'limitations':['Synthetic successful ad receipts establish mathematical route parity only.',
          'Changes relative to an invalidated run are a repair impact comparison, not a calibration target.',
          'No physical-device, actual player, live service or release acceptance is established.']}
(base/'corrected-v4-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['cases','changed_cases','changes_per_field','note_conservation_cases']},indent=2))
