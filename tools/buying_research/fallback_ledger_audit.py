"""Reproduce the baseline's terminal-quote demand-ledger counterexample."""
import argparse
import json
from pathlib import Path
from economy.core import model as M
from economy.core.state import reset_world
from economy.kernel import tick as reference, numba as compiled


def audit():
    rows = []
    for fast in (False, True):
        cfg, w = reset_world(dict(t2FirmCount=3, distributorCount=1,
            distributorActivation=1, distributorSearchOffers=20,
            t2ReservationPremium=0, seed=137))
        w.t2LineProduct[:3] = 0
        w.distributorProduct[0] = M.NP
        w.distributorPreferredSupplier[0] = -1
        w.distributorQMax[0] = 20
        w.distributorEta[0] = 1
        profile = M.procurement_profile(M.T2_PRODUCTS[0], cfg,
            M.reference_tier2_cost(M.T2_PRODUCTS[0], cfg))
        w.distributorChoke[0] = 10 / profile['valuation']
        w.t2Price[:3] = [10, 15, 30]
        w.t2Fin[:3] = [2, 3, 20]
        if fast:
            compiled.clear_distributors(w, cfg, 1)
        else:
            reference.clear_distributors(w, cfg, M.PRODUCTS, M.T2_PRODUCTS, 1)
        assert w.t2Sold[:3].tolist() == [2, 3, 0]
        assert w.distributorLastQ[0] == 8 and w.marketStockUnmet.sum() == 3
        rows.append(dict(engine='compiled' if fast else 'reference',
            quotes=[10, 15, 30], quoteDemand=[10, 8, 5], openingStock=[2, 3, 20],
            sold=w.t2Sold[:3].tolist(), lastQuantity=int(w.distributorLastQ[0]),
            marketStockUnmet=float(w.marketStockUnmet.sum()),
            marketPriceLost=float(w.marketPriceLost.sum()), finalVisitedQuoteRemaining=0))
    return dict(status='verified', rows=rows, productionChanges=False,
        interpretation='Actual quantities obey the user rule. Baseline LastQ retains the last positive request total (8), not the total at the zero-remaining terminal quote (5); it reports three stock-unmet units. R1 instead records its first funded quote-stage intention. Their loss denominators are protocol-dependent and not directly comparable as the same latent demand measure.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = audit()
    with args.output.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(json.dumps(data))


if __name__ == '__main__':
    main()
