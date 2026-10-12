import unittest
from tools.buying_v2.continuation_leaf_rows import LeafRows


class LeafRowsTests(unittest.TestCase):
    def test_order_exact_identifiers_and_copy(self):
        a=LeafRows(3);a.append(2**53+1)
        b=LeafRows(2);b.append(7);b.append(0);a.extend(b)
        b.rows[0]=9
        self.assertEqual(list(a),[2**53+1,7,0])
        self.assertEqual(a.rows.nbytes,24)

    def test_atomic_capacity_and_invalid_identifiers(self):
        a=LeafRows(1);a.append(3);b=LeafRows(1);b.append(4)
        with self.assertRaises(ValueError):a.extend(b)
        with self.assertRaises(ValueError):a.append(5)
        self.assertEqual(list(a),[3])
        for row in (-1,2**63,True,1.5):
            c=LeafRows(1)
            with self.assertRaises(ValueError):c.append(row)
            self.assertEqual(len(c),0)
        z=LeafRows(0);z.extend(LeafRows(0));self.assertEqual(list(z),[])


if __name__=='__main__':unittest.main()
