import logging
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from urllib.parse import unquote, urlencode
from owslib.util import bind_url
from owslib.util import ServiceException
logging.basicConfig(level=logging.INFO)


def esri_url_parser(url):
    try:
        layers = wmts_layers(url + "/WMTS")
        return layers
    except Exception as e:
        pass

    try:
        layers = arcgis_exporttiles_layers(url)
        return layers
    except Exception as e:
        pass


def layerurl(url, type="MOCK"):
    if type == "WMS":
        return wms_layers(url)
    elif type == "WMTS":
        return wmts_layers(url)
    elif type == "ESRI":
        return esri_url_parser(url)
    elif type == "MOCK":
        wms = wms_layers("https://img.nj.gov/imagerywms/Natural2015?")
        wmts = wmts_layers("https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/WMTS")
        wms["layers"].extend(wmts["layers"])
        return {"messages": "This is a test messsage.", "layers": wms["layers"]}
    else:
        return {"messages": "Unknown type"}


# WMS example
# 'type': 'raster',
# 'tiles': [
# 'https://img.nj.gov/imagerywms/Natural2015?bbox={bbox-epsg-3857}&format=image/png&service=WMS&version=1.1.1&request=GetMap&srs=EPSG:3857&transparent=true&width=256&height=256&layers=Natural2015'
# ],
# 'tileSize': 256
def wms_layers(url):
    """Retrieve layers from WMS url."""

    try:
        wms = WebMapService(url, version="1.1.1")
    except ServiceException as e:
        return {"message": "Can't parse url as WMS service.", "layers": []}

    layers = []
    messages = []

    for layer in list(wms.contents):
        if 'EPSG:3857' in wms[layer].crsOptions:
            layer_url = wms._WebMapService_1_1_1__build_getmap_request(
                layers=[layer], bgcolor='#FFFFFF', bbox=[], srs="EPSG:3857", size=(256, 256), format="image/png", transparent=True)
            layer_url = unquote(urlencode(layer_url))
            layer_url = layer_url.replace("bbox=", "bbox={bbox-epsg-3857}")
        else:
            logging.warning("Layer {layer} has the wrong CRS.".format(layer=layer))
            continue

        layers.append({"name": layer, "tiles": [layer_url]})

    return {"messages": messages, "layers": layers}


accepted_names = ["3857", "GoogleMapsCompatible"]


def filter_tilematrix_crs(tilematrixsetlinks):
    def check_name(tilematrix):
        return any(name in tilematrix for name in accepted_names)

    tilematrices = [tilematrix for tilematrix in tilematrixsetlinks if check_name(tilematrix)]
    return tilematrices


# WMTS example
# "wmts-layer", {
    # "type": "raster",
    # "tiles":['https://www.wmts.nrw.de/geobasis/wmts_nw_dop20/tiles/nw_dop20/EPSG_3857_16/{z}/{x}/{y}.jpeg'],
    # "tiles":['https://www.wmts.nrw.de/geobasis/wmts_nw_dop20/tiles/nw_dop20/EPSG_3857_16/{z}/{x}/{y}.jpeg'],
    # "tileSize": 256
def wmts_layers(url):
    """Retrieve layers from WMS url."""
    try:
        wmts = WebMapTileService(url, version="1.0.0")
    except ServiceException as e:
        return {"message": "Can't parse url as WMTS service.", "layers": []}

    layers = []
    messages = []

    for layer in list(wmts.contents):

        matrixsets = []
        for matrix in wmts[layer].tilematrixsetlinks:
            crs = wmts.tilematrixsets[matrix].crs
            if crs is not None and "3857" in wmts.tilematrixsets[matrix].crs:
                matrixsets.append(matrix)

        # matrixsets = filter_tilematrix_crs(wmts[layer].tilematrixsetlinks)
        if len(matrixsets) == 0:
            messages.append("Ignored layer due to wrong CRS.")
            continue
        # print(wmts[layer].tilematrixsets[0].crs)
        # print(dir(wmts[layer].tilematrixsets[0]))
        # print(dir(wmts[layer].tilematrixsetlinks))

        # Rest based URL
        if wmts.restonly:
            logging.info("Rest only layer.")
            layer_url = wmts.buildTileResource(
                layer=layer, tilematrixset=matrixsets[0], tilematrix="{z}", row="{y}", column="{x}")
        else:
            layer_url_data = wmts.buildTileRequest(
                layer=layer, tilematrixset=matrixsets[0], tilematrix="{z}", row="{y}", column="{x}")
            layer_url = bind_url(url) + unquote(layer_url_data)

        layers.append({"name": layer, "tiles": [layer_url]})

    return {"messages": messages, "layers": layers}


# ExportMap ArcGIS
# https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/
#   export?bbox=-2.003750722959434E7%2C-1.997186888040859E7%2C2.003750722959434E7%2C1.9971868880408563E7&bboxSR=EPSG%3A3857&layers=&layerDefs=&size=&imageSR=&format=png&transparent=true&dpi=&f=image
#   export?bbox={bbox-epsg-3857}&bboxSR=EPSG%3A3857&layers=&size=256,256&imageSR=EPSG%3A3857&format=png&transparent=true&dpi=&f=image
def arcgis_exporttiles_layers(url):
    """Retrieve layers from WMS url."""
    wmts = WebMapTileService(url, version="1.1.1")
    for layer in list(wmts.contents):
        print(layer)
        if 'GoogleMapsCompatible' in wmts[layer].tilematrixsets:
            print(wmts[layer].layers)
            print(dir(wmts[layer]))


if __name__ == "__main__":
    url = "https://img.nj.gov/imagerywms/Natural2015?"
    # wms_layers(url)

    url = "https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/WMTS"
    url = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/WMTS"
    # url = "https://tiles.arcgis.com/tiles/nSZVuSZjHpEZZbRo/arcgis/rest/services/Waterdiepte_bij_intense_neerslag_1_per_1000_jaar/MapServer/WMTS"
    print(wmts_layers(url))

    url = "https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/"
    # arcgis_exporttiles_layers(url)

    # print(layerurl("", "MOCK"))
