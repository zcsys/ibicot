# Calibration scope — first principles

This is the canonical statement of what the economy calibration is, what it may
and may not touch, and how success is judged. It supersedes the accumulated
experiment notes; those are history, not rules.

## Objective

Make the **bot-run economy** (no players, no ownership layer) reach a defensible
outcome: standard bots in every tier earn **comparable percentage returns** and
roughly **double their simulation-opening book equity over one Age**
(one Age = 24 Generations / 480 years / 172,800 ticks), while the individual-company hierarchy
and every accounting invariant hold.

## First principles (non-negotiable invariants)

1. **Fixed structure.** 20 Tier 0 / 1,000 Tier 1 / 61,950 Tier 2 firms; one
   million external buyers; 420 distinct recipes (200 active, 220 reserved);
   2/6/12 C-3/C-4/C-5 active products per sector. These counts are never
   changed to make returns look correct.
2. **Fixed capital.** Opening book equity is $1,000,000 per Tier 0 firm,
   $20,000/$80,000 per basic/compound Tier 1 firm, and $1,000 per Tier 2 route
   plus $2,500 working cash ($3,500–$6,500 for one to four routes).
   Per-company: **Tier 0 > Tier 1 > Tier 2**. In aggregate: **Tier 2 > Tier 1 >
   Tier 0**, purely from company counts.
3. **Book accounting.** Equity = cash + owned machinery + acquisition-basis
   inventory. Unsold asking-price changes never create equity. Cash is
   conserved on every transfer; external demand is the only injection and
   extraction/conversion/equipment spend are the only sinks.
4. **The Age target is a metric, never a mechanism.** It must not enter buyer
   valuation, supplier selection, price learning, transfers, or profit
   crediting. A calibration target is not a payment and not a forecast.
5. **Limited degrees of freedom.** Calibration may vary only the permitted
   demand/supply fields: production cost, capacity, and the fixed engineering
   demand profile. Company counts, startup capital, and Tier 0's prescribed
   limits stay fixed. A behavioral rule change requires a separately versioned
   protocol.
6. **Fairness over tier averages.** Cohorts (Tier 1 material, Tier 2
   sector/width, Tier 0 focus width, initial price direction) must have
   comparable expected opportunity. A starting product choice must not confer a
   statistically built-in advantage. Real competition and individual outcomes
   may differ; built-in structural edges may not.

## What calibration is

1. **Fix the market rules** (pricing, search, switching, elasticity,
   activation) and freeze them as a versioned protocol.
2. **Calibrate demand and supply** within the permitted fields so standard bots
   hit the return target.
3. **Validate** across multiple seeds and disruptions with actual accounting:
   the 1.9–2.1 mean-equity-multiple band per tier, cohort fairness, absence of
   persistent sales droughts, and firm-level profit/equity reconciliation.

## What calibration is not

- **Ownership, licenses, and holding companies.** That is a separate layer
  above the economy (see `progression_and_ownership.md`) and does not change
  bot behavior.
- Player onboarding, takeover valuation, invention activation, marketing, or
  visibility.
- Real-money, subscriptions, or billing.
- Short-window curve-fitting presented as full-Age validation.

## Method

Separate four distinct claims and never collapse them:

1. **Structural regression** — a rule change causally alters behavior.
2. **Short numerical fit** — a candidate matches a finite horizon.
3. **Observed equity trajectory** — actual recorded returns over real ticks.
4. **Full-Age validation** — 172,800 ticks, multiple seeds, all accounting and
   fairness gates pass.

A short fit is not a trajectory; a trajectory is not full-Age validation; and no
candidate is adopted until the actual-Age evidence passes every gate.
