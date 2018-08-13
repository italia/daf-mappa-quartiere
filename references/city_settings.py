import os
import shapely

from references.city_items import ServiceType
from references import common_cfg, data_io


class ModelCity(dict):
    """Stores all the initalised settings for a city in the application."""
    def __init__(self,
                 name, zones_path, zoom_center_tuple, service_layers_dict):

        self.name = name
        self.source = zones_path
        self.zoom_center = zoom_center_tuple

        super().__init__(service_layers_dict)

        # load istat data
        self.istat_cpa_data = data_io.fetch_istat_section_data(self)

        # precompute city boundary
        self.boundary = shapely.ops.cascaded_union(
            self.istat_cpa_data.geometry)
        self.convhull = self.boundary.convex_hull

    @property
    def service_paths(self):
        return {s: os.path.join(
            common_cfg.processed_path, self[s]) for s in self.keys()}


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
         }),
    ModelCity(
        'Bari',
        '',
        (10, [16.871871, 41.117143]),  # zoom level and center for d3
        {ServiceType.School: 'Bari_scuole.csv',
         ServiceType.Library: 'Bari_biblioteche.csv',
         #ServiceType.TransportStop: 'Bari_TPL.csv',
         ServiceType.Pharmacy: 'Bari_farmacie.csv',
         }),
    ModelCity(
         'Firenze',
         '',
         (10, [11.2462600, 43.7792500]),  # zoom level and center for d3
         {ServiceType.School: 'Firenze_scuole.csv',
          ServiceType.Library: 'Firenze_biblioteche.csv',
          ServiceType.TransportStop: 'Firenze_TPL.csv',
          ServiceType.Pharmacy: 'Firenze_farmacie.csv',
          }),
    ModelCity(
         'Roma',
         '',
         (10, [12.49, 41.91]),  # zoom level and center for d3
         {ServiceType.School: 'Roma_scuole.csv',
          ServiceType.Library: 'Roma_biblioteche.csv',
          ServiceType.TransportStop: 'Roma_TPL.csv',
          ServiceType.Pharmacy: 'Roma_farmacie.csv',
          })

    ]

city_names_list = [city.name for city in default_cities]


def get_city_config(city_name):
    settings = [c for c in default_cities if c.name == city_name]
    assert len(settings) == 1, 'Error in recognising city'
    return settings[0]
