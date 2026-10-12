import unittest
from tools.buying_v2.fee_boundary_study import fee_case,income_case
from tools.buying_v2.phase_oracle import solve


class TransferNeutralFundingTests(unittest.TestCase):
    def test_intentions_do_not_buy_waste_to_avoid_future_fee(self):
        c,s,paths=fee_case(7.,3.,3)
        original=solve(c,s,paths,funding='continuation')
        alternative=solve(c,s,paths,funding='continuation-transfer-neutral')
        self.assertEqual(original['leaves'][0]['trace'][0]['allocation'],(2,))
        self.assertEqual(alternative['leaves'][0]['trace'][0]['allocation'],(1,))
        self.assertEqual(alternative['leaves'][0]['state'].accounts.fee_expense,3.)
        self.assertEqual(alternative['leaves'][0]['state'].incumbents,(1,2))
        self.assertEqual(alternative['expectedValue'],4.75)
        self.assertEqual(original['expectedValue'],6.75)
        # Current fee income/expense is posted by the unchanged actual path.
        later=next(t for t in alternative['leaves'][0]['trace'] if t['label']=='B-later')
        self.assertEqual(later['feeRecipients'],(-1,7))

    def test_neutral_intentions_can_miss_a_useful_fee_financed_buffer(self):
        for probability,old_value,new_value,old_q in ((0.,4.,4.,0),(0.5,5.375,5.,1),(1.,7.75,6.,1)):
            c,s,paths=income_case(probability)
            original=solve(c,s,paths,funding='continuation')
            alternative=solve(c,s,paths,funding='continuation-transfer-neutral')
            with self.subTest(probability=probability):
                self.assertEqual(original['expectedValue'],old_value)
                self.assertEqual(alternative['expectedValue'],new_value)
                self.assertTrue(all(leaf['trace'][0]['allocation']==(old_q,) for leaf in original['leaves']))
                self.assertTrue(all(leaf['trace'][0]['allocation']==(0,) for leaf in alternative['leaves']))
                self.assertAlmostEqual(sum(leaf['probability']*leaf['state'].accounts.fee_income for leaf in alternative['leaves']),2*probability)

    def test_fee_grid_matches_independent_cash_and_payment_calculation(self):
        excess=0
        for cash in (5.,6.,7.,8.,9.):
            for fee in (0.,1.,2.,3.,5.):
                for slot in (1,2,3,4):
                    # At most one output can sell. For q>=1, the incumbent is
                    # fundable iff cash-q covers $5 goods plus $.25 conversion.
                    # Otherwise the outsider is fee-free, if $1.25 remains.
                    candidates=[(0.,0)]
                    for q in range(1,slot+1):
                        remaining=cash-q
                        if remaining<1.25:
                            value=-q
                        else:
                            payment=min(5.,1.+fee) if remaining>=5.25 else 1.
                            value=10.-q-payment-.25
                        candidates.append((value,q))
                    expected_value,q=max(candidates,key=lambda item:(item[0],-item[1]))
                    c,s,paths=fee_case(cash,fee,slot)
                    result=solve(c,s,paths,funding='continuation')
                    neutral=solve(c,s,paths,funding='continuation-transfer-neutral')
                    with self.subTest(cash=cash,fee=fee,slot=slot):
                        self.assertEqual(result['expectedValue'],expected_value)
                        self.assertEqual(result['leaves'][0]['trace'][0]['allocation'],(q,))
                        self.assertEqual(neutral['leaves'][0]['trace'][0]['allocation'],(1,))
                        self.assertEqual(neutral['expectedValue'],dict((q,v) for v,q in candidates)[1])
                    excess+=int(q>1)
        self.assertEqual(excess,14)

    def test_zero_future_transfers_match_finance_aware_model(self):
        c,s,paths=fee_case(7.,0.,3)
        a=solve(c,s,paths,funding='continuation');b=solve(c,s,paths,funding='continuation-transfer-neutral')
        self.assertEqual(a['expectedValue'],b['expectedValue'])
        for x,y in zip(a['leaves'],b['leaves']):
            self.assertEqual(x['state'],y['state'])
            self.assertEqual([t['allocation'] for t in x['trace'] if t['event']=='Purchase'],
                             [t['allocation'] for t in y['trace'] if t['event']=='Purchase'])


if __name__=='__main__':unittest.main()
