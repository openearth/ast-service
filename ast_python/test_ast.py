import unittest
import json
import pandas as pd

import ast_heatstress
import ast_selection
import ast_pluvflood


class TestAST(unittest.TestCase):
    def test_pluvflood(self):
        with open("test_pluvflood_new.json") as f:
            jsonstr = f.read()
        return_time_project_area = ast_pluvflood.pluvflood_json(jsonstr)
        self.assertAlmostEqual(return_time_project_area, 4.45)

    def test_heatstress_temperature(self):
        with open("test_heatstress_temperature_new.json") as f:
            jsonstr = f.read()
        temp_reduction = ast_heatstress.temperature_json(jsonstr)
        self.assertAlmostEqual(temp_reduction, 0.11)

    def test_heatstress_cost(self):
        with open("test_heatstress_cost_new.json") as f:
            jsonstr = f.read()
        maintenance_cost, construction_cost = ast_heatstress.cost_json(jsonstr)
        self.assertAlmostEqual(maintenance_cost, 15.0)
        self.assertAlmostEqual(construction_cost, 500.0)

    def test_heatstress_waterquality(self):
        with open("test_heatstress_waterquality_new.json") as f:
            jsonstr = f.read()
        capture_unit, settling_unit, filtering_unit = ast_heatstress.waterquality_json(
            jsonstr
        )
        self.assertAlmostEqual(capture_unit, 90.0)
        self.assertAlmostEqual(settling_unit, 93.0)
        self.assertAlmostEqual(filtering_unit, 95.0)

    def test_selection(self):
        with open("test_selection_new.json") as f:
            jsonstr = f.read()
        measures_list = ast_selection.selection_json(jsonstr)
        df = pd.DataFrame(json.loads(measures_list))
        # check top three ranking by their AST_ID
        self.assertEqual(df["AST_ID"][0], 72)
        self.assertEqual(df["AST_ID"][1], 22)
        self.assertEqual(df["AST_ID"][2], 27)

if __name__ == "__main__":
    unittest.main()
