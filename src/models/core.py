
import numpy as np
import pandas as pd
import geopandas as gpd
import geopy, geopy.distance
import shapely
from sklearn import gaussian_process

## TODO: find way to put this into some global settings
import os
import sys
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import common_cfg
from src.models.city_items import AgeGroup, ServiceArea, ServiceType, SummaryNorm # enum classes for the model

gaussKern = gaussian_process.kernels.RBF


## ServiceUnit class
class ServiceUnit:
    def __init__(self, service, name='', position=geopy.Point(45.4641, 9.1919),
                 ageDiffusionIn={}, scaleIn=1, attributesIn={}):
        assert isinstance(position, geopy.Point), 'Position must be a geopy Point' 
        assert isinstance(service, ServiceType), 'Service must belong to the Eum'
        assert isinstance(name, str), 'Name must be a string'
        
        assert (np.isscalar(scaleIn)) & (scaleIn>0) , 'Scale must be a positive scalar'
        assert isinstance(attributesIn, dict), 'Attributes can be provided in a dict'
        
        self.name = name
        self.service = service
        
        # A ServiceType can have many sites, so each unit has its own. 
        # Moreover, a site is not uniquely assigned to a service
        self.site = position
        
        self.scale = scaleIn # store scale info
        self.attributes = attributesIn# dictionary
        
        # how the service availablity area varies for different age groups
        if ageDiffusionIn==None:
            self.ageDiffusion = {g: (
                1 + .005*np.round(np.random.normal(),2))*self.scale for g in AgeGroup.all()} 
        else:
            assert set(ageDiffusionIn.keys()) <= set(AgeGroup.all()), 'Diffusion keys should be AgeGroups'
            #assert all
            self.ageDiffusion = ageDiffusionIn
            
        # define kernel taking scale into account
        self.kernel = {g: gaussKern(length_scale=l*self.scale) for g, l in self.ageDiffusion.items()}
        
        
    def evaluate(self, targetPositions, ageGroup):
        assert all([isinstance(t, geopy.Point) for t in targetPositions]),'Geopy Points expected'
        
        # get distances
        distances = np.zeros(shape=(len(targetPositions),1))
        distances[:,0] = [geopy.distance.great_circle(x, self.site).km for x in targetPositions]
        
        # evaluate kernel to get level service score. If age group is not relevant to the service, return 0 as default
        if self.kernel.__contains__(ageGroup):
            score = self.kernel[ageGroup](distances, np.array([[0],]))
            # check conversion from tuple to nparray
            #targetPositions= np.array(targetPositions)
            #score2 = self.kernel[ageGroup](targetPositions, reshapedPos)
            #assert all(score-score2==0)
        else:
            score = np.zeros_like(targetPositions)
        return np.squeeze(score)
    
    @property
    def users(self): return list(self.propagation.keys())

    
## Mapped positions frame class
class MappedPositionsFrame(pd.DataFrame):
    '''A class to collect an array of positions alongside areas labels'''

    def __init__(self, positions=None, long=None, lat=None, idQuartiere=None):
        
        # build positions data
        if not positions:
            if idQuartiere is None:
                idQuartiere = np.full(long.shape, np.nan)
            # create mapping dict from coordinates
            mappingDict = {
                common_cfg.coordColNames[0]:long, #long
                common_cfg.coordColNames[1]:lat, #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
                            }
            # istantiate geopy positions
            geopyPoints = list(map(lambda y,x: geopy.Point(y,x), lat, long))
            mappingDict[common_cfg.positionsCol] = geopyPoints
            mappingDict[common_cfg.tupleIndexName] = [tuple(p) for p in geopyPoints] 
            
        else:
            assert all([isinstance(t, geopy.Point) for t in positions]),'Geopy Points expected'
            assert not long, 'Long input not expected if positions provided'
            assert not lat, 'Lat input not expected if positions provided'
            if idQuartiere is None:
                idQuartiere = np.full(len(positions), np.nan)
            # create mapping dict from positions    
            mappingDict = {
                common_cfg.coordColNames[0]: [x.longitude for x in positions], #long
                common_cfg.coordColNames[1]: [x.latitude for x in positions], #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
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
        joined = pd.concat([valuesSeries,self.mappedPositions], axis=1)

        # format output as (x,y,z) surface
        z = valuesSeries.values
        x = joined[common_cfg.coordColNames[0]].values
        y = joined[common_cfg.coordColNames[1]].values
        return x,y,z
        
    @property     
    def positions(self): 
        return list(self.mappedPositions.Positions.values)    
    
    
class ServiceEvaluator:
    '''A class to evaluate a given list of service units'''
    
    def __init__(self, unitList, outputServicesIn=[t for t in ServiceType]):
        assert isinstance(unitList, list), 'List expected, got %s' % type(unitList)
        assert all([isinstance(t, ServiceUnit) for t in unitList]), 'ServiceUnits expected in list'
        self.units = unitList
        self.outputServices = outputServicesIn
        self.servicePositions = MappedPositionsFrame(positions=[u.site for u in unitList])

    def evaluate_services_at(self, mappedPositions):
        assert isinstance(mappedPositions, MappedPositionsFrame), 'Expected MappedPositionsFrame'
        # set all age groups as output default
        outputAgeGroups = AgeGroup.all()
        # initialise output with dedicated class
        valuesStore = ServiceValues(mappedPositions)
        
        # loop over different services
        for thisServType in self.outputServices:
            serviceUnits = [u for u in self.units if u.service == thisServType]
            if not serviceUnits:
                continue
            else:
                for thisAgeGroup in outputAgeGroups:
                    unitValues = np.stack(list(map(
                        lambda x: x.evaluate(
                            valuesStore.positions, thisAgeGroup), serviceUnits)), axis=-1)
                    # aggregate unit contributions according to the service type norm
                    valuesStore[thisServType][thisAgeGroup] = thisServType.aggregate_units(unitValues)
        return valuesStore


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
        ageMIndex = [self[common_cfg.IdQuartiereColName],
                     self[common_cfg.positionsCol].apply(tuple)]
        return self[AgeGroup.all()].set_index(ageMIndex)

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
        assert cityName in common_cfg.cityList, \
            'Unrecognised city name "%s"' % cityName
        frame = DemandFrame(common_cfg.get_istat_cpa_data(cityName),
                            bDuplicatesCheck=False)
        return frame

### KPI calculation

class KPICalculator:
    '''Class to aggregate demand and evaluate section based and position based KPIs'''

    def __init__(self, demandFrame, serviceUnits, cityName):
        assert cityName in common_cfg.cityList, 'Unrecognized city name %s' % cityName
        assert isinstance(demandFrame, DemandFrame), 'Demand frame expected'
        assert all(
            [isinstance(su, ServiceUnit) for su in serviceUnits]), 'Demand unit list expected'

        self.city = cityName
        self.demand = demandFrame
        self.sources = serviceUnits
        # initialise the service evaluator
        self.evaluator = ServiceEvaluator(serviceUnits)
        self.servicePositions = self.evaluator.servicePositions
        # initialise output values
        self.serviceValues = ServiceValues(self.demand.mappedPositions)
        self.weightedValues = ServiceValues(self.demand.mappedPositions)
        self.quartiereKPI = {}
        self.istatKPI = {}

        # derive Ages frame
        ageMIndex = [demandFrame[common_cfg.IdQuartiereColName],
                     demandFrame[common_cfg.positionsCol].apply(tuple)]
        self.agesFrame = demandFrame[AgeGroup.all()].set_index(ageMIndex)
        self.agesTotals = self.agesFrame.groupby(level=0).sum()

    def evaluate_services_at_demand(self):
        self.serviceValues = self.evaluator.evaluate_services_at(
            self.demand.mappedPositions)
        return self.serviceValues

    def compute_kpi_for_localized_services(self):
        assert self.serviceValues, 'Service values not available, have you computed them?'
        # get mean service levels by quartiere, weighting according to the number of citizens
        for service, data in self.serviceValues.items():
            checkRange = {}
            for col in self.agesFrame.columns:  # iterate over columns as Enums are not orderable...

                self.weightedValues[service][col] = pd.Series.multiply(
                    data[col], self.agesFrame[col])  # /self.agesTotals[col]
                # TODO: introduce Demand Factors to set to NaN the cases
                # where a service is not needed by a certain AgeGroup

            # sum weighted fractions and assign to output
            checkRange = (data.groupby(common_cfg.IdQuartiereColName).min() - np.finfo(float).eps,
                          data.groupby(common_cfg.IdQuartiereColName).max() + np.finfo(float).eps)
            self.quartiereKPI[service] = (self.weightedValues[service].groupby(
                common_cfg.IdQuartiereColName).sum() / self.agesTotals).reindex(
                columns=AgeGroup.all(), copy=False)

            # check that the weighted mean lies between min and max in the neighbourhood
            for col in self.quartiereKPI[service].columns:
                bGood = (self.quartiereKPI[service][col].between(
                    checkRange[0][col], checkRange[1][col]) | self.quartiereKPI[service][
                             col].isnull())
                assert all(bGood), 'Unexpected error in mean computation'

        return self.quartiereKPI

    def compute_kpi_for_istat_values(self):
        kpiFrame = istat_kpi.wrangle_istat_cpa2011(
            self.demand.groupby(common_cfg.IdQuartiereColName).sum(),
            self.city)
        self.istatKPI = kpiFrame.to_dict()
        return self.istatKPI