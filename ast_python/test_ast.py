import unittest
import json
import pandas as pd

import ast_heatstress
import ast_selection
import ast_pluvflood


class TestAST(unittest.TestCase):
    def test_pluvflood(self):
        with open("test_pluvflood.json") as f:
            jsonstr = f.read()
        return_time_project_area = ast_pluvflood.pluvflood_json(jsonstr)
        self.assertAlmostEqual(return_time_project_area, 4.45)

    def test_heatstress_temperature(self):
        with open("test_heatstress_temperature.json") as f:
            jsonstr = f.read()
        temp_reduction = ast_heatstress.temperature_json(jsonstr)
        self.assertAlmostEqual(temp_reduction, 0.11)

    def test_heatstress_cost(self):
        with open("test_heatstress_cost.json") as f:
            jsonstr = f.read()
        res = ast_heatstress.cost_json(jsonstr)
        self.assertAlmostEqual(res['maintenanceCost'], 15.0)
        self.assertAlmostEqual(res['constructionCost'], 500.0)

    def test_heatstress_waterquality(self):
        with open("test_heatstress_waterquality.json") as f:
            jsonstr = f.read()
        res = ast_heatstress.waterquality_json(
            jsonstr
        )
        self.assertAlmostEqual(res['captureUnit'], 90.0)
        self.assertAlmostEqual(res['settlingUnit'], 93.0)
        self.assertAlmostEqual(res['filteringUnit'], 95.0)

    def test_selection(self):
        with open("test_selection.json") as f:
            jsonstr = f.read()
        measures_list = ast_selection.selection_json(jsonstr)
        df = pd.DataFrame(json.loads(measures_list))
        # check top three ranking by their AST_ID
        self.assertEqual(df["AST_ID"][0], 72)
        self.assertEqual(df["AST_ID"][1], 22)
        self.assertEqual(df["AST_ID"][2], 27)

if __name__ == "__main__":
    unittest.main()
