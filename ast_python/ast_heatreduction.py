import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import box
from .geoserver_utils import geoserver_upload_gtif
from .ast_utils import *
import pandas as pd
import json
import numpy as np
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
           buffered_layer.geometry =  buffered_layer.geometry.buffer(float(buffered_layer.areaRadius))
           buffered_layers.loc[index, 'geometry'] = buffered_layer.geometry

        if (layer.geometry.geom_type == "Polygon" or layer.geometry.geom_type == "LineString"):
            buffered_layer.geometry =  buffered_layer.geometry.buffer(float(buffered_layer.areaWidth))
            buffered_layers.loc[index, 'geometry'] = buffered_layer.geometry

    buffered_layers.sort_values(by=['heatReductionFactor'], ascending=True, inplace=True )  
    buffered_layers.reset_index(inplace=True)       
    
    return buffered_layers


# main
def ast_heatreduction(collection):  

    #read the configuration
    tmp, json_dir, owsurl, resturl, user, password, layer= read_config()
    gdf = gpd.GeoDataFrame.from_features(collection["features"])
    print ('gdf')
    print (gdf.crs)
    #read measures table
    measures_fname = "ast_measures_heatstress.json"
    measures = pd.read_json(os.path.join(json_dir, measures_fname))
    
    
    
     
    #reproject
    reprojgdf = gdf.copy()
    reprojgdf.crs = {'init':'epsg:4326'}
    reprojgdf = reprojgdf.to_crs("EPSG:28992")
    # get the bounding box from the geojson and buffer it
    bbox = extract_bbox(reprojgdf)
     #make tempdir 
    caseTmpDir = makeTempDir(tmp) 
    print ('case {}'.format(caseTmpDir))
    # Get PET_potential WCS from geoserver
    PETfname = os.path.join(caseTmpDir, 'PET_original.tif')
    cut_wcs(*bbox, layername = "NKWK:PET_potential", owsurl = owsurl, outfname = PETfname)
    

    # get the reduct layers from the geojson
    reductLayers = extract_layers(reprojgdf, measures)

    #Read PET_original
    PEToriginal = gdal.Open(PETfname)
    band = PEToriginal.GetRasterBand(1)
    #Calc stats of PET original
    oldStats = band.GetStatistics(True, True)

    PETvalues = band.ReadAsArray().astype(float)

    gdf_to_shp(reductLayers,'reduct_layer', "factor", caseTmpDir)
    #rasterize the reduct shapefile
    infname = os.path.join(caseTmpDir, 'reduct_layer.shp')
    outfname = os.path.join(caseTmpDir, 'reduct.tif')
    rasterize(PETfname, infname, outfname)

    reductLayer = gdal.Open(outfname)
    band = reductLayer.GetRasterBand(1)
    reductValues = band.ReadAsArray().astype(float)
    reductValues = reductValues * 0.01
    #PET DIFF
    PETdiffvalues = PETvalues*reductValues
    PETdiffoutfname = os.path.join(caseTmpDir, 'PET_diff.tif')
    write_array_grid (PETfname, PETdiffoutfname, PETdiffvalues)
    PETdifflyrname = 'PET_diff_{}'.format(int(1000000*time.time()))
    wmsDiff = geoserver_upload_gtif(PETdifflyrname, resturl, user, password, PETdiffoutfname)
    

    # PET NEW
    PETvalues = PETvalues - PETvalues*reductValues

    PEToutfname = os.path.join(caseTmpDir, 'PET_new.tif')
    write_array_grid (PETfname, PEToutfname, PETvalues)
    PETlyrname = 'PET_new_{}'.format(int(1000000*time.time()))
    wmsNew = geoserver_upload_gtif(PETlyrname, resturl, user, password, PEToutfname)

    # Calc stats new
    PETnew = gdal.Open(PEToutfname)
    band = PEToriginal.GetRasterBand(1)
    newStats = band.GetStatistics(True, True)




    #prepare response
    response = {
        "PETnew": {"layerName": wmsNew,
                    "baseUrl": owsurl
            	  },
                    
        "PETdiff": {"layerName": wmsDiff,
                    "baseUrl": owsurl
            	  },
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
        
    }

    return response

#TEST
