import copy,json,unittest
from tools.buying_v2.ownership_audit import audit,CATALOG,SELECTION


class OwnershipScopeTests(unittest.TestCase):
    def test_current_and_full_catalog_have_no_same_sector_input_edge(self):
        catalog=json.loads(CATALOG.read_text());selected=json.loads(SELECTION.read_text())['inventedRecipeIds']
        result=audit(catalog,selected)
        self.assertGreater(result['manufacturedInputEdges'],0)
        self.assertGreater(result['initiallyInventedEdges'],0)
        self.assertEqual(result['sameSectorEdges'],[])
        from economy.core import model as M
        self.assertEqual(set(selected),{p['catalogId'] for p in M.T2_PRODUCTS})

    def test_audit_detects_changed_ownership_scope(self):
        catalog=json.loads(CATALOG.read_text());selected=json.loads(SELECTION.read_text())['inventedRecipeIds']
        by={p['id']:p for p in catalog['products']}
        edge=audit(catalog,selected)['edges'][0]
        by[edge['output']]['sectorId']=by[edge['input']]['sectorId']
        changed=audit(catalog,selected)
        self.assertTrue(any(x['output']==edge['output'] and x['input']==edge['input'] for x in changed['sameSectorEdges']))
        bad=copy.deepcopy(catalog);bad['products'].append(bad['products'][0])
        with self.assertRaisesRegex(ValueError,'identities'):audit(bad,selected)

    def test_actual_installation_rejects_own_input_sector_and_duplicate_but_allows_multiline(self):
        from economy.core import model as M
        from economy.core.state import reset_world,add_tier2_line
        cfg,w=reset_world(dict(t2FirmCount=4200,distributorCount=1))
        line=next(i for i in range(int(w.t2LineCount)) if any(m>=M.NP for m,q in M.T2_PRODUCTS[int(w.t2LineProduct[i])]['ingredients']))
        product=M.T2_PRODUCTS[int(w.t2LineProduct[line])];firm=int(w.t2LineFirm[line])
        material=next(m for m,q in product['ingredients'] if m>=M.NP)
        source=M.T2_INPUT_PRODUCTS[material]
        count=int(w.t2LineCount);owned=int(w.t2FirmLineCount[firm])
        with self.assertRaisesRegex(ValueError,'sector and capability'):
            add_tier2_line(w,cfg,firm,source,paid=False)
        with self.assertRaisesRegex(ValueError,'already installed'):
            add_tier2_line(w,cfg,firm,product,paid=False)
        self.assertEqual(w.t2LineCount,count);self.assertEqual(w.t2FirmLineCount[firm],owned)
        other=next(p for p in M.T2_PRODUCTS if p['invented'] and p['sectorIndex']==product['sectorIndex']
                   and p['complexity']<=product['complexity'] and p['id']!=product['id'])
        installed=add_tier2_line(w,cfg,firm,other,paid=False)
        self.assertEqual(w.t2LineFirm[installed],firm)
        self.assertEqual(w.t2FirmLineCount[firm],owned+1)
        self.assertNotIn(other['id'],[M.T2_INPUT_PRODUCTS[m]['id'] for m,q in product['ingredients'] if m>=M.NP])


if __name__=='__main__':unittest.main()
