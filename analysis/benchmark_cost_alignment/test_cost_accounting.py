import math
import unittest
import csv
import json

from cost_utils import cost_values
from enrich_cost_data import ROOT, component_total, vals_tasks


class CostAccountingTest(unittest.TestCase):
    def test_duellab_recorded_total_is_not_weighted_mean_times_runs(self):
        rows = list(csv.DictReader((ROOT / 'data/duellab.csv').read_text().splitlines()))
        pair = [next(r for r in rows if r['model_canonical'] == model and r['effort'] == 'xhigh')
                for model in ['gpt-6-astra', 'claude-fable-5.1']]
        self.assertAlmostEqual(sum(float(r['cost_usd']) for r in pair), 6.324516745700856)
        self.assertAlmostEqual(sum(float(r['cost_total_usd']) for r in pair), 59.1665579312137)
        fable = pair[1]
        self.assertNotAlmostEqual(float(fable['cost_total_usd']), float(fable['cost_usd']) * float(fable['n_tasks']))
        self.assertEqual(cost_values(5, 'weighted_per_game', 11, 48), (48, 5))

    def test_pinnacle_token_pricing_and_nonadditive_unit(self):
        rows = list(csv.DictReader((ROOT / 'data/pinnacle.csv').read_text().splitlines()))
        pair = [next(r for r in rows if r['model_canonical'] == model and r['effort'] == effort)
                for model, effort in [('gpt-6-astra', 'max'), ('claude-fable-5.1', 'default')]]
        self.assertAlmostEqual(sum(float(r['cost_usd']) for r in pair), 3.97503)
        self.assertTrue(json.loads(pair[1]['note'])['input_estimated'])
        self.assertTrue(math.isnan(cost_values(3.97503, 'per_correct_task', 280)[0]))

    def test_mean_and_reported_total(self):
        self.assertEqual(cost_values(2, 'per_test', 100), (200, 2))
        self.assertEqual(cost_values(2, 'per_run', 17), (34, 2))
        total, per_unit = cost_values(200, 'total_run', math.nan)
        self.assertEqual(total, 200)
        self.assertTrue(math.isnan(per_unit))

    def test_nonadditive_and_missing_denominators_stay_missing(self):
        for unit, count in [('median_per_task', 100), ('weighted_per_test', 130), ('unknown', 100), ('per_test', math.nan), ('per_test', 0)]:
            self.assertTrue(math.isnan(cost_values(2, unit, count)[0]))

    def test_code_migration_uses_execution_counts(self):
        tasks = vals_tasks(ROOT / 'raw/vals_benchmarks/code-migration.html')
        key = 'openai/gpt-6-astra'
        total = component_total(tasks, key, {'cli': 120, 'cobol': 10})
        self.assertAlmostEqual(total, 6932.62008)
        displayed = tasks['overall'][key]['cost_per_test']
        self.assertNotAlmostEqual(total, displayed * 130)
        self.assertNotAlmostEqual(total, displayed * 40)
        self.assertEqual(cost_values(displayed, 'weighted_per_test', 130, total), (total, displayed))
        self.assertIsNone(component_total(tasks, 'missing-model', {'cli': 120, 'cobol': 10}))

    def test_excel_modes_have_equal_cost_weights(self):
        tasks = vals_tasks(ROOT / 'raw/vals_benchmarks/emb.html')
        for key in ['openai/gpt-6-astra', 'anthropic/claude-fable-5-1']:
            mean = tasks['overall'][key]['cost_per_test']
            total = component_total(tasks, key, {'template': 51, 'scratch': 51})
            self.assertAlmostEqual(total, 102 * mean, delta=0.0001)


if __name__ == '__main__':
    unittest.main()
