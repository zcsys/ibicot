import unittest
from dataclasses import replace
from tools.buying_v2.phase_oracle import solve
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.fee_boundary_study import fee_case,income_case
from test_buying_v2_persistent_supply import fixture

class BoundAuditTests(unittest.TestCase):
    def test_shadow_audit_preserves_all_outputs_and_detects_useful_bounds(self):
        cases=[case(1,1,2,2),fee_case(7.,3.,3),income_case(.5)]
        c,s,path=fixture(2);cases.append((c,s,(path,)))
        useful=0
        for args in cases:
            for mode in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    base=solve(*args,funding=mode,supply=supply)
                    audited=solve(*args,funding=mode,supply=supply,audit_continuation_bound=True)
                    stats=audited.pop('boundAudit');base.pop('boundAudit')
                    self.assertEqual(base,audited)
                    self.assertGreater(stats['checked'],0)
                    self.assertGreaterEqual(stats['minSlack'],0.)
                    useful+=stats['wouldPrune']
        self.assertGreater(useful,0)

    def test_cancellation_and_tiny_sale_scales(self):
        for scale in (1e-8,1.,1e8):
            c,s,paths=case(1,1,1,1)
            c=replace(c,lines=(replace(c.lines[0],conversion=.5*scale,quote=10.*scale),))
            s=replace(s,cash=100.*scale,quotes=(10.*scale,))
            event=paths[0].events[0]
            event=replace(event,offers=tuple(replace(o,price=o.price*scale) for o in event.offers))
            paths=(replace(paths[0],events=(event,)+paths[0].events[1:]),)
            r=solve(c,s,paths,funding='continuation',audit_continuation_bound=True)
            self.assertGreaterEqual(r['boundAudit']['minSlack'],0.)

    def test_invalid_flag_rejected(self):
        with self.assertRaises(ValueError):solve(*case(1,1,1,1),funding='continuation',audit_continuation_bound='yes')

if __name__=='__main__':unittest.main()
