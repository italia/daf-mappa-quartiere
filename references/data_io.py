"""Module to perform read and write operations."""
import geopandas as gpd
import numpy as np
import os
from references import common_cfg

# from references.city_items import ServiceType

local_load_folder = common_cfg.processed_path


def fetch_service_units(service_type, city):
    #local_load_folder
    pass


def fetch_istat_section_data(city):
    """Fetch the Istat data by section for the provided city."""

    # hardcoded filename standard
    istat_data = gpd.read_file(os.path.join(
        local_load_folder, city.name + '_sezioni.geojson'))

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
