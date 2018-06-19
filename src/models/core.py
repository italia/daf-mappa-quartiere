import os
import sys
from time import time
import geopy
import geopy.distance
import numpy as np
import pandas as pd
from sklearn import gaussian_process
from matplotlib import pyplot as plt
import functools

from scipy.optimize import fsolve
from scipy.spatial.distance import cdist

from references import common_cfg, istat_kpi, city_settings
# enum classes for the model
from src.models.city_items import AgeGroup, ServiceType


# TODO: find way to put this into some global settings
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

gaussKern = gaussian_process.kernels.RBF


@functools.lru_cache(maxsize=int(1e6))  # cache expensive distance calculation
def compute_distance(x, y):
    return geopy.distance.great_circle(x, y).km


# ServiceUnit class
class ServiceUnit:
    def __init__(self, service, name, unit_id, position, scale,
                 age_diffusion=None, kernel_thresholds=None,
                 attributes=None):
        assert isinstance(
            position, geopy.Point), 'Position must be a geopy Point'
        assert isinstance(
            service, ServiceType), 'Service must belong to the Eum'
        assert isinstance(name, str), 'Name must be a string'
        assert (np.isscalar(scale)) & \
               (scale > 0), 'Scale must be a positive scalar'
        assert set(age_diffusion.keys()) <= set(
            AgeGroup.all()), 'Diffusion keys should be AgeGroups'
        if not attributes:
            attributes = {}
        assert isinstance(
            attributes, dict), 'Attributes have to be provided in a dict'
        if kernel_thresholds:
            assert set(kernel_thresholds.keys()) >= set(age_diffusion.keys()),\
                'Kernel thresholds if provided must' \
                ' be defined for every age diffusion key'
            b_thresholds_input = True
        else:
            b_thresholds_input = False

        self.name = name
        self.id = unit_id
        self.service = service

        # A ServiceType can have many sites, so each unit has its own.
        # Moreover, a site is not uniquely assigned to a service
        self.site = position
        self.coord_tuple = (position.latitude, position.longitude)

        self.scale = scale  # store scale info
        self.attributes = attributes  # dictionary

        # how the service availability area varies for different age groups
        self.age_diffusion = age_diffusion

        # define kernel taking scale into account
        self.kernel = {g: gaussKern(length_scale=l * self.scale)
                       for g, l in self.age_diffusion.items()}

        # precompute kernel threshold per AgeGroup
        # initialise to Inf
        self.ker_thresholds = {g: np.Inf for g in AgeGroup.all()}
        if b_thresholds_input:
            assert all([isinstance(kern, gaussKern)
                        for kern in self.kernel.values()]),\
                'Unexpected kernel type in ServiceUnit'
            assert all([val > 0 for val in kernel_thresholds.values()]), \
                'Thresholds must be positive'
            self.ker_thresholds.update(kernel_thresholds)
        else:
            self._compute_kernel_thresholds()

        # initialise attendance
        self.attendance = np.nan

    def _compute_kernel_thresholds(self):
        """Triggers kernel thresholds computation for all ages groups"""
        for age_group in self.kernel.keys():
            kern = self.kernel[age_group]
            threshold_value = np.Inf
            if not isinstance(kern, gaussKern):
                # check it's a rescaled gaussian
                if not (isinstance(kern, gaussian_process.kernels.Product) and
                        isinstance(kern.k1,
                                   gaussian_process.kernels.ConstantKernel) and
                        isinstance(kern.k2, gaussKern)):
                    print('WARNING: skipping kernel thresholds '
                          'for type %s' % type(kern))
                    # skip this age group
                    continue

            def fun_to_solve(x):
                out = self.kernel[age_group](
                    x, np.array([[0], ])) - common_cfg.kernel_value_cutoff
                return out.flatten()

            initial_guess = common_cfg.kernel_start_zero_guess * self.scale

            for k in range(3):  # try 3 alternatives
                solution_value, _, flag, msg = \
                    fsolve(fun_to_solve, np.array(initial_guess),
                           full_output=True)
                if flag == 1:
                    threshold_value = solution_value  # assign found value
                    break
                else:
                    initial_guess = initial_guess * 1.1
            if flag != 1:
                print('WARNING: could not compute thresholds '
                      'for unit %s, age %s' % (self.name, age_group))

            # assign positive value as threshold
            self.ker_thresholds[age_group] = abs(threshold_value)

    def transform_kernels_with_factor(self, rescaling_factor):
        """This function applies the transformation:
          newKernel = k * oldKernel(x/k) """
        assert rescaling_factor > 0, 'Expected positive factor'
        for age_group in self.kernel.keys():
            # change lengthscale
            self.kernel[age_group].length_scale =\
                self.kernel[age_group].length_scale / rescaling_factor
            self.kernel[age_group] = rescaling_factor * self.kernel[age_group]

        # trigger threshold recomputation
        self._compute_kernel_thresholds()

    def evaluate(self, target_coords, age_group):
        # evaluate kernel to get service level score.
        # If age group is not relevant to the service, return 0 as default
        if self.kernel.__contains__(age_group):
            assert isinstance(target_coords, np.ndarray), 'ndarray expected'
            assert target_coords.shape[1] == 2, 'lat and lon columns expected'
            # get distances
            distances = np.zeros(shape=(len(target_coords), 1))
            distances[:, 0] = np.apply_along_axis(
                lambda x: compute_distance(tuple(x), self.coord_tuple),
                axis=1, arr=target_coords)

            score = self.kernel[age_group](distances, np.array([[0], ]))

        else:
            score = np.zeros(shape=target_coords.shape[0])

        return np.squeeze(score)


# Mapped positions frame class
class MappedPositionsFrame(pd.DataFrame):
    """A class to collect an array of positions alongside areas labels"""

    def __init__(self, long, lat, geopy_pos, id_quartiere):
        # check id quartiere input
        if id_quartiere:
            assert len(long) == len(id_quartiere), 'Inconsistent lengths'

        # create mapping dict from all inputs
        mapping_dict = {
            common_cfg.coord_col_names[0]: long,
            common_cfg.coord_col_names[1]: lat,
            common_cfg.id_quartiere_col_name: id_quartiere,
            common_cfg.positions_col: geopy_pos,
            common_cfg.tuple_index_name: [tuple(p) for p in geopy_pos]
            }

        # finally call DataFrame constructor
        super().__init__(mapping_dict)
        self.set_index(
            [common_cfg.id_quartiere_col_name, common_cfg.tuple_index_name],
            inplace=True)

    @classmethod
    def from_geopy_points(cls, geopy_points, id_quartiere=None):
        assert all([isinstance(
            t, geopy.Point) for t in geopy_points]), 'Geopy Points expected'

        out = cls(long=[x.longitude for x in geopy_points],
                  lat=[x.latitude for x in geopy_points],
                  geopy_pos=geopy_points,
                  id_quartiere=id_quartiere)
        return out

    @classmethod
    def from_coordinates_arrays(cls, long, lat, id_quartiere=None):
        assert len(long) == len(lat), 'Inconsistent lengths'

        geopy_points = [geopy.Point(yx) for yx in zip(lat, long)]

        out = cls(
            long=long, lat=lat, geopy_pos=geopy_points,
            id_quartiere=id_quartiere)
        return out

    @classmethod
    def from_tuples(cls, tuple_list, id_quartiere=None):
        assert all([isinstance(
            t, tuple) for t in tuple_list]), 'tuple positions expected'

        geopy_points = [geopy.Point(t[1], t[0]) for t in tuple_list]

        out = cls(long=[x.longitude for x in geopy_points],
                  lat=[x.latitude for x in geopy_points],
                  geopy_pos=geopy_points, id_quartiere=id_quartiere)
        return out


# Demand modelling
class DemandFrame(pd.DataFrame):
    """A class to store demand units in row and
    make them available for aggregation"""

    OUTPUT_AGES = AgeGroup.all()
    _metadata = ['ages_frame', 'mapped_positions']

    def __init__(self, df_input, b_duplicates_check=True):
        assert isinstance(df_input, pd.DataFrame), 'Input DataFrame expected'

        # initialise and assign base DataFrame properties
        # FIXME: this is not nice at all. Refactor to properly inherit from df
        super().__init__()
        self.__dict__.update(df_input.copy().__dict__)

        # prepare the AgeGroups cardinalities
        groups_col = 'ageGroup'
        people_by_sample_age = common_cfg.fill_sample_ages_in_cpa_columns(self)
        data_by_group = people_by_sample_age.rename(
            AgeGroup.find_age_group, axis='columns').T
        # index is now given by AgeGroup items
        data_by_group.index.name = groups_col
        # extract to convert to categorical and groupby
        data_by_group = data_by_group.reset_index()
        data_by_group[groups_col] = \
            data_by_group[groups_col].astype('category')
        ages_by_section = data_by_group.groupby(groups_col).sum().T
        self['PeopleTot'] = ages_by_section.sum(axis=1)
        # report all ages
        for col in self.OUTPUT_AGES:
            self[col] = ages_by_section.get(
                col, np.zeros_like(self.iloc[:, 0]))

        # extract long and lat and build geopy locations
        self[common_cfg.coord_col_names[0]] = self['geometry'].apply(
            lambda pos: pos.centroid.x)

        self[common_cfg.coord_col_names[1]] = self['geometry'].apply(
            lambda pos: pos.centroid.y)

        self[common_cfg.positions_col] = [geopy.Point(yx) for yx in zip(
            self[common_cfg.coord_col_names[::-1]].as_matrix())]

        if b_duplicates_check:
            # check no location is repeated - takes a while
            assert not any(self[common_cfg.positions_col].duplicated()),\
                'Repeated position found'

        # cache ages frame and mapped positions for quicker access
        age_multi_index = [self[common_cfg.id_quartiere_col_name],
                           self[common_cfg.positions_col].apply(tuple)]
        self.ages_frame = self[AgeGroup.all()].set_index(age_multi_index)

        self.mapped_positions = MappedPositionsFrame(
            long=self[common_cfg.coord_col_names[0]],
            lat=self[common_cfg.coord_col_names[1]],
            geopy_pos=self[common_cfg.positions_col].tolist(),
            id_quartiere=self[common_cfg.id_quartiere_col_name].tolist()
            )

    def get_age_sample(self, age_group=None, n_sample=1000):

        if age_group is not None:
            coord, n_repeat = self.mapped_positions.align(
                self.ages_frame[age_group], axis=0)
        else:
            coord, n_repeat = self.mapped_positions.align(
                self.ages_frame.sum(axis=1), axis=0)
        idx = np.repeat(range(coord.shape[0]), n_repeat)
        coord = coord[common_cfg.coord_col_names].iloc[idx]
        sample = coord.sample(int(n_sample)).as_matrix()
        return sample[:, 0], sample[:, 1]

    @classmethod
    def create_from_istat_cpa(cls, city_name):
        """Constructor caller for DemandFrame"""
        city_config = city_settings.get_city_config(city_name)
        return cls(city_config.istat_cpa_data, b_duplicates_check=False)


class ServiceValues(dict):
    """A class to store, make available for aggregation
     and easily export estimated service values"""

    def __init__(self, mapped_positions):
        assert isinstance(mapped_positions, MappedPositionsFrame), \
            'Expected MappedPositionsFrame'
        self.mappedPositions = mapped_positions

        # initialise for all service types
        super().__init__(
            {service: pd.DataFrame(0.0, index=mapped_positions.index,
                                   columns=DemandFrame.OUTPUT_AGES)
             for service in ServiceType})

    def plot_output(self, service_type, age_group):
        """Make output for plotting for a given serviceType and age_group"""
        # extract values
        values_series = self[service_type][age_group]
        # TODO: this is quite inefficient though still fast, optimise it
        joined = pd.concat([values_series, self.mappedPositions], axis=1)

        # format output as (x,y,z) surface
        z = values_series.values
        x = joined[common_cfg.coord_col_names[0]].values
        y = joined[common_cfg.coord_col_names[1]].values
        return x, y, z

    @property
    def positions(self):
        return list(self.mappedPositions.Positions.values)


class ServiceEvaluator:
    """A class to evaluate a given list of service units"""

    def __init__(self, unit_list, output_services=None):
        assert isinstance(unit_list, list), \
            'List expected, got %s' % type(unit_list)
        if not output_services:
            output_services = [t for t in ServiceType]
        assert all([isinstance(u, ServiceUnit) for u in unit_list]),\
            'ServiceUnits expected in list'
        self.units = tuple(unit_list)  # lock ordering
        self.output_services = output_services
        self.units_tree = {}
        for service_type in self.output_services:
            type_units = tuple(
                [u for u in self.units if u.service == service_type])
            if type_units:
                self.units_tree[service_type] = type_units

        self.service_positions = {}
        for service_type, service_units in self.units_tree.items():
            if service_units:
                self.service_positions[service_type] = \
                    MappedPositionsFrame.from_geopy_points(
                        [u.site for u in service_units])
            else:
                continue  # no units for this servicetype, do not create key

    @property
    def attendance_tree(self):
        out = {}
        for service_type, service_units in self.units_tree.items():
            if service_units:
                out[service_type] = np.array(
                    [u.attendance for u in service_units])
            else:
                continue  # no units for this service type, do not create key
        return out

    @property
    def attendance_means(self):
        return pd.Series(
            {service_type: attendance.mean() for service_type, attendance
             in self.attendance_tree.items()})

    def get_interactions_at(self, targets_coord_array):
        """
        STEP 1
        Evaluates the initial service availabilities at demand location
        before correcting for attendance
        """

        interactions = {}

        # loop over different services
        for service_type, service_mapped_positions \
                in self.service_positions.items():

            interactions[service_type] = {}  # initialise
            # get lat-long data for this servicetype units
            service_coord_array = service_mapped_positions[
                common_cfg.coord_col_names[::-1]].as_matrix()

            start = time()
            # compute a lower bound for pairwise distances
            # if this is larger than threshold, set the interaction to zero.
            distance_matrix = cdist(
                service_coord_array, targets_coord_array) * min(
                common_cfg.approx_tile_deg_to_km)

            print(service_type,
                  'Approx distance matrix in %.4f' % (time() - start))

            # Compute interactions for age groups that can be served by this
            # service
            for this_age_group in service_type.demand_ages:
                print('\n Computing', service_type, this_age_group)
                start_group = time()
                # assign default value of zero to interactions
                interactions[service_type][this_age_group] = \
                    np.zeros([service_coord_array.shape[0],
                              targets_coord_array.shape[0]])

                for iUnit, thisUnit in enumerate(
                        self.units_tree[service_type]):

                    if iUnit > 0 and iUnit % 500 == 0:
                        print('... %i units done' % iUnit)

                    # each row can be used to drop positions that are too far:
                    # we flag the positions that are within the
                    # threshold and we compute values just for them
                    b_active_unit = distance_matrix[iUnit, :] <\
                        thisUnit.ker_thresholds[this_age_group]
                    if any(b_active_unit):
                        interactions[service_type][this_age_group][
                            iUnit, b_active_unit] = thisUnit.evaluate(
                            targets_coord_array[b_active_unit, :],
                            this_age_group)
                print('AgeGroup time %.4f' % (time() - start_group))

        return interactions

    def _compute_attendance_from_interactions(self, interactions, ages_data):
        """
        STEP 2 & 3
        Get estimates of attendance for each service unit
        """
        for service_type, ages in interactions.items():
            # initialise group loads for every unit given by current age_group
            group_loads = np.zeros(
                [self.service_positions[service_type].shape[0],
                 len(DemandFrame.OUTPUT_AGES)])

            unassigned_pop = np.zeros(len(DemandFrame.OUTPUT_AGES))

            for i_age, age_group in enumerate(ages):
                this_interactions = interactions[service_type][age_group]
                sums_at_positions = this_interactions.sum(axis=0)
                b_above_thr = \
                    sums_at_positions > common_cfg.kernel_value_cutoff
                # compute coefficients to apply to population values
                load_coefficients = np.zeros_like(this_interactions)
                load_coefficients[:, b_above_thr] = \
                    this_interactions[:, b_above_thr] / \
                    sums_at_positions[b_above_thr]

                group_loads[:, i_age] = np.matmul(
                    load_coefficients, ages_data[age_group])
                unassigned_pop[i_age] = \
                    ages_data[age_group][~b_above_thr].sum()
                print('%s: %s -- unassigned: %i | Total: %i' % (
                    service_type, age_group, unassigned_pop[i_age],
                    ages_data[age_group].sum()))

            # collect loads for the different age groups
            total_loads = group_loads.sum(axis=1)

            # store unit loads in existing instances
            for iUnit, unit in enumerate(self.units_tree[service_type]):
                unit.attendance = total_loads[iUnit]

        return None

    def _compute_attendance_factors(self, clip_level):
        """
        This function gets the relative correction factors
        from the computed attendance values
        """
        assert clip_level > 1, 'The clipping factor should be greater than 1'
        out = {}

        for service_type, attendance_values in self.attendance_tree.items():
            # get ratios
            raw_ratios = attendance_values / attendance_values.mean()
            np.nan_to_num(raw_ratios, copy=False)  # this replaces Nan with 0
            # Apply [1/m, m] clipping to raw ratios
            out[service_type] = 1 / np.clip(
                raw_ratios, 1 / clip_level, clip_level)
        return out

    def get_aggregate_values_from_interactions(
            self, interactions, demand_data, b_evaluate_attendance,
            clip_level):

        assert isinstance(demand_data, DemandFrame), \
            'Ages frame should be a DemandFrame'

        # initialise output with dedicated class
        values_store = ServiceValues(demand_data.mapped_positions)

        if b_evaluate_attendance:
            # STEPS 2 & 3: get estimates of attendance for each service unit
            self._compute_attendance_from_interactions(
                interactions, demand_data.ages_frame)

            # STEP 4 & FINAL STEP:
            # correct interactions with unit attendance and aggregate
            attendance_factors = self._compute_attendance_factors(clip_level)

            for service_type, ages in interactions.items():
                for age_group in ages:
                    values_store[service_type][age_group] = \
                        service_type.aggregate_units(
                            interactions[service_type][age_group] *
                            attendance_factors[service_type][:, np.newaxis],
                            axis=0)
        else:
            # FINAL STEP:
            # aggregate unit contributions according to the service type norm
            for service_type, ages in interactions.items():
                for age_group in ages:
                    values_store[service_type][age_group] = \
                        service_type.aggregate_units(
                            interactions[service_type][age_group],
                            axis=0)

        return values_store


# KPI calculation
class KPICalculator:
    """Class to aggregate demand and evaluate
    census-section-based and position based KPIs"""

    def __init__(self, demand_frame, service_units, city_name):
        assert city_name in city_settings.city_names_list,\
            'Unrecognized city name %s' % city_name
        assert isinstance(demand_frame, DemandFrame), 'Demand frame expected'
        assert all(
            [isinstance(su, ServiceUnit) for su in service_units]), \
            'Service units list expected'

        self.city = city_name
        self.demand = demand_frame
        # initialise the service evaluator
        self.evaluator = ServiceEvaluator(service_units)
        self.service_positions = self.evaluator.service_positions
        # initialise output values
        self.service_interactions = None
        self.service_values = ServiceValues(self.demand.mapped_positions)
        self.weighted_values = ServiceValues(self.demand.mapped_positions)
        self.quartiere_kpi = {}
        self.istat_kpi = pd.DataFrame()
        self.istat_vitality = pd.DataFrame()

        # compute ages totals
        self.ages_totals = self.demand.ages_frame.groupby(level=0).sum()

    def evaluate_services_at_demand(
            self,
            b_evaluate_attendance=True,
            clip_level=common_cfg.demand_correction_clip):
        """
        Wrapper on the ServiceEvaluator that triggers the
        computation pipeline. Once interactions are first evaluated,
        different aggregations use the computed values.
        """

        if not self.service_interactions:
            # trigger service interaction evaluation
            self.evaluate_interactions_at_demand()
        else:
            print('Found existing interactions, using them')

        # aggregate interactions using the providing clip level to adjust
        # for attendance
        self.service_values = \
            self.evaluator.get_aggregate_values_from_interactions(
                self.service_interactions,
                self.demand,
                b_evaluate_attendance=b_evaluate_attendance,
                clip_level=clip_level)

        return self.service_values

    def evaluate_interactions_at_demand(self):
        # extract demand coordinates from demand data and evaluate
        # interaction values at them
        targets_coord_array = self.demand.mapped_positions[
            common_cfg.coord_col_names[::-1]].as_matrix()

        self.service_interactions = self.evaluator.get_interactions_at(
            targets_coord_array)

        return self.service_interactions

    def compute_kpi_for_localized_services(self):
        assert self.service_interactions, \
            'Have we evaluated service values before making averages for KPIs?'
        # get mean service levels by quartiere,
        # weighting according to the number of citizens
        tol = 1e-12

        for service, values_at_locations in self.service_values.items():
            # iterate over columns as Enums are not orderable...
            for col in DemandFrame.OUTPUT_AGES:
                if col in service.demand_ages:
                    self.weighted_values[service][col] = pd.Series.multiply(
                        values_at_locations[col], self.demand.ages_frame[col])
                else:
                    self.weighted_values[service][col] = \
                        np.nan * values_at_locations[col]
            # get minmax range for sanity checks after
            check_range = (
                values_at_locations.groupby(
                    common_cfg.id_quartiere_col_name).min() - tol,
                values_at_locations.groupby(
                    common_cfg.id_quartiere_col_name).max() + tol
                          )
            # sum weighted fractions by neighbourhood
            weighted_sums = self.weighted_values[service].groupby(
                common_cfg.id_quartiere_col_name).sum()
            # set to NaN value the age groups that have no people or there is
            #  no demand for the service
            weighted_sums[self.ages_totals == 0] = np.nan
            weighted_sums.iloc[:, ~weighted_sums.columns.isin(
                service.demand_ages)] = np.nan
            self.quartiere_kpi[service] = (
                weighted_sums / self.ages_totals).reindex(
                columns=DemandFrame.OUTPUT_AGES, copy=False)

            # check that the weighted mean lies
            # between min and max in the neighbourhood
            for col in self.quartiere_kpi[service].columns:
                b_good = (self.quartiere_kpi[service][col].between(
                    check_range[0][col],
                    check_range[1][col]) | self.quartiere_kpi[service][
                    col].isnull())
                assert all(b_good),\
                    ''' -- Unexpected error in mean computation:
                            Service: %s,
                            AgeGroup: %s

                        Bad values:
                        %s

                        Range:
                        %s
                    ''' % (service, col,
                           self.quartiere_kpi[service][col][~b_good],
                           check_range
                           )

        return self.quartiere_kpi

    def compute_kpi_for_istat_values(self):
        all_quartiere = \
            self.demand.groupby(common_cfg.id_quartiere_col_name).sum()

        drop_columns = [
            c for c in DemandFrame.OUTPUT_AGES + common_cfg.excluded_columns
            if c in all_quartiere.columns]
        quartiere_data = all_quartiere.drop(drop_columns, axis=1)

        kpi_frame = istat_kpi.wrangle_istat_cpa2011(quartiere_data, self.city)

        self.istat_kpi = kpi_frame
        self.istat_vitality = istat_kpi.compute_vitality_cpa2011(
            quartiere_data)

        return self.istat_kpi, self.istat_vitality

    def plot_unit_attendance(
            self, service_type, min_level=0, max_level=np.Inf):
        """
        Scatter units of a ServiceType according to the estimated
        attendence
        """
        units = self.evaluator.units_tree[service_type]
        plot_units = [p for p in units if min_level < p.attendance < max_level]
        plt.scatter(self.demand.mapped_positions.Long,
                    self.demand.mapped_positions.Lat,
                    c='b', s=self.demand.P1, marker='.')
        for a in plot_units:
            plt.scatter(a.site.longitude, a.site.latitude,
                        c='red', marker='.', s=a.attendance / 10)
        if not plot_units:
            print('NO UNITS!')
        plt.xlabel('Long')
        plt.ylabel('Lat')
        plt.title(
            '%s di %s con bacino stimato fra %s e %s' % (
                service_type.label, self.city, min_level, max_level))
        plt.legend(['Residenti', service_type.label])
        plt.show()

        return None
