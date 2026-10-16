import json
import unittest
from economy.server.complexity_history import accumulate, project


class ComplexityHistoryTests(unittest.TestCase):
    def test_period_ratios_save_restore_and_year_boundary(self):
        history = []
        counts = {1: 2, 2: 1, 3: 0, 4: 0}
        def rows(net, revenue, sold):
            return [dict(complexity=1, netEarnings=net, revenue=revenue, sold=sold)]
        accumulate(history, 1, rows(-10, 10, 1), counts, 2)
        history = json.loads(json.dumps(history))  # checkpoint round trip
        counts[1] = 4
        accumulate(history, 2, rows(22, 90, 30), counts, 2)
        accumulate(history, 2, rows(999, 999, 999), counts, 2)  # no duplicate
        point = project(history)[0]
        self.assertEqual(point['bands']['1']['netPerCompany'], 2)
        self.assertAlmostEqual(point['bands']['1']['price'], 100/31)
        self.assertIsNone(point['bands']['3']['price'])
        accumulate(history, 3, rows(-4, 0, 0), counts, 2)
        self.assertEqual(len(history), 2)
        self.assertEqual(project(history)[1]['bands']['1']['netPerCompany'], -1)
        self.assertEqual(project(history)[0], point)

    def test_missing_earnings_are_not_zero(self):
        history = []
        accumulate(history, 500, [dict(complexity=2, netEarnings=None, revenue=0, sold=0)],
                   {1: 0, 2: 2, 3: 0, 4: 0}, 360)
        self.assertIsNone(project(history)[0]['bands']['2']['netPerCompany'])
        self.assertEqual(project(history)[0]['startTick'], 500)
