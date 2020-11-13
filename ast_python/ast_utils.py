# -*- coding: utf-8 -*-
import configparser
import json
import os
import tempfile
from os.path import abspath, dirname, join, realpath

import osgeo.ogr as ogr
import osgeo.osr as osr
from osgeo import gdal, gdalconst

from .wcs_utils import *


def read_json_array(filename):
    with open(filename, "r") as f:
        json_data = f.read()
        return json.loads(json_data)
    return {}


def find_record(identifier, filename):
    # Read JSON array data
    data = read_json_array(filename)

    # Search item [first match]
    rec = {}
    for item in data:
        if item["ID"] == identifier:
            rec = item

    return rec


# ast_heatreduction utils
# read configuration file
def read_config():
    # Default config file (relative path)
    cfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../config.txt")
    cf = configparser.RawConfigParser()
    cf.read(cfile)

    temp_dir = join(dirname(realpath(__file__)), cf.get("Directories", "temp_dir"))
    json_dir = join(
        dirname(realpath(__file__)), cf.get("Directories", "json_dir")
    )  # gives the absolute path of the  dir

    ows_url = cf.get("GeoServer", "ows_url")
    ows_url = cf.get("GeoServer", "ows_url")
    ows_public_url = cf.get("GeoServer", "ows_public_url")
    rest_url = cf.get("GeoServer", "rest_url")
    layername = cf.get("GeoServer", "layername")
    user = cf.get("GeoServer", "user")
    password = cf.get("GeoServer", "pass")

    return (
        temp_dir,
        json_dir,
        ows_url,
        rest_url,
        user,
        password,
        layername,
        ows_public_url,
    )


# Cut a raster layer
# TODO crs=28992
def cut_wcs(xst, yst, xend, yend, layername, owsurl, outfname, crs=4326, all_box=False):
    linestr = "LINESTRING ({} {}, {} {})".format(xst, yst, xend, yend)
    l = LS(linestr, crs, owsurl, layername)
    l.line()
    l.getraster(outfname, all_box=all_box)
    l = None
    logging.info("Writing: {}".format(outfname))


def makeTempDir(dir):
    # Temporary folder setup
    tmpdir = tempfile.mkdtemp(dir=dir)
    return tmpdir


# geodataframe to shapeflie
def gdf_to_shp(gdf, layername, dir, fieldName=None):

    features = gdf.copy()
    # create an output datasouce in memory
    driver = ogr.GetDriverByName("ESRI Shapefile")
    shpfile = os.path.join(dir, layername + ".shp")
    source = driver.CreateDataSource(shpfile)

    # open the memory data source with writing access
    logging.info("Writing: {}".format(shpfile))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)
    layer = source.CreateLayer(layername, srs, ogr.wkbPolygon)

    layer.CreateField(ogr.FieldDefn(fieldName, ogr.OFTInteger64))

    for index, row in features.iterrows():
        feat = row.copy()
        feature = ogr.Feature(layer.GetLayerDefn())

        if fieldName == "id":
            field_value = 1

        else:
            field_value = feat.heatReductionFactor
        feature.SetField(fieldName, field_value)
        wkt = feat.geometry.wkt
        geom = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometryDirectly(geom)
        layer.CreateFeature(feature)
        feature = None
    source = None
    return layer


# rasterize


def rasterize(rasterin, vectorin, rasterout, field="factor", read=False):
    # Read geometry from given raster
    data = gdal.Open(rasterin, gdalconst.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    x_res = data.RasterXSize
    y_res = data.RasterYSize

    # Read features and rasterize to output
    shp = ogr.Open(vectorin)
    lyr = shp.GetLayer()
    target_ds = gdal.GetDriverByName("GTiff").Create(
        rasterout, x_res, y_res, 1, gdal.GDT_Byte, ["COMPRESS=LZW", "TILED=YES"]
    )
    target_ds.SetGeoTransform(geo_transform)
    band = target_ds.GetRasterBand(1)
    NoData_value = -999999
    band.SetNoDataValue(NoData_value)
    band.FlushCache()

    logging.info("Writing: {}".format(rasterout))
    gdal.RasterizeLayer(
        target_ds, [1], lyr, options=["ALL_TOUCHED=TRUE", "ATTRIBUTE={}".format(field)]
    )
    # Return band if necessary
    if read:
        return band.ReadAsArray()
    # Free
    target_ds = None


# Write array to grid file
def write_array_grid(
    RasterGrid, RasterName, array, nodataval, output_type=gdal.GDT_Byte
):
    SourceRaster = gdal.Open(RasterGrid)
    GeoTrans = SourceRaster.GetGeoTransform()
    projection = osr.SpatialReference()
    projection.ImportFromWkt(SourceRaster.GetProjectionRef())
    xsize = SourceRaster.RasterXSize
    ysize = SourceRaster.RasterYSize
    driver = gdal.GetDriverByName("GTiff")
    Raster = driver.Create(
        RasterName, xsize, ysize, 1, output_type, ["COMPRESS=LZW", "TILED=YES"]
    )
    Raster.SetGeoTransform(GeoTrans)
    Raster.SetProjection(projection.ExportToWkt())
    band = Raster.GetRasterBand(1)
    band.WriteArray(array)
    band.SetNoDataValue(nodataval)
    return RasterName
