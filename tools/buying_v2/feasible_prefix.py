"""Lexicographic allocation traversal with cash/slot and optional caller pruning.

Internal helper: callers validate offers/state through the ordinary ledger.
Positive prices make prefix goods spending monotone. No fee, sales, production,
posterior or future-value assumption is used by the built-in feasibility checks.
An optional caller supplies a separately verified prefix-pruning predicate.
"""


def allocations(ranges,offers,held,slots,cash,stats,max_prefix_nodes,prune=None):
    remaining=[max(0,s-h) for s,h in zip(slots,held)]
    chosen=[0]*len(ranges)
    suffix=[1]*(len(ranges)+1)
    for i in range(len(ranges)-1,-1,-1):suffix[i]=suffix[i+1]*len(ranges[i])

    def walk(i,goods):
        if i==len(ranges):
            yield tuple(chosen)
            return
        offer=offers[i];original=ranges[i];m=offer.material
        allowed=min(len(original),remaining[m]//original.step+1)
        stats['prunedLeaves']+=(len(original)-allowed)*suffix[i+1]
        for j in range(allowed):
            stats['visitedPrefixes']+=1
            limit = max_prefix_nodes() if callable(max_prefix_nodes) else max_prefix_nodes
            if stats['visitedPrefixes']>limit:
                raise ValueError('event-tree prefix node limit; no approximate result returned')
            q=j*original.step
            # Same offer order and arithmetic as the ledger's goods reduction.
            payment=goods+q*offer.price
            if payment>cash:
                stats['prunedLeaves']+=(allowed-j)*suffix[i+1]
                break
            chosen[i]=q;remaining[m]-=q
            if prune is not None and prune(tuple(chosen[:i+1])):
                stats['prunedLeaves']+=suffix[i+1]
                stats['boundPrunedLeaves']+=suffix[i+1]
                stats['boundPrunedPrefixes']+=1
            else:
                yield from walk(i+1,payment)
            remaining[m]+=q
    yield from walk(0,0.)
