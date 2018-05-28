import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os
from geopy import distance as geodist
from geopy import Point as geoPoint
import numpy as np

projRoot = os.path.dirname(os.path.dirname(__file__)) # expected to be in root/references

processedPath = os.path.join(projRoot,'data/processed/')

# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Location conventions
coordColNames = ['Long', 'Lat']
tupleIndexName = 'PositionTuples'
positionsCol = 'Positions'

# Kernel evaluation speedup
kernelValueCutoff = 1e-2  # interaction values below this level will be set to 0
kernelStartZeroGuess = 3  # initial input for kernel in solving

# Compute thresholds
kmStep = geodist.great_circle(kilometers=1)
center = (38.116667, 13.366667) # Get the long, lat tile around Palermo
# Note that a value in the south is conservative, as it gives a higher threshold for longitude
# deltas in degress to match a given level in kilometers
approxTileDegToKm = 1/np.array(
    [kmStep.destination(geoPoint(center), 90).longitude - center[1],
     kmStep.destination(geoPoint(center), 0).latitude - center[0]])

# Istat parameters
cpaPath = os.path.join(projRoot,'data/raw/istat/dati-cpa_2011/Sezioni di Censimento/')
sezioneColName = 'SEZ2011'
IdQuartiereColName = 'IDquartiere'
quartiereDescColName = 'quartiere'

#per quanto riguarda censimento abitazioni
# da quello che ho visto escluderei i campi A44, da PF a PF9, E27 per ora
excludedColumns = ['A44', 'E27']+['PF%i'%(i+1) for i in range(9)] +\
    ['SEZ', 'SHAPE_LEN', ]

# Json/GeoJson path parameters
outputPath = 'data/output'
vizOutputPath = 'data/output'
istatLayerName = 'Istat'
vitalityLayerName = 'Vitality'
menuGroupTemplate = { 
                'id' : '',
                'city' : '', # es: 'Torino'
                'type' : "source", #or 'layer'
                'url' : '',
                'sourceId' : '', # id of the source geojson
                'indicators':[  #list of different indicators
                    {'category' : '',
                    'label' : '',
                    'id' : '',
                    'default' : False,
                    'dataSource': '',
                     }]
                 }

#*** TPL parameters *****
tplPath = os.path.join(projRoot,'data/raw/tpl/')
tplRouteType = {"0":"Tram, Streetcar, Light rail",
                "1":"Subway, Metro",
                "2":"Rail",
                "3":"Bus",
                "4":"Ferry",
                "5":"Cable car",
                "6":"Gondola, Suspended cable car",
                "7":"Funicular"}

## Loading tools
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


def df_to_gdf(input_df):
    """
    Convert a DataFrame with longitude and latitude columns
    to a GeoDataFrame. WSG84
    """
    df = input_df.copy()
    geometry = [Point(xy) for xy in zip(df.longitude, df.latitude)]
    geo = gpd.GeoDataFrame(df, crs=4326, geometry=geometry)
    geo.crs = {'init' :'epsg:4326'}
    return geo


def csv_to_geojson(input_fp, output_fp):
    """
    Read a CSV file, transform it into a GeoJSON and save it.
    """
    csv_data = pd.read_csv(input_fp, 
                       compression='bz2', 
                       sep=';', 
                       encoding='utf-8')
    geojson_data = (csv_data.pipe(df_to_gdf)
                            .drop(['extra'], axis=1)
                            .to_json())
    with open(output_fp, 'w') as geojson_file:
        geojson_file.write(geojson_data)

