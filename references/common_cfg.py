import pandas as pd
import geopandas as gpd
import os

projRoot = os.path.dirname(os.path.dirname(__file__)) # expected to be in root/references

# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Location conventions
coordColNames = ['Long', 'Lat']

# Istat parameters
cpaPath = os.path.join(projRoot,'data/raw/istat/dati-cpa_2011/Sezioni di Censimento/')
sezioneColName = 'SEZ2011'
IdQuartiereColName = 'IDquartiere'
quartiereDescColName = 'quartiere'


## Loading tools
def get_istat_cpa_data(cityName):
    # hardcoded filename standard
    loaded = gpd.read_file(os.path.join(projRoot, 'data/processed/'+cityName+'_sezioni.geojson'))
    # check coordinate system (we use epsg 4326)
    assert loaded.crs['init'] == 'epsg:4326', 'Please make sure the input coordinate ref system is epsg:4326'
    assert set([sezioneColName, IdQuartiereColName]) <= set(loaded.columns), \
        'Missing expected standard columns for city %s' % cityName
    return loaded.set_index(sezioneColName)


def get_istat_filelist():
    return [f for f in os.listdir(cpaPath) if f.startswith('R')]


cached_metadata = pd.read_csv(os.path.join(cpaPath, 'tracciato_2011_sezioni.csv'), sep=';',encoding='cp1252')

def get_istat_metadata():
    return cached_metadata


def fill_sample_ages_in_cpa_columns(frameIn):
    '''Extract a representative age for hardcoded age-band columns in standard istat data'''
    assert isinstance(frameIn, pd.DataFrame), 'Series expected in input'
    istatAgeDict = {'P%i'%(i+14): 3+5*i for i in range(16)}
    istatAges = frameIn.loc[:, list(istatAgeDict.keys())].copy()
    
    return istatAges.rename(istatAgeDict, axis='columns')

