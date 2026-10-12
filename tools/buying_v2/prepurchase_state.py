"""Read-only sampled T2 state; not a forecast, executable policy or checkpoint.

Caller must pass the overhead snapshot taken at phase entry. Capturing it anew at
buyer entry changes the gate when earlier buyers changed equity or receipts.
"""
from copy import deepcopy
import math
import numpy as np
from economy.core import model as M
from economy.kernel import tick as K
from .discovery import sample_distinct


def capture_t2(w, cfg, tick, firm, phase, book, phase_overhead):
    """Capture immediately before this buyer's purchases, once per phase.

    Preserve fractional quantities and pending seller settlements separately.
    All installed lines and held materials are included, even outside this phase.
    Only discovered offers are exported; this is an opt-in diagnostic operation.
    """
    if not 0 <= firm < cfg['t2FirmCount'] or phase not in M.TIER_BOUNDARIES['T2']:
        raise ValueError('invalid active firm or production phase')
    if book.world is not w or book.tick != tick:
        raise ValueError('book does not belong to this world/tick')
    if phase_overhead is None or len(phase_overhead) < cfg['t2FirmCount']:
        raise ValueError('phase-entry overhead snapshot required')
    ids = [int(w.t2FirmLines[firm*M.T2_MAX_PRODUCTS_PER_FIRM+s])
           for s in range(int(w.t2FirmLineCount[firm]))]
    active = [i for i in ids if M.T2_PRODUCTS[int(w.t2LineProduct[i])]['complexity'] == phase]
    materials = sorted({int(m) for i in active
                        for m, _ in M.T2_PRODUCTS[int(w.t2LineProduct[i])]['ingredients']})
    slots, output_slot, _ = K.tier2_storage_layout(w, cfg, firm)

    def seller(s):
        return dict(supplier=int(s), owner=int(book.owner[s]),
                    current={k:float(getattr(book,k)[s]) for k in book._initial},
                    opening={k:float(v[s]) for k,v in book._initial.items()})

    inputs = []
    offers = []
    for m in range(M.NI):
        raw, basis, width = ((w.t2Raw,w.t2RawBasis,M.NE) if m < M.NE
                            else (w.t2T1Raw,w.t2T1Basis,M.NI))
        incumbent = int(w.t2Preferred[firm*M.NI+m])
        inputs.append(dict(material=m,held=float(raw[firm*width+m]),
                           basis=float(basis[firm*width+m]),slot=float(slots[m]),
                           space=float(M.T2_INPUT_PRODUCTS[m]['complexity']),incumbent=incumbent))
        if m in materials:
            eligible = np.array(sorted(s for s in book.offers[m] if math.isfinite(book.price[s])),dtype=np.int64)
            selected = sample_distinct(eligible,incumbent,cfg['seed'],tick,firm,m)
            offers.append(dict(material=m,eligibleCount=len(eligible),
                               suppliers=[seller(int(s)) for s in selected]))
    lines = []
    for i in ids:
        p = M.T2_PRODUCTS[int(w.t2LineProduct[i])]
        lines.append(dict(line=i,product=int(w.t2LineProduct[i]),
                          complexity=p['complexity'],ingredients=deepcopy(p['ingredients']),
                          outputQty=p['outputQty'],finished=float(w.t2Fin[i]),
                          basis=float(w.t2FinBasis[i]),quote=float(w.t2Price[i]),
                          sellerBook=seller(book.n1+i)))
    owner = M.N1+firm
    return dict(schema=1,boundary='before-company-phase-purchases',tick=tick,firm=firm,phase=phase,
                config=deepcopy(cfg),activeLines=active,installedLines=ids,
                productionOrder=active,materials=inputs,offers=offers,lines=lines,
                cash=float(w.t2Cash[firm]),equipmentBook=float(w.t2EqBook[firm]),
                rentArrears=float(w.t2RentArrears[firm]),
                switchingIncome=float(w.t2SwitchingIncome[firm]),
                switchingExpense=float(w.t2SwitchingExpense[firm]),
                switchingNetEMA=float(w.t2SwitchingNetEMA[firm]),
                loyaltyMultiples=np.asarray(w.lm2).tolist(),
                phaseEntryOverheadPerLine=float(phase_overhead[firm]),
                outputSlotSpace=float(output_slot),
                goodsSpace=float(K.tier2_goods_space(w,cfg,firm)),
                inventorySpace=float(K.tier2_inventory_units(w,firm)),
                pendingSellerCash=float(book.cash[owner]-book._cash_initial[owner]),
                pendingSwitchingIncome=float(book.switch_income[owner]-book._income_initial[owner]),
                missingPlannerInputs=['adopted forecast','continuation horizon','terminal valuation'],
                scope='Raw diagnostic state; no continuation projection or policy adoption.')
