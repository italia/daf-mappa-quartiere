import os
import os.path
import numpy as np
import pandas as pd
import geopandas as gpd
import geopy
import geopy.distance
import sys
import shapely

from references import city_settings, common_cfg

# enum classes for the model
from src.models.city_items import AgeGroup, ServiceType
from src.models.core import ServiceUnit

# TODO: find way to put this into some global settings
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)


# UnitFactory father class
class UnitFactory:
    servicetype = None  # this gets overridden in subclasses

    def __init__(self, model_city, sep_input=';', decimal_input=','):
        assert isinstance(
            model_city, city_settings.ModelCity), 'ModelCity expected'
        self.model_city = model_city
        self._raw_data = pd.read_csv(
            self.file_path, sep=sep_input, decimal=decimal_input)

    def extract_locations(self):
        default_pos_columns = common_cfg.coord_col_names
        if set(default_pos_columns).issubset(set(self._raw_data.columns)):
            print('Location data found')
            # check and drop units outside provided city boundary
            geometry = [shapely.geometry.Point(xy) for xy in zip(
                self._raw_data[default_pos_columns[0]],  # Long
                self._raw_data[default_pos_columns[1]])]  # Lat
            b_within_boundary = np.array(list(map(
                lambda p: p.within(self.model_city.convhull), geometry)))

            if not all(b_within_boundary):
                print('%s -- dropping %i units outside city.' %
                      (self.servicetype, sum(~b_within_boundary)))

                self._raw_data = self._raw_data.iloc[
                    b_within_boundary, :].reset_index()

            # store geolocations as geopy Point
            locations = [geopy.Point(yx) for yx in zip(
                self._raw_data[default_pos_columns[1]],  # Lat
                self._raw_data[default_pos_columns[0]])]  # Long

            propert_data = self._raw_data.drop(default_pos_columns, axis=1)

        else:
            raise NotImplementedError('Locations not found - not implemented!')

        return propert_data, locations

    def save_units_with_attendance_to_geojson(self, units_list):
        """ Trim units to the ones of this loader type and
        append attendance for matching id. Then export original unit data
        completed with attendance in geojson format"""

        data = gpd.GeoDataFrame(self._raw_data).copy()
        # convert bool in GeoDataFrame to str in order to save it
        for col in data.columns:
            if data[col].dtype in (np.bool, bool):
                data[col] = data[col].astype(str)
        # build geometry column
        long_col, lat_col = common_cfg.coord_col_names
        data = data.set_geometry([shapely.geometry.Point(xy) for xy in zip(
            data[long_col], data[lat_col])])

        # append attendance
        compatible_units = [u for u in units_list if
                            u.service == self.servicetype]
        if compatible_units:
            unit_frame = pd.DataFrame(
                {self.id_col: [u.id for u in compatible_units],
                 'Affluenza': [u.attendance for u in compatible_units]})
            data = data.merge(unit_frame, on=self.id_col)

        # save file and overwrite if it already exists
        try:
            os.remove(self.output_path)
        except OSError:
            pass

        data.to_file(self.output_path, driver='GeoJSON')

        return data

    @property
    def n_units(self):
        return self._raw_data.shape[0]

    @property
    def file_path(self):
        return self.model_city.service_paths[self.servicetype]

    @property
    def output_path(self):
        _, fullfile = os.path.split(self.file_path)
        filename, _ = os.path.splitext(fullfile)
        return os.path.join(
            common_cfg.units_output_path, filename + '.geojson')

    @staticmethod
    def get_factory(service_type):
        type_factory = [factory for factory in UnitFactory.__subclasses__()
                        if factory.servicetype == service_type]
        assert len(type_factory) <= 1, 'Duplicates in loaders types'
        if type_factory:
            return type_factory[0]
        else:
            print("We're sorry, this service has not been implemented yet!")
            return []

    @staticmethod
    def make_loaders_for_city(model_city):
        loaders_dict = {}
        for sType in model_city.keys():
            loaders_dict[sType.label] = \
                UnitFactory.get_factory(sType)(model_city)
        return loaders_dict


# UnitFactory children classes
class SchoolFactory(UnitFactory):

    servicetype = ServiceType.School
    name_col = 'DENOMINAZIONESCUOLA'
    type_col = 'ORDINESCUOLA'
    scale_col = 'ALUNNI'
    id_col = 'CODSCUOLA'

    def load(self, mean_radius=None, private_rescaling=1, size_power_law=0):

        assert mean_radius, \
            'Please provide a reference radius for the mean school size'
        (propert_data, locations) = super().extract_locations()

        type_age_dict = {
            'SCUOLA PRIMARIA': {AgeGroup.ChildPrimary: 1},
            'SCUOLA SECONDARIA I GRADO': {AgeGroup.ChildMid: 1},
            'SCUOLA SECONDARIA II GRADO': {AgeGroup.ChildHigh: 1}
        }

        school_types = propert_data[self.type_col].unique()
        assert set(school_types) <= set(type_age_dict.keys()), \
            'Unrecognized types in input'

        attendance_proxy = propert_data[self.scale_col].copy()

        # set the scale to be proportional
        # to the square root of number of children
        scale_data = attendance_proxy ** size_power_law

        # mean value is mapped to input parameter
        scale_data = scale_data / scale_data.mean() * mean_radius

        # assign to new column
        rescaled_name = 'SCALE'
        propert_data[rescaled_name] = scale_data
        unit_list = []

        for school_type in school_types:
            b_this_group = propert_data[self.type_col] == school_type
            type_data = propert_data[b_this_group]
            type_locations = [
                l for i, l in enumerate(locations) if b_this_group[i]]

            for i_unit in range(type_data.shape[0]):
                row_data = type_data.iloc[i_unit, :]
                attr_dict = {'level': school_type,
                             'Public': row_data['bStatale']}

                this_unit = ServiceUnit(
                    self.servicetype,
                    name=row_data[self.name_col],
                    unit_id=row_data[self.id_col],
                    position=type_locations[i_unit],
                    age_diffusion=type_age_dict[school_type],
                    scale=row_data[rescaled_name],
                    attributes=attr_dict)

                if not attr_dict['Public'] and private_rescaling != 1:
                    this_unit.transform_kernels_with_factor(private_rescaling)

                unit_list.append(this_unit)

        return unit_list


class LibraryFactory(UnitFactory):

    servicetype = ServiceType.Library
    name_col = 'denominazioni.ufficiale'
    type_col = 'tipologia-funzionale'
    id_col = 'codiceIsil'

    def load(self, mean_radius=None):

        assert mean_radius, \
            'Please provide a reference radius for the mean library size'
        (propert_data, locations) = super().extract_locations()

        # Modifica e specifica che per le fasce d'età
        possible_users = AgeGroup.all_but([AgeGroup.Newborn, AgeGroup.Kinder])
        type_age_dict = {
            'Specializzata': {group: 1 for group in possible_users},
            'Importante non specializzata': {
                group: 1 for group in possible_users},
            'Pubblica': {group: 1 for group in possible_users},
            'NON SPECIFICATA': {group: 1 for group in possible_users},
            'Scolastica': {group: 1 for group in [
                AgeGroup.ChildPrimary, AgeGroup.ChildMid, AgeGroup.ChildHigh]},
            'Istituto di insegnamento superiore': {
                group: 1 for group in AgeGroup.all_but([
                    AgeGroup.Newborn,
                    AgeGroup.Kinder,
                    AgeGroup.ChildPrimary,
                    AgeGroup.ChildMid])},
            'Nazionale': {group: 1 for group in possible_users}
        }

        library_types = propert_data[self.type_col].unique()
        assert set(library_types) <= set(type_age_dict.keys()), \
            'Unrecognized types in input'

        unit_list = []

        for lib_type in library_types:
            b_this_group = propert_data[self.type_col] == lib_type
            type_data = propert_data[b_this_group]
            type_locations = [l for i, l in enumerate(locations) if
                              b_this_group[i]]

            for i_unit in range(type_data.shape[0]):
                row_data = type_data.iloc[i_unit, :]
                attr_dict = {'level': lib_type}
                this_unit = ServiceUnit(self.servicetype,
                                        name=row_data[self.name_col],
                                        unit_id=row_data[self.id_col],
                                        scale=mean_radius,
                                        position=type_locations[i_unit],
                                        age_diffusion=type_age_dict[lib_type],
                                        attributes=attr_dict)
                unit_list.append(this_unit)

        return unit_list


class TransportStopFactory(UnitFactory):

    servicetype = ServiceType.TransportStop
    name_col = 'stopCode'
    type_col = 'routeDesc'
    id_col = 'stopCode'

    def __init__(self, model_city):
        super().__init__(model_city, decimal_input='.')

    def load(self, mean_radius):

        assert mean_radius, 'Please provide a reference radius for stops'
        (propert_data, locations) = super().extract_locations()
        # make unique stop code
        propert_data['stopCode'] = \
            propert_data['stop_id'] + '_' + propert_data['route_id']
        # append route types
        route_type_col = 'route_type'
        gtfs_types_dict = {0: 'Tram', 1: 'Metro', 3: 'Bus'}
        assert all(propert_data[route_type_col].isin(gtfs_types_dict.keys())),\
            'Unexpected route type'
        propert_data['routeDesc'] = \
            propert_data[route_type_col].replace(gtfs_types_dict)

        scale_dict = {0: mean_radius, 1: 2 * mean_radius, 3: mean_radius}
        thresholds_dict = {t: None for t in scale_dict.keys()}

        unit_list = []
        for i_unit in range(propert_data.shape[0]):
            row_data = propert_data.iloc[i_unit, :]
            unit_route_type = row_data[route_type_col]
            attr_dict = {'routeType': row_data[self.type_col]}
            # this is None by default
            cached_thresholds = thresholds_dict[unit_route_type]
            this_unit = ServiceUnit(self.servicetype,
                                    name=row_data[self.name_col],
                                    unit_id=row_data[self.id_col],
                                    position=locations[i_unit],
                                    scale=scale_dict[unit_route_type],
                                    age_diffusion={
                                        g: 1 for g in AgeGroup.all_but(
                                            [AgeGroup.Newborn, AgeGroup.Kinder])},
                                    kernel_thresholds=cached_thresholds,
                                    attributes=attr_dict)
            unit_list.append(this_unit)
            # if there are no provided thresholds for this unit type,
            #  cache the computed ones
            if not cached_thresholds:
                thresholds_dict[unit_route_type] = this_unit.ker_thresholds

        return unit_list


class PharmacyFactory(UnitFactory):

    servicetype = ServiceType.Pharmacy
    name_col = 'CODICEIDENTIFICATIVOFARMACIA'
    id_col = name_col

    def __init__(self, model_city):
        super().__init__(model_city, decimal_input='.')

    def load(self, mean_radius=None):
        assert mean_radius, 'Please provide a reference radius for pharmacies'
        (propert_data, locations) = super().extract_locations()

        col_attributes = {
            'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unit_list = []
        # We assume all pharmacies share the same scale, so only one
        # threshold is necessary
        cached_thresholds = None
        for i_unit in range(propert_data.shape[0]):
            row_data = propert_data.iloc[i_unit, :]
            attr_dict = {name: row_data[col] for name, col in
                         col_attributes.items()}
            this_unit = ServiceUnit(
                self.servicetype,
                name=row_data[self.name_col].astype(str),
                unit_id=row_data[self.id_col],
                position=locations[i_unit],
                scale=mean_radius,
                age_diffusion={g: 1 for g in AgeGroup.all()},
                kernel_thresholds=cached_thresholds,
                attributes=attr_dict)

            unit_list.append(this_unit)
            # if there were no thresholds, cache the computed ones
            if not cached_thresholds:
                cached_thresholds = this_unit.ker_thresholds

        return unit_list


class UrbanGreenFactory(UnitFactory):
    servicetype = ServiceType.UrbanGreen
