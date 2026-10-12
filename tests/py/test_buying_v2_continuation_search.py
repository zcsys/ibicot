import unittest
from dataclasses import replace
from tools.buying_v2.continuation_search import solve,SearchLimit
from tools.buying_v2.phase_oracle import solve as oracle
from tools.buying_v2.phase_ledger import Purchase,OpenBook,SettleBook,SharedSettleBook
from tools.buying_v2.continuation_information import FIELDS
from tools.buying_v2.continuation_observation import decode
from tools.buying_v2.continuation_program import compile_calendar
from tools.buying_v2.benchmark_phase_search import case
from test_buying_v2_information_history import fixture,scenario


class SearchTests(unittest.TestCase):
    def compare(self,c,s,paths,*,supply='independent-snapshots',funding='supplied',storage='resident'):
        by_label={e.label:e.funded_demands for e in paths[0].events if isinstance(e,Purchase)}
        expected=oracle(c,s,paths,funding='continuation' if funding=='continuation' else lambda c,s,e:by_label[e.label],supply=supply)
        actual=solve(c,s,paths,supply=supply,funding=funding,storage=storage)
        self.assertEqual(actual['expectedValue'],expected['expectedValue'])
        self.assertEqual(len(actual['leaves']),len(expected['leaves']))
        labels=compile_calendar(c,s,paths).labels
        for a,b in zip(actual['leaves'],expected['leaves']):
            self.assertEqual(a['state'],b['state']);self.assertEqual(a['value'],b['value']);self.assertEqual(a['probability'],b['probability'])
            if funding=='continuation':
                for i,detail in a['funding'].items():
                    for key,value in detail.items():self.assertEqual(value,b['trace'][i]['funding'][key],(i,key))
            self.assertEqual(a['policy'],{i:d['allocation'] for i,d in enumerate(b['trace']) if 'allocation' in d})
            self.assertEqual(tuple(decode(x,labels) for x in a['observations']),tuple({k:v for k,v in d.items() if k in FIELDS or k in ('event','label')} for d in b['trace']))
        return actual

    def test_multiple_purchases_lines_and_outcomes(self):
        for lines in (1,2):
            c,s,paths=case(1,2,2,2,lines=lines)
            paths=tuple(replace(p,events=tuple(replace(e,funded_demands=tuple(c.slots[o.material] for o in e.offers)) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
            self.compare(c,s,paths)

    def test_timing_signal_and_censored_demand_policies(self):
        c,s,b=fixture();b=replace(b,funded_demands=(1,))
        paths=tuple(scenario((OpenBook('early'),SettleBook('early',(d,)),OpenBook('later'),SettleBook('later',(1-d,)),b,OpenBook('final'),SettleBook('final',(d,)))) for d in (0,1))
        self.compare(c,s,paths)
        s=replace(s,finished=(0,),finished_basis=(0.,))
        paths=tuple(scenario((OpenBook('empty'),SharedSettleBook('empty',(d,),groups=((0,),)),b,OpenBook('final'),SettleBook('final',(d,)))) for d in (0,1))
        result=self.compare(c,s,paths)
        self.assertEqual([x['policy'][2] for x in result['leaves']],[(0,),(0,)])

    def test_rent_quotes_tick_end_and_empty_calendar(self):
        from tools.buying_v2.phase_ledger import Rent,SetQuotes,EndTick
        c,s,paths=case(1,1,1,2)
        paths=tuple(replace(p,events=(replace(p.events[0],funded_demands=(1,1)),*p.events[1:],
            SetQuotes('quotes',(2.,)),Rent('rent',.5,0.),EndTick('end',.2))) for p in paths)
        self.compare(c,s,paths)
        self.compare(c,s,tuple(replace(p,events=()) for p in paths))

    def test_limits_do_not_return_partial_policy(self):
        c,s,paths=case(1,2,2,2)
        paths=tuple(replace(p,events=tuple(replace(e,funded_demands=(1,)*len(e.offers)) if isinstance(e,Purchase) else e for e in p.events)) for p in paths)
        for kwargs in ({'max_frames':1},{'max_allocations':1},{'max_prefixes':1},{'history_nodes':1}):
            with self.assertRaises(SearchLimit) as cm:solve(c,s,paths,**kwargs)
            self.assertIn('activeFrames',cm.exception.diagnostics);self.assertNotIn('leaves',cm.exception.diagnostics)

    def test_hidden_funding_is_rejected_and_zero_weight_path_ignored(self):
        c,s,b=fixture();b=replace(b,funded_demands=(1,))
        paths=(scenario((b,)),scenario((replace(b,funded_demands=(0,)),)))
        with self.assertRaisesRegex(ValueError,'hidden scenario'):solve(c,s,paths)
        paths=(replace(paths[0],probability=1.),replace(paths[1],probability=0.))
        self.assertEqual(len(solve(c,s,paths)['leaves']),1)


if __name__=='__main__':unittest.main()
