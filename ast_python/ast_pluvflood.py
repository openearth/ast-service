# -*- coding: utf-8 -*-

import json


def pluvflood_json(jsonstr):
    d = json.loads(jsonstr)
    return pluvflood(**d)


def pluvflood(
    record, project_area, measure_area, measure_depth, inflow_area, current_return_time
):
    storage_capacity = measure_area * measure_depth
    effective_depth = storage_capacity / inflow_area  # [m]
    effective_depth_mm = effective_depth * 1000.0
    effective_depth_list = [
        0.0,
        5.0,
        10.0,
        20.0,
        30.0,
        40.0,
        50.0,
        100.0,
        200.0,
        500.0,
        1000.0,
        1.00E+12,
    ]

    for i in range(len(effective_depth_list)):
        if effective_depth_list[i] <= effective_depth_mm:
            index_a = i
            index_b = i + 1
            effective_depth_a = effective_depth_list[index_a]
            effective_depth_b = effective_depth_list[index_b]
        else:
            break

    recurrence_a = float(record[f"Col{index_a}"])
    recurrence_b = float(record[f"Col{index_b}"])

    multiplication_factor = recurrence_a + (recurrence_b - recurrence_a) * (
        effective_depth_mm - effective_depth_a
    ) / (effective_depth_b - effective_depth_a)
    return_time_inflow_area = current_return_time * multiplication_factor
    return_time_project_area = (
        return_time_inflow_area * inflow_area / (project_area)
        + current_return_time * (project_area - inflow_area) / project_area
    )

    return return_time_project_area
