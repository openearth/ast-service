import configparser
import os
import shutil
from os.path import dirname, join, realpath
import logging
from geoserver.catalog import Catalog

logging.basicConfig(
    filename="cleanup.log",
    format="%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s",
    level=logging.DEBUG,
)


# Read default configuration from file
def read_config():
    cfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../config.txt")
    cf = configparser.RawConfigParser()
    cf.read(cfile)
    return cf


def cleanup_temp_directories(cf):
    temp_dir = join(dirname(realpath(__file__)), cf.get("Directories", "temp_dir"))
    subdirs = os.listdir(temp_dir)
    for dir in subdirs:
        dir = os.path.join(temp_dir, dir)

        try:
            shutil.rmtree(dir, ignore_errors=False, onerror=None)
            logging.info("Remove temp directories")
        except:
            logging.warning("Error while deleting directories")


# Cleanup temporary layers and stores


def cleanup_temp(cf, workspace="TEMP"):

    # Connect and get workspace
    cat = Catalog(
        cf.get("GeoServer", "rest_url"),
        username=cf.get("GeoServer", "user"),
        password=cf.get("GeoServer", "pass"),
    )

    # Layers
    layers = cat.get_layers()
    for l in layers:
        if (workspace + ":") in l.name:
            logging.info("Deleting layer = {}".format(l.name))
            try:
                cat.delete(l)
            except Exception as e:
                logging.warning(
                    f"An exception happened during deleting of workspace: {e} "
                )
    cat.reload()

    # Stores
    stores = cat.get_stores()
    for s in stores:
        if workspace in s.workspace.name:
            logging.info("Deleting store = {}".format(s.name))
            try:
                cat.delete(s)
            except Exception as e:
                logging.warning(
                    f"An exception happened during deleting the store: {e} "
                )
    cat.reload()


if __name__ == "__main__":
    logging.info("Cleaning up...")
    cf = read_config()
    cleanup_temp(cf)
    cleanup_temp_directories(cf)
