"""Independent calibration proof reconciliation; never promotes scope status."""
import argparse, copy, hashlib, itertools, json, pathlib, re, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HASH = re.compile(r'^[a-f0-9]{64}$')
REWARD = ['normal_and_crew_core_story_persistence_equal',
          'single_charge_600_seconds_20_percent', 'collectible_set_does_not_duplicate',
          'undo_restart_and_route_traversed', 'duplicate_controls_disabled']
PRACTICE = ['full_route_undo_restart_work',
            'both_claims_disabled_before_and_after_solving',
            'complete_core_and_story_unchanged']
STATES = ['unearned', 'previously_earned', 'no_stored_focus_practice']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def require(condition, label):
    if not condition: raise ValueError(label)

def conditions(locale):
    return {f'{locale}-{view}-{scale}-{motion}': {
        'condition_id': f'{locale}-{view}-{scale}-{motion}', 'locale': locale,
        'viewport': size, 'text_scale': scale / 100,
        'reduced_motion': motion == 'reduced'}
        for (view, size), scale, motion in itertools.product(
            [('phone', [320, 720]), ('tablet', [1024, 768])],
            [100, 150, 200], ['normal', 'reduced'])}

def validate_structure(data, metadata, *, full=True):
    locale = data['locale']
    require(locale in ['en-US', 'qps-ploc'], 'known locale')
    require(data['pseudo_enabled'] is (locale == 'qps-ploc'), 'exact pseudo boolean')
    require(data['schema_version'] == 1, 'schema')
    expected = conditions(locale)
    require(len(data['conditions']) == 12 and
            {x['condition_id']: x for x in data['conditions']} == expected,
            'exact display cross product')
    require(data['expected_pattern_display_cases'] == 144 and
            data['expected_state_rows'] == 432, 'unmodified expected counts')
    rows = data['rows']; keys = set()
    for row in rows:
        key = row['pattern_id'], row['condition_id'], row['state']
        require(key not in keys, 'duplicate state row'); keys.add(key)
        require(row['pattern_id'] in [f'calibration.{n:02}' for n in range(1, 13)] and
                row['state'] in STATES and row['condition_id'] in expected, 'declared row')
        for field, value in expected[row['condition_id']].items():
            require(type(row[field]) is type(value) or field in ['viewport','text_scale'], 'condition value type')
            require(row[field] == value, 'row condition matches identifier')
        require(row['layout_exception'] is False and
                row['reachable_48px_controls_and_named_semantics'] is True and
                row['result'] == 'passed_bounded_host_case', 'row success assertions')
        flags = PRACTICE if row['state'] == STATES[2] else REWARD
        require(all(row.get(f) is True for f in flags), 'all actual assertions present and true')
        if row['state'] == STATES[2]:
            require(type(row['commands']) is int and row['commands'] == 0 and
                    type(row['save_writes']) is int and row['save_writes'] == 0,
                    'practice is inert')
            hashes = ['unchanged_core_sha256']
        else:
            hashes = ['before_core_sha256', 'after_core_sha256', 'after_session_sha256']
            require(row['before_core_sha256'] != row['after_core_sha256'], 'completion changes state')
        require(all(HASH.fullmatch(row[h]) for h in hashes), 'state digest syntax')
    require(data['observed_passing_state_rows'] == len(rows), 'observed count reconciles')
    require(data['complete_matrix_observed'] is (len(rows) == 432), 'honest completeness')
    require(data['runner_exit_status_is_also_required'] is True, 'exit required')
    if full:
        require(keys == set(itertools.product([f'calibration.{n:02}' for n in range(1,13)], expected, STATES)), 'full 432 unique rows')
        require(not metadata['source_differences'], 'stable source')
        require(all(r['exit_code'] == 0 for r in metadata['results']), 'real process success')
        cmd = next(r['command'] for r in metadata['results'] if r['name']=='calibration')
        require('test/calibration_accessibility_matrix_test.dart' in cmd, 'actual suite')
        for c in cmd:
            require(not re.match(r'^(--(?:name|plain-name|tags|exclude-tags)(?:=|$)|-[ntx])', c), 'unfiltered full invocation')
        require(('--dart-define=TIDEGLASS_PSEUDO=true' in cmd) == (locale == 'qps-ploc'), 'actual presentation mode')
    # Display, locale and motion are presentation-only: every identical logical
    # starting case must retain the identical complete-state hashes.
    by_case = {}
    for row in rows:
        key = row['pattern_id'], row['state']
        digest_fields = {k:v for k,v in row.items() if k.endswith('_sha256')}
        require(by_case.setdefault(key, digest_fields) == digest_fields, 'display-independent economic result')
    return {'locale':locale,'state_rows':len(rows),'full':full,'state_fingerprints':by_case}

def reconcile(report, proof, *, full=True):
    data=json.loads(report.read_text()); meta=json.loads((proof/'verification.json').read_text())
    result=validate_structure(data,meta,full=full)
    require(sha(report)==meta['calibration_report_sha256'], 'actual report hash')
    before=json.loads((proof/'source-before.json').read_text())
    after=json.loads((proof/'source-after.json').read_text())
    require(before==after and not meta['source_differences'], 'source stable through execution')
    for p,h in before.items(): require(sha(proof/'source'/p)==h, 'archived source '+p)
    for p,h in data['source_sha256'].items():
        normalized=str((pathlib.Path('game/mobile')/p))
        normalized=str(pathlib.Path(__import__('os').path.normpath(normalized)))
        require(before[normalized]==h,'report input '+p)
    for run in meta['results']:
        require(sha(proof/(run['name']+'.log'))==run['log_sha256'],'actual '+run['name']+' log')
    text=(proof/'calibration.log').read_text()
    if full: require('+144: All tests passed!' in text, '144 actual widget tests')
    result['source_inputs']=len(before)
    result['source_fingerprint']=hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result.pop('state_fingerprints')
    return result

class EvidenceCounterexamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'release/accessibility-current/root-calibration-full-20261021T124620.563753Z/calibration-matrix.json').read_text())
        cls.meta=json.loads((ROOT/'release/native-proof/root-calibration-full-20261021T124620.563753Z/verification.json').read_text())
    def rejects(self, mutate):
        d,m=copy.deepcopy(self.data),copy.deepcopy(self.meta);mutate(d,m)
        with self.assertRaises((ValueError,KeyError)):validate_structure(d,m)
    def test_control(self):validate_structure(self.data,self.meta)
    def test_missing_row(self):self.rejects(lambda d,m:d['rows'].pop())
    def test_duplicate_row(self):self.rejects(lambda d,m:d['rows'].__setitem__(0,copy.deepcopy(d['rows'][1])))
    def test_missing_pattern(self):self.rejects(lambda d,m:d['rows'][0].__setitem__('pattern_id','calibration.13'))
    def test_false_reward_equivalence(self):self.rejects(lambda d,m:d['rows'][0].__setitem__(REWARD[0],False))
    def test_missing_reward_claim(self):self.rejects(lambda d,m:d['rows'][0].pop(REWARD[1]))
    def test_integer_not_boolean(self):self.rejects(lambda d,m:d['rows'][0].__setitem__(REWARD[2],1))
    def test_wrong_viewport(self):self.rejects(lambda d,m:d['rows'][0].__setitem__('viewport',[320,721]))
    def test_wrong_text_scale(self):self.rejects(lambda d,m:d['rows'][0].__setitem__('text_scale',1.5))
    def test_wrong_motion(self):self.rejects(lambda d,m:d['rows'][0].__setitem__('reduced_motion',True))
    def test_omitted_condition(self):self.rejects(lambda d,m:d['conditions'].pop())
    def test_practice_reward(self):self.rejects(lambda d,m:d['rows'][2].__setitem__('commands',1))
    def test_practice_save(self):self.rejects(lambda d,m:d['rows'][2].__setitem__('save_writes',1))
    def test_real_failure(self):self.rejects(lambda d,m:m['results'][-1].__setitem__('exit_code',1))
    def test_source_drift(self):self.rejects(lambda d,m:m['source_differences'].append('lib/calibration_screen.dart'))
    def test_filtered_full(self):self.rejects(lambda d,m:m['results'][-1]['command'].append('--name=phone'))
    def test_short_filtered_full(self):self.rejects(lambda d,m:m['results'][-1]['command'].extend(['-n','phone']))
    def test_wrong_mode(self):self.rejects(lambda d,m:m['results'][-1]['command'].append('--dart-define=TIDEGLASS_PSEUDO=true'))
    def test_display_changes_state(self):self.rejects(lambda d,m:d['rows'][36].__setitem__('after_core_sha256','0'*64))
    def test_failed_pseudo_never_full(self):
        d=json.loads((ROOT/'release/accessibility-current/root-calibration-pseudo-full-20261021T124804.560266Z/calibration-matrix.json').read_text())
        m=json.loads((ROOT/'release/native-proof/root-calibration-pseudo-full-20261021T124804.560266Z/verification.json').read_text())
        with self.assertRaises(ValueError):validate_structure(d,m)
        self.assertEqual(validate_structure(d,m,full=False)['state_rows'],360)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=pathlib.Path);parser.add_argument('--proof',type=pathlib.Path);parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    if args.report:print(json.dumps(reconcile(args.report,args.proof,full=not args.partial),indent=2))
    else:unittest.main(argv=['calibration-independent-counterexamples'],verbosity=2)
