# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import json


def selection_json(jsonstr):
    d = json.loads(jsonstr)
    df = selection(**d)
    return df.to_json(orient="records")


def selection(
    scores,
    scale,
    soil,
    slope,
    multifunctionality,
    surface,
    subsurface_characteristics,
    climate_capacity,
    site_suitability,
):

    # construct DataFrame from list of dicts
    df = pd.DataFrame(scores)

    # convert checkboxes to index the DataFrame with
    scale_list = _checklist(scale)
    climate_capacity_list = _checklist(climate_capacity)
    site_suitability_list = _checklist(site_suitability)

    max_scale = df[scale_list].max(axis=1)

    # include all characteristics less than or equal to subsurface_characteristics
    subsurface_characteristics_range = ["High", "Medium", "Low", "Very_low"]
    subsurface_characteristics_index = subsurface_characteristics_range.index(
        subsurface_characteristics
    )
    subsurface_characteristics_list = subsurface_characteristics_range[
        subsurface_characteristics_index:
    ]

    # technical feasability
    df["TechFeasabilty"] = max_scale + df[soil] + df[slope]

    # TODO implement multifuntional landuse scores or multiply with 2
    df["site_suitability1"] = (
        df[site_suitability_list].max(axis=1)
        + multifunctionality * df["Enables_multifunctional_land_use"] * 2
    )
    # check what to do with roofs versus subsurface, now they can sum to 2, instead of 1
    df["site_suitability2"] = df[surface] + df[subsurface_characteristics_list].max(
        axis=1
    )

    df["site_suitability"] = df["site_suitability1"] * df["site_suitability2"].replace(
        0, 0.4
    )

    df["climate_capacity_sum"] = df[climate_capacity_list].sum(axis=1)

    # TODO check whether 0 values should be allowed
    df.loc[np.isclose(df["climate_capacity_sum"], 0), "climate_capacity_factor"] = 0.0
    df.loc[np.isclose(df["climate_capacity_sum"], 1), "climate_capacity_factor"] = 1.25
    df.loc[np.isclose(df["climate_capacity_sum"], 2), "climate_capacity_factor"] = 1.35
    df.loc[np.isclose(df["climate_capacity_sum"], 3), "climate_capacity_factor"] = 1.425
    df.loc[np.isclose(df["climate_capacity_sum"], 4), "climate_capacity_factor"] = 1.5
    df.loc[np.isclose(df["climate_capacity_sum"], 5), "climate_capacity_factor"] = 1.575
    df.loc[np.isclose(df["climate_capacity_sum"], 6), "climate_capacity_factor"] = 1.6

    # TODO find out why tech feas score instead of rank?
    df["system_suitability"] = (df["site_suitability"] + df["TechFeasabilty"]) * df[
        "climate_capacity_factor"
    ]

    df["system_suitability_rank"] = df["system_suitability"].rank(
        axis=0, ascending=False, method="min"
    )
    df_sorted = df.sort_values("system_suitability_rank")

    measures_list = df_sorted[["AST_ID", "Name", "system_suitability"]]
    return measures_list


def _checklist(checkboxes):
    """Turns a dict of {"a":True, "b": False, "c": True} into ["a", "c"]"""
    return [key for key, checked in checkboxes.items() if checked]
