"""Recursive demand, procurement, and independent accounting invariants."""
import copy
import unittest
from collections import Counter
import numpy as np
from economy.core import model as M
from economy.core.state import reset_world, validate_storage
from economy.core.accounting import company_earnings
from economy.kernel import tick as K, numba as NB


class RecursiveDemandTests(unittest.TestCase):
    def test_final_demand_matches_weighted_dependency_flow(self):
        self.assertEqual(Counter(p['complexity'] for p in M.T2_PRODUCTS), {3:36,4:69})
        demands = {p['catalogId']: float(p['distributorWeight']) for p in M.T2_PRODUCTS}
        for p in sorted(M.T2_PRODUCTS,key=lambda p:-p['complexity']):
            for m,q in p['ingredients']:
                key = M.T2_INPUT_PRODUCTS[m]['catalogId']
                demands[key] = demands.get(key,0) + q * demands[p['catalogId']]
        self.assertTrue(all(demands[p['catalogId']]>0 for p in M.PRODUCTS))
        self.assertEqual(sum(M.T2_FINAL_DEMAND_WEIGHTS.values()),1598976)
        for p in M.T2_PRODUCTS:
            self.assertEqual(demands[p['catalogId']],M.T2_PRODUCT_FIRM_COUNTS[p['id']]*M.T2_ALLOCATION_CAPACITIES[p['complexity']])

    def test_uninvented_recipes_stay_out_of_operations(self):
        self.assertEqual(len(M.T2_Catalog),255)
        self.assertEqual(len(M.T2_UNINVENTED_PRODUCTS),150)
        self.assertEqual(M.NI,50)
        active={p['catalogId'] for p in M.T2_PRODUCTS}
        self.assertEqual(len({p['sectorIndex'] for p in M.T2_PRODUCTS}),14)
        self.assertTrue(all(p['distributorWeight']==M.T2_FINAL_DEMAND_WEIGHTS[p['catalogId']] for p in M.T2_PRODUCTS))
        for p in M.T2_PRODUCTS:
            self.assertTrue(all(i in active or i.startswith(('C1-','C2-')) for i in p['ingredientCatalogIds']))
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':5980})
        from economy.core.state import add_tier2_line
        for p in M.T2_UNINVENTED_PRODUCTS:
            self.assertEqual(p['distributorWeight'],0)
            with self.assertRaises(ValueError):add_tier2_line(w,cfg,0,p,paid=False)

    def test_routing_is_stratified_and_independent_of_supply(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':5980})
        actual=np.bincount(w.distributorProduct[:5980]-M.NP,minlength=len(M.T2_PRODUCTS))
        expected=np.array([p['distributorWeight'] for p in M.T2_PRODUCTS],dtype=float)
        expected *= 5980/expected.sum()
        self.assertTrue(np.all(np.abs(actual-expected)<1))
        from economy.core.state import initialize_distributors
        old=w.distributorProduct.copy()
        cfg['t2Capacity'][3] *= 10
        initialize_distributors(w,cfg)
        np.testing.assert_array_equal(old,w.distributorProduct)

    def test_recursive_cost_reference(self):
        cfg,w=reset_world({'t2FirmCount':1,'distributorCount':1})
        p=next(p for p in M.T2_PRODUCTS if p['demandGroup']=='c4_basic_c3')
        c3=next(M.T2_INPUT_PRODUCTS[m] for m,q in p['ingredients'] if m>=M.NP)
        basic=next(M.T2_INPUT_PRODUCTS[m] for m,q in p['ingredients'] if m<M.NP)
        expected=(M.refinery_unit_cost(basic,cfg)+M.initial_tier2_cost(c3,cfg))*1.25+.75
        self.assertEqual(M.initial_tier2_cost(p,cfg),expected)

    def test_default_distributor_cohorts_cover_every_products_final_capacity(self):
        # Initialize the real million-buyer cohorts; a minimal seller fleet keeps
        # this routing audit cheap. Capacity below is the default full fleet.
        cfg,w=reset_world({'t2FirmCount':1})
        ids=w.distributorProduct[:cfg['distributorCount']]-M.NP
        self.assertTrue(np.all((ids>=0)&(ids<len(M.T2_PRODUCTS))))
        counts=np.bincount(ids,minlength=len(M.T2_PRODUCTS))
        gross=np.array([M.T2_PRODUCT_FIRM_COUNTS[p['id']]*cfg['t2Capacity'][p['complexity']]
                        for p in M.T2_PRODUCTS],dtype=float)
        intermediate=np.zeros(len(M.T2_PRODUCTS))
        product_ids={p['catalogId']:p['id'] for p in M.T2_PRODUCTS}
        for p in M.T2_PRODUCTS:
            for material,quantity in p['ingredients']:
                if material>=M.NP:
                    target=product_ids[M.T2_INPUT_PRODUCTS[material]['catalogId']]
                    intermediate[target]+=quantity*gross[p['id']]
        final=gross-intermediate
        self.assertTrue(np.all(final>0))
        self.assertTrue(np.all(np.abs(counts-cfg['distributorCount']*final/final.sum())<1))

        reference=np.array([M.initial_tier2_cost(p,cfg) for p in M.T2_PRODUCTS])
        price=np.array([M.round_to_cent(reference[p['id']]*(1+M.tier2_starting_markup(p,cfg)))
                        for p in M.T2_PRODUCTS])
        premium=np.array([1+cfg['t2ReservationPremium']*(p['complexity']-1) for p in M.T2_PRODUCTS])
        choke=reference[ids]*premium[ids]*w.distributorChoke[:len(ids)]
        # Expected demand before stock/search constraints. Stochastic rounding
        # preserves this expectation; activation is probabilistic each tick.
        quantity=w.distributorQMax[:len(ids)]/(1+(price[ids]/choke)**w.distributorEta[:len(ids)])
        demand=np.bincount(ids,weights=quantity*cfg['distributorActivation'],minlength=len(final))
        for p in M.T2_PRODUCTS:
            self.assertGreater(demand[p['id']],final[p['id']],p['catalogId'])

    def test_intermediate_trade_production_and_equity_both_engines(self):
        cfg,w=reset_world({'t2FirmCount':2,'distributorCount':1,'storageRentPerUnitYear':0})
        buyer=next(p for p in M.T2_PRODUCTS if p['demandGroup']=='c4_basic_c3')
        m=next(m for m,q in buyer['ingredients'] if m>=M.NP)
        seller=M.T2_INPUT_PRODUCTS[m]
        for firm,p in enumerate([seller,buyer]):
            w.t2LineProduct[firm]=p['id'];w.t2Sector[firm]=p['sectorIndex']
            w.t2Price[firm]=100
            for material,q in p['ingredients']:
                if material >= M.NP:continue
                raw,basis=(w.t2Raw,w.t2RawBasis) if material<M.NE else (w.t2T1Raw,w.t2T1Basis)
                idx=firm*(M.NE if material<M.NE else M.NI)+material
                raw[idx]=100;basis[idx]=2
        w.t2Fin[0]=100;w.t2FinBasis[0]=5
        before=K.storage_rent_equity(w,cfg,'t2').copy()
        reference=copy.deepcopy(w)
        K.operate_tier2(reference,cfg,M.PRODUCTS,K.T0P,M.T2_PRODUCTS,1)
        self.assertGreater(reference.t2IntermediateSold[seller['id']],0)
        self.assertEqual(reference.t2Made[0],32)
        # Buyer quote covers acquired C3 stock and produces at capacity.
        w.t2Price[1]=200;reference=copy.deepcopy(w)
        K.operate_tier2(reference,cfg,M.PRODUCTS,K.T0P,M.T2_PRODUCTS,1)
        self.assertEqual(reference.t2Made[1],24)
        np.testing.assert_allclose(K.storage_rent_equity(reference,cfg,'t2')-before,
                                   company_earnings(reference,cfg,'t2'),atol=1e-8,rtol=0)
        validate_storage(reference,cfg)
        if NB._HAVE_NUMBA:
            NB.operate_tier2(w,cfg,1)
            for name in w.array_names:
                np.testing.assert_allclose(getattr(w,name),getattr(reference,name),atol=1e-10,rtol=0,err_msg=name)
            self.assertAlmostEqual(w.costSinks,reference.costSinks)
