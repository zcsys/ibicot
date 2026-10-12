import hashlib
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
import numpy as np
from tools.buying_v2.seller_history import SellerHistory
from tools.buying_v2.forecast_screen import evaluate
from test_buying_v2_forecast import PARAMETERS


class ForecastScreenTests(unittest.TestCase):
    def test_known_sales_errors_and_selected_channel_subset(self):
        h=SellerHistory(3)
        for channel in ('retail','another-phase'):
            for tick,sold in ((1,[2.,6.]),(2,[4.,8.])):
                sales=np.array(sold)
                h.record(channel,tick,np.array([3,3]),np.array([0,1]),np.ones(2),
                         np.full(2,10.),10.-sales,np.full(2,2.),sales,np.array([[1,1],[1,1],[0,0]]))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'history.npz';h.save(path)
            spec=dict(history=str(path),historySha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      historyEndTick=2,channels=['retail'],evaluationTicks=[2,2],samplingSeed=137,
                      sellersPerProduct=2,profiles={'example':asdict(PARAMETERS)})
            result=evaluate(spec)
            rows=result['results'][0]['scores']
            self.assertEqual(len(rows),3)
            self.assertEqual(result['results'][0]['sampledSellerIds'],[0,1])
            for row in rows:
                self.assertEqual(row['observations'],2)
                self.assertAlmostEqual(row['actualItems'],12.)
                self.assertAlmostEqual(row['forecastItems'],8.)
                self.assertAlmostEqual(row['bias'],-2.)
                self.assertAlmostEqual(row['MAE'],2.)
            paired=evaluate({**spec,'feedbackModes':['inquiries','transactions']})
            pairs=paired['results'][0]['scores']
            self.assertEqual(len(pairs),6)
            for inquiry,transaction in zip(pairs[:3],pairs[3:]):
                self.assertEqual(inquiry['feedback'],'inquiries')
                self.assertEqual(transaction['feedback'],'transactions')
                self.assertEqual({k:v for k,v in inquiry.items() if k!='feedback'},
                                 {k:v for k,v in transaction.items() if k!='feedback'})
            for modes in ([],['unknown'],['transactions','transactions']):
                with self.assertRaisesRegex(ValueError,'feedback modes'):
                    evaluate({**spec,'feedbackModes':modes})
            with self.assertRaisesRegex(ValueError,'identity changed'):
                evaluate({**spec,'historySha256':'wrong'})
            with self.assertRaisesRegex(ValueError,'selected history'):
                evaluate({**spec,'channels':['missing']})


if __name__=='__main__':unittest.main()
