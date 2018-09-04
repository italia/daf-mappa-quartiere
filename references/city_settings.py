"""Module to store all the city-specific settings for the application."""

import shapely

from references.city_items import ServiceType
from references import data_io


class ModelCity:
    """Stores all the initalised settings for a city in the application."""
    def __init__(self, name, zones_path, zoom_center_tuple,
                 available_services):

        assert isinstance(available_services, list), 'List expected'

        self.name = name
        self.source = zones_path
        self.zoom_center = zoom_center_tuple
        self.services = available_services

        # load istat data
        self.istat_cpa_data = data_io.fetch_istat_section_data(self)

        # precompute city boundary
        self.boundary = shapely.ops.cascaded_union(
            self.istat_cpa_data.geometry)
        self.convhull = self.boundary.convex_hull


DEFAULT_CITIES = [
    ModelCity(
        'Milano',
        '',
        (11, [9.191383, 45.464211]),  # zoom level and center for d3
        [ServiceType.School,
         ServiceType.Library,
         ServiceType.TransportStop,
         ServiceType.Pharmacy]
        ),
    ModelCity(
        'Torino',
        '',
        (12, [7.191383, 46]),  # zoom level and center for d3
        [ServiceType.School,
         ServiceType.Library,
         ServiceType.TransportStop,
         ServiceType.Pharmacy]
        ),
    ModelCity(
        'Bari',
        '',
        (10, [16.871871, 41.117143]),  # zoom level and center for d3
        [ServiceType.School,
         ServiceType.Library,
         #ServiceType.TransportStop,
         ServiceType.Pharmacy]
        ),
    ModelCity(
        'Firenze',
        '',
        (10, [11.2462600, 43.7792500]), # zoom level and center for d3
        [ServiceType.School,
         ServiceType.Library,
         ServiceType.TransportStop,
         ServiceType.Pharmacy]
        ),
    ModelCity(
        'Roma',
        '',
        (10, [12.49, 41.91]),  # zoom level and center for d3
        [ServiceType.School,
         ServiceType.Library,
         #ServiceType.TransportStop,
         ServiceType.Pharmacy]
        )
    ]

CITY_NAMES_LIST = [city.name for city in DEFAULT_CITIES]


def get_city_config(city_name):
    """Get default config for a given city name."""
    settings = [c for c in DEFAULT_CITIES if c.name == city_name]
    assert len(settings) == 1, 'Error in recognising city'
    return settings[0]
