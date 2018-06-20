import os
import geopandas as gpd
import shapely

from src.models.city_items import ServiceType
from references import common_cfg


class ModelCity(dict):
    load_folder = common_cfg.processed_path

    def __init__(self,
                 name, zones_path, zoom_center_tuple, service_layers_dict):
        self.name = name
        self.source = zones_path
        self.zoom_center = zoom_center_tuple
        self.istat_cpa_data = self._get_istat_cpa_data()
        # precompute city boundary
        self.boundary = shapely.ops.cascaded_union(
            self.istat_cpa_data.geometry)
        self.convhull = self.boundary.convex_hull

        super().__init__(service_layers_dict)

    def _get_istat_cpa_data(self):
        # hardcoded filename standard
        loaded = gpd.read_file(os.path.join(
            self.load_folder, self.name + '_sezioni.geojson'))

        # check coordinate system (we use epsg 4326)
        assert loaded.crs['init'] == 'epsg:4326',\
            'Please make sure the input coordinate ref system is epsg:4326'
        assert {common_cfg.sezione_col_name,
                common_cfg.id_quartiere_col_name} <= set(loaded.columns),\
            'Missing expected standard columns for city %s' % self.name

        # cast sezione ID as int
        loaded[common_cfg.sezione_col_name] = \
            loaded[common_cfg.sezione_col_name].astype(int)

        return loaded.set_index(common_cfg.sezione_col_name)

    @property
    def service_paths(self):
        return {s: os.path.join(
            self.load_folder, self[s]) for s in self.keys()}


default_cities = [
    ModelCity(
        'Milano',
        '',
        (11, [9.191383, 45.464211]),  # zoom level and center for d3
        {ServiceType.School: 'Milano_scuole.csv',
         ServiceType.Library: 'Milano_biblioteche.csv',
         ServiceType.TransportStop: 'Milano_TPL.csv',
         ServiceType.Pharmacy: 'Milano_farmacie.csv',
         }),
    ModelCity(
        'Torino',
        '',
        (12, [7.191383, 46]),  # zoom level and center for d3
        {ServiceType.School: 'Torino_scuole.csv',
         ServiceType.Library: 'Torino_biblioteche.csv',
         ServiceType.TransportStop: 'Torino_TPL.csv',
         ServiceType.Pharmacy: 'Torino_farmacie.csv',
         })
]

city_names_list = [city.name for city in default_cities]


def get_city_config(city_name):
    settings = [c for c in default_cities if c.name == city_name]
    assert len(settings) == 1, 'Error in recognising city'
    return settings[0]
