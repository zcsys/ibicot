"""Names cannot import the commission's new mechanics, roles, or fiction."""
import json
import subprocess
import unittest
from pathlib import Path
from economy.core import model as M
from economy.core.state import T0P

ROOT = Path(__file__).resolve().parents[2]
SOURCE = json.loads((ROOT / 'catalogs/midbridge-4263/naming-source.json').read_text())


class NamingCatalogTests(unittest.TestCase):
    def test_every_existing_recipe_has_accepted_name_and_machine(self):
        names = {p['recipe_id']: p for p in SOURCE['recipes']}
        rows = M.PRODUCTS + M.T2_Catalog
        self.assertEqual({p['catalogId'] for p in rows}, set(names))
        for p in rows:
            n = names[p['catalogId']]
            self.assertEqual(p['name'], n['product_name'])
            self.assertEqual(p['installationName'], n['installation_name'])
            self.assertEqual(p['machineFamily'], n['machine_family'])
            self.assertEqual(p['formula'], n['unchanged_formula'])

    def test_t0_names_match_current_source(self):
        names = [c['name'] for c in SOURCE['t0_companies']]
        self.assertEqual(len(names), 20)
        self.assertIn('Old Toby & Daughters, Inc.', names)
        self.assertIn('The Oligarch', names)
        self.assertEqual([c['name'] for c in T0P], names)

    def test_no_new_fiction_roles_or_economic_fields(self):
        defaults = json.loads((ROOT / 'catalogs/midbridge-4263/runtime-defaults.json').read_text())
        self.assertEqual(M.WORLD_STORY, defaults['constants']['WORLD_STORY'])
        self.assertEqual(M.EQUIPMENT_MAKERS, [T0P[6]['name']])
        forbidden = {'scope', 'interpretation', 'physical_use', 'physical_description',
                     'downstream_role', 'role', 'initiative_name', 'setting', 'rules',
                     'equipment_makers'}

        def check(v):
            if isinstance(v, dict):
                self.assertFalse(forbidden & v.keys())
                for x in v.values():
                    check(x)
            elif isinstance(v, list):
                for x in v:
                    check(x)
        check(M.NAMING_CATALOG)
        for p in M.T2_PRODUCTS:
            original = defaults['manufacturerTemplates'][str(p['complexity'])]
            for field in ['equipmentPrice', 'conversionCost', 'needWeight', 'demandWeight',
                          'demandFactor', 'reservationPremium', 'distributorValue',
                          'needType', 'kind']:
                self.assertEqual(p[field], original[field], (p['catalogId'], field))
        self.assertEqual(M.COMPANY_NUMBERING['T2']['start'], 1003)
        self.assertEqual(M.N2_FIRMS, 57960)

    def test_browser_names_and_symbols_match_python(self):
        script = ("require('./web/model-helpers.js');require('./web/midbridge-catalog.js'); "
                  "const m=globalThis.Phase0Model; console.log(JSON.stringify("
                  "[m.PRODUCTS,m.T2_Catalog,m.NAMING_CATALOG,m.T2_NEED_TYPES,"
                  "m.EQUIPMENT_MAKERS,m.ELEMENTS]));")
        data = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT, text=True))
        self.assertEqual(data, [M.PRODUCTS, M.T2_Catalog, M.NAMING_CATALOG,
                                M.T2_NEED_TYPES, M.EQUIPMENT_MAKERS, M.ELEMENTS])

    def test_all_company_stems_resources_and_equipment(self):
        self.assertEqual(M.ELEMENTS, ['Organics', 'Inorganics', 'Metals', 'Radioactives'])
        stems = {c['sector_id']: c['generic_stem'] for c in SOURCE['t1_companies']}
        for cid in range(M.N1):
            sector = 'S1-%02d' % (M.T1_FIRM_PRODUCT[cid] + 1)
            self.assertEqual(M.t1_firm_name(cid), stems[sector] + ' ' + M.company_number('T1', cid))
        for sector, (offset, count) in enumerate(zip(M.T2_SECTOR_FIRM_OFFSETS, M.T2_SECTOR_FIRM_COUNTS)):
            stem = SOURCE['t2_companies'][sector]['facility_stem']
            for cid in range(offset, offset + count):
                self.assertEqual(M.t2_firm_name(sector, cid), stem + ' ' + M.company_number('T2', cid))
        # Neither tier has flagship names.
        self.assertFalse(any('flagship' in c for c in SOURCE['t1_companies']))
        self.assertFalse(any('flagship' in c for c in SOURCE['t2_companies']))

    def test_generator_matches_current_runtime_metadata(self):
        from tools.build_naming_metadata import build_names
        names = build_names()
        self.assertEqual(names, M.NAMING_CATALOG)

    def test_machine_families_and_sectors_match_current_catalog(self):
        catalog = M.NAMING_CATALOG
        # T1 equipment families
        t1 = {f['sector_id']: f['family'] for f in SOURCE['t1_equipment_families']}
        got_t1 = {f['sector_id']: f['name'] for f in catalog['machine_families'] if f['tier'] == 'T1'}
        self.assertEqual(got_t1, t1)
        # T2 equipment families
        t2 = {(f['sector_id'], f['complexity']): f['family'] for f in SOURCE['t2_equipment_families']}
        got_t2 = {(f['sector_id'], f['complexity']): f['name'] for f in catalog['machine_families'] if f['tier'] == 'T2'}
        self.assertEqual(got_t2, t2)
        # T2 sector names
        self.assertEqual([s['name'] for s in catalog['t2_sectors']],
                         [s['name'] for s in SOURCE['t2_sectors']])
        # Refinery sector names
        self.assertEqual([m['refinery_sector_name'] for m in catalog['materials']],
                         [m['refinery_sector_name'] for m in SOURCE['refined_materials']])


if __name__ == '__main__':
    unittest.main()
