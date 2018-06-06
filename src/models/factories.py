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
import shapely

rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import common_cfg

from src.models.city_items import AgeGroup, ServiceArea, ServiceType, SummaryNorm # enum classes for the model
from src.models.core import ServiceUnit, ServiceEvaluator, ServiceValues, MappedPositionsFrame

    
## UnitFactory father class
class UnitFactory:
    def __init__(self, path, boundary, sepInput=';', decimalInput=','):
        assert os.path.isfile(path), 'File "%s" not found' % path
        self.filepath = path
        if boundary:
            assert isinstance(boundary,  (shapely.geometry.MultiPolygon, shapely.geometry.Polygon)),\
                'Boundary expected as Polygon or MultiPolygon'
        self.boundary = boundary
        self._rawData = pd.read_csv(self.filepath, sep=sepInput, decimal=decimalInput)
        
    def extract_locations(self):
           
        defaultLocationColumns = ['Lat', 'Long']
        if set(defaultLocationColumns).issubset(set(self._rawData.columns)):
            print('Location data found')
            # check and drop units outside provided city boundary
            geometry = [shapely.geometry.Point(xy) for xy in zip(
                self._rawData[defaultLocationColumns[1]],
                self._rawData[defaultLocationColumns[0]])]
            bWithinBoundary = np.array(list(map(lambda p: p.within(self.boundary), geometry)))

            if not all(bWithinBoundary):
                print('%s -- dropping %i units outside city.' % (self.servicetype, sum(
                    ~bWithinBoundary)))
                self._rawData = self._rawData.iloc[bWithinBoundary, :]

            # store geolocations as geopy Point
            locations = [geopy.Point(yx) for yx in zip(
                self._rawData[defaultLocationColumns[0]],
                self._rawData[defaultLocationColumns[1]])]

            propertData = self._rawData.drop(defaultLocationColumns, axis=1)

        else:
            raise NotImplementedError('Locations not found - not implemented!')

        return propertData, locations

    @property
    def nUnits(self):
        return self._rawData.shape[0]

    @staticmethod
    def createLoader(serviceType, path, boundary):
        typeFactory = [factory for factory in UnitFactory.__subclasses__() \
                       if factory.servicetype ==serviceType]
        assert len(typeFactory) <= 1, 'Duplicates in loaders types'
        if typeFactory:
            return typeFactory[0](path, boundary)
        else:
            print ("We're sorry, this service has not been implemented yet!")
            return []

    @staticmethod
    def make_loaders_for_city(modelCity):
        loadersDict = {}
        for sType in modelCity.keys():
            loadersDict[sType.label] = UnitFactory.createLoader(
                serviceType=sType,
                path=modelCity.servicePaths[sType],
                boundary=modelCity.convhull)
        return loadersDict

            
## UnitFactory children classes
class SchoolFactory(UnitFactory):

    servicetype = ServiceType.School
        
    def load(self, meanRadius):
        
        assert meanRadius, 'Please provide a reference radius for the mean school size'
        (propertData, locations) = super().extract_locations()
        
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

    servicetype = ServiceType.Library

    def __init__(self, path, boundary):
        super().__init__(path, boundary, decimalInput='.')
        
    def load(self, meanRadius):
        
        assert meanRadius, 'Please provide a reference radius for the mean library size'
        (propertData, locations) = super().extract_locations()
        
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


class TransportStopFactory(UnitFactory):

    servicetype = ServiceType.TransportStop

    def __init__(self, path, boundary):
        super().__init__(path, boundary, decimalInput='.')

    def load(self, meanRadius):

        assert meanRadius, 'Please provide a reference radius for stops'
        (propertData, locations) = super().extract_locations()
        # make unique stop code
        propertData['stopCode'] = propertData['stop_id'] + '_' + propertData['route_id']
        # append route types
        routeTypeCol = 'route_type'
        gtfsTypesDict = {0: 'Tram', 1: 'Metro', 3: 'Bus'}
        assert all(propertData[routeTypeCol].isin(gtfsTypesDict.keys())), 'Unexpected route type'
        propertData['routeDesc'] = propertData[routeTypeCol].replace(gtfsTypesDict)

        nameCol = 'stopCode'
        typeCol = 'routeDesc'

        scaleDict = {0:meanRadius, 1: 2*meanRadius, 3: meanRadius}
        thresholdsDict = {t: None for t in scaleDict.keys()}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            unitRouteType = rowData[routeTypeCol]
            attrDict = {'routeType': rowData[typeCol]}
            cachedThresholds = thresholdsDict[unitRouteType] # this is None by default
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol],
                                   position=locations[iUnit],
                                   scaleIn=scaleDict[unitRouteType],
                                   ageDiffusionIn={g:1 for g in AgeGroup.all_but(
                                       [AgeGroup.Newborn, AgeGroup.Kinder])},
                                   kernelThresholds=cachedThresholds,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)
            # if there were no thresholds for this unit type, cache the computed ones
            if not cachedThresholds:
                thresholdsDict[unitRouteType] = thisUnit.kerThresholds

        return unitList


class PharmacyFactory(UnitFactory):

    servicetype = ServiceType.Pharmacy

    def __init__(self, path, boundary):
        super().__init__(path, boundary, decimalInput='.')

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for pharmacies'
        (propertData, locations) = super().extract_locations()

        nameCol = 'CODICEIDENTIFICATIVOFARMACIA'
        colAttributes = {'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unitList = []
        cachedThresholds = None # unique value as all pharmacies share the same scale
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {name:rowData[col] for name, col in colAttributes.items()}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol].astype(str),
                                   position=locations[iUnit],
                                   scaleIn=meanRadius,
                                   ageDiffusionIn={g: 1 for g in AgeGroup.all()},
                                   kernelThresholds=cachedThresholds,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)
            # if there were no thresholds, cache the computed ones
            if not cachedThresholds:
                cachedThresholds = thisUnit.kerThresholds

        return unitList


class UrbanGreenFactory(UnitFactory):

    servicetype = ServiceType.UrbanGreen

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for urban green'
        (propertData, locations) = super().extract_locations()

        nameCol = 'CODICEIDENTIFICATIVOFARMACIA'
        colAttributes = {'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {name: rowData[col] for name, col in colAttributes.items()}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol].astype(str),
                                   position=locations[iUnit],
                                   ageDiffusionIn={g: 1 for g in AgeGroup.all()},
                                   scaleIn=meanRadius,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)

        return unitList