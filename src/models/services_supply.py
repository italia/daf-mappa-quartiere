
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
