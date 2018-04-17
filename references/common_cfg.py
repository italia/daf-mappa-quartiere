import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os

projRoot = os.path.dirname(os.path.dirname(__file__)) # expected to be in root/references

# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Istat parameters
cpaPath = os.path.join(projRoot,'data/raw/istat/dati-cpa_2011/Sezioni di Censimento/')
sezioneColName = 'SEZ2011'
IdQuartiereColName = 'IDquartiere'
quartiereDescColName = 'quartiere'

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

