import os
import json
import re
import numpy as np
import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt

import geopy
import geopy.distance
import shapely
from scipy.interpolate import griddata

from references import common_cfg, city_settings
from src.models.city_items import AgeGroup, ServiceType
from src.models.core import ServiceValues, MappedPositionsFrame, KPICalculator

plt.rcParams['figure.figsize'] = (20, 14)


class GridMaker:

    """Create a grid and map it to various given land subdivisions.

    """

    def __init__(self, city_geo_files_dict, grid_step=0.1):  # grid_step in km

        self._quartiere_key = 'quartieri'  # hardcoded

        # load division geofiles with geopandas
        self.subdivisions = {}
        for name, file_name in city_geo_files_dict.items():
            self.subdivisions[name] = gpd.read_file(file_name)

        # compute city boundary
        self.city_boundary = shapely.ops.cascaded_union(
            self.subdivisions[self._quartiere_key]['geometry'])

        # precompute coordinate ranges
        self.long_range = (self.city_boundary.bounds[0],
                           self.city_boundary.bounds[2])
        self.lat_range = (self.city_boundary.bounds[1],
                          self.city_boundary.bounds[3])
        self.long_n_grid = int(self.longitude_range_km // grid_step) + 1
        self.lat_n_grid = int(self.latitude_range_km // grid_step) + 1

        (self._x_plot, self._y_plot) = np.meshgrid(
            np.linspace(*self.long_range, self.long_n_grid),
            np.linspace(*self.lat_range, self.lat_n_grid), indexing='ij')

        # construct point objects with same shape
        self._b_in_perimeter = np.empty_like(self._x_plot, dtype=bool)
        self._id_quartiere = np.empty_like(self._x_plot, dtype=object)

        for (i, j), _ in np.ndenumerate(self._b_in_perimeter):
            shapely_point = shapely.geometry.Point(
                (self._x_plot[i, j], self._y_plot[i, j]))
            # mark points outside boundaries
            self._b_in_perimeter[i, j] = \
                self.city_boundary.contains(shapely_point)

            if self._b_in_perimeter[i, j]:
                b_found = False
                for i_row in range(self.subdivisions[
                        self._quartiere_key].shape[0]):
                    this_quartiere_polygon = self.subdivisions[
                        self._quartiere_key]['geometry'][i_row]
                    if this_quartiere_polygon.contains(shapely_point):
                        # assign found ID
                        self._id_quartiere[i, j] = self.subdivisions[
                            self._quartiere_key][
                                common_cfg.id_quartiere_col_name][i_row]
                        b_found = True
                        break  # skip remaining zones
                assert b_found, \
                    'Point within city boundary was not assigned to any zone'

            else:  # assign default value for points outside city perimeter
                self._id_quartiere[i, j] = np.nan

        # call common format constructor
        self.grid = MappedPositionsFrame.from_coordinates_arrays(
            long=self._x_plot[self._b_in_perimeter].flatten(),
            lat=self._y_plot[self._b_in_perimeter].flatten(),
            id_quartiere=self._id_quartiere[self._b_in_perimeter].flatten())

        self.full_grid = MappedPositionsFrame.from_coordinates_arrays(
            long=self._x_plot.flatten(),
            lat=self._y_plot.flatten(),
            id_quartiere=self._id_quartiere.flatten())

    @property
    def longitude_range_km(self):
        return geopy.distance.great_circle(
            (self.lat_range[0], self.long_range[0]),
            (self.lat_range[0], self.long_range[1])).km

    @property
    def latitude_range_km(self):
        return geopy.distance.great_circle(
            (self.lat_range[0], self.long_range[0]),
            (self.lat_range[1], self.long_range[0])).km


# Plot tools
class ValuesPlotter:

    """Plot various output from ServiceValues.

    """

    def __init__(self, service_values, b_on_grid=False):
        assert isinstance(
            service_values, ServiceValues), 'ServiceValues class expected'
        self.values = service_values
        self.b_on_grid = b_on_grid

    def plot_locations(self):
        """Plot the locations of the provided ServiceValues"""
        coord_names = common_cfg.coord_col_names
        plt.figure()
        plt.scatter(self.values.mapped_positions[coord_names[0]],
                    self.values.mapped_positions[coord_names[1]])
        plt.xlabel(coord_names[0])
        plt.ylabel(coord_names[1])
        plt.axis('equal')
        plt.show()
        return None

    def plot_service_levels(self, serv_type, grid_density=40, n_levels=50):
        """Plot a contour graph of the results for each age group"""
        assert isinstance(
            serv_type, ServiceType), 'ServiceType expected in input'

        for age_group in self.values[serv_type].keys():

            x_plot, y_plot, z_plot = self.values.plot_output(
                serv_type, age_group)

            if (~all(np.isnan(z_plot))) & (np.count_nonzero(z_plot) > 0):
                if self.b_on_grid:
                    grid_shape = (len(set(x_plot)), len(set(y_plot.flatten())))
                    assert len(x_plot) == grid_shape[0] * grid_shape[
                        1], 'X values do not seem on a grid'
                    assert len(y_plot) == grid_shape[0] * grid_shape[
                        1], 'Y values do not seem on a grid'
                    xi = np.array(x_plot).reshape(grid_shape)
                    yi = np.array(y_plot).reshape(grid_shape)
                    zi = z_plot.reshape(grid_shape)
                else:
                    # grid the data using natural neighbour interpolation
                    xi = np.linspace(min(x_plot), max(x_plot), grid_density)
                    yi = np.linspace(min(y_plot), max(y_plot), grid_density)
                    zi = griddata((x_plot, y_plot), z_plot,
                                  (xi[None, :], yi[:, None]), 'nearest')
                plt.figure()
                plt.title(age_group)
                contour_axes = plt.contourf(xi, yi, zi, n_levels)
                cbar = plt.colorbar(contour_axes)
                cbar.ax.set_ylabel('Service level')
                plt.show()

        return None


class JSONWriter:

    """Handle IO output from model to JSON for visualization.

    """

    write_options_dict = {'sort_keys': True,
                          'indent': 4,
                          'separators': (',', ' : ')}

    nan_string = '"NaN"'

    def __init__(self, kpi_calculator):
        assert isinstance(kpi_calculator, KPICalculator), \
            'KPI calculator is needed'
        self.layers_data = kpi_calculator.quartiere_kpi
        self.istat_data = kpi_calculator.istat_kpi
        self.vitality_data = kpi_calculator.istat_vitality
        self.city = city_settings.get_city_config(kpi_calculator.city)
        self.areas_tree = {}
        for serv_type in self.layers_data:
            area = serv_type.service_area
            self.areas_tree[area] = [serv_type] + self.areas_tree.get(area, [])

    def make_menu(self):

        def make_output_menu(city, services, istat_layers=None):
            """Creates a list of dictionaries
            that is ready to be saved as a json"""
            out_list = []
            assert isinstance(
                city, city_settings.ModelCity), 'City template expected'

            # source element
            source_id = city.name + '_quartieri'
            source_item = common_cfg.menu_group_template.copy()
            source_item['city'] = city.name
            source_item['url'] = city.source
            source_item['id'] = source_id
            # add center and zoom info for the source layer only
            source_item['zoom'] = city.zoom_center[0]
            source_item['center'] = city.zoom_center[1]

            # declare the joinField
            source_item['joinField'] = common_cfg.id_quartiere_col_name

            #  Does a source have a data_source?
            # 'data_source': '',
            out_list.append(source_item)

            # service layer items
            areas = set(s.service_area for s in services)
            for area in areas:
                this_services = [s for s in services if s.service_area == area]
                layer_item = common_cfg.menu_group_template.copy()
                layer_item['type'] = 'layer'
                layer_item['city'] = city.name
                layer_item['id'] = city.name + '_' + area.value
                layer_item['url'] = ''  # default empty url
                layer_item['source_id'] = source_id  # link to defined source
                #
                layer_item['indicators'] = ([{
                    'category': service.service_area.value,
                    'label': service.label,
                    'id': service.name,
                    'data_source': service.data_source,
                    } for service in this_services])

                out_list.append(layer_item)

            # istat layers items
            if istat_layers:
                for istat_area, indicators in istat_layers.items():
                    istat_item = common_cfg.menu_group_template.copy()
                    istat_item['type'] = 'layer'
                    istat_item['city'] = city.name
                    istat_item['id'] = city.name + '_' + istat_area
                    istat_item['url'] = ''  # default empty url
                    # link to defined source
                    istat_item['source_id'] = source_id
                    #
                    istat_item['indicators'] = ([{
                        'category': istat_area,
                        'label': indicator,
                        'id': indicator,
                        'data_source': 'ISTAT'
                        } for indicator in indicators])
                    out_list.append(istat_item)

            return out_list

        json_list = make_output_menu(
            self.city,
            services=list(self.layers_data.keys()),
            istat_layers={'Vitalita': list(self.vitality_data.columns)}
            )
        return json_list

    def make_serviceareas_output(self, precision=4):

        out = dict()
        # tool to format frame data that does not depend on age

        def prepare_frame_data(frame_in):
            frame_in = frame_in.round(precision)
            orig_type = frame_in.index.dtype.type
            data_dict = frame_in.reset_index().to_dict(orient='records')
            # restore type as pandas has a bug and casts to float if int
            for quartiere_data in data_dict:
                old_value = quartiere_data[common_cfg.id_quartiere_col_name]
                if orig_type in (np.int32, np.int64, int):
                    quartiere_data[
                        common_cfg.id_quartiere_col_name] = int(old_value)

            return data_dict

        # make istat layer
        out[common_cfg.istat_layer_name] = prepare_frame_data(self.istat_data)

        # make vitality layer
        out[common_cfg.vitality_layer_name] = prepare_frame_data(
            self.vitality_data)

        # make layers
        for area, layers in self.areas_tree.items():
            layer_list = []
            for service in layers:
                data = self.layers_data[service].round(precision)
                layer_list.append(pd.Series(
                    data[AgeGroup.all()].as_matrix().tolist(),
                    index=data.index, name=service.name))
            area_data = pd.concat(layer_list, axis=1).reset_index()
            out[area.value] = area_data.to_dict(orient='records')

        return out

    @classmethod
    def _dump_json(cls, input_obj, file_io):
        """Replace default nan export with class setting"""
        string_json = json.dumps(input_obj, **cls.write_options_dict)
        # replace default 'Nan' with cls property string
        regex = re.compile(r'\bNaN\b', flags=re.IGNORECASE)
        string_json = re.sub(regex, cls.nan_string, string_json)
        # write to file
        file_io.write(string_json)

    def _update_menu_in_default_path(self):
        """Load current menu from json and replace the calculator city info
        with new data"""
        with open(os.path.join(
            common_cfg.viz_output_path, 'menu.json'), 'r') as orig_file:
            current_menu = json.load(orig_file)

        other_items = [v for v in current_menu if v['city'] != self.city.name]
        updated_menu = other_items + self.make_menu()

        with open(os.path.join(
            common_cfg.viz_output_path, 'menu.json'), 'w') as menu_file:
            self._dump_json(updated_menu, menu_file)

    def write_all_files_to_default_path(self):
        # update menu
        self._update_menu_in_default_path()

        # build and write all areas
        areas_output = self.make_serviceareas_output()
        for name, data in areas_output.items():
            filename = '%s_%s.json' % (self.city.name, name)
            with open(os.path.join(common_cfg.output_path,
                                   filename), 'w') as area_file:
                self._dump_json(data, area_file)
