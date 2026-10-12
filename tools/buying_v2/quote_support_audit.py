"""Structural coverage of the published-book response selector; no fitted forecasts."""
import numpy as np
from .forecast import PublishedChannel, _positive_integer
from .seller_history import SellerHistory


def audit(history, *, decision_tick, max_quote_folds):
    if not isinstance(history, SellerHistory) or not _positive_integer(decision_tick):
        raise ValueError('seller history and positive decision tick required')
    if not _positive_integer(max_quote_folds):
        raise ValueError('positive fold budget required')
    channels = []
    categories = ('noEligibleObservations', 'nonpositiveSales', 'insufficientQuotes',
                  'foldBudgetExceeded', 'structurallySupported')
    for name in sorted(history.channels):
        history._validate_state(name, history.channels[name])
        publication = PublishedChannel(history, name, decision_tick)
        rows = publication.rows
        if rows is None or not len(rows['ticks']):
            continue
        latest = rows['offered'][-1].astype(bool)
        products = []
        for product in np.unique(publication.products[latest]):
            columns = np.flatnonzero(publication.products == product)
            offered = rows['offered'][:, columns].astype(bool)
            current = columns[offered[-1]]
            counts = offered.sum(axis=1)
            n = len(current)
            # Disjoint exclusions in the same eligibility order as the models.
            remaining = counts == n
            exclusions = {'changedSellerCount': int((~remaining).sum())}
            for label, flags in (
                ('uninformedBook', np.any(offered & ~publication.local_informed[:, columns], axis=1)),
                ('constrainedBook', np.any(offered & publication.local_constrained[:, columns], axis=1)),
                ('emptyOpening', np.any(offered & ((rows['sold'][:, columns] + rows['closingStock'][:, columns]) <= 0), axis=1)),
            ):
                exclusions[label] = int(np.count_nonzero(remaining & flags))
                remaining &= ~flags
            support = {}
            for row in np.flatnonzero(remaining):
                ids = columns[offered[row]]
                quotes, inverse, multiplicities = np.unique(rows['quote'][row, ids], return_inverse=True, return_counts=True)
                starts = np.cumsum(multiplicities) - multiplicities
                for j, price in enumerate(quotes):
                    key = (int(starts[j]), int(multiplicities[j] - 1))
                    entry = support.setdefault(key, {'quotes': set(), 'nonpositive': False})
                    entry['quotes'].add(float(price))
                    entry['nonpositive'] |= bool(np.any(rows['sold'][row, ids[inverse == j]] <= 0))
            prices, multiplicities = np.unique(rows['quote'][-1, current], return_counts=True)
            starts = np.cumsum(multiplicities) - multiplicities
            totals = dict.fromkeys(categories, 0)
            for j, price in enumerate(prices):
                entry = support.get((int(starts[j]), int(multiplicities[j] - 1)))
                if entry is None: category = 'noEligibleObservations'
                elif entry['nonpositive']: category = 'nonpositiveSales'
                elif len(entry['quotes']) < 3: category = 'insufficientQuotes'
                elif len(entry['quotes']) > max_quote_folds: category = 'foldBudgetExceeded'
                else: category = 'structurallySupported'
                totals[category] += int(multiplicities[j])
            assert sum(totals.values()) == n
            assert sum(exclusions.values()) + int(remaining.sum()) == len(rows['ticks'])
            products.append(dict(product=int(product), latestOfferedSellers=n,
                                 candidateBooks=len(rows['ticks']), eligibleBooks=int(remaining.sum()),
                                 exclusions=exclusions, sellerSupport=totals))
        channels.append(dict(channel=name, latestPublishedTick=int(rows['ticks'][-1]), products=products,
            latestOfferedSellers=sum(p['latestOfferedSellers'] for p in products),
            sellerSupport={key: sum(p['sellerSupport'][key] for p in products) for key in categories}))
    return dict(version=1, decisionTick=int(decision_tick), maxQuoteFolds=int(max_quote_folds), channels=channels,
        scope='Latest offered seller columns at their latest quotes; whole-book inquiry eligibility and rank support. Structural support is necessary, not sufficient: fit admissibility, withheld-fold support, extrapolation, decay and predictive accuracy are not tested. Counts are seller columns, not unique companies.')
