from enum import Enum
import os.path

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
from src.models.process_tools import MappedPositionsFrame, ServiceValues

gaussKern = gaussian_process.kernels.RBF
# useful conversion function 
make_shapely_point = lambda geoPoint: shapely.geometry.Point((geoPoint.longitude, geoPoint.latitude))
# test utility
get_random_pos = lambda n: list(map(geopy.Point, list(zip(np.round(np.random.uniform(45.40, 45.50, n), 5), 
                                np.round(np.random.uniform(9.1, 9.3, n), 5)))))

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

    
class ServiceEvaluator:
    '''A class to evaluate a given list of service units'''
    
    def __init__(self, unitList, outputServicesIn=[t for t in ServiceType]):
        assert isinstance(unitList, list), 'List expected, got %s' % type(unitList)
        assert all([isinstance(t, ServiceUnit) for t in unitList]), 'ServiceUnits expected in list'
        self.units = unitList
        self.outputServices = outputServicesIn
    
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

    
## UnitFactory father class
class UnitFactory:
    def __init__(self, path):
        assert os.path.isfile(path), 'File "%s" not found' % path
        self.filepath = path
        self.rawData = []
        
    def load(self):
           
        defaultLocationColumns = ['Lat', 'Long']
        if set(defaultLocationColumns).issubset(set(self.rawData.columns)):
            print('Location data found')
            # store geolocations as geopy Point
            locations = [geopy.Point(self.rawData.loc[i, defaultLocationColumns]) for i in range(self.nUnits)]
            propertData = self.rawData.drop(defaultLocationColumns, axis=1)
        else:
            propertData = self.rawData
            locations = []
            
        return propertData, locations

    @staticmethod
    def createLoader(serviceType, path):
        if serviceType == ServiceType.School:
            return SchoolFactory(path)
        elif serviceType == ServiceType.Library:
            return LibraryFactory(path)
        else:
            print ("We're sorry, this service han not been implemented yet!")

## UnitFactory children classes
class SchoolFactory(UnitFactory):
    
    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.School
        
    def load(self, meanRadius):
        
        self.rawData = pd.read_csv(self.filepath, sep=';', decimal=',')
        self.nUnits = self.rawData.shape[0]
        
        
        assert meanRadius, 'Please provide a reference radius for the mean school size'
        (propertData, locations) = super().load()
        
        nameCol = 'DENOMINAZIONESCUOLA'
        typeCol = 'ORDINESCUOLA'
        scaleCol = 'ALUNNI'
        
        typeAgeDict = {'SCUOLA PRIMARIA': {AgeGroup.ChildPrimary:1},
                      'SCUOLA SECONDARIA I GRADO': {AgeGroup.ChildMid:1},
                      'SCUOLA SECONDARIA II GRADO': {AgeGroup.ChildHigh:1},}
        
        schoolTypes = propertData[typeCol].unique()
        assert set(schoolTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'
        
        # set the scale to be proportional to the square root of number of children
        scaleData = propertData[scaleCol]**.5
        scaleData = scaleData/scaleData.mean() * meanRadius #mean value is mapped to input parameter
        propertData[scaleCol] = scaleData 
        unitList = []
                
        for scType in schoolTypes:
            bThisGroup = propertData[typeCol]==scType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':scType}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[nameCol], 
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[scType], 
                        scaleIn=rowData[scaleCol],
                        attributesIn=attrDict)
                unitList.append(thisUnit)
        
        return unitList


class LibraryFactory(UnitFactory):
    
    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.Library
        
    def load(self, meanRadius):
        
        self.rawData = pd.read_csv(self.filepath, sep=';', decimal='.')
        self.nUnits = self.rawData.shape[0]
        
        assert meanRadius, 'Please provide a reference radius for the mean library size'
        (propertData, locations) = super().load()
        
        nameCol = 'denominazioni.ufficiale'
        typeCol = 'tipologia-funzionale'
        
        # Modifica e specifica che per le fasce d'età
        typeAgeDict = {'Specializzata': {group:1 for group in AgeGroup.all()},
                      'Importante non specializzata': {group:1 for group in AgeGroup.all()},
                      'Pubblica': {group:1 for group in AgeGroup.all()},
                      'NON SPECIFICATA': {AgeGroup.ChildPrimary:1},
                      'Scolastica': {AgeGroup.ChildPrimary:1},
                      'Istituto di insegnamento superiore': {AgeGroup.ChildPrimary:1},
                      'Nazionale': {AgeGroup.ChildPrimary:1},}
        
        libraryTypes = propertData[typeCol].unique()
        assert set(libraryTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'
        
        unitList = []
                
        for libType in libraryTypes:
            bThisGroup = propertData[typeCol]==libType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':libType}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[nameCol], 
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[libType], 
                        attributesIn=attrDict)
                unitList.append(thisUnit)
        
        return unitList