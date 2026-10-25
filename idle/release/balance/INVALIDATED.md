# Superseded economic results — cross-engine cache defect

The initial88-case and v2/v3 94-case matrices are **invalid as full-game balance evidence**. The supplemental-v1 run is also affected. Preserve their source pins, logs and findings as defect evidence; do not freeze beta balance from them or reuse their pacing numbers.

The static fleet-rate memo in `TideglassEngine.outputPerSecond` keyed counts and Charts, but a subclass may override producer rules. Main, challenge and seasonal fleets with the same counts could reuse a rate computed under another ruleset. Gameplay independently reproduced challenge.05 returning8421050000000000000000000000000raw after the main engine filled the cache, instead of its exact producer sum11381050000000000000000000000000raw. Cache order therefore affected timelines and goals.

The lead repaired the base engine to memoize fleet rates only when `runtimeType == TideglassEngine`. Scenario subclasses calculate their virtual producer sum directly. Prices, count logarithms and the base Chart-power memo do not call virtual rule functions and retain their exact bounded caches. Economic constants are unchanged.

The earlier62-case byte-identical numeric report remains evidence for its tested main-engine cases only. It did not prove compatibility with overridden scenario rules. Its independent review missed that integration dimension. No previous report is rewritten to hide that gap.

Required next evidence: permanent cross-engine/order/eviction regressions; all core/progression/event checks; fresh original-policy matrix v4; supplemental rerun under a new pin; independent audit of corrected trajectories. Human pacing and elapsed retention gates remain separate and unmet.
