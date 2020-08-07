import os
from geoserver.catalog import Catalog
import configparser

# Read default configuration from file
def read_config():
    cfile=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../config.txt')
    cf = configparser.RawConfigParser()
    cf.read(cfile)
    return cf
	
    
    
	
# Cleanup temporary layers and stores

def cleanup_temp(cf, workspace='TEMP'):

    # Connect and get workspace
    cat = Catalog(cf.get('GeoServer', 'rest_url'), username=cf.get('GeoServer', 'user'), password=cf.get('GeoServer', 'pass'))
    
    # Layers
    layers = cat.get_layers()
    for l in layers:
        if (workspace+':') in l.name:
            print('Deleting layer = {}'.format(l.name))
            try:
                cat.delete(l)
                print('OK')
            except:
                print('ERR')
    cat.reload()
    
    # Stores
    stores = cat.get_stores()        
    print('-------------------')
    for s in stores:
        if workspace in s.workspace.name:
            print('Deleting store = {}'.format(s.name))
            try:
                cat.delete(s)
                print('OK')
            except:
                print('ERR')
    cat.reload()
print ('I am in')
cf = read_config()
cleanup_temp(cf)