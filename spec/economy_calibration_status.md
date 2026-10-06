# Economy calibration — resumed 4 October 2026

> ## Structural correction — Tier 2 opening equity (5 October 2026)
>
> The previous Tier 2 initialization endowed every firm with a **$300,000 shared
> factory** (`T2_FACTORY_CAPITAL`), giving each Tier 2 firm $302,500 opening
> equity — larger than a Tier 1 firm ($20,000/$80,000). That inverted the intended
> hierarchy. The governing principle is: **per company, Tier 0 > Tier 1 > Tier 2**
> (lower tiers far larger), while **in aggregate, Tier 2 > Tier 1 > Tier 0**
> because of company counts (61,950 / 1,000 / 20).
>
> The shared-factory concept has been **removed entirely**. Each Tier 2 firm now
> owns its routes outright at **$1,000 each** (`T2_ROUTE_SETUP`), plus $2,500
> working cash, for **$3,500–$6,500** opening equity (one to four routes).
> `T2_FACTORY_CAPITAL` is deleted from `engine/model.js`; a Tier 2 firm's
> equipment book is the sum of its routes' prices.
>
> **All prior calibration results that assumed $300k/$302.5k Tier 2 equity are
> superseded.** The fixed Tier 2 reference earnings target changes from
> $1.750579/tick to $0.020255–$0.037616/tick (one to four routes). New full-Age
> calibration runs are required; none has been launched yet.

The user resumed the full calibration from the 4 October transfer. **No economy
standard is selected or adopted.** The parameter search has converged to a
leading candidate (V20), which is now under full-Age validation. The original
V6 actual Ages failed return and fairness criteria; the new V13 ten-year
evidence also rejects its k=0 profile as a calibrated endpoint.

V13 passed all42 ordinary-default mechanical checks and all three full-population
opening pairs. Its three fresh ten-year trials then completed with native exit0.
The actual paired audit and independent review reconcile every company book and
all ten annual histories, but reveal a41–44% mono-versus-four-product final-firm
gain advantage,65–101 final firms without a sale in the final year, and3–19 with
five-year droughts. The controls had no such year-long endpoint droughts.
Tier averages remain nearly unchanged; raw percentage returns remain lower than
both downstream tiers. A mechanical or accounting pass is not acceptance.

The same-source k=0.35 diagnostic has now completed all three ten-year runs
and its independent full-history audit. It is also rejected: four-product
final firms gain15–23% more than single-product firms, endpoint one-year sales
droughts rise to686–733 firms, and the first-percentile gains deteriorate in
both downstream tiers. Accounting and all first-year equity identities pass.

V14 local surplus backtracking completed all three ten-year runs and passed
accounting and independent history checks. It is rejected: T2 mean gains fall
about 1.17–1.18% against controls; one-year drought still affects 653–686 firms,
and width, material and initial-direction disparities persist. T1 lower tails
improve, but the mixed economic result does not justify three extra memory
arrays. The simpler V13 k=0.35 source remains an experimental base only.

Two faster no-request responses were rejected before source integration.
Doubling downward step growth can cycle at zero profit in thin markets.
Halving a seller's own surplus avoids that deadlock but severely suppresses
profit under sparse rounded demand. The latter is a robustness counterexample,
not a claim that typical active full-economy sellers fail. The next isolated diagnostic, V15, changes only priceObservationTicks from
360 to90 on the unchanged V13 source. Its three fresh ten-year treatments
completed native0 against the V13 k=0.35 controls; the paired accounting/history
audit and independent saved-evidence arithmetic pass. V15 is rejected as a
standard: quarterly observation cuts Tier 2 one-year endpoint drought from
686–733 to 342–344 firms, five-year drought from 29–40 to 0–1, and Tier 1
drought to zero, and shrinks the four-vs-one-product gain gap from 15–23% to
about 3–6%. The same change lowers Tier 2 mean gain from about 2.07% to 1.91%
and its first-percentile gain in every seed, while Tier 0/Tier 1 gains rise,
widening the cross-tier spread. No new source, defaults or parameters are
adopted.

V16 canonical retail discovery completed all three ten-year runs and passed
accounting and independent saved-evidence arithmetic. It is a clean null
result: removing the global Tier 2 quote sort from bounded discovery moves
Tier 2 mean gain by at most 0.000004, leaves endpoint droughts (717/702/679
one-year), width fairness (0.86/0.81/0.90) and lower tails essentially
unchanged. The price-to-discovery coupling is not economically material, so
retail discovery ordering is ruled out as the cause of the persistent drought
and portfolio-width problems. The market-rule phase is exhausted; the remaining
levers are physical/demand parameters. V17 capacity one
([root disposition](../reports/v17-capacity-one-root-disposition.json)) reduces
the shared final factory capacity from 3 to 1 output unit per company per tick
on the unchanged V13 k=.35 source. It is a decisive Tier 2 improvement — final
utilization 19.9% to 56.9%, one-year drought 686–733 to 205–245 firms, width
gap 15–23% to 2–7% — but it shifts the return imbalance upstream: Tier 0 gain
falls about 7–14% and Tier 1 about 5–6% while Tier 1 drought worsens to 22–43.
Capacity two is the better physical baseline: utilization 19.9% to 29.5%,
one-year drought 686–733 to 433–500, width gap 15–23% to 6–11%, while Tier 0/Tier 1
returns are essentially unchanged and Tier 1 first-percentile gain improves about
17%. It is retained as the preferred physical candidate but not adopted.

V19 +10% tier2DemandFactor is the decisive magnitude lever: it raises every
tier (Tier 0 +16–20%, Tier 1 +20%, Tier 2 +10%), repairs the Tier 0 lag
(Tier 0 ≈ Tier 2), eliminates the Tier 1 drought (13/13/1 to 1/1/2) and about
doubles the Tier 1 first-percentile gain, but over-tilts Tier 1 (about 2.61%
versus 2.27% Tier 0 / 2.28% Tier 2).

V20 combines the two dominant levers — capacity two + 10% demand factor — and
composes them with positive interaction: utilization 32.3%, Tier 2 one-year
drought halved to 312–349, width gap 2–5%, Tier 0 lag repaired, Tier 2
first-percentile gain +22%. Its single remaining defect is the Tier 1 over-tilt
(about 10–16%).

V21 (+50% Tier 1 capacity) and V22 (+25%) test Tier 1 moderation and show a
monotonic tradeoff with no clean sweet spot: more Tier 1 capacity lowers
Tier 1 returns but raises Tier 1 droughts, collapses the Tier 1 lower tail and
depresses Tier 0. The Tier 1 over-tilt is therefore a structural bottleneck
rent that capacity cannot cleanly remove; it is accepted as explainable.

V20 ([candidate selection](../reports/v20-candidate-selection.json)) is now
selected as the candidate and is under full-Age validation: three fresh seeds
at 0x2A300 (172,800) ticks against the 1.9–2.1 Age equity-multiple target and
the repeated-cohort 10% tolerance. Disruption/recovery and coherent default
adoption remain to be completed after the Age readout. No candidate or defaults
have been adopted.

The user's explicit pricing condition applies to every market: buyers pursue
lower purchase costs and sellers pursue profitable selling prices independently.
Neither side may follow a shared optimum quote. Source review and permanent
buyer–seller separation tests cover that condition; the ordinary quick suite
now contains43 checks. No candidate or defaults have been adopted.

Use [the current record](../reports/calibration-current.json) for active work.
The [completed V16 analysis](../reports/v16-canonical-retail-discovery-outcome.json),
[independent saved arithmetic](../work/v16-saved-outcome-independent-arithmetic.json),
[economic readout](../reports/v16-canonical-retail-discovery-economic-readout.json)
and [root disposition](../reports/v16-canonical-retail-discovery-root-disposition.json)
bind the latest decision (V16 null result). The
[V17 capacity-one root selection](../reports/v17-capacity-one-root-selection.json)
begins parameter calibration. Full-Age validation, source-matched
disruption/recovery, parameter adoption and the coherent commit remain
unfinished.

## Historical state at the transfer

The requested work remains unfinished. No standard parameters have been adopted.
The three original experimental V6 producers completed **480 actual years /
172,800 ticks** with native exit zero, and their unchanged full-Age reader and
independent reviews are complete. Accounting passes; return/fairness targets
**fail/HOLD**. Calibration work has stopped for the requested handoff. The
[original handoff](economy_calibration_handoff.md) remains the historical stop
record. Use this file for the resumed work and
[validation protocol](calibration_validation.md) for evidence requirements.

Latest progress: the two older baseline jobs stopped cleanly for memory scheduling at **89,790** and **90,090 actual ticks**, with full states and partial-year accumulators [preserved](../reports/annual-v2-resource-stop-preserved-states.json). They remain unfinished. Their preserved 100-year states have independent reviews and persistent Tier 2
width gaps. Both full-population ten-year relative-switching trials completed.
The stronger retention policy worsens standalone opportunities and will not be
adopted. All 42 quick checks also pass for the copied pure-v6 clearing rule with ordinary
application defaults; its two fresh ten-year experiments completed with independent company audits. The combined annual company-history, sold-basis reporting and execution runtime is frozen and independently reviewed. The three fresh full-population experimental Age producers at seeds 12345, 24680 and 31415 completed **172,800 actual ticks / 480 years** with native exit zero (`705afc`, `db3ee0`, `1fc4ec`), bound by the [genuine completion and reader prelaunch](../reports/annual-v6-three-age-genuine-native-completion-and-actual-reader-prelaunch.json). All original producer sessions are closed. The unchanged prepared [full-Age analyzer completed with native exit zero](../reports/annual-v6-full-age-fairness-actual-native-handback.json) (`f20d71`, Root session 77471). Its provenance/accounting verdict is **PASS**, while the original all-tier return/fairness objective is **FAIL/HOLD**. The [independent full-path review](../reports/resumed-annual-v6-full-age-saved-evidence-independent-native-handback.json) and [market/physical review](../reports/resumed-annual-v6-full-age-market-physical-independent-readout-native-handback.json) are complete. All experiment, simulation and audit processes are closed; no selected standard or adopted defaults are established. Earlier incomplete progress observations remain historical below. The three fresh selected-source cost-shock treatments completed **3,600 actual ticks** with native exit zero, using the same three predeclared seeds and exact frozen source. Their [native completion binding](../reports/annual-v6-selected-disruption-completion-binding.json) and [completed paired analysis](../reports/annual-v6-selected-disruption-paired-analysis-native-handback.json) preserve all source, configuration, accounting and history checks. The controls came from [genuine ten-year snapshots](../reports/annual-v6-selected-disruption-preserved-controls-binding.json) of the corresponding candidate Age worlds. Their [passive exports completed with native exit zero](../reports/annual-v6-selected-control-export-revision2-native-binding.json), without extra simulation ticks, and the [independent actual-export audit](../reports/resumed-selected-v6-control-exports-native-audit-handback.json) passes every company record and all ten annual vectors. All four pre-shock annual company-equity vectors match exactly in each pair. The paired analysis also checks every final company and both cost-only action boundaries. The [independent actual economic and individual-effect review](../reports/resumed-selected-v6-disruption-independent-findings.json) completed with native exit zero across all three seeds. The [actual ten-year figure](../reports/resumed-annual-v6-selected-disruption-actual-ten-year-panels.png) shows persistent raw-price and Tier 1 profit residuals during the four recovery years; it makes no full-recovery or Age claim. The [full-Age analyzer preparation](../reports/calibration-full-age-fairness-preparation.json) requires all three actual 480-year histories and checks every company and all 657 opening cohorts, rather than extrapolating these ten-year controls. The [reviewed exporter revision](../reports/resumed-control-export-revision2-source-independent-review.json) checks equality of the complete decoded state. Earlier serialized-stream hash mismatches and the diagnostic attempts are preserved; serialized hashes remain diagnostic, and their exact differences are unexplained.

The earliest completed resumed experiments used annual-v1 and
[execution3 with an admin action ledger](../reports/calibration-protocol-annual-v1-execution3-admin-ledger.json).
That runtime and its instrument have an exact
[source archive](../reports/calibration-runtime-execution3-source.json).
A proven integer-allocation defect is corrected in
[annual-v2](../reports/calibration-protocol-annual-v2-integer-apportionment.json),
which passes all **39 quick checks**. Its two matched ten-year trials are complete;
parameter selection and actual Age validation remain unfinished.
Numeric ingredient lookups preserve every world-state value and transaction in
full-population parity trials, with an indicative 3.6–4.5% execution saving.
Manual machinery purchases now have immediate cumulative administrative sinks
and sequenced receipts. Tick transaction counters remain per actual tick, so
manual payments cannot disappear or be counted twice. Bot-only state parity
and admin cash/asset/restart regressions pass. All **36 quick checks pass** with
the execution3 source fingerprints. The old 32-check report and resumed
[36-check report](../reports/scarcity-aware-quality-execution3-36.json) are preserved
separately. The new [39-check report](../reports/scarcity-aware-quality-annual-v2-39.json)
records the corrected allocation and intervention regressions.
The expanded [42-check report](../reports/scarcity-aware-quality-annual-v2-42.json)
also passes strict cross-rule, drought-diagnostic and paired-disruption guards,
alongside the fractional-cent UI changes. Runtime, UI and suite fingerprints are
recorded; frozen experiment protocols retain their original launch records.

## Completed resumed evidence

The matched cost-shock and control runs both completed **0xE10 actual ticks**
using the preserved processing-value candidate and original annual-v1 runtime.
Both pass accounting, participation, stocks and pricing across all 214 markets.
The [paired report](../reports/resumed-cost-disruption-comparison.json) verifies
identical pre-shock trajectories and both cost-only transitions.

During the two-year 30% extraction-cost increase, raw transaction prices passed
through about 13.9% and 16.5% of the nominal added cost in the two annual windows.
Raw contribution fell sharply and refinery contribution also declined. Final
unit fill stayed about 99.997%. Four recovery years later, raw transaction prices
remained 2.26% above control and Tier 1 profit was about 3.8% lower. Final firm
book equity reconciled with cumulative profit to less than $0.000001 error;
the maximum aggregate cash error was less than $0.000022. These results establish
accounting and physical resilience for this disturbance, while exposing slow
pass-through and residual learning effects. They do not certify a new candidate.

The [fairness audit](../reports/resumed-fairness-audit.json) confirms repeatable
ten-year portfolio gaps across both preserved seeds. Tier 0 width-one firms gain
25–31% more than width-four firms. Tier 2 width-four firms gain 14–16% more than
width-one firms. Sector means differ by about 1%, hiding these differences.
Single-product firms also have a much weaker recent earnings lower tail.
No permanent starvation or Age return is inferred from a recent window.

![Observed portfolio gains](../reports/resumed-portfolio-equity-gaps.png)

The [market diagnosis](resumed_market_diagnosis.md) connects rising extraction
contribution to near-capacity raw flows and incomplete refinery pass-through.
It distinguishes current annual-v1 drift from an older, different-protocol
compound-refinery collapse. Neither a specific pricing bug nor a settled equal
return equilibrium has been established from aggregate observations.

## Moderate-margin alternatives

The allowed-data moderate-margin profiles increase real conversion spending
and matching fixed procurement references. Their nominal opening calculation
targets a 50% aggregate final gross margin and reduces raw utilization to 80%.
Opening capital and the complete producer/buyer population remain fixed.
Outside spending rises to cover real costs rather than inventing profit.
The nominal fit remains an offline calculation, not evidence of actual returns.

The completed matched pair differs **only in shared final factory capacity, 2 or 3**:

- [Capacity 2](../reports/parameter-candidates/moderate-margin-50-capacity-2-raw80.json),
  seed 12345, prefix `reports/resumed-moderate-raw80-cap2-seed12345-10y`.
- [Capacity 3](../reports/parameter-candidates/moderate-margin-50-capacity-3-raw80.json),
  seed 12345, prefix `reports/resumed-moderate-raw80-cap3-seed12345-10y`.

Both completed full populations for **0xE10 actual ticks**. Each annual
checkpoint contains the exact world and cumulative evidence, allowing supported
continuation to a whole Age without rebuilding the economy or compressing time.
The new runner checks per-company equity/profit bridges, B2B units and cash,
physical production/stocks, funded upstream fulfillment, working cash, shared
capacity/warehouse limits, every active market, initial cohorts and annual
trajectories. Binary checkpoints and observation JSON have distinct roles.

The [completed comparison](../reports/resumed-moderate-raw80-capacity-completed-comparison.json)
records final tier mean gains of 1.817% / 2.051% / 2.092% for capacity 2, and
1.858% / 2.056% / 2.069% for capacity 3. These are ten-year actual outcomes.
Final annual gross margins are approximately 50%, with factory utilization near
30% / 20%. Capacity 3 achieves 99.997% final unit fill in its final year, versus
99.828% for capacity 2. Tier averages still conceal substantial width gaps.

Capacity 2 nominally binds six starting portfolios; capacity 3 provides headroom
for every nominal mean and more atomic-order bursts. Their aggregate utilization
is about 30% versus 20%. These measurements do not establish that either profile
is a fair standard.

## Proven Tier 0 rule defect and revision

The [read-only world diagnostic](../reports/resumed-t0-structural-diagnostic.json)
finds wide-firm raw lines stranded at 998 or 999 units. They need one or two units
to reach the 1,000-unit wholesale lot, but sequential proportional production can
repeatedly round their allocation to zero while sibling lines have large deficits.
Those lines remain invisible to stocked supplier selection; their demand forecast
decays and the bootstrap target stays at 1,000. Single-material firms receive the
remaining capacity and avoid this feedback.

The correction conserves integer production and shared capacity, allocates
rounding remainders without a permanent material-order preference, and pass cash,
acquisition-basis, storage and affordability regressions. It is a behavioral change
under a new economic protocol. Initial price-direction parity, decision
staggering and switching friction are separate observations; their causal
contribution has not been proved or silently changed.

The capacity-3 seed-12345 world continued exactly to tick 4,080, then stopped with
its real state and partial-year evidence intact after the defect was found. It
remains a historical counterfactual, not an Age result. The capacity-3 seed 24680
ten-year replication also completed with annual-v1. New rule trials must start from
opening populations rather than importing an old world into changed behavior and
calling it a continuous calibration.

Current process/session metadata is in
[research-running-state.json](../reports/research-running-state.json). Runtime
and instrument files must remain unchanged while experiments run. A failed
validation checkpoint is diagnostic evidence and cannot resume as an accepted run.

## Current controlled trials

Annual-v2 starts the same capacity-3 raw80 data from opening populations at seeds
12345 and 24680. Both completed ten years. Tier mean actual equity gains are
1.855% / 2.057% / 2.069% and 1.846% / 2.061% / 2.069%, respectively.
Their exact worlds are now continuing toward **0x2A300 actual ticks** using the
same frozen source, instruments, settings and opening cohorts. These are
unfinished Age experiments. Allocation regressions and independent review pass blocked-lot
restoration, all material permutations, scarce machine time and cash, shared
storage, heterogeneous costs and acquisition-basis accounting. Standard integral
proportions remain unchanged. No order, price or profit is supplied by the fix.
At both ten-year endpoints, every feasible positive integer production deficit
receives production; the former sub-lot rounding trap is absent. Width-four
Tier 0 gains improve against the matched earlier runs, but narrow/wide gain
ratios remain 2.12 and 2.43. The rule correction does not settle portfolio fairness.
At an earlier 32-year observation, tier mean equity gains were around 6.5–6.6%.
Later observations and preserved audits below supersede that historical progress
point. Individual-company and annual-income drift remain part of unfinished
validation; partial trajectories are not full-Age returns or extrapolations.
The [preserved 30-year checkpoint audit](../reports/resumed-annual-v2-30year-trajectory-audit.json)
retains all actual annual observations and full cohort distributions. Tier 0
decade-average profit per tick rises approximately 103→119→133 and 103→114→130;
Tier 1 moves approximately 320→319→308 and 322→324→310. These observed
changes establish surviving profit drift over the measured period. Tier 2
standalone firms retain lower mean returns than width-four firms, and three
then four final firms have no sales in the last ten years at the two endpoints.
Accounting and physical reconciliation continue to pass. No future equilibrium
or complete-Age return is inferred.
The [completed fairness and drift synthesis](../reports/resumed-annual-v2-fairness-drift-findings.json)
reports each seed separately: final-year Tier 0 income is much closer by width
than cumulative ten-year income, while Tier 1 drift remains seed-dependent.

![Completed pricing diagnostics](../reports/resumed-annual-v2-pricing-diagnostics.png)

This figure uses completed actual ten-year trajectories and company returns.
The input hashes, protocols and settings are in its
[binding record](../reports/resumed-annual-v2-pricing-diagnostics.json).

The [Tier 2 drought diagnosis](../reports/resumed-t2-width-drought-findings.json)
finds a repeatable initialization effect: width-four firms starting with a positive
price direction earn about 22.5% more than those starting negative in both cap3
seeds. Most year-long dormant firms remain stocked, funded and priced only slightly
above competing offers. Their next annual cuts can be slow. Isolated dormant
recipes overlap weakly across seeds, so those tails do not establish a fixed
ingredient disadvantage.

A separately declared [opportunity-10 trial](../reports/calibration-protocol-annual-v2-market-opportunity10.json)
changes one existing behavioral setting. It waits for ten allocated market order
opportunities, with the same annual window and ten-year stale timeout. This counts
market traffic rather than each line's observed orders; it can delay both noisy
reversals and zero-sale cuts. This ten-year trial and its strict matched
comparison are complete.
The [completed gate findings](../reports/resumed-annual-v2-opportunity10-findings-seed12345.json)
show Tier 2 annual droughts falling from 1,229 to 1,094 and the width-four
starting-direction mean-gain gap shrinking from 22.57% to 15.58%. Tier 0 mean
gain falls about 5%, one Tier 0 firm develops an annual drought, and compound
Tier 1 annual droughts rise from one to eight. This is a one-seed tradeoff.

A [zero-intensity negative control](../reports/calibration-protocol-annual-v2-price-k0-negative-control.json)
retains current-cost reservation while disabling voluntary quote experiments.
This isolates the learner's contribution to width/direction differences. It is
an attribution experiment, not a proposed standard bot. The attempted zero
response was rejected before any actual ticks because the normalizer enforces a
positive response floor; the accepted zero search intensity `k` supplies the
intended control with unchanged runtime. Both probes retain the
same full populations, initial directions, demand/supply settings and accounting.
Both probes have completed ten years; neither is an Age result or an adopted
standard. The completed annual-v2 cost-shock pair increases extraction cost
30% before tick 1,441 and restores it before tick 2,161, ending at tick 3,600.
It uses the completed main seed-12345 run as control; results are described below.

The [quote-hold comparison](../reports/resumed-annual-v2-k0-versus-adaptive-cap3-seed12345.json)
keeps Tier 2 average return close to control but raises its 10th-percentile gain
from 1.282% to 1.959% and removes all annual sales droughts. Tier 0 average gain
falls and its wide-firm disadvantage becomes larger. Holding quotes fixed cannot
resolve the full calibration objective.

The annual-v2 raw-cost disruption has now completed all ten years, including
four recovery years. Its [strict paired comparison](../reports/resumed-annual-v2-raw80-cap3-seed12345-cost-disruption-comparison.json)
passes matched configuration, actual pre-shock trajectory, full population,
cost-only receipts and accounting/physical reconciliation. During the shock,
raw contribution falls about 89%; final unit fill stays above 99.994%.
Four years after restoration, raw transaction prices remain 2.59% above control
and Tier 1 contribution is 3.81% lower. Raw deliveries include 231,000 then
19,000 units below their actual inventory basis in the two shock years. These
real losses reconcile with book equity. The
[actual one-tick mechanism fixture](../reports/resumed-annual-v2-posted-offer-timing-diagnostic.json)
confirms that extraction replenishes before buyers clear at existing offers,
then applies its cost reservation in the pricing phase. Raw extraction lacks
the downstream expected-proceeds production gate. This is a documented current
policy difference, not an accounting defect; changing it would require a
separate controlled rule trial. The comparator does not issue a recovery or
calibration acceptance badge.

## Isolated first-evidence rule trial

The [actual 720-tick first-decision replay](../reports/resumed-annual-v2-first-decision-12345-720.json)
confirms broad reach of a startup asymmetry: 91.2% of the 232,032 Tier 2 first
decisions recorded, including 32 paid route additions, respond to excess
inquiries. With no previous profit experiment, opposite initial directions give
different step sizes under identical forced scarcity or no-sales evidence.
This proves the mechanism is exercised; it does not establish its contribution
to later return gaps.

A copied [annual-v3 protocol](../reports/calibration-protocol-annual-v3-first-evidence.json)
retains the incoming experiment scale until finite previous-window profit exists.
Ordinary first up/down exploration, forced directions, cost reservations and all
finite-history adaptation remain unchanged. Only the copied model changes; the
kernel, worker, six instruments, settings, capital and full populations retain
their annual-v2 bytes/values. Two copied regressions pass, including 2,016 exact
finite-history comparisons. The [source and test archive](../reports/calibration-runtime-annual-v3-first-evidence-source.json)
makes the variant reviewable and reproducible.

Both fresh ten-year trials at seeds 12345 and 24680 completed. Their
[strict matched comparisons and synthesis](../reports/resumed-annual-v3-first-evidence-findings.json)
verify identical starting choices, capital, configuration and instruments.
Tier 2 annual sales droughts fall from 1,229 to 556 and from 1,208 to 614,
but width-four/standalone cumulative mean-gain ratios rise from 1.132 to
1.278 and from 1.113 to 1.246. The final-year income gap also persists in
both seeds. The width-four starting-direction advantage reverses: positive/negative
mean-gain ratios become about 0.900 and 0.898. Tier 0 cumulative width gaps
also grow, though its last-year width income narrows in one seed. This is
a conceptually isolated correction with observed fairness tradeoffs, not an
empirical calibration success. The worlds began fresh without importing
annual-v2 state. The application still uses annual-v2 logic, and both existing
Age worlds retain that original protocol. No annual-v3 behavior or demand/supply
parameters have been adopted.

Comparison-chart price and cost axes now retain five-decimal precision for
fractional-cent values. Cost controls accept the worker's real numeric precision.
Existing UI, dashboard, comparison and calibration-contract checks pass; these
presentation changes leave the experimental runtime and instrument hashes intact.

## Copied execution optimization

The [durable execution candidate](../reports/calibration-execution-probe-annual-v2-manifest.json)
passes repeated 120-tick full-population late-state parity and full-population
startup/live-configuration/paid-administration checks. Every world field, worker
closure and transaction remains bit-identical on each tested tick. The
[independent review](../reports/resumed-execution-optimization-independent-review.json)
also checks stable equal-price offer ordering, mutable reference inputs and binary
checkpoint source rejection. Paired engine CPU measurements show about a 19%
saving; checkpointing and research instrumentation remain unchanged, so this
is not a guaranteed end-to-end speedup. The complete copied source/proof archive
is preserved. No running Age world has been migrated and the application kernel
remains frozen. The [separate first-evidence execution revision](../reports/calibration-runtime-annual-v3-first-evidence-execution1-source.json)
now passes its own full-state late/startup/live/paid-action parity and independent
parent/checkpoint/archive binding review. Its separately copied complete workspace
passes [all 42 quick checks](../reports/scarcity-aware-quality-annual-v3-first-evidence-execution1-42.json).
That suite records actual current application defaults and leaves the raw80
candidate unadopted. It validates the runtime mechanics, not economic fairness
or full-Age returns.

## Completed decision-phase trials

Source review finds that decision dates based on sparse line number are coupled
to firm parity, recipe order and portfolio widths. Opposite initial-direction
groups occupy disjoint date residue classes within several opening cohorts.
Matched v2/v3 comparisons keep each company’s phase fixed, but the return
contrast between direction groups also includes these phase associations.

A separately copied annual-v4 prototype uses a fixed
seeded hash of tier, firm and product identity to assign the calendar phase,
without reading direction, width, profits or target returns. Evidence ages,
annual spacing, traffic/staleness gates and every other decision/transaction
rule remain fixed. Mechanical checks now pass 102 stable-identity cases,
144 nondecision cases, 216 exact decision-arithmetic comparisons, 51 gate cases
and 2,880 calendar-cadence cases. The fixed preselected salt is recorded;
eight zero-tick census seeds show the modular sign/width lattice is removed
without requiring exact balancing of finite cohorts. Independent source review
finds no unintended rule change.

This changes within-portfolio scheduling and requires an explicit rule trial
from fresh worlds. Its future effect cannot be attributed solely to removing
the old modular coupling: wider portfolios also spread their quote changes
over the year rather than acting on adjacent dates. Static distributions can establish the
removed modular coupling, not its actual economic effect. Both fresh ten-year phase trials have now launched at seeds 12345 and 24680,
using the same raw80/capacity-3 data and full populations as their completed
pure-v3 controls. The [protocol and exact source archive](../reports/calibration-runtime-annual-v4-hashed-decision-phase-source.json)
are frozen; strict matched-rule comparison is ready in a distinct phase-only
mode. These worlds do not import changed-source checkpoints, and no phase
outcome or acceptance was claimed at launch. The [independent review](../reports/resumed-annual-v4-independent-review.json)
verifies the final protocol, archive and all twelve members. Both first-year
pre-treatment samples now match their same-seed pure-v3 controls exactly
across all 214 markets, recorded annual equity cohorts and accounting/physical
flows. The calendar rule cannot make a learning decision before tick 361. The
[source-bound predecision audit](../reports/resumed-annual-v4-predecision-control-audit.json)
preserves those exact first-year records independently of rolling checkpoints.
Both phase trials completed **3,600 actual ticks**, with identical full
populations, opening capital, data and six instruments. The
[strict paired and cross-seed synthesis](../reports/resumed-annual-v4-hashed-phase-findings.json)
finds that removing the calendar lattice does not resolve the earnings gaps.
Tier 2 width-four/standalone cumulative mean-gain ratios increase from
1.278/1.246 under pure v3 to **1.319/1.356** under v4. Their final-year income
ratios remain 1.299/1.496. Width-four positive/negative initial-direction gain
ratios remain about 0.898/0.899. Tier 0 cumulative width-one/width-four ratios
narrow to 2.545/2.607, with mixed final-year income contrasts. Neither revision
is adopted. These are ten-year rule diagnostics, not Age results.

## Positive-learning intensity diagnostic

Two fresh full-population ten-year trials used the
[frozen k005 protocol](../reports/calibration-protocol-annual-v4-hashed-decision-phase-k005.json)
and the exact pure-v4 economic source and six instruments. They change only
`k` from 0.35 to 0.05: the initial unconstrained log-price experiment changes
from 1.75% to 0.25%. The choice and two seeds were
[recorded before treatment outcomes](../reports/planned-annual-v4-k005-experiment.json).
This follows the earlier k0 control's reduced dispersion and the v4 calendar
trial's persistent direction/width gaps; it tests retained positive learning
rather than assuming the smaller steps solve calibration.

The [zero-tick startup audit](../reports/annual-v4-k005-startup-audit.json)
verifies both seeds: only k differs among all 64 normalized settings, while
the complete opening worlds, identities, acquisition-basis equity, prices and
directions remain exactly equal. A strict comparison guard verifies the exact
parent/child protocols and rejects extra configuration, source, instrument,
revision, capital, population or intervention changes. Its outcome fixtures
are synthetic guard tests, rather than actual trial observations.

All voluntary moves in all tiers become smaller, including corrective
catch-up. Cost reservation stays active. Smaller steps can still produce
competitive sorting, stochastic reversals and persistent unequal returns;
they may also slow recovery. These diagnostics start fresh, reuse the unchanged
frozen runtime archive, and do not replace the continuing annual-v2 Age worlds.
At launch, no k005 outcome or acceptance was claimed. No parameter selection,
adoption or actual Age result is claimed.
Both recorded first years now match their completed same-seed pure-v4 controls
exactly across all 214 markets, 229 retained annual equity cohorts and the
recorded flows. The
[actual predecision audit](../reports/resumed-annual-v4-k005-predecision-control-audit.json)
preserves those first-year samples independently of rolling checkpoints.
The [independent freeze review](../reports/resumed-annual-v4-k005-independent-freeze-review.json)
also verifies the final protocol/configuration, shared archive, working source
bytes, startup bindings and native process-to-seed log associations. This
establishes control integrity, not the later treatment outcome.

Both k005 trials subsequently completed 3,600 actual ticks and passed the
[strict paired comparisons](../reports/resumed-annual-v4-k005-effect-seed12345.json)
and [same-protocol cross-seed comparison](../reports/resumed-annual-v4-k005-cross-seed-comparison.json).
Tier 2 width-four/standalone cumulative gain ratios are **1.390/1.344**, with
final-year income ratios 1.660/1.548. Width-four initial positive/negative
direction ratios remain 0.899/0.902. Tier 0 mean gains fall to 1.588%/1.585%,
while Tier 1 and Tier 2 remain near 2.07%. Smaller positive moves do not resolve
the observed return gaps. The [complete source-bound synthesis](../reports/resumed-annual-v4-k005-findings.json)
includes every firm, material, product, sector and portfolio width. Tier 1's
basic/compound mean-gain ratio improves to 1.000 in both seeds, material
maximum/minimum mean-gain ratios narrow to 1.012/1.004, and annual sales
droughts disappear. Because k changes in every tier, upstream input effects
are part of these observations. Tier 2's lower tail and persistent droughts
do not improve consistently: firms with at least five annual sales droughts
increase from 22/26 to 25/32. No k005 standard is selected. Selected-profile
disruption tests and actual Age validation remain outstanding.

## Preserved sixty-year baseline trajectories

Both unchanged annual-v2 worlds have passed sixty actual years. Their exact
**21,600-tick** states are separately preserved and passively audited in the
[sixty-year trajectory report](../reports/resumed-annual-v2-60year-trajectory-audit.json).
Mean actual equity gains are 13.584%/12.262%/12.376% at seed 12345 and
12.934%/12.408%/12.380% at seed 24680 for Tier 0/1/2. The endpoint includes
all companies and all 657 cohort summaries; recorded annual summaries cover
229 cohorts, rather than raw company vectors or every overlapping cohort.

Tier 2 width-four/standalone cumulative gain ratios are 1.315/1.306 and the
last-year income gap persists. Standalone annual sales droughts remain
25/200 and 24/200, compared with 54/48,450 and 52/48,450 for width four.
Tier 0's cumulative startup width-one/four gap has narrowed to 0.956/1.016;
width two now has the highest mean gain in both seeds. Raw contribution is
not monotonic: decade means rise overall but dip in some decades, while
refinery contribution partly recovers after its third-decade decline. No
settled equilibrium or eventual Age doubling is inferred.

Maximum cumulative cash reconciliation errors remain below $0.000224,
maximum company equity/profit errors below $0.000005, and recorded physical
and business unit-transfer errors remain zero. This supports accounting
integrity while leaving distributional calibration unfinished. The
[actual-trajectory chart](../reports/resumed-annual-v2-60year-actual-trajectories.png)
shows all sixty annual observations and complete-company endpoint quantiles,
without extending any trajectory beyond its observed horizon.
The [independent sixty-year review](../reports/resumed-annual-v2-60year-independent-fairness-review.json)
recomputes all endpoint cohorts and verifies that the first thirty recorded
annual samples remain unchanged. Width-four/standalone gain ratios rise from
1.223/1.206 at year 30 to 1.315/1.306 at year 60; year-60 income ratios are
1.397/1.445. Six/seven final firms have ten-year sales droughts, restricted
to opening widths one and two. These are observed outcomes, not forward estimates.

The unchanged worlds subsequently passed **100 actual years**. Their genuine
36,000-tick states are separately preserved and [passively audited](../reports/resumed-annual-v2-100year-trajectory-audit.json).
Mean book-equity gains at seeds 12345/24680 are 23.610%/22.001% for Tier 0,
20.260%/20.764% for Tier 1, and 20.548%/20.555% for Tier 2. Tier 2 width-four/
standalone cumulative gain ratios widen to 1.350/1.334, with year-100 income
ratios 1.505/1.369. One/three final firms have ten-year sales droughts at these
endpoints. Maximum cumulative cash reconciliation errors stay below $0.000475,
company equity/profit errors below $0.000011, and physical and business unit
transfer errors remain zero. All firms and 657 endpoint cohorts are recomputed;
the annual record still contains 229 cohorts, rather than raw company vectors.
These remain partial baseline trajectories, with no full-Age or selected-rule
validation claim.

The [passive accounting precision diagnosis](../reports/resumed-annual-v2-100year-accounting-precision-diagnosis.json)
recomputes every stored cash value using exact IEEE-754 decomposition and checks
the results against Python decimal arithmetic. Endpoint cash residuals of
$0.000333/$0.000406 become $0.000383/$0.000391 with exact aggregation. Tier sum
rounding explains only part of the residual; final expression rounding contributes
zero at these endpoints. Annual grouping also leaves a residual and cannot
identify an earlier update or journal discrepancy from saved totals. Individual
book bridges and unchanged accounting guards pass. No threshold, instrument,
stored account or running world has been modified to hide the difference.

The [passive upstream transaction decomposition](../reports/resumed-annual-v2-100year-upstream-drift-decomposition.json) compares actual years 1–10 with 91–100. Tier 0 aggregate profit rises by $39.689/$25.302 per tick, with symmetric invoice-price effects of $39.239/$24.884 and quantity effects of only about $0.41. Aggregate raw production utilization remains about 80.22%, compared with 79.97% in the first decade. Tier 1 profit changes by −$18.040/−$4.575: higher output invoice prices contribute +$19.345/+$18.369, while higher acquisition COGS contributes −$39.070/−$24.741. This describes endogenous recorded transactions, not a controlled causal policy effect or an independent historical journal reconstruction. The [independent binary/arithmetic handback](../reports/resumed-annual-v2-100year-upstream-drift-independent-handback.json) reproduces 36,376 numeric comparisons. Aggregate component effects include delivered material and seller mix; they are distinct from a fixed-mix causal price treatment.

The [read-only source review](../reports/resumed-current-source-read-only-review.json)
finds no new reachable cash, acquisition-basis, shared-limit, population or
catalogue-boundary defect against HEAD. It records a presentation caveat:
Tier 0 dashboard “gross profit” currently measures operating cash flow, while
calibration uses actual sold-cost accrued profit and reconciled book equity.
The [final adoption map](calibration_default_adoption_map.md) carries a concrete
proposal to distinguish those fields in every view and verify both bridges.
No frozen worker or experiment was changed by the review.

A separately copied evidence upgrade has been frozen and reviewed for prospective
selected-rule Age runs: exact annual Float64 book-equity vectors for every
company, retaining opening identities and all actual annual dates. This would
allow independent company and recipe/material/portfolio trajectory audits
beyond selected annual cohorts and complete endpoint distributions. Estimated
uncompressed history is about 231 MiB per Age, before measured compression.
No frozen instrument or running world has changed, and no unobserved earlier
history will be reconstructed or claimed. The
[independent copied-instrument review](../reports/resumed-annual-history-independent-review.json)
passes focused source, cache-invalidation, artifact-corruption and receipt
checks. A genuine full-population one-year mechanics test preserves all worker
world bytes, existing research and 229 annual cohort metrics. Canonical opening
membership indices now avoid rediscovering memberships at each annual capture;
all new financial values are still read and checked. A repeated-year 480-record
fixture measures validation time only and does not represent executed Age history.
The [frozen proposal archive](../reports/calibration-annual-company-equity-proposal.json)
and [final independent binding review](../reports/resumed-annual-history-independent-final-binding.json)
verify all 64 archived members and the genuine full-population one-year evidence.
There is no changed-source continuation or selected-rule Age launch.

The [copied Tier 0 reporting correction](../reports/tier0-reporting-proposal-manifest.json)
uses actual sold acquisition basis for COGS and gross profit, and separately
reports extraction spending and operating cash flow throughout tier, element,
company, comparison and history views. Three actual small mechanism ticks
cover stock building, sale from earlier stock and a cost shock while holding
earlier inventory. Cash change matches operating cash flow, book-equity change
matches sold-basis profit, and their difference matches the inventory-value
change. The [independent reproduction](../reports/tier0-reporting-independent-review.json)
verifies all 28 archive members and reproduces these observations exactly.
Complete economic world arrays and non-reporting closure match; reporting
snapshots and histories intentionally differ. Root and frozen worker sources
remain unchanged. These are reporting mechanics, not calibration evidence.

The [offline comparator correction](../reports/calibration-candidate-instrument-binding-fix-review.json)
also requires exact instrument-map equality with a declared protocol. Two
equally misbound reports can no longer pass merely by matching one another.
Historical unbound protocols retain their explicit older limitations, and
the completed v4 cross-seed output remains byte-identical after the correction.

## Relative final-buyer switching-effort trial

The [separate annual-v5 protocol](../reports/calibration-protocol-annual-v5-relative-final-switching-cost.json)
changes only the final buyer's alternative-offer ranking effort: incumbent
posted unit price times the existing reliability-based fraction, with fixed
4.5%–18% bounds. Absolute business switching effort retains the original
configuration. This is an authored buyer policy; stronger retention can protect
expensive incumbents and slow competitive switching. It uses no return target,
asset value or portfolio width. Effort affects ranking only; delivered quantity,
invoice payments and real costs retain their existing rules.

The [independent mechanical reproduction](../reports/relative-consumer-switching-independent-review.json)
verifies the exact one-line kernel change and unchanged model, worker and six
instruments. Both full-population opening worlds and complete closures match
exactly at tick zero, including all 64 normalized settings. Synthetic clearing
fixtures verify price scaling, strict ties, preference and stock fallback,
invoice-based demand and payments, real zero-price losses and unchanged
business transfers. They execute no complete worker ticks and establish no
return or Age result. The [frozen prospective plan](../reports/planned-annual-v5-relative-final-switching-experiment.json)
declares two fresh 3,600-tick trials against completed pure-v4 controls, retaining
k=0.35 and the same raw80/capacity-3 data. Execution, reporting and annual-history
proposals are excluded. This policy can affect relationships before the first
annual price decision; equal first-year treatment outcomes are not presumed.
No trial outcome or standard adoption is claimed at freeze.
Both trials have subsequently launched from fresh tick-zero worlds. The
[native launch binding](../reports/annual-v5-relative-final-switching-launch-binding.json)
verifies each process's log, exact declared runtime and six instruments, and
all 64 settings against its completed same-seed control. The
[independent final comparison-guard review](../reports/calibration-rule-relative-final-switching-independent-review.json)
passes 73 rejection cases and the exact frozen declaration using constructed
guard fixtures. These establish trial control integrity, not economic success.

Both trials subsequently completed **3,600 actual ticks** with exit code zero.
The [complete findings](../reports/resumed-annual-v5-relative-switching-findings.json)
retain all 62,970 companies, 657 endpoint cohorts, ten actual annual windows of
229 cohorts and all 214 markets. Strict same-seed comparisons and the cross-seed
comparison pass; the [independent endpoint review](../reports/resumed-annual-v5-independent-endpoint-review.json)
recomputes accounts directly from the genuine final worlds.

Tier 2 mean gains stay near 2.078%, but width-four/standalone cumulative gain
ratios worsen from 1.319/1.356 to **2.057/2.285**. Final-year income ratios reach
5.214/4.148. Standalone firms with no sales in the final year increase from
48/60 to **94/108 of 200**; five-year droughts increase from 9/13 to 41/38.
Overall Tier 2 p10 improves while p01 and standalone p10 decline. Wider firms
dominate the population, so a better aggregate quantile does not establish
comparable starting opportunities. Material contrasts and Tier 1 droughts also
worsen. This particular predeclared 4.5%–18% policy will not be adopted.

Final weighted gross margins remain about 50.07%/50.10%, utilization
19.91%/19.89%, and funded unit fill exceeds 99.997%. Maximum company equity
residuals remain below $0.000000677 and cash residuals below $0.000042. The
fairness deterioration is therefore observed in invoice transactions and real
acquisition-basis accounts. It does not establish that every relative effort
policy fails or that the original absolute effort was a defect. The completed [passive customer, stock and learning census](../reports/resumed-annual-v4-v5-customer-inventory-learning-findings.json) finds fewer matching customer memories at standalone firms and stocked inventories during zero-sales windows. These endpoint associations do not identify the full causal path. The [monthly-label erratum](../reports/resumed-annual-v4-v5-customer-census-monthly-erratum.json) preserves the original census while correcting its explanatory month length to 30 ticks.

The [pure-v5 quality report](../reports/scarcity-aware-quality-pure-annual-v5-42.json)
passes all **42 quick checks** with ordinary application defaults, rather than
injecting the experimental raw80/capacity-3 profile. Its separate archive contains
190 verified members; the [independent review](../reports/resumed-pure-annual-v5-quality42-independent-review.json)
checks every captured input, log, assertion and source binding. This establishes
integration mechanics for the unoptimized copied rule, not economic calibration.

A [separate copied-v5 execution probe](../reports/calibration-execution-probe-annual-v5-execution1-startup-manifest.json)
preserves every world, closure and transaction value over 120 actual startup
ticks, including live configuration changes and paid route additions. The
[independent startup review](../reports/resumed-annual-v5-execution1-startup-independent-review.json)
verifies its 78 archived members and focused pricing/phase/consumer regressions.
The [separate late-state archive](../reports/calibration-execution-probe-annual-v5-execution1-late-manifest.json)
then records three 120-tick comparisons from genuine 3,600-tick states: both
seeds and a repeated seed-12345 window. Every world, complete closure, setting
and transaction value matches at every tick. Measured engine CPU savings are
18.46%–19.42%; these measurements exclude prospective annual-company evidence
and do not predict a whole Age's execution time. The new archive preserves 91
members while retaining the earlier startup archive unchanged. The [independent late-state review](../reports/resumed-annual-v5-execution1-late-independent-review.json) verifies all 91 archived members and source/checkpoint/parity bindings. No live experiment has migrated to these
execution, reporting or recorder proposals, and no accepted changed-source
continuation or actual Age is claimed.

## Consumer clearing edge case

The [source-bound stage diagnostic](../reports/resumed-zero-demand-alternative-diagnostic.json)
establishes a reachable clearing defect in both v4 and v5. Effective offer
ranking adds switching effort, but physical quantities use invoice prices and a
shared rounding draw. A retained higher invoice can therefore request zero
units while a later discovered cheaper invoice requests one. The current loop
stops at the zero request and never evaluates the feasible alternative. Legal
initialized buyer parameters, ordinary activation/search settings and stocked
quotes above engineering cost reproduce this in 20 synthetic consumer stages.
They execute no worker ticks and do not measure real-run incidence.

A [separate passive final-tick census](../reports/resumed-zero-demand-actual-endpoint-census.json)
reconstructs discovery from actual saved tick-3,600 records. It excludes routes
added after clearing and restores the preceding discovery weights. The v4
controls have zero discovered cheaper positive-demand cases at that tick; v5
has 15/11, of which 14/11 have enough closing stock to be individually feasible.
These are one-tick observations. Buyers can share the same alternative's stock,
so requested units are not jointly deliverable hypothetical sales or profits.
Neither diagnostic explains the broader return and drought gaps.

The [independent mechanical review](../reports/resumed-zero-demand-alternative-independent-review.json) passes 27 isolated consumer-stage calls. The copied correction skips zero-demand offers anywhere in the candidate order and retains the first positive-demand offer as the unfilled fallback when initial invoice demand is zero. A later stocked positive offer replaces that fallback. Ranking, invoice quantities, shared rounding, real payments and stock limits remain fixed. The separate [v6 protocol](../reports/calibration-protocol-annual-v6-zero-demand-alternative-fallback.json) and two-seed [prospective ten-year plan](../reports/planned-annual-v6-zero-demand-alternative-experiment.json) are frozen. Their [independent freeze review](../reports/resumed-annual-v6-freeze-independent-review.json) verifies all 19 archive members, unchanged settings and full topology. The [independent comparison review](../reports/resumed-annual-v6-comparison-guard-independent-review.json) passes exact whole-protocol bindings and 139 rejection cases. Both [fresh full-population ten-year trials](../reports/annual-v6-zero-demand-alternative-completion-binding.json) completed from tick zero against the same-seed v4 controls. They retain the same complete configuration and six-file instrument. The [actual findings](../reports/resumed-annual-v6-zero-demand-findings.json), [independent endpoint audit](../reports/resumed-annual-v6-independent-endpoint-review.json) and [independent synthesis review](../reports/resumed-annual-v6-findings-independent-review.json) reconcile all 62,970 companies, 657 endpoint cohorts, 229 annual cohort paths and 214 markets. Tier 2 mean-gain changes are only about 0.0000000073, yet individual differences range from −0.580 to +0.500 percentage points in one seed and −0.192 to +0.218 in the other. Width-four/standalone gains remain 1.327/1.357; final-year income expands these gaps. Annual drought counts improve slightly overall, while standalone and longer-drought outcomes are mixed. Tier 0 width-four gains remain only 0.851%/0.830%, versus standalone gains of 2.167%/2.165%. This fixes traversal logic without establishing harmony, standard adoption or an Age outcome. The [root reproduction record](../reports/zero-demand-alternative-root-final-reproduction-review.json) keeps a native V8 crash separate from the successful identical-proof retry; no complete crash cause or cure is established.

The [pure-v6 quick-quality archive](../reports/quality-pure-annual-v6-42-source.json) records all 42 checks passing with ordinary application defaults. Its [independent review](../reports/resumed-pure-annual-v6-quality42-independent-review.json) verifies all 191 members, 144 captured inputs and ordered child exits without modifying the earlier v5 evidence. These are integration checks, not selected-profile or Age acceptance.

The [separate combined proposal](../reports/calibration-v6-evidence-execution-reporting-proposal.json) passes two fresh full-population one-year comparisons against pure v6. All world values, transaction observations, 229 annual cohorts, 657 endpoint cohorts and 62,970 annual equity values agree. Intentional Tier 0 reporting differences and additive research history are checked separately. Its [independent source-scope review](../reports/resumed-annual-v6-integrated-source-scope-independent-review.json) reconstructs the exact two execution regions and reviewed reporting/recorder donors; the [final independent archive/proof review](../reports/resumed-annual-v6-integrated-proof-independent-review.json) verifies all 66 members and actual annual artifacts. Temporary one-year raw world files were deleted, so recorded monthly world/transaction comparisons remain bound author evidence rather than an independent raw-world rerun. No accepted protocol or live experiment has migrated to the combined source.

The [preserved 180-year baseline audit](../reports/resumed-annual-v2-180year-trajectory-audit.json) records actual mean gains of 44.14% / 36.18% / 36.72% and 41.49% / 37.05% / 36.73% across Tier 0 / 1 / 2. Tier 2 width-four/standalone gains remain 1.355/1.349. These original annual-v2 worlds pass unchanged accounting guards and retain all 180 annual observations; they are still incomplete Age controls under their own older rules. No future trajectory is inferred. The new 180-year audit has not yet received a separate independent binary review.

The [ten-year v6 quantity/contribution identity](../reports/resumed-annual-v6-width-volume-margin-decomposition.json) separates each width return into actual sold units per firm and pooled sold-cost profit per unit. Tier 0 width-four firms sell only 49.6%/55.3% of standalone volume and receive 79.2%/69.4% of pooled unit contribution. Tier 2 width-four volume is 131.8%/139.8% of standalone volume, while pooled unit contribution is 100.7%/97.1%. Product mix and sold-cost timing remain included; these are descriptive accounting identities, not causal pricing or capacity findings.

A [passive discovery geometry analysis](../reports/resumed-discovery-exposure-geometry.json) finds a 0.4854% opening width-four advantage from duplicate draws under the independent-uniform-draw probability model. The [independent opening arithmetic](../reports/resumed-discovery-opening-arithmetic-independent-review.json) confirms that direct inclusion effect. Candidate inclusion, contacted suppliers, retained preferences and actual sales are distinct; this small static effect does not bound long-run feedback.

The [combined 42-check quality archive](../reports/quality-combined-annual-v6-42-source.json) passes all checks with native exit zero and ordinary application defaults. Its [independent archive review](../reports/resumed-combined-annual-v6-quality42-independent-review.json) verifies 250 members, 145 inputs and every ordered child exit. The initial attempt retains a legacy dashboard assertion failure: cash change was compared with gross profit. An [independently reviewed copied fixture adaptation](../reports/resumed-annual-v6-combined-quality-adaptation-independent-review.json) instead checks cash against operating cash flow and book-equity change against sold-basis profit, while retaining unrelated checks. The [mature-state mechanics archive](../reports/calibration-v6-combined-mature-mechanics-proposal.json) and its [independent review](../reports/resumed-annual-v6-mature-proof-independent-review.json) also pass both seeds plus a repeated 120-tick probe. Every economic value and transaction matches through established learning; only declared Tier 0 reporting differs. An initial auxiliary observer assertion failure remains preserved separately. The distinct [seven-instrument protocol](../reports/calibration-protocol-annual-v6-company-history-execution-reporting-validation1.json), [three-seed plan](../reports/planned-annual-v6-company-history-execution-reporting-validation1.json) and [immutable freeze review](../reports/resumed-annual-v6-age-freeze-independent-review.json) are complete. The [native launch binding](../reports/annual-v6-company-history-validation-launch-binding.json) records three fresh worlds at seeds 12345, 24680 and 31415, each starting at zero and targeting 172,800 actual ticks. All 62,970 annual book-equity values are captured every 360 ticks, with full simulation checkpoints every 3,600 ticks. These runs are incomplete; unresolved early width gaps remain explicit. The separately declared selected-source cost-shock runs and matched accounting/history comparisons have completed; independent economic review has completed with residuals retained. No final calibration or standard adoption is claimed.

The [preserved actual66-year tier diagnostic](../reports/resumed-selected-v6-actual-66year-tier-trajectory-diagnostic.json) shows upstream drift persists under the corrected V6 family. In seed order12345/24680/31415, Tier0 mean cumulative gains are15.96%/17.17%/15.48%, Tier1 gains13.81%/13.30%/13.83%, and Tier2 gains13.55%/13.55%/13.57%. Tier0/Tier1 relative gain differences are15.6%/29.1%/11.9%. Recent ten-year Tier0 mean annual income/opening exceeds the first decade in allthree, while Tier1 is lower. These are actual emitted paths through23,760 ticks, preserved in immutable log prefixes; no extrapolation, durable-world or full-Age completion, causal rule finding, or company/cohort fairness verdict is implied. A separate [actual120-year emitted-prefix diagnostic](../reports/resumed-selected-v6-actual120-tier-trajectory-diagnostic.json) preserves all360 annual rows across three worlds through43,200 ticks. Tier0/Tier1 cumulative gain ratios are1.332/1.532/1.148; recent ten-year Tier0 income is62.2%/83.7%/35.4% above its opening decade, while Tier1 is11.16%/19.84%/1.88% below it. The [independent120-year arithmetic review](../reports/resumed-selected-v6-actual120-independent-review.json) verifies all360 annual rows, allthree full profiles, all12 sources, exact cumulative distributions and5,097 scalar calculations with maximum differencezero. Its first66-year prefixes are byte-identical to the earlier preserved evidence. Original66-year evidence remains unchanged; neither partial horizon forecasts480-year outcomes.

## Remaining completion work

Evaluate the completed pair and pricing probes, resolve repeatable return drift
and starting-choice effects, and complete the exact worlds over **0x2A300 actual ticks** across
independent seeds. Validate disruptions on the selected profile, adopt supported
settings throughout defaults/reset/UI/specifications, complete the final
market and UI gates, consolidate the large accumulated diff and commit the coherent
authorized work. Preserve unrelated `spec/technology_strategy.md`. Marketing,
invention activation, onboarding and war gameplay remain deferred.

## Paid diversification hypothesis

The [policy audit](../reports/resumed-t2-diversification-policy-audit.json) identifies a barrier for low-sales firms: at shared capacity three, adding a route requires 68 units sold in a month, while standalone firms average about 13–14. V7 removes only that 75% utilization entry condition. The real $1,000 fee, $1,600 cash gate, eligibility, four-product ceiling, and shared factory/storage/input limits stay the same. Liquid firms can buy without sales; prudence and subsequent demand remain empirical questions.

The [mechanical evidence](../reports/calibration-v7-paid-diversification-mechanics-source.json) and [independent review](../reports/resumed-annual-v7-mechanics-independent-review.json) pass three fresh full-population tick0→30 pairs. Worlds match through tick29 and immediately before month-end expansion. Each treatment buys 13,500 actual routes for $13.5m, with a matching cash debit/equipment entry and no book-equity gain at purchase. No extra physical capacity, inputs, goods, sales or customers are granted. Saved purchase records were independently reconciled; raw private world streams were not retained.

The [original 42-check attempt](../reports/quality-annual-v7-42-source.json) remains failed with 40 passes and two route-assumption fixture failures. The [exact reviewed adaptations](../reports/calibration-v7-quality-fixture-adaptations-root-review.json) preserve existing assertions while handling actual new-route birth and every bot fee. The [separate full registry](../reports/quality-reviewed-annual-v7-42-source.json) passes all42 checks, and its [independent review](../reports/resumed-annual-v7-quality42-independent-review.json) verifies all199 members.

The [final protocol](../reports/calibration-protocol-annual-v7-paid-diversification-exploration.json), plan and89-member archive have a [passing immutable review](../reports/resumed-annual-v7-final-freeze-independent-review.json). The [freeze addendum](v7_paid_diversification_freeze_revision2.md) retains the original optimization-guard finding and corrected helper. A producer-status mismatch in the original comparator was also found before actual outcomes; the preserved revision2 and [exact-final activation review](../reports/resumed-annual-v7-exact-final-comparator-activation-independent-review.json) pass.

Root’s [prelaunch checks](../reports/annual-v7-paid-diversification-root-prelaunch-gate.json) pass. Three actual fresh3600-tick trials have **completed nativeexit0** at seeds12345/24680/31415; the [native launch binding](../reports/annual-v7-paid-diversification-launch-binding.json) records exact zero-tick headers, full64-field profiles, PID/session pairs and unchanged source. Their matched controls are the genuinely audited parent Age snapshots at3600. Their [actual completion binding](../reports/annual-v7-paid-diversification-completion-binding.json) records ten complete annual observations per seed and all saved output hashes. The unchanged [strict all-company paired analysis](../reports/resumed-annual-v7-paid-diversification-strict-paired-comparison-revision2.json) completed with [genuine native exit zero](../reports/resumed-annual-v7-paid-diversification-strict-comparison-native-handback.json). It validates every company book, paid fee, shared resource, all657 opening cohorts and ten actual annual equity vectors per arm. The [independent actual six-arm arithmetic audit](../reports/resumed-annual-v7-independent-outcome-audit-revision3-native-handback.json) has completed with genuine native exit zero. It independently verifies every company book and all657 cohort conclusions, invoice/fee calculations and actual annual equity histories; all six complete decoded states remain equal. Its [first actual audit attempt](../reports/resumed-annual-v7-independent-outcome-audit-first-native-failure.json) stopped with native exit one on a cash-cohort mean differing by about $8e-11. Both producers sum sorted observations; the independent helper sums company order. The [exact cohort diagnosis](../reports/resumed-annual-v7-independent-audit-distribution-order-diagnosis.json) and [separate aggregation repair review](../reports/resumed-annual-v7-independent-outcome-audit-revision3-source-review.json) pass. The repair changes summation order to match both declared producers; every numerical, accounting and economic threshold stays unchanged. The separate repaired audit completed successfully under the reviewed source, with the original native failure preserved. The [actual paired figure](../reports/resumed-annual-v7-paid-diversification-actual-panels.png) shows opening-width returns, endpoint droughts and completed-tick cash tails for all three seeds. The [first actual comparison failure](../reports/resumed-annual-v7-first-comparison-native-failure.json) is preserved: its nativeexit1 occurred before world reading because the assembler descriptor omitted the byte sizes of three final receipts. Existing launch/completion hashes and sizes are correct. The [separate metadata-only repair](../reports/annual-v7-paid-diversification-completed-input-assembly-revision2.json) and its [independent review](../reports/resumed-annual-v7-completed-input-assembler-revision2-independent-review.json) passed; the strict reader and economic sources remain unchanged. The three candidate Age jobs continue; the two older baseline jobs stopped for memory scheduling with exact states preserved. Their [independent continuation-eligibility review](../reports/resumed-annual-v2-stopped-states-passive-eligibility-review.json) passes the complete worlds, 249/250 annual observations and 150/90 partial-year ticks. Current signed cash-ledger residuals of $0.002625/$0.002735 are preserved within the existing $1 guard; no restart or completed Age is claimed. The ten-year comparison records individual annual incomes, opening cohorts, paid fees, liquidity and droughts. Paid access raises narrower-portfolio means and reduces their endpoint droughts across all three seeds; four-product means fall slightly and cash reserves decline for buyers. Repeatable portfolio gaps remain. The [independent economic interpretation](../reports/resumed-annual-v7-independent-economic-interpretation.json) reviews all657 cohorts, individual/annual tails, fees, liquidity, droughts and starting-direction strata. Root’s [completed-outcome disposition](../reports/annual-v7-paid-diversification-root-completed-outcome-disposition.json) is **HOLD experimental candidate**. Mono/width-four mean gains differ23.86–26.89%, final-year income differs20.26–27.29%, and width-four gains fall about5% in every seed. Eleven repeated product-membership pairs and five Tier1-material pairs exceed10%; overlapping membership returns remain distinct from allocated route outcomes. All originally narrow firms pay towardfour routes, spending$15.8m perseed with substantially lower minimum cash. The [upstream market interpretation](../reports/resumed-annual-v7-independent-upstream-market-findings.json) also retains raw mono/wide ratios2.26–2.73 and material ranges13.5–15.4%. No standard selection, automatic additional three-Age launch or full-Age conclusion follows.

The [full-Age interpretation note](../reports/calibration-full-age-fairness-interpretation-note.json) requires examining repeated pairwise and family-range differences against the unchanged 10% criterion. An empty list of deviations from the family mean would not alone certify fairness.

The [independent selected-source shock findings](../reports/resumed-selected-v6-disruption-independent-findings.json) retain the full company distributions. Four recovery years later, raw invoice prices remain 2.659% / 1.814% / 2.857% above controls, and Tier 1 annual sold-cost gross profit remains 3.358% / 2.652% / 4.013% below them, in seed order 12345 / 24680 / 31415. Tier 0 cumulative mean gains remain lower by 0.2972 / 0.3583 / 0.2496 percentage points. The nearly unchanged Tier 2 mean hides offsetting company effects: paired cumulative-gain p10 is about −0.60 to −0.64 percentage points and p90 about +0.60 to +0.63. One-year and five-year drought counts move in both directions across seeds. Closing-cash tails and all completed-tick cash minima remain positive; those cumulative minima are not shock-phase or intra-tick measurements. Real below-acquisition-basis raw trades during the shock remain recorded as losses. Tiny recovered raw unit-cost differences make large price/COGS residual ratios economically unsuitable pass-through estimates. Weighted invoice prices also include supplier and material mix. These are complete ten-year disturbance observations, without a full-recovery, Age or standard-adoption verdict.

The [shared-capacity pricing diagnosis](../reports/resumed-selected-v6-shared-capacity-pricing-source-diagnosis.json) and [cost-relative pricing assessment](../reports/selected-v6-cost-relative-pricing-mechanics-assessment.md) identify unselected research questions. Current bots optimize each route’s sold-cost GP, while resources are shared and costs move between windows. Neither changing to firm GP nor using a learned markup is established as a cure. No further runtime rule or default has been changed.

The [upstream pricing observer source review](../reports/resumed-upstream-price-decision-observer-source-independent-review.json) passes the reversible route-identity transform and unchanged learner body. The separate prospective three-year,1,080-tick paired probe from preserved year70 worlds has passing [dispatcher/source](../reports/resumed-upstream-price-observer-1080-source-independent-review.json) and [bounded codec](../reports/resumed-upstream-price-observer-codec-source-independent-review.json) reviews. Its41 archived files and twelve constructed codec rejection checks are verified. It can observe two consecutive360-tick profit windows where the actual learner supplies them, without backfilling history. Root’s [exact source generation](../reports/upstream-price-observer-1080-source-generation-native-handback.json), [independent concrete activation review](../reports/resumed-upstream-observer-1080-generated-activation-independent-review.json) and [native preflight](../reports/upstream-price-observer-1080-root-native-preflight.json) pass. The first [actual sequential probe](../reports/upstream-price-observer-1080-actual-native-launch-binding.json) stopped with [genuine native exit one](../reports/upstream-price-observer-1080-first-actual-native-failure.json) on a recorder cost-array assertion. Its original source, log andpartial header remain preserved; no final events or completedseed proof exists. Selectedworker source uses NaN for an absent last raw invoice, which the blanket finite guard rejects. The [actual fixed70 vector diagnosis](../reports/resumed-upstream-observer-actual70-nan-invoice-diagnosis.json) confirms all2,400 unused raw-input invoice slots contain legalNaN absent-invoice sentinels, while all raw-stock and acquisition-basis slots remain finite. The [separate lossless codec repair](../reports/upstream-price-observer-last-invoice-sentinel-repair-source-proposal.json) accepts NaN only in optional last-invoice slots and retains finite nonnegative real costs and quantities; The [independent repair review](../reports/resumed-upstream-observer-invoice-sentinel-independent-review.json) passes four positives and56 rejection cases. The [concrete repaired activation review](../reports/resumed-upstream-observer-revision2-generated-source-independent-review.json) and [Root native preflight](../reports/upstream-price-observer-revision2-root-native-preflight.json) pass; the [separate actual three-seed replay](../reports/upstream-price-observer-revision2-actual-native-completion.json) completed with genuine native exit zero. All three seeds preserve equality of every World and closure field through 1,080 paired ticks and all four physical/accounting boundaries. Each seed records 3,120 retained decisions across all 1,040 active upstream routes. The independently reviewed [bounded event verifier](../reports/resumed-upstream-observer-1080-verifier-independent-source-review.json) has a [concrete one-literal activation](../reports/upstream-price-observer-verifier-actual-activation-source.json); the [independent amendment review](../reports/resumed-upstream-observer-actual-verifier-concrete-source-independent-review.json) passes and [actual event verification](../reports/upstream-price-observer-1080-decision-verifier-native-handback.json) completed with genuine native exit zero. All 9,360 retained decision formulas, framing, continuity, exact calendar visits and complete source-prefix GP windows pass. There are 1,040 aligned own-versus-firm comparisons per seed; first incomplete windows remain null. All floor-change and floor-clipping flags are zero during this probe. Raw multi-route signal disagreements require interpretation, while all single-route controls agree. Observer completion advances no accepted Age history and establishes no economic cure. The acceptedAge worlds continue separately.

The [actual120-year figure](../reports/resumed-selected-v6-actual120-tier-trajectories.png) plots the preserved observed annual tier paths and mean income without smoothing or forecasts. Its [native and visual verification](../reports/resumed-selected-v6-actual120-tier-plot-native-handback.json) is complete; all120 years remain partial Age evidence.

## Actual pricing signals and isolated company-profit experiment

The [independent branch interpretation](../reports/resumed-upstream-price-observer-1080-independent-decision-findings.json) and [independent GP-signal review](../reports/resumed-upstream-observer-actual-GP-signal-independent-review.json) agree on the authenticated actual70-to73-year probe. Raw route-versus-company GP changes disagree in10/40,10/40 and11/40 aligned comparisons; only9,6 and7 occur in ordinary positive-sales decisions where GP selects direction. All8 single-route raw firms and all1,000 single-route refineries agree perseed. The other differences use scarcity or zero-sales branches. All floor-change/clipping flags are zero over this probe. T1 steps finish at the minimum in54–57% of decisions; scarcity overrides account for their small net quote increases while ordinary GP-following decisions move quotes down overall. These phased decision snapshots do not reproduce long-run drift across every seed, independently replay invoices, or establish the benefit of alternative prices.

Root has [selected one experimental hypothesis](../reports/annual-v8-whole-firm-gp-root-hypothesis-selection.json): each product judges its price experiment using signed whole-firm sold-cost GP over that product's own window. The [V8 protocol](../reports/calibration-protocol-annual-v8-whole-firm-gp.json) applies a common firm objective across alltiers; Tier2 is a source-based extension beyond observed raw-firm signals. Existing route calendars, reset dates, quantities, traffic, costs, shared constraints, paid additions and all64 candidate settings stay fixed. Old own-route GP checkpoints cannot become new company-GP histories. The [direct mechanics](../reports/whole-firm-gp-mechanics-native-handback.json) pass10 constructed checks with no Workers or actual ticks, and [all42 inherited contracts](../reports/annual-v8-whole-firm-gp-quality42-native-handback.json) pass on the copied runtime. The [source package](../reports/calibration-runtime-annual-v8-whole-firm-gp-source.json) preserves209 source/test/metadata files. The [final independent package review](../reports/resumed-annual-v8-whole-firm-gp-final-package-independent-review.json) and [Root prelaunch checks](../reports/annual-v8-whole-firm-gp-root-prelaunch-gate.json) pass. The [three fresh3,600-tick matched diagnostics](../reports/planned-annual-v8-whole-firm-gp.json) were [genuinely launched](../reports/annual-v8-whole-firm-gp-launch-binding.json) alongside the original Age runs. Allthree diagnostics [completed3,600 actual ticks with genuine native exit zero](../reports/annual-v8-whole-firm-gp-completion-binding.json), with allten annual dates, populations, sources and64settings checked. The [completed evidence descriptor](../reports/annual-v8-whole-firm-gp-completed-evidence.json) binds the actual outputs. The [strict actual paired comparison](../reports/annual-v8-whole-firm-gp-actual-paired-comparison-native-handback.json), [independent full-company arithmetic](../reports/resumed-annual-v8-endpoint-independent-audit-native-handback.json) and [all657-cohort economic interpretation](../reports/resumed-annual-v8-independent-economic-interpretation-native-handback.json) completed with genuine native exit zero. The [passive comparison tool](../reports/calibration-whole-firm-gp-comparator-preparation.json) has [independent source review](../reports/resumed-annual-v8-whole-firm-gp-comparator-independent-review.json), with117 rejection cases and12 positive cases passing. It requires genuine completion from allthree native runs before reading endpoints; the actual comparison and independent endpoint audit now pass. No extra Age trial is authorized automatically, and no standard or fairness cure is selected.

## Completed whole-firm GP outcome

The [Root disposition](../reports/annual-v8-whole-firm-gp-root-completed-outcome-disposition.json) is **HOLD / experimental and unselected**. Tier2 mean ten-year gains rise about0.8percent relative to controls, and narrow portfolios improve. Its cumulative gain p10 falls5.8-6.9percent, final-year income p10 falls14.3-17.8percent, and companies ending with at least a year without sales rise551→727,536→752 and540→757. Width4/standalone gain gaps remain18.8-33.5percent; final-year income gaps are37.4-49.4percent. Product-membership disparities worsen while sector averages remain close. Tier1 gains fall versus controls in allthree seeds; this does not mean its V8 income falls absolutely between years1 and10.

Raw standalone/width4 gain ratios remain2.56-2.82. Raw minimum book assets exceed every refinery/final firm, while the weakest raw firm earns6.9-7.5k versus a final-firm maximum20.1-24.9k. All firms have positive cumulative earned profit at this completed diagnostic endpoint; no future profit guarantee follows. The common first360 observation already shows raw width gaps, while final-tier widths are initially within about2percent. Annual individual equity and endpoint accumulated cash/sales do not supply missing intrayear histories.

The [market review and visually checked actual figures](../reports/resumed-annual-v8-independent-market-findings-and-figure-review.json) explain the raw-price/refinery-cost transfer and retain all10 actual annual dates across allthree seeds. Final gross margin remains near50.2percent, use near19.9percent, invoice-demand fill99.995percent and latent-need fill about71.7percent. The [two-page figure](../reports/resumed-annual-v8-whole-firm-gp-actual-panels.pdf) is available and queued for display in the app. A lean passive raw-width stock/quote/forecast/shared-capacity/discovery census follows; no next policy or profile is selected and no V8 Age is automatically launched.

## Raw wholesale-lot readiness hypothesis

The [six actual endpoint census](../reports/resumed-annual-v6-v8-raw-width-endpoint-census.json) and [physical findings](../reports/resumed-annual-v6-v8-raw-width-physical-findings.json) show that all twelve width-four firm endpoints used their full 10,000-unit production budget, while four to six of their eight routes per arm still held fewer than 1,000 units before purchases. These routes produced positive quantities: this differs from the previously repaired zero-quantum defect. Cumulative wide-firm utilization was roughly 40–48 percent versus 85–88 percent for mono firms. Closing targets are diagnostics, not reconstructed historical production budgets. The physical report separately verifies that the observed opening stock gaps could fit the retained opening cash, capacity and warehouse budgets. These observations support a refutable availability hypothesis; they do not establish its historical causal contribution.

The [root hypothesis selection](../reports/annual-v9-raw-lot-readiness-root-hypothesis-selection.json) chooses one experimental scheduling change from V6. After inherited unit-quantum protection, complete missing wholesale-lot stock only when all eligible routes can be funded together under existing targets, shared capacity, storage and exact cash clamps. Otherwise retain the original allocator. One positive route bypasses this block. No target, capital, demand, quote, profit or physical ceiling is granted. The [prospective protocol](../reports/calibration-protocol-annual-v9-raw-lot-readiness.json) retains all twenty core declarations and the three full 64-field configurations.

Nine constructed mechanics groups passed with 932 direct production calls, zero Worker calls and zero simulation ticks. All 42 inherited checks passed in one complete native rerun. Two production fixtures have separately reviewed allocation expectations for the intended rule; two already-stocked proportional controls preserve the inherited behavior. All accounting and calibration bounds remain unchanged. All three zero-tick, full-population opening comparisons passed with identical 64-field configurations, acquisition books, catalogue, portfolios, 159 World fields and 33 closure fields. The initial fixture and metadata failures remain preserved with their corrections.

The [frozen source package](../reports/calibration-runtime-annual-v9-raw-lot-readiness-source.json) and [independent final review](../reports/resumed-annual-v9-raw-lot-readiness-final-package-independent-review.json) pass. Root [genuinely launched three fresh ten-year diagnostics](../reports/annual-v9-raw-lot-readiness-launch-binding.json) against the preserved V6 controls, alongside the original Age runs. All three [completed 3,600 actual ticks with native exit zero](../reports/annual-v9-raw-lot-readiness-completion-binding.json), retaining the twelve source files, three full configurations, populations and ten annual dates. The [completed descriptor](../reports/annual-v9-raw-lot-readiness-completed-evidence.json) binds all real outputs. The [single passive auditor](../spec/calibration_raw_lot_readiness_audit.md) has [independent source review](../reports/resumed-annual-v9-raw-lot-readiness-auditor-independent-source-review.json), with 21 positive and 80 negative constructed cases. The [actual six-endpoint audit](../reports/annual-v9-raw-lot-readiness-actual-audit-native-handback.json) completed with genuine native exit zero. All company books, unchanged accounting guards, ten annual vectors and 657 opening cohorts per seed pass; the [independent saved-output accounting review](../reports/resumed-annual-v9-saved-audit-accounting-review.json) also passes. The economic disposition below remains separate from accounting validity. The production change can alter first-year outcomes; only opening opportunity and configuration identities must match. No automatic V9 Age launch, standard adoption or final fairness result is claimed.

## Actual 240-year drift

The [actual 240-year readout](../reports/resumed-selected-v6-actual240-tier-trajectory-readout.json), its [native handback](../reports/resumed-selected-v6-actual240-readout-native-handback.json) and [independent arithmetic review](../reports/resumed-selected-v6-actual240-independent-arithmetic-review.json) verify all 720 observed annual rows and 2,160 tier records. Tier 0/Tier 1 cumulative percentage-gain ratios at year 240 are 1.562, 1.793 and 1.275 across the three seeds, versus 1.332, 1.532 and 1.148 at year 120. Mean annual Tier 0 income rises 16.1–24.0 percent between the first and second 120-year blocks; Tier 1 income falls 5.3–10.8 percent and Tier 2 income falls about 2.1 percent. Capital weighting preserves the divergence. Individual windows are not uniformly monotonic.

The [actual figure](../reports/resumed-selected-v6-actual240-tier-trajectories.pdf) shows the observed cumulative returns and trailing ten-year income through exactly 86,400 ticks. These saved annual tier summaries do not reconstruct individual annual cash, sales or quote paths, forecast year 480, or establish doubling. Live jobs have subsequently reached later observations; those are recorded separately in the current requirement audit.

## Completed raw-lot readiness outcome and next diagnostic

The [Root V9 disposition](../reports/annual-v9-raw-lot-readiness-root-completed-outcome-disposition.json) is **HOLD / experimental and unselected**. The [actual physical market findings](../reports/resumed-annual-v9-independent-market-physical-findings.json) confirm that pre-purchase raw routes holding less than one wholesale lot fall from 16/9/18 to zero in all three endpoints. Width-four cumulative raw utilization rises to 50.3–55.2 percent. This fixes the observed endpoint availability symptom, without establishing historical causal completeness or comparable returns.

The [all-cohort economic findings](../reports/resumed-annual-v9-raw-lot-readiness-economic-findings.json) retain raw mono/four-product percentage-gain ratios of 2.07–2.42. Final-tier four-product/mono gain ratios remain 1.37–1.41; their final-year income ratios are 1.50–1.83. Mono final-firm ending one-year sales droughts worsen in all three seeds, and their mean cumulative completed-tick minimum cash falls. Tier 1 cumulative material ranges improve to 6.9–8.9 percent, while final-year material-income ranges remain 18.3–30.3 percent. Mixed lower-tail and cross-seed results prevent selection. Tiny cohorts, overlapping product membership, annual observed drawdowns and completed-tick cash minima retain their stated interpretation limits.

Final-year gross margins remain about 24.3–24.5 percent for raw goods, 34.4–34.5 percent for processed goods and 49.7 percent for final goods. Raw utilization is about 80 percent and final factory utilization about 20 percent. Final-year invoice-request fill is about 99.997 percent, while fulfillment of latent need is about 72 percent; price-suppressed need is included only in the latter denominator. Cumulative ten-year fill includes opening buildup and is not a final-year deterioration claim. The [actual six-panel figure](../reports/resumed-annual-v9-raw-lot-readiness-economic-figure-revision2.pdf) has [independent visual review](../reports/resumed-annual-v9-economic-figure-independent-visual-review.json); Root also inspected its PNG. No actual Age or disruption result for V9 follows from this diagnostic.

Root [selected preparation of V10](../reports/annual-v10-zero-adaptive-quotes-root-hypothesis-selection.json), a zero multiplicative price-adjustment control on the exact unchanged V9 runtime. Its [separate protocol](../reports/calibration-protocol-annual-v10-zero-adaptive-quotes.json) and [paired plan](../reports/planned-annual-v10-zero-adaptive-quotes.json) declare only k=.35→0, preserving all other 63 full configuration fields and existing acceptance bounds. This removes GP-driven, scarcity and stocked-idle multiplicative quote steps across all tiers together; cost/held-basis/minimum reservations, raised posted quotes, learner state/calendar, clearing and physical rules remain. It measures their combined effect with market spillovers, not a GP-only effect or a static-price standard. Focused mechanics, six actual zero-tick opening initializations, independent review and unchanged-source quality binding precede any Root dispatch. Source inspection additionally predicts exact actual first360 company-equity vector equality: learning ages are tested before end-of-tick accumulation, so k cannot enter a price decision in ticks1–360. This concrete prediction will be checked against actual native V9 controls; later annual outcomes can differ. The initial protocol/plan revision is preserved with its corrected native-control provenance sentence. All preparation gates now pass: 13 direct cases/26 production-model calls, exactly six actual full-population zero-tick initializations, all 159 World fields and 33 captured closure fields compared with only state.cfg.k different, current inherited 145 input/source bindings and independent source/proof reviews. The [compact source manifest](../reports/calibration-runtime-annual-v10-zero-adaptive-quotes-source.json) explicitly reuses the unchanged V9 archive; new declarations/profiles/proofs are separately bound. Root [authorized exactly three treatments](../reports/annual-v10-zero-adaptive-quotes-root-prelaunch.json) and [genuinely launched them](../reports/annual-v10-zero-adaptive-quotes-launch-binding.json). Their actual startup headers match all64 settings, start at tick0 and request3600 actual ticks. All three treatments [completed 3,600 actual ticks with genuine native exit zero](../reports/annual-v10-zero-adaptive-quotes-completion-binding.json). Their [completed descriptor](../reports/annual-v10-zero-adaptive-quotes-completed-evidence.json) binds the native V9 controls and V10 outputs. The [single actual passive six-endpoint audit](../reports/annual-v10-zero-adaptive-quotes-actual-audit-native-handback.json) completed with genuine native exit zero in 520.33 seconds, with six real checkpoint decodes and zero Worker/stage calls or added simulation ticks. All 62,970 company books, 657 opening cohorts, ten annual vectors per arm and unchanged physical/cash/source guards pass. All three first360 company-equity vectors are byte-identical to their native V9 controls, confirming the source prediction. The [saved-output accounting review](../reports/resumed-annual-v10-saved-audit-accounting-review-native-handback.json), [all-cohort economic interpretation](../reports/resumed-annual-v10-zero-adaptive-quotes-economic-findings-native-handback.json) and [independent physical market interpretation](../reports/resumed-annual-v10-independent-market-findings-native-handback.json) completed with genuine native zero. Root [holds V10 as experimental and unselected](../reports/annual-v10-zero-adaptive-quotes-root-completed-outcome-disposition.json); no automatic new Age or default adoption follows.

The [main application adoption-gap review](../reports/resumed-current-application-adoption-gap-audit.json) separates outstanding economic integration from reporting correctness. The [main Tier 0 reporting correction](../reports/main-tier0-reporting-correction.json) now shows sold-acquisition-cost COGS and signed gross profit, with extraction spending and operating cash flow separately in worker summaries, company views and histories. Six focused checks and paired stock-build, depletion and cost-shock fixtures passed. Model, kernel, economic defaults and initialization remain byte-unchanged. The [independent integration review](../reports/resumed-main-tier0-reporting-independent-integration-review.json) passes the exact diff, accounting bridges, saved focused native checks and source/UI/doc coherence. No experimental economic profile is adopted by this reporting fix.

## Completed zero-amplitude outcome and isolated buffer preparation

V10 reduces final-tier width-four/mono cumulative gain ratios to 1.009–1.019, removes observed ending one/two/five-year final sales droughts, and reduces refinery material mean-return ranges below 0.36 percent. Raw width-four/mono gains deteriorate to 0.139–0.169 and their final-year income to 0.053–0.073 of mono income. Wide raw cumulative utilization is only 13.4–16.4 percent, while mono use is about 96.8 percent and aggregate raw use remains about 80 percent. Raw pooled contribution per sold unit is almost equal: aggregate use and one terminal ready lot hide the distribution of sales. Individual standalone recipe and raw-composition cohorts retain repeated disparities. Small cohorts and overlapping membership remain explicit limitations.

Final-year margin/use remain about 50/20 percent. Cumulative requested and latent physical-unit fill improve slightly; Year10 requested fill improves but latent fill declines by about 0.0145–0.0189 percentage points. The [actual six-panel figure](../reports/resumed-annual-v10-zero-adaptive-quotes-economic-figure.pdf) has author/peer visual checks and Root inspected its PNG. Source inspection shows k0 incumbent bot quotes can rise to reservations but cannot fall merely when costs restore. That is a source-only recovery limit; no V10 cost shock or actual Age was run.

The [next controlled preparation](../reports/annual-v11-raw-lot-safety-buffer-root-hypothesis-selection.json) isolates one additional wholesale lot in every raw route target: `Tnew = min(targetInventory / width, maxInventory / width, Told + minWholesaleLot)`. The [V11 protocol](../reports/calibration-protocol-annual-v11-raw-lot-safety-buffer.json) and [paired plan](../reports/planned-annual-v11-raw-lot-safety-buffer.json) keep all64 V10 k0 settings, books, populations and acceptance unchanged. Only the target expression changes in a separate copied kernel; extra inventory must be produced and paid under existing cash, 10k shared capacity, 500k target and 1m warehouse bounds. This tests intermittent-order availability/retention, with no promised clients or comparable profits. Initialization already saturates raw target ceilings, so zero-tick opening targets should match; actual first-year outcomes need not. Direct mechanics, applicable current quality and independent source review precede exactly three paired zero-tick comparisons (six initializations) and any Root treatment dispatch. No V11 actual treatment or extra Age is launched yet.

The [constructed raw-buffer mechanics](../reports/raw-lot-safety-buffer-mechanics-native-handback.json) passed eight groups with 630 direct production calls and zero actual simulation ticks. The [independent source/mechanics review](../reports/resumed-annual-v11-raw-lot-safety-buffer-independent-source-mechanics-review.json) passes the exact two-expression kernel diff, unchanged other eleven inputs, all 64 profiles and the prepared zero-tick helper. The [complete untouched quality attempt](../reports/v11-quality42-complete-unchanged-attempt.json) exercised all 42 checks: 40 passed, while two retained old target/allocation expectations. The [narrow fixture proposal](../reports/v11-quality-fixture-adaptations-proposal.json) preserves real cash/basis, shared limits and all numerical tolerances, including true one/two-unit deficit cases. It remains separately reviewed before a fresh complete quality run; no current 42-pass or actual opening result is claimed.

The [independent fixture review](../reports/resumed-annual-v11-quality-fixture-adaptations-independent-review.json) passed before a separately copied [full 42-check native run](../reports/annual-v11-raw-lot-safety-buffer-quality42-native-handback.json), which completed with exit zero. All 145 quality inputs remained unchanged; exactly the two reviewed fixtures differ from the preserved original runtime, while all twelve runtime/UI/instrument sources and the other 143 inputs match. The [actual opening proof](../reports/annual-v11-raw-lot-safety-buffer-startup-opening-audit-native-handback.json) then passed exactly six fresh full-population initializations with zero economic ticks, matching every World and captured closure field, all 64 configurations and all opening acquisition books. The [compact frozen source package](../reports/calibration-runtime-annual-v11-raw-lot-safety-buffer-source.json) contains 183 explicitly bound source/proof/quality members in a 565,228-byte archive. Independent package review and separate Root three-treatment dispatch remain pending; no actual V11 treatment, completed Age or standard is claimed. The [current Age observation](../reports/annual-v11-quality-current-age-observation.json) records durable year 350 and logged years 356–357 for the three original V6 runs, all still incomplete.

The [independent final package review](../reports/resumed-annual-v11-raw-lot-safety-buffer-final-package-independent-review.json) passed the frozen archive, profiles, real quality/startup records, native V10 controls and all 18 absent future outputs. Root [authorized exactly three treatments](../reports/annual-v11-raw-lot-safety-buffer-root-prelaunch.json) and [genuinely launched them](../reports/annual-v11-raw-lot-safety-buffer-launch-binding.json) at seeds 12345, 24680 and 31415. Every actual native startup header matches its full 64-field configuration and runtime/instrument fingerprints, starts at tick zero and requests 3,600 actual ticks. Node/time identities are mapped by live parent PIDs and each stdout log descriptor. Genuine completion, all company/cohort/annual accounting and economic suitability remain pending; no new Age, main economic parameters or standard has been adopted.

The [paired auditor source review](../reports/resumed-annual-v11-endpoint-auditor-independent-source-review.json) passes all nine inherited arithmetic bodies, concrete source/startup gates, both native history checksum domains and unchanged monetary/physical bounds. Its 33 positive and 176 rejection fixtures remain distinct from actual outcomes. Separately prepared [economic](../reports/resumed-annual-v11-economic-findings-independent-source-review.json) and [market](../reports/resumed-annual-v11-market-interpreter-independent-source-review.json) interpreters have independent source review; unknown actual input pins still prevent their main readers from running. The [current native observation](../reports/annual-v11-current-native-progress-after-launch.json) records the three buffer treatments at two actual years, and original Ages at durable year 360 with logged years 367–368. No actual V11 paired accounting or economic verdict is produced yet.

All three V11 treatments [completed 3,600 actual ticks with genuine native exit zero](../reports/annual-v11-raw-lot-safety-buffer-completion-binding.json), retaining all 64 settings, twelve sources, full populations and ten real annual dates. The [completed descriptor](../reports/annual-v11-raw-lot-safety-buffer-completed-evidence.json) binds all native V10 control and V11 treatment outputs. Root [launched the single passive six-endpoint auditor](../reports/annual-v11-raw-lot-safety-buffer-actual-audit-launch-binding.json) with the exact independently reviewed helper. Its final native outcome, all company/cohort/annual accounting and economic interpretation remain pending. This reader advances no simulation ticks; the three original Ages continue. No V11 Age or standard is adopted.

At the 4 October 10:32 UTC observation, the original three V6 Ages have durable **390-year / 140,400-tick** states and emitted **392 / 392 / 393** complete annual rows, with no observed validation failures. The [current native observation](../reports/annual-v11-actual-audit-completed-current-age-observation.json) records the three continuing processes. All three V11 buffer treatments and the [single passive six-endpoint accounting audit](../reports/annual-v11-raw-lot-safety-buffer-actual-audit-native-handback.json) completed with genuine native exit zero. The [saved economic interpretation](../reports/annual-v11-raw-lot-safety-buffer-economic-native-handback.json) also completed native zero; Root captured its own source and all 17 declared inputs before and after, with exact equality. Independent outcome reviews and Root economic disposition remain pending. These ten-year results do not certify an Age or adopt parameters.

V11 has a [completed Root HOLD disposition](../reports/annual-v11-raw-lot-safety-buffer-root-completed-outcome-disposition.json). The buffer raises wide raw gains and reduces the lower-tail disparity, but width4/mono cumulative gain remains **0.357–0.527** and final-year income **0.142–0.242**. Raw tier gains remain roughly **1.55%**, against **2.07%** downstream. All annual raw delivered units and downstream demand/outcomes remain unchanged; this is a real redistribution, not aggregate demand relief. [Independent economic](../reports/resumed-annual-v11-independent-economic-assessment-native-handback.json) and [market](../reports/resumed-annual-v11-market-readout-native-handback.json) reviews preserve all657 cohort diagnostics, small-N limits and pricing restoration caveats. The actual figure passed author, independent and Root PNG visual checks. No selected economic standard or additional Age is authorized.

One [V12 capacity/coverage hypothesis](../reports/annual-v12-capacity-coverage-raw-buffer-root-hypothesis-selection.json) is selected for controlled preparation only. It retains the V11 paid safety lot and adds a stock minimum based on existing nameplate capacity and three-tick coverage, capped by the existing shared target/warehouse limits. All64 profiles stay identical. This intends30000 units of company stock coverage at the selected values, divided over routes; actual stock still requires paid production. Source, mechanics, quality, six actual opening comparisons and final package gates precede any three fresh3600-tick treatments. The 10:53 UTC [original-Age observation](../reports/annual-v12-preparation-current-age-observation.json) records durable **400years/144000ticks** and emitted **402/403/404** annual dates, still incomplete and without observed validation failures.

## V12 preparation — source/mechanics reviewed, final quality active

The separate capacity/coverage raw buffer changes only the two target-expression lines in the copied kernel, retains the V11 extra lot, and leaves all 64 settings per seed unchanged. Independent source/mechanics review passes. Its 647 direct production-stage checks are constructed evidence, with zero Workers or actual simulation ticks. A metadata-only correction points the current parent projection at genuine V11 controls; original declarations and source reviews are preserved.

The first unchanged quality attempt exercised all 42 checks once: 40 passed and two fixtures retained old target expectations. The exact two-fixture adaptation was independently reviewed, including a later hidden narrow-route expectation. One complete registry is now active in a separate final test copy with the same kernel; no pass is claimed yet. Six actual full-population opening comparisons, final freeze and market treatments remain pending. No standard or application default is adopted. The original three V6 Ages are durably at 410 years; emitted annual rows were 415/416/416 at the recorded observation, with no observed validation failure and no native completion.

[Exact fixture and startup-pin review](../reports/resumed-annual-v12-quality-adaptation-and-startup-pins-revision-independent-review.json), [final quality prelaunch](../reports/v12-quality42-final-prelaunch.json), [actual Age observation](../reports/annual-v12-current-age-observation-before-final-quality.json).

## V12 actual diagnostic launch — historical launch observation

Exactly three fresh full-population V12 treatments now run for 3,600 actual ticks at seeds 12345, 24680 and 31415. The complete copied 42-check registry passed with native exit zero and all 145 inputs unchanged. Six actual full-population normal zero-tick initializations produced exact 159-field World, 33-field captured-closure, all64 configuration and opening-book equality; all120 opening raw target comparisons agree. The only excluded comparison is the separately checked source-fingerprint envelope. The exact frozen 204-member source package passed independent review before dispatch. Actual startup headers match all64 parameters and three runtime/seven instrument hashes, and live PIDs are linked to each native stdout log.

The prospective passive auditor now binds the real final receipts. Its first prepared-source attempt found only absolute-versus-relative receipt path spelling; original failure remains. The separately reviewed equivalent-path guard retains exact map/receipt keys, resolved paths, SHA and byte sizes. One changed-source suite passes native0 (41 positives/189 rejections,60 captured inputs unchanged), including five constructed deserializations and zero real economic endpoints. No actual ten-year accounting or economic result is claimed yet. V12 retains the k0 quote-restoration limit and does not authorize an Age or standard adoption.

The original three V6 Ages have durable430-year checkpoints and emitted434/434/435 annual rows at the latest saved observation, with no recorded validation failure and no completed Age. All six native jobs continue. The existing commit-evidence curation plan was updated; no files are staged or newly committed.

[Actual native launch binding](../reports/annual-v12-capacity-coverage-raw-buffer-launch-binding.json), [independent final package review](../reports/resumed-annual-v12-final-package-independent-review.json), [startup native proof](../reports/annual-v12-capacity-coverage-raw-buffer-startup-opening-audit-native-handback.json), [current native observation](../reports/annual-v12-current-original-age-and-treatment-observation.json).

## V12 native completion and passive audit — historical running observation

All three fresh V12 capacity/coverage treatments [completed 3,600 actual ticks with genuine native exit zero](../reports/annual-v12-capacity-coverage-raw-buffer-completion-binding.json), with final native tool receipts `6aafe5`, `613909` and `35bfaa`. The [completed descriptor](../reports/annual-v12-capacity-coverage-raw-buffer-completed-evidence.json) binds the three genuine V11 native controls and V12 treatment outputs under the unchanged full64 profiles. Root [preflighted](../reports/annual-v12-capacity-coverage-raw-buffer-actual-audit-root-prelaunch.json) and [launched one actual six-endpoint revision3 passive audit](../reports/annual-v12-capacity-coverage-raw-buffer-actual-audit-launch-binding.json), session62813/Node47332/time47331/initialtool0963ac, after the [independent final source/constructed-validation review](../reports/resumed-annual-v12-auditor-revision3-validation-independent-review.json). At the targeted process observation the reader is running; its native completion, accounting, all657 cohort/annual and economic verdicts remain **pending**. No audit pass is inferred from completed trial processes. No treatment producer outcome, checkpoint or sidecar was opened for this status update.

The [bounded current observation](../reports/annual-v12-native-completion-audit-running-current-status-observation.json) distinguishes progress-declared durable **440years/158400ticks** in each original V6 Age from later emitted **444/445/445** complete annual rows. It reads only scalar progress metadata, each last512KiB native-log tail and targeted process records. No observed validation failure or native Age completion is recorded. The only active Node processes in this observation are the three original Ages3182/3186/3194 and passive audit47332; completed V12 treatment PIDs are absent. The earlier430-year/launch observation above is historical and preserved. Actual480-year evidence, final compatible disturbance gates, standard selection and economic/default adoption remain unfinished.

The [one-field reservation-coordinate source assessment](../reports/unselected-last-reservation-delta-quote-coordinate-assessment.json) and [independent source assessment](../reports/unselected-last-reservation-anchor-independent-source-assessment.json) are source reasoning without outcome validation. Their anchor preserves nonnegative absolute dollar surplus rather than percentage markup; exact birth floors, full manual reservation tracking, before-calendar price aliasing, actual posted-price stability, zero-time configuration/controller semantics and new fresh save/load guards are required. Held/last costs and endogenous replacement quotes can delay restoration, while profit windows retain quantity/shared-resource confounding. Neither assessment establishes a fairness remedy, authorizes economic execution or selects a standard.

## V12 completed disposition and V13 preparation — historical 13:09 observation

The three fresh V12 treatments completed **3,600 actual ticks** with native exit zero (`6aafe5`, `613909`, `35bfaa`). The [actual six-endpoint accounting audit](../reports/annual-v12-capacity-coverage-raw-buffer-actual-audit-native-handback.json) also completed native zero: all 62,970 company books in each arm, all 657 fixed-opening cohorts and ten annual paths pass the original bounds. The [saved accounting review](../reports/resumed-annual-v12-saved-audit-accounting-independent-review.json), [economic findings/native receipt](../reports/annual-v12-capacity-coverage-raw-buffer-economic-interpretation-native-handback.json), [independent economic assessment](../reports/resumed-annual-v12-independent-economic-assessment.json), [market readout](../reports/resumed-annual-v12-independent-market-physical-readout.json) and [PNG visual QA](../reports/resumed-annual-v12-economic-figure-independent-visual-qa.json) are complete. PDF metadata is bound; no independent PDF rendering is claimed. No V12 treatment or passive reader remains on the current live-process list.

Root's [completed disposition](../reports/annual-v12-capacity-coverage-raw-buffer-root-completed-outcome-disposition.json) is **HOLD** for economic standard selection, while retaining the paid physical buffer as a provisional experimental baseline. Raw width maximum/minimum ten-year gain gaps improve to **8.48% / 7.14% / 8.87%**, but Year 10 income gaps remain **10.56% / 9.65% / 15.40%**; repeated same-pair gaps exceed the unchanged 10% diagnostic. Raw tier percentage gains remain below downstream gains. All 644 recorded nonraw cohort paths and their market flows are unchanged. These are actual ten-year results, with small raw cohorts and overlapping recipe memberships; they do not certify an Age, shock recovery or a standard.

At the [saved 2026-10-04 13:09:08 UTC observation](../reports/annual-v12-completed-and-original-v6-age-observation-before-root-disposition.json), the **only three original Age processes** are 3182 / 3186 / 3194. Each has a progress-declared durable **460 years / 165,600 ticks**, separately from **465 / 465 / 466** emitted annual rows. All remain incomplete, without an observed validation failure or native completion. This update did not poll those sessions, progress files, logs or processes. Later unsaved progress is not substituted for this receipt. The earlier audit-running entry is preserved above as history.

The [V13 reservation-delta selection](../reports/annual-v13-reservation-delta-bot-quotes-root-hypothesis-selection.json) authorizes preparation of one separate source hypothesis. Its [prototype](../reports/drafts/v13-reservation-delta-bot-quotes/source-preparation.json) changes only kernel and worker; the other ten files and all 64 profile fields remain exact. The [Root independent source review](../reports/resumed-annual-v13-reservation-delta-prototype-root-independent-source-review.json) passes. Root has now authorized **one bounded direct mechanics suite with at most three reduced fresh initializations**, under the [mechanics plan](../reports/v13-reservation-delta-direct-mechanics-plan.json). Its result is not yet completed in this status record. No full quality, six full-population startup, ten-year trial, shock or Age is authorized or completed by this source review. Reservation anchoring preserves dollar surplus, subject to full floors and held-cost memory; it does not promise constant percentage markup, profit or fairness. Fresh reservation-memory persistence and manual/controller semantics still require mechanics.

All **seven original requirements remain unfinished or partial**. Original acceptance, actual 480-year/three-seed evidence, final compatible disturbance evidence, final standard/default adoption and the review commit remain outstanding. No governing requirement, immutable runtime/declaration, original handoff or application default changed in this status correction.
## Three actual Age completions and V13 mechanics — historical reader-running observation

Root's [genuine completion/prelaunch receipt](../reports/annual-v6-three-age-genuine-native-completion-and-actual-reader-prelaunch.json), written **2026-10-04 13:39:41 UTC**, establishes all three original V6 fresh **0–172,800-tick / 480-year** producers completed with native exit zero (`705afc`, `db3ee0`, `1fc4ec`). No Age producer or V12 treatment/accounting process remains live in the current record. The earlier 13:09 incomplete observation is preserved above and in the JSON chronology.

The only current passive reader is the unchanged prepared full-Age analyzer, [launched by Root](../reports/annual-v6-full-age-fairness-actual-audit-launch-binding.json) with initial native tool `8762cc`, session **77471**, Node **50616** and time parent **50615**. The saved launch observation records it running at **13:43:39 UTC**; this documentation update did not poll it, read its output or decode any producer data. Accounting, all-company/cohort fairness and economic acceptance remain **pending**. A completed experimental horizon is distinct from accepted 480-year calibration or selected-standard validation.

V13's [reduced direct mechanics](../reports/reservation-delta-quote-mechanics.json) completed with [genuine native exit zero](../reports/reservation-delta-quote-mechanics-native-handback.json) and [independent passive review](../reports/resumed-annual-v13-reservation-delta-mechanics-independent-review.json): **eight groups, 1,217 direct helper calls, 13 external economic stage calls**, three successful reduced fresh initializations plus two preserved failed-attempt initializations (**five total**), and **zero Worker steps, kernel ticks or actual ticks**. The precisely checked additional reduced `stateBytes` telemetry is **81,280 bytes** for the three new reservation arrays; the remaining declared opening economic fields are exact. These constructed mechanics do not establish a treatment outcome or fairness.

A separate [prospective copied runtime preparation](../reports/annual-v13-reservation-delta-bot-quotes-source-preparation.json), [protocol](../reports/calibration-protocol-annual-v13-reservation-delta-bot-quotes.json) and [plan](../reports/planned-annual-v13-reservation-delta-bot-quotes.json) now exist. Their execution flags remain false. Root package review/freeze, full quality, six full-population zero-tick openings and actual treatment trials remain pending. The source-derived **2,063,040-byte** full-population reservation-memory delta must be proved by those future openings. No accepted old-state import/backfill, application default change or automatic Age is established.

All **seven original requirements remain partial or incomplete**. Completed V12 retains its economic **HOLD** disposition. Pending actual full-Age accounting/economics, final compatible standard disturbance evidence, standard/default adoption and the review commit remain outstanding; this update changes status only.
## Final handoff status — 4 October 2026

Calibration work is **stopped at the human's request for a new chat**. All experiment, simulation and audit processes are closed. This status update launches nothing and changes no runtime, fixture, profile, application default or acceptance criterion. Prior status bytes and dated chronology are preserved; the original handoff remains untouched.

All three original V6 fresh **0–172,800-tick / 480-year** producers completed native zero. The unchanged full-Age reader also completed native zero (`f20d71`), as did both [independent saved-evidence](../reports/resumed-annual-v6-full-age-saved-evidence-independent-native-handback.json) and [market/physical](../reports/resumed-annual-v6-full-age-market-physical-independent-readout-native-handback.json) reviews. Provenance and real acquisition-book accounting pass the original bounds across all 62,970 companies, all 657 opening cohorts, 130 additional observed direction cohorts and 480 annual dates per seed. No raw World/history replay or analyzer rerun was needed for those independent reviews.

Economic/fairness acceptance is **FAIL/HOLD**. The declared mean-equity band remains **1.9–2.1**: raw equal-company multiples range **2.4720–2.8127**, T1 **1.8084–1.8987** (capital-weighted **1.7868–1.8850**), and T2 **1.9503–1.9518**. T2's tier mean passes while the all-tier objective fails. The exact **226 repeated starting-choice flags** and **eight initial-direction flags** remain; T2 wide/mono cumulative gain gaps are about **37–38%**. Small raw cohorts, one-firm standalone recipes and overlapping memberships limit interpretation; these are observational associations, not causal policy proofs. Books and earned-dollar profit are separate, including seed24680's failure of raw minimum earned profit above every T2 firm. The completed original candidate Age is not an accepted selected-standard Age.

V13's **eight reduced direct mechanics groups** and [independent review](../reports/resumed-annual-v13-reservation-delta-mechanics-independent-review.json) are complete: 1,217 helper calls, 13 external stages, three successful plus two preserved failed initializations (**five total**), and zero actual ticks. Its [first ordinary unchanged quality42 attempt](../reports/v13-quality42-unchanged-native-handback.json) closed **FAILED** at check6 (`potential_demand`): **five passes, one failure and 36 unexecuted checks**. A [two-fixture correction proposal](../reports/drafts/v13-reservation-coordinate-quality-fixture-proposal/proposal.json) and [exact diff](../reports/drafts/v13-reservation-coordinate-quality-fixture-proposal/fixture-proposal.diff) are saved **source-only, unapplied and unrun**. No full42 pass, full-population opening, V13 treatment trial, shock or Age is claimed. Further execution requires a resumed task and the outstanding review/gates; it is not authorized by this handoff.

All **seven original requirements remain unfinished or partial**. Achievements include complete original experimental Age evidence, exact accounting and long-run fairness/drift diagnosis, completed controlled ten-year comparisons through V12 and reviewed V13 source/reduced mechanics. Remaining work includes resolving economic disparities, any separately authorized V13 fixture/QC/opening/trial gates, actual Age and compatible disturbance evidence for a selected standard, coherent UI/spec/default adoption, final review and commit. No standard was adopted and no overall goal completion is claimed.
