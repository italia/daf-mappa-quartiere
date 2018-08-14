"""Module to perform read and write operations."""
import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd

from references import common_cfg
from references.city_items import ServiceType

# expecting to be in root/references
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
LOCAL_LOAD_FOLDER = os.path.join(PROJECT_ROOT, 'data/processed/')
LOCAL_WRITE_FOLDER = os.path.join(PROJECT_ROOT, 'data/output')
# save menu alongside other files
LOCAL_MENU_PATH = os.path.join(LOCAL_WRITE_FOLDER, 'menu.json')

# TODO: when files are available in DAF, server addresses can go here
SERVICE_FILENAMES_MAPPING = {
    ServiceType.School: 'scuole',
    ServiceType.Library: 'biblioteche',
    ServiceType.TransportStop: 'TPL',
    ServiceType.Pharmacy: 'farmacie',
    }

CSV_READ_SETTINGS = {'sep': ';', 'decimal': ','}

## INPUT FUNCTIONS

def fetch_service_units(service_type, city):
    """Fetch the provided type service units data for the selected city."""

    # TODO: replace hardcoding with API
    load_path = os.path.join(LOCAL_LOAD_FOLDER,
                             city.name + '_' + SERVICE_FILENAMES_MAPPING[
                                 service_type] + '.csv')

    if service_type in [ServiceType.Pharmacy, ServiceType.TransportStop]:
        # FIXME: temporary bespoke setting
        service_df = pd.read_csv(load_path, sep=';', decimal='.')
    else:
        # default
        service_df = pd.read_csv(load_path, **CSV_READ_SETTINGS)

    return service_df


def fetch_istat_section_data(city):
    """Fetch the Istat data by section for the provided city."""

    # TODO: replace hardcoding with API
    load_path = os.path.join(LOCAL_LOAD_FOLDER, city.name + '_sezioni.geojson')
    istat_data = gpd.read_file(load_path)

    # check coordinate system (we use epsg 4326)
    assert istat_data.crs['init'] == 'epsg:4326',\
        'Please make sure the input coordinate ref system is epsg:4326'

    assert {common_cfg.sezione_col_name,
            common_cfg.id_quartiere_col_name} <= set(istat_data.columns),\
        'Missing expected standard columns for city %s' % city.name

    # cast sezione ID as int
    istat_data[common_cfg.sezione_col_name] = \
        istat_data[common_cfg.sezione_col_name].astype(np.int64)

    return istat_data.set_index(common_cfg.sezione_col_name)


def fetch_current_menu():
    """Get the current information for the visualization menu."""
    # TODO: replace local file with DAF API
    with open(LOCAL_MENU_PATH, 'r') as file_io:
        current_menu = json.load(file_io)
    return current_menu


## OUTPUT FUNCTIONS

def write_json_kpi_file(city, service_area_name, json_string):
    """Write provided KPI data to json format."""
    # TODO: this should be replaced with DAF API call to push data
    file_path = os.path.join(LOCAL_WRITE_FOLDER,
                             '%s_%s.json' % (city.name, service_area_name))
    with open(file_path, 'w') as file_io:
        file_io.write(json_string)
    return None

def write_updated_menu(json_string):
    """Write updated menu data."""
    # TODO: replace local file with DAF API
    with open(LOCAL_MENU_PATH, 'w') as file_io:
        file_io.write(json_string)
    return None


def write_service_units_attendance(city, service_type, data_to_save):
    """Write provided unit attendance data to geojson format."""
    # TODO: replace hardcoding with API
    units_write_path = os.path.join(
        LOCAL_WRITE_FOLDER,
        'units',  # define units subfolder
        city.name + '_' + SERVICE_FILENAMES_MAPPING[service_type] + '.geojson'
        )

    # save file and overwrite if it already exists
    try:
        os.remove(units_write_path)
    except OSError:
        pass
    data_to_save.to_file(units_write_path, driver='GeoJSON')

    return None
