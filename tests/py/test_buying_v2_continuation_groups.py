import random
import unittest
from tools.buying_v2.continuation_groups import Groups


class GroupTests(unittest.TestCase):
    def test_stable_partition_matches_independent_lists(self):
        rng=random.Random(8319)
        for n in range(100):
            branches=[object() for _ in range(n)];ids=[];expected=[]
            for branch in branches:
                group=rng.randrange(len(expected)+1)
                if group==len(expected):expected.append([])
                ids.append(group);expected[group].append(branch)
            actual=Groups(branches,ids)
            self.assertEqual([list(actual[i]) for i in range(len(actual))],expected)
            self.assertEqual(sorted(actual.members.tolist()),list(range(n)))
            self.assertEqual(actual.members.nbytes,8*n)
            for i,group in enumerate(expected):
                self.assertIs(actual[i][0],group[0]);self.assertEqual(len(actual[i]),len(group))

    def test_bad_ids_and_indices_rejected(self):
        for ids in ((1,),(0,2),(0,-1),(False,),(0.,)):
            with self.assertRaises(ValueError):Groups([None]*len(ids),ids)
        with self.assertRaises(ValueError):Groups([], (0,))
        g=Groups([1],(0,))
        for index in (-1,1,True):
            with self.assertRaises(IndexError):g[index]
            with self.assertRaises(IndexError):g[0][index]

    def test_view_uses_original_branch_identity(self):
        branches=[object(),object(),object()];g=Groups(branches,(0,1,0));view=g[0]
        replacement=object();branches[2]=replacement
        self.assertIs(view[1],replacement)
        self.assertIs(view.groups,g)


if __name__=='__main__':unittest.main()
