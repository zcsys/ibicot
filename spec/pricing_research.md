# Pricing and purchasing: research and model choices

Research reviewed on 2 October 2026, before changing the economic rules.

| Primary source | Relevant result | Decision for Phase 0 |
| --- | --- | --- |
| [Kephart, Hanson & Greenwald (2000), Dynamic Pricing by Software Agents, §3.1–3.2](https://cs.brown.edu/people/amy/papers/rudin.pdf) | Derivative-following sellers experiment with small price changes and reverse direction when observed profit falls. Buyers differ in how many offers they compare. Adaptive competitors can produce cycles rather than a single equilibrium. | Use profit-directed price experiments and a small consumer comparison set. A seller needs its own results, not private consumer valuations or an ideal price. |
| [Gualdi et al. (2014), Tipping points in macroeconomic Agent-Based models, §II.3–II.5](https://arxiv.org/html/1307.5319) | Mark I separates price and quantity decisions using excess demand and relative market prices; households compare a random sample of sellers. | Retain separate quantity planning and bounded consumer search. Do not use its market-average price condition: identical starting quotes can make that condition inactive, and our durable inventories differ from its non-storable output. |
| [Dawid et al., Eurace@Unibi v1.0 manual, §3.2.2 and §3.3.2](https://noah.nrw/ubbihs/content/titleinfo/5127756/full.pdf) | Firms replenish toward forecast demand plus a stock buffer; sold-out observations require a demand correction. Consumers choose among available offers with price sensitivity. | Use an order-up-to stock policy and record actual attempted orders. Avoid the larger model's regression, capital optimization, survey and labor machinery. |
| [Huh et al., An Adaptive Algorithm for Finding the Optimal Base-Stock Policy in Lost Sales Inventory Systems with Censored Demand](https://www.columbia.edu/~th2113/files/Mixing-MOR-final-version.pdf) | Sales understate demand when stock constrains fulfillment. Adaptive inventory control must handle censoring. | Forecast from observed requested units, including refused orders. Our short-lead-time EMA rule is an adaptation, not the paper's algorithm or an optimality claim. |
| [Dawid, Delli Gatti, Fierro & Poledna (2024), Implications of Behavioral Rules in Agent-Based Macroeconomics, §2 and §4](https://www.ifo.de/DocDL/cesifo1_wp11411.pdf) | Four established behavioral rule families can look similar in ordinary conditions yet respond differently to demand, cost and productivity shocks. | Test counterfactual responses, cost accounting and inventory recovery, as well as long-run default operation. Absence of floor trades alone is insufficient evidence of a working market. |
| [Dasgupta & Das (2000), Dynamic Pricing with Limited Competitor Information, §3.2–4](https://www.researchgate.net/publication/221549081_Dynamic_Pricing_with_Limited_Competitor_Information_in_a_Multi-Agent_Economy) | Fixed experiment sizes can produce large oscillations and lost profit. Adaptive steps improve resolution, while short observation histories still have limitations. | Halve experimental scale on reversals and restore it on a consistent direction. These factors are explicit learning assumptions; this is not the paper's exact adaptive algorithm. |

Follow-up review: Mark I/0's price/quantity rules also use excess demand.
The Phase 0 adaptation uses each seller's received requested units versus
actual window deliveries plus closing stock. It drops the reference model's
market-average price condition and retains ordinary posted-offer trades.
Business orders to wholly sold-out markets must reach a contacted supplier;
otherwise no local pricebot can observe that scarcity.

## Selected design

Use derivative-following pricing, order-up-to replenishment, cost-aware input purchasing, and consumer comparison shopping. These are established building blocks; their integration into the four-tier recipe network is a Phase 0 design choice.

Sellers compare total gross profit per tick over completed observation windows. They keep moving in the last experimental direction if profit improves and reverse if it falls. The objective is total profit, not revenue per sold unit: the latter could reward an almost idle, overpriced firm. Unsold stocked sellers reduce their offers; sellers with no output and no orders hold their quotes. Observation windows are staggered across firms to avoid simultaneous repricing.

Received orders exceeding delivered units plus closing stock make a seller
try a higher quote, including windows with zero deliveries. Experiment sizes
adapt to directional reversals. No quality, location, service, extra scarcity
parameter or required positive margin is added. A fraction-to-boundary price
safeguard and automatic preservation of a prior margin were considered and
discarded: avoiding a numerical boundary is not a mechanism for prices to emerge.

There is no prescribed long-run markup, consumer-derived seller ceiling, or shared desired price. Starting markups only initialize offers. Bot quotes cover observed unit cost; that is a break-even reservation constraint, not a guaranteed profit margin. Competitive trading at variable cost can be economically meaningful and must be reported rather than hidden by an above-floor target. Player offers obey the same cost constraint.

Consumer value scales are authored preferences by complexity, independent of recipes, current prices, production costs and starting markups. The existing decreasing quantity curve remains a stylized demand assumption. Its scale is the price at which expected quantity halves, not a hard reservation-price ceiling. A consumer compares five sampled posted offers plus its previous successful supplier; stockouts can prevent fulfillment despite stock elsewhere.

Manufacturers order inputs for a bounded finished-stock deficit, first checking the current replacement cost of the complete recipe against their output quote. Existing ingredients are shared between installed lines. Whole-lot buying can leave residual inputs. Cash, conversion costs, supplier stock and capacity still constrain actual output. Seller forecasts include only orders they actually receive; failed searches are not distributed to every firm as omniscient demand.

## Assumptions and limitations

The observation interval, experiment size, five-offer search, stock coverage, initial markups and consumer value scales are explicit simulation assumptions, not fitted empirical estimates. Profit comparisons in a changing competitive market are noisy and do not identify a causal derivative or guarantee optimal prices. Gross profit excludes labor, rent, depreciation and financing because these flows are absent from Phase 0. Unlimited consumer cash remains an external injection; this is a supply-chain economy, not a closed macroeconomic model.

Exact equations, transaction order, information sets, stock handling and reproducible checks belong in [economy_contract.md](economy_contract.md). Validation must distinguish stable operation, meaningful behavioral responses and empirical realism; passing the first two does not establish the third.
