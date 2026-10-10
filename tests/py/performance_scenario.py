"""Behavior fixture with all complexities, multiple machines and live edits.

Also executable against an unmodified baseline via PYTHONPATH to regenerate
its oracle. The oracle excludes only wall-clock performance telemetry.
"""
from pathlib import Path
import json
import tempfile

import numpy as np

from economy.core import model as M
from economy.core.state import add_tier2_line
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint, load_checkpoint
from tools.performance import fingerprint, digest


def scenario():
    rt = KernelRuntime({'t2FirmCount': 6000, 'distributorCount': 800, 'seed': 9137,
                        'storage': 50000, 't2Equity': 6000000, 'conversionFactor': .37,
                        't2Capacity': {3: 73, 4: 46, 5: 29}, 'elasticity': 1.7})
    w = rt.world
    for p in [p for p in M.T2_PRODUCTS if p['sectorIndex'] == w.t2Sector[0] and p['id'] != 0][:3]:
        add_tier2_line(w, rt.cfg, 0, p)
    rt.set_ownership_enforcement(False)
    rt.player('T1', 0, 'W', 1.87, True, 'PLAYER')
    rt.buy_equipment('T1', 0, 'W+E')
    products, first = np.unique(w.t2LineProduct[:w.t2LineCount], return_index=True)
    w.distributorProduct[:len(products)] = products + M.NP
    w.distributorPreferredSupplier[:len(products)] = first
    rt.player('T2', 0, M.T2_PRODUCTS[0]['code'], 4.17, True, 'PLAYER')
    rt.player('T0', 0, 'Water', 1.32, True, 'PLAYER')
    rt.watch_companies({'T0': [0, 7], 'T1': [0, 500]})
    rt.select('T2', 0)
    result = {}
    with tempfile.TemporaryDirectory() as tmp:
        rt.statsPath = Path(tmp) / 'stats.jsonl'
        for tick in range(1, 62):
            if tick == 17:
                rt.apply_config({'t2MaterialCost': 2.17, 'conversionFactor': .43,
                                 't2Capacity': {3: 23000, 4: 12000, 5: 8000},
                                 'loyaltyMultiple': {1: 9, 2: {3: .3, 4: 2, 5: .8}, 3: .9},
                                 'researchPriceMinimumOpportunities': 2, 'researchPriceMaxObservationTicks': 14})
            if tick == 33:
                rt.apply_config({'researchPriceMinimumOpportunities': 0, 'elasticity': 2.3})
            rt.step()
            rt.publish()
            if tick in (1, 16, 17, 29, 30, 31, 33, 60, 61):
                result[str(tick)] = fingerprint(rt)
            if tick == 31:
                path = str(Path(tmp) / 'checkpoint')
                save_checkpoint(path, rt.cfg, rt.tick, w, rt.state, rt.checkpoint_metadata())
                cfg, saved_tick, loaded, scalars = load_checkpoint(path)
                assert saved_tick == rt.tick
                rt.cfg, rt.world = cfg, loaded
                rt._init_admin()
                rt.restore_metadata(scalars['runtimeMetadata'])
                w = loaded
        pages = {}
        for sort in ('id', 'name', 'sector', 'cash', 'equity', 'inventory', 'raw', 'finished',
                     'capacity', 'utilization', 'margin', 'revenue', 'grossProfit', 'reliability'):
            for descending in (False, True):
                rt.tier2Query.update(sort=sort, descending=descending, page=1)
                pages[f'{sort}/{descending}'] = digest(rt._tier2_page())
        for search, sector, controller in (('0x', '', ''), ('systems', '', ''),
                ('', M.T2_SECTORS[3], ''), ('', '', 'PLAYER'), ('', '', 'BOT'),
                ('none found', '', ''), ('', 'unknown sector', ''), ('', '', 'invalid')):
            rt.tier2Query.update(search=search, sector=sector, controller=controller)
            pages[f'{search}/{sector}/{controller}'] = digest(rt._tier2_page())
        result['pages'] = pages
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = scenario()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    if args.verify:
        assert result == json.loads(args.verify.read_text()), 'Scenario behavior changed'
        print('Scenario: exact baseline match (configuration, controls, equipment, checkpoint, pages).')
