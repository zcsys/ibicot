"""Synthetic contract negatives only; never widget execution evidence."""
import copy,unittest
from content_contract import digest
from check_content_report import validate_row,validate

class CheckerCases(unittest.TestCase):
    def setUp(self):
        self.condition={'viewport':'phone','text_percent':100,'pseudo':False}
        self.want={'id':'asset.test','state':'read','route':'ActualScreen','fields':['title'],'assertions':['read_only'],'minimum_callbacks':1,'minimum_controls':1,'exact_english':{'title':'Example'}}
        ledger={'main':{},'story':{}}
        self.row={'id':'asset.test','state':'read','route':'ActualScreen','fixture':'Synthetic checker positive control; not production evidence.','condition':self.condition,'before':ledger,'after':ledger,'before_sha256':digest(ledger),'after_sha256':digest(ledger),'assertions':{'read_only':True},'texts':[{'field':'title','english':'Example','display':'Example','english_sha256':digest('Example'),'display_sha256':digest('Example'),'code_units':7,'line_boxes':1,'observed_line_boxes':[{'rect':[1,1,60,20],'viewport':[0,0,320,720]}],'complete_text':True,'untruncated':True,'all_lines_in_viewport':True}], 'controls':[{'id':'read','enabled':True,'rect':[1,21,61,81],'viewport':[0,0,320,720],'minimum_48':True,'whole_control_visible':True,'semantic_name':'Read','semantic_tap':True,'hit_points':5,'callback_invoked':True}]}
    def check(self):validate_row(self.row,self.want,self.condition)
    def rejects(self,edit):edit();self.assertRaises((ValueError,KeyError),self.check)
    def test_positive(self):self.check()
    def test_missing_paragraph(self):self.rejects(lambda:self.row['texts'].clear())
    def test_duplicate_paragraph(self):self.rejects(lambda:self.row['texts'].append(copy.deepcopy(self.row['texts'][0])))
    def test_missing_observed_line(self):self.rejects(lambda:self.row['texts'][0]['observed_line_boxes'].clear())
    def test_clipped_line(self):self.rejects(lambda:self.row['texts'][0]['observed_line_boxes'][0].update(rect=[1,700,60,730]))
    def test_truncation_flag(self):self.rejects(lambda:self.row['texts'][0].update(untruncated=False))
    def test_tiny_control(self):self.rejects(lambda:self.row['controls'][0].update(rect=[1,21,41,81]))
    def test_outside_clip(self):self.rejects(lambda:self.row['controls'][0].update(viewport=[0,30,320,720]))
    def test_missing_hit_point(self):self.rejects(lambda:self.row['controls'][0].update(hit_points=4))
    def test_missing_semantics(self):self.rejects(lambda:self.row['controls'][0].update(semantic_name=''))
    def test_missing_callback(self):self.rejects(lambda:self.row['controls'][0].update(callback_invoked=False))
    def test_false_flag(self):self.rejects(lambda:self.row['assertions'].update(read_only=False))
    def test_missing_flag(self):self.rejects(lambda:self.row['assertions'].clear())
    def test_wrong_route(self):self.rejects(lambda:self.row.update(route='FakeMirror'))
    def test_wrong_condition(self):self.rejects(lambda:self.row.update(condition={**self.condition,'text_percent':200}))
    def test_ledger_mutation(self):
        self.row['after']={'main':{'wallet':1},'story':{}};self.row['after_sha256']=digest(self.row['after']);self.assertRaises(ValueError,self.check)
    def test_text_hash(self):self.rejects(lambda:self.row['texts'][0].update(display_sha256='0'*64))
    def test_replacement_copy(self):
        t=self.row['texts'][0];t.update(english='Changed',display='Changed',english_sha256=digest('Changed'),display_sha256=digest('Changed'));self.assertRaises(ValueError,self.check)
    def test_duplicate_identity(self):
        self.assertRaises(ValueError,validate,{'schema_version':1,'kind':'production_widget_content_observations','rows':[self.row,self.row]},{'rows':[self.want],'rows_per_condition':2},self.condition)
    def test_missing_identity(self):
        self.assertRaises(ValueError,validate,{'schema_version':1,'kind':'production_widget_content_observations','rows':[]},{'rows':[self.want],'rows_per_condition':1},self.condition)
if __name__=='__main__':unittest.main()
