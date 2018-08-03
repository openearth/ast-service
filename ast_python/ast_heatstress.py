# -*- coding: utf-8 -*-

import json


def temperature_json(jsonstr):
    d = json.loads(jsonstr)
    return temperature(**d)


def temperature(record, project_area, measure_area):
    temp_reduction_local = float(record["Value_T"])
    temp_reduction = temp_reduction_local * measure_area / project_area
    return temp_reduction


def cost_json(jsonstr):
    d = json.loads(jsonstr)
    return cost(**d)


def cost(record, measure_area):
    construction_unit_cost = float(record["construction_m2"])
    maintenance_unit_cost = float(record["maint_annual_frac_constr"])

    construction_cost = construction_unit_cost * measure_area
    maintenance_cost = 0.01 * maintenance_unit_cost * construction_cost
    return maintenance_cost


def waterquality_json(jsonstr):
    d = json.loads(jsonstr)
    return waterquality(**d)


def waterquality(record, measure_area):
    capture_unit = float(record["Nutrients"])
    settling_unit = float(record["AdsorbingPollutants"])
    filtering_unit = float(record["Pathogens"])

    capture_unit = capture_unit * measure_area
    settling_unit = settling_unit * measure_area
    filtering_unit = filtering_unit * measure_area
    return capture_unit, settling_unit, filtering_unit
