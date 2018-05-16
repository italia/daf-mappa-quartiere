import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os

projRoot = os.path.dirname(os.path.dirname(__file__)) # expected to be in root/references

processedPath = os.path.join(projRoot,'data/processed/')

# cities included in the project
cityList = ['Milano', 'Torino', 'Roma']

# Location conventions
coordColNames = ['Long', 'Lat']
tupleIndexName = 'PositionTuples'
positionsCol = 'Positions'

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
                'center' : [],
                'zoom' : [],
                'joinField' : IdQuartiereColName,
                'sourceId' : '', # id of the source geojson
                'indicators':[  #list of different indicators
                    {'category' : '',
                    'label' : '',
                    'id' : '',
                    'default' : False,
                    'dataSource': '',
                     }]
                 }


def make_output_menu(cityName, services, istatLayers=None, sourceUrl=''):
    '''Creates a list of dictionaries that is ready to be saved as a json'''
    outList = []
    
    # source element
    sourceId = cityName + '_quartieri' 
    sourceItem = menuGroupTemplate.copy()
    sourceItem['city'] = cityName
    sourceItem['url'] = sourceUrl
    sourceItem['id'] = sourceId
    outList.append(sourceItem)
    
    # service layer items
    areas = set(s.serviceArea for s in services)
    for area in areas:
        thisServices = [s for s in services if s.serviceArea == area] 
        layerItem = menuGroupTemplate.copy()
        layerItem['type'] = 'layer'
        layerItem['city'] = cityName
        layerItem['id'] = cityName + '_' + area.value
        layerItem['url'] = '' # default empty url
        layerItem['sourceId'] = sourceId # link to defined source
        #
        layerItem['indicators']=(
            [{'category': service.serviceArea.value,
             'label': service.label,
             'id': service.name,
             'dataSource': service.dataSource,
            } for service in thisServices]),
        outList.append(layerItem)
        
    # istat layers items
    if istatLayers:
        for istatArea, indicators in istatLayers.items():
            istatItem = menuGroupTemplate.copy()
            istatItem['type'] = 'layer'
            istatItem['city'] = cityName
            istatItem['id'] = cityName + '_' + istatArea
            istatItem['url'] = ''  # default empty url
            istatItem['sourceId'] = sourceId  # link to defined source
            #
            istatItem['indicators'] = (
                                          [{'category': istatArea,
                                            'label': indicator,
                                            'id': indicator,
                                            'dataSource': 'ISTAT',
                                            } for indicator in indicators]),
            outList.append(istatItem)

    return outList


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

