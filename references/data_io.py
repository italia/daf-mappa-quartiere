"""Module to perform read and write operations."""
import geopandas as gpd
import pandas as pd
import numpy as np
import os

from references import common_cfg
from references.city_items import ServiceType

local_load_folder = common_cfg.processed_path
local_write_folder = common_cfg.output_path

# TODO: when files are available in DAF, server addresses can go here
service_filenames_mapping = {
    ServiceType.School: 'scuole',
    ServiceType.Library: 'biblioteche',
    ServiceType.TransportStop: 'TPL',
    ServiceType.Pharmacy: 'farmacie',
    }

csv_read_settings = {'sep': ';', 'decimal': ','}


def fetch_service_units(service_type, city):
    """Fetch the provided type service units data for the selected city."""

    # TODO: replace hardcoding with API
    load_path = os.path.join(local_load_folder,
                             city.name + '_' + service_filenames_mapping[
                                 service_type] + '.csv')

    if service_type in [ServiceType.Pharmacy, ServiceType.TransportStop]:
        # FIXME: temporary bespoke setting
        service_df = pd.read_csv(load_path, sep=';', decimal='.')
    else:
        # default
        service_df = pd.read_csv(load_path, **csv_read_settings)

    return service_df


def fetch_istat_section_data(city):
    """Fetch the Istat data by section for the provided city."""

    # TODO: replace hardcoding with API
    load_path = os.path.join(local_load_folder, city.name + '_sezioni.geojson')
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


def write_service_units_attendance(city, service_type, data_to_save):
    """Write provided unit attendance data to geojson format."""

    # TODO: replace hardcoding with API
    units_write_path = os.path.join(local_write_folder,
                             'units',  # define units subfolder
                             city.name + '_' + service_filenames_mapping[
                                 service_type] + '.geojson')

    # save file and overwrite if it already exists
    try:
        os.remove(units_write_path)
    except OSError:
        pass
    data_to_save.to_file(units_write_path, driver='GeoJSON')

    return None


def write_json_kpi_file(city, service_type, data_to_save):
    """Write provided KPI data to json format."""
