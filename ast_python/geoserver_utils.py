# -*- coding: utf-8 -*-
import os

from geoserver.catalog import Catalog

# Upload raster file to GeoServer


def geoserver_upload_gtif(
    layername, resturl, user, password, gtifpath, sld_style, workspace="TEMP"
):

    # Connect and get workspace
    cat = Catalog(resturl, username=user, password=password)
    ws = cat.get_workspace(workspace)

    # Create store
    print("Uploading {} at geoserver".format(layername))
    ft = cat.create_coveragestore(layername, workspace=ws, data=gtifpath)

    # Associate SLD styling to it
    layer = cat.get_layer(layername)
    layer.default_style = sld_style
    cat.save(layer)

    # Return wms url
    wmslay = workspace + ":" + layername
    return wmslay


# Cleanup temporary layers and stores
def cleanup_temp(rest_url, user, password, workspace="TEMP"):

    # Connect and get workspace
    cat = Catalog(rest_url, username=user, password=password)

    # Layers
    layers = cat.get_layers()
    for l in layers:
        if (workspace + ":") in l.name:
            print("Deleting layer = {}".format(l.name))
            try:
                cat.delete(l)
                print("OK")
            except:
                print("ERR")
    cat.reload()

    # Stores
    stores = cat.get_stores()
    print("-------------------")
    for s in stores:
        if workspace in s.workspace.name:
            print("Deleting store = {}".format(s.name))
            try:
                cat.delete(s)
                print("OK")
            except:
                print("ERR")
    cat.reload()
