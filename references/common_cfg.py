"""Module to store application-wide constants that are used both in offline
data preprocessing and model evaluation."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy import distance as geodist
from geopy import Point as geoPoint


from scipy.sparse.csgraph import connected_components

project_root = os.path.dirname(
    os.path.dirname(__file__))  # expected to be in root/references

processed_path = os.path.join(project_root, 'data/processed/')

# cities included in the project
city_list = ['Milano', 'Torino', 'Roma', 'Bari', 'Firenze']

# Location conventions
coord_col_names = ['Long', 'Lat']
tuple_index_name = 'PositionTuples'
positions_col = 'Positions'

# Kernel evaluation speedup
# interaction values below this level will be set to 0
kernel_value_cutoff = 1e-4
kernel_start_zero_guess = 1  # initial input for kernel in solving
# Clip level for demand correction:
# maximum multiple that can be applied in correcting service level
demand_correction_clip = 1.4
assert demand_correction_clip > 1, \
    'The clipping factor should be greater than 1'

# Compute thresholds
km_step = geodist.great_circle(kilometers=1)

# Note that a value in the south to build the rectangle is conservative,
# as it gives a higher threshold for longitude deltas in degress to match a
# given level in kilometers

center = (38.116667, 13.366667)  # Get the long, lat tile around Palermo
approx_tile_deg_to_km = 1 / np.array(
    [km_step.destination(geoPoint(center), 90).longitude - center[1],
     km_step.destination(geoPoint(center), 0).latitude - center[0]])

# Istat parameters
cpa_path = os.path.join(
    project_root, 'data/raw/istat/dati-cpa_2011/Sezioni di Censimento/')
sezione_col_name = 'SEZ2011'
id_quartiere_col_name = 'IDquartiere'
quartiere_desc_col_name = 'quartiere'

# Mapping from column labels to relevant ages:
istat_age_dict = {'P%i' % (i + 14): np.arange(5 * i, 5 * (i + 1))
                  for i in range(16)}

# per quanto riguarda censimento abitazioni, da quello che ho visto
# escluderei i campi A44, da PF a PF9, E27 per ora
excluded_columns = ['A44', 'E27'] + ['PF%i' % (i + 1) for i in range(9)] + \
                   ['SEZ', 'SHAPE_LEN'] + coord_col_names

# Json/GeoJson path parameters
output_path = os.path.join(project_root, 'data/output')
viz_output_path = os.path.join(project_root, 'data/output')
istat_layer_name = 'Istat'
vitality_layer_name = 'Vitality'
menu_group_template = {
    'id': '',
    'city': '',  # es:'Torino'
    'type': "source",  # or 'layer'
    'url': '',
    'sourceId': '',  # id of the source geojson
    'indicators': [{   # list of different indicators
        'category': '',
        'label': '',
        'id': '',
        'default': False,
        'data_source': '',
        }]
    }

# TPL parameters
tpl_path = os.path.join(project_root, 'data/raw/tpl/')
tpl_route_type = {
    "0": "Tram, Streetcar, Light rail",
    "1": "Subway, Metro",
    "2": "Rail",
    "3": "Bus",
    "4": "Ferry",
    "5": "Cable car",
    "6": "Gondola, Suspended cable car",
    "7": "Funicular"
    }

# Loading tools
cached_metadata = pd.read_csv(os.path.join(
    cpa_path, 'tracciato_2011_sezioni.csv'), sep=';', encoding='cp1252')

def detect_similar_locations(positions_list, tol=0.003):
    """This function flags the groups of locations that are within a
    given tolerance
        tolerance default: 30m
    """
    n_positions = len(positions_list)
    test_dist = 10 * np.ones([n_positions] * 2)
    for i_pos in range(n_positions):
        for j_pos in np.arange(i_pos + 1, n_positions):
            test_dist[i_pos, j_pos] = geodist.great_circle(
                positions_list[i_pos], positions_list[j_pos]).km
    graph_matrix = (test_dist < tol).astype(float)
    # find groups of positions that are close together
    _, labels = connected_components(graph_matrix, directed=False)

    return labels


def get_istat_metadata():
    return cached_metadata


def get_istat_filelist():
    return [f for f in os.listdir(cpa_path) if f.startswith('R')]


def df_to_gdf(input_df):
    """
    Convert a DataFrame with longitude and latitude columns
    to a GeoDataFrame. WSG84
    """
    df = input_df.copy()
    geometry = [Point(xy) for xy in zip(
        df[coord_col_names[0]], df[coord_col_names[1]])]
    geo = gpd.GeoDataFrame(df, crs=4326, geometry=geometry)
    geo.crs = {'init': 'epsg:4326'}
    return geo


def csv_to_geojson(input_fp, output_fp):
    """
    Read a CSV file, transform it into a GeoJSON and save it.
    """
    csv_data = pd.read_csv(input_fp,
                           compression='bz2',
                           sep=';',
                           encoding='utf-8')
    geojson_data = (
        csv_data.pipe(
            df_to_gdf).drop(['extra'], axis=1).to_json())
    with open(output_fp, 'w') as geojson_file:
        geojson_file.write(geojson_data)
