## TODO: find way to put this into some global settings
import os
import sys
from time import time

import geopy
import geopy.distance
import numpy as np
import pandas as pd
from sklearn import gaussian_process
from sqlalchemy.sql.operators import comma_op

rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import common_cfg, istat_kpi, city_settings
from src.models.city_items import AgeGroup, ServiceType  # enum classes for the model

from scipy.optimize import fsolve
from scipy.spatial.distance import cdist

import functools

gaussKern = gaussian_process.kernels.RBF


@functools.lru_cache(maxsize=int(1e6))  # cache expensive distance calculation
def compute_distance(x, y):
    return geopy.distance.great_circle(x, y).km


## ServiceUnit class
class ServiceUnit:
    def __init__(self, service, name, position, scaleIn,
                 ageDiffusionIn={}, kernelThresholds=None, attributesIn={}):
        assert isinstance(position, geopy.Point), 'Position must be a geopy Point'
        assert isinstance(service, ServiceType), 'Service must belong to the Eum'
        assert isinstance(name, str), 'Name must be a string'
        assert (np.isscalar(scaleIn)) & (scaleIn > 0), 'Scale must be a positive scalar'
        assert set(ageDiffusionIn.keys()) <= set(
            AgeGroup.all()), 'Diffusion keys should be AgeGroups'
        assert isinstance(attributesIn, dict), 'Attributes can be provided in a dict'
        if kernelThresholds:
            assert set(kernelThresholds.keys()) >= set(ageDiffusionIn.keys()), \
                'Kernel thresholds if provided must be defined for every age diffusion key'
            bThresholdsInput = True
        else:
            bThresholdsInput = False

        self.name = name
        self.service = service

        # A ServiceType can have many sites, so each unit has its own. 
        # Moreover, a site is not uniquely assigned to a service
        self.site = position
        self.coordTuple = (position.latitude, position.longitude)

        self.scale = scaleIn  # store scale info
        self.attributes = attributesIn  # dictionary

        # how the service availability area varies for different age groups
        self.ageDiffusion = ageDiffusionIn

        # define kernel taking scale into account
        self.kernel = {
            g: gaussKern(length_scale=l * self.scale) for g, l in self.ageDiffusion.items()}

        # precompute kernel threshold per AgeGroup
        self.kerThresholds = {g: np.Inf for g in AgeGroup.all()}  # initialise to Inf
        if bThresholdsInput:
            assert all([isinstance(kern, gaussKern) for kern in self.kernel.values()]), \
                'Unexpected kernel type in ServiceUnit'
            assert all(
                [val > 0 for val in kernelThresholds.values()]), 'Thresholds must be positive'
            self.kerThresholds.update(kernelThresholds)
        else:
            self._compute_kernel_thresholds()

        # initialise attendance
        self.attendance = np.nan

    def _compute_kernel_thresholds(self):
        '''Triggers kernel thresholds computation for all ages groups'''
        for ageGroup in self.kernel.keys():
            kern = self.kernel[ageGroup]
            thrValue = np.Inf
            if not isinstance(kern, gaussKern):
                print('WARNING: non gaussian class found in kernel: type is %s' % \
                      type(kern))
            def fun_to_solve(x):
                out = self.kernel[ageGroup](
                    x, np.array([[0], ])) - common_cfg.kernelValueCutoff
                return out.flatten()

            initGuess = common_cfg.kernelStartZeroGuess * self.scale

            for k in range(3):  # try 3 alternatives
                solValue, _, flag, msg = fsolve(fun_to_solve,
                                                np.array(initGuess), full_output=True)
                if flag == 1:
                    thrValue = solValue  # assign found value
                    break
                else:
                    initGuess = initGuess * 1.1
            if flag != 1:
                print('WARNING: could not compute thresholds for unit %s, age %s' % \
                      (self.name, ageGroup))

            # assign positive value as threshold
            self.kerThresholds[ageGroup] = abs(thrValue)

    def transform_kernels_with_factor(self, kValue):
        '''This function applies the transformation:
          newKernel = k * oldKernel(x/k) '''
        assert kValue > 0, 'Expected positive factor'
        for ageGroup in self.kernel.keys():
            # change lengthscale
            self.kernel[ageGroup].length_scale = self.kernel[ageGroup].length_scale/kValue
            self.kernel[ageGroup] = kValue * self.kernel[ageGroup]

        # trigger threshold recomputation
        self._compute_kernel_thresholds()

    def evaluate(self, targetCoords, ageGroup):
        # evaluate kernel to get service level score.
        # If age group is not relevant to the service, return 0 as default
        if self.kernel.__contains__(ageGroup):
            assert isinstance(targetCoords, np.ndarray), 'ndarray expected'
            assert targetCoords.shape[1] == 2, 'lat and lon columns expected'
            # get distances
            distances = np.zeros(shape=(len(targetCoords), 1))
            distances[:, 0] = np.apply_along_axis(
                lambda x: compute_distance(tuple(x), self.coordTuple),
                axis=1, arr=targetCoords)

            score = self.kernel[ageGroup](distances, np.array([[0], ]))

        else:
            score = np.zeros(shape=targetCoords.shape[0])

        return np.squeeze(score)

## Mapped positions frame class
class MappedPositionsFrame(pd.DataFrame):
    '''A class to collect an array of positions alongside areas labels'''

    def __init__(self, positions=None, long=None, lat=None, idQuartiere=None):

        # build positions data
        if not positions:
            assert long or lat, 'Expected input if positions are not given'

            if idQuartiere is None:
                idQuartiere = np.full(long.shape, np.nan)
            # create mapping dict from coordinates
            mappingDict = {
                common_cfg.coordColNames[0]: long,  # long
                common_cfg.coordColNames[1]: lat,  # lat
                common_cfg.IdQuartiereColName: idQuartiere,  # quartiere aggregation
            }
            # istantiate geopy positions
            geopyPoints = list(map(lambda y, x: geopy.Point(y, x), lat, long))
            mappingDict[common_cfg.positionsCol] = geopyPoints
            mappingDict[common_cfg.tupleIndexName] = [tuple(p) for p in geopyPoints]

        else:
            assert all([isinstance(t, geopy.Point) for t in positions]), 'Geopy Points expected'
            assert not long, 'Long input not expected if positions provided'
            assert not lat, 'Lat input not expected if positions provided'
            if idQuartiere is None:
                idQuartiere = np.full(len(positions), np.nan)
            # create mapping dict from positions    
            mappingDict = {
                common_cfg.coordColNames[0]: [x.longitude for x in positions],  # long
                common_cfg.coordColNames[1]: [x.latitude for x in positions],  # lat
                common_cfg.IdQuartiereColName: idQuartiere,  # quartiere aggregation
                common_cfg.positionsCol: positions,
                common_cfg.tupleIndexName: [tuple(p) for p in positions]}

        # finally call DataFrame constructor
        super().__init__(mappingDict)
        self.set_index([common_cfg.IdQuartiereColName, common_cfg.tupleIndexName], inplace=True)


class ServiceValues(dict):
    '''A class to store, make available for aggregation and easily export estimated service values'''

    def __init__(self, mappedPositions):
        assert isinstance(mappedPositions, MappedPositionsFrame), 'Expected MappedPositionsFrame'
        self.mappedPositions = mappedPositions

        # initialise for all service types
        super().__init__({service: pd.DataFrame(
            np.zeros([mappedPositions.shape[0], len(AgeGroup.all())]),
            index=mappedPositions.index, columns=AgeGroup.all())
            for service in ServiceType})

    def plot_output(self, servType, ageGroup):
        '''Make output for plotting for a given serviceType and ageGroup'''
        # extract values
        valuesSeries = self[servType][ageGroup]
        # TODO: this is quite inefficient though still fast, optimise it
        joined = pd.concat([valuesSeries, self.mappedPositions], axis=1)

        # format output as (x,y,z) surface
        z = valuesSeries.values
        x = joined[common_cfg.coordColNames[0]].values
        y = joined[common_cfg.coordColNames[1]].values
        return x, y, z

    @property
    def positions(self):
        return list(self.mappedPositions.Positions.values)


class ServiceEvaluator:
    '''A class to evaluate a given list of service units'''

    def __init__(self, unitList, outputServicesIn=[t for t in ServiceType]):
        assert isinstance(unitList, list), 'List expected, got %s' % type(unitList)
        assert all([isinstance(t, ServiceUnit) for t in unitList]), 'ServiceUnits expected in list'
        self.units = tuple(unitList)  # lock ordering
        self.outputServices = outputServicesIn
        self.unitsTree = {}
        for sType in self.outputServices:
            typeUnits = tuple([u for u in self.units if u.service == sType])
            if typeUnits:
                self.unitsTree[sType] = typeUnits

        self.servicePositions = {}
        for sType, serviceUnits in self.unitsTree.items():
            if serviceUnits:
                self.servicePositions[sType] = MappedPositionsFrame(
                    positions=[u.site for u in serviceUnits])
            else:
                continue  # no units for this servicetype, do not create key

    @property
    def attendanceTree(self):
        out = {}
        for sType, serviceUnits in self.unitsTree.items():
            if serviceUnits:
                out[sType] = np.array([u.attendance for u in serviceUnits])
            else:
                continue  # no units for this servicetype, do not create key
        return out

    @property
    def attendanceMeans(self):
        return pd.Series({sType: attendance.mean() \
                          for sType, attendance in self.attendanceTree.items()})

    @property
    def attendanceFactors(self):
        '''
        This function gets the relative correction factors
        '''
        out = {}
        for sType, attendanceValues in self.attendanceTree.items():
            # get ratios
            rawRatios = attendanceValues / attendanceValues.mean()
            np.nan_to_num(rawRatios, copy=False)  # this replaces Nan with 0
            out[sType] = 1/np.clip(rawRatios, 1 / common_cfg.demandCorrectionClip,
                                 common_cfg.demandCorrectionClip) # [1/m, m] clipping
        return out


    def evaluate_services_at(self, demandData, bEvaluateAttendance=False):
        assert isinstance(demandData, DemandFrame), 'Expected MappedPositionsFrame'

        agesData = demandData.agesFrame

        # initialise output with dedicated class
        valuesStore = ServiceValues(agesData)

        # STEP 1: evaluate service interactions at demand locations
        # using (lat, long) format for evaluations
        targetsCoordArray = agesData[common_cfg.coordColNames[::-1]].as_matrix()
        self._evaluate_interactions_at(targetsCoordArray)

        if bEvaluateAttendance:
            # STEPS 2 & 3: get estimates of attendance for each service unit
            self._compute_attendance_from_interactions(agesData)

            # STEP 4 & FINAL STEP: correct interactions with unit attendance and aggregate
            attendanceFactors = self.attendanceFactors

            for sType, ages in self.interactions.items():
                for ageGroup in ages:
                    valuesStore[sType][ageGroup] = sType.aggregate_units(
                        self.interactions[sType][ageGroup]*attendanceFactors[sType][:,np.newaxis],
                        axis=0)
        else:
            # FINAL STEP: aggregate unit contributions according to the service type norm
            for sType, ages in self.interactions.items():
                for ageGroup in ages:
                    valuesStore[sType][ageGroup] = sType.aggregate_units(
                        self.interactions[sType][ageGroup],
                        axis=0)

        return valuesStore

    def _evaluate_interactions_at(self, targetsCoordArray):
        '''
        STEP 1

        Evaluates the initial service availabilities at demand location, before correcting
        for attendance
        '''

        self.interactions = {}

        # loop over different services
        for serviceType, serviceMappedPositions in self.servicePositions.items():

            self.interactions[serviceType] = {}  # initialise
            # get lat-long data for this servicetype units
            serviceCoordArray = serviceMappedPositions[
                common_cfg.coordColNames[::-1]].as_matrix()

            start = time()
            # compute a lower bound for pairwise distances
            # if this is larger than threshold, set the interaction to zero.
            Dmatrix = cdist(serviceCoordArray, targetsCoordArray) * min(
                common_cfg.approxTileDegToKm)
            print(serviceType, 'Approx distance matrix in %.4f' % (time() - start))

            for thisAgeGroup in AgeGroup.all():
                if thisAgeGroup in serviceType.demandAges:  # the service can serve this agegroup
                    print('\n Computing', serviceType, thisAgeGroup)
                    startGroup = time()
                    # assign default value of zero to interactions
                    self.interactions[serviceType][thisAgeGroup] = np.zeros(
                        [serviceCoordArray.shape[0], targetsCoordArray.shape[0]])

                    for iUnit, thisUnit in enumerate(self.unitsTree[serviceType]):

                        if iUnit > 0 and iUnit % 500 == 0: print('... %i units done' % iUnit)
                        # each row can be used to drop positions that are too far:
                        # we flag the positions that are within
                        # the threshold and we compute values just for them
                        bActiveUnit = Dmatrix[iUnit, :] < thisUnit.kerThresholds[thisAgeGroup]
                        if any(bActiveUnit):
                            self.interactions[
                                serviceType][thisAgeGroup][iUnit, bActiveUnit] = \
                                thisUnit.evaluate(targetsCoordArray[bActiveUnit, :],
                                                  thisAgeGroup)
                    print('AgeGroup time %.4f' % (time() - startGroup))
                else:
                    continue  # leave default value in valuesStore

        return self.interactions

    def _compute_attendance_from_interactions(self, agesData):
        '''
        STEP 2 & 3: get estimates of attendance for each service unit
        '''
        for sType, ages in self.interactions.items():
            # initialise group loads for every unit given by current ageGroup
            groupLoads = np.zeros([self.servicePositions[sType].shape[0], len(AgeGroup.all())])
            unassignedPop = np.zeros(len(AgeGroup.all()))
            for iAge, ageGroup in enumerate(ages):
                interactions = self.interactions[sType][ageGroup]
                sumsAtPositions = interactions.sum(axis=0)
                bAboveThr = sumsAtPositions > common_cfg.kernelValueCutoff
                # compute coefficients to apply to population values
                loadCoefficients = np.zeros_like(interactions)
                loadCoefficients[:, bAboveThr] = interactions[:, bAboveThr] / sumsAtPositions[
                    bAboveThr]
                # compute coefficients to apply to population values
                groupLoads[:, iAge] = np.matmul(loadCoefficients, agesData[ageGroup])
                unassignedPop[iAge] = agesData[ageGroup][~bAboveThr].sum()
                print('%s: %s -- unassigned: %i | Total: %i' % (
                    sType, ageGroup, unassignedPop[iAge], agesData[ageGroup].sum()))

            # collect loads for the different age groups
            totalLoads = groupLoads.sum(axis=1)

            # store unit loads in existing instances
            for iUnit, unit in enumerate(self.unitsTree[sType]):
                unit.attendance = totalLoads[iUnit]

        return None


### Demand modelling
class DemandFrame(pd.DataFrame):
    '''A class to store demand units in row and
    make them available for aggregation'''

    def __init__(self, dfIn, bDuplicatesCheck=True):
        assert isinstance(dfIn, pd.DataFrame), 'Input DataFrame expected'
        # initialise and assign base DataFrame properties
        super().__init__()
        self.__dict__.update(dfIn.copy().__dict__)

        # prepare the AgeGroups cardinalities
        groupsCol = 'ageGroup'
        peopleBySampleAge = common_cfg.fill_sample_ages_in_cpa_columns(self)
        dataByGroup = peopleBySampleAge.rename(AgeGroup.find_AgeGroup, axis='columns').T
        dataByGroup.index.name = groupsCol  # index is now given by AgeGroup items
        dataByGroup = dataByGroup.reset_index()  # extract to convert to categorical and groupby
        dataByGroup[groupsCol] = dataByGroup[groupsCol].astype('category')
        agesBySection = dataByGroup.groupby(groupsCol).sum().T
        # self['Ages'] = pd.Series(agesBySection.T.to_dict()) # assign dict to each section
        self['PeopleTot'] = agesBySection.sum(axis=1)
        # report all ages
        for col in AgeGroup.all():
            self[col] = agesBySection.get(col, np.zeros_like(self.iloc[:, 0]))

        # assign centroid as position
        geopyValues = self['geometry'].apply(
            lambda pos: geopy.Point(pos.centroid.y, pos.centroid.x))
        self[common_cfg.positionsCol] = geopyValues

        if bDuplicatesCheck:
            # check no location is repeated - takes a while
            assert not any(self[common_cfg.positionsCol].duplicated()), 'Repeated position found'

    @property
    def mappedPositions(self):
        return MappedPositionsFrame(positions=self[common_cfg.positionsCol].tolist(),
                                    idQuartiere=self[common_cfg.IdQuartiereColName].tolist())

    @property
    def agesFrame(self):
        # start from the mappedPositions
        out = self.mappedPositions
        # prepare agesData with matching index
        ageMIndex = [self[common_cfg.IdQuartiereColName],
                     self[common_cfg.positionsCol].apply(tuple)]
        agesData = self[AgeGroup.all()].set_index(ageMIndex)
        # concatenate
        out[agesData.columns] = agesData
        return out

    def get_age_sample(self, ageGroup=None, nSample=1000):

        if ageGroup is not None:
            coord, nRep = self.mappedPositions.align(self.agesFrame[ageGroup], axis=0)
        else:
            coord, nRep = self.mappedPositions.align(self.agesFrame.sum(axis=1), axis=0)
        idx = np.repeat(range(coord.shape[0]), nRep)
        coord = coord[common_cfg.coordColNames].iloc[idx]
        sample = coord.sample(int(nSample)).as_matrix()
        return sample[:, 0], sample[:, 1]

    @staticmethod
    def create_from_istat_cpa(cityName):
        '''Constructor caller for DemandFrame'''
        cityConfig = city_settings.get_city_config(cityName)
        frame = DemandFrame(cityConfig.istatCpaData, bDuplicatesCheck=False)
        return frame


### KPI calculation
class KPICalculator:
    '''Class to aggregate demand and evaluate section based and position based KPIs'''

    def __init__(self, demandFrame, serviceUnits, cityName):
        assert cityName in city_settings.cityNamesList, 'Unrecognized city name %s' % cityName
        assert isinstance(demandFrame, DemandFrame), 'Demand frame expected'
        assert all(
            [isinstance(su, ServiceUnit) for su in serviceUnits]), 'Service units list expected'

        self.city = cityName
        self.demand = demandFrame
        self.sources = serviceUnits
        # initialise the service evaluator
        self.evaluator = ServiceEvaluator(serviceUnits)
        self.servicePositions = self.evaluator.servicePositions
        # initialise output values
        self.serviceValues = ServiceValues(self.demand.mappedPositions)
        self.bEvaluated = False
        self.weightedValues = ServiceValues(self.demand.mappedPositions)
        self.quartiereKPI = {}
        self.istatKPI = pd.DataFrame()

        # derive Ages frame
        ageMIndex = [demandFrame[common_cfg.IdQuartiereColName],
                     demandFrame[common_cfg.positionsCol].apply(tuple)]
        self.agesFrame = demandFrame[AgeGroup.all()].set_index(ageMIndex)
        self.agesTotals = self.agesFrame.groupby(level=0).sum()

    def evaluate_services_at_demand(self,bEvaluateAttendance):
        self.serviceValues = self.evaluator.evaluate_services_at(self.demand, bEvaluateAttendance)
        # set the evaluation flag to True
        self.bEvaluated = True
        return self.serviceValues

    def compute_kpi_for_localized_services(self):
        assert self.bEvaluated, 'Have you evaluated service values before making averages for KPIs?'
        # get mean service levels by quartiere, weighting according to the number of citizens
        for service, data in self.serviceValues.items():
            checkRange = {}
            for col in self.agesFrame.columns:  # iterate over columns as Enums are not orderable...
                if col in service.demandAges:
                    self.weightedValues[service][col] = pd.Series.multiply(
                        data[col], self.agesFrame[col])
                else:
                    self.weightedValues[service][col] = np.nan * data[col]

            checkRange = (data.groupby(common_cfg.IdQuartiereColName).min() - np.finfo(float).eps,
                          data.groupby(common_cfg.IdQuartiereColName).max() + np.finfo(float).eps)

            # sum weighted fractions by neighbourhood
            weightedSums = self.weightedValues[service].groupby(common_cfg.IdQuartiereColName).sum()
            # set to NaN value the AgeGroups that have no people or there is no demand for the service
            weightedSums[self.agesTotals == 0] = np.nan
            weightedSums.iloc[:, ~weightedSums.columns.isin(service.demandAges)] = np.nan

            self.quartiereKPI[service] = (weightedSums / self.agesTotals).reindex(
                columns=AgeGroup.all(), copy=False)

            # check that the weighted mean lies between min and max in the neighbourhood
            for col in self.quartiereKPI[service].columns:
                bGood = (self.quartiereKPI[service][col].between(
                    checkRange[0][col], checkRange[1][col]) | self.quartiereKPI[service][
                             col].isnull())
                assert all(bGood), 'Unexpected error in mean computation'

        return self.quartiereKPI

    def compute_kpi_for_istat_values(self):
        allQuartiere = self.demand.groupby(common_cfg.IdQuartiereColName).sum()

        dropColumns = [c for c in AgeGroup.all() + common_cfg.excludedColumns \
                       if c in allQuartiere.columns]
        quartiereData = allQuartiere.drop(dropColumns, axis=1)

        kpiFrame = istat_kpi.wrangle_istat_cpa2011(quartiereData, self.city)

        self.istatKPI = kpiFrame
        self.istatVitality = istat_kpi.compute_vitality_cpa2011(quartiereData)

        return self.istatKPI, self.istatVitality
