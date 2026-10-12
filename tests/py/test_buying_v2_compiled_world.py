import unittest
import numpy as np
from economy.core import model as M
from economy.core.state import add_tier2_line
from economy.server.runtime import KernelRuntime
from tools.buying_v2.engine import IndustrialReferenceEngine, ManufacturerCompiledEngine, IndustrialCompiledEngine


class CompiledIndustrialWorldTests(unittest.TestCase):
    def check_engines(self, compiled_type, population=300, ticks=6):
        runtimes=[KernelRuntime(dict(t2FirmCount=population,distributorCount=1000,seed=137)) for _ in range(2)]
        for rt in runtimes:
            w=rt.world
            for firm in (0,20,100):
                native=M.T2_PRODUCTS[int(w.t2LineProduct[w.t2FirmLines[firm*M.T2_MAX_PRODUCTS_PER_FIRM]])]
                other=next(p for p in M.T2_PRODUCTS if p['invented'] and p['sectorIndex']==native['sectorIndex'] and p['complexity']<=native['complexity'] and p['id']!=native['id'])
                add_tier2_line(w,rt.cfg,firm,other,paid=False)
        engines=[IndustrialReferenceEngine(runtimes[0]),compiled_type(runtimes[1])]
        for tick in range(1,ticks+1):
            for engine in engines:
                engine.step(tick)
            a,b=[rt.world for rt in runtimes]
            for name in a.array_names:
                np.testing.assert_array_equal(getattr(a,name),getattr(b,name),err_msg=f'{name} tick {tick}')
            for name in ('costSinks','equipmentSinks','lm1','lm3','aov1','aov3'):
                self.assertEqual(getattr(a,name),getattr(b,name),f'{name} tick {tick}')
            self.assertEqual(runtimes[0].state,runtimes[1].state)
            np.testing.assert_array_equal(engines[0].industrial_observations,engines[1].industrial_observations)

    def test_manufacturer_compilation_preserves_full_world(self):
        self.check_engines(ManufacturerCompiledEngine)

    def test_both_tiers_compilation_preserves_full_world(self):
        self.check_engines(IndustrialCompiledEngine, population=4200, ticks=4)

    def test_fractional_owned_inputs_are_rejected_without_transfers(self):
        from economy.core.state import reset_world
        from economy.kernel import numba as N
        from tools.buying_v2 import refinery_compiled as R, manufacturer_compiled as T
        for tier in (1,2):
            cfg,w=reset_world(dict(t2FirmCount=3,distributorCount=1,seed=137))
            if tier==1:
                w.raw[0]=.5
            else:
                p=M.T2_PRODUCTS[int(w.t2LineProduct[0])]
                m=p['ingredients'][0][0]
                (w.t2Raw if m<M.NE else w.t2T1Raw)[m]=.5
            fields=('raw','rawBasis','t0Inv','t0Cash','t1Cash','t2Cash','t2Raw','t2T1Raw','t0Revenue','t1Revenue','t2Revenue')
            before={name:getattr(w,name).copy() for name in fields}
            with self.assertRaisesRegex(ValueError,'nonintegral owned input'):
                if tier==1:
                    N.plan_and_buy_inputs(w,cfg,0,purchase_company=R.buy,execution_kernel=R.phase_kernel)
                else:
                    N._operate_tier2_phase(w,cfg,0,p['complexity'],purchase_company=T.buy,execution_kernel=T.phase_kernel)
            for name,value in before.items():
                np.testing.assert_array_equal(getattr(w,name),value,err_msg=name)


if __name__=='__main__':
    unittest.main()
