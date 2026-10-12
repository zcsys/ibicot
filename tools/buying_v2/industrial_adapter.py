"""Actual-resource T2 adapter for isolated purchasing experiments.

Default problems contain no assumed output valuation. Workload-only callers can
explicitly request synthetic own-quote output tables with disabled fees.
"""
import math
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from .discovery import sample_distinct
from .industry_oracle import Problem, Offer, Line


def company_problem(w, cfg, tick, firm, phase, book, overhead, *, workload_values=False):
    line_ids = w.t2FirmLines[firm*M.T2_MAX_PRODUCTS_PER_FIRM:firm*M.T2_MAX_PRODUCTS_PER_FIRM + int(w.t2FirmLineCount[firm])]
    line_ids = [int(i) for i in line_ids if M.T2_PRODUCTS[int(w.t2LineProduct[i])]['complexity'] == phase]
    materials = sorted({m for line in line_ids for m, q in M.T2_PRODUCTS[int(w.t2LineProduct[line])]['ingredients']})
    index = {m: i for i, m in enumerate(materials)}
    slots, output_slot, _ = K.tier2_storage_layout(w, cfg, firm)
    held, basis, spaces = [], [], []
    offers, incumbents, lines = [], [], []
    for m in materials:
        arr, costs, width = (w.t2Raw, w.t2RawBasis, M.NE) if m < M.NE else (w.t2T1Raw, w.t2T1Basis, M.NI)
        held.append(int(arr[firm*width + m]))
        basis.append(float(costs[firm*width + m]))
        spaces.append(float(M.T2_INPUT_PRODUCTS[m]['complexity']))
        incumbent = int(w.t2Preferred[firm*M.NI+m])
        incumbents.append(incumbent)
        eligible = np.array(sorted(s for s in book.offers[m] if math.isfinite(book.price[s])), dtype=np.int64)
        sampled = sample_distinct(eligible, incumbent, cfg['seed'], tick, firm, m)
        for supplier in sampled:
            offers.append(Offer(index[m], int(supplier), float(book.price[supplier]), int(book.fin[supplier])))
    for line in (line_ids if workload_values else []):
        product = M.T2_PRODUCTS[int(w.t2LineProduct[line])]
        output_qty = int(product['outputQty'])
        bound = int(max(0, min(cfg['t2Capacity'][phase], math.floor(output_slot / phase) - w.t2Fin[line])) // output_qty)
        recipe = [0] * len(materials)
        for m, q in product['ingredients']:
            recipe[index[m]] += int(q)
        lines.append(Line(tuple(recipe), bound, float(M.conversion_cost(phase, cfg)), float(w.t2Price[line]),
                          float(overhead[firm]), tuple(float(w.t2Price[line])*y for y in range(bound*output_qty+1)),
                          float(phase), output_qty))
    caps = tuple(max(held[j], int(math.floor(slots[m]))) for j,m in enumerate(materials))
    free = max(0., K.tier2_goods_space(w, cfg, firm) - K.tier2_inventory_units(w, firm))
    native_class = M.T2_PRODUCTS[int(w.t2LineProduct[w.t2FirmLines[firm*M.T2_MAX_PRODUCTS_PER_FIRM]])]['complexity']-3
    fees = tuple(M.loyalty_charge(M.material_switching_reference(cfg), book.rel[s], w.lm2[native_class])
                 if s in book.offers[m] else 0. for m,s in zip(materials,incumbents))
    p = Problem(tuple(held), tuple(basis), tuple(spaces), caps, free, float(w.t2Cash[firm]), tuple(offers),
                tuple(incumbents), (0,)*len(materials), (0.,)*len(materials) if workload_values else fees, tuple(lines),
                tuple((0.,)*(cap+1) for cap in caps), cfg['productionMarginBand'])
    return p, dict(firm=firm, phase=phase, lines=line_ids, materials=materials)



def buy_t2_reference(w, cfg, tick, firm, phase, book, *, max_nodes=100000, observations=None, exposure=None, trace=None):
    """Plan and atomically settle one company's phase under D3 comparison rules.

    The caller owns the phase boundary and invokes this once per company/phase.
    Seller receipts remain in the book until its ordinary phase-end settlement.
    """
    from .funding import replenishment_plan
    from .industrial_settlement import settle_t2
    problem, identity = company_problem(w,cfg,tick,firm,phase,book,None)
    if not identity['materials']:
        return None
    funded, result = replenishment_plan(problem,max_nodes)
    postings = settle_t2(w,cfg,firm,phase,book,funded,result[0],identity['materials'],funded.funded_demands,observations,exposure,trace)
    return dict(identity=identity, problem=funded, allocation=result[0], postings=postings)
