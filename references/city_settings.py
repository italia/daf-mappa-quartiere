import os
import sys
rootDir = os.path.dirname(__file__)
if rootDir not in sys.path:
    sys.path.append(rootDir)

import geopandas as gpd

from src.models.city_items import ServiceType
from references import common_cfg

class ModelCity(dict):
    loadFolder = common_cfg.processedPath

    def __init__(self, name, zonesPath, serviceLayersDict):
        self.name = name
        self.source = zonesPath
        super().__init__(serviceLayersDict)

    def get_istat_cpa_data(self):
        # hardcoded filename standard
        loaded = gpd.read_file(os.path.join(self.loadFolder, self.name + '_sezioni.geojson'))

        # check coordinate system (we use epsg 4326)
        assert loaded.crs['init'] == 'epsg:4326',\
            'Please make sure the input coordinate ref system is epsg:4326'
        assert {common_cfg.sezioneColName, common_cfg.IdQuartiereColName} \
               <= set(loaded.columns), \
            'Missing expected standard columns for city %s' % self.name

        # cast sezione ID as int
        loaded[common_cfg.sezioneColName] = loaded[common_cfg.sezioneColName].astype(int)

        return loaded.set_index(common_cfg.sezioneColName)

    @property
    def servicePaths(self):
        return {s: os.path.join(self.loadFolder, self[s]) for s in self.keys()}

defaultCities = [
    ModelCity(
        'Milano',
        '',
        {ServiceType.School: 'Milano_scuole.csv',
         ServiceType.Library: 'Milano_biblioteche.csv',
         ServiceType.TransportStop: 'Milano_TPL.csv',
         ServiceType.Pharmacy: 'Milano_farmacie.csv',
         }),
    ModelCity(
        'Torino',
        '',
        {ServiceType.School: 'Torino_scuole.csv',
         ServiceType.Library: 'Torino_biblioteche.csv',
         ServiceType.TransportStop: 'Torino_TPL.csv',
         ServiceType.Pharmacy: 'Torino_farmacie.csv',
         })
                ]

cityNamesList = [city.name for city in defaultCities]

def get_city_config(cityName):
    settings = [c for c in defaultCities if c.name==cityName]
    assert len(settings) == 1, 'Error in recognising city'
    return settings[0]