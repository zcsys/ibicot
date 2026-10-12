from dataclasses import replace
from itertools import product
import random
import unittest
from tools.buying_v2.closing_certificate import certify,complement_boxes,solve as certified_solve
from tools.buying_v2.benchmark_phase_search import case
from tools.buying_v2.phase_oracle import solve,Scenario
from tools.buying_v2.phase_ledger import Company,State,Line,Offer,Purchase,OpenBook,SettleBook


class ClosingCertificateTests(unittest.TestCase):
    def test_complement_is_disjoint_and_excludes_only_proposal(self):
        lo=(0,0,0);hi=(4,3,6);lots=(2,1,3)
        universe=set(product(*(range(a,b+1,l) for a,b,l in zip(lo,hi,lots))))
        for point in universe:
            covered=[]
            for a,b in complement_boxes(lo,hi,point,lots):
                covered.extend(product(*(range(x,y+1,l) for x,y,l in zip(a,b,lots))))
            self.assertEqual(len(covered),len(set(covered)))
            self.assertEqual(set(covered),universe-{point})

    def test_unique_candidate_and_inconclusive_wrong_tied_or_limited_proposals(self):
        c,s,paths=case(2,2,1,1)
        event=replace(paths[0].events[0],funded_demands=(2,)*4)
        posterior=((1.,replace(paths[0],events=paths[0].events[1:])),)
        q=(2,0,2,0)
        result=certify(c,s,s,event,posterior,q)
        self.assertTrue(result['certified']);self.assertEqual(result['proposal']['value'],11.)
        self.assertFalse(certify(c,s,s,event,posterior,(0,)*4)['certified'])
        self.assertEqual(certify(c,s,s,event,posterior,q,max_boxes=1)['reason'],'proof-limit')
        equal=replace(event,offers=tuple(replace(o,price=2.) for o in event.offers))
        self.assertFalse(certify(c,s,s,equal,posterior,q)['certified'])
        fallback=certified_solve(c,s,s,equal,posterior)
        self.assertEqual(fallback['certificates'],0)
        self.assertEqual(fallback['allocation'],(0,2,0,2))
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError):certify(c,s,s,event,posterior,q,max_boxes=value)

    def test_known_ledger_near_tie_cannot_be_certified(self):
        c=Company((1.,),(1,),2.,(Line((1,),1,0.,10.,0.,(0.,0.),1.),),(1,),0.)
        s=State(1000.,(0,),(0.,),(0,),(0.,),(10.,),(-1,))
        e=Purchase('buy',(Offer(0,0,.1,1),),(1,),(0.,),0.,0.,(),0.)
        p=Scenario(1.,(OpenBook('sales'),SettleBook('sales',(0,))),((0.,.10000000100001),),((0.,0.),))
        for q in ((0,),(1,)):
            self.assertFalse(certify(c,s,s,e,((1.,p),),q)['certified'])

    def test_integrated_proofs_preserve_full_policy_and_accounting(self):
        for args in (case(1,1,2,2),case(2,2,2,2)):
            for funding in ('continuation','continuation-transfer-neutral'):
                for supply in ('independent-snapshots','persistent-arrivals'):
                    kw=dict(funding=funding,supply=supply,funding_memo_size=4096,
                            max_nodes=50000,max_prefix_nodes=200000)
                    base=solve(*args,**kw)
                    actual=solve(*args,**kw,closing_search='compiled-certified-boxes',closing_memo_size=4096)
                    self.assertEqual(base['expectedValue'],actual['expectedValue'])
                    self.assertEqual(base['leaves'],actual['leaves'])
                    self.assertGreater(actual['closingSolver']['certificates'],0)
                    self.assertLessEqual(actual['closingSolver']['boxes']+actual['closingSolver']['proposalStates']+
                                         actual['prefixSearch']['visitedPrefixes'],kw['max_prefix_nodes'])
        for budget in (dict(max_nodes=1),dict(max_prefix_nodes=1)):
            with self.assertRaisesRegex(ValueError,'node limit; no approximate result returned'):
                solve(*case(2,2,2,2),funding='continuation',closing_search='compiled-certified-boxes',**budget)

    def test_certified_random_proposals_match_independent_event_tree(self):
        rng=random.Random(641239)
        certified=0
        for _ in range(40):
            lines=tuple(Line(recipe,2,rng.choice((.1,.5)),10.,0.,(0.,)*3,float(sum(recipe)))
                        for recipe in ((1,1),(1,0))[:rng.choice((1,2))])
            n=len(lines)
            c=Company((1.,1.),(2,2),12.,lines,(2,)*n,0.)
            s=State(rng.choice((5.,20.,1000.)),(0,0),(0.,0.),(0,)*n,(0.,)*n,(10.,)*n,(-1,-1))
            offers=tuple(Offer(m,2*m+i,rng.choice((.1,1.,2.,3.)),2) for m in range(2) for i in range(2))
            e=Purchase('buy',offers,(2,)*4,(0.,)*4,0.,0.,tuple(range(n)),0.)
            paths=tuple(Scenario(w,(e,OpenBook('sales'),SettleBook('sales',tuple(rng.randrange(3) for _ in lines))),
                         tuple(tuple(rng.choice((0.,.1)) for _ in range(3)) for _ in range(2)),
                         tuple((0.,0.,0.) for _ in lines)) for w in (.25,.75))
            expected=solve(c,s,paths,funding=lambda *_:e.funded_demands)
            q=expected['leaves'][0]['trace'][0]['allocation']
            posterior=tuple((p.probability,replace(p,events=p.events[1:])) for p in paths)
            wrapped=certified_solve(c,s,s,e,posterior)
            self.assertEqual(wrapped['allocation'],q)
            self.assertEqual(wrapped['value'],expected['expectedValue'])
            for proposal in (q,(0,)*4):
                result=certify(c,s,s,e,posterior,proposal,max_boxes=2000)
                if result['certified']:
                    certified+=1
                    self.assertEqual(proposal,q)
                    self.assertEqual(result['proposal']['value'],expected['expectedValue'])
        self.assertGreater(certified,0)


if __name__=='__main__':unittest.main()
