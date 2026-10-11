"""Public company identity is global; internal array indexes remain tier-local."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from economy.core import model as M
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint,load_checkpoint


class CompanyNumberTests(unittest.TestCase):
    def test_ranges_are_contiguous_unique_and_reversible(self):
        expected=0
        for tier,block in M.COMPANY_NUMBERING.items():
            self.assertEqual(block['start'],expected)
            for cid in {0,block['count']//2,block['count']-1}:
                number=M.company_number(tier,cid)
                self.assertEqual(int(number,16),expected+cid)
                self.assertEqual(M.company_from_number(number),(tier,cid))
            expected += block['count']
        self.assertEqual(expected,1+M.N0+M.N1+M.N2_FIRMS+M.N_DISTRIBUTORS)
        self.assertEqual(M.company_number(-1,0),'0x0')
        self.assertEqual(M.company_number(0,0),'0x1')
        self.assertEqual(M.company_number(0,1),'0x2')
        self.assertNotEqual(M.t1_firm_name(0).split()[-1],M.t1_firm_name(100).split()[-1])
        for value in ['1','-0x1','0xz','0x100000000']:
            with self.assertRaises(ValueError):M.company_from_number(value)
        with self.assertRaises(ValueError):M.company_number('T2',M.N2_FIRMS)

    def test_snapshot_lookup_and_checkpoint_keep_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('economy.server.runtime._STATS_DIR',Path(directory)),patch('economy.server.service._STATS_DIR',Path(directory)):
                rt=KernelRuntime({'t2FirmCount':2,'distributorCount':3})
                snapshot=rt.publish()
                self.assertEqual(snapshot['companyRegistry']['gaia']['companyNumber'],'0x0')
                self.assertEqual(rt.company_detail(None,'0x0')['name'],'Gaia')
                self.assertEqual(snapshot['t0Companies'][0]['name'],'Raw Materials Corp.')
                for tier,cid in [('T0',0),('T1',100),('T2',1),('T3',2)]:
                    number=M.company_number(tier,cid)
                    self.assertEqual(rt.company_detail(None,number)['companyNumber'],number)
                    self.assertEqual(rt.company_detail(tier,cid)['id'],cid)
                with self.assertRaises(ValueError):rt.company_detail('T1','0x1')
                self.assertIsNone(rt.company_detail('T3',3))
                self.assertEqual(snapshot['companies'][100]['companyNumber'],M.company_number('T1',100))
                path=str(Path(directory)/'checkpoint')
                save_checkpoint(path,rt.cfg,0,rt.world,{})
                meta=json.loads(Path(path+'.json').read_text())
                self.assertEqual(meta['companyNumbering'],M.COMPANY_NUMBERING)
                cfg,_,_,_=load_checkpoint(path)
                self.assertEqual(M.company_registry(cfg),snapshot['companyRegistry'])

    def test_browser_numbering_matches_python(self):
        root=Path(__file__).resolve().parents[2]
        script="""
require('./web/catalog.js');require('./web/midbridge-catalog.js');
const m=globalThis.Phase0Model;
const rows=[];
for(const [tier,b] of Object.entries(m.COMPANY_NUMBERING)){
 for(const id of [0,b.count-1]){
  const number=m.companyNumber(tier,id);
  if(m.companyLocalId(tier,number)!==id)throw Error('bad inverse');
  rows.push([tier,id,number]);
 }
}
if(m.companyLocalId('T2','0x1')!==null || m.companyLocalId('T2','1421')!==null)throw Error('invalid number accepted');
console.log(JSON.stringify(rows));
"""
        rows=json.loads(subprocess.check_output(['node','-e',script],cwd=root,text=True))
        for tier,cid,number in rows:self.assertEqual(number,M.company_number(tier,cid))
