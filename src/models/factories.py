import numpy as np
import pandas as pd
import geopandas as gpd
import geopy
import geopy.distance
import shapely

from references import city_settings, common_cfg, data_io

# enum classes for the model
from references.city_items import AgeGroup, ServiceType
from src.models.core import ServiceUnit


# UnitFactory father class
class UnitFactory:

    """Superclass for all the service unit factories.

    Load from file and prepare the data for service-specific parsing.
    The class constants get overridden in subclasses.

    """

    servicetype = None
    id_col = ''

    def __init__(self, model_city):
        """Load and cache the input data for the service units"""

        assert isinstance(
            model_city, city_settings.ModelCity), 'ModelCity expected'
        self.model_city = model_city

        self._raw_data = data_io.fetch_service_units(
            self.servicetype, self.model_city)

    def extract_locations(self):
        """Preprocess the location data"""
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
                      (self.servicetype,
                       sum(np.bitwise_not(b_within_boundary))))
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


    def append_matching_units_attendance_data(self, units_list):

        """ Trim units to the ones of this loader type and
        append attendance for matching id."""

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

        return data


    def save_units_with_attendance_to_geojson(self, units_list):
        """Collect attendance data and call saving interface."""

        data_to_save = self.append_matching_units_attendance_data(units_list)
        # call writer
        data_io.write_service_units_attendance(
            self.model_city, self.servicetype, data_to_save)

        return None

    @property
    def n_units(self):
        return self._raw_data.shape[0]

    @staticmethod
    def get_factory(service_type):
        """Get the right factory for a ServiceType"""
        type_factory = [factory for factory in UnitFactory.__subclasses__()
                        if factory.servicetype == service_type]
        assert len(type_factory) <= 1, 'Duplicates in loaders types'
        if type_factory:
            return type_factory[0]

        print("We're sorry, this service has not been implemented yet!")
        return []

    @classmethod
    def make_loaders_for_city(cls, model_city):
        """Get all the available factories for a city."""
        loaders_dict = {
            s.label: cls.get_factory(s)(model_city)
            for s in model_city.services}
        return loaders_dict


# UnitFactory children classes
class SchoolFactory(UnitFactory):

    servicetype = ServiceType.School
    name_col = 'DENOMINAZIONESCUOLA'
    type_col = 'ORDINESCUOLA'
    capacity_col = 'ALUNNI'
    id_col = 'CODSCUOLA'

    def load(self, mean_radius, private_rescaling=1, size_power_law=0):

        assert mean_radius, \
            'Please provide a reference radius for the mean school size'
        (propert_data, locations) = super().extract_locations()

        type_age_dict = {
            'SCUOLA PRIMARIA': AgeGroup.ChildPrimary,
            'SCUOLA SECONDARIA I GRADO': AgeGroup.ChildMid,
            }
        school_types = propert_data[self.type_col].unique()
        assert set(school_types) <= set(type_age_dict.keys()), \
            'Unrecognized types in input'

        unit_list = []
        for school_type in school_types:

            b_this_group = propert_data[self.type_col] == school_type
            type_data = propert_data[b_this_group].copy()
            type_locations = [
                l for i, l in enumerate(locations) if b_this_group[i]]
            # analyse capacity
            capacity = type_data[self.capacity_col]
            mean_capacity = capacity.mean()
            print('Observed mean capacity %.2f for %s' %
                  (mean_capacity, school_type))

            # set the lengthscale (radius) to be proportional
            # to the chosen power law of the relative capacity

            type_data['lengthscale'] = \
                mean_radius * (capacity / mean_capacity) ** size_power_law

            for i_unit in range(type_data.shape[0]):
                row_data = type_data.iloc[i_unit, :]
                attr_dict = {'level': school_type,
                             'Public': row_data['bStatale']}

                this_unit = ServiceUnit(
                    self.servicetype,
                    name=row_data[self.name_col],
                    unit_id=row_data[self.id_col],
                    position=type_locations[i_unit],
                    lengthscales={
                        type_age_dict[school_type]: row_data['lengthscale']},
                    capacity=row_data[self.capacity_col],
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
            'Specializzata': [], # do not consider it
            'Importante non specializzata': possible_users,
            'Pubblica': possible_users,
            'NON SPECIFICATA': possible_users,
            'Scolastica': [AgeGroup.ChildPrimary,
                           AgeGroup.ChildMid,
                           AgeGroup.ChildHigh],
            'Istituto di insegnamento superiore': AgeGroup.all_but([
                AgeGroup.Newborn,
                AgeGroup.Kinder,
                AgeGroup.ChildPrimary,
                AgeGroup.ChildMid]),
            'Nazionale': possible_users
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

            type_lenghtscales = {
                group: mean_radius for group in type_age_dict[lib_type]}

            for i_unit in range(type_data.shape[0]):
                row_data = type_data.iloc[i_unit, :]
                attr_dict = {'level': lib_type}
                this_unit = ServiceUnit(self.servicetype,
                                        name=row_data[self.name_col],
                                        unit_id=row_data[self.id_col],
                                        capacity=np.nan,  # we have no data
                                        position=type_locations[i_unit],
                                        lengthscales=type_lenghtscales,
                                        attributes=attr_dict)
                unit_list.append(this_unit)

        return unit_list


class TransportStopFactory(UnitFactory):

    servicetype = ServiceType.TransportStop
    name_col = 'stopCode'
    type_col = 'routeDesc'
    id_col = 'stopCode'

    def load(self, mean_radius):

        assert mean_radius, 'Please provide a reference radius for stops'
        (propert_data, locations) = super().extract_locations()
        # make unique stop code
        propert_data['stop_id'] = propert_data['stop_id'].astype(str)
        propert_data['route_id'] = propert_data['route_id'].astype(str)
        propert_data['stopCode'] = \
            propert_data['stop_id'] + '_' + propert_data['route_id']
        # append route types
        route_type_col = 'route_type'
        gtfs_types_dict = {0: 'Tram',
                           1: 'Metro',
                           2: 'Rail',
                           3: 'Bus',
                           7: 'Funicular'
                           }
        assert all(propert_data[route_type_col].isin(gtfs_types_dict.keys())),\
            'Unexpected route type'
        propert_data['routeDesc'] = \
            propert_data[route_type_col].replace(gtfs_types_dict)

        users = AgeGroup.all_but([AgeGroup.Newborn, AgeGroup.Kinder])

        lengthscales_dict = {0: mean_radius,  # tram, light rail
                             1: 2 * mean_radius,  # underground
                             2: 2 * mean_radius,  # rail
                             3: mean_radius,  # bus
                             7: 2 * mean_radius  # funicular
                             }
        thresholds_dict = {t: None for t in lengthscales_dict}

        unit_list = []
        for i_unit in range(propert_data.shape[0]):
            row_data = propert_data.iloc[i_unit, :]
            unit_route_type = row_data[route_type_col]
            attr_dict = {'routeType': row_data[self.type_col]}
            # this is None by default

            this_unit = ServiceUnit(
                self.servicetype,
                name=row_data[self.name_col],
                unit_id=row_data[self.id_col],
                position=locations[i_unit],
                capacity=np.nan,  # we have no capacity data yet
                lengthscales={
                    g: lengthscales_dict[unit_route_type] for g in users},
                kernel_thresholds=thresholds_dict[unit_route_type],
                attributes=attr_dict
                )

            unit_list.append(this_unit)
            # if there are no provided thresholds for this unit type,
            #  cache the computed ones
            if not thresholds_dict[unit_route_type]:
                thresholds_dict[unit_route_type] = this_unit.ker_thresholds

        return unit_list


class PharmacyFactory(UnitFactory):

    servicetype = ServiceType.Pharmacy
    name_col = 'CODICEIDENTIFICATIVOFARMACIA'
    id_col = name_col

    def load(self, mean_radius=None):
        assert mean_radius, 'Please provide a reference radius for pharmacies'
        (propert_data, locations) = super().extract_locations()

        col_attributes = {
            'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unit_list = []
        # We assume all pharmacies share the same capacity, so only one
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
                capacity=np.nan,  # we have no capacity data yet
                lengthscales={g: mean_radius for g in AgeGroup.all()},
                kernel_thresholds=cached_thresholds,
                attributes=attr_dict)

            unit_list.append(this_unit)
            # if there were no thresholds, cache the computed ones
            if not cached_thresholds:
                cached_thresholds = this_unit.ker_thresholds

        return unit_list


class UrbanGreenFactory(UnitFactory):
    pass
