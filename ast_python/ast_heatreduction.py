import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import box
from .geoserver_utils import geoserver_upload_gtif
from .ast_utils import *
import pandas as pd
import json
import numpy as np
import os
from os.path import join, dirname, realpath, abspath
import time
from osgeo import gdal
# All utils that are referred to the AST_heatreduction
def bufferBbox (bbox, size = 100):
        return [bbox[0]-size, bbox[1]-size, bbox[2]+size, bbox[3] +size]

def extract_bbox(geojson):
    projectArea = geojson.copy()
    projectArea = projectArea[(projectArea.isProjectArea == True)]
    bounds = projectArea.total_bounds
    bufferedBbox = bufferBbox (bounds)

    return bufferedBbox


#returns lines, polygons, points. 
def extract_layers(geojson, measures):

    #extract all the geomtypes of the geojson
    geom_types = geojson.geometry.geom_type
    #drop the row of the project area
    layers = geojson[geojson.isProjectArea != True]
    layers.measure = layers.measure.astype(int)
    layers = layers.merge(measures, on ='measure')
    
    #buffer features and create a gdf with the layers
    buffered_layers = layers.copy()

    for index, layer in buffered_layers.iterrows():
        buffered_layer = layer.copy()
        if layer.geometry.geom_type == "Point":
            
            try: 
                buffered_layer.geometry =  buffered_layer.geometry.buffer(float(buffered_layer.areaRadius))
                buffered_layers.loc[index, 'geometry'] = buffered_layer.geometry
                
            except:
                print ('didnt work')
                buffered_layer.geometry =  buffered_layer.geometry.buffer(1)
        if (layer.geometry.geom_type == "Polygon" or layer.geometry.geom_type == "LineString"):
            try:

                buffered_layer.geometry =  buffered_layer.geometry.buffer(float(buffered_layer.areaWidth))
                buffered_layers.loc[index, 'geometry'] = buffered_layer.geometry
            except:
                print ('didnt work')
                buffered_layer.geometry =  buffered_layer.geometry.buffer(5)

    buffered_layers.sort_values(by=['heatReductionFactor'], ascending=True, inplace=True )  
    buffered_layers.reset_index(inplace=True)       
    
    return buffered_layers


# main
def ast_heatreduction(collection): 
    
    #read the configuration
    tmp, json_dir, owsurl, resturl, user, password, layer= read_config()
    print('read the temp')
    gdf = gpd.GeoDataFrame.from_features(collection["features"])
    #read measures table
    measures_fname = "ast_measures_heatstress.json"
    measures = pd.read_json(os.path.join(json_dir, measures_fname))

    #reproject
    reprojgdf = gdf.copy()
    reprojgdf.crs = {'init':'epsg:4326'}
    reprojgdf = reprojgdf.to_crs("EPSG:28992")
    # get the bounding box from the geojson and buffer it
    bbox = extract_bbox(reprojgdf)
    #make tempdir & unique id every time
    caseTmpDir = makeTempDir(tmp)
    unique_id = int(1000000*time.time()) 
    
    print('case {}'.format(caseTmpDir))

    #PET_current from geoserver
    PETcurfname = os.path.join(caseTmpDir, 'PET_current.tif')
    cut_wcs(*bbox, layername = "NKWK:PET_current", owsurl = owsurl, outfname = PETcurfname)
    print('cut PET current wcs')
    #cut on the area : upload to geoserver
    PETcurlyrname = 'PET_current_cut_{}'.format(unique_id)
    wmsCur = geoserver_upload_gtif(PETcurlyrname, resturl, user, password, PETcurfname, 'PET')
    #read PET current values
    PETcurrent = gdal.Open(PETcurfname)
    band = PETcurrent.GetRasterBand(1)
    #Calc stats of PET current
    oldStats = band.GetStatistics(True, True)
    currentValues = band.ReadAsArray().astype(float)

    
    #PET_potential from geoserver
    PETpotenfname = os.path.join(caseTmpDir, 'PET_potential.tif')
    cut_wcs(*bbox, layername = "NKWK:PET_potential", owsurl = owsurl, outfname = PETpotenfname)
    print('cut PET potential wcs')
    #cut on the area : upload to geoserver
    PETpotenlyrname = 'PET_potential_cut_{}'.format(unique_id)
    wmsPoten = geoserver_upload_gtif(PETpotenlyrname, resturl, user, password, PETpotenfname, 'PET')
    #read PET potential values
    PETpoten = gdal.Open(PETpotenfname)
    band = PETpoten.GetRasterBand(1)
    #Calc stats of PET potential
    oldStats = band.GetStatistics(True, True)
    potenValues = band.ReadAsArray().astype(float)

    # get the reduct layers from the geojson
    try:
        reductLayers = extract_layers(reprojgdf, measures)
    except Exception as e:
        print ('Please provide meausures and try again')
        res = json.dumps({'error_html' : 'Please provide meausures and try again'})
        return res


 

    gdf_to_shp(reductLayers,'reduct_layer', "factor", caseTmpDir)
    #rasterize the reduct shapefile
    infname = os.path.join(caseTmpDir, 'reduct_layer.shp')
    outfname = os.path.join(caseTmpDir, 'reduct.tif')
    rasterize(PETpotenfname, infname, outfname)

    reductLayer = gdal.Open(outfname)
    band = reductLayer.GetRasterBand(1)
    reductValues = band.ReadAsArray().astype(float)
    reductValues = reductValues * 0.01
    
    #PET DIFF
    diffValues = potenValues*reductValues
    PETdiffname = os.path.join(caseTmpDir, 'PET_diff.tif')
    write_array_grid (PETpotenfname, PETdiffname, diffValues)
    PETdifflyrname = 'PET_diff_{}'.format(unique_id)
    wmsDiff = geoserver_upload_gtif(PETdifflyrname, resturl, user, password, PETdiffname, 'PET_potential')
    
    
    #PET NEW 
    newValues = currentValues - potenValues*reductValues

    PETnewfname = os.path.join(caseTmpDir, 'PET_new.tif')
    write_array_grid (PETpotenfname, PETnewfname, newValues)
    PETnewlyrname = 'PET_new_{}'.format(unique_id)
    wmsNew = geoserver_upload_gtif(PETnewlyrname, resturl, user, password, PETnewfname, 'PET')

    # Calc stats new
    PETnew = gdal.Open(PETnewfname)
    band = PETnew.GetRasterBand(1)
    newStats = band.GetStatistics(True, True)

    # Calc stats diff
    
    diffStats = list(np.array(newStats) - np.array(oldStats))

    #prepare response
    response = {
        "layers":[{
            "id": "pet_new",
            "title": "PET new",
            "layerName": wmsNew ,
            "baseUrl": owsurl
        },
        {
            "id": "pet_diff",
            "title": "PET differences",
            "layerName": wmsDiff ,
            "baseUrl": owsurl
        },
        {
            "id": "pet_potential",
            "title": "PET potential",
            "layerName": wmsPoten ,
            "baseUrl": owsurl
        },
        {
            "id": "pet_current",
            "title": "PET current",
            "layerName": wmsCur ,
            "baseUrl": owsurl
        }],
        "oldStats": {
            "min": oldStats[0],
            "max": oldStats[1],
            "mean": oldStats[2]
        },
        "newStats": {
            "min": newStats[0],
            "max": newStats[1],
            "mean": newStats[2]
        },
        "diffStats": {
            "min": diffStats[0],
            "max": diffStats[1],
            "mean": diffStats[2]
        }

    }

    return response
