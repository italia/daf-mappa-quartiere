import pandas as pd
import geopandas as gpd


# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Istat parameters
sezioneColName = 'SEZ2011'
IdQuartiereColName = 'IDquartiere'


## Loading tools
def get_istat_cpa_data(cityName):
    # hardcoded filename standard
    loaded = gpd.read_file('../data/processed/'+cityName+'_sezioni.geojson')
    assert set([sezioneColName, IdQuartiereColName]) <= set(loaded.columns), \
        'Missing expected standard columns for city %s' % cityName
    return loaded.set_index(sezioneColName)


def get_istat_metadata():
    return pd.read_csv('../data/raw/istat/dati-cpa_2011/Sezioni di Censimento/tracciato_2011_sezioni.csv', sep=';', encoding='cp1252')

