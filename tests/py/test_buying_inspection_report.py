import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.buying_v2.inspection_report import build,write
from tools.buying_v2.decision_traces import DecisionTrace


class InspectionReportTests(unittest.TestCase):
    def fixture(self,path):
        manifest=dict(status='complete',invariantGate=True,sourceIdentity='fixture',
                      specification=dict(window=[1,2],seed=137,treatment='fixture'))
        (path/'manifest.json').write_text(json.dumps(manifest))
        for tick in (1,2):
            document=DecisionTrace(1,1,137,tick,1,1).export()
            (path/f'decision-traces-{tick:06}.json').write_text(json.dumps([document]))
        return manifest

    def test_complete_window_and_missing_duplicate_or_wrong_tick_rejected(self):
        with tempfile.TemporaryDirectory() as directory,patch('tools.buying_v2.inspection_report.report',return_value={'rows':[]}):
            path=Path(directory);manifest=self.fixture(path)
            self.assertEqual(len(build(path)['traces']),2)
            file=path/'decision-traces-000002.json';good=file.read_text()
            file.unlink()
            with self.assertRaisesRegex(ValueError,'trace files'):
                build(path)
            file.write_text(good)
            document=json.loads(good)[0]
            file.write_text(json.dumps([document,document]))
            with self.assertRaisesRegex(ValueError,'duplicate'):
                build(path)
            document['tick']=1;file.write_text(json.dumps([document]))
            with self.assertRaisesRegex(ValueError,'tick/seed'):
                build(path)
            manifest['invariantGate']=False;(path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'accounting'):
                build(path)

    def test_output_is_exclusive_and_embedded_data_cannot_close_script(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.html'
            data={'run':'</script><script>alert(1)</script>','version':1}
            with patch('tools.buying_v2.inspection_report.build',return_value=data):
                write('unused',path)
                with self.assertRaises(FileExistsError):
                    write('unused',path)
            html=path.read_text()
            self.assertNotIn(data['run'],html)
            self.assertIn('\\u003c/script\\u003e',html)
            self.assertNotIn('/*__INSPECTOR_',html)

if __name__=='__main__':
    unittest.main()
