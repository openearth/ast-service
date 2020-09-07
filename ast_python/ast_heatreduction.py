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

# read layer from geoserver, cut it, open it as array, get statistics
def wcs_2_array(dir, file, bbox, layer, owsurl, layer_cut, unique_id, resturl, user, password):
    fname = os.path.join(dir, file)
    cut_wcs(*bbox, layername = layer, owsurl = owsurl, outfname = fname)
    print(layer)
    #upload to geoserver
    cut_layer = '{0}{1}'.format(layer_cut, unique_id)
    wmslayer = geoserver_upload_gtif(cut_layer, resturl, user, password, fname, 'PET')
    #read values
    raster = gdal.Open(fname)
    band = raster.GetRasterBand(1)
    #Get nodata value
    nodata = band.GetNoDataValue()
    print ('nodata', nodata)


    #Calc stats 
    stats = band.GetStatistics(True, True)
    values = band.ReadAsArray().astype(float) # deal with no data when I am reading the array. check gdal
    print ('values', values)
    values = np.ma.masked_equal(values, nodata)
    print ('masked values', values)
    return (values, stats, wmslayer)



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



    #PET current
    currentValues, currentStats, wmsCur = wcs_2_array(caseTmpDir, 'PET_current.tif', bbox, "NKWK:PET_current", owsurl, 'PET_current_cut_', unique_id, resturl, user, password)
    #old stats= potenStats?
    potenValues, potenStats, wmsPoten = wcs_2_array(caseTmpDir, 'PET_potential.tif', bbox, "NKWK:PET_potential", owsurl, 'PET_potential_cut_', unique_id, resturl, user, password)
    
    

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
    rasterin = os.path.join(caseTmpDir, 'PET_potential.tif')
    rasterize(rasterin, infname, outfname)

    reductLayer = gdal.Open(outfname)
    band = reductLayer.GetRasterBand(1)
    reductValues = band.ReadAsArray().astype(float)
    reductValues = reductValues * 0.01
    
    #PET DIFF
    diffValues = potenValues*reductValues
    PETdiffname = os.path.join(caseTmpDir, 'PET_diff.tif')
    write_array_grid (rasterin, PETdiffname, diffValues)
    PETdifflyrname = 'PET_diff_{}'.format(unique_id)
    wmsDiff = geoserver_upload_gtif(PETdifflyrname, resturl, user, password, PETdiffname, 'PET_potential')
    
    
    #PET NEW 
    newValues = currentValues - potenValues*reductValues
    print ('newValues', newValues)
    PETnewfname = os.path.join(caseTmpDir, 'PET_new.tif')
    write_array_grid (rasterin, PETnewfname, newValues)
    PETnewlyrname = 'PET_new_{}'.format(unique_id)
    wmsNew = geoserver_upload_gtif(PETnewlyrname, resturl, user, password, PETnewfname, 'PET')

    # Calc stats new
    PETnew = gdal.Open(PETnewfname)
    newband = PETnew.GetRasterBand(1)
    newStats = newband.GetStatistics(True, True)

    # Calc stats diff
    
    diffStats = list(np.array(newStats) - np.array(potenStats))

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
            "min": currentStats[0],
            "max": currentStats[1],
            "mean": currentStats[2]
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
