import json
import logging
import os
import time

import geopandas as gpd
import numpy as np
import pandas as pd
from osgeo import gdal
from rasterstats import zonal_stats
from shapely.geometry import box

from .ast_utils import (
    makeTempDir,
    cut_wcs,
    read_config,
    gdf_to_shp,
    rasterize,
    write_array_grid,
)
from .geoserver_utils import geoserver_upload_gtif


# All utils that are referred to the AST_heatreduction
def bufferBbox(bbox, size=250):
    return [bbox[0] - size, bbox[1] - size, bbox[2] + size, bbox[3] + size]


# TODO function that gets the project area geojson and make it a shp
def get_project_area(gdf, tmp):
    proj_area_gdf = gdf.copy()
    proj_area_gdf = proj_area_gdf[(proj_area_gdf.isProjectArea == True)]
    gdf_to_shp(proj_area_gdf, "project_area", dir=tmp, fieldName="id")
    proj_area_lyr = os.path.join(tmp, "project_area.shp")
    return proj_area_lyr


def extract_bbox(gdf):
    projectArea = gdf.copy()
    utm_crs = projectArea.estimate_utm_crs()
    projectArea = projectArea.to_crs(utm_crs)
    projectArea = projectArea[(projectArea.isProjectArea == True)]
    bounds = projectArea.total_bounds
    buffered_bbox = bufferBbox(bounds)
    buffered_bbox_geom = box(*buffered_bbox)
    bbox_gdf = gpd.GeoDataFrame([], geometry=[buffered_bbox_geom], crs=utm_crs)
    return bbox_gdf.to_crs(4326).total_bounds
    


# returns lines, polygons, points.
def extract_layers(geojson, measures):
    # extract all the geomtypes of the geojson
    geom_types = geojson.geometry.geom_type
    # drop the row of the project area
    layers = geojson[geojson.isProjectArea != True]
    layers.measure = layers.measure.astype(int)
    layers = layers.merge(measures, on="measure")

    # buffer features and create a gdf with the layers
    buffered_layers = layers.copy()

    for index, layer in buffered_layers.iterrows():
        buffered_layer = layer.copy()
        if layer.geometry.geom_type == "Point":
            try:
                buffered_layer.geometry = buffered_layer.geometry.buffer(
                    float(buffered_layer.areaRadius)
                )
                buffered_layers.loc[index, "geometry"] = buffered_layer.geometry

            except Exception:
                logging.exception("Buffering layer didn't work")
                buffered_layer.geometry = buffered_layer.geometry.buffer(1)
        if layer.geometry.geom_type == "LineString":
            try:
                buffered_layer.geometry = buffered_layer.geometry.buffer(
                    float(buffered_layer.areaWidth)
                )
                buffered_layers.loc[index, "geometry"] = buffered_layer.geometry
            except Exception:
                logging.exception("Buffering layer didn't work")
                buffered_layer.geometry = buffered_layer.geometry.buffer(5)

    buffered_layers.sort_values(
        by=["heatReductionFactor"], ascending=True, inplace=True
    )
    buffered_layers.reset_index(inplace=True)

    return buffered_layers


# read layer from geoserver, cut it, open it as array, get statistics
def wcs_2_array(
    dir,
    file,
    bbox,
    proj_area,
    layer,
    owsurl,
    layer_cut,
    unique_id,
    resturl,
    user,
    password,
):
    fname = os.path.join(dir, file)
    cut_wcs(*bbox, layername=layer, owsurl=owsurl, outfname=fname)

    # upload to geoserver
    cut_layer = "{0}{1}".format(layer_cut, unique_id)
    wmslayer = geoserver_upload_gtif(cut_layer, resturl, user, password, fname, "PET")
    # read values
    raster = gdal.Open(fname)
    band = raster.GetRasterBand(1)
    # Get nodata value
    nodata = band.GetNoDataValue()
    # Calc stats
    stats = zonal_stats(proj_area, fname, stats="min mean max")[0]

    values = band.ReadAsArray().astype(float)
    values = np.ma.masked_equal(values, nodata)
    return (values, stats, wmslayer)


# main
def ast_heatreduction(collection, PETCurrentLayerName, PETPotentialLayerName):
    # read the configuration
    (
        tmp,
        json_dir,
        owsurl,
        resturl,
        user,
        password,
        layer,
        ows_public_url,
    ) = read_config()

    gdf = gpd.GeoDataFrame.from_features(collection["features"])
    # read measures table
    measures_fname = "ast_measures_heatstress.json"
    measures = pd.read_json(os.path.join(json_dir, measures_fname))

    gdf = gdf.set_crs(epsg=4326)

    # reproject
    # reprojgdf = gdf.copy()
    # reprojgdf.crs = {"init": "epsg:4326"}
    # utm_crs = reprojgdf.estimate_utm_crs()
    # reprojgdf = reprojgdf.to_crs(utm_crs)
    # get the bounding box from the geojson and buffer it
    bbox = extract_bbox(gdf)
    print(bbox)
    
    # make tempdir & unique id every time
    caseTmpDir = makeTempDir(tmp)
    unique_id = int(1000000 * time.time())

    print("case {}".format(caseTmpDir))

    # Project area
    projectArea = get_project_area(gdf, caseTmpDir)

    # PET current
    currentValues, currentStats, wmsCur = wcs_2_array(
        caseTmpDir,
        "PET_current.tif",
        bbox,
        projectArea,
        PETCurrentLayerName,  # "NKWK:PET_current",
        owsurl,
        "PET_current_cut_",
        unique_id,
        resturl,
        user,
        password,
    )
    # PET potential
    potenValues, potenStats, wmsPoten = wcs_2_array(
        caseTmpDir,
        "PET_potential.tif",
        bbox,
        projectArea,
        PETPotentialLayerName,  # "NKWK:PET_potential",
        owsurl,
        "PET_potential_cut_",
        unique_id,
        resturl,
        user,
        password,
    )

    # get the reduct layers from the geojson
    try:
        reductLayers = extract_layers(gdf, measures)
    except Exception:
        res = json.dumps({"error_html": "Please provide meausures and try again"})
        return res

    gdf_to_shp(reductLayers, "reduct_layer", caseTmpDir, "factor")

    # rasterize the reduct shapefile
    infname = os.path.join(caseTmpDir, "reduct_layer.shp")
    outfname = os.path.join(caseTmpDir, "reduct.tif")
    rasterin = os.path.join(caseTmpDir, "PET_potential.tif")
    rasterize(rasterin, infname, outfname)

    reductLayer = gdal.Open(outfname)
    band = reductLayer.GetRasterBand(1)
    reductValues = band.ReadAsArray().astype(float)
    reductValues = reductValues * 0.01

    # PET DIFF
    diffValues = potenValues * reductValues
    PETdiffname = os.path.join(caseTmpDir, "PET_diff.tif")
    write_array_grid(rasterin, PETdiffname, diffValues, nodataval=128)
    PETdifflyrname = "PET_diff_{}".format(unique_id)
    wmsDiff = geoserver_upload_gtif(
        PETdifflyrname, resturl, user, password, PETdiffname, "PET_potential"
    )

    # PET NEW
    newValues = currentValues - potenValues * reductValues
    PETnewfname = os.path.join(caseTmpDir, "PET_new.tif")
    write_array_grid(rasterin, PETnewfname, newValues, nodataval=255)
    PETnewlyrname = "PET_new_{}".format(unique_id)
    wmsNew = geoserver_upload_gtif(
        PETnewlyrname, resturl, user, password, PETnewfname, "PET"
    )

    # Calc stats new
    newStats = zonal_stats(projectArea, PETnewfname, stats="min mean max")[0]

    # Calc stats diff
    diffStats = zonal_stats(projectArea, PETdiffname, stats="min mean max")[0]

    # diffStats = list(np.array(newStats) - np.array(potenStats))

    # prepare response

    response = {
        "layers": [
            {
                "id": "pet_new",
                "title": "PET new",
                "layerName": wmsNew,
                "baseUrl": ows_public_url,
            },
            {
                "id": "pet_diff",
                "title": "PET differences",
                "layerName": wmsDiff,
                "baseUrl": ows_public_url,
            },
            {
                "id": "pet_current",
                "title": "PET current",
                "layerName": wmsCur,
                "baseUrl": ows_public_url,
            },
        ],
        "oldStats": {
            "min": currentStats["min"],
            "max": currentStats["max"],
            "mean": currentStats["mean"],
        },
        "newStats": {
            "min": newStats["min"],
            "max": newStats["max"],
            "mean": newStats["mean"],
        },
        "diffStats": {
            "min": diffStats["min"],
            "max": diffStats["max"],
            "mean": diffStats["mean"],
        },
    }

    return response
