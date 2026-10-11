"""Names cannot import the commission's new mechanics, roles, or fiction."""
import json
import re
import subprocess
import unittest
from pathlib import Path
from economy.core import model as M
from economy.core.state import T0P

ROOT=Path(__file__).resolve().parents[2]

class NamingCatalogTests(unittest.TestCase):
    def test_every_existing_recipe_has_accepted_name_and_machine(self):
        source=json.loads((ROOT/'catalogs/midbridge-4259-recursive/naming.json').read_text())
        names={p['recipe_id']:p for p in source['products']}
        rows=M.PRODUCTS+M.T2_Catalog
        self.assertEqual({p['catalogId'] for p in rows},set(names))
        for p in rows:
            n=names[p['catalogId']]
            self.assertEqual(p['name'],n['product_name'])
            self.assertEqual(p['installationName'],n['installation_name'])
            self.assertEqual(p['machineFamily'],n['machine_family'])
            self.assertEqual(p['formula'],n['unchanged_formula'])
        for sector,offset in enumerate(M.T2_SECTOR_FIRM_OFFSETS):
            self.assertEqual(M.t2_firm_name(sector,offset),source['t2_companies'][sector]['flagship_name']+' '+M.company_number('T2',offset))
            self.assertEqual(M.t2_firm_name(sector,offset+1),source['t2_companies'][sector]['generic_stem']+' '+M.company_number('T2',offset+1))
        for i,c in enumerate(T0P):self.assertEqual(c['name'],source['t0_companies'][i]['name'])

    def test_no_new_fiction_roles_or_economic_fields(self):
        legacy=json.loads((ROOT/'economy/core/catalog.json').read_text())
        self.assertEqual(M.WORLD_STORY,{**legacy['WORLD_STORY'],'name':'Midbridge Colony'})
        self.assertEqual(M.EQUIPMENT_MAKERS,[T0P[6]['name']])
        forbidden={'scope','interpretation','physical_use','physical_description','downstream_role','role','initiative_name','setting','rules','equipment_makers'}
        def check(v):
            if isinstance(v,dict):
                self.assertFalse(forbidden & v.keys())
                for x in v.values():check(x)
            elif isinstance(v,list):
                for x in v:check(x)
        check(M.NAMING_CATALOG)
        for p in M.T2_PRODUCTS:
            original=next(x for x in legacy['T2_PRODUCTS'] if x['complexity']==p['complexity'])
            for field in ['equipmentPrice','conversionCost','needWeight','demandWeight','demandFactor','reservationPremium','distributorValue','needType','kind']:
                self.assertEqual(p[field],original[field],(p['catalogId'],field))
        self.assertEqual(M.COMPANY_NUMBERING['T2']['start'],1029)
        self.assertEqual(M.N2_FIRMS,57960)

    def test_browser_names_and_symbols_match_python(self):
        script="require('./web/catalog.js');require('./web/midbridge-catalog.js'); const m=globalThis.Phase0Model; console.log(JSON.stringify([m.PRODUCTS,m.T2_PRODUCTS,m.NAMING_CATALOG,m.T2_NEED_TYPES,m.EQUIPMENT_MAKERS]));"
        data=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
        self.assertEqual(data,[M.PRODUCTS,M.T2_PRODUCTS,M.NAMING_CATALOG,M.T2_NEED_TYPES,M.EQUIPMENT_MAKERS])
