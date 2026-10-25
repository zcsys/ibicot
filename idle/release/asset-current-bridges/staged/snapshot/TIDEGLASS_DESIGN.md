# Tideglass economy and retention blueprint

Design baseline dated 16 October 2026. Tideglass is a single-player incremental game about restoring a dark ocean through networks of floating light collectors. Its economic promise is that a small early structure can remain strategically useful after an observatory dominates raw production.

The three phases below distinguish documented mechanics, inferred design lessons, proposed parameters, and numerical experiments. Public documentation does not establish that a mechanic caused retention or that every reference title earned millions. The proposed economy is an executable baseline for playtesting, not a claim of commercially proven balance.

## PHASE 1 THE DISCOVERY AND ANALYSIS PHASE

### 1 Contemporary progression architectures

The important advance beyond a classic clicker is **a change in the decisions the player makes**. Automation removes a mastered task; a new layer introduces a different allocation problem. A second currency is justified when it has a different source, sink, persistence rule, or decision horizon.

| Reference | Progression and multi-currency loop | What carries the experience beyond clicking | Design implication |
|---|---|---|---|
| Idle Miner Tycoon | Continent-specific Cash funds shafts, elevators and warehouses. Mine prestige resets a particular mine for higher income while retaining remaining Cash, Super Cash and other mines. Research, managers and collectibles form additional progression paths. Super Cash can accelerate progression. | Several infrastructure components and several persistent advancement tracks create competing places to invest. | Distinguish temporary infrastructure from permanent account progress. Display the next useful investment across the whole network. |
| Leaf Blower Revolution | Leaf types fund their shops; prestige coins and successive Big, Mega and Ultra Leaf Crunch layers deepen progression. Crafting and specialist resources add parallel systems. The developer's ULC update explicitly introduces another prestige currency, new encounters and a skill tree. | New mechanics, automation, challenges and minigames broaden the activity space as numbers grow. | A higher reset must unlock a different decision. Merely adding another reset currency is insufficient. |
| Melvor Idle | Resources become processed items, equipment and supplies; currency purchases improve capacity and tools. Skill progress strengthens production and combat, creating dependencies across activities. | Planning resource chains, equipment and skill selection provides depth without requiring a conventional global prestige loop. | Retention can come from horizontal mastery and preparation. A prestige reset is a tool, not a genre requirement. |
| Antimatter Dimensions | Antimatter buys Dimensions; higher Dimensions produce lower ones. Infinity Points, Eternity Points and Reality Machines support successive layers. Reality also awards Glyphs and Perk Points. | Challenges alter rules, study choices create builds, and automation compresses earlier layers. | Each reset should preserve learned convenience and add a new strategic choice. |

Sources: Kolibri's [economy account](https://www.kolibrigames.com/blog/economy-in-free-to-play-mobile-games-part-2/), [currency reference](https://kolibri-games.helpshift.com/hc/en/3-idle-miner-tycoon/faq/55-what-are-the-different-types-of-currency-in-the-game/) and [prestige specification](https://kolibri-games.helpshift.com/hc/en/3-idle-miner-tycoon/faq/48-how-does-the-prestige-system-work/); Leaf Blower Revolution's [published feature description](https://store.steampowered.com/app/1468260/Leaf_Blower_Revolution__Idle_Game/) and [ULC release](https://lbr.humblenorth.de/lbr/wp2/the-ultra-leaf-crunch-update-v2-26-0/); Melvor's [developer store description](https://store.steampowered.com/app/1267910/Melvor_Idle/); Antimatter Dimensions' [current in-game help source](https://github.com/IvarK/AntimatterDimensionsSourceCode/blob/master/src/core/secret-formula/h2p.js).

The review signal is narrower than the design inference. The fetched Steam pages show 94% positive among 22,621 English reviews for Leaf Blower Revolution and 92% among 8,643 English reviews for Melvor. Their displayed recent-review results are 85% of 75 and 82% of 106, respectively. These are page snapshots with different populations, not retention cohorts, revenue estimates, or controlled comparisons. Sources: [Leaf Blower Revolution reviews](https://store.steampowered.com/app/1468260/Leaf_Blower_Revolution__Idle_Game/), [Melvor reviews](https://store.steampowered.com/app/1267910/Melvor_Idle/).

### 2 Active and passive hybrid triggers

| Pattern | Documented mechanism | Retention hypothesis | Failure mode to avoid |
|---|---|---|---|
| Cookie Clicker Grimoire | Magic refills over time. Spells spend magic and can backfire; Force the Hand of Fate can summon a golden cookie. | Players can prepare a burst while ordinary production continues, converting some waiting into planning. | Optimal play can become constant monitoring, repeated reloading or excessive burst stacking. |
| Cookie Clicker Stock Market | Goods have changing prices; the live script uses 60-second market ticks. | Reading prices and managing positions gives a different activity from buying production. | A side activity can become a second chore or an opaque source of dominant income. |
| Antimatter Dimensions automation | Milestones retain upgrades and unlock automation; later systems support programmable progression. | The player can graduate from execution to choosing policies. | Automation that behaves differently offline undermines trust in plans. |
| Leaf Blower Revolution side systems | The developer's recent update feed includes daily bounties, more daily quests, passive minigame play and automation improvements. | Alternative goals can reduce the experience of having nothing useful to do during a production gate. | More tasks and currencies can obscure the main objective. |

The first two observations come from the live [Grimoire script](https://orteil.dashnet.org/cookieclicker/minigameGrimoire.js) and [Stock Market script](https://orteil.dashnet.org/cookieclicker/minigameMarket.js). The latter two come from the [Antimatter Dimensions help implementation](https://github.com/IvarK/AntimatterDimensionsSourceCode/blob/master/src/core/secret-formula/h2p.js) and [Leaf Blower Revolution developer announcements](https://steamcommunity.com/app/1468260/allnews/).

These mechanisms may reduce perceived waiting; the sources do not establish a causal reduction in churn. Test whether players understand the alternate activity, voluntarily return to it, and still feel comfortable leaving the game.

### 3 Offline progress and catch-up models

The following equations are analytical archetypes, not assertions that all four games use identical source code or coefficients.

| Model | Mathematical form | Appropriate use and limitation |
|---|---|---|
| Rate-based credit | \(G=r_0\eta\min(T,C)\) | Constant production, no automatic purchases. \(r_0\) is currency/second, \(\eta\) is an offline fraction, \(T\) and \(C\) are seconds. Idle Miner's documented collection of offline Cash illustrates the broad pattern; its current precise rate/cap is not inferred here. |
| Action simulation | \(s_{k+1}=\Phi(s_k,\Delta t_k)\) | Production chains, resource consumption and automation. If an action takes \(d\) seconds and consumes a finite input, action count is bounded by both \(\lfloor T/d\rfloor\) and input availability. Melvor's interconnected production is suited to this model. |
| Compressed catch-up simulation | \(G\approx\sum_{k=1}^{N}r(s_k)\Delta t_k\) | Antimatter Dimensions documents enlarged offline ticks. Coarse ticks can reduce how often an autobuyer executes, so runtime and fidelity trade off. |
| Record-based replay, a candidate design pattern | \(G=\nu\lfloor T/d\rfloor\kappa B\) | \(B\) is a personally achieved reward, \(\nu\) repeats per interval and \(\kappa\) a replay fraction. This can turn an active breakthrough into a passive floor. Coefficients must be capped and record updates must be atomic. No current title coefficient is assumed. |

The factual offline examples are supported by [Idle Miner's help page](https://kolibri-games.helpshift.com/hc/en/3-idle-miner-tycoon/faq/56-what-is-idle-cash/), [Melvor's feature description](https://store.steampowered.com/app/1267910/Melvor_Idle/), and [Antimatter Dimensions' offline help](https://github.com/IvarK/AntimatterDimensionsSourceCode/blob/master/src/core/secret-formula/h2p.js). Offline earnings and the ability to launch without an internet connection are separate features; Melvor's [offline-client beta announcement](https://news.melvoridle.com/offline-client-public-beta-now-available-on-steam-mobile/) concerns the latter.

Catch-up has three distinct meanings: accounting for elapsed time, accelerating reconstruction of already-mastered content, and helping returning players recover missed opportunities. Tideglass addresses all three without granting a returning player more production than an otherwise identical continuously progressing account.

### 4 Hook Habit Hobby timeline

These are proposed experience windows, not measured universal stages.

| Stage | Design window | Player question | Useful mechanic | Measurement |
|---|---|---|---|---|
| Hook | First 30 minutes | Does my choice visibly change the world? | Immediate production, understandable upgrades, a preview of the first reset | First upgrade, first independent purchase decision, prestige comprehension |
| Habit | Days 1–7 | What will be ready when I return? | Reliable offline progress, predictable cycles, adaptable quests and a backlog | D1/D7 return, completion by visit frequency, perceived obligation |
| Hobby | Day 8 onward | What strategy or collection is mine? | Saved automation policies, challenge variants, cosmetic collections and seasonal experiments | D30 return, build diversity, voluntary activity selection, satisfaction |

The resulting design requirements are a coherent core currency, a distinct permanent reward, bounded active bonuses, preserved automation, meaningful low-tier marginal value, and rewards that tolerate a normal sleep/work schedule.

## PHASE 2 THE MATHEMATICAL ENGINE AND CORES

### 1 Original concept and currency accounting

**Tideglass:** players operate a floating conservatory that collects scattered light and restores an ocean's lost constellations. A prestige is a **Rechart**: the fleet is rebuilt from a better permanent atlas. The restored skyline, discoveries and cosmetic choices remain visible.

| Variable or resource | Symbol and unit | Source | Sink or use | Rechart behavior |
|---|---|---|---|---|
| Radiance wallet | \(W\), R | Producers and eligible bonuses | Buying structures | Resets to zero |
| Lifetime Radiance | \(L\), R | All newly earned main-world Radiance | Prestige eligibility; never spendable | Persists |
| Producer ownership | \(n_i\), integer | Purchases; one starting Tier 1 gift | Production and synergies | Becomes \((1,0,0,0,0)\) |
| Charts | \(P\), integer | Newly claimable prestige entitlement | Automatically committed to permanent power and unlocks | Persists; never decremented |
| Survey Notes | \(N\), integer | Surveys: 10 each; contracts: 10 each | Extra saved plans, archive projects and challenge access | Persists |
| Focus charges | \(z\), integer 0–12 | One per 2 hours | Optional calibration activities | Persists |
| Season XP | \(X_s\), XP | Qualifying contracts | Cosmetic pass levels | Independent of Rechart |
| Cosmetic ownership | Entitlement set | Play and direct purchases | Appearance only | Persists |

Charts are deliberately an automatically invested currency. There is no spendable Chart balance whose depletion could reduce production or cause old entitlement to be claimed again. Survey Notes provide the separate spend/choose loop. Initial Note sinks are 50 for an additional saved automation plan, up to five extra plans; 100 for a persistent optional challenge dossier; and 50 for an archive decoration. Basic automation and economic forecasts are free unlocks, not Note sinks.

Start with one free Spark Skiff, \(W=L=P=N=0\). The gift counts toward ownership and price inflation but adds no lifetime earnings. There is no selling or conversion back to Radiance in the baseline. Cosmetic purchases, event resources, gifts and administrative refunds never increment \(L\). Ordinary producer earnings, offline earnings and explicitly bounded main-world bonuses do.

### 2 Base producers and price geometry

| Tier \(i\) | Producer | Base price \(b_i\), R | Unit output \(p_i\), R/s | Base payback \(b_i/p_i\) |
|---|---|---:|---:|---:|
| 1 | Spark Skiff | 30 | 1 | 30 s |
| 2 | Prism Nursery | 600 | 20 | 30 s |
| 3 | Tide Dynamo | 12,000 | 400 | 30 s |
| 4 | Aurora Loom | 240,000 | 8,000 | 30 s |
| 5 | Dawn Observatory | 4,800,000 | 160,000 | 30 s |

For \(i\in\{1,\ldots,5\}\):

\[
b_i=30\cdot20^{i-1},\qquad p_i=20^{i-1},\qquad q=1.12.
\]

The **tier multiplier is 20 for both cost and output**. This preserves identical base efficiency across tiers. It avoids making a new tier intrinsically better by an arbitrary efficiency jump; its advantage is a fresh purchase count and its strategic connections. This is a controlled baseline, not a universal proof that 20 is optimal for every game.

The **building scale multiplier is 1.12**, a 12% increase per purchase within a tier, inside the requested 1.07–1.15 range. At existing ownership \(n_i\):

\[
C_i(n_i)=b_iq^{n_i},\qquad
C_i(n_i,k)=b_iq^{n_i}\frac{q^k-1}{q-1}.
\]

The maximum affordable batch is

\[
k_{\max}=\max\left(0,\left\lfloor\frac{\ln\!\left(1+W(q-1)/(b_iq^{n_i})\right)}{\ln q}\right\rfloor\right).
\]

Verify the final batch against actual cost and adjust by one if floating-point approximation crosses a boundary. Tier \(i>1\) becomes purchasable when \(n_{i-1}\ge10\). The UI always previews the next tier. Rechart resets the ownership requirements but preserves the player's explanatory help and saved automation policies.

### 3 Multiplier arrays and complete production equation

| Parameter | Exact baseline | Meaning |
|---|---:|---|
| Milestone spacing | 25 structures | Milestones at 25, 50, 75, 100 |
| Milestone multiplier | 2 per milestone | Maximum local milestone multiplier 16 |
| Prestige earnings scale | \(L_0=10^9\) R | First Rechart eligibility |
| Chart entitlement scale | 10 Charts | Entitlement at \(L_0\) |
| Prestige exponent | \(\alpha=0.65=13/20\) | Diminishing entitlement per earned R |
| Permanent-power exponent | \(\beta=0.5\) | Additional damping of prestige power |
| Synergy activation | \(P\ge25\) | Reveals network planning after early resets |
| Synergy count scale | 25 structures | Normalizes logarithmic count effects |

Define the arrays \(\mathbf p=(1,20,400,8000,160000)\), \(\mathbf m=(m_1,\ldots,m_5)\), and \(\mathbf S=(1,1,1,S_4,S_5)\):

\[
m_i(n_i)=2^{\min(4,\lfloor n_i/25\rfloor)},\qquad
M_P(P)=1+\sqrt{P/10}.
\]

With unboosted production \(R_0\) and optional additive bonus fraction \(b(t)\):

\[
R_0(\mathbf n,P)=M_P(P)\sum_{i=1}^{5}n_i p_i m_i(n_i)S_i(\mathbf n),
\qquad R(t)=R_0(\mathbf n,P)[1+b(t)].
\]

\[
\frac{dW}{dt}=R(t),\qquad \frac{dL}{dt}=R(t)
\]

between purchases and resets. A purchase subtracts its price from \(W\) only. A milestone multiplies the output of all owned structures in that tier. Optional bonuses add within the single bonus term; Focus and support boosts never multiply one another. Their budgets are specified in Phase 3.

### 4 Lifetime prestige entitlement and diminishing returns

Let \(P\) be the number of Charts previously awarded across all Recharts. Define

\[
F(L)=\left\lfloor10\left(\frac{L}{10^9}\right)^{0.65}\right\rfloor,
\qquad
\Delta P=\max(0,F(L)-P).
\]

Rechart is enabled only when \(L\ge10^9\) and \(\Delta P\ge1\). It atomically sets \(P\leftarrow F(L)\), resets \(W\) and \(\mathbf n\), and retains \(L\), Notes, discoveries, timers and entitlements. Awarding the full \(F(L)\) on every reset would create an exploit; subtracting awarded entitlement prevents it. A second reset with no new earnings grants nothing.

| Lifetime Radiance \(L\) | Total eligible Charts \(F(L)\) | Additional Charts if 10 already awarded | Power if all eligible Charts are claimed |
|---:|---:|---:|---:|
| \(10^9\) | 10 | 0 | 2.000× |
| \(10^{10}\) | 44 | 34 | 3.098× |
| \(10^{11}\) | 199 | 189 | 5.461× |
| \(10^{12}\) | 891 | 881 | 10.439× |

For the unfloored curve \(f(L)=10(L/L_0)^{0.65}\):

\[
f'(L)=\frac{6.5}{L_0}(L/L_0)^{-0.35},\qquad
f''(L)=-\frac{2.275}{L_0^2}(L/L_0)^{-1.35}<0.
\]

Ten times lifetime earnings gives approximately 4.467 times entitlement and 0.447 times the marginal Charts per R. Doubling entitlement requires approximately \(2^{1/0.65}=2.905\) times lifetime earnings. The next Chart threshold is exactly

\[
L_{P+1}=L_0\left(\frac{P+1}{10}\right)^{1/0.65},
\]

subject to the first-reset eligibility gate. The permanent-power curve makes high-end production scale roughly as \(L^{0.325}\) at fixed ownership when entitlement is claimed. It damps progression further while still giving a clear 2× first reset.

### 5 What an optimal prestige time actually means

**Concavity alone does not determine a perfect reset time.** Lifetime earnings continue across runs; production, reconstruction, milestone proximity, automation and the player's next visit all matter. A fixed rule such as “reset at 20% more currency” is a heuristic.

For a defined horizon \(H\), objective of maximizing lifetime production, and allowed control policies \(\pi\), the correct control problem is

\[
V(s,H)=\sup_{\pi}\log\bigl(1+L_{\pi}(H)\bigr).
\]

State \(s\) includes wallet, lifetime earnings, counts, Charts, remaining timers and automation policy. Reset is optimal only when its value exceeds every allowed continuation at that state. With a specified future purchase policy and **exactly one permitted reset**, the reset timing reduces to

\[
t^*=\underset{0\le t\le H}{\arg\max}\;
L\!\left(\Phi_{H-t}\!\left[\mathcal R(\Phi_t(s))\right]\right),
\]

also comparing the no-reset path. \(\Phi_t\) advances the economy under that purchase policy and \(\mathcal R\) is the Rechart transition. The supplied model enumerates this restricted problem on a one-minute grid, not the unrestricted optimal-control problem.

A transparent local approximation is useful in the interface. Assume the current production \(r\) would stay constant, reconstruction produces nothing for \(\tau\), and the restored fleet then earns \(mr\), where \(m=M_P(P+\Delta P)/M_P(P)\). Reset breaks even after

\[
H_{\rm break}=\frac{m\tau}{m-1},\quad m>1.
\]

For a reset from 10 to 40 Charts, power rises from 2× to 3×, so \(m=1.5\). With a hypothetical ten-minute reconstruction, break-even is 30 minutes. Real reconstruction produces something and purchases change both branches, so use the simulator for the final estimate. Show “estimated break-even,” assumptions, and the next meaningful milestone; never label a heuristic universally optimal.

The first ten Charts unlock basic autobuying for all tiers. At 25, cross-tier synergies unlock. At 100, saved conditional reset plans unlock; automatic Rechart is opt-in, with an explicit horizon/threshold and a preview. New-player guidance can value learning a new feature; it must not misrepresent that objective as maximizing currency over a fixed horizon.

### 6 Cross-tier synergy matrix

For \(P\ge25\), define \(x_i=\log_2(1+n_i/25)\). Before that, all \(S_i=1\).

| Source ownership | Tier 1 target | Tier 2 target | Tier 3 target | Tier 4 target | Tier 5 target |
|---|---:|---:|---:|---:|---:|
| Tier 1 Spark Skiffs, \(x_1\) | 0 | 0 | 0 | 0.20 | 0.10 |
| Tier 2 Prism Nurseries, \(x_2\) | 0 | 0 | 0 | 0.10 | 0.25 |

\[
S_4=1+0.20x_1+0.10x_2,\qquad
S_5=1+0.10x_1+0.25x_2.
\]

At \(n_1=n_2=100\), \(S_4=1.6966\) and \(S_5=1.8127\). The terms add inside a target's synergy multiplier. They depend only on ownership, never on already-multiplied output, preventing a circular output calculation.

Let \(B_j=n_jp_jm_j\). When no local milestone is crossed, the exact extra output from buying one Tier 1 structure is

\[
\Delta R_1=M_P\left[p_1m_1+
\log_2\left(\frac{26+n_1}{25+n_1}\right)(0.20B_4+0.10B_5)\right].
\]

Replace coefficients with 0.10 and 0.25 for the Tier 2 support term. At a local milestone, use the full difference \(R_0(\mathbf n+\mathbf e_i,P)-R_0(\mathbf n,P)\), which includes the jump for existing structures.

Rank candidate investments by **marginal network output per R spent**, not an individual building's displayed direct output. For a batch, use the full batch cost and full state difference. Waiting time and access to future unlocks still make greedy efficiency a heuristic.

The diagnostic state \(\mathbf n=(100,100,50,50,50)\), \(P=100\), yields:

| Next purchase | Cost, R | Direct marginal R/s with synergies disabled | Full marginal R/s | Full marginal payback |
|---|---:|---:|---:|---:|
| Tier 1 | 2,505,668 | 66.60 | 168,491.70 | 14.87 s |
| Tier 2 | 50,113,359 | 1,331.93 | 391,771.94 | 127.91 s |
| Tier 4 | 69,360,526 | 133,192.89 | 225,972.18 | 306.94 s |
| Tier 5 | 1,387,210,511 | 2,663,857.70 | 4,828,707.82 | 287.28 s |

This demonstrates renewed utility, not a promise that every low-tier purchase is always best. Logarithmic support gives decreasing gains while exponential prices eventually move the best purchase elsewhere. Later growth in Tier 4/5 production increases the support value again.

### 7 Numerical validation and interpretation

The reference simulation starts with one gifted Skiff and makes instantaneous purchases using the highest marginal output/cost among currently unlocked single purchases. It saves until the selected purchase is affordable. There are no manual taps, bonuses, quests or purchases for money. Before automation is unlocked, this represents an idealized attentive player.

| First-run event | Simulated time |
|---|---:|
| First Tier 2 owned | 3.11 min |
| First Tier 3 owned | 5.82 min |
| First Tier 4 owned | 8.50 min |
| First Tier 5 owned | 11.19 min |
| First prestige eligibility, \(L=10^9\) | 16.75 min |

| Purchase growth \(q\) | First prestige eligibility |
|---:|---:|
| 1.07 | 13.90 min |
| 1.10 | 15.50 min |
| **1.12** | **16.75 min** |
| 1.15 | 18.85 min |

These are policy-dependent simulation outputs, not population medians. Milestone discontinuities make local sensitivity nonlinear.

A second experiment resets at ten Charts, then whenever total eligible Charts double. It reaches resets 1, 4, 8 and 12 at 16.75, 42.90, 86.59 and 247.77 minutes. The respective cycle lengths are 16.75, 7.58, 14.78 and 69.11 minutes. This verifies a useful fast-rebuild phase followed by longer waits under this heuristic; it does not establish optimal play or a month of content.

The restricted one-reset search starts at first prestige eligibility and examines the following eight hours. Its best grid point is 155 minutes later. Terminal lifetime earnings are approximately \(1.1322\times10^{14}\), versus \(1.0463\times10^{13}\) for an immediate single reset and \(3.1199\times10^{12}\) for no reset. Multiple future resets are excluded from that experiment, so this is **not** a recommendation to make new players wait 155 minutes.

The validation suite passes 203 checks, including price aggregation, lifetime award accounting, monotone output, synergy effects and timer budgets. An independent one-second integration differs from event-based integration by 0.333% after one hour. Human comprehension, long-term retention, revenue and unrestricted optimal play remain empirical or further optimization work.

## PHASE 3 MODERN PILLARS AND USER RETENTION DESIGN

### 1 Psychological progression and feedback

| Moment | Mechanical feedback | Visual or audio response | Player meaning |
|---|---|---|---|
| First production | Radiance rises from the gifted Skiff | A visible stream of light reaches the harbor | The world changes without repetitive tapping |
| Purchase | Before/after R/s and time-to-goal update immediately | A structure launches and joins the light network | My decision changed the rate |
| 25/50/75/100 milestone | Whole-tier output doubles | A short construction transformation and optional chord | This is a new capability, not only a larger number |
| Synergy purchase | Highlight the affected Loom/Observatory and its incremental output | A connecting beam thickens briefly | My early fleet still matters |
| Return from absence | Show earned R, purchases made by automation and completed projects separately | A short harbor time-lapse with skip control | My plan continued to work |
| Rechart | Preview resets, retained progress, new power and reconstruction estimate | Previously restored constellations remain overhead | Rebuilding expresses accumulated knowledge |

Use predictable feedback for ordinary actions and distinctive celebrations for new capabilities. “Dopamine hits” is shorthand for satisfying feedback here, not a measured neurochemical outcome. Support reduced motion, independent audio controls, high-contrast indicators, large text and keyboard/controller navigation. Color is never the only carrier of economic information.

The optional **Constellation Calibration** is a short untimed routing puzzle. One Focus charge allows a choice of a displayed network to emphasize for ten minutes, implemented as a 20% global production bonus in the baseline so no puzzle route has a hidden superior payout. Solving earns an archive pattern; a single-button accessible completion gives identical economic value. Charges can be queued, and repeated rewards extend duration rather than multiply magnitude. The puzzle's lasting value is collecting patterns and understanding the network, not punishing a failed reflex test.

### 2 Asymmetric clocks with daily collection parity

| Clock | Mathematical rule | Storage or queue | Intended use |
|---|---|---|---|
| 2-hour Focus cycle | One charge per 7,200 real seconds | 12 charges, with fractional progress retained | Frequent players can calibrate between tasks; daily players can collect the same generation |
| 8-hour Survey cycle | One completed survey per 28,800 real seconds | 3 completed surveys; automatic repeat while space exists | Morning/evening planning, or one daily collection; each completion yields 10 Notes |
| 24-hour production window | Full production simulation for 86,400 seconds of absence | Additional reduced-rate catch-up below | Supports normal sleep and work |
| 24-hour contract refresh | 3 contracts per account day | Up to 7 daily sets, or 21 contracts | A missed day does not erase a streak or create an urgent chore |

For a replenishing resource with cap \(c\), rate \(g\), and elapsed real time \(T\), use \(z'=\min(c,z+gT)\); fractional progress belongs to the saved state. For discrete surveys, preserve cycle phase, count completed cycles, and stop generating when the completed queue is full. After collection, auto-repeat resumes without another launch interaction. New accounts begin with zero stored rewards; the onboarding demonstration is not a redeemable extra charge.

Focus provides +20% for 600 seconds per charge. Its long-run maximum is 12 charges/day, equivalent to 1,440 unboosted production seconds/day, or 1.667% of a constant-rate day. A previously accumulated inventory may be consumed in a shorter period; it is not a hard per-day spending cap. Banked charges eliminate the economic requirement to return every two hours. Activating a queued charge uses the same rules online and offline.

Use an account-day boundary chosen at onboarding, with a fixed UTC offset for the baseline; changing time zones never grants another day's rewards. Day identifiers, queue states and claim receipts survive Rechart. Notifications are opt-in, can be bundled, and respect quiet hours.

### 3 Offline formula and returning-player catch-up

For absence \(T\ge0\) seconds, define effective production time

\[
\tau(T)=\min(T,86400)+0.25\min(\max(T-86400,0),172800).
\]

| Absence | Effective production time | Meaning |
|---:|---:|---|
| 2 h | 2 h | Full rate |
| 8 h | 8 h | Full rate |
| 24 h | 24 h | Full rate |
| 48 h | 30 h | First day plus quarter-rate second day |
| 72 h | 36 h | Maximum offline production time |
| 7 days | 36 h | No further production; contract backlog can still help |

At a fixed rate with no changes or bonuses, \(G_{\rm off}=R_0\tau(T)\). With autobuying, advance the actual saved state through affordability and milestone events; do not multiply the player's last displayed rate by the entire absence and call that a simulation.

More generally, define offline rate weight \(w(t)=1\) for the first 24 hours, \(0.25\) for the next 48 hours and zero thereafter:

\[
G_{\rm off}=\int_0^T w(t)R_0(s(t))[1+b(t)]\,dt.
\]

Temporary bonuses expire on real time, so do not extend them by reducing the earning clock. Survey and Focus timers also use real time, independently of economic time. The reference model validates the effective-time envelope; a production implementation must also implement these event boundaries and replay the same chosen automation policy online and offline.

Do not add a second “offline penalty” inside an already reduced rate. Resuming and claiming updates the last-settled timestamp atomically; reloading cannot claim the same interval twice. Store pending completions when a queue is full. Clock rollback produces no negative progress; save conflicts are resolved using receipts and account revision, not by adding two versions of the same earnings.

The reduced-rate tail, preserved autobuyers and seven-day contract backlog form the catch-up package. They recover opportunity without handing out unearned records or letting absence outperform the same state's continuously simulated progress. An actively replanning player can still outperform a fixed saved policy; daily collection parity does not imply identical strategic results.

### 4 Dynamic daily contracts

Generate contracts only from mechanics the player has unlocked. Seed choices by account and day; a reload cannot reroll them. Progress persists through Rechart and advances offline where applicable. Give one free reroll per contract; retain the original difficulty snapshot after reroll.

| Contract family | Exact baseline target | Reward |
|---|---|---|
| Restore | Earn \(Q_R=\lceil600r_{\rm ref}\rceil\) main-world R after assignment | 10 Notes + 250 season XP |
| Build | Buy \(Q_B=\min(5,\max(1,\lfloor300r_{\rm ref}/C_{\min}\rfloor))\) structures | 10 Notes + 250 season XP |
| Discover | Complete one available calibration, archive interaction or optional challenge objective | 10 Notes + 250 season XP |

Here \(r_{\rm ref}\) is unboosted production and \(C_{\min}\) the cheapest currently purchasable structure at assignment. Both are frozen for that contract. If a returning player has no current production history, use the current saved state; never substitute a population percentile that scales their target beyond their economy. Accrued backlog slots materialize on return using that snapshot, so absence does not require simulating hypothetical player choices. Granting a quest reward does not count toward another earn-R quest.

At full daily completion, contracts yield 30 Notes and 750 XP; surveys yield another 30 Notes. A contract can be completed at any point while retained, without a streak multiplier or reset demand. Prestige, advertisements, spending money and inviting friends are never required contract objectives.

### 5 Seasonal live operations

Run a 28-day **Night of Returning Stars** season with a separate challenge fleet, its own temporary resources, and a fixed initial state. For the first event, retain base prices and outputs but set the event synergy matrix to

\[
A_{\rm event}=\begin{pmatrix}0.10&0.20\\0.25&0.10\end{pmatrix}
\]

for sources 1/2 and targets 4/5. Event synergies are available immediately. This swaps which source most benefits each late producer and changes the planning problem. Event Rechart and its power are disabled; permanent main-world Charts, boosts and wallet never enter the event. These event parameters require a separate pacing test before release.

| Boundary | Rule |
|---|---|
| Main-world export | Cosmetics, archive entries and badges only; zero R, Charts, Notes or permanent production multipliers |
| Main progression during event play | Continues using the player's saved policy; event attention does not stop main production |
| Event reward eligibility | Fixed personal milestones; if a leaderboard exists, rewards do not depend on rank |
| Pass progression | One shared contract-XP ledger; completing an event alternative replaces a daily objective rather than doubling its reward |
| Missed content | Event becomes an archived challenge; purchased passes can be completed later, one selected pass at a time |
| Changes during a season | Versioned parameters, public descriptions, reversible rollout; no secret personalized difficulty |

The pass has 30 levels at 500 XP each: 15,000 XP total. Three 250-XP contracts per completed day allow completion in 20 days out of 28; the seven-day backlog provides additional scheduling flexibility. Event-only objectives are alternative routes to the same XP budget, not mandatory extra chores. Cosmetic pass rewards cannot alter prestige or survey capacity.

### 6 Ethical rewarded advertising and premium offers

An offline doubler changes the economy even in a single-player game. Ethical design therefore requires a visible limit and an economically equal no-ad route; “optional” by itself does not establish parity.

All players receive access to six daily **Support tokens**, each worth at most 300 unboosted production-equivalent seconds. A short, accessible crew briefing grants the same token as an optional rewarded ad. Both draw from the same six-token allowance. No payment or ad can create extra slots, extend caps or refill used allowance. An ad no-fill or failure leaves the free route available. Tokens expire after their account day without penalty or streak loss, and nothing in the core balance assumes their use.

| Token use | Exact benefit | Guardrail |
|---|---|---|
| Temporary speed boost | +25% production for 1,200 real seconds | \(0.25\times1,200=300\) production-equivalent seconds; nonmultiplicative, queued |
| Offline salvage doubler | Match an eligible five-minute slice of already calculated unboosted offline earnings | Bonus \(B=\min(G_{\rm slice},300r_{\rm claim})\); display “double this salvage cache,” not “double all offline earnings” |

\(G_{\rm slice}\) contains only genuine unboosted production from a selected, unclaimed slice of the return settlement; each slice can be matched once. \(r_{\rm claim}\) is the unboosted rate at settlement. Consumption and bonus entitlement are committed before any purchase or reset; the match cannot itself be doubled. The six-token allowance creates at most 1,800 production-equivalent seconds of entitlement per account day, 2.083% of a constant-rate day; activated effects can straddle a day boundary. Focus and support together add at most 3.75% of a steady-state day's production over their long-run generation budgets. That is **not** a 3.75% bound on compounded lifetime advantage: earlier purchases can amplify the benefit, so compare complete trajectories in playtests.

Support and Focus bonuses add: simultaneous +20% and +25% means 1.45×, never 1.50×. Speed effects persist through Rechart and retain their original real-time expiry, preventing resets from refreshing durations. A Support token is required for each queued effect.

| Premium offer | Proposed initial price, USD | What the player buys | Economic effect |
|---|---:|---|---|
| Structure or harbor skin | $4.99 | Previewable appearance | None |
| 28-day cosmetic pass | $7.99 | Additional cosmetics on the same XP track; completion remains available later | None |
| Supporter collection | $14.99 | A fixed cosmetic bundle and soundtrack | None |

Prices are product hypotheses, not market benchmarks. Avoid paid Chart multipliers, purchased storage, paid automation access, random paid loot, tier skips, manufactured discounts and subscription renewal traps. A premium pass changes rewards, not XP rate or contract difficulty. Purchased cosmetic ownership persists through every Rechart. This model deliberately limits monetization pressure; commercial viability must be tested through voluntary cosmetic demand and ad yield, not assumed from another game's revenue.

### 7 Production standards and empirical launch gates

| Area | Acceptance criterion or test |
|---|---|
| Economy arithmetic | Preserve bulk-cost identities, nonnegative wallets and monotone entitlement; no currency minted by a repeated reset or replayed claim |
| Large numbers | Use large-number storage for production and stable logarithmic comparisons; do not use ordinary float to store arbitrarily large integer wallets |
| Prestige boundary | With exact integer earning units, verify \(P^{20}L_0^{13}\le10^{20}L^{13}\) to select the greatest valid integer \(P\); scale \(L\) and \(L_0\) to identical units |
| Online/offline agreement | Test matched policies across 2/8/24-hour spans, milestone crossings, temporary-bonus expiry, quest refresh and interrupted resumes |
| Save resilience | Transaction receipts, versioned migrations, local export and recovery; conflict resolution cannot merge duplicated income |
| First-session pacing | Playtest median first prestige eligibility against a proposed 15–30-minute window; keep simulation results separate from observed medians |
| Return flexibility | Compare 1/3/6 visits per day with identical policies; all should collect generated Focus and surveys up to the stated capacities |
| Active bonus impact | Compare full purchase/prestige trajectories with and without bonuses; report progress ratios and subjective pressure, not only nominal bonus percentages |
| Retention | Measure install-cohort D1/D7/D30 with a fixed denominator; segment by play style and progression, not by willingness to spend |
| Content depth | Test whether players adopt different viable policies and optional challenges; do not treat an endlessly rising number as sufficient month-long content |
| Experiment quality | Pre-register a primary retention or satisfaction metric, duration and minimum detectable effect; do not optimize only ad views or session count |

The implementation pack contains `economy.json`, the executable reference `economy.py`, `validate.py`, generated CSV experiments, and JSON results. Run `python3 economy.py` and `python3 validate.py` from this directory. The reference implements core purchases, milestones, prestige, synergies and the offline time envelope. It does not implement a client, save service, full live-ops system or ad integration; those are specified above for subsequent production work.
