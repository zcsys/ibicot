#!/usr/bin/env python3
"""Derive readable tables from the immutable production-engine experiment.

Run from repository root with Python3. Decimal arithmetic is presentation only;
all gameplay quantities and choices were computed by the exact Dart engine.
"""
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path

BASE = Path(__file__).resolve().parent
raw_path = BASE / 'supplemental-v2.json'
x = json.loads(raw_path.read_text())
if x['status'] != 'complete' or not x['sources_unchanged_through_run']:
    raise SystemExit('Refusing to summarize incomplete or changed-source run')
rows = x['trajectories']
assert len(rows) == x['planned_trajectories'] == 90
assert len({r['case_id'] for r in rows}) == 90
assert all(r['notes_conserved'] for r in rows)

def day(seconds):
    return None if seconds is None else round(seconds / 86400, 3)

def ranges(values):
    present = [v for v in values if v is not None]
    return {'min': min(present) if present else None,
            'max': max(present) if present else None,
            'unreached': len(values) - len(present), 'cases': len(values)}

def range_text(r):
    if r['min'] is None:
        return 'Unreached'
    text = f"{r['min']:.2f}–{r['max']:.2f}"
    if r['unreached']:
        text += f" ({r['unreached']} unreached)"
    return text

reset = []
for horizon in (30, 90):
    for visits in (1, 3, 6):
        selected = [r for r in rows if r['group'] == 'reset' and
                    r['horizon_days'] == horizon and r['visits_per_day'] == visits]
        best = max(int(r['lifetime_r_micros']) for r in selected)
        for r in selected:
            recoveries = [n['recovery_seconds_upper_bound'] for n in
                          r['reconstruction_observations'] if
                          'recovery_seconds_upper_bound' in n]
            with localcontext() as ctx:
                ctx.prec = 30
                relative = str((Decimal(int(r['lifetime_r_micros'])) /
                                Decimal(best)).quantize(Decimal('0.0001')))
            reset.append({
                'days': horizon, 'visits': visits, 'policy': r['reset_policy'],
                'recharts': r['recharts'], 'charts': r['charts'],
                'lifetime_micros': r['lifetime_r_micros'],
                'lifetime_fraction_of_best_in_matched_group': relative,
                'ending_day_upper_bound': day(r['chapter_seconds_upper_bounds'].get('chapter.06')),
                'maximum_observed_reconstruction_seconds_upper_bound': max(recoveries, default=None),
                'unrecovered_before_next_reset': sum(n.get('superseded_without_observed_recovery', False)
                                                     for n in r['reconstruction_observations']),
            })

note_groups = defaultdict(list)
for r in rows:
    if r['group'] == 'notes':
        note_groups[(r['horizon_days'], r['contract_policy'], r['sink_order'])].append(r)
notes = []
for (horizon, contract, order), group in sorted(note_groups.items()):
    notes.append({
        'days': horizon, 'contracts': contract, 'sink_order': order,
        'notes_earned': ranges([int(r['notes_earned']) for r in group]),
        'notes_spent': ranges([int(r['notes_spent_dossiers']) + int(r['notes_spent_plans']) +
                              int(r['notes_spent_decorations']) for r in group]),
        'ending_days_upper_bound': ranges([day(r['chapter_seconds_upper_bounds'].get('chapter.06'))
                                          for r in group]),
        'all_sinks_purchased_days_upper_bound': ranges([day(r['all_sinks_purchased_seconds_upper_bound'])
                                                       for r in group]),
        'full_dossier_completion_cases': sum(len(r['dossiers_completed']) == 12 for r in group),
    })

marginals = []
for r in rows:
    for sample in r['marginal_samples']:
        marginals.append((r['case_id'], sample))
low_tier_best = sum(s['efficiency_ranking'][0] in (1, 2) for _, s in marginals)
low_tier_cross = []
for _, s in marginals:
    for tier in s['rows'][:2]:
        total, cross = int(tier['total_gain_raw']), int(tier['cross_tier_gain_raw'])
        low_tier_cross.append(Decimal(cross) / Decimal(total) if total else Decimal(0))
late_rows = [r for r in rows if r['horizon_days'] == 90]
low_tier = {
    'sampled_reachable_states': len(marginals),
    'sampled_states_with_low_tier_best_one_unit_efficiency': low_tier_best,
    'low_tier_externality_positive_samples': sum(v > 0 for v in low_tier_cross),
    'low_tier_externality_sample_denominator': len(low_tier_cross),
    'cross_tier_share_of_low_tier_gain_min': str(min(low_tier_cross)),
    'cross_tier_share_of_low_tier_gain_max': str(max(low_tier_cross)),
    'ninety_day_cases': len(late_rows),
    'ninety_day_cases_buying_both_low_tiers_after_day30': sum(
        min(r['purchases_by_elapsed_period']['days30plus'][:2]) > 0 for r in late_rows),
    'caveat': 'After-day30 purchases include reset reconstruction. Exact one-unit efficiency is not a proof of an optimal multi-purchase policy.',
}
summary = {
    'raw_report_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    'analysis_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'source_digest': x['source_digest'], 'source_archive': x['source_archive'],
    'trajectories': len(rows), 'reset_comparisons': reset,
    'note_spending_comparisons': notes, 'low_tier_relevance': low_tier,
    'season_isolation': x['season_isolation'],
    'actual_engine_seconds': sum(r['runtime_milliseconds'] for r in rows) / 1000,
    'acceptance': 'Supplemental author evidence only; no original package/scope/beta gate accepted.',
}
(BASE / 'supplemental-v2-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
lines = [
    '# Supplemental balance experiments — author evidence', '',
    f"Source digest: `{x['source_digest']}`. The complete report contains **90 virtual 30/90-day trajectories**, 2 paired season checks and {len(marginals)} sampled reachable fleet states. No economic constants were changed. Original initial/v2/v3 reports, interrupted supplementalv1, and `policy_run.dart` were preserved. Those cache-era scenario outputs are invalidated by the shared fleet-rate cache defect. This run uses the repaired production core; see the independent scenario-cache regression and invalidation note.", '',
    'This supplements roadmap §7 and packages M5-05/M6-03, informing S07/S18/S25/S29/S33/S44/S34. It does not accept those packages: observed novice behavior, actual learning/decision burden, human pacing, real season observation and D30 retention remain unavailable. Independent review remains separate from this author report.', '',
    'The tested winner depends on horizon: the 24-hour forecast has the highest lifetime income in each 30-day cadence group, while the 20% multiplier-gain rule leads each 90-day group. At three visits/day over 90 days, that rule makes 18 resets versus 271 for the fixed 10-Chart rule, which earns 84.56% as much lifetime Radiance. These bounded comparisons support evaluating advice around multiplier gain and forecast horizon; they do not establish a universal reset optimum.', '',
    'Optional spending order matters more to the ending than the full collection total suggests. With one daily visit and Surveys only, campaign-first reaches the ending by day 20.17; plans-first by day 29.17; decorations-first by day 39.17. Buying all 23 items takes 29–30 days when pursuing actual contracts, 44 days with at most one contract per visit, and 59 days with Surveys only. These are virtual purchase/evaluation bounds, excluding human learning. The model should therefore keep optional spending clearly distinguishable from mandatory campaign costs; no prices are changed here.', '',
    '## Reset comparisons', '',
    'All strategies share the first 10-Chart reset, the ten-minute minimum run, purchase policy, visit cadence and minimal three required calibrations. Fixed policies request 10 or 100 additional Charts. The multiplier policy requests a 20% increase in actual permanent output multiplier. Forecast policies compare real-engine immutable retain/reset branches over 1/8/24 hours and reset only when newly generated Radiance exceeds the retained branch by more than 1%. They include rebuilding cost and retained-boost expiry, with no hypothetical future bonuses, claims or further resets. Decisions happen at matching action opportunities, not continuously between visits.', '',
    'The ratio below is lifetime income divided by the best tested strategy at the same horizon and cadence. It is not a proof of a globally optimal policy. Reconstruction observations are upper bounds at evaluation boundaries (up to four-hour offline chunks); they are not exact recovery times.', '',
    '| Days | Visits/day | Reset strategy | Recharts | Lifetime / matched best | Ending day ≤ |',
    '|---:|---:|---|---:|---:|---:|',
]
for r in reset:
    lines.append(f"| {r['days']} | {r['visits']} | {r['policy']} | {r['recharts']} | {r['lifetime_fraction_of_best_in_matched_group']} | {r['ending_day_upper_bound']} |")
lines += ['', '## Real Note spending', '',
    'Each purchase invokes production transitions: 12 dossiers × 100 Notes, five extra plans × 50 Notes, and six decorations × 50 Notes. The simulation spends the full 1,750 Notes when affordable; it does not merely reserve an arithmetic budget. Orders are strict wish lists: campaign-first buys six mandatory and then six optional dossiers before plans/decorations; plans-first buys plans, mandatory dossiers, decorations and optional dossiers; decorations-first buys decorations, plans and all dossiers. An unavailable first remaining item waits. Dossier execution is sequential. Extra plan capacity is bought but does not silently improve the chosen automation policy.', '',
    'Each row spans three paired context tuples: seed-a / UTC+00:00 / midnight UTC start; seed-b / UTC+03:00 / 23:55 UTC start; seed-c / UTC−07:00 / 05:30 UTC start. These varied tuples test robustness; they do not isolate causal seed, offset and phase effects. All Note runs use one visit/day. Partial contracts claim at most one per visit; pursuing contracts uses actual reflections and seasonal alternatives, with no invented completion or 60-Note/day assumption.', '',
    '| Horizon | Contract policy | Spending order | Ending day ≤ range | All 23 purchases day ≤ range |',
    '|---:|---|---|---:|---:|',
]
for r in notes:
    lines.append(f"| {r['days']} | {r['contracts']} | {r['sink_order']} | {range_text(r['ending_days_upper_bound'])} | {range_text(r['all_sinks_purchased_days_upper_bound'])} |")
lines += ['', 'All trajectories conserve Notes: surveys + contract Notes = remaining Notes + all actual sinks. No economic reward was imported from challenge or seasonal fleets.', '',
    '## Low-tier relevance and isolation', '',
    f"The exact one-unit marginal ranking places Tier 1 or Tier 2 first in **{low_tier_best}/{len(marginals)}** sampled states. Cross-tier output contributes positively in **{low_tier['low_tier_externality_positive_samples']}/{len(low_tier_cross)}** low-tier marginal observations. Both low tiers are purchased after day 30 in **{low_tier['ninety_day_cases_buying_both_low_tiers_after_day30']}/{len(late_rows)}** long trajectories. Those purchases include reconstruction after resets; they alone do not prove interesting human choices. The raw report separates direct output from synergy externality and includes exact cost/rate integers and late purchase counts.", '',
    'New and reachable veteran profiles have byte-identical event states under matched continuous-online and daily-offline schedules through the 28-day end, paused archive and resumed day 31. Main profiles remain unchanged; injecting main Charts into the event fleet is rejected. Event initialization accepts no main-profile or paid-power input. This verifies engine separation, not actual account-service or UI identity binding.', '',
    '## Reproduction and limits', '',
    'From `game/simulation`: run `../../tool/dart analyze`, `../../tool/dart test`, compile `bin/run_supplemental.dart` with the project launcher, then execute the compiled binary from that directory. The runner refuses to overwrite an existing report; `--resume` requires an identical source digest. Every pinned input is copied into the content-addressed source archive and unchanged input hashes are checked after the full run. From repository root, run `python3 release/balance/summarize_supplemental_v2.py` to regenerate these tables.', '',
    'Author checks cover eight supplemental tests plus six unchanged v3 harness tests. The shared decoration extraction has independent 49/50-Note boundary, duplicate, invalid-ID and unrelated-state conservation checks here. Model tests, exact trajectories and host execution do not replace human onboarding comprehension, D30 cohorts, physical-device performance, real store/ad delivery, sustained live operations or a mature seasonal study. No product acceptance threshold was reduced.', '',
    f"Raw report SHA256: `{summary['raw_report_sha256']}`.",
]
(BASE / 'SUPPLEMENTAL_V2_REVIEW.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'trajectories':len(rows),'source_digest':x['source_digest'],
                 'low_tier_relevance':low_tier},indent=2))
