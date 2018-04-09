import pandas as pd
import geopandas as gpd
import os

projRoot = os.path.dirname(os.path.dirname(__file__)) # expected to be in root/references

# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Istat parameters
cpaPath = os.path.join(projRoot,'data/raw/istat/dati-cpa_2011/Sezioni di Censimento/')
sezioneColName = 'SEZ2011'
IdQuartiereColName = 'IDquartiere'

## Loading tools
def get_istat_cpa_data(cityName):
    # hardcoded filename standard
    loaded = gpd.read_file(os.path.join(projRoot, 'data/processed/'+cityName+'_sezioni.geojson'))
    assert set([sezioneColName, IdQuartiereColName]) <= set(loaded.columns), \
        'Missing expected standard columns for city %s' % cityName
    return loaded.set_index(sezioneColName)


def get_istat_filelist():
    return [f for f in os.listdir(cpaPath) if f.startswith('R')]


cached_metadata = pd.read_csv(os.path.join(cpaPath, 'tracciato_2011_sezioni.csv'), sep=';',encoding='cp1252')

def get_istat_metadata():
    return cached_metadata

